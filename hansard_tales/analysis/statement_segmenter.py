"""
Statement Segmentation System.

This module provides functionality for segmenting Hansard text into
individual statements by MPs using boundary detection patterns and
MP identification.
"""

import re
from dataclasses import dataclass

from hansard_tales.analysis.mp_identifier import MPIdentifier


@dataclass
class Statement:
    """
    A single statement by an MP in Hansard.

    Attributes:
        text: The statement text
        mp_id: UUID of the MP who made the statement (None if unidentified)
        start_pos: Starting position in source text
        end_pos: Ending position in source text
        page_number: Page number in source document (optional)
    """

    text: str
    mp_id: str | None
    start_pos: int
    end_pos: int
    page_number: int | None = None


class StatementSegmenter:
    """
    Segment Hansard text into individual statements.

    This class uses boundary detection patterns to split Hansard text
    into individual statements by MPs. Boundaries are detected using:
    - MP name mentions (start of new statement)
    - Speaker interventions
    - Section headers
    - Page breaks

    Hansard statements are bounded by:
    - MP name mentions (start of new statement)
    - Speaker interventions
    - Section headers
    - Page breaks
    """

    def __init__(self, mp_identifier: MPIdentifier):
        """
        Initialize statement segmenter.

        Args:
            mp_identifier: MPIdentifier instance for identifying MPs
        """
        self.mp_identifier = mp_identifier

        # Patterns for statement boundaries
        self.boundary_patterns = [
            # MP name with title
            re.compile(r"\n(?:Hon\.|Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+[A-Z]"),
            # Speaker interventions
            re.compile(r"\n(?:The Speaker|The Chairperson|The Deputy Speaker):"),
            # Section headers (10+ uppercase characters)
            re.compile(r"\n[A-Z\s]{10,}\n"),
        ]

    def segment(self, text: str, session_id: str) -> list[Statement]:
        """
        Segment text into statements.

        Args:
            text: Hansard text to segment
            session_id: Session ID for context

        Returns:
            List of Statement objects
        """
        statements = []

        # Find all boundary positions
        boundaries = self._find_boundaries(text)
        boundaries.append(len(text))  # Add end of text

        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]

            segment_text = text[start:end].strip()
            if not segment_text or len(segment_text) < 20:
                continue

            # Identify MP for this segment
            mp_match = self.mp_identifier.identify(segment_text[:200])

            statement = Statement(
                text=segment_text,
                mp_id=mp_match.mp_id if mp_match else None,
                start_pos=start,
                end_pos=end,
            )
            statements.append(statement)

        return statements

    def _find_boundaries(self, text: str) -> list[int]:
        """
        Find all statement boundary positions.

        Args:
            text: Text to search for boundaries

        Returns:
            Sorted list of boundary positions
        """
        boundaries = [0]  # Start of text

        for pattern in self.boundary_patterns:
            for match in pattern.finditer(text):
                pos = match.start()
                if pos not in boundaries:
                    boundaries.append(pos)

        return sorted(boundaries)

    def clean_statement(self, text: str) -> str:
        """
        Clean statement text.

        Removes:
        - Page numbers
        - Excessive whitespace
        - Header/footer artifacts

        Args:
            text: Statement text to clean

        Returns:
            Cleaned text
        """
        # Remove page numbers
        text = re.sub(r"\n\d+\n", "\n", text)

        # Remove excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)

        # Remove header/footer artifacts
        text = re.sub(r"NATIONAL ASSEMBLY.*?\n", "", text)

        return text.strip()
