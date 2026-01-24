"""
Property-based tests for logging completeness.

This module tests that all operations are properly logged according to
the requirements:
- Property 11: Download Attempt Logging
- Property 12: Database Operation Logging
- Property 13: File Operation Logging

Feature: end-to-end-workflow-validation
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
from hypothesis import given, settings
from hypothesis import strategies as st

from hansard_tales.database.db_manager import DatabaseManager
from hansard_tales.database.db_updater import DatabaseUpdater
from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.storage.filesystem import FilesystemStorage


# ============================================================================
# Property 11: Download Attempt Logging
# ============================================================================

@given(
    url=st.text(min_size=10, max_size=100).map(lambda x: f"http://example.com/{x}.pdf"),
    title=st.text(min_size=5, max_size=50),
    date=st.dates(min_value=datetime.date(2020, 1, 1), max_value=datetime.date(2030, 12, 31)).map(str),
    should_succeed=st.booleans()
)
@settings(max_examples=10, deadline=None)  # Reduced from 100 to meet 5s performance target
def test_property_11_download_attempt_logging(url, title, date, should_succeed):
    """
    Feature: end-to-end-workflow-validation, Property 11: Download Attempt Logging
    
    For any download attempt, the log should contain the URL, filename, and result
    (success, skip, or fail).
    
    Validates: Requirements 11.1
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
        handler.setLevel(logging.INFO)
        logger = logging.getLogger('hansard_tales.scrapers.hansard_scraper')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        try:
            # Mock the HTTP request
            with patch.object(scraper.session, 'get') as mock_get:
                if should_succeed:
                    # Successful download
                    mock_response = Mock()
                    mock_response.iter_content.return_value = [b'test content']
                    mock_response.raise_for_status.return_value = None
                    mock_get.return_value = mock_response
                else:
                    # Failed download
                    mock_get.side_effect = requests.RequestException("Network error")
                
                # Attempt download
                result = scraper.download_pdf(url, title, date)
                
                # Get log output
                log_output = log_stream.getvalue()
                
                # Verify logging requirements
                # 1. URL must be in log
                assert url in log_output, f"URL not found in log: {url}"
                
                # 2. Result must be in log (success, skipped, or failed)
                if should_succeed:
                    assert 'result=success' in log_output or 'result=skipped' in log_output, \
                        "Success/skip result not logged"
                else:
                    assert 'result=failed' in log_output, "Failed result not logged"
                
                # 3. Filename should be in log
                assert 'filename=' in log_output, "Filename not logged"
                
                # 4. Download attempt should be logged
                assert 'Download attempt:' in log_output, "Download attempt not logged"
        
        finally:
            logger.removeHandler(handler)


# ============================================================================
# Property 12: Database Operation Logging
# ============================================================================

