"""
Tests for Database Manager.

This module tests the database backup and clean functionality including
backup filename format validation and database maintenance operations.
"""

import pytest
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings

from hansard_tales.database.db_manager import DatabaseManager


@pytest.fixture
def temp_backup_dir():
    """Create a temporary backup directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def manager():
    """Create a DatabaseManager instance for testing."""
    return DatabaseManager()


class TestBackupProperties:
    """Property-based tests for database backup functionality."""
    
    @given(
        timestamp=st.datetimes(
            min_value=datetime(2020, 1, 1, 0, 0, 0),
            max_value=datetime(2030, 12, 31, 23, 59, 59)
        )
    )
    @settings(max_examples=100)
    def test_backup_filename_format_property(self, timestamp):
        """
        **Validates: Requirements 8.2**
        
        Property 8: Backup Filename Format
        
        For any backup operation, the backup filename should match the pattern
        hansard_YYYYMMDD_HHMMSS.db where the timestamp reflects the backup
        creation time.
        
        This property test verifies that:
        1. Backup filenames always match the expected pattern
        2. Timestamp is correctly formatted as YYYYMMDD_HHMMSS
        3. Backup files are created in the correct directory
        4. Backup filename reflects the actual backup creation time
        """
        import re
        import shutil
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db = f.name
        
        # Create temporary backup directory
        temp_backup_dir = tempfile.mkdtemp()
        
        try:
            # Initialize database with basic schema
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            cursor.execute("INSERT INTO test VALUES (1)")
            conn.commit()
            conn.close()
            
            # Create manager instance
            manager = DatabaseManager()
            
            # Mock datetime.now() to return our test timestamp
            with patch('hansard_tales.database.db_manager.datetime') as mock_datetime:
                mock_datetime.now.return_value = timestamp
                
                # Create backup
                backup_path = manager.backup(temp_db, temp_backup_dir)
                
                # Verify backup file was created
                assert Path(backup_path).exists(), (
                    f"Backup file was not created at {backup_path}"
                )
                
                # Extract filename from path
                backup_filename = Path(backup_path).name
                
                # Verify filename matches pattern hansard_YYYYMMDD_HHMMSS.db
                pattern = r'^hansard_\d{8}_\d{6}\.db$'
                assert re.match(pattern, backup_filename), (
                    f"Backup filename '{backup_filename}' does not match pattern '{pattern}'"
                )
                
                # Verify timestamp components are correct
                expected_date = timestamp.strftime('%Y%m%d')
                expected_time = timestamp.strftime('%H%M%S')
                expected_filename = f"hansard_{expected_date}_{expected_time}.db"
                
                assert backup_filename == expected_filename, (
                    f"Expected filename '{expected_filename}', got '{backup_filename}'"
                )
                
                # Verify backup is in correct directory
                assert Path(backup_path).parent == Path(temp_backup_dir), (
                    f"Backup not in expected directory. "
                    f"Expected: {temp_backup_dir}, Got: {Path(backup_path).parent}"
                )
                
                # Verify backup file has content (not empty)
                backup_size = Path(backup_path).stat().st_size
                assert backup_size > 0, (
                    f"Backup file is empty (size: {backup_size})"
                )
                
                # Verify backup is a valid SQLite database
                try:
                    conn = sqlite3.connect(backup_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    conn.close()
                    
                    assert len(tables) > 0, (
                        "Backup database has no tables"
                    )
                except sqlite3.Error as e:
                    pytest.fail(f"Backup is not a valid SQLite database: {e}")
        
        finally:
            # Cleanup
            Path(temp_db).unlink(missing_ok=True)
            shutil.rmtree(temp_backup_dir, ignore_errors=True)


class TestBackup:
    """Unit tests for database backup functionality."""
    
    def test_backup_creates_file(self, manager, production_db, temp_backup_dir):
        """Test that backup creates a file."""
        backup_path = manager.backup(production_db, temp_backup_dir)
        
        assert Path(backup_path).exists()
        assert Path(backup_path).is_file()
    
    def test_backup_preserves_data(self, manager, production_db, temp_backup_dir):
        """Test that backup preserves all data."""
        # Add some test data first
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO downloaded_pdfs (original_url, file_path, date) VALUES ('http://test.com/1.pdf', 'test1.pdf', '2024-01-01')")
        cursor.execute("INSERT INTO hansard_sessions (term_id, date, title, pdf_url) VALUES (1, '2024-01-01', 'Test Session', 'http://test.com/1.pdf')")
        conn.commit()
        conn.close()
        
        # Create backup
        backup_path = manager.backup(production_db, temp_backup_dir)
        
        # Verify data in backup
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM downloaded_pdfs")
        assert cursor.fetchone()[0] >= 1
        
        cursor.execute("SELECT COUNT(*) FROM hansard_sessions")
        assert cursor.fetchone()[0] >= 1
        
        conn.close()
    
    def test_backup_creates_directory_if_not_exists(self, manager, production_db):
        """Test that backup creates backup directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir) / "backups" / "nested"
            
            backup_path = manager.backup(production_db, str(backup_dir))
            
            assert Path(backup_path).exists()
            assert Path(backup_path).parent == backup_dir
    
    def test_backup_nonexistent_database_raises_error(self, manager, temp_backup_dir):
        """Test that backing up nonexistent database raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Database not found"):
            manager.backup("nonexistent.db", temp_backup_dir)
    
    def test_backup_returns_correct_path(self, manager, production_db, temp_backup_dir):
        """Test that backup returns the correct backup file path."""
        backup_path = manager.backup(production_db, temp_backup_dir)
        
        assert backup_path.startswith(temp_backup_dir)
        assert backup_path.endswith('.db')
        assert 'hansard_' in backup_path
    
    def test_backup_multiple_times_creates_unique_files(self, manager, production_db, temp_backup_dir):
        """Test that multiple backups create unique files."""
        import time
        
        backup1 = manager.backup(production_db, temp_backup_dir)
        time.sleep(1.1)  # Ensure different timestamp
        backup2 = manager.backup(production_db, temp_backup_dir)
        
        assert backup1 != backup2
        assert Path(backup1).exists()
        assert Path(backup2).exists()
    
    def test_backup_default_directory(self, manager, production_db):
        """Test backup with default directory."""
        # Use a temporary directory as default
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = manager.backup(production_db, tmpdir)
            
            assert Path(backup_path).exists()
            assert str(Path(backup_path).parent) == tmpdir


class TestClean:
    """Unit tests for database clean functionality."""
    
    def test_clean_preserves_downloaded_pdfs(self, manager, production_db):
        """Test that clean preserves downloaded_pdfs table by default."""
        # Add test data
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO downloaded_pdfs (original_url, file_path, date) VALUES ('http://test.com/1.pdf', 'test1.pdf', '2024-01-01')")
        cursor.execute("INSERT INTO hansard_sessions (term_id, date, title, pdf_url) VALUES (1, '2024-01-01', 'Test Session', 'http://test.com/1.pdf')")
        conn.commit()
        conn.close()
        
        # Clean database (without confirmation)
        manager.clean(production_db, confirm=False)
        
        # Verify downloaded_pdfs still has data
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM downloaded_pdfs")
        assert cursor.fetchone()[0] >= 1
        
        conn.close()
    
    def test_clean_removes_other_tables(self, manager, production_db):
        """Test that clean removes data from other tables."""
        # Add test data
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO hansard_sessions (term_id, date, title, pdf_url) VALUES (1, '2024-01-01', 'Test Session', 'http://test.com/1.pdf')")
        cursor.execute("INSERT INTO statements (mp_id, session_id, text) VALUES (1, 1, 'Test statement')")
        conn.commit()
        conn.close()
        
        # Clean database (without confirmation)
        manager.clean(production_db, confirm=False)
        
        # Verify other tables are empty
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM hansard_sessions")
        assert cursor.fetchone()[0] == 0
        
        cursor.execute("SELECT COUNT(*) FROM statements")
        assert cursor.fetchone()[0] == 0
        
        conn.close()
    
    def test_clean_with_custom_preserve_list(self, manager, production_db):
        """Test clean with custom preserve tables list."""
        # Add test data
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO downloaded_pdfs (original_url, file_path, date) VALUES ('http://test.com/1.pdf', 'test1.pdf', '2024-01-01')")
        cursor.execute("INSERT INTO statements (mp_id, session_id, text) VALUES (1, 1, 'Test statement')")
        conn.commit()
        conn.close()
        
        # Clean but preserve statements table
        manager.clean(production_db, preserve_tables=['statements'], confirm=False)
        
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Statements should be preserved
        cursor.execute("SELECT COUNT(*) FROM statements")
        assert cursor.fetchone()[0] >= 1
        
        # Other tables should be empty
        cursor.execute("SELECT COUNT(*) FROM downloaded_pdfs")
        assert cursor.fetchone()[0] == 0
        
        cursor.execute("SELECT COUNT(*) FROM hansard_sessions")
        assert cursor.fetchone()[0] == 0
        
        conn.close()
    
    def test_clean_nonexistent_database_raises_error(self, manager):
        """Test that cleaning nonexistent database raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Database not found"):
            manager.clean("nonexistent.db", confirm=False)
    
    def test_clean_with_confirmation_yes(self, manager, production_db):
        """Test clean with user confirmation (yes)."""
        # Add test data
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO hansard_sessions (term_id, date, title, pdf_url) VALUES (1, '2024-01-01', 'Test Session', 'http://test.com/1.pdf')")
        conn.commit()
        conn.close()
        
        with patch('builtins.input', return_value='yes'):
            manager.clean(production_db, confirm=True)
        
        # Verify clean was executed
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM hansard_sessions")
        assert cursor.fetchone()[0] == 0
        
        conn.close()
    
    def test_clean_with_confirmation_no(self, manager, production_db):
        """Test clean with user confirmation (no)."""
        # Add test data
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO hansard_sessions (term_id, date, title, pdf_url) VALUES (1, '2024-01-01', 'Test Session', 'http://test.com/1.pdf')")
        conn.commit()
        conn.close()
        
        with patch('builtins.input', return_value='no'):
            manager.clean(production_db, confirm=True)
        
        # Verify clean was NOT executed
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM hansard_sessions")
        assert cursor.fetchone()[0] >= 1  # Data still present
        
        conn.close()
    
    def test_clean_preserves_table_structure(self, manager, production_db):
        """Test that clean preserves table structure (only deletes data)."""
        manager.clean(production_db, confirm=False)
        
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Verify tables still exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'downloaded_pdfs' in tables
        assert 'hansard_sessions' in tables
        assert 'statements' in tables
        
        conn.close()
    
    def test_clean_does_not_affect_sqlite_tables(self, manager, production_db):
        """Test that clean does not affect SQLite system tables."""
        manager.clean(production_db, confirm=False)
        
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Verify sqlite_master still exists and has content
        cursor.execute("SELECT COUNT(*) FROM sqlite_master")
        count = cursor.fetchone()[0]
        assert count > 0
        
        conn.close()


class TestEdgeCases:
    """Test edge cases for database manager."""
    
    def test_backup_empty_database(self, manager, temp_backup_dir):
        """Test backing up an empty database."""
        # Create empty database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            empty_db = f.name
        
        try:
            # Initialize empty database
            conn = sqlite3.connect(empty_db)
            conn.close()
            
            # Backup should work
            backup_path = manager.backup(empty_db, temp_backup_dir)
            assert Path(backup_path).exists()
        finally:
            Path(empty_db).unlink(missing_ok=True)
    
    def test_clean_empty_tables(self, manager, production_db):
        """Test cleaning database that already has empty tables."""
        # First clean
        manager.clean(production_db, confirm=False)
        
        # Second clean should not raise error
        manager.clean(production_db, confirm=False)
        
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM hansard_sessions")
        assert cursor.fetchone()[0] == 0
        
        conn.close()
    
    def test_backup_with_special_characters_in_path(self, manager, production_db):
        """Test backup with special characters in directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir) / "backup dir with spaces"
            backup_dir.mkdir()
            
            backup_path = manager.backup(production_db, str(backup_dir))
            assert Path(backup_path).exists()
