"""
Unit tests for session summary generator.

Tests the SessionSummaryGenerator class including:
- Statement aggregation
- Summary generation
- Structured parsing
- Batch processing
- Edge cases
"""

import json
import sqlite3
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

from hansard_tales.analysis.session_summary_generator import (
    SessionSummary,
    SessionSummaryGenerator,
)


@pytest.fixture
def temp_db():
    """Create temporary database with test data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute(
        """
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            date TEXT NOT NULL,
            session_type TEXT NOT NULL,
            chamber TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE mps (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            chamber TEXT NOT NULL,
            party TEXT,
            constituency TEXT,
            parliament_term INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE statements (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            mp_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp TEXT,
            source_url TEXT NOT NULL,
            source_hash TEXT NOT NULL,
            page_number INTEGER,
            line_number INTEGER,
            vector_doc_id TEXT NOT NULL,
            classification TEXT,
            statement_type TEXT,
            primary_topic TEXT,
            key_points TEXT,
            sentiment TEXT,
            quality_score REAL,
            topics TEXT,
            related_bill_ids TEXT,
            related_question_ids TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (mp_id) REFERENCES mps(id),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE bills (
            id TEXT PRIMARY KEY,
            bill_number TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            chamber TEXT NOT NULL,
            status TEXT NOT NULL,
            current_version INTEGER DEFAULT 1,
            sponsor_id TEXT NOT NULL,
            co_sponsor_ids TEXT,
            related_statement_ids TEXT,
            related_vote_ids TEXT,
            related_question_ids TEXT,
            related_petition_ids TEXT,
            topics TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (sponsor_id) REFERENCES mps(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE bill_statement_links (
            id TEXT PRIMARY KEY,
            bill_id TEXT NOT NULL,
            statement_id TEXT NOT NULL,
            mention_text TEXT,
            confidence REAL,
            context TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (bill_id) REFERENCES bills(id),
            FOREIGN KEY (statement_id) REFERENCES statements(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE vote_records (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            motion_text TEXT NOT NULL,
            vote_type TEXT NOT NULL,
            result TEXT NOT NULL,
            ayes INTEGER NOT NULL,
            noes INTEGER NOT NULL,
            abstentions INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """
    )

    # Insert test data
    now = datetime.now(UTC).isoformat()
    session_id = str(uuid4())
    mp_id = str(uuid4())
    bill_id = str(uuid4())

    cursor.execute(
        """
        INSERT INTO sessions (id, document_id, date, session_type, chamber, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (session_id, "doc-1", "2024-12-01", "morning", "national_assembly", now, now),
    )

    cursor.execute(
        """
        INSERT INTO mps (id, name, chamber, party, constituency, parliament_term, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (mp_id, "John Doe", "national_assembly", "UDA", "Nairobi West", 2022, now, now),
    )

    # Insert substantive statements
    for i in range(5):
        stmt_id = str(uuid4())
        cursor.execute(
            """
            INSERT INTO statements (
                id, document_id, mp_id, session_id, text, source_url, source_hash,
                vector_doc_id, classification, statement_type, primary_topic,
                key_points, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                stmt_id,
                "doc-1",
                mp_id,
                session_id,
                f"Statement {i} about healthcare",
                "http://example.com",
                "hash123",
                "vec-1",
                "substantive",
                "substantive",
                "Healthcare",
                json.dumps([f"Point {i}"]),
                now,
            ),
        )

    # Insert bill
    cursor.execute(
        """
        INSERT INTO bills (
            id, bill_number, title, chamber, status, sponsor_id,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            bill_id,
            "Bill-001",
            "Healthcare Bill 2024",
            "national_assembly",
            "active",
            mp_id,
            now,
            now,
        ),
    )

    # Link bill to statement
    cursor.execute(
        """
        INSERT INTO bill_statement_links (
            id, bill_id, statement_id, mention_text, confidence, created_at
        )
        SELECT ?, ?, id, 'Healthcare Bill', 0.9, ?
        FROM statements
        LIMIT 1
    """,
        (str(uuid4()), bill_id, now),
    )

    # Insert vote
    cursor.execute(
        """
        INSERT INTO vote_records (
            id, session_id, motion_text, vote_type, result,
            ayes, noes, abstentions, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            str(uuid4()),
            session_id,
            "Motion to pass Healthcare Bill",
            "division",
            "passed",
            150,
            50,
            10,
            now,
        ),
    )

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    Path(db_path).unlink()


@pytest.fixture
def mock_db_session(temp_db):
    """Create mock database session."""
    from unittest.mock import MagicMock

    session = MagicMock()

    # Mock query results
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Get session data
    cursor.execute("SELECT * FROM sessions LIMIT 1")
    session_row = cursor.fetchone()

    # Create mock session object
    mock_session = MagicMock()
    mock_session.id = session_row[0]
    mock_session.session_id = session_row[0]  # Add session_id attribute
    mock_session.date = date.fromisoformat(session_row[2])
    mock_session.doc_metadata = {"session_type": session_row[3]}

    # Get statements
    cursor.execute(
        """
        SELECT s.*, m.name
        FROM statements s
        JOIN mps m ON s.mp_id = m.id
        WHERE s.session_id = ?
    """,
        (session_row[0],),
    )
    statement_rows = cursor.fetchall()

    mock_statements = []
    for row in statement_rows:
        stmt = MagicMock()
        stmt.id = row[0]
        stmt.mp_id = row[2]
        stmt.session_id = row[3]
        stmt.text = row[4]
        stmt.primary_topic = row[11]
        # Handle key_points - check if it's a valid JSON string
        try:
            stmt.key_points = json.loads(row[12]) if row[12] else []
        except (json.JSONDecodeError, TypeError):
            stmt.key_points = []
        stmt.mp = MagicMock()
        stmt.mp.name = row[-1]
        mock_statements.append(stmt)

    # Setup query chain
    def query_side_effect(model):
        query_mock = MagicMock()

        if "Document" in str(model):
            filter_mock = MagicMock()
            filter_mock.first.return_value = mock_session
            query_mock.filter.return_value = filter_mock
        elif "Statement" in str(model):
            filter_mock = MagicMock()
            filter_mock.all.return_value = mock_statements
            query_mock.filter.return_value = filter_mock
        elif "Bill" in str(model):
            filter_mock = MagicMock()
            mock_bill = MagicMock()
            mock_bill.title = "Healthcare Bill 2024"
            filter_mock.all.return_value = [mock_bill]
            query_mock.filter.return_value = filter_mock
        elif "Vote" in str(model):
            filter_mock = MagicMock()
            mock_vote = MagicMock()
            mock_vote.motion_text = "Motion to pass Healthcare Bill"
            filter_mock.all.return_value = [mock_vote]
            query_mock.filter.return_value = filter_mock

        return query_mock

    session.query.side_effect = query_side_effect

    conn.close()
    return session


@pytest.fixture
def mock_llm():
    """Create mock LLM analyzer."""
    llm = Mock()
    llm.model = "claude-3-5-haiku-20241022"

    # Mock API response
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = json.dumps(
        {
            "title": "Healthcare Budget Debate",
            "summary": "The session focused on healthcare funding. MPs discussed the Healthcare Bill 2024.",
            "key_debates": ["Healthcare funding", "Rural hospital access", "Medical equipment"],
            "main_topics": ["Healthcare", "Budget", "Infrastructure"],
        }
    )
    mock_response.content = [mock_content]

    llm.client = Mock()
    llm.client.messages.create.return_value = mock_response

    return llm


class TestSessionSummaryDataclass:
    """Test SessionSummary dataclass."""

    def test_create_session_summary(self):
        """Test creating SessionSummary instance."""
        summary = SessionSummary(
            session_id="session-123",
            date=date(2024, 12, 1),
            session_type="morning",
            title="Healthcare Debate",
            summary="Discussion about healthcare funding",
            key_debates=["Healthcare funding", "Rural access"],
            bills_discussed=["Healthcare Bill 2024"],
            votes_held=["Motion to pass bill"],
            total_mps_present=150,
            total_statements=50,
            main_topics=["Healthcare", "Budget"],
        )

        assert summary.session_id == "session-123"
        assert summary.date == date(2024, 12, 1)
        assert summary.session_type == "morning"
        assert summary.title == "Healthcare Debate"
        assert len(summary.key_debates) == 2
        assert len(summary.bills_discussed) == 1
        assert summary.total_mps_present == 150

    def test_default_values(self):
        """Test default values for optional fields."""
        summary = SessionSummary(
            session_id="session-123",
            date=date(2024, 12, 1),
            session_type="morning",
            title="Test Session",
            summary="Test summary",
        )

        assert summary.key_debates == []
        assert summary.bills_discussed == []
        assert summary.votes_held == []
        assert summary.total_mps_present == 0
        assert summary.total_statements == 0
        assert summary.main_topics == []


class TestStatementAggregation:
    """Test statement aggregation."""

    def test_aggregate_statements(self, mock_db_session, mock_llm):
        """Test aggregating substantive statements."""
        generator = SessionSummaryGenerator(mock_db_session, mock_llm)

        # Get session ID from mock
        from hansard_tales.database.models import DocumentORM

        session_query = mock_db_session.query(DocumentORM)
        session = session_query.filter().first()
        session_id = session.session_id if hasattr(session, "session_id") else str(session.id)

        statements = generator._aggregate_statements(session_id)

        assert len(statements) == 5
        assert all(hasattr(s, "text") for s in statements)


class TestSummaryGeneration:
    """Test LLM summary generation."""

    def test_generate_llm_summary(self, mock_db_session, mock_llm):
        """Test generating summary with LLM."""
        generator = SessionSummaryGenerator(mock_db_session, mock_llm)

        # Create mock session and statements
        mock_session = Mock()
        mock_session.date = date(2024, 12, 1)
        mock_session.doc_metadata = {"session_type": "morning"}

        mock_statement = Mock()
        mock_statement.mp = Mock()
        mock_statement.mp.name = "John Doe"
        mock_statement.topics = {"primary": "Healthcare"}
        mock_statement.related_bill_ids = {"key_points": ["Point 1", "Point 2"]}

        summary_text = generator._generate_llm_summary(mock_session, [mock_statement])

        assert "Healthcare Budget Debate" in summary_text
        assert mock_llm.client.messages.create.called


class TestStructuredParsing:
    """Test structured parsing of LLM output."""

    def test_parse_summary_json(self, mock_db_session, mock_llm):
        """Test parsing JSON from LLM response."""
        generator = SessionSummaryGenerator(mock_db_session, mock_llm)

        mock_session = Mock()
        mock_session.id = "session-123"
        mock_session.session_id = "session-123"
        mock_session.date = date(2024, 12, 1)
        mock_session.doc_metadata = {"session_type": "morning"}

        mock_statement = Mock()
        mock_statement.id = "stmt-1"
        mock_statement.mp_id = "mp-1"

        summary_text = json.dumps(
            {
                "title": "Healthcare Debate",
                "summary": "Discussion about healthcare",
                "key_debates": ["Funding", "Access"],
                "main_topics": ["Healthcare", "Budget"],
            }
        )

        summary = generator._parse_summary(mock_session, [mock_statement], summary_text)

        assert summary.title == "Healthcare Debate"
        assert summary.summary == "Discussion about healthcare"
        assert len(summary.key_debates) == 2
        assert len(summary.main_topics) == 2

    def test_parse_summary_with_markdown(self, mock_db_session, mock_llm):
        """Test parsing JSON wrapped in markdown code blocks."""
        generator = SessionSummaryGenerator(mock_db_session, mock_llm)

        mock_session = Mock()
        mock_session.id = "session-123"
        mock_session.session_id = "session-123"
        mock_session.date = date(2024, 12, 1)
        mock_session.doc_metadata = {"session_type": "morning"}

        summary_text = """```json
{
  "title": "Healthcare Debate",
  "summary": "Discussion about healthcare",
  "key_debates": ["Funding"],
  "main_topics": ["Healthcare"]
}
```"""

        summary = generator._parse_summary(mock_session, [], summary_text)

        assert summary.title == "Healthcare Debate"

    def test_parse_summary_invalid_json(self, mock_db_session, mock_llm):
        """Test error handling for invalid JSON."""
        generator = SessionSummaryGenerator(mock_db_session, mock_llm)

        mock_session = Mock()
        mock_session.id = "session-123"
        mock_session.session_id = "session-123"
        mock_session.date = date(2024, 12, 1)
        mock_session.doc_metadata = {"session_type": "morning"}

        with pytest.raises(ValueError, match="No JSON found"):
            generator._parse_summary(mock_session, [], "Not valid JSON")


class TestBatchProcessing:
    """Test batch summary generation."""

    def test_generate_batch(self, mock_db_session, mock_llm):
        """Test generating summaries for multiple sessions."""
        generator = SessionSummaryGenerator(mock_db_session, mock_llm)

        # Get session ID from mock
        from hansard_tales.database.models import DocumentORM

        session_query = mock_db_session.query(DocumentORM)
        session = session_query.filter().first()
        session_id = session.session_id if hasattr(session, "session_id") else str(session.id)

        summaries = generator.generate_batch([session_id, session_id])

        assert len(summaries) == 2
        assert all(isinstance(s, SessionSummary) for s in summaries)

    def test_generate_batch_with_errors(self, mock_db_session, mock_llm):
        """Test batch generation with some failures."""
        generator = SessionSummaryGenerator(mock_db_session, mock_llm)

        # Mix valid and invalid session IDs
        summaries = generator.generate_batch(["valid-id", "invalid-id"])

        assert len(summaries) == 2
        # Second summary should be error summary
        assert "Error" in summaries[1].title


class TestEdgeCases:
    """Test edge cases."""

    def test_session_not_found(self, mock_db_session, mock_llm):
        """Test error when session doesn't exist."""
        generator = SessionSummaryGenerator(mock_db_session, mock_llm)

        # Mock query to return None
        from hansard_tales.database.models import DocumentORM

        session_query = mock_db_session.query(DocumentORM)
        filter_mock = session_query.filter.return_value
        filter_mock.first.return_value = None

        with pytest.raises(ValueError, match="Session not found"):
            generator.generate_summary("nonexistent-id")

    def test_empty_statements(self, mock_db_session, mock_llm):
        """Test handling session with no statements."""
        generator = SessionSummaryGenerator(mock_db_session, mock_llm)

        # Mock empty statements
        from hansard_tales.database.models import StatementORM

        statement_query = mock_db_session.query(StatementORM)
        filter_mock = statement_query.filter.return_value
        filter_mock.all.return_value = []

        # Get session ID
        from hansard_tales.database.models import DocumentORM

        session_query = mock_db_session.query(DocumentORM)
        session = session_query.filter().first()
        session_id = session.session_id if hasattr(session, "session_id") else str(session.id)

        summary = generator.generate_summary(session_id)

        assert summary.total_statements == 0
        assert summary.total_mps_present == 0

    def test_no_bills_discussed(self, mock_db_session, mock_llm):
        """Test session with no bills discussed."""
        generator = SessionSummaryGenerator(mock_db_session, mock_llm)

        # Mock no bills
        from hansard_tales.database.models import BillORM

        bill_query = mock_db_session.query(BillORM)
        filter_mock = bill_query.filter.return_value
        filter_mock.all.return_value = []

        # Get session ID
        from hansard_tales.database.models import DocumentORM

        session_query = mock_db_session.query(DocumentORM)
        session = session_query.filter().first()
        session_id = session.session_id if hasattr(session, "session_id") else str(session.id)

        summary = generator.generate_summary(session_id)

        assert summary.bills_discussed == []

    def test_no_votes_held(self, mock_db_session, mock_llm):
        """Test session with no votes."""
        generator = SessionSummaryGenerator(mock_db_session, mock_llm)

        # Mock no votes
        from hansard_tales.database.models import VoteORM

        vote_query = mock_db_session.query(VoteORM)
        filter_mock = vote_query.filter.return_value
        filter_mock.all.return_value = []

        # Get session ID
        from hansard_tales.database.models import DocumentORM

        session_query = mock_db_session.query(DocumentORM)
        session = session_query.filter().first()
        session_id = session.session_id if hasattr(session, "session_id") else str(session.id)

        summary = generator.generate_summary(session_id)

        assert summary.votes_held == []
