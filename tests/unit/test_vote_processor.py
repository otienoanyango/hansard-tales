"""Unit tests for VoteProcessor."""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from hansard_tales.analysis.mp_identifier import MPMatch
from hansard_tales.processors.vote_processor import (
    MPVote,
    VoteProcessor,
    VoteRecord,
)


class TestMPVote:
    """Test MPVote dataclass."""

    def test_mp_vote_creation(self):
        """Test creating MPVote instance."""
        vote = MPVote(mp_id="mp-123", vote="aye")

        assert vote.mp_id == "mp-123"
        assert vote.vote == "aye"

    def test_mp_vote_types(self):
        """Test all valid vote types."""
        valid_votes = ["aye", "no", "abstain", "absent"]

        for vote_type in valid_votes:
            vote = MPVote(mp_id="mp-123", vote=vote_type)
            assert vote.vote == vote_type


class TestVoteRecord:
    """Test VoteRecord dataclass."""

    def test_vote_record_creation(self):
        """Test creating VoteRecord instance."""
        mp_votes = [
            MPVote(mp_id="mp-1", vote="aye"),
            MPVote(mp_id="mp-2", vote="no"),
        ]

        record = VoteRecord(
            vote_id="vote-123",
            session_id="session-456",
            date=date(2024, 1, 15),
            motion_text="Motion to approve budget",
            vote_type="division",
            result="passed",
            ayes=10,
            noes=5,
            abstentions=2,
            mp_votes=mp_votes,
        )

        assert record.vote_id == "vote-123"
        assert record.session_id == "session-456"
        assert record.date == date(2024, 1, 15)
        assert record.motion_text == "Motion to approve budget"
        assert record.vote_type == "division"
        assert record.result == "passed"
        assert record.ayes == 10
        assert record.noes == 5
        assert record.abstentions == 2
        assert len(record.mp_votes) == 2

    def test_vote_record_default_mp_votes(self):
        """Test VoteRecord with default empty mp_votes."""
        record = VoteRecord(
            vote_id="vote-123",
            session_id="session-456",
            date=date(2024, 1, 15),
            motion_text="Test motion",
            vote_type="division",
            result="passed",
            ayes=0,
            noes=0,
            abstentions=0,
        )

        assert record.mp_votes == []


