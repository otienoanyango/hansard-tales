"""
Bill text extraction and structure parsing.

This module implements extraction of text, metadata, and structure from
parliamentary bill PDFs.
"""

import re
from dataclasses import dataclass
from typing import Optional

import pdfplumber


@dataclass
class BillSection:
    """A section of a bill."""

    section_number: str
    title: str
    text: str
    subsections: list["BillSection"]


@dataclass
class BillStructure:
    """Parsed structure of a bill."""

    preamble: str
    parts: list[dict]
    schedules: list[dict]
    explanatory_memo: Optional[str]


class BillTextExtractor:
    """
    Extractor for bill PDF text and structure.

    This extractor handles:
    - Text extraction from PDF files
    - Metadata extraction (title, date, etc.)
    - Structure parsing (parts, sections, schedules)
    - Explanatory memo extraction

    Example:
        >>> extractor = BillTextExtractor()
        >>> structure = extractor.extract_structure(pdf_content)
    """

    def __init__(self):
        """Initialize the extractor."""
        self.logger = self._get_logger()

    def _get_logger(self):
        """Get logger instance."""
        import logging

        return logging.getLogger(self.__class__.__name__)

    def extract_text(self, pdf_content: bytes) -> str:
        """
        Extract all text from PDF.

        Args:
            pdf_content: PDF file content as bytes

        Returns:
            Extracted text

        Raises:
            ValueError: If PDF is invalid or unreadable
        """
        try:
            import io

            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                    text += "\n"
                return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {e}") from e

    def extract_metadata(self, text: str) -> dict:
        """
        Extract metadata from bill text.

        Extracts:
        - Bill number
        - Title
        - Date
        - Chapter (for bills that are acts)

        Args:
            text: Full bill text

        Returns:
            Dictionary with metadata keys
        """
        metadata = {
            "bill_number": None,
            "title": None,
            "date": None,
            "chapter": None,
        }

        # Extract bill number (e.g., "THE BILL (No. 25 of 2023)")
        bill_num_match = re.search(r"THE (?:BILL|ACT).*?(?:No\.?\s*)?(\d+)\s*of\s*(\d{4})", text)
        if bill_num_match:
            metadata["bill_number"] = f"{bill_num_match.group(1)}/{bill_num_match.group(2)}"

        # Extract title (usually first few lines after preamble)
        lines = text.split("\n")
        for i, line in enumerate(lines[:20]):
            if "BILL" in line.upper() and len(line.strip()) > 10:
                metadata["title"] = line.strip()
                break

        # Extract date
        date_match = re.search(
            r"\b(\d{1,2})[th|st|nd|rd]?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
            text,
            re.IGNORECASE,
        )
        if date_match:
            metadata["date"] = f"{date_match.group(1)} {date_match.group(2)}"

        return metadata

    def extract_structure(self, pdf_content: bytes) -> BillStructure:
        """
        Extract and parse bill structure.

        Identifies:
        - Preamble (introductory text)
        - Parts (major divisions)
        - Sections (legal provisions)
        - Schedules (attached tables/lists)
        - Explanatory memo

        Args:
            pdf_content: PDF file content as bytes

        Returns:
            BillStructure object with parsed components

        Raises:
            ValueError: If PDF is invalid
        """
        text = self.extract_text(pdf_content)

        # Extract preamble (before first "PART" or "SECTION")
        preamble_end = min(
            [i for i in [text.find("PART"), text.find("SECTION")] if i != -1],
            default=len(text) // 4,
        )
        preamble = text[:preamble_end].strip()

        # Extract parts
        parts = self._extract_parts(text)

        # Extract schedules
        schedules = self._extract_schedules(text)

        # Extract explanatory memo
        memo = self._extract_explanatory_memo(text)

        return BillStructure(
            preamble=preamble,
            parts=parts,
            schedules=schedules,
            explanatory_memo=memo,
        )

    def _extract_parts(self, text: str) -> list[dict]:
        """
        Extract parts from bill text.

        Args:
            text: Full bill text

        Returns:
            List of part dictionaries
        """
        parts = []

        # Find all "PART X" sections
        part_pattern = r"PART\s+([A-Z\d]+)[.—\-]?\s*(.+?)(?=PART\s+[A-Z\d]|SCHEDULE|$)"
        matches = re.finditer(part_pattern, text, re.IGNORECASE | re.DOTALL)

        for match in matches:
            part_num = match.group(1).strip()
            part_text = match.group(2).strip()

            # Extract sections within this part
            sections = self._extract_sections(part_text)

            parts.append(
                {
                    "part_number": part_num,
                    "text": part_text[:200],  # First 200 chars
                    "sections": sections,
                }
            )

        return parts

    def _extract_sections(self, text: str) -> list[dict]:
        """
        Extract sections from text.

        Args:
            text: Text containing sections

        Returns:
            List of section dictionaries
        """
        sections = []

        # Find all "Section X" or just numbers followed by periods
        section_pattern = r"(?:Section\s+)?(\d+)[.—\-]?\s*(.+?)(?=Section\s+\d|^\s*\d+\.|$)"
        matches = re.finditer(section_pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)

        for match in matches:
            section_num = match.group(1).strip()
            section_text = match.group(2).strip()

            sections.append(
                {
                    "section_number": section_num,
                    "text": section_text[:500],  # First 500 chars
                }
            )

        return sections

    def _extract_schedules(self, text: str) -> list[dict]:
        """
        Extract schedules from bill text.

        Args:
            text: Full bill text

        Returns:
            List of schedule dictionaries
        """
        schedules = []

        # Find all "SCHEDULE X" sections
        schedule_pattern = r"SCHEDULE\s+([A-Z\d]+)[.—\-]?\s*(.+?)(?=SCHEDULE\s+[A-Z\d]|$)"
        matches = re.finditer(schedule_pattern, text, re.IGNORECASE | re.DOTALL)

        for match in matches:
            schedule_num = match.group(1).strip()
            schedule_text = match.group(2).strip()

            schedules.append(
                {
                    "schedule_number": schedule_num,
                    "text": schedule_text[:1000],  # First 1000 chars
                }
            )

        return schedules

    def _extract_explanatory_memo(self, text: str) -> Optional[str]:
        """
        Extract explanatory memorandum.

        Args:
            text: Full bill text

        Returns:
            Explanatory memo text or None
        """
        # Look for "MEMORANDUM" or "EXPLANATORY NOTES"
        memo_start_patterns = [
            r"MEMORANDUM",
            r"EXPLANATORY\s+(?:MEMORANDUM|NOTES)",
        ]

        for pattern in memo_start_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract from memo start to end of document
                start = match.start()
                memo_text = text[start : start + 5000]  # First 5000 chars of memo
                return memo_text.strip()

        return None
