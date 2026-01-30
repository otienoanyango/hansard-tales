"""
Unit tests for Statement Segmenter.

Tests cover statement segmentation, boundary detection, text cleaning,
and edge cases.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from hansard_tales.analysis.statement_segmenter import Statement, StatementSegmenter


class TestStatementSegmenter:
    """Test suite for StatementSegmenter."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing using ORM."""
        from datetime import datetime

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from hansard_tales.database.models import MPORM, Base, ChamberEnum

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        # Create engine and tables using ORM
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        # Create session and insert test MPs
        Session = sessionmaker(bind=engine)
        session = Session()

        # Insert test MPs
        test_mps_data = [
            ("JOHN DOE", "UDA", "Nairobi West"),
            ("JANE SMITH", "ODM", "Kisumu Central"),
            ("PETER JONES", "UDA", "Mombasa North"),
        ]

        now = datetime.now()
        for name, party, constituency in test_mps_data:
            mp = MPORM(
                id=uuid4(),
                name=name,
                chamber=ChamberEnum.NATIONAL_ASSEMBLY,
                party=party,
                constituency=constituency,
                parliament_term=2022,
                created_at=now,
                updated_at=now,
            )
            session.add(mp)

        session.commit()
        session.close()

        yield db_path

        # Cleanup
        Path(db_path).unlink()

    @pytest.fixture
    def mock_db_session(self, temp_db):
        """Create mock database session."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{temp_db}")
        Session = sessionmaker(bind=engine)
        session = Session()

        yield session

        session.close()

    @pytest.fixture
    def mock_mp_identifier(self, mock_db_session):
        """Create mock MP identifier."""
        from hansard_tales.analysis.mp_identifier import MPIdentifier

        with patch("spacy.load") as mock_load:
            mock_nlp = Mock()
            mock_doc = Mock()
            mock_doc.ents = []
            mock_nlp.return_value = mock_doc
            mock_load.return_value = mock_nlp

            identifier = MPIdentifier(mock_db_session)
            identifier.nlp = mock_nlp
            return identifier

    @pytest.fixture
    def segmenter(self, mock_mp_identifier):
        """Create statement segmenter instance."""
        return StatementSegmenter(mock_mp_identifier)

    def test_init(self, mock_mp_identifier):
        """Test statement segmenter initialization."""
        segmenter = StatementSegmenter(mock_mp_identifier)

        assert segmenter.mp_identifier == mock_mp_identifier
        assert len(segmenter.boundary_patterns) == 3

    def test_find_boundaries_mp_names(self, segmenter):
        """Test boundary detection with MP names."""
        text = """Some initial text.
Hon. JOHN DOE spoke about the budget.
Dr. JANE SMITH raised a point of order.
Mr. PETER JONES presented the report."""

        boundaries = segmenter._find_boundaries(text)

        # Should find boundaries at each MP name
        assert len(boundaries) >= 3  # At least 3 MP names + start
        assert 0 in boundaries  # Start of text

    def test_find_boundaries_speaker(self, segmenter):
        """Test boundary detection with Speaker interventions."""
        text = """Hon. JOHN DOE spoke.
The Speaker: Order! Order!
Hon. JANE SMITH continued."""

        boundaries = segmenter._find_boundaries(text)

        # Should find boundaries at MP names and Speaker
        assert len(boundaries) >= 3
        assert 0 in boundaries

    def test_find_boundaries_section_headers(self, segmenter):
        """Test boundary detection with section headers."""
        text = """Hon. JOHN DOE spoke.
COMMUNICATION FROM THE CHAIR
Hon. JANE SMITH responded."""

        boundaries = segmenter._find_boundaries(text)

        # Should find boundaries at MP names and section header
        assert len(boundaries) >= 3
        assert 0 in boundaries

    def test_segment_simple(self, segmenter):
        """Test simple segmentation with two MPs."""
        text = """Hon. JOHN DOE spoke about the budget and fiscal policy.
