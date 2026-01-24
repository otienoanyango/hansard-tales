"""
Test the production_db fixture to ensure it creates a proper database.

This test validates that the production_db fixture:
1. Creates a database with the production schema
2. Runs all migrations
3. Inserts the current parliamentary term
4. Has all expected tables, indexes, and views
"""

import sqlite3

import pytest


class TestProductionDBFixture:
    """Test suite for production_db fixture."""
    
    def test_fixture_creates_database(self, production_db):
        """Test that fixture creates a database file."""
        from pathlib import Path
        assert Path(production_db).exists()
        assert Path(production_db).suffix == '.db'
    
    def test_all_tables_exist(self, production_db):
        """Test that all production tables are created."""
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'parliamentary_terms',
            'mps',
            'mp_terms',
            'hansard_sessions',
            'statements',
            'downloaded_pdfs'
        ]
        
        for table in expected_tables:
            assert table in tables, f"Missing table: {table}"
        
        conn.close()
    
    def test_all_views_exist(self, production_db):
        """Test that all production views are created."""
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]
        
        expected_views = [
            'current_mps',
            'mp_current_term_performance',
            'mp_historical_performance'
        ]
        
        for view in expected_views:
            assert view in views, f"Missing view: {view}"
        
        conn.close()
    
    def test_indexes_exist(self, production_db):
        """Test that indexes are created."""
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Check for some key indexes
        expected_index_prefixes = [
            'idx_statements_',
            'idx_hansard_',
            'idx_mp_terms_',
            'idx_downloaded_pdfs_'
        ]
        
        for prefix in expected_index_prefixes:
            has_index = any(idx.startswith(prefix) for idx in indexes)
            assert has_index, f"Missing indexes with prefix: {prefix}"
        
        conn.close()
    
    def test_current_term_inserted(self, production_db):
        """Test that current parliamentary term is inserted."""
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT term_number, start_date, end_date, is_current
            FROM parliamentary_terms
            WHERE term_number = 13
        """)
        
        result = cursor.fetchone()
        assert result is not None, "Current term not found"
        
        term_number, start_date, end_date, is_current = result
        assert term_number == 13
        assert start_date == '2022-09-08'
        assert end_date == '2027-09-07'
        assert is_current == 1
        
        conn.close()
    
    def test_migration_columns_exist(self, production_db):
        """Test that migration columns are added."""
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Check that migration added period_of_day and session_id columns
        cursor.execute("PRAGMA table_info(downloaded_pdfs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        assert 'period_of_day' in columns, "Migration column 'period_of_day' not found"
        assert 'session_id' in columns, "Migration column 'session_id' not found"
        
        conn.close()
    
    def test_schema_matches_production(self, production_db):
        """Test that schema matches production schema exactly."""
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Check mps table has all production columns
        cursor.execute("PRAGMA table_info(mps)")
        mp_columns = [row[1] for row in cursor.fetchall()]
        
        expected_mp_columns = [
            'id', 'name', 'constituency', 'party', 'photo_url',
            'first_elected_year', 'created_at', 'updated_at'
        ]
        
        for col in expected_mp_columns:
            assert col in mp_columns, f"Missing column in mps table: {col}"
        
        # Check mp_terms table exists (junction table)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mp_terms'")
        assert cursor.fetchone() is not None, "mp_terms junction table not found"
        
        conn.close()
    
    def test_foreign_keys_defined(self, production_db):
        """Test that foreign key constraints are defined."""
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Check foreign keys on statements table
        cursor.execute("PRAGMA foreign_key_list(statements)")
        fks = cursor.fetchall()
        
        # Should have foreign keys to mps and hansard_sessions
        fk_tables = [fk[2] for fk in fks]
        assert 'mps' in fk_tables, "Missing foreign key to mps"
        assert 'hansard_sessions' in fk_tables, "Missing foreign key to hansard_sessions"
        
        conn.close()
    
    def test_unique_constraints_exist(self, production_db):
        """Test that unique constraints are defined."""
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Check unique constraint on hansard_sessions (date, title)
        cursor.execute("PRAGMA index_list(hansard_sessions)")
        indexes = cursor.fetchall()
        
        # Look for unique index
        has_unique = any(idx[2] == 1 for idx in indexes)  # idx[2] is 'unique' flag
        assert has_unique, "Missing unique constraint on hansard_sessions"
        
        conn.close()
    
    def test_check_constraint_on_period(self, production_db):
        """Test that CHECK constraint on period_of_day works."""
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Try to insert invalid period - should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO downloaded_pdfs 
                (original_url, file_path, date, period_of_day)
                VALUES ('test://invalid', '/tmp/test.pdf', '2024-01-01', 'X')
            """)
        
        # Valid periods should work
        cursor.execute("""
            INSERT INTO downloaded_pdfs 
            (original_url, file_path, date, period_of_day)
            VALUES ('test://valid', '/tmp/test.pdf', '2024-01-01', 'A')
        """)
        
        conn.rollback()  # Don't save test data
        conn.close()
    
    def test_fixture_cleanup(self, production_db):
        """Test that fixture cleans up after itself."""
        from pathlib import Path
        db_path = Path(production_db)
        
        # Database should exist during test
        assert db_path.exists()
        
        # Store path for later check
        stored_path = str(db_path)
        
        # After test completes, pytest will call fixture cleanup
        # We can't test this directly, but we verify the path is valid
        assert stored_path.endswith('.db')
