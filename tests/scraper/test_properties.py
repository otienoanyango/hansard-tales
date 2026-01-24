"""
Property-based tests for scraper functionality.
"""

import logging
import sqlite3
import tempfile
from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import Mock

import pytest
from hypothesis import given, settings, strategies as st

from hansard_tales.scrapers.hansard_scraper import HansardScraper


class TestDownloadTrackingProperties:
    """Property-based tests for download tracking metadata."""
    
    @given(
        url=st.from_regex(r'https?://[a-z0-9\-\.]+\.[a-z]{2,}/[a-z0-9\-_/]+\.pdf', fullmatch=True),
        file_path=st.from_regex(r'hansard_\d{8}_[APE](?:_\d+)?\.pdf', fullmatch=True),
        date=st.dates(min_value=datetime(2020, 1, 1).date(), 
                     max_value=datetime(2030, 12, 31).date()),
        period_of_day=st.sampled_from(['A', 'P', 'E']),
        session_id=st.one_of(st.none(), st.integers(min_value=1, max_value=10000)),
        file_content=st.binary(min_size=100, max_size=10000)
    )
    @settings(max_examples=100, deadline=None)
    def test_download_tracking_metadata_completeness_property(
        self, url, file_path, date, period_of_day, session_id, file_content
    ):
        """
        Feature: end-to-end-workflow-validation, Property 6:
        Download Tracking Metadata Completeness
        
        For any successfully downloaded PDF, the database record should include
        all required fields: original_url, file_path, date, period_of_day, 
        file_size, and downloaded_at timestamp.
        
        Validates: Requirements 4.1, 4.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create temporary database with schema
            db_path = Path(tmpdir) / 'test.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE downloaded_pdfs (
                    id INTEGER PRIMARY KEY,
                    original_url TEXT UNIQUE,
                    file_path TEXT,
                    date TEXT,
                    period_of_day TEXT CHECK(period_of_day IN ('A', 'P', 'E')),
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
            
            # Create test file with content
            storage.write(file_path, file_content)
            
            # Track download
            date_str = date.strftime('%Y-%m-%d')
            scraper._track_download(
                url,
                file_path,
                date_str,
                period_of_day,
                session_id
            )
            
            # Verify all required fields are present in database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT original_url, file_path, date, period_of_day, 
                       session_id, file_size, downloaded_at
                FROM downloaded_pdfs
                WHERE original_url = ?
            """, (url,))
            result = cursor.fetchone()
            conn.close()
            
            # Assert record exists
            assert result is not None, f"No record found for URL: {url}"
            
            # Assert all required fields are present
            db_url, db_file_path, db_date, db_period, db_session_id, db_file_size, db_timestamp = result
            
            # Verify original_url
            assert db_url == url, f"URL mismatch: expected {url}, got {db_url}"
            
            # Verify file_path
            assert db_file_path == file_path, f"File path mismatch: expected {file_path}, got {db_file_path}"
            
            # Verify date
            assert db_date == date_str, f"Date mismatch: expected {date_str}, got {db_date}"
            
            # Verify period_of_day
            assert db_period == period_of_day, f"Period mismatch: expected {period_of_day}, got {db_period}"
            
            # Verify session_id (can be None)
            assert db_session_id == session_id, f"Session ID mismatch: expected {session_id}, got {db_session_id}"
            
            # Verify file_size is present and matches actual file size
            assert db_file_size is not None, "File size should not be None for existing file"
            assert db_file_size == len(file_content), f"File size mismatch: expected {len(file_content)}, got {db_file_size}"
            
            # Verify downloaded_at timestamp is present
            assert db_timestamp is not None, "Downloaded timestamp should not be None"
            assert len(db_timestamp) > 0, "Downloaded timestamp should not be empty"
    
    @given(
        url=st.from_regex(r'https?://[a-z0-9\-\.]+\.[a-z]{2,}/[a-z0-9\-_/]+\.pdf', fullmatch=True),
        file_path=st.from_regex(r'hansard_\d{8}_[APE](?:_\d+)?\.pdf', fullmatch=True),
        date=st.one_of(st.none(), st.dates(min_value=datetime(2020, 1, 1).date(), 
                                           max_value=datetime(2030, 12, 31).date())),
        period_of_day=st.one_of(st.none(), st.sampled_from(['A', 'P', 'E'])),
        session_id=st.one_of(st.none(), st.integers(min_value=1, max_value=10000))
    )
    @settings(max_examples=100, deadline=None)
    def test_download_tracking_handles_null_values_property(
        self, url, file_path, date, period_of_day, session_id
    ):
        """
        Feature: end-to-end-workflow-validation, Property 6 (extended):
        Download Tracking with NULL Values
        
        For any download tracking call, the system should correctly handle
        NULL values for optional fields (date, period_of_day, session_id).
        
        Validates: Requirements 4.1, 4.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create temporary database with schema
            db_path = Path(tmpdir) / 'test.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE downloaded_pdfs (
                    id INTEGER PRIMARY KEY,
                    original_url TEXT UNIQUE,
                    file_path TEXT,
                    date TEXT,
                    period_of_day TEXT CHECK(period_of_day IN ('A', 'P', 'E') OR period_of_day IS NULL),
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
            
            # Track download with potentially NULL values
            date_str = date.strftime('%Y-%m-%d') if date else None
            scraper._track_download(
                url,
                file_path,
                date_str,
                period_of_day,
                session_id
            )
            
            # Verify record was created
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT original_url, file_path, date, period_of_day, session_id
                FROM downloaded_pdfs
                WHERE original_url = ?
            """, (url,))
            result = cursor.fetchone()
            conn.close()
            
            # Assert record exists
            assert result is not None, f"No record found for URL: {url}"
            
            # Verify values match (including NULLs)
            db_url, db_file_path, db_date, db_period, db_session_id = result
            
            assert db_url == url
            assert db_file_path == file_path
            assert db_date == date_str
            assert db_period == period_of_day
            assert db_session_id == session_id
    
    @given(
        url=st.from_regex(r'https?://[a-z0-9\-\.]+\.[a-z]{2,}/[a-z0-9\-_/]+\.pdf', fullmatch=True),
        file_path=st.from_regex(r'hansard_\d{8}_[APE](?:_\d+)?\.pdf', fullmatch=True),
        date=st.dates(min_value=datetime(2020, 1, 1).date(), 
                     max_value=datetime(2030, 12, 31).date()),
        period_of_day=st.sampled_from(['A', 'P', 'E']),
        file_content=st.binary(min_size=100, max_size=10000)
    )
    @settings(max_examples=100, deadline=None)
    def test_download_tracking_insert_or_replace_property(
        self, url, file_path, date, period_of_day, file_content
    ):
        """
        Feature: end-to-end-workflow-validation, Property 6 (extended):
        Download Tracking INSERT OR REPLACE Behavior
        
        For any URL that is tracked multiple times, the system should use
        INSERT OR REPLACE to update the existing record rather than creating
        duplicates.
        
        Validates: Requirements 4.1, 4.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create temporary database with schema
            db_path = Path(tmpdir) / 'test.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE downloaded_pdfs (
                    id INTEGER PRIMARY KEY,
                    original_url TEXT UNIQUE,
                    file_path TEXT,
                    date TEXT,
                    period_of_day TEXT CHECK(period_of_day IN ('A', 'P', 'E')),
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
            storage.write(file_path, file_content)
            
            # Track download first time
            date_str = date.strftime('%Y-%m-%d')
            scraper._track_download(
                url,
                file_path,
                date_str,
                period_of_day,
                None  # session_id initially None
            )
            
            # Track same URL again with different session_id
            new_session_id = 12345
            scraper._track_download(
                url,
                file_path,
                date_str,
                period_of_day,
                new_session_id
            )
            
            # Verify only one record exists (not duplicated)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM downloaded_pdfs WHERE original_url = ?", (url,))
            count = cursor.fetchone()[0]
            
            # Verify the record was updated (session_id should be new value)
            cursor.execute("""
                SELECT session_id FROM downloaded_pdfs WHERE original_url = ?
            """, (url,))
            result = cursor.fetchone()
            conn.close()
            
            # Assert only one record exists
            assert count == 1, f"Expected 1 record, found {count} for URL: {url}"
            
            # Assert session_id was updated
            assert result[0] == new_session_id, f"Session ID should be updated to {new_session_id}, got {result[0]}"


class TestSkipReasonLoggingProperty:
    """Property-based tests for skip reason logging."""
    
    @given(
        file_exists=st.booleans(),
        db_record_exists=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_skip_reason_logging_property(self, file_exists, db_record_exists):
        """
        Feature: end-to-end-workflow-validation, Property 5:
        Skip Reason Logging
        
        For any skipped download, the log should contain the reason
        (either "file_exists_with_record" or "file_exists_without_record").
        
        Validates: Requirements 3.7
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create temporary database with schema
            db_path = Path(tmpdir) / 'test.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE downloaded_pdfs (
                    id INTEGER PRIMARY KEY,
                    original_url TEXT UNIQUE,
                    file_path TEXT,
                    date TEXT,
                    period_of_day TEXT CHECK(period_of_day IN ('A', 'P', 'E')),
                    session_id INTEGER,
                    file_size INTEGER,
                    downloaded_at TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
            
            # Create scraper with database
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path=str(db_path), rate_limit_delay=0.1)
            
            # Setup test URL and filename
            test_url = 'https://example.com/test.pdf'
            # The filename that will be generated by download_pdf for this date/title
            # Since no files exist initially, it will be: hansard_20240101_P.pdf
            expected_filename = 'hansard_20240101_P.pdf'
            
            # Setup state based on test parameters
            # IMPORTANT: We need to use the SAME filename that download_pdf will generate
            if file_exists:
                storage.write(expected_filename, b'test content')
            
            if db_record_exists:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO downloaded_pdfs (original_url, file_path, date)
                    VALUES (?, ?, ?)
                """, (test_url, expected_filename, '2024-01-01'))
                conn.commit()
                conn.close()
            
            # Setup logging capture
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            
            # Get the logger used by the scraper
            scraper_logger = logging.getLogger('hansard_tales.scrapers.hansard_scraper')
            original_level = scraper_logger.level
            scraper_logger.setLevel(logging.INFO)
            scraper_logger.addHandler(handler)
            
            try:
                # Mock the session to avoid actual HTTP requests
                mock_response = Mock()
                mock_response.iter_content = Mock(return_value=[b'PDF content'])
                mock_response.raise_for_status = Mock()
                
                mock_session = Mock()
                mock_session.get = Mock(return_value=mock_response)
                scraper.session = mock_session
                
                # Call download_pdf which will internally call _check_existing_download
                scraper.download_pdf(test_url, 'Morning Session', '2024-01-01')
                
                # Get the log output
                log_output = log_stream.getvalue()
                
                # Determine expected behavior based on state
                # Case 1: file exists AND db record exists -> should skip with "file_exists_with_record"
                # Case 2: file exists but NO db record -> should skip with "file_exists_without_record"
                # Case 3: file NOT exists but db record exists -> should download with "file_missing_redownload"
                # Case 4: neither exists -> should download with "new_download"
                
                if file_exists and db_record_exists:
                    # Should skip with "file_exists_with_record"
                    assert 'Download skipped' in log_output, \
                        f"Expected 'Download skipped' in log for case (file_exists=True, db_record=True), but got: {log_output}"
                    assert 'file_exists_with_record' in log_output, \
                        f"Expected 'file_exists_with_record' in log, but got: {log_output}"
                
                elif file_exists and not db_record_exists:
                    # Should skip with "file_exists_without_record"
                    assert 'Download skipped' in log_output, \
                        f"Expected 'Download skipped' in log for case (file_exists=True, db_record=False), but got: {log_output}"
                    assert 'file_exists_without_record' in log_output, \
                        f"Expected 'file_exists_without_record' in log, but got: {log_output}"
                
                elif not file_exists and db_record_exists:
                    # Should download with "file_missing_redownload"
                    assert 'Downloading' in log_output, \
                        f"Expected 'Downloading' in log for case (file_exists=False, db_record=True), but got: {log_output}"
                    assert 'file_missing_redownload' in log_output, \
                        f"Expected 'file_missing_redownload' in log, but got: {log_output}"
                
                else:
                    # Should download with "new_download"
                    assert 'Downloading' in log_output, \
                        f"Expected 'Downloading' in log for case (file_exists=False, db_record=False), but got: {log_output}"
                    assert 'new_download' in log_output, \
                        f"Expected 'new_download' in log, but got: {log_output}"
                
            finally:
                # Cleanup: remove handler and restore original level
                scraper_logger.removeHandler(handler)
                scraper_logger.setLevel(original_level)
                handler.close()


class TestDownloadDecisionLogicProperties:
    """Property-based tests for download decision logic."""
    
    @given(
        file_exists=st.booleans(),
        db_record_exists=st.booleans(),
        url=st.from_regex(r'https?://[a-z0-9\-\.]+\.[a-z]{2,}/[a-z0-9\-_/]+\.pdf', fullmatch=True),
        filename=st.from_regex(r'hansard_\d{8}_[APE](?:_\d+)?\.pdf', fullmatch=True)
    )
    @settings(max_examples=100, deadline=None)
    def test_download_decision_logic_property(
        self, file_exists, db_record_exists, url, filename
    ):
        """
        Feature: end-to-end-workflow-validation, Property 4:
        Download Decision Logic
        
        For any URL and filename combination, the download decision should follow
        this logic:
        - Skip if file exists in storage AND in database (file_exists_with_record)
        - Skip and insert record if file exists in storage but NOT in database 
          (file_exists_without_record)
        - Download and update record if file NOT in storage but in database 
          (file_missing_redownload)
        - Download and insert record if file NOT in storage AND NOT in database 
          (new_download)
        
        Validates: Requirements 3.2, 3.3, 3.4, 3.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create temporary database with schema
            db_path = Path(tmpdir) / 'test.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE downloaded_pdfs (
                    id INTEGER PRIMARY KEY,
                    original_url TEXT UNIQUE,
                    file_path TEXT,
                    date TEXT,
                    period_of_day TEXT CHECK(period_of_day IN ('A', 'P', 'E') OR period_of_day IS NULL),
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
            
            # Setup state based on test parameters
            if file_exists:
                # Create file in storage
                storage.write(filename, b'test content')
            
            if db_record_exists:
                # Insert record in database
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO downloaded_pdfs (original_url, file_path, date)
                    VALUES (?, ?, '2024-01-01')
                """, (url, filename))
                conn.commit()
                conn.close()
            
            # Check download decision
            should_skip, reason = scraper._check_existing_download(url, filename, '2024-01-01', 'P')
            
            # Verify logic based on all 4 cases
            if file_exists and db_record_exists:
                # Case 1: File exists in storage AND in database
                assert should_skip is True, \
                    f"Case 1: Should skip when file exists and DB record exists"
                assert reason == "file_exists_with_record", \
                    f"Case 1: Expected reason 'file_exists_with_record', got '{reason}'"
            
            elif file_exists and not db_record_exists:
                # Case 2: File exists in storage but NOT in database
                assert should_skip is True, \
                    f"Case 2: Should skip when file exists but no DB record"
                assert reason == "file_exists_without_record", \
                    f"Case 2: Expected reason 'file_exists_without_record', got '{reason}'"
                
                # Verify that a tracking record was inserted
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM downloaded_pdfs WHERE original_url = ?",
                    (url,)
                )
                count = cursor.fetchone()[0]
                conn.close()
                
                assert count == 1, \
                    f"Case 2: Expected tracking record to be inserted, found {count} records"
            
            elif not file_exists and db_record_exists:
                # Case 3: File NOT in storage but in database
                assert should_skip is False, \
                    f"Case 3: Should NOT skip when file missing but DB record exists"
                assert reason == "file_missing_redownload", \
                    f"Case 3: Expected reason 'file_missing_redownload', got '{reason}'"
            
            else:
                # Case 4: File NOT in storage AND NOT in database
                assert should_skip is False, \
                    f"Case 4: Should NOT skip when neither file nor DB record exists"
                assert reason == "new_download", \
                    f"Case 4: Expected reason 'new_download', got '{reason}'"
