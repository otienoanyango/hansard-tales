"""
Tests for download tracking functionality.
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from hansard_tales.scrapers.hansard_scraper import HansardScraper


@pytest.fixture
def scraper():
    """Create a scraper instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from hansard_tales.storage.filesystem import FilesystemStorage
        storage = FilesystemStorage(tmpdir)
        yield HansardScraper(storage=storage, rate_limit_delay=0.1)


class TestDownloadTracking:
    """Test suite for download tracking functionality."""
    
    def test_track_download_success_case(self):
        """Test _track_download() success case."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create temporary database with new schema
            db_path = Path(tmpdir) / 'test.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE downloaded_pdfs (
                    id INTEGER PRIMARY KEY,
                    original_url TEXT UNIQUE,
                    file_path TEXT,
                    date TEXT,
                    period_of_day TEXT,
                    session_id INTEGER,
                    file_size INTEGER,
                    downloaded_at TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
            
            # Create scraper with database
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path=str(db_path))
            
            # Create test file using storage
            storage.write('test.pdf', b'test content')
            
            # Track download with new signature
            scraper._track_download(
                'https://example.com/test.pdf',
                'test.pdf',
                '2024-01-01',
                'P',  # period_of_day
                None  # session_id
            )
            
            # Verify in database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT original_url, date, period_of_day, file_size FROM downloaded_pdfs")
            result = cursor.fetchone()
            conn.close()
            
            assert result is not None
            assert result[0] == 'https://example.com/test.pdf'
            assert result[1] == '2024-01-01'
            assert result[2] == 'P'
            assert result[3] == len(b'test content')
    
    def test_track_download_database_error(self):
        """Test _track_download() with database error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create scraper with invalid database path
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path='/invalid/path/db.db')
            
            # Create test file
            storage.write('test.pdf', b'test content')
            
            # Should not raise exception, just log warning
            scraper._track_download(
                'https://example.com/test.pdf',
                'test.pdf',
                '2024-01-01',
                'P',
                None
            )
    
    def test_track_download_no_database(self):
        """Test _track_download() with no database configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create scraper without database
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path=None)
            
            # Create test file
            storage.write('test.pdf', b'test content')
            
            # Should return immediately without error
            scraper._track_download(
                'https://example.com/test.pdf',
                'test.pdf',
                '2024-01-01',
                'P',
                None
            )
    
    def test_check_existing_download_file_exists(self, scraper):
        """Test _check_existing_download() when file exists."""
        # Create test file using storage
        scraper.storage.write('existing.pdf', b'existing content')
        
        # Should return (True, 'file_exists_without_record')
        should_skip, reason = scraper._check_existing_download(
            'https://example.com/test.pdf',
            'existing.pdf',
            '2024-01-15',
            'P'
        )
        assert should_skip is True
        assert reason == 'file_exists_without_record'
    
    def test_check_existing_download_in_database(self):
        """Test _check_existing_download() when in database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create temporary database
            db_path = Path(tmpdir) / 'test.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE downloaded_pdfs (
                    id INTEGER PRIMARY KEY,
                    original_url TEXT UNIQUE,
                    file_path TEXT,
                    date TEXT,
                    period_of_day TEXT,
                    session_id INTEGER,
                    file_size INTEGER,
                    downloaded_at TIMESTAMP
                )
            """)
            cursor.execute("""
                INSERT INTO downloaded_pdfs (original_url, file_path, date)
                VALUES ('https://example.com/test.pdf', 'test.pdf', '2024-01-01')
            """)
            conn.commit()
            conn.close()
            
            # Create scraper with database
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path=str(db_path))
            
            # File doesn't exist but is in database
            should_skip, reason = scraper._check_existing_download(
                'https://example.com/test.pdf',
                'test.pdf',
                '2024-01-01',
                'P'
            )
            
            # Should return (False, 'file_missing_redownload')
            assert should_skip is False
            assert reason == 'file_missing_redownload'
    
    def test_check_existing_download_not_found(self, scraper):
        """Test _check_existing_download() when not found."""
        # File doesn't exist and no database
        should_skip, reason = scraper._check_existing_download(
            'https://example.com/test.pdf',
            'nonexistent.pdf',
            '2024-01-15',
            'P'
        )
        
        # Should return (False, 'new_download')
        assert should_skip is False
        assert reason == 'new_download'


class TestDatabaseErrorHandling:
    """Test suite for database error handling in download tracking."""
    
    def test_database_connection_error(self):
        """Test handling of database connection errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create scraper with invalid database path
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path='/invalid/path/db.db')
            
            # Should not raise exception
            should_skip, reason = scraper._check_existing_download(
                'https://example.com/test.pdf',
                'test.pdf',
                '2024-01-15',
                'P'
            )
            
            # Should return new_download when database unavailable
            assert should_skip is False
            assert reason == 'new_download'
    
    def test_track_download_insert_or_replace_new_record(self):
        """Test INSERT OR REPLACE behavior with new record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create temporary database
            db_path = Path(tmpdir) / 'test.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE downloaded_pdfs (
                    id INTEGER PRIMARY KEY,
                    original_url TEXT UNIQUE,
                    file_path TEXT,
                    date TEXT,
                    period_of_day TEXT,
                    session_id INTEGER,
                    file_size INTEGER,
                    downloaded_at TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
            
            # Create scraper with database
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path=str(db_path))
            
            # Create test file
            storage.write('test.pdf', b'test content')
            
            # Track download (INSERT)
            scraper._track_download(
                'https://example.com/test.pdf',
                'test.pdf',
                '2024-01-01',
                'P',
                None
            )
            
            # Verify record was inserted
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM downloaded_pdfs")
            count = cursor.fetchone()[0]
            conn.close()
            
            assert count == 1
    
    def test_track_download_insert_or_replace_existing_record(self):
        """Test INSERT OR REPLACE behavior with existing record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create temporary database
            db_path = Path(tmpdir) / 'test.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE downloaded_pdfs (
                    id INTEGER PRIMARY KEY,
                    original_url TEXT UNIQUE,
                    file_path TEXT,
                    date TEXT,
                    period_of_day TEXT,
                    session_id INTEGER,
                    file_size INTEGER,
                    downloaded_at TIMESTAMP
                )
            """)
            # Insert initial record
            cursor.execute("""
                INSERT INTO downloaded_pdfs (original_url, file_path, date, period_of_day)
                VALUES ('https://example.com/test.pdf', 'old_path.pdf', '2024-01-01', 'A')
            """)
            conn.commit()
            conn.close()
            
            # Create scraper with database
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path=str(db_path))
            
            # Create test file with new path
            storage.write('new_path.pdf', b'updated content')
            
            # Track download with same URL (REPLACE)
            scraper._track_download(
                'https://example.com/test.pdf',
                'new_path.pdf',
                '2024-01-01',
                'P',
                123
            )
            
            # Verify record was replaced (not duplicated)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM downloaded_pdfs")
            count = cursor.fetchone()[0]
            
            # Verify updated values
            cursor.execute("""
                SELECT file_path, period_of_day, session_id 
                FROM downloaded_pdfs 
                WHERE original_url = 'https://example.com/test.pdf'
            """)
            result = cursor.fetchone()
            conn.close()
            
            # Assert only one record exists (not duplicated)
            assert count == 1
            
            # Assert values were updated
            assert result[0] == 'new_path.pdf'
            assert result[1] == 'P'
            assert result[2] == 123
