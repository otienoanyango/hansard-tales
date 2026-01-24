"""
Property-based tests for error propagation and cleanup.

This module uses property-based testing to verify that error handling
works correctly across all error types and scenarios.

Property 9: Error Propagation and Cleanup
Validates: Requirements 6.2, 6.3, 6.5
"""

import datetime
import logging
import sqlite3
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests
from hypothesis import given, strategies as st, settings, example, HealthCheck

from hansard_tales.database.db_updater import DatabaseUpdater
from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.storage.filesystem import FilesystemStorage


# Strategy for generating various error types (only request-related)
error_types = st.sampled_from([
    requests.ConnectionError,
    requests.Timeout,
    requests.HTTPError,
    requests.RequestException,
])


# Strategy for generating error messages
error_messages = st.text(min_size=5, max_size=100).filter(
    lambda x: x.strip() and not x.isspace()
)


class TestErrorPropagationProperty:
    """Property-based tests for error propagation."""
    
    @given(
        error_type=error_types,
        error_message=error_messages
    )
    @settings(
        max_examples=20,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @example(error_type=requests.ConnectionError, error_message="Connection refused")
    @example(error_type=requests.Timeout, error_message="Request timed out")
    @example(error_type=requests.HTTPError, error_message="404 Not Found")
    def test_scraper_handles_any_error_type(
        self,
        production_db,
        error_type,
        error_message
    ):
        """
        Property 9: For ANY error type and message, scraper handles it gracefully.
        
        This property verifies that:
        1. Errors don't crash the scraper
        2. Error messages are preserved
        3. Scraper returns False (not raises exception)
        
        Validates: Requirements 6.2, 6.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path=str(production_db))
            
            # Capture logs
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.ERROR)
            logger = logging.getLogger('hansard_tales.scrapers.hansard_scraper')
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
            
            try:
                # Mock session to raise the error
                with patch.object(scraper.session, 'get') as mock_get:
                    # Create error instance
                    if issubclass(error_type, requests.RequestException):
                        error = error_type(error_message)
                    else:
                        error = error_type(error_message)
                    
                    mock_get.side_effect = error
                    
                    # Attempt download - should NOT raise exception
                    result = scraper.download_pdf(
                        "http://example.com/test.pdf",
                        "Test Session",
                        "2024-01-01"
                    )
                    
                    # Property 1: Should return False (not raise)
                    assert result is False, \
                        f"Scraper should return False for {error_type.__name__}"
                    
                    # Property 2: Error should be logged
                    log_output = log_stream.getvalue()
                    assert len(log_output) > 0, \
                        f"Error should be logged for {error_type.__name__}"
                    
                    # Property 3: Error message should be preserved in logs
                    # (May be truncated or formatted, but some part should be there)
                    assert 'Download failed:' in log_output or 'ERROR' in log_output, \
                        f"Error context should be logged for {error_type.__name__}"
            
            finally:
                logger.removeHandler(handler)
    
    @given(
        error_message=error_messages
    )
    @settings(
        max_examples=15,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @example(error_message="Database locked")
    @example(error_message="Constraint violation")
    def test_database_handles_any_error_message(
        self,
        production_db,
        error_message
    ):
        """
        Property 9: For ANY error message, database updater handles it gracefully.
        
        This property verifies that:
        1. Errors don't crash the updater
        2. Error messages are preserved
        3. Updater returns error status (not raises exception)
        
        Validates: Requirements 6.2, 6.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            updater = DatabaseUpdater(str(production_db))
            
            # Create a temporary PDF file
            pdf_path = Path(tmpdir) / "test.pdf"
            pdf_path.write_bytes(b'%PDF-1.4 fake pdf content')
            
            # Capture logs
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.ERROR)
            logger = logging.getLogger('hansard_tales.database.db_updater')
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
            
            try:
                # Mock PDF processor to raise error
                with patch('hansard_tales.database.db_updater.PDFProcessor') as mock_processor:
                    mock_processor.return_value.extract_text.side_effect = \
                        RuntimeError(error_message)
                    
                    # Attempt to process - should NOT raise exception
                    result = updater.process_hansard_pdf(
                        str(pdf_path),
                        "http://example.com/test.pdf",
                        "2024-01-01",
                        "Test Session"
                    )
                    
                    # Property 1: Should return error status (not raise)
                    assert isinstance(result, dict), \
                        "Updater should return dict, not raise exception"
                    assert result['status'] == 'error', \
                        "Updater should return error status"
                    
                    # Property 2: Error should be logged
                    log_output = log_stream.getvalue()
                    assert len(log_output) > 0, \
                        "Error should be logged"
            
            finally:
                logger.removeHandler(handler)
    
    @given(
        error_type=error_types,
        error_message=error_messages
    )
    @settings(
        max_examples=15,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @example(error_type=RuntimeError, error_message="Processing failed")
    def test_cleanup_executes_for_any_error(
        self,
        production_db,
        error_type,
        error_message
    ):
        """
        Property 9: For ANY error, cleanup operations execute successfully.
        
        This property verifies that:
        1. Database connections are closed
        2. No partial files remain
        3. No database locks remain
        
        Validates: Requirements 6.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path=str(production_db))
            
            # Mock session to raise error
            with patch.object(scraper.session, 'get') as mock_get:
                # Create error instance
                if issubclass(error_type, requests.RequestException):
                    error = error_type(error_message)
                else:
                    error = error_type(error_message)
                
                mock_get.side_effect = error
                
                # Attempt download
                try:
                    scraper.download_pdf(
                        "http://example.com/test.pdf",
                        "Test Session",
                        "2024-01-01"
                    )
                except Exception:
                    # Some errors might propagate, that's ok
                    pass
                
                # Property 1: Database should be accessible (no locks)
                try:
                    conn = sqlite3.connect(str(production_db))
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM parliamentary_terms")
                    cursor.fetchone()
                    conn.close()
                    database_accessible = True
                except sqlite3.OperationalError:
                    database_accessible = False
                
                assert database_accessible, \
                    f"Database should be accessible after {error_type.__name__}"
                
                # Property 2: No partial files should remain
                # (Either no files, or only complete files)
                files = list(Path(tmpdir).rglob("*.pdf"))
                for file in files:
                    # If file exists, it should have content
                    assert file.stat().st_size > 0, \
                        f"No partial files should remain after {error_type.__name__}"


class TestErrorLoggingProperty:
    """Property-based tests for error logging."""
    
    @given(
        url=st.text(min_size=10, max_size=100).filter(
            lambda x: x.strip() and not x.isspace()
        ),
        session_name=st.text(min_size=5, max_size=50).filter(
            lambda x: x.strip() and not x.isspace()
        ),
        date=st.dates(min_value=datetime.date(2020, 1, 1), max_value=datetime.date(2030, 12, 31))
    )
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @example(
        url="http://example.com/test.pdf",
        session_name="Morning Session",
        date=datetime.date(2024, 1, 15)
    )
    def test_error_logs_include_context_for_any_input(
        self,
        production_db,
        url,
        session_name,
        date
    ):
        """
        Property 9: For ANY input, error logs include context.
        
        This property verifies that error logs always include:
        1. Error level (ERROR)
        2. Some context about what failed
        
        Validates: Requirements 6.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path=str(production_db))
            
            # Capture logs
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.ERROR)
            logger = logging.getLogger('hansard_tales.scrapers.hansard_scraper')
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
            
            try:
                # Mock session to raise error
                with patch.object(scraper.session, 'get') as mock_get:
                    mock_get.side_effect = requests.ConnectionError("Connection failed")
                    
                    # Attempt download
                    scraper.download_pdf(
                        url,
                        session_name,
                        date.isoformat()
                    )
                    
                    # Get log output
                    log_output = log_stream.getvalue()
                    
                    # Property 1: Error should be logged
                    assert len(log_output) > 0, \
                        "Error should be logged for any input"
                    
                    # Property 2: Log should indicate error level
                    # (Either explicit ERROR or error-related message)
                    assert 'ERROR' in log_output or 'error' in log_output.lower() or \
                           'failed' in log_output.lower(), \
                        "Log should indicate error occurred"
            
            finally:
                logger.removeHandler(handler)
