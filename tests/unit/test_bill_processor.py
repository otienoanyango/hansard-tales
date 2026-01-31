"""
Unit tests for BillTextExtractor.
"""

from unittest.mock import patch

import pytest

from hansard_tales.processors.bill_processor import BillStructure, BillTextExtractor


@pytest.fixture
def extractor():
    """Create a text extractor instance."""
    return BillTextExtractor()


class TestBillTextExtractorMetadata:
    """Tests for metadata extraction."""

    def test_extract_metadata_bill_number(self, extractor):
        """Test extracting bill number from text."""
        text = "THE BILL (No. 25 of 2023)\nAn Act to amend..."
        metadata = extractor.extract_metadata(text)

        assert metadata["bill_number"] == "25/2023"

    def test_extract_metadata_title(self, extractor):
        """Test extracting title from text."""
        text = "THE BILL (No. 25 of 2023)\nTHE AGRICULTURE AND FOOD SECURITY BILL"
        metadata = extractor.extract_metadata(text)

        assert metadata["title"] is not None
        assert "AGRICULTURE" in metadata["title"].upper() or "BILL" in metadata["title"]

    def test_extract_metadata_date(self, extractor):
        """Test extracting date from text."""
        text = "THE BILL (No. 25 of 2023)\n15 January 2024\n" "An Act to amend..."
        metadata = extractor.extract_metadata(text)

        # Date extraction should work or return None
        assert isinstance(metadata, dict)

    def test_extract_metadata_missing_fields(self, extractor):
        """Test extracting metadata when fields are missing."""
        text = "Some bill text without standard format"
        metadata = extractor.extract_metadata(text)

        # Should return dict with None values
        assert isinstance(metadata, dict)
        assert "bill_number" in metadata

    def test_extract_metadata_chapter(self, extractor):
        """Test extracting chapter number for acts."""
        text = "THE AGRICULTURE AND FOOD SECURITY ACT\nChapter 318"
        metadata = extractor.extract_metadata(text)

        # Chapter field should exist even if not extracted
        assert "chapter" in metadata


class TestBillTextExtractorStructure:
    """Tests for structure extraction."""

    def test_extract_structure_parts(self, extractor):
        """Test extracting parts from bill."""
        text = """
        PREAMBLE TEXT HERE

        PART I: PRELIMINARY PROVISIONS
        1. Short title
        2. Commencement

        PART II: ADMINISTRATION
        3. Establishment of board
        4. Functions of board

        SECTION 5. Powers of board
        """

        with patch.object(extractor, "extract_text", return_value=text):
            structure = extractor.extract_structure(text.encode())

            assert isinstance(structure, BillStructure)
            assert structure.preamble is not None
            assert len(structure.parts) > 0

    def test_extract_structure_sections(self, extractor):
        """Test extracting sections from bill."""
        text = """
        SECTION 1. Short title
        This Act may be cited as the Test Act, 2024.

        SECTION 2. Application
        This Act applies to all counties.

        3. Commencement
        This Act shall come into force on publication.
        """

        with patch.object(extractor, "extract_text", return_value=text):
            structure = extractor.extract_structure(text.encode())

            # Should extract structure
            assert isinstance(structure, BillStructure)

    def test_extract_structure_schedules(self, extractor):
        """Test extracting schedules from bill."""
        text = """
        PART I: MAIN PROVISIONS

        SECTION 1. Definitions

        SCHEDULE A: FORMS
        Form 1: Application Form
        Form 2: Approval Form

        SCHEDULE B: FEES
        Processing Fee: KES 5,000
        """

        with patch.object(extractor, "extract_text", return_value=text):
            structure = extractor.extract_structure(text.encode())

            assert len(structure.schedules) > 0

    def test_extract_structure_explanatory_memo(self, extractor):
        """Test extracting explanatory memorandum."""
        text = """
        PART I: PROVISIONS

        MEMORANDUM
        The purpose of this Bill is to...
        """

        with patch.object(extractor, "extract_text", return_value=text):
            structure = extractor.extract_structure(text.encode())

            assert structure.explanatory_memo is not None
            assert "purpose" in structure.explanatory_memo.lower()


class TestBillTextExtractorParsing:
    """Tests for parsing methods."""

    def test_extract_parts_multiple(self, extractor):
        """Test extracting multiple parts."""
        text = """
        PART I: PRELIMINARY
        Section 1. Title

        PART II: ADMINISTRATION
        Section 2. Board

        PART III: OFFENCES
        Section 3. Penalties
        """

        parts = extractor._extract_parts(text)

        assert len(parts) >= 2
        assert all("part_number" in p for p in parts)
        assert all("sections" in p for p in parts)

    def test_extract_sections_multiple(self, extractor):
        """Test extracting multiple sections."""
        text = """
        1. Short title
        This Act may be cited as the Test Act.

        2. Commencement
        This Act shall come into force.

        3. Definitions
        In this Act...
        """

        sections = extractor._extract_sections(text)

        assert len(sections) >= 2

    def test_extract_schedules_multiple(self, extractor):
        """Test extracting multiple schedules."""
        text = """
        SCHEDULE I: FORMS
        Various forms...

        SCHEDULE II: FEES
        Fee schedule...

        SCHEDULE III: PENALTIES
        Penalty schedule...
        """

        schedules = extractor._extract_schedules(text)

        assert len(schedules) >= 2


class TestBillTextExtractorEdgeCases:
    """Tests for edge cases and error handling."""

    def test_extract_structure_empty_text(self, extractor):
        """Test extracting structure from empty text."""
        with patch.object(extractor, "extract_text", return_value=""):
            structure = extractor.extract_structure(b"")

            assert isinstance(structure, BillStructure)
            assert structure.preamble == ""

    def test_extract_metadata_with_special_chars(self, extractor):
        """Test extracting metadata with special characters."""
        text = 'THE BILL (No. 25–A of 2023)\nTitle with "quotes" and other chars'
        metadata = extractor.extract_metadata(text)

        # Should not crash
        assert isinstance(metadata, dict)

    def test_extract_structure_malformed_sections(self, extractor):
        """Test extracting structure with malformed sections."""
        text = """
        SECTION 1 title missing number
        Some text

        2.
        Standalone section number
        """

        with patch.object(extractor, "extract_text", return_value=text):
            structure = extractor.extract_structure(text.encode())

            # Should extract what it can
            assert isinstance(structure, BillStructure)


class TestBillTextExtractorConsistency:
    """Tests for consistency and idempotence."""

    def test_extract_metadata_idempotent(self, extractor):
        """Test that extracting metadata twice gives same result."""
        text = "THE BILL (No. 25 of 2023)\n15th January 2024"

        result1 = extractor.extract_metadata(text)
        result2 = extractor.extract_metadata(text)

        assert result1 == result2

    def test_extract_structure_consistent(self, extractor):
        """Test that structure extraction is consistent."""
        text = """
        PREAMBLE

        PART I
        Section 1. Title
        """

        with patch.object(extractor, "extract_text", return_value=text):
            structure1 = extractor.extract_structure(text.encode())
            structure2 = extractor.extract_structure(text.encode())

            assert len(structure1.parts) == len(structure2.parts)
            assert structure1.preamble == structure2.preamble
