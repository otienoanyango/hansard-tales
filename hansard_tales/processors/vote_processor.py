"""
Vote processing module for Votes & Proceedings documents.

This module provides functionality for extracting and processing voting records
from Votes & Proceedings PDFs, including individual MP votes and vote totals.
"""

import uuid
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Literal

import pdfplumber
import structlog

from hansard_tales.analysis.mp_identifier import MPIdentifier

logger = structlog.get_logger(__name__)


@dataclass
class MPVote:
    """Individual MP vote record."""

    mp_id: str
    vote: Literal["aye", "no", "abstain", "absent"]


@dataclass
class VoteRecord:
    """A single vote record from Votes & Proceedings."""

    vote_id: str
    session_id: str
    date: date
    motion_text: str
    vote_type: Literal["division", "voice"]
    result: Literal["passed", "failed"]
    ayes: int
    noes: int
    abstentions: int
    mp_votes: list[MPVote] = field(default_factory=list)


class VoteProcessor:
    """
    Process Votes & Proceedings documents.

    Extracts voting records from PDF tables, matches MPs to votes,
    and calculates vote totals.

    Attributes:
        db_session: Database session for queries
        mp_identifier: MPIdentifier instance for matching MP names
    """

    def __init__(self, db_session, mp_identifier: MPIdentifier):
        """
        Initialize VoteProcessor.

        Args:
            db_session: SQLAlchemy database session
            mp_identifier: MPIdentifier instance for MP name matching
        """
        self.db = db_session
        self.mp_identifier = mp_identifier
        self.logger = logger.bind(component="vote_processor")

    def process_pdf(self, pdf_path: Path) -> list[VoteRecord]:
        """
        Extract votes from Votes & Proceedings PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of VoteRecord objects

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF cannot be processed
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        self.logger.info("processing_votes_pdf", pdf_path=str(pdf_path))

        votes = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    self.logger.debug("processing_page", page=page_num)

                    # Extract tables from page
                    tables = page.extract_tables()

                    for table_num, table in enumerate(tables, 1):
                        if self._is_vote_table(table):
                            self.logger.debug("found_vote_table", page=page_num, table=table_num)

                            vote = self._parse_vote_table(table)
                            if vote:
                                votes.append(vote)

        except Exception as e:
            self.logger.error("pdf_processing_error", error=str(e))
            raise ValueError(f"Failed to process PDF: {e}") from e

        self.logger.info("votes_extracted", count=len(votes))
        return votes

    def _is_vote_table(self, table: list[list[str]]) -> bool:
        """
        Check if table contains vote data.

        Args:
            table: Extracted table as list of rows

        Returns:
            True if table appears to contain vote data
        """
        if not table or len(table) < 2:
            return False

        # Check for vote-related headers in first row
        header = " ".join(str(cell) for cell in table[0] if cell).lower()

        vote_keywords = ["ayes", "noes", "vote", "division", "aye", "no"]
        return any(keyword in header for keyword in vote_keywords)

    def _parse_vote_table(self, table: list[list[str]]) -> VoteRecord | None:
        """
        Parse vote table into structured data.

        Args:
            table: Extracted table as list of rows

        Returns:
            VoteRecord object or None if parsing fails
        """
        if not table or len(table) < 2:
            return None

        mp_votes = []

        # Parse MP votes from table rows (skip header)
        for row in table[1:]:
            if not row or len(row) < 2:
                continue

            # Extract MP name and vote value
            mp_name = str(row[0]).strip() if row[0] else ""
            vote_value = str(row[1]).strip().lower() if row[1] else ""

            if not mp_name or not vote_value:
                continue

            # Match MP to database
            mp_match = self.mp_identifier.identify(mp_name)
            if not mp_match:
                self.logger.warning("mp_not_matched", mp_name=mp_name)
                continue

            # Parse vote value
            vote = self._parse_vote_value(vote_value)

            mp_votes.append(MPVote(mp_id=mp_match.mp_id, vote=vote))

        # Calculate totals
        ayes = sum(1 for v in mp_votes if v.vote == "aye")
        noes = sum(1 for v in mp_votes if v.vote == "no")
        abstentions = sum(1 for v in mp_votes if v.vote == "abstain")

        # Determine result
        result = "passed" if ayes > noes else "failed"

        return VoteRecord(
            vote_id=str(uuid.uuid4()),
            session_id="",  # Will be set from context
            date=date.today(),  # Will be extracted from PDF metadata
            motion_text="",  # Will be extracted from PDF text
            vote_type="division",
            result=result,
            ayes=ayes,
            noes=noes,
            abstentions=abstentions,
            mp_votes=mp_votes,
        )

    def _parse_vote_value(self, vote_value: str) -> Literal["aye", "no", "abstain", "absent"]:
        """
        Parse vote value from text.

        Args:
            vote_value: Vote value as string

        Returns:
            Standardized vote value
        """
        vote_lower = vote_value.lower()

        # Check for specific patterns first (most specific to least specific)
        if "abstain" in vote_lower:
            return "abstain"
        elif "absent" in vote_lower or not vote_value.strip():
            return "absent"
        elif "aye" in vote_lower or "yes" in vote_lower:
            return "aye"
        elif vote_lower in ["no", "nay"] or vote_value.lower().startswith("no "):
            return "no"
        else:
            return "absent"
