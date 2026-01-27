"""
Shared test fixtures for Hansard Tales test suite.

This module provides common fixtures used across multiple test modules
to avoid duplication and ensure consistency.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from hansard_tales.database.init_db import initialize_database
# from hansard_tales.database.migrate_pdf_tracking import migrate_pdf_tracking
from tests.fixtures.html_samples import ParliamentHTMLSamples


@pytest.fixture
def production_db():
    """
    Create temporary database with production schema.
    
    This fixture MUST be used by all tests that need a database.
    It ensures schema consistency by using the production initialize_database() function.
    
    The fixture:
    1. Creates a temporary database file
    2. Calls initialize_database() from production code
    3. Runs all migrations automatically
    4. Inserts the current parliamentary term (term 13, 2022-09-08 to 2027-09-07)
    5. Yields the database path
    6. Cleans up the temporary file
    
    Validates: Requirements 3.1, 3.2, 3.5
    """
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Use production initialization
    initialize_database(db_path)
    
    # Run PDF tracking migration (commented out - migration module doesn't exist)
    # migrate_pdf_tracking(db_path, source_dir="data/pdfs", dry_run=False)
    
    # Insert current parliamentary term (required for most operations)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO parliamentary_terms (term_number, start_date, end_date, is_current)
        VALUES (13, '2022-09-08', '2027-09-07', 1)
    """)
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink()


@pytest.fixture
def temp_db():
    """
    DEPRECATED: Use production_db fixture instead.
    
    This fixture is kept for backward compatibility but should not be used
    in new tests. It creates a custom schema that may diverge from production.
    
    Use production_db to ensure schema consistency.
    """
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    conn = sqlite3.Connection(db_path)
    cursor = conn.cursor()
    
    # Create minimal schema for testing
    cursor.execute("""
        CREATE TABLE parliamentary_terms (
            id INTEGER PRIMARY KEY,
            term_number INTEGER,
            start_date DATE,
            end_date DATE,
            is_current BOOLEAN DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE mps (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            constituency TEXT,
            party TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE hansard_sessions (
            id INTEGER PRIMARY KEY,
            term_id INTEGER,
            date DATE,
            title TEXT,
            pdf_url TEXT,
            pdf_path TEXT,
            processed BOOLEAN DEFAULT 0,
            FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id),
            UNIQUE(date, title)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE statements (
            id INTEGER PRIMARY KEY,
            mp_id INTEGER,
            session_id INTEGER,
            text TEXT,
            page_number INTEGER,
            bill_reference TEXT,
            content_hash TEXT,
            FOREIGN KEY (mp_id) REFERENCES mps(id),
            FOREIGN KEY (session_id) REFERENCES hansard_sessions(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE downloaded_pdfs (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE,
            filename TEXT,
            download_date TIMESTAMP,
            file_size INTEGER
        )
    """)
    
    # Insert current term
    cursor.execute("""
        INSERT INTO parliamentary_terms (term_number, start_date, end_date, is_current)
        VALUES (13, '2022-09-08', '2027-09-07', 1)
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink()


@pytest.fixture
def temp_pdf_dir():
    """Create temporary directory with sample PDFs."""
    import shutil
    temp_dir = tempfile.mkdtemp()
    pdf_dir = Path(temp_dir) / "pdfs" / "hansard-report"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample PDF files (empty files with correct names)
    sample_pdfs = [
        "20240101_0_P.pdf",
        "20240115_0_A.pdf",
        "20240201_0_P.pdf",
        "Hansard_Report_2024-03-15.pdf",
    ]
    
    for pdf_name in sample_pdfs:
        (pdf_dir / pdf_name).touch()
    
    yield pdf_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory."""
    import shutil
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mocked_parliament_http():
    """
    Mock HTTP responses from parliament.go.ke.
    
    This fixture MUST be used before creating any scraper instances to prevent
    real network calls. It mocks requests.Session at the module level before
    object instantiation.
    
    The fixture provides:
    1. Mocked requests.Session class
    2. Realistic HTML responses from ParliamentHTMLSamples
    3. Proper response attributes (text, status_code, raise_for_status)
    4. Returns the mock session for test assertions
    
    Usage:
        def test_scraper(mocked_parliament_http):
            # HTTP is already mocked before this point
            scraper = HansardScraper(storage=storage)
            
            # Test operations (no real network calls)
            result = scraper.scrape_hansard_page(1)
            
            # Verify mock was called
            assert mocked_parliament_http.get.called
    
    Validates: Requirements 4.1, 4.4, 4.5
    """
    with patch('hansard_tales.scrapers.hansard_scraper.requests.Session') as mock_session_class:
        # Create mock session instance
        mock_session = Mock()
        
        # Setup realistic response using HTML from fixtures
        mock_response = Mock()
        mock_response.text = ParliamentHTMLSamples.HANSARD_LIST_PAGE
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()  # No-op for successful responses
        
        # Configure session to return the mock response
        mock_session.get.return_value = mock_response
        
        # Configure the Session class to return our mock session
        mock_session_class.return_value = mock_session
        
        yield mock_session
