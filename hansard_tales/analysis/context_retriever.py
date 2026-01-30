"""
Context Retrieval (RAG) for statement analysis.

This module provides functionality for retrieving relevant context from the vector
database to enhance LLM analysis of parliamentary statements. It implements
Retrieval-Augmented Generation (RAG) to provide historical statements, related
bills, votes, and session context.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from hansard_tales.analysis.statement_segmenter import Statement
from hansard_tales.vector_db.interface import VectorDB

logger = logging.getLogger(__name__)


@dataclass
class RetrievedContext:
    """
    Context retrieved for a statement using RAG.

    This dataclass holds all relevant context retrieved from the vector database
    to support LLM analysis of a parliamentary statement.

    Attributes:
        historical_statements: Previous statements by the same MP
        related_bills: Bills semantically related to the statement
        related_votes: Votes semantically related to the statement
        session_context: Other statements from the same session
    """

    historical_statements: list[dict[str, Any]] = field(default_factory=list)
    related_bills: list[dict[str, Any]] = field(default_factory=list)
    related_votes: list[dict[str, Any]] = field(default_factory=list)
    session_context: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Validate retrieved context."""
        # Ensure all fields are lists
        if not isinstance(self.historical_statements, list):
            self.historical_statements = []
        if not isinstance(self.related_bills, list):
            self.related_bills = []
        if not isinstance(self.related_votes, list):
            self.related_votes = []
        if not isinstance(self.session_context, list):
            self.session_context = []

    def total_items(self) -> int:
        """Get total number of context items retrieved."""
        return (
            len(self.historical_statements)
            + len(self.related_bills)
            + len(self.related_votes)
            + len(self.session_context)
        )

    def is_empty(self) -> bool:
        """Check if no context was retrieved."""
        return self.total_items() == 0