class TestVoteProcessor:
    """Test VoteProcessor class."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return Mock()

    @pytest.fixture
    def mock_mp_identifier(self):
        """Create mock MP identifier."""
        identifier = Mock()
        identifier.identify = Mock(
            return_value=MPMatch(
                mp_id="mp-123",
                name="John Doe",
                confidence=0.95,
                constituency="Test Constituency",
                party="Test Party",
            )
        )
        return identifier

    @pytest.fixture
    def processor(self, mock_db_session, mock_mp_identifier):
        """Create VoteProcessor instance."""
        return VoteProcessor(mock_db_session, mock_mp_identifier)

    def test_initialization(self, mock_db_session, mock_mp_identifier):
        """Test VoteProcessor initialization."""
        processor = VoteProcessor(mock_db_session, mock_mp_identifier)

        assert processor.db == mock_db_session
        assert processor.mp_identifier == mock_mp_identifier

    def test_is_vote_table_with_valid_table(self, processor):
        """Test vote table detection with valid table."""
        table = [
            ["MP Name", "Vote", "Constituency"],
            ["John Doe", "Aye", "Nairobi"],
            ["Jane Smith", "No", "Mombasa"],
        ]

        assert processor._is_vote_table(table) is True

    def test_is_vote_table_with_ayes_noes_header(self, processor):
        """Test vote table detection with ayes/noes header."""
        table = [
            ["Ayes", "Noes"],
            ["John Doe", ""],
            ["", "Jane Smith"],
        ]

        assert processor._is_vote_table(table) is True

    def test_is_vote_table_with_division_header(self, processor):
        """Test vote table detection with division header."""
        table = [
            ["Division Results"],
            ["John Doe - Aye"],
        ]

        assert processor._is_vote_table(table) is True

    def test_is_vote_table_with_empty_table(self, processor):
        """Test vote table detection with empty table."""
        assert processor._is_vote_table([]) is False
        assert processor._is_vote_table([[]]) is False

    def test_is_vote_table_with_non_vote_table(self, processor):
        """Test vote table detection with non-vote table."""
        table = [
            ["Name", "Age", "Location"],
            ["John", "30", "Nairobi"],
        ]

        assert processor._is_vote_table(table) is False

    def test_parse_vote_value_aye(self, processor):
        """Test parsing 'aye' vote values."""
        assert processor._parse_vote_value("Aye") == "aye"
        assert processor._parse_vote_value("aye") == "aye"
        assert processor._parse_vote_value("AYE") == "aye"
        assert processor._parse_vote_value("Yes") == "aye"
        assert processor._parse_vote_value("yes") == "aye"

    def test_parse_vote_value_no(self, processor):
        """Test parsing 'no' vote values."""
        assert processor._parse_vote_value("No") == "no"
        assert processor._parse_vote_value("no") == "no"
        assert processor._parse_vote_value("NO") == "no"
        assert processor._parse_vote_value("Nay") == "no"
        assert processor._parse_vote_value("nay") == "no"

    def test_parse_vote_value_abstain(self, processor):
        """Test parsing 'abstain' vote values."""
        assert processor._parse_vote_value("Abstain") == "abstain"
        assert processor._parse_vote_value("abstain") == "abstain"
        assert processor._parse_vote_value("ABSTAIN") == "abstain"

    def test_parse_vote_value_absent(self, processor):
        """Test parsing 'absent' or unknown vote values."""
        assert processor._parse_vote_value("Absent") == "absent"
        assert processor._parse_vote_value("") == "absent"
        assert processor._parse_vote_value("Not Present") == "absent"

    def test_parse_vote_table_with_valid_data(self, processor, mock_mp_identifier):
        """Test parsing vote table with valid data."""
        table = [
            ["MP Name", "Vote"],
            ["John Doe", "Aye"],
            ["Jane Smith", "No"],
            ["Bob Johnson", "Abstain"],
        ]

        # Mock MP identifier to return different MPs
        mock_mp_identifier.identify.side_effect = [
            MPMatch(mp_id="mp-1", name="John Doe", confidence=0.95),
            MPMatch(mp_id="mp-2", name="Jane Smith", confidence=0.95),
            MPMatch(mp_id="mp-3", name="Bob Johnson", confidence=0.95),
        ]

        result = processor._parse_vote_table(table)

        assert result is not None
        assert len(result.mp_votes) == 3
        assert result.ayes == 1
        assert result.noes == 1
        assert result.abstentions == 1
        assert result.result == "failed"  # 1 aye vs 1 no

    def test_parse_vote_table_passed_result(self, processor, mock_mp_identifier):
        """Test vote table parsing with passed result."""
        table = [
            ["MP Name", "Vote"],
            ["MP 1", "Aye"],
            ["MP 2", "Aye"],
            ["MP 3", "No"],
        ]

        mock_mp_identifier.identify.side_effect = [
            MPMatch(mp_id=f"mp-{i}", name=f"MP {i}", confidence=0.95) for i in range(1, 4)
        ]

        result = processor._parse_vote_table(table)

        assert result is not None
        assert result.ayes == 2
        assert result.noes == 1
        assert result.result == "passed"

    def test_parse_vote_table_with_unmatched_mp(self, processor, mock_mp_identifier):
        """Test parsing vote table with unmatched MP."""
        table = [
            ["MP Name", "Vote"],
            ["John Doe", "Aye"],
            ["Unknown MP", "No"],
        ]

        # First MP matches, second doesn't
        mock_mp_identifier.identify.side_effect = [
            MPMatch(mp_id="mp-1", name="John Doe", confidence=0.95),
            None,
        ]

        result = processor._parse_vote_table(table)

        assert result is not None
        assert len(result.mp_votes) == 1  # Only matched MP
        assert result.ayes == 1
        assert result.noes == 0

    def test_parse_vote_table_with_empty_rows(self, processor):
        """Test parsing vote table with empty rows."""
        table = [
            ["MP Name", "Vote"],
            ["", ""],
            ["John Doe", "Aye"],
            [None, None],
        ]

        result = processor._parse_vote_table(table)

        assert result is not None
        assert len(result.mp_votes) == 1

    def test_parse_vote_table_with_empty_table(self, processor):
        """Test parsing empty vote table."""
        assert processor._parse_vote_table([]) is None
        assert processor._parse_vote_table([[]]) is None

    @patch("pdfplumber.open")
    def test_process_pdf_success(self, mock_pdfplumber, processor, mock_mp_identifier):
        """Test successful PDF processing."""
        # Create mock PDF with pages and tables
        mock_page = Mock()
        mock_page.extract_tables.return_value = [
            [
                ["MP Name", "Vote"],
                ["John Doe", "Aye"],
                ["Jane Smith", "No"],
            ]
        ]

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value.pages = [mock_page]
        mock_pdfplumber.return_value = mock_pdf

        mock_mp_identifier.identify.side_effect = [
            MPMatch(mp_id="mp-1", name="John Doe", confidence=0.95),
            MPMatch(mp_id="mp-2", name="Jane Smith", confidence=0.95),
        ]

        pdf_path = Path("test.pdf")

        with patch.object(Path, "exists", return_value=True):
            results = processor.process_pdf(pdf_path)

        assert len(results) == 1
        assert results[0].ayes == 1
        assert results[0].noes == 1

    @patch("pdfplumber.open")
    def test_process_pdf_multiple_tables(self, mock_pdfplumber, processor, mock_mp_identifier):
        """Test PDF processing with multiple vote tables."""
        mock_page = Mock()
        mock_page.extract_tables.return_value = [
            [["MP Name", "Vote"], ["MP 1", "Aye"]],
            [["Name", "Age"]],  # Non-vote table
            [["MP Name", "Vote"], ["MP 2", "No"]],
        ]

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value.pages = [mock_page]
        mock_pdfplumber.return_value = mock_pdf

        mock_mp_identifier.identify.side_effect = [
            MPMatch(mp_id="mp-1", name="MP 1", confidence=0.95),
            MPMatch(mp_id="mp-2", name="MP 2", confidence=0.95),
        ]

        pdf_path = Path("test.pdf")

        with patch.object(Path, "exists", return_value=True):
            results = processor.process_pdf(pdf_path)

        assert len(results) == 2

    def test_process_pdf_file_not_found(self, processor):
        """Test PDF processing with non-existent file."""
        pdf_path = Path("nonexistent.pdf")

        with pytest.raises(FileNotFoundError, match="PDF not found"):
            processor.process_pdf(pdf_path)

    @patch("pdfplumber.open")
    def test_process_pdf_processing_error(self, mock_pdfplumber, processor):
        """Test PDF processing with error."""
        mock_pdfplumber.side_effect = Exception("PDF error")

        pdf_path = Path("test.pdf")

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(ValueError, match="Failed to process PDF"):
                processor.process_pdf(pdf_path)

    @patch("pdfplumber.open")
    def test_process_pdf_no_vote_tables(self, mock_pdfplumber, processor):
        """Test PDF processing with no vote tables."""
        mock_page = Mock()
        mock_page.extract_tables.return_value = [
            [["Name", "Age"], ["John", "30"]],
        ]

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value.pages = [mock_page]
        mock_pdfplumber.return_value = mock_pdf

        pdf_path = Path("test.pdf")

        with patch.object(Path, "exists", return_value=True):
            results = processor.process_pdf(pdf_path)

        assert len(results) == 0
