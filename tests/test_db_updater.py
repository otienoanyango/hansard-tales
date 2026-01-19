"""
Tests for database update logic.

This module tests the database updater functionality including
MP creation, session management, and statement insertion.
"""

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Import the modules
from hansard_tales.database.db_updater import DatabaseUpdater
from hansard_tales.processors.mp_identifier import Statement
from hansard_tales.processors.bill_extractor import BillReference


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Initialize database schema
    conn = sqlite3.Connection(db_path)
    cursor = conn.cursor()
    
    # Create tables (simplified schema for testing)
    cursor.execute("""
        CREATE TABLE parliamentary_terms (
            id INTEGER PRIMARY KEY,
            term_number INTEGER,
            start_date DATE,
            end_date DATE,
            is_current BOOLEAN DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE mps (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            constituency TEXT,
            party TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE mp_terms (
            id INTEGER PRIMARY KEY,
            mp_id INTEGER,
            term_id INTEGER,
            constituency TEXT,
            party TEXT,
            is_current BOOLEAN DEFAULT 0,
            FOREIGN KEY (mp_id) REFERENCES mps(id),
            FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id),
            UNIQUE(mp_id, term_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE hansard_sessions (
            id INTEGER PRIMARY KEY,
            term_id INTEGER,
            date DATE,
            title TEXT,
            pdf_url TEXT,
            pdf_path TEXT,
            processed BOOLEAN DEFAULT 0,
            FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id),
            UNIQUE(date, title)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE statements (
            id INTEGER PRIMARY KEY,
            mp_id INTEGER,
            session_id INTEGER,
            text TEXT,
            page_number INTEGER,
            bill_reference TEXT,
            FOREIGN KEY (mp_id) REFERENCES mps(id),
            FOREIGN KEY (session_id) REFERENCES hansard_sessions(id)
        )
    """)
    
    # Insert current term
    cursor.execute("""
        INSERT INTO parliamentary_terms (term_number, start_date, end_date, is_current)
        VALUES (13, '2022-09-08', '2027-09-07', 1)
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink()


@pytest.fixture
def updater(temp_db):
    """Create a database updater instance."""
    return DatabaseUpdater(temp_db)


@pytest.fixture
def sample_statements():
    """Create sample statements for testing."""
    return [
        Statement("John Doe", "This is a test statement.", 0, 100, page_number=1),
        Statement("Jane Smith", "Another test statement.", 100, 200, page_number=1),
        Statement("John Doe", "Second statement from John.", 200, 300, page_number=2),
    ]


class TestDatabaseConnection:
    """Test suite for database connection."""
    
    def test_get_connection(self, updater):
        """Test getting database connection."""
        conn = updater.get_connection()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        conn.close()


class TestMPManagement:
    """Test suite for MP management."""
    
    def test_get_or_create_mp_new(self, updater):
        """Test creating a new MP."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        mp_id = updater.get_or_create_mp(cursor, "John Doe", "Nairobi", "Party A")
        
        assert mp_id > 0
        
        # Verify MP was created
        cursor.execute("SELECT * FROM mps WHERE id = ?", (mp_id,))
        mp = cursor.fetchone()
        
        assert mp is not None
        assert mp['name'] == "John Doe"
        assert mp['constituency'] == "Nairobi"
        assert mp['party'] == "Party A"
        
        conn.close()
    
    def test_get_or_create_mp_existing(self, updater):
        """Test getting existing MP."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        # Create MP first
        mp_id1 = updater.get_or_create_mp(cursor, "John Doe", "Nairobi", "Party A")
        
        # Try to create again
        mp_id2 = updater.get_or_create_mp(cursor, "John Doe", "Nairobi", "Party A")
        
        # Should return same ID
        assert mp_id1 == mp_id2
        
        # Verify only one MP exists
        cursor.execute("SELECT COUNT(*) as count FROM mps WHERE name = ?", ("John Doe",))
        count = cursor.fetchone()['count']
        assert count == 1
        
        conn.close()
    
    def test_link_mp_to_current_term(self, updater):
        """Test linking MP to current term."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        # Create MP
        mp_id = updater.get_or_create_mp(cursor, "John Doe")
        
        # Link to current term
        updater.link_mp_to_current_term(cursor, mp_id, "Nairobi", "Party A")
        
        # Verify link was created
        cursor.execute("""
            SELECT * FROM mp_terms 
            WHERE mp_id = ? AND is_current = 1
        """, (mp_id,))
        
        link = cursor.fetchone()
        assert link is not None
        assert link['constituency'] == "Nairobi"
        assert link['party'] == "Party A"
        
        conn.close()
    
    def test_link_mp_to_current_term_duplicate(self, updater):
        """Test that duplicate links are not created."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        mp_id = updater.get_or_create_mp(cursor, "John Doe")
        
        # Link twice
        updater.link_mp_to_current_term(cursor, mp_id)
        updater.link_mp_to_current_term(cursor, mp_id)
        
        # Verify only one link exists
        cursor.execute("SELECT COUNT(*) as count FROM mp_terms WHERE mp_id = ?", (mp_id,))
        count = cursor.fetchone()['count']
        assert count == 1
        
        conn.close()


class TestSessionManagement:
    """Test suite for session management."""
    
    def test_get_or_create_session_new(self, updater):
        """Test creating a new session."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        session_id = updater.get_or_create_session(
            cursor,
            "2024-12-04",
            "Test Session",
            "https://example.com/test.pdf",
            "/path/to/test.pdf"
        )
        
        assert session_id > 0
        
        # Verify session was created
        cursor.execute("SELECT * FROM hansard_sessions WHERE id = ?", (session_id,))
        session = cursor.fetchone()
        
        assert session is not None
        assert session['date'] == "2024-12-04"
        assert session['title'] == "Test Session"
        assert session['pdf_url'] == "https://example.com/test.pdf"
        
        conn.close()
    
    def test_get_or_create_session_existing(self, updater):
        """Test getting existing session."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        # Create session first
        session_id1 = updater.get_or_create_session(
            cursor, "2024-12-04", "Test Session", "https://example.com/test.pdf"
        )
        
        # Try to create again
        session_id2 = updater.get_or_create_session(
            cursor, "2024-12-04", "Test Session", "https://example.com/test.pdf"
        )
        
        # Should return same ID
        assert session_id1 == session_id2
        
        conn.close()
    
    def test_check_duplicate_session(self, updater):
        """Test checking for duplicate sessions."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        # Create and mark as processed
        session_id = updater.get_or_create_session(
            cursor, "2024-12-04", "Test Session", "https://example.com/test.pdf"
        )
        updater.mark_session_processed(cursor, session_id)
        conn.commit()
        
        # Check for duplicate
        is_duplicate = updater.check_duplicate_session(cursor, "2024-12-04", "Test Session")
        
        assert is_duplicate is True
        
        conn.close()
    
    def test_mark_session_processed(self, updater):
        """Test marking session as processed."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        session_id = updater.get_or_create_session(
            cursor, "2024-12-04", "Test Session", "https://example.com/test.pdf"
        )
        
        # Mark as processed
        updater.mark_session_processed(cursor, session_id)
        conn.commit()
        
        # Verify
        cursor.execute("SELECT processed FROM hansard_sessions WHERE id = ?", (session_id,))
        processed = cursor.fetchone()['processed']
        
        assert processed == 1
        
        conn.close()


class TestStatementInsertion:
    """Test suite for statement insertion."""
    
    def test_insert_statement(self, updater):
        """Test inserting a statement."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        # Create MP and session
        mp_id = updater.get_or_create_mp(cursor, "John Doe")
        session_id = updater.get_or_create_session(
            cursor, "2024-12-04", "Test Session", "https://example.com/test.pdf"
        )
        
        # Create statement
        statement = Statement("John Doe", "Test statement text", 0, 100, page_number=1)
        
        # Insert statement
        statement_id = updater.insert_statement(cursor, mp_id, session_id, statement)
        
        assert statement_id > 0
        
        # Verify statement was inserted
        cursor.execute("SELECT * FROM statements WHERE id = ?", (statement_id,))
        stmt = cursor.fetchone()
        
        assert stmt is not None
        assert stmt['mp_id'] == mp_id
        assert stmt['session_id'] == session_id
        assert stmt['text'] == "Test statement text"
        assert stmt['page_number'] == 1
        
        conn.close()
    
    def test_insert_statement_with_bills(self, updater):
        """Test inserting statement with bill references."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        mp_id = updater.get_or_create_mp(cursor, "John Doe")
        session_id = updater.get_or_create_session(
            cursor, "2024-12-04", "Test Session", "https://example.com/test.pdf"
        )
        
        statement = Statement("John Doe", "Test statement", 0, 100)
        bill_refs = ["Bill No. 123", "Finance Bill 2024"]
        
        statement_id = updater.insert_statement(
            cursor, mp_id, session_id, statement, bill_refs
        )
        
        # Verify bill references were stored
        cursor.execute("SELECT bill_reference FROM statements WHERE id = ?", (statement_id,))
        bill_ref = cursor.fetchone()['bill_reference']
        
        assert "Bill No. 123" in bill_ref
        assert "Finance Bill 2024" in bill_ref
        
        conn.close()


class TestProcessHansardPDF:
    """Test suite for complete PDF processing."""
    
    @patch('hansard_tales.database.db_updater.PDFProcessor')
    @patch('hansard_tales.database.db_updater.MPIdentifier')
    @patch('hansard_tales.database.db_updater.BillExtractor')
    def test_process_hansard_pdf_success(
        self,
        mock_bill_extractor,
        mock_mp_identifier,
        mock_pdf_processor,
        updater
    ):
        """Test successful PDF processing."""
        # Mock PDF processor
        mock_pdf = Mock()
        mock_pdf.extract_text_from_pdf.return_value = {
            'pages': [
                {'page_number': 1, 'text': 'Test content'}
            ]
        }
        mock_pdf_processor.return_value = mock_pdf
        
        # Mock MP identifier
        mock_mp = Mock()
        mock_statements = [
            Statement("John Doe", "Test statement", 0, 100, page_number=1)
        ]
        mock_mp.extract_statements_from_pages.return_value = mock_statements
        mock_mp.get_unique_mp_names.return_value = ["John Doe"]
        mock_mp_identifier.return_value = mock_mp
        
        # Mock bill extractor
        mock_bill = Mock()
        mock_bill.extract_bill_references.return_value = []
        mock_bill_extractor.return_value = mock_bill
        
        # Recreate updater with mocked dependencies
        updater.pdf_processor = mock_pdf
        updater.mp_identifier = mock_mp
        updater.bill_extractor = mock_bill
        
        # Process PDF
        result = updater.process_hansard_pdf(
            "/path/to/test.pdf",
            "https://example.com/test.pdf",
            "2024-12-04",
            "Test Session"
        )
        
        assert result['status'] == 'success'
        assert result['statements'] == 1
        assert result['unique_mps'] == 1
    
    def test_process_hansard_pdf_skip_duplicate(self, updater):
        """Test skipping already processed session."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        # Create and mark session as processed
        session_id = updater.get_or_create_session(
            cursor, "2024-12-04", "Test Session", "https://example.com/test.pdf"
        )
        updater.mark_session_processed(cursor, session_id)
        conn.commit()
        conn.close()
        
        # Try to process again
        with patch.object(updater.pdf_processor, 'extract_text_from_pdf'):
            result = updater.process_hansard_pdf(
                "/path/to/test.pdf",
                "https://example.com/test.pdf",
                "2024-12-04",
                "Test Session",
                skip_if_processed=True
            )
        
        assert result['status'] == 'skipped'
        assert result['reason'] == 'already_processed'


class TestSessionStatistics:
    """Test suite for session statistics."""
    
    def test_get_session_statistics(self, updater):
        """Test getting session statistics."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        # Create session with statements
        mp_id = updater.get_or_create_mp(cursor, "John Doe")
        session_id = updater.get_or_create_session(
            cursor, "2024-12-04", "Test Session", "https://example.com/test.pdf"
        )
        
        # Insert statements
        for i in range(3):
            statement = Statement("John Doe", f"Statement {i}", 0, 100)
            updater.insert_statement(cursor, mp_id, session_id, statement)
        
        conn.commit()
        conn.close()
        
        # Get statistics
        stats = updater.get_session_statistics(session_id)
        
        assert stats['session_id'] == session_id
        assert stats['statements'] == 3
        assert stats['unique_mps'] == 1
    
    def test_get_session_statistics_not_found(self, updater):
        """Test getting statistics for non-existent session."""
        stats = updater.get_session_statistics(99999)
        
        assert 'error' in stats