class ContextRetriever:
    """
    Retrieve relevant context for statement analysis using RAG.

    This class implements Retrieval-Augmented Generation (RAG) to fetch relevant
    context from the vector database. It retrieves:
    - Historical statements by the same MP
    - Related bills mentioned or discussed
    - Related votes on similar topics
    - Session context from the same parliamentary session

    The retrieved context is used to enhance LLM analysis by providing relevant
    background information.

    Attributes:
        vector_db: Vector database interface for similarity search
        embedding_model: Name of the sentence-transformers model
        embedder: Sentence transformer model for generating embeddings
    """

    def __init__(
        self,
        vector_db: VectorDB,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize context retriever.

        Args:
            vector_db: Vector database interface for similarity search
            embedding_model: Name of sentence-transformers model to use
        """
        self.vector_db = vector_db
        self.embedding_model = embedding_model
        self.embedder = None  # Will be initialized lazily

        logger.info(f"Initialized ContextRetriever with model: {embedding_model}")

    def _init_embedder(self):
        """Initialize sentence-transformers embedder lazily."""
        if self.embedder is None:
            try:
                from sentence_transformers import SentenceTransformer

                self.embedder = SentenceTransformer(self.embedding_model)
                logger.info(f"Loaded embedding model: {self.embedding_model}")
            except ImportError:
                logger.error(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )
                raise
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise

    def retrieve(self, statement: Statement, top_k: int = 5) -> RetrievedContext:
        """
        Retrieve relevant context for a statement.

        This is the main entry point for context retrieval. It fetches all types
        of relevant context and returns them in a structured format.

        Args:
            statement: Statement to retrieve context for
            top_k: Number of results to retrieve for each context type

        Returns:
            RetrievedContext with all retrieved context

        Example:
            >>> retriever = ContextRetriever(vector_db)
            >>> context = retriever.retrieve(statement, top_k=5)
            >>> print(f"Retrieved {context.total_items()} context items")
        """
        logger.debug(f"Retrieving context for statement: {statement.text[:100]}...")

        # Initialize embedder if needed
        self._init_embedder()

        # Generate embedding for statement
        query_embedding = self.embedder.encode(statement.text)

        # Retrieve different types of context
        historical = self._retrieve_historical_statements(statement, query_embedding, top_k)
        bills = self._retrieve_related_bills(query_embedding, top_k)
        votes = self._retrieve_related_votes(query_embedding, top_k)
        session = self._retrieve_session_context(statement, top_k)

        context = RetrievedContext(
            historical_statements=historical,
            related_bills=bills,
            related_votes=votes,
            session_context=session,
        )

        logger.info(
            f"Retrieved {context.total_items()} context items "
            f"(historical: {len(historical)}, bills: {len(bills)}, "
            f"votes: {len(votes)}, session: {len(session)})"
        )

        return context

    def _retrieve_historical_statements(
        self,
        statement: Statement,
        query_embedding: Any,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """
        Retrieve historical statements by the same MP.

        Args:
            statement: Current statement
            query_embedding: Embedding of the statement text
            top_k: Number of results to retrieve

        Returns:
            List of historical statement dictionaries
        """
        if not statement.mp_id:
            logger.debug("No MP ID provided, skipping historical retrieval")
            return []

        try:
            # Query vector DB for statements by same MP
            filter_dict = {"mp_id": statement.mp_id, "document_type": "statement"}
            results = self.vector_db.search(
                collection="statements",
                query_vector=query_embedding.tolist(),
                limit=top_k,
                filter=filter_dict,
            )

            # Extract and format results
            historical = []
            for result in results:
                historical.append(
                    {
                        "text": result.text,
                        "metadata": result.payload,
                        "distance": result.score,
                    }
                )

            logger.debug(
                f"Retrieved {len(historical)} historical statements for MP {statement.mp_id}"
            )
            return historical

        except Exception as e:
            logger.error(f"Error retrieving historical statements: {e}")
            return []

    def _retrieve_related_bills(self, query_embedding: Any, top_k: int) -> list[dict[str, Any]]:
        """
        Retrieve bills related to the statement.

        Args:
            query_embedding: Embedding of the statement text
            top_k: Number of results to retrieve

        Returns:
            List of related bill dictionaries
        """
        try:
            # Query vector DB for bills
            filter_dict = {"document_type": "bill"}
            results = self.vector_db.search(
                collection="bills",
                query_vector=query_embedding.tolist(),
                limit=top_k,
                filter=filter_dict,
            )

            # Extract and format results
            bills = []
            for result in results:
                bills.append(
                    {
                        "text": result.text,
                        "metadata": result.payload,
                        "distance": result.score,
                    }
                )

            logger.debug(f"Retrieved {len(bills)} related bills")
            return bills

        except Exception as e:
            logger.error(f"Error retrieving related bills: {e}")
            return []

    def _retrieve_related_votes(self, query_embedding: Any, top_k: int) -> list[dict[str, Any]]:
        """
        Retrieve votes related to the statement.

        Args:
            query_embedding: Embedding of the statement text
            top_k: Number of results to retrieve

        Returns:
            List of related vote dictionaries
        """
        try:
            # Query vector DB for votes
            filter_dict = {"document_type": "vote"}
            results = self.vector_db.search(
                collection="votes",
                query_vector=query_embedding.tolist(),
                limit=top_k,
                filter=filter_dict,
            )

            # Extract and format results
            votes = []
            for result in results:
                votes.append(
                    {
                        "text": result.text,
                        "metadata": result.payload,
                        "distance": result.score,
                    }
                )

            logger.debug(f"Retrieved {len(votes)} related votes")
            return votes

        except Exception as e:
            logger.error(f"Error retrieving related votes: {e}")
            return []

    def _retrieve_session_context(self, statement: Statement, top_k: int) -> list[dict[str, Any]]:
        """
        Retrieve other statements from the same session.

        Args:
            statement: Current statement
            top_k: Number of results to retrieve

        Returns:
            List of session context statement dictionaries
        """
        # TODO: Implement session context retrieval
        # This requires session tracking in the database
        # For now, return empty list
        logger.debug("Session context retrieval not yet implemented")
        return []