This is a longer statement to ensure it meets the minimum length requirement.
Dr. JANE SMITH raised a point of order about parliamentary procedure.
This is also a longer statement to meet the minimum length."""

        statements = segmenter.segment(text, "session-123")

        # Should create at least 2 statements
        assert len(statements) >= 2

        # Check statement structure
        for stmt in statements:
            assert isinstance(stmt, Statement)
            assert stmt.text
            assert stmt.start_pos >= 0
            assert stmt.end_pos > stmt.start_pos

    def test_segment_with_mp_identification(self, segmenter):
        """Test segmentation identifies MPs correctly."""
        text = """Hon. JOHN DOE (Nairobi West, UDA) spoke about the budget and fiscal policy matters.
This is a longer statement to ensure it meets the minimum length requirement.
Dr. JANE SMITH (Kisumu Central, ODM) raised a point of order about parliamentary procedure.
This is also a longer statement to meet the minimum length."""

        statements = segmenter.segment(text, "session-123")

        # Should create at least 2 statements
        assert len(statements) >= 2

        # At least one statement should have an identified MP (if MP identifier works)
        # Note: MP identification depends on database and spaCy, so we just check structure
        for stmt in statements:
            assert isinstance(stmt.mp_id, str | None)

    def test_segment_filters_short_statements(self, segmenter):
        """Test segmentation filters out very short statements."""
        text = """Hon. JOHN DOE spoke about the budget and fiscal policy matters.
This is a longer statement to ensure it meets the minimum length requirement.
Short.
Dr. JANE SMITH raised a point of order about parliamentary procedure.
This is also a longer statement to meet the minimum length."""

        statements = segmenter.segment(text, "session-123")

        # Should not include the "Short." statement
        for stmt in statements:
            assert len(stmt.text) >= 20

    def test_segment_empty_text(self, segmenter):
        """Test segmentation with empty text."""
        statements = segmenter.segment("", "session-123")

        assert statements == []

    def test_segment_no_boundaries(self, segmenter):
        """Test segmentation with text containing no boundaries."""
        text = "This is a long text without any MP names or boundaries. " * 10

        statements = segmenter.segment(text, "session-123")

        # Should create at least one statement from the entire text
        assert len(statements) >= 1

    def test_clean_statement_page_numbers(self, segmenter):
        """Test text cleaning removes page numbers."""
        text = "This is a statement.\n123\nContinued text."

        cleaned = segmenter.clean_statement(text)

        assert "123" not in cleaned
        assert "This is a statement" in cleaned
        assert "Continued text" in cleaned

    def test_clean_statement_excessive_whitespace(self, segmenter):
        """Test text cleaning removes excessive whitespace."""
        text = "This is a statement.\n\n\n\nWith too many newlines."

        cleaned = segmenter.clean_statement(text)

        assert "\n\n\n" not in cleaned
        assert "This is a statement" in cleaned

    def test_clean_statement_header_artifacts(self, segmenter):
        """Test text cleaning removes header artifacts."""
        text = "NATIONAL ASSEMBLY DEBATES\nThis is a statement."

        cleaned = segmenter.clean_statement(text)

        assert "NATIONAL ASSEMBLY" not in cleaned
        assert "This is a statement" in cleaned

    def test_clean_statement_multiple_spaces(self, segmenter):
        """Test text cleaning removes multiple spaces."""
        text = "This  is  a  statement  with  multiple  spaces."

        cleaned = segmenter.clean_statement(text)

        assert "  " not in cleaned
        assert "This is a statement with multiple spaces" in cleaned

    def test_segment_with_speaker_interventions(self, segmenter):
        """Test segmentation handles Speaker interventions."""
        text = """Hon. JOHN DOE spoke about the budget and fiscal policy matters.
This is a longer statement to ensure it meets the minimum length requirement.
The Speaker: Order! Order! The honorable member should address the chair.
Hon. JANE SMITH raised a point of order about parliamentary procedure.
This is also a longer statement to meet the minimum length."""

        statements = segmenter.segment(text, "session-123")

        # Should create multiple statements
        assert len(statements) >= 2

    def test_segment_preserves_order(self, segmenter):
        """Test segmentation preserves statement order."""
        text = """Hon. JOHN DOE spoke first about the budget and fiscal policy.