@given(
    mp_name=st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
    operation_type=st.sampled_from(['INSERT', 'UPDATE', 'DELETE', 'SELECT'])
)
@settings(max_examples=10, deadline=None)  # Reduced from 100 to meet 5s performance target
def test_property_12_database_operation_logging(mp_name, operation_type):
    """
    Feature: end-to-end-workflow-validation, Property 12: Database Operation Logging
    
    For any database operation, the log should contain the table name and operation type
    (INSERT, UPDATE, DELETE).
    
    Validates: Requirements 11.2
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup database
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE parliamentary_terms (
                id INTEGER PRIMARY KEY,
                name TEXT,
                start_date DATE,
                end_date DATE,
                is_current INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            INSERT INTO parliamentary_terms (name, start_date, end_date, is_current)
            VALUES ('Test Term', '2020-01-01', '2025-12-31', 1)
        """)
        cursor.execute("""
            CREATE TABLE mps (
                id INTEGER PRIMARY KEY,
                name TEXT,
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
        handler.setLevel(logging.DEBUG)
        
        # Add handler to both loggers
        logger_updater = logging.getLogger('hansard_tales.database.db_updater')
        logger_updater.addHandler(handler)
        logger_updater.setLevel(logging.DEBUG)
        
        logger_manager = logging.getLogger('hansard_tales.database.db_manager')
        logger_manager.addHandler(handler)
        logger_manager.setLevel(logging.DEBUG)
        
        try:
            # Perform database operation based on type
            conn = updater.get_connection()
            cursor = conn.cursor()
            
            if operation_type in ['INSERT', 'SELECT']:
                # This will trigger INSERT or SELECT logging
                mp_id = updater.get_or_create_mp(cursor, mp_name, "Test Constituency", "Test Party")
                conn.commit()
            elif operation_type == 'UPDATE':
                # First create an MP
                mp_id = updater.get_or_create_mp(cursor, mp_name, "Test Constituency", "Test Party")
                conn.commit()
                # Then link to term (triggers UPDATE-like operations)
                updater.link_mp_to_current_term(cursor, mp_id, "Test Constituency", "Test Party")
                conn.commit()
            elif operation_type == 'DELETE':
                # For DELETE, we'll test the db_manager clean operation instead
                # First create an MP to have data
                mp_id = updater.get_or_create_mp(cursor, mp_name, "Test Constituency", "Test Party")
                conn.commit()
                conn.close()
                
                # Now test DELETE via db_manager
                manager = DatabaseManager()
                manager.clean(str(db_path), preserve_tables=['downloaded_pdfs'], confirm=False)
                
                # Get log output
                log_output = log_stream.getvalue()
                
                # Verify DELETE logging
                assert 'Database operation: DELETE' in log_output, "DELETE operation not logged"
                assert 'table=' in log_output, "Table name not logged for DELETE"
                return  # Early return for DELETE case
            
            conn.close()
            
            # Get log output
            log_output = log_stream.getvalue()
            
            # Verify logging requirements
            # 1. Operation type should be in log
            assert 'Database operation:' in log_output, "Database operation not logged"
            
            # 2. Table name should be in log
            assert 'table=' in log_output, "Table name not logged"
            
            # 3. For INSERT operations, verify INSERT is logged
            if operation_type == 'INSERT':
                assert 'INSERT' in log_output, "INSERT operation not logged"
            
            # 4. For SELECT operations, verify SELECT is logged
            if operation_type == 'SELECT':
                assert 'SELECT' in log_output, "SELECT operation not logged"
        
        finally:
            logger_updater.removeHandler(handler)
            logger_manager.removeHandler(handler)


# ============================================================================
# Property 13: File Operation Logging
# ============================================================================

@given(
    filename=st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))).map(
        lambda x: f"{x}.pdf"
    ),
    operation=st.sampled_from(['write', 'delete', 'move']),
    content_size=st.integers(min_value=100, max_value=10000)
)
@settings(max_examples=10, deadline=None)  # Reduced from 100 to meet 5s performance target
def test_property_13_file_operation_logging(filename, operation, content_size):
    """
    Feature: end-to-end-workflow-validation, Property 13: File Operation Logging
    
    For any file operation (move, delete, write), the log should contain the source
    and destination paths.
    
    Validates: Requirements 11.3
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup storage
        storage = FilesystemStorage(tmpdir)
        
        # Capture logs
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.INFO)
        logger = logging.getLogger('hansard_tales.storage.filesystem')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        try:
            # Perform file operation
            if operation == 'write':
                content = b'x' * content_size
                storage.write(filename, content)
                
                # Get log output
                log_output = log_stream.getvalue()
                
                # Verify logging requirements
                assert 'File operation: WRITE' in log_output, "WRITE operation not logged"
                assert f'path={filename}' in log_output, "File path not logged"
                assert f'size={content_size}' in log_output, "File size not logged"
            
            elif operation == 'delete':
                # First create a file
                content = b'x' * content_size
                storage.write(filename, content)
                log_stream.truncate(0)
                log_stream.seek(0)
                
                # Then delete it
                storage.delete(filename)
                
                # Get log output
                log_output = log_stream.getvalue()
                
                # Verify logging requirements
                assert 'File operation: DELETE' in log_output, "DELETE operation not logged"
                assert f'path={filename}' in log_output, "File path not logged"
            
            elif operation == 'move':
                # First create a file
                content = b'x' * content_size
                storage.write(filename, content)
                log_stream.truncate(0)
                log_stream.seek(0)
                
                # Then move it
                new_filename = f"moved_{filename}"
                storage.move(filename, new_filename)
                
                # Get log output
                log_output = log_stream.getvalue()
                
                # Verify logging requirements
                assert 'File operation: MOVE' in log_output, "MOVE operation not logged"
                assert f'src={filename}' in log_output, "Source path not logged"
                assert f'dest={new_filename}' in log_output, "Destination path not logged"
        
        finally:
            logger.removeHandler(handler)


# ============================================================================
# Additional Logging Tests
# ============================================================================

def test_skip_reason_logging():
    """
    Test that skip reasons are properly logged.
    
    This verifies that when a download is skipped, the reason is included
    in the log message.
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
        handler.setLevel(logging.INFO)
        logger = logging.getLogger('hansard_tales.scrapers.hansard_scraper')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        try:
            # Create a file to trigger skip
            test_content = b'test content'
            storage.write('hansard_20240101_P.pdf', test_content)
            
            # Mock the HTTP request
            with patch.object(scraper.session, 'get') as mock_get:
                mock_response = Mock()
                mock_response.iter_content.return_value = [test_content]
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response
                
                # Attempt download (should be skipped)
                result = scraper.download_pdf(
                    "http://example.com/test.pdf",
                    "Test Session",
                    "2024-01-01"
                )
                
                # Get log output
                log_output = log_stream.getvalue()
                
                # Verify skip reason is logged
                assert 'reason=' in log_output, "Skip reason not logged"
                assert 'result=skipped' in log_output, "Skip result not logged"
        
        finally:
            logger.removeHandler(handler)


def test_database_clean_operation_logging():
    """
    Test that database clean operations are properly logged.
    
    This verifies that DELETE operations during clean are logged with
    table names.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup database
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create test tables
        cursor.execute("CREATE TABLE test_table1 (id INTEGER PRIMARY KEY)")
        cursor.execute("CREATE TABLE test_table2 (id INTEGER PRIMARY KEY)")
        cursor.execute("CREATE TABLE downloaded_pdfs (id INTEGER PRIMARY KEY)")
        cursor.execute("INSERT INTO test_table1 VALUES (1)")
        cursor.execute("INSERT INTO test_table2 VALUES (1)")
        conn.commit()
        conn.close()
        
        # Create manager
        manager = DatabaseManager()
        
        # Capture logs
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.INFO)
        logger = logging.getLogger('hansard_tales.database.db_manager')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        try:
            # Clean database (without confirmation)
            manager.clean(str(db_path), confirm=False)
            
            # Get log output
            log_output = log_stream.getvalue()
            
            # Verify logging requirements
            assert 'Database operation: DELETE' in log_output, "DELETE operation not logged"
            assert 'table=' in log_output, "Table name not logged"
            assert 'test_table1' in log_output or 'test_table2' in log_output, \
                "Specific table name not logged"
        
        finally:
            logger.removeHandler(handler)
