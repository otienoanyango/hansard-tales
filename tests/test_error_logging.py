"""
Unit tests for error logging with stack traces.

This module tests that all error logging includes full error messages
and stack traces as required by Requirement 11.4.
"""

import logging
import sqlite3
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from hansard_tales.database.db_manager import DatabaseManager
from hansard_tales.database.db_updater import DatabaseUpdater
from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.storage.filesystem import FilesystemStorage
from hansard_tales.workflow.orchestrator import WorkflowOrchestrator


class TestErrorLoggingWithStackTraces:
    """Test that error logging includes stack traces."""
    
    def test_scraper_download_error_includes_stack_trace(self):
        """
        Test that download errors include stack trace.
        
        Validates: Requirements 11.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            storage = FilesystemStorage(tmpdir)
            db_path = Path(tmpdir) / "test.db"
            
            # Initialize database
            conn = sqlite3.connect(str(db_path))
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
            
            # Create scraper
            scraper = HansardScraper(storage=storage, db_path=str(db_path))
            
            # Capture logs
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.ERROR)
            logger = logging.getLogger('hansard_tales.scrapers.hansard_scraper')
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
            
            try:
                # Mock the HTTP request to raise an exception
                with patch.object(scraper.session, 'get') as mock_get:
                    mock_get.side_effect = requests.RequestException("Network error")
                    
                    # Attempt download (should fail)
                    result = scraper.download_pdf(
                        "http://example.com/test.pdf",
                        "Test Session",
                        "2024-01-01"
                    )
                    
                    # Get log output
                    log_output = log_stream.getvalue()
                    
                    # Verify error logging includes stack trace
                    assert 'Download failed:' in log_output, "Error message not logged"
                    assert 'Network error' in log_output, "Error details not logged"
                    assert 'Traceback' in log_output, "Stack trace not logged"
                    assert result is False, "Download should have failed"
            
            finally:
                logger.removeHandler(handler)
    
    def test_database_updater_error_includes_stack_trace(self):
        """
        Test that database processing errors include stack trace.
        
        Validates: Requirements 11.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup database with missing table to trigger error
            db_path = Path(tmpdir) / "test.db"
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            # Create minimal schema (missing required tables)
            cursor.execute("""
                CREATE TABLE parliamentary_terms (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    is_current INTEGER
                )
            """)
            conn.commit()
            conn.close()
            
            # Create updater
            updater = DatabaseUpdater(str(db_path))
            
            # Capture logs
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.ERROR)
            logger = logging.getLogger('hansard_tales.database.db_updater')
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
            
            try:
                # Create a temporary PDF file
                pdf_path = Path(tmpdir) / "test.pdf"
                pdf_path.write_bytes(b'%PDF-1.4 fake pdf content')
                
                # Attempt to process (should fail due to missing tables)
                result = updater.process_hansard_pdf(
                    str(pdf_path),
                    "http://example.com/test.pdf",
                    "2024-01-01",
                    "Test Session"
                )
                
                # Get log output
                log_output = log_stream.getvalue()
                
                # Verify error logging includes stack trace
                assert 'Error processing Hansard:' in log_output, "Error message not logged"
                assert 'Traceback' in log_output, "Stack trace not logged"
                assert result['status'] == 'error', "Should return error status"
            
            finally:
                logger.removeHandler(handler)
    
    def test_database_manager_clean_error_includes_stack_trace(self):
        """
        Test that database clean errors include stack trace.
        
        Validates: Requirements 11.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup database
            db_path = Path(tmpdir) / "test.db"
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY)")
            conn.commit()
            conn.close()
            
            # Create manager
            manager = DatabaseManager()
            
            # Capture logs
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.ERROR)
            logger = logging.getLogger('hansard_tales.database.db_manager')
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
            
            try:
                # Mock cursor.execute to raise an error
                with patch('sqlite3.connect') as mock_connect:
                    mock_conn = Mock()
                    mock_cursor = Mock()
                    mock_cursor.execute.side_effect = sqlite3.Error("Database locked")
                    mock_conn.cursor.return_value = mock_cursor
                    mock_connect.return_value = mock_conn
                    
                    # Attempt clean (should fail)
                    with pytest.raises(sqlite3.Error):
                        manager.clean(str(db_path), confirm=False)
                    
                    # Get log output
                    log_output = log_stream.getvalue()
                    
                    # Verify error logging includes stack trace
                    assert 'Database error during clean:' in log_output, "Error message not logged"
                    assert 'Database locked' in log_output, "Error details not logged"
                    assert 'Traceback' in log_output, "Stack trace not logged"
            
            finally:
                logger.removeHandler(handler)
    
    def test_workflow_orchestrator_error_includes_stack_trace(self):
        """
        Test that workflow orchestrator errors include stack trace.
        
        Validates: Requirements 11.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            db_path = Path(tmpdir) / "test.db"
            storage = FilesystemStorage(tmpdir)
            
            # Create orchestrator
            orchestrator = WorkflowOrchestrator(
                db_path=str(db_path),
                storage=storage
            )
            
            # Capture logs
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.ERROR)
            logger = logging.getLogger('hansard_tales.workflow.orchestrator')
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
            
            try:
                # Mock _scrape_mps to raise an exception
                with patch.object(orchestrator, '_scrape_mps') as mock_scrape:
                    mock_scrape.side_effect = Exception("MP scraping failed")
                    
                    # Run workflow (should catch exception and log it)
                    try:
                        result = orchestrator.run_full_workflow()
                    except Exception:
                        # Exception is expected to be raised
                        pass
                    
                    # Get log output
                    log_output = log_stream.getvalue()
                    
                    # Verify error logging includes stack trace
                    assert 'Workflow failed:' in log_output, "Error message not logged"
                    assert 'MP scraping failed' in log_output, "Error details not logged"
                    assert 'Traceback' in log_output, "Stack trace not logged"
            
            finally:
                logger.removeHandler(handler)
    
    def test_error_logging_format(self):
        """
        Test that error logging uses exc_info=True for stack traces.
        
        This test verifies that the logging format includes the full
        exception information including traceback.
        
        Validates: Requirements 11.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            storage = FilesystemStorage(tmpdir)
            db_path = Path(tmpdir) / "test.db"
            
            # Initialize database
            conn = sqlite3.connect(str(db_path))
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
            
            # Create scraper
            scraper = HansardScraper(storage=storage, db_path=str(db_path))
            
            # Capture logs with detailed format
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.ERROR)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger = logging.getLogger('hansard_tales.scrapers.hansard_scraper')
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
            
            try:
                # Mock the HTTP request to raise a specific exception
                with patch.object(scraper.session, 'get') as mock_get:
                    mock_get.side_effect = requests.ConnectionError("Connection refused")
                    
                    # Attempt download (should fail)
                    result = scraper.download_pdf(
                        "http://example.com/test.pdf",
                        "Test Session",
                        "2024-01-01"
                    )
                    
                    # Get log output
                    log_output = log_stream.getvalue()
                    
                    # Verify comprehensive error logging
                    assert 'ERROR' in log_output, "Error level not logged"
                    assert 'Download failed:' in log_output, "Error message not logged"
                    assert 'Connection refused' in log_output, "Exception message not logged"
                    assert 'Traceback (most recent call last):' in log_output, \
                        "Stack trace header not logged"
                    assert 'ConnectionError' in log_output, \
                        "Exception type not logged"
            
            finally:
                logger.removeHandler(handler)
    
    def test_multiple_error_types_logged_with_stack_traces(self):
        """
        Test that different error types all include stack traces.
        
        Validates: Requirements 11.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            storage = FilesystemStorage(tmpdir)
            db_path = Path(tmpdir) / "test.db"
            
            # Initialize database
            conn = sqlite3.connect(str(db_path))
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
            
            # Create scraper
            scraper = HansardScraper(storage=storage, db_path=str(db_path))
            
            # Capture logs
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.ERROR)
            logger = logging.getLogger('hansard_tales.scrapers.hansard_scraper')
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
            
            try:
                # Test different error types
                error_types = [
                    requests.Timeout("Request timeout"),
                    requests.HTTPError("404 Not Found"),
                    requests.ConnectionError("Connection refused"),
                ]
                
                for error in error_types:
                    log_stream.truncate(0)
                    log_stream.seek(0)
                    
                    with patch.object(scraper.session, 'get') as mock_get:
                        mock_get.side_effect = error
                        
                        # Attempt download (should fail)
                        result = scraper.download_pdf(
                            "http://example.com/test.pdf",
                            "Test Session",
                            "2024-01-01"
                        )
                        
                        # Get log output
                        log_output = log_stream.getvalue()
                        
                        # Verify error logging includes stack trace for each error type
                        assert 'Download failed:' in log_output, \
                            f"Error message not logged for {type(error).__name__}"
                        assert 'Traceback' in log_output, \
                            f"Stack trace not logged for {type(error).__name__}"
                        assert str(error) in log_output, \
                            f"Error details not logged for {type(error).__name__}"
            
            finally:
                logger.removeHandler(handler)