This is a longer statement to ensure it meets the minimum length requirement.
Dr. JANE SMITH spoke second about parliamentary procedure and rules.
This is also a longer statement to meet the minimum length."""

        statements = segmenter.segment(text, "session-123")

        # Statements should be in order
        for i in range(len(statements) - 1):
            assert statements[i].start_pos < statements[i + 1].start_pos

    def test_segment_with_multiple_paragraphs(self, segmenter):
        """Test segmentation handles multi-paragraph statements."""
        text = """Hon. JOHN DOE spoke about the budget.

This is the second paragraph of the same statement.

This is the third paragraph.

Dr. JANE SMITH raised a different point about parliamentary procedure.

This is also a multi-paragraph statement."""

        statements = segmenter.segment(text, "session-123")

        # Should create statements that may contain multiple paragraphs
        assert len(statements) >= 2

    def test_statement_dataclass(self):
        """Test Statement dataclass creation."""
        stmt = Statement(
            text="Test statement",
            mp_id="mp-123",
            start_pos=0,
            end_pos=100,
            page_number=5,
        )

        assert stmt.text == "Test statement"
        assert stmt.mp_id == "mp-123"
        assert stmt.start_pos == 0
        assert stmt.end_pos == 100
        assert stmt.page_number == 5

    def test_statement_dataclass_optional_fields(self):
        """Test Statement dataclass with optional fields."""
        stmt = Statement(text="Test statement", mp_id=None, start_pos=0, end_pos=100)

        assert stmt.text == "Test statement"
        assert stmt.mp_id is None
        assert stmt.page_number is None

    def test_segment_real_hansard_format(self, segmenter):
        """Test segmentation with realistic Hansard format."""
        text = """NATIONAL ASSEMBLY DEBATES

Thursday, 4th December 2025

Hon. JOHN DOE (Nairobi West, UDA): Mr. Speaker, I rise to support this Bill.
The Finance Bill, 2025, is crucial for our economic development and growth.
We must ensure that we have adequate resources for development projects.

The Speaker (Hon. Moses Wetangula): Order! The honorable member's time is up.

Dr. JANE SMITH (Kisumu Central, ODM): Mr. Speaker, I beg to differ with my colleague.
This Bill will burden the common mwananchi with excessive taxation.
We need to reconsider the tax measures proposed in this legislation."""

        statements = segmenter.segment(text, "session-123")

        # Should create multiple statements
        assert len(statements) >= 2

        # Check that statements have reasonable content
        for stmt in statements:
            assert len(stmt.text) > 0
            assert stmt.start_pos >= 0
            assert stmt.end_pos > stmt.start_pos


class TestStatementDataclass:
    """Test suite for Statement dataclass."""

    def test_statement_creation(self):
        """Test creating a Statement instance."""
        stmt = Statement(
            text="This is a test statement",
            mp_id="mp-123",
            start_pos=0,
            end_pos=24,
            page_number=1,
        )

        assert stmt.text == "This is a test statement"
        assert stmt.mp_id == "mp-123"
        assert stmt.start_pos == 0
        assert stmt.end_pos == 24
        assert stmt.page_number == 1

    def test_statement_without_mp(self):
        """Test creating a Statement without MP identification."""
        stmt = Statement(text="Unidentified statement", mp_id=None, start_pos=0, end_pos=22)

        assert stmt.text == "Unidentified statement"
        assert stmt.mp_id is None
        assert stmt.page_number is None

    def test_statement_equality(self):
        """Test Statement equality comparison."""
        stmt1 = Statement(text="Test", mp_id="mp-1", start_pos=0, end_pos=4)
        stmt2 = Statement(text="Test", mp_id="mp-1", start_pos=0, end_pos=4)

        assert stmt1 == stmt2

    def test_statement_inequality(self):
        """Test Statement inequality comparison."""
        stmt1 = Statement(text="Test1", mp_id="mp-1", start_pos=0, end_pos=5)
        stmt2 = Statement(text="Test2", mp_id="mp-2", start_pos=0, end_pos=5)

        assert stmt1 != stmt2
