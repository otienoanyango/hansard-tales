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


# Use production_db fixture from conftest.py
# Note: production_db already has term 13 inserted


class TestParliamentaryTermInsertion:
    """Test suite for parliamentary term insertion."""
    
    def test_insert_13th_parliament(self, production_db):
        """Test inserting 13th Parliament term."""
        conn = sqlite3.connect(production_db)
        
        term_id = insert_parliamentary_term(
            conn,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        assert term_id is not None
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM parliamentary_terms WHERE term_number = 13"
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 13  # term_number
        assert result[2] == "2022-09-08"  # start_date
        assert result[3] == "2027-09-07"  # end_date
        assert result[4] == 1  # is_current
        
        conn.close()
    
    def test_insert_12th_parliament(self, production_db):
        """Test inserting 12th Parliament term."""
        conn = sqlite3.connect(production_db)
        
        term_id = insert_parliamentary_term(
            conn,
            term_number=12,
            start_date="2017-08-31",
            end_date="2022-09-07",
            is_current=False
        )
        
        assert term_id is not None
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM parliamentary_terms WHERE term_number = 12"
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 12  # term_number
        assert result[4] == 0  # is_current (False)
        
        conn.close()
    
    def test_insert_duplicate_term(self, production_db):
        """Test that duplicate term numbers are handled."""
        conn = sqlite3.connect(production_db)
        
        # Insert first time
        term_id_1 = insert_parliamentary_term(
            conn,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        # Try to insert again
        term_id_2 = insert_parliamentary_term(
            conn,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        # Should return existing term ID
        assert term_id_1 == term_id_2
        
        conn.close()
    
    def test_insert_multiple_terms(self, production_db):
        """Test inserting multiple parliamentary terms."""
        conn = sqlite3.connect(production_db)
        
        # Insert 13th Parliament (already exists, should return existing)
        term_id_13 = insert_parliamentary_term(
            conn,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        # Insert 12th Parliament
        term_id_12 = insert_parliamentary_term(
            conn,
            term_number=12,
            start_date="2017-08-31",
            end_date="2022-09-07",
            is_current=False
        )
        
        assert term_id_13 is not None
        assert term_id_12 is not None
        assert term_id_13 != term_id_12
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM parliamentary_terms")
        count = cursor.fetchone()[0]
        
        assert count >= 2  # At least 2 terms
        
        conn.close()


class TestParliamentaryTermVerification:
    """Test suite for parliamentary term verification."""
    
    def test_verify_with_current_term(self, production_db):
        """Test verification passes with current term."""
        conn = sqlite3.connect(production_db)
        
        insert_parliamentary_term(
            conn,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        assert verify_parliamentary_terms(conn) is True
        conn.close()
    
    def test_verify_with_no_terms(self, production_db):
        """Test verification fails with no terms."""
        # Create a fresh database without terms
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM parliamentary_terms")
        conn.commit()
        
        assert verify_parliamentary_terms(conn) is False
        conn.close()
    
    def test_verify_with_no_current_term(self, production_db):
        """Test verification fails with no current term."""
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Remove current term marker
        cursor.execute("UPDATE parliamentary_terms SET is_current = 0")
        conn.commit()
        
        assert verify_parliamentary_terms(conn) is False
        conn.close()
    
    def test_verify_with_multiple_current_terms(self, production_db):
        """Test verification fails with multiple current terms."""
        conn = sqlite3.connect(production_db)
        
        # Insert two terms both marked as current
        conn.execute("""
            INSERT OR IGNORE INTO parliamentary_terms 
            (term_number, start_date, end_date, is_current)
            VALUES (12, '2017-08-31', '2022-09-07', 1)
        """)
        
        # Update existing term 13 to also be current (if not already)
        conn.execute("""
            UPDATE parliamentary_terms 
            SET is_current = 1
            WHERE term_number = 13
        """)
        
        conn.commit()
        
        assert verify_parliamentary_terms(conn) is False
        conn.close()
    
    def test_verify_with_historical_and_current(self, production_db):
        """Test verification passes with historical and current terms."""
        conn = sqlite3.connect(production_db)
        
        insert_parliamentary_term(
            conn,
            term_number=12,
            start_date="2017-08-31",
            end_date="2022-09-07",
            is_current=False
        )
        
        insert_parliamentary_term(
            conn,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        assert verify_parliamentary_terms(conn) is True
        conn.close()


class TestInitializeParliamentData:
    """Test suite for full parliament data initialization."""
    
    def test_initialize_current_term_only(self, production_db):
        """Test initializing only current term."""
        success = initialize_parliament_data(
            production_db,
            include_historical=False
        )
        
        assert success is True
        
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Check 13th Parliament exists
        cursor.execute(
            "SELECT * FROM parliamentary_terms WHERE term_number = 13"
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[4] == 1  # is_current
        
        # Check 12th Parliament may or may not exist (depends on test order)
        cursor.execute(
            "SELECT * FROM parliamentary_terms WHERE term_number = 12"
        )
        result = cursor.fetchone()
        # Don't assert - it may exist from other tests
        
        conn.close()
    
    def test_initialize_with_historical(self, production_db):
        """Test initializing with historical term."""
        success = initialize_parliament_data(
            production_db,
            include_historical=True
        )
        
        assert success is True
        
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Check both terms exist
        cursor.execute("SELECT COUNT(*) FROM parliamentary_terms")
        count = cursor.fetchone()[0]
        assert count >= 2  # At least 2 terms
        
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
    
    def test_initialize_idempotent(self, production_db):
        """Test that initialization can be run multiple times."""
        # First initialization
        success1 = initialize_parliament_data(
            production_db,
            include_historical=False
        )
        assert success1 is True
        
        # Second initialization (should handle duplicates)
        success2 = initialize_parliament_data(
            production_db,
            include_historical=False
        )
        assert success2 is True
        
        # Verify at least one term exists
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM parliamentary_terms")
        count = cursor.fetchone()[0]
        assert count >= 1
        conn.close()


class TestParliamentaryTermDates:
    """Test suite for parliamentary term date validation."""
    
    def test_13th_parliament_dates(self, production_db):
        """Test 13th Parliament has correct dates."""
        conn = sqlite3.connect(production_db)
        
        insert_parliamentary_term(
            conn,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT start_date, end_date FROM parliamentary_terms WHERE term_number = 13"
        )
        result = cursor.fetchone()
        
        assert result[0] == "2022-09-08"
        assert result[1] == "2027-09-07"
        
        conn.close()
    
    def test_12th_parliament_dates(self, production_db):
        """Test 12th Parliament has correct dates."""
        conn = sqlite3.connect(production_db)
        
        insert_parliamentary_term(
            conn,
            term_number=12,
            start_date="2017-08-31",
            end_date="2022-09-07",
            is_current=False
        )
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT start_date, end_date FROM parliamentary_terms WHERE term_number = 12"
        )
        result = cursor.fetchone()
        
        assert result[0] == "2017-08-31"
        assert result[1] == "2022-09-07"
        
        conn.close()



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
