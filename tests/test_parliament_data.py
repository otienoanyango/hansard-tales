"""
Tests for parliamentary term data initialization.

This module verifies that parliamentary term data is correctly
inserted and validated.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import modules
from hansard_tales.database.init_db import initialize_database
from hansard_tales.database.init_parliament_data import (
    insert_parliamentary_term,
    verify_parliamentary_terms,
    initialize_parliament_data
)


@pytest.fixture
def temp_db():
    """Create a temporary database with schema for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Initialize database schema
    initialize_database(db_path)
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def db_connection(temp_db):
    """Create a database connection for testing."""
    conn = sqlite3.connect(temp_db)
    yield conn
    conn.close()


class TestParliamentaryTermInsertion:
    """Test suite for parliamentary term insertion."""
    
    def test_insert_13th_parliament(self, db_connection):
        """Test inserting 13th Parliament term."""
        term_id = insert_parliamentary_term(
            db_connection,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        assert term_id is not None
        
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT * FROM parliamentary_terms WHERE term_number = 13"
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 13  # term_number
        assert result[2] == "2022-09-08"  # start_date
        assert result[3] == "2027-09-07"  # end_date
        assert result[4] == 1  # is_current
    
    def test_insert_12th_parliament(self, db_connection):
        """Test inserting 12th Parliament term."""
        term_id = insert_parliamentary_term(
            db_connection,
            term_number=12,
            start_date="2017-08-31",
            end_date="2022-09-07",
            is_current=False
        )
        
        assert term_id is not None
        
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT * FROM parliamentary_terms WHERE term_number = 12"
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 12  # term_number
        assert result[4] == 0  # is_current (False)
    
    def test_insert_duplicate_term(self, db_connection):
        """Test that duplicate term numbers are handled."""
        # Insert first time
        term_id_1 = insert_parliamentary_term(
            db_connection,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        # Try to insert again
        term_id_2 = insert_parliamentary_term(
            db_connection,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        # Should return existing term ID
        assert term_id_1 == term_id_2
    
    def test_insert_multiple_terms(self, db_connection):
        """Test inserting multiple parliamentary terms."""
        # Insert 13th Parliament
        term_id_13 = insert_parliamentary_term(
            db_connection,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        # Insert 12th Parliament
        term_id_12 = insert_parliamentary_term(
            db_connection,
            term_number=12,
            start_date="2017-08-31",
            end_date="2022-09-07",
            is_current=False
        )
        
        assert term_id_13 is not None
        assert term_id_12 is not None
        assert term_id_13 != term_id_12
        
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM parliamentary_terms")
        count = cursor.fetchone()[0]
        
        assert count == 2


class TestParliamentaryTermVerification:
    """Test suite for parliamentary term verification."""
    
    def test_verify_with_current_term(self, db_connection):
        """Test verification passes with current term."""
        insert_parliamentary_term(
            db_connection,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        assert verify_parliamentary_terms(db_connection) is True
    
    def test_verify_with_no_terms(self, db_connection):
        """Test verification fails with no terms."""
        assert verify_parliamentary_terms(db_connection) is False
    
    def test_verify_with_no_current_term(self, db_connection):
        """Test verification fails with no current term."""
        insert_parliamentary_term(
            db_connection,
            term_number=12,
            start_date="2017-08-31",
            end_date="2022-09-07",
            is_current=False
        )
        
        assert verify_parliamentary_terms(db_connection) is False
    
    def test_verify_with_multiple_current_terms(self, db_connection):
        """Test verification fails with multiple current terms."""
        # Insert two terms both marked as current
        db_connection.execute("""
            INSERT INTO parliamentary_terms 
            (term_number, start_date, end_date, is_current)
            VALUES (12, '2017-08-31', '2022-09-07', 1)
        """)
        
        db_connection.execute("""
            INSERT INTO parliamentary_terms 
            (term_number, start_date, end_date, is_current)
            VALUES (13, '2022-09-08', '2027-09-07', 1)
        """)
        
        db_connection.commit()
        
        assert verify_parliamentary_terms(db_connection) is False
    
    def test_verify_with_historical_and_current(self, db_connection):
        """Test verification passes with historical and current terms."""
        insert_parliamentary_term(
            db_connection,
            term_number=12,
            start_date="2017-08-31",
            end_date="2022-09-07",
            is_current=False
        )
        
        insert_parliamentary_term(
            db_connection,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        assert verify_parliamentary_terms(db_connection) is True


class TestInitializeParliamentData:
    """Test suite for full parliament data initialization."""
    
    def test_initialize_current_term_only(self, temp_db):
        """Test initializing only current term."""
        success = initialize_parliament_data(
            temp_db,
            include_historical=False
        )
        
        assert success is True
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Check 13th Parliament exists
        cursor.execute(
            "SELECT * FROM parliamentary_terms WHERE term_number = 13"
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[4] == 1  # is_current
        
        # Check 12th Parliament does not exist
        cursor.execute(
            "SELECT * FROM parliamentary_terms WHERE term_number = 12"
        )
        result = cursor.fetchone()
        assert result is None
        
        conn.close()
    
    def test_initialize_with_historical(self, temp_db):
        """Test initializing with historical term."""
        success = initialize_parliament_data(
            temp_db,
            include_historical=True
        )
        
        assert success is True
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Check both terms exist
        cursor.execute("SELECT COUNT(*) FROM parliamentary_terms")
        count = cursor.fetchone()[0]
        assert count == 2
        
        # Check 13th Parliament is current
        cursor.execute(
            "SELECT is_current FROM parliamentary_terms WHERE term_number = 13"
        )
        result = cursor.fetchone()
        assert result[0] == 1
        
        # Check 12th Parliament is not current
        cursor.execute(
            "SELECT is_current FROM parliamentary_terms WHERE term_number = 12"
        )
        result = cursor.fetchone()
        assert result[0] == 0
        
        conn.close()
    
    def test_initialize_nonexistent_database(self):
        """Test initialization fails with nonexistent database."""
        success = initialize_parliament_data(
            "nonexistent.db",
            include_historical=False
        )
        
        assert success is False
    
    def test_initialize_idempotent(self, temp_db):
        """Test that initialization can be run multiple times."""
        # First initialization
        success1 = initialize_parliament_data(
            temp_db,
            include_historical=False
        )
        assert success1 is True
        
        # Second initialization (should handle duplicates)
        success2 = initialize_parliament_data(
            temp_db,
            include_historical=False
        )
        assert success2 is True
        
        # Verify only one term exists
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM parliamentary_terms")
        count = cursor.fetchone()[0]
        assert count == 1
        conn.close()


class TestParliamentaryTermDates:
    """Test suite for parliamentary term date validation."""
    
    def test_13th_parliament_dates(self, db_connection):
        """Test 13th Parliament has correct dates."""
        insert_parliamentary_term(
            db_connection,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT start_date, end_date FROM parliamentary_terms WHERE term_number = 13"
        )
        result = cursor.fetchone()
        
        assert result[0] == "2022-09-08"
        assert result[1] == "2027-09-07"
    
    def test_12th_parliament_dates(self, db_connection):
        """Test 12th Parliament has correct dates."""
        insert_parliamentary_term(
            db_connection,
            term_number=12,
            start_date="2017-08-31",
            end_date="2022-09-07",
            is_current=False
        )
        
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT start_date, end_date FROM parliamentary_terms WHERE term_number = 12"
        )
        result = cursor.fetchone()
        
        assert result[0] == "2017-08-31"
        assert result[1] == "2022-09-07"



class TestCLI:
    """Test suite for CLI argument parsing and main() function."""
    
    @patch('hansard_tales.database.init_parliament_data.initialize_parliament_data')
    @patch('sys.argv', ['hansard-init-parliament', '--db-path', 'test.db'])
    def test_main_with_arguments(self, mock_init_parliament):
        """Test main() with custom arguments."""
        from hansard_tales.database.init_parliament_data import main
        
        # Mock successful initialization
        mock_init_parliament.return_value = True
        
        # Run main
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Should exit with 0 (success)
        assert exc_info.value.code == 0
        
        # Verify initialize_parliament_data was called
        mock_init_parliament.assert_called_once_with('test.db', False)
    
    @patch('hansard_tales.database.init_parliament_data.initialize_parliament_data')
    @patch('sys.argv', ['hansard-init-parliament'])
    def test_main_default_path(self, mock_init_parliament):
        """Test main() with default database path."""
        from hansard_tales.database.init_parliament_data import main
        
        # Mock successful initialization
        mock_init_parliament.return_value = True
        
        # Run main
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Should exit with 0 (success)
        assert exc_info.value.code == 0
        
        # Verify initialize_parliament_data was called with default path
        mock_init_parliament.assert_called_once_with('data/hansard.db', False)
