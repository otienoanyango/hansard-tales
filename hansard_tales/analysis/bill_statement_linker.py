"""
Bill-Statement Linking for parliamentary analysis.

This module provides functionality for linking parliamentary statements to bills
they discuss. It uses pattern-based extraction, database resolution, and vector
similarity for disambiguation.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from hansard_tales.analysis.statement_segmenter import Statement
from hansard_tales.database.models import BillORM
from hansard_tales.vector_db.interface import VectorDB

logger = logging.getLogger(__name__)


@dataclass
class BillMention:
    """
    A mention of a bill in a parliamentary statement.

    This dataclass represents a detected reference to a bill within a statement,
    including the bill's identity, the mention text, confidence score, and
    surrounding context.

    Attributes:
        bill_id: Database ID of the referenced bill
        bill_title: Full title of the bill
        mention_text: The actual text that mentioned the bill
        confidence: Confidence score (0.0-1.0) for the match
        context: Surrounding text providing context for the mention
    """

    bill_id: str
    bill_title: str
    mention_text: str
    confidence: float
    context: str

    def __post_init__(self):
        """Validate bill mention data."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if not self.bill_id:
            raise ValueError("bill_id cannot be empty")
        if not self.mention_text:
            raise ValueError("mention_text cannot be empty")


class BillStatementLinker:
    """
    Link parliamentary statements to bills they discuss.

    This class implements bill mention detection and resolution using:
    - Pattern-based extraction for explicit bill references
    - Database lookup for bill resolution
    - Vector similarity for disambiguation when multiple bills match

    Bill mention patterns include:
    - "The Finance Bill, 2024"
    - "Bill No. 15 of 2024"
    - "the Bill" (contextual reference)

    Attributes:
        db: SQLAlchemy database session
        vector_db: Vector database interface for similarity search
        patterns: Compiled regex patterns for bill mention detection
    """

    def __init__(self, db_session: Session, vector_db: VectorDB | None = None):
        """
        Initialize bill-statement linker.

        Args:
            db_session: SQLAlchemy database session for bill lookup
            vector_db: Optional vector database for disambiguation
        """
        self.db = db_session
        self.vector_db = vector_db

        # Compile bill mention patterns
        self.patterns = [
            # Pattern 1: "The Finance Bill, 2024" or "Finance Bill, 2024"
            re.compile(
                r"(?:The\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Bill,?\s+(\d{4})", re.IGNORECASE
            ),
            # Pattern 2: "Bill No. 15 of 2024"
            re.compile(r"Bill\s+No\.\s+(\d+)\s+of\s+(\d{4})", re.IGNORECASE),
            # Pattern 3: "the Bill" (contextual reference)
            re.compile(r"\bthe\s+Bill\b", re.IGNORECASE),
        ]

        logger.info("Initialized BillStatementLinker")

    def find_bill_mentions(self, statement: Statement) -> list[BillMention]:
        """
        Find all bill mentions in a statement.

        This is the main entry point for bill mention detection. It applies
        pattern-based extraction and attempts to resolve each mention to a
        specific bill in the database.

        Args:
            statement: Statement to search for bill mentions

        Returns:
            List of BillMention objects for all detected and resolved mentions

        Example:
            >>> linker = BillStatementLinker(db_session)
            >>> mentions = linker.find_bill_mentions(statement)
            >>> for mention in mentions:
            ...     print(f"Found bill: {mention.bill_title}")
        """
        logger.debug(f"Finding bill mentions in statement: {statement.text[:100]}...")

        mentions = []

        # Apply each pattern
        for pattern in self.patterns:
            for match in pattern.finditer(statement.text):
                mention_text = match.group(0)

                # Try to resolve to specific bill
                bill = self._resolve_bill(mention_text, statement)
                if bill:
                    # Extract context around mention
                    context = self._extract_context(statement.text, match.start())

                    mention = BillMention(
                        bill_id=str(bill.id),
                        bill_title=bill.title,
                        mention_text=mention_text,
                        confidence=0.90,  # High confidence for pattern match
                        context=context,
                    )
                    mentions.append(mention)

                    logger.debug(f"Resolved mention '{mention_text}' to bill: {bill.title}")

        # Remove duplicates (same bill mentioned multiple times)
        mentions = self._deduplicate_mentions(mentions)

        logger.info(f"Found {len(mentions)} unique bill mentions in statement")
        return mentions

    def _resolve_bill(self, mention_text: str, statement: Statement) -> BillORM | None:
        """
        Resolve a bill mention to a database record.

        This method attempts to match the mention text to a bill in the database
        using exact title matching. If multiple bills match, it uses vector
        similarity to disambiguate based on statement context.

        Args:
            mention_text: The text mentioning the bill
            statement: The full statement for context

        Returns:
            BillORM object if resolved, None otherwise
        """
        logger.debug(f"Resolving bill mention: {mention_text}")

        # Try exact title match (case-insensitive)
        bills = self.db.query(BillORM).filter(BillORM.title.ilike(f"%{mention_text}%")).all()

        if len(bills) == 0:
            logger.debug(f"No bills found matching: {mention_text}")
            return None

        if len(bills) == 1:
            logger.debug(f"Found exact match: {bills[0].title}")
            return bills[0]

        # Multiple matches - use vector similarity to disambiguate
        logger.debug(f"Found {len(bills)} matching bills, using vector similarity")
        return self._disambiguate_bills(bills, statement)

    def _disambiguate_bills(self, bills: list[BillORM], statement: Statement) -> BillORM | None:
        """
        Disambiguate between multiple matching bills using vector similarity.

        When multiple bills match a mention, this method uses semantic similarity
        between the statement and each bill's content to select the most relevant.

        Args:
            bills: List of candidate bills
            statement: Statement for context

        Returns:
            Most relevant BillORM, or None if vector DB unavailable
        """
        if not self.vector_db:
            logger.warning("Vector DB not available for disambiguation, returning first match")
            return bills[0]

        try:
            # Initialize embedder if needed
            if not hasattr(self, "embedder") or self.embedder is None:
                from sentence_transformers import SentenceTransformer

                self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

            # Generate embedding for statement
            query_embedding = self.embedder.encode(statement.text)

            best_bill = None
            best_score = 0.0

            for bill in bills:
                # Generate embedding for bill (title + summary if available)
                bill_text = bill.title
                # Note: BillORM doesn't have summary field in current schema
                # If bill versions exist, could use first version text

                bill_embedding = self.embedder.encode(bill_text)

                # Calculate cosine similarity
                score = self._cosine_similarity(query_embedding, bill_embedding)

                if score > best_score:
                    best_score = score
                    best_bill = bill

            # Only return if similarity is above threshold
            if best_score > 0.7:
                logger.debug(f"Disambiguated to: {best_bill.title} (score: {best_score:.2f})")
                return best_bill
            else:
                logger.debug(f"Best score {best_score:.2f} below threshold, no disambiguation")
                return None

        except Exception as e:
            logger.error(f"Error during disambiguation: {e}")
            return bills[0]  # Fallback to first match

    def _cosine_similarity(self, vec1: Any, vec2: Any) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0.0-1.0)
        """
        import numpy as np

        # Normalize vectors
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norm = vec2 / np.linalg.norm(vec2)

        # Calculate dot product
        similarity = np.dot(vec1_norm, vec2_norm)

        return float(similarity)

    def _extract_context(self, text: str, position: int, window: int = 100) -> str:
        """
        Extract context around a bill mention.

        Args:
            text: Full statement text
            position: Position of the mention in the text
            window: Number of characters to include before/after

        Returns:
            Context string with mention highlighted
        """
        start = max(0, position - window)
        end = min(len(text), position + window)
        context = text[start:end]

        # Add ellipsis if truncated
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."

        return context.strip()

    def _deduplicate_mentions(self, mentions: list[BillMention]) -> list[BillMention]:
        """
        Remove duplicate bill mentions.

        If the same bill is mentioned multiple times, keep only the mention
        with the highest confidence score.

        Args:
            mentions: List of bill mentions (may contain duplicates)

        Returns:
            Deduplicated list of bill mentions
        """
        if not mentions:
            return []

        # Group by bill_id
        bill_groups = {}
        for mention in mentions:
            if mention.bill_id not in bill_groups:
                bill_groups[mention.bill_id] = []
            bill_groups[mention.bill_id].append(mention)

        # Keep highest confidence mention for each bill
        deduplicated = []
        for _bill_id, group in bill_groups.items():
            best_mention = max(group, key=lambda m: m.confidence)
            deduplicated.append(best_mention)

        return deduplicated

    def link_statement_to_bills(self, statement: Statement) -> list[str]:
        """
        Link a statement to bills and return bill IDs.

        This is a convenience method that finds bill mentions and returns
        just the bill IDs for database storage.

        Args:
            statement: Statement to link to bills

        Returns:
            List of bill IDs (as strings)

        Example:
            >>> linker = BillStatementLinker(db_session)
            >>> bill_ids = linker.link_statement_to_bills(statement)
            >>> # Store in database
            >>> statement_orm.related_bill_ids = bill_ids
        """
        mentions = self.find_bill_mentions(statement)
        return [mention.bill_id for mention in mentions]
