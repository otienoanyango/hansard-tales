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
def updater(production_db):
    """Create a database updater instance."""
    return DatabaseUpdater(production_db)


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



class TestEdgeCases:
    """Test suite for edge cases and error handling."""
    
    @patch('hansard_tales.database.db_updater.PDFProcessor')
    @patch('hansard_tales.database.db_updater.MPIdentifier')
    @patch('hansard_tales.database.db_updater.BillExtractor')
    def test_process_hansard_no_current_term(
        self,
        mock_bill_extractor,
        mock_mp_identifier,
        mock_pdf_processor,
        updater
    ):
        """Test processing Hansard when no current term exists."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        # Remove current term marker
        cursor.execute("UPDATE parliamentary_terms SET is_current = 0")
        conn.commit()
        conn.close()
        
        # Mock PDF processor
        mock_pdf = Mock()
        mock_pdf.extract_text_from_pdf.return_value = {
            'pages': [{'page_number': 1, 'text': 'Test content'}]
        }
        mock_pdf_processor.return_value = mock_pdf
        
        # Mock MP identifier
        mock_mp = Mock()
        mock_statements = [Statement("John Doe", "Test statement", 0, 100, page_number=1)]
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
        
        # Process should handle gracefully (will fail due to no current term)
        result = updater.process_hansard_pdf(
            "/path/to/test.pdf",
            "https://example.com/test.pdf",
            "2024-12-04",
            "Test Session"
        )
        
        # Should return error due to no current term
        assert result['status'] == 'error'
    
    def test_get_or_create_mp_with_special_characters(self, updater):
        """Test MP creation with special characters in name."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        # Create MP with special characters
        mp_id = updater.get_or_create_mp(cursor, "O'Brien-Smith")
        
        assert mp_id is not None
        
        # Verify MP was created
        cursor.execute("SELECT name FROM mps WHERE id = ?", (mp_id,))
        row = cursor.fetchone()
        assert row[0] == "O'Brien-Smith"
        
        conn.close()
    
    def test_insert_statement_with_empty_text(self, updater):
        """Test inserting statement with empty text."""
        conn = updater.get_connection()
        cursor = conn.cursor()
        
        mp_id = updater.get_or_create_mp(cursor, "John Doe")
        session_id = updater.get_or_create_session(
            cursor, "2024-12-04", "Test Session", "https://example.com/test.pdf"
        )
        
        # Create statement with empty text
        statement = Statement("John Doe", "", 0, 0)
        
        # Should handle gracefully
        result = updater.insert_statement(cursor, mp_id, session_id, statement)
        
        conn.commit()
        conn.close()
        
        # Should still create statement
        assert result is not None
    
    @patch('hansard_tales.database.db_updater.PDFProcessor')
    @patch('hansard_tales.database.db_updater.MPIdentifier')
    @patch('hansard_tales.database.db_updater.BillExtractor')
    def test_process_hansard_with_duplicate_statements(
        self,
        mock_bill_extractor,
        mock_mp_identifier,
        mock_pdf_processor,
        updater
    ):
        """Test processing Hansard with duplicate statements."""
        # Mock PDF processor
        mock_pdf = Mock()
        mock_pdf.extract_text_from_pdf.return_value = {
            'pages': [{'page_number': 1, 'text': 'Test content'}]
        }
        mock_pdf_processor.return_value = mock_pdf
        
        # Mock MP identifier with duplicate statements
        mock_mp = Mock()
        mock_statements = [
            Statement("John Doe", "Same statement", 0, 100, page_number=1),
            Statement("John Doe", "Same statement", 0, 100, page_number=1),  # Duplicate
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
        
        result = updater.process_hansard_pdf(
            "/path/to/test.pdf",
            "https://example.com/test.pdf",
            "2024-12-04",
            "Test Session"
        )
        
        assert result['status'] == 'success'
        # Should handle duplicates gracefully - both statements get inserted
        assert result['statements'] == 2



class TestCLI:
    """Test CLI functionality."""
    
    @patch('hansard_tales.database.db_updater.DatabaseUpdater')
    @patch('sys.argv', [
        'prog',
        '/path/to/test.pdf',
        '--db-path', 'test.db',
        '--pdf-url', 'https://example.com/test.pdf',
        '--date', '2024-12-04',
        '--title', 'Test Session'
    ])
    def test_main_with_arguments(self, mock_updater_class):
        """Test main function with arguments."""
        from hansard_tales.database.db_updater import main
        
        # Mock updater instance
        mock_updater = Mock()
        mock_updater.process_hansard_pdf.return_value = {
            'status': 'success',
            'session_id': 1,
            'statements': 10,
            'unique_mps': 5,
            'bills': 2
        }
        mock_updater.get_session_statistics.return_value = {
            'date': '2024-12-04',
            'title': 'Test Session',
            'processed': True
        }
        mock_updater_class.return_value = mock_updater
        
        # Run main
        result = main()
        
        # Verify
        assert result == 0
        mock_updater.process_hansard_pdf.assert_called_once()
    
    @patch('hansard_tales.database.db_updater.DatabaseUpdater')
    @patch('sys.argv', [
        'prog',
        '/path/to/test.pdf',
        '--db-path', 'test.db',
        '--pdf-url', 'https://example.com/test.pdf',
        '--date', '2024-12-04',
        '--force'
    ])
    def test_main_with_force_flag(self, mock_updater_class):
        """Test main function with force flag."""
        from hansard_tales.database.db_updater import main
        
        # Mock updater instance
        mock_updater = Mock()
        mock_updater.process_hansard_pdf.return_value = {
            'status': 'success',
            'session_id': 1,
            'statements': 10,
            'unique_mps': 5,
            'bills': 2
        }
        mock_updater.get_session_statistics.return_value = {
            'date': '2024-12-04',
            'title': 'Test',
            'processed': True
        }
        mock_updater_class.return_value = mock_updater
        
        # Run main
        result = main()
        
        # Verify force flag was passed
        assert result == 0
        call_args = mock_updater.process_hansard_pdf.call_args
        assert call_args[1]['skip_if_processed'] == False
    
    @patch('hansard_tales.database.db_updater.DatabaseUpdater')
    @patch('sys.argv', [
        'prog',
        '/path/to/test.pdf',
        '--db-path', 'test.db',
        '--pdf-url', 'https://example.com/test.pdf',
        '--date', '2024-12-04'
    ])
    def test_main_skipped_session(self, mock_updater_class):
        """Test main function with skipped session."""
        from hansard_tales.database.db_updater import main
        
        # Mock updater instance
        mock_updater = Mock()
        mock_updater.process_hansard_pdf.return_value = {
            'status': 'skipped',
            'reason': 'Session already processed'
        }
        mock_updater_class.return_value = mock_updater
        
        # Run main
        result = main()
        
        # Verify
        assert result == 0
    
    @patch('hansard_tales.database.db_updater.DatabaseUpdater')
    @patch('sys.argv', [
        'prog',
        '/path/to/test.pdf',
        '--db-path', 'test.db',
        '--pdf-url', 'https://example.com/test.pdf',
        '--date', '2024-12-04'
    ])
    def test_main_error_case(self, mock_updater_class):
        """Test main function with error."""
        from hansard_tales.database.db_updater import main
        
        # Mock updater instance
        mock_updater = Mock()
        mock_updater.process_hansard_pdf.return_value = {
            'status': 'error',
            'reason': 'Failed to process PDF'
        }
        mock_updater_class.return_value = mock_updater
        
        # Run main
        result = main()
        
        # Verify error return code
        assert result == 1
