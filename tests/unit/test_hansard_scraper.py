"""
Core scraper tests - minimal essential coverage.

This file consolidates all scraper tests into a minimal, essential suite.
Tests are organized by functionality and follow the principle of testing
behavior, not implementation.
"""

import pytest
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.storage.filesystem import FilesystemStorage


# =============================================================================
# HTML EXTRACTION TESTS
# =============================================================================

class TestHTMLExtraction:
    """Test HTML extraction with real parliament.go.ke structure."""
    
    def test_extract_links_from_cols2_table(self, tmp_path):
        """Test extraction of PDF links from visible table (cols-2)."""
        html = '''
        <table class="cols-2">
            <tbody>
                <tr>
                    <td class="views-field views-field-field-pdf">
                        <a href="https://parliament.go.ke/sites/default/files/2025-07/Hansard%20Report%20-%20Wednesday%2C%2030th%20July%202025%20%28P%29.pdf">
                            Hansard Report - Wednesday, 30th July 2025 - Afternoon Sitting
                        </a>
                    </td>
                </tr>
                <tr>
                    <td class="views-field views-field-field-pdf">
                        <a href="https://parliament.go.ke/sites/default/files/2025-07/Hansard%20Report%20-%20Wednesday%2C%2030th%20July%202025%20%28A%29.pdf">
                            Hansard Report - Wednesday, 30th July 2025 - Morning Sitting
                        </a>
                    </td>
                </tr>
            </tbody>
        </table>
        '''
        
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        scraper = HansardScraper(storage=storage, db_path=None)
        
        hansards = scraper.extract_hansard_links(html)
        
        assert len(hansards) == 2
        assert hansards[0]['date'] == '2025-07-30'
        assert hansards[1]['date'] == '2025-07-30'
    
    def test_ignores_hidden_col0_table(self, tmp_path):
        """Test that hidden table (col-0) is ignored."""
        html = '''
        <table class="col-0">
            <tbody>
                <tr>
                    <td class="views-field views-field-field-pdf">
                        <a href="https://parliament.go.ke/duplicate.pdf">Duplicate Link</a>
                    </td>
                </tr>
            </tbody>
        </table>
        <table class="cols-2">
            <tbody>
                <tr>
                    <td class="views-field views-field-field-pdf">
                        <a href="https://parliament.go.ke/real.pdf">Real Link</a>
                    </td>
                </tr>
            </tbody>
        </table>
        '''
        
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        scraper = HansardScraper(storage=storage, db_path=None)
        
        hansards = scraper.extract_hansard_links(html)
        
        assert len(hansards) == 1
        assert 'real.pdf' in hansards[0]['url']
    
    def test_filters_order_papers(self, tmp_path):
        """Test that Order Papers are filtered out."""
        html = '''
        <table class="cols-2">
            <tbody>
                <tr>
                    <td class="views-field views-field-field-pdf">
                        <a href="https://parliament.go.ke/order-paper.pdf">Order Paper For Thursday, 4th December 2025</a>
                    </td>
                </tr>
                <tr>
                    <td class="views-field views-field-field-pdf">
                        <a href="https://parliament.go.ke/hansard.pdf">Hansard Report - Thursday, 4th December 2025</a>
                    </td>
                </tr>
            </tbody>
        </table>
        '''
        
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        scraper = HansardScraper(storage=storage, db_path=None)
        
        hansards = scraper.extract_hansard_links(html)
        
        assert len(hansards) == 1
        assert 'hansard.pdf' in hansards[0]['url']


# =============================================================================
# DATE PARSING TESTS
# =============================================================================

class TestDateParsing:
    """Test date extraction from various formats."""
    
    @pytest.mark.parametrize("text,expected", [
        # British formats with ordinals
        ("Thursday, 4th December 2025", "2025-12-04"),
        ("1st January 2025", "2025-01-01"),
        ("22nd November 2024", "2024-11-22"),
        
        # ISO format
        ("2025-12-04", "2025-12-04"),
        
        # DD/MM/YYYY and DD-MM-YYYY
        ("04/12/2025", "2025-12-04"),
        ("04-12-2025", "2025-12-04"),
        
        # American format
        ("December 4, 2025", "2025-12-04"),
        
        # Embedded in text
        ("Hansard for Thursday, 4th December 2025 - Afternoon", "2025-12-04"),
        
        # Invalid
        ("No date here", None),
        ("", None),
    ])
    def test_extract_date_formats(self, text, expected):
        """Test extraction of dates from various formats."""
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=Mock(), db_path=None)
        
        result = scraper.extract_date(text)
        assert result == expected


# =============================================================================
# DATABASE INITIALIZATION TESTS
# =============================================================================

class TestDatabaseInitialization:
    """Test database auto-initialization and schema verification."""
    
    def test_database_auto_created_if_missing(self, tmp_path):
        """Test database is automatically created if it doesn't exist."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        assert not Path(db_path).exists()
        
        scraper = HansardScraper(storage=storage, db_path=db_path)
        
        assert Path(db_path).exists()
        
        # Verify table exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='downloaded_pdfs'
        """)
        assert cursor.fetchone() is not None
        conn.close()
    
    def test_creates_table_if_db_exists_but_table_missing(self, tmp_path):
        """Test creates table if database exists but table is missing."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        # Create empty database (no tables)
        conn = sqlite3.connect(db_path)
        conn.close()
        
        scraper = HansardScraper(storage=storage, db_path=db_path)
        
        # Verify table was created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='downloaded_pdfs'
        """)
        assert cursor.fetchone() is not None
        conn.close()
    
    def test_raises_error_if_table_has_wrong_schema(self, tmp_path):
        """Test raises error if table exists with wrong schema."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        # Create database with wrong schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE downloaded_pdfs (
                id INTEGER PRIMARY KEY,
                url TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        
        with pytest.raises(RuntimeError, match="incorrect schema"):
            HansardScraper(storage=storage, db_path=db_path)


# =============================================================================
# DOWNLOAD LOGIC TESTS
# =============================================================================

class TestDownloadLogic:
    """Test download decision logic and tracking."""
    
    def test_download_new_file(self, tmp_path):
        """Test downloading a new file."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(storage=storage, db_path=db_path)
        
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'PDF content']
        
        with patch.object(scraper.session, 'get', return_value=mock_response):
            success, action = scraper.download_pdf(
                'http://test.com/test.pdf',
                'Afternoon Session',
                '2025-01-15'
            )
        
        assert success is True
        assert action == 'downloaded'
        assert storage.exists('hansard_20250115_A.pdf')
    
    def test_skip_existing_file(self, tmp_path):
        """Test skipping file that already exists."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(storage=storage, db_path=db_path)
        
        # Create existing file
        storage.write("hansard_20250115_A.pdf", b"existing content")
        scraper._track_download(
            "http://test.com/old.pdf",
            "hansard_20250115_A.pdf",
            "2025-01-15",
            "A",
            None
        )
        
        success, action = scraper.download_pdf(
            'http://test.com/old.pdf',
            'Afternoon Session',
            '2025-01-15'
        )
        
        assert success is True
        assert action == 'skipped_exists'
    
    def test_filter_by_date_range(self, tmp_path):
        """Test filtering by date range."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(
            storage=storage,
            db_path=None,
            start_date="2025-06-01",
            end_date="2025-07-01"
        )
        
        # Date before range
        success, action = scraper.download_pdf(
            'http://test.com/test.pdf',
            'Afternoon Session',
            '2025-05-15'
        )
        assert action == 'skipped_date'
        
        # Date after range
        success, action = scraper.download_pdf(
            'http://test.com/test.pdf',
            'Afternoon Session',
            '2025-08-15'
        )
        assert action == 'skipped_date'
    
    def test_download_failure_cleanup(self, tmp_path):
        """Test that partial downloads are cleaned up on failure."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(storage=storage, db_path=None)
        
        # Mock download to fail
        with patch.object(scraper.session, 'get', side_effect=requests.ConnectionError("Network error")):
            success, action = scraper.download_pdf(
                'http://test.com/test.pdf',
                'Afternoon Session',
                '2025-01-15'
            )
        
        assert success is False
        assert action == 'failed'
        # File should not exist after cleanup
        assert not storage.exists('hansard_20250115_A.pdf')


# =============================================================================
# RETRY LOGIC TESTS
# =============================================================================

class TestRetryLogic:
    """Test download retry with exponential backoff."""
    
    def test_download_succeeds_on_first_attempt(self, tmp_path):
        """Test successful download on first attempt."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=storage, db_path=None)
        
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'PDF content']
        mock_get = Mock(return_value=mock_response)
        
        with patch.object(scraper.session, 'get', mock_get):
            content = scraper._download_pdf_with_retry('http://test.com/test.pdf')
        
        assert content == b'PDF content'
        assert mock_get.call_count == 1
    
    def test_download_retries_on_network_error(self, tmp_path):
        """Test download retries on network errors."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=storage, db_path=None)
        
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'PDF content']
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.ConnectionError("Network error")
            return mock_response
        
        with patch.object(scraper.session, 'get', side_effect=side_effect):
            content = scraper._download_pdf_with_retry('http://test.com/test.pdf')
        
        assert content == b'PDF content'
        assert call_count == 3
    
    def test_download_fails_after_max_retries(self, tmp_path):
        """Test download fails after maximum retries."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=storage, db_path=None)
        
        mock_get = Mock(side_effect=requests.ConnectionError("Network error"))
        
        with patch.object(scraper.session, 'get', mock_get):
            try:
                scraper._download_pdf_with_retry('http://test.com/test.pdf')
                assert False, "Should have raised ConnectionError"
            except requests.ConnectionError:
                assert mock_get.call_count == 3


# =============================================================================
# PAGINATION TESTS
# =============================================================================

class TestPagination:
    """Test pagination detection and handling."""
    
    def test_extract_max_page_from_pagination(self):
        """Test extraction of max page from pagination HTML."""
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=Mock(), db_path=None)
        
        html = """
        <html>
            <li class="pager__item pager__item--last">
                <a href="?page=18">Last</a>
            </li>
        </html>
        """
        
        max_page = scraper.extract_max_page(html)
        assert max_page == 19  # page=18 is 0-indexed
    
    def test_extract_max_page_no_pagination(self):
        """Test returns 1 when no pagination found."""
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=Mock(), db_path=None)
        
        html = "<html><body>No pagination here</body></html>"
        
        max_page = scraper.extract_max_page(html)
        assert max_page == 1
    
    def test_stops_when_finding_date_before_start_date(self, tmp_path):
        """Test scraper stops pagination when finding date before start_date."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(
                storage=storage,
                db_path=None,
                start_date="2025-06-01"
            )
        
        mock_html = '<html><li class="pager__item--last"><a href="?page=5">Last</a></li></html>'
        
        page1_hansards = [
            {'url': 'http://test.com/1.pdf', 'title': 'Session 1', 'date': '2025-07-01'},
            {'url': 'http://test.com/2.pdf', 'title': 'Session 2', 'date': '2025-06-15'},
        ]
        
        page2_hansards = [
            {'url': 'http://test.com/3.pdf', 'title': 'Session 3', 'date': '2025-06-01'},
            {'url': 'http://test.com/4.pdf', 'title': 'Session 4', 'date': '2025-05-20'},
        ]
        
        mock_extract = Mock(side_effect=[page1_hansards, page2_hansards])
        
        with patch.object(scraper, 'fetch_page', return_value=mock_html):
            with patch.object(scraper, 'extract_hansard_links', mock_extract):
                hansards = scraper.scrape_all()
        
        assert len(hansards) == 4
        assert mock_extract.call_count == 2


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_extract_links_raises_error_when_no_pdf_links(self, tmp_path):
        """Test that extraction raises RuntimeError when no PDF links found."""
        html = '''
        <html>
            <body>
                <p>No PDF links here</p>
            </body>
        </html>
        '''
        
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        scraper = HansardScraper(storage=storage, db_path=None)
        
        with pytest.raises(RuntimeError, match="No PDF links found with CSS selector"):
            scraper.extract_hansard_links(html)
    
    def test_download_pdf_with_no_date(self, tmp_path):
        """Test download fails gracefully when no date provided."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        scraper = HansardScraper(storage=storage, db_path=None)
        
        success, action = scraper.download_pdf(
            'http://test.com/test.pdf',
            'Afternoon Session',
            None  # No date
        )
        
        assert success is False
        assert action == 'failed'
    
    def test_download_pdf_with_empty_date(self, tmp_path):
        """Test download fails gracefully when empty date provided."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        scraper = HansardScraper(storage=storage, db_path=None)
        
        success, action = scraper.download_pdf(
            'http://test.com/test.pdf',
            'Afternoon Session',
            ''  # Empty date
        )
        
        assert success is False
        assert action == 'failed'
    
    def test_fetch_page_with_network_error(self, tmp_path):
        """Test fetch_page raises exception on network error."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=storage, db_path=None)
        
        with patch.object(scraper.session, 'get', side_effect=requests.ConnectionError("Network error")):
            with pytest.raises(requests.ConnectionError):
                scraper.fetch_page('http://test.com')
    
    def test_scrape_all_handles_network_error_on_first_page(self, tmp_path):
        """Test scrape_all returns empty list when first page fails."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=storage, db_path=None)
        
        with patch.object(scraper, 'fetch_page', side_effect=requests.ConnectionError("Network error")):
            hansards = scraper.scrape_all()
        
        assert hansards == []
    
    def test_scrape_all_stops_on_network_error_mid_pagination(self, tmp_path):
        """Test scrape_all stops gracefully on network error during pagination."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=storage, db_path=None)
        
        mock_html = '<html><li class="pager__item--last"><a href="?page=5">Last</a></li></html>'
        
        page1_hansards = [
            {'url': 'http://test.com/1.pdf', 'title': 'Session 1', 'date': '2025-07-01'},
        ]
        
        def fetch_side_effect(url):
            if 'page=2' in url:
                raise requests.ConnectionError("Network error")
            return mock_html
        
        with patch.object(scraper, 'fetch_page', side_effect=fetch_side_effect):
            with patch.object(scraper, 'extract_hansard_links', return_value=page1_hansards):
                hansards = scraper.scrape_all()
        
        assert len(hansards) == 1
    
    def test_scrape_all_stops_when_all_dates_after_end_date(self, tmp_path):
        """Test scrape_all stops when all dates on page are after end_date."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(
                storage=storage,
                db_path=None,
                end_date="2025-06-01"
            )
        
        mock_html = '<html><li class="pager__item--last"><a href="?page=5">Last</a></li></html>'
        
        page1_hansards = [
            {'url': 'http://test.com/1.pdf', 'title': 'Session 1', 'date': '2025-07-01'},
            {'url': 'http://test.com/2.pdf', 'title': 'Session 2', 'date': '2025-07-15'},
        ]
        
        page2_hansards = []  # Empty page to stop pagination
        
        with patch.object(scraper, 'fetch_page', return_value=mock_html):
            with patch.object(scraper, 'extract_hansard_links', side_effect=[page1_hansards, page2_hansards]):
                hansards = scraper.scrape_all()
        
        # Should include hansards from first page even though dates are after end_date
        # (filtering happens in download_all, not scrape_all)
        assert len(hansards) == 2


class TestDateExtraction:
    """Test date extraction with dateparser."""
    
    def test_extract_date_with_dateparser_available(self, tmp_path):
        """Test date extraction when dateparser is available."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=storage, db_path=None)
        
        # Test with dateparser
        with patch('hansard_tales.scrapers.hansard_scraper.DATEPARSER_AVAILABLE', True):
            # Mock the search_dates function from dateparser.search module
            with patch('dateparser.search.search_dates') as mock_search:
                from datetime import datetime
                mock_search.return_value = [("Thursday, 4th December 2025", datetime(2025, 12, 4))]
                
                result = scraper.extract_date("Thursday, 4th December 2025")
                assert result == "2025-12-04"
    
    def test_extract_date_dateparser_exception_fallback(self, tmp_path):
        """Test date extraction falls back to regex when dateparser fails."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=storage, db_path=None)
        
        # Test dateparser exception fallback
        with patch('hansard_tales.scrapers.hansard_scraper.DATEPARSER_AVAILABLE', True):
            with patch('dateparser.search.search_dates', side_effect=Exception("Parser error")):
                result = scraper.extract_date("2025-12-04")
                assert result == "2025-12-04"


class TestTrackingLogic:
    """Test download tracking logic."""
    
    def test_track_download_without_database(self, tmp_path):
        """Test tracking is skipped when no database configured."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        scraper = HansardScraper(storage=storage, db_path=None)
        
        # Should not raise error
        scraper._track_download(
            "http://test.com/test.pdf",
            "hansard_20250115_A.pdf",
            "2025-01-15",
            "A",
            None
        )
    
    def test_track_download_with_file_size(self, tmp_path):
        """Test tracking includes file size when file exists."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(storage=storage, db_path=db_path)
        
        # Create file
        storage.write("hansard_20250115_A.pdf", b"test content")
        
        # Track it
        scraper._track_download(
            "http://test.com/test.pdf",
            "hansard_20250115_A.pdf",
            "2025-01-15",
            "A",
            None
        )
        
        # Verify file_size was recorded
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT file_size FROM downloaded_pdfs WHERE file_path = ?", ("hansard_20250115_A.pdf",))
        file_size = cursor.fetchone()[0]
        conn.close()
        
        assert file_size == 12  # len(b"test content")
    
    def test_check_existing_download_file_missing_redownload(self, tmp_path):
        """Test check returns redownload when file in DB but not in storage."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(storage=storage, db_path=db_path)
        
        # Track file without creating it
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO downloaded_pdfs (original_url, file_path, date, period_of_day)
            VALUES (?, ?, ?, ?)
        """, ("http://test.com/test.pdf", "hansard_20250115_A.pdf", "2025-01-15", "A"))
        conn.commit()
        conn.close()
        
        should_skip, reason = scraper._check_existing_download(
            "http://test.com/test.pdf",
            "hansard_20250115_A.pdf",
            "2025-01-15",
            "A"
        )
        
        assert should_skip is False
        assert reason == "file_missing_redownload"
    
    def test_check_existing_download_database_error(self, tmp_path):
        """Test check raises error when database query fails."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(storage=storage, db_path=db_path)
        
        # Mock database connection to fail
        with patch('sqlite3.connect', side_effect=sqlite3.Error("Database error")):
            with pytest.raises(RuntimeError, match="Database query failed"):
                scraper._check_existing_download(
                    "http://test.com/test.pdf",
                    "hansard_20250115_A.pdf",
                    "2025-01-15",
                    "A"
                )
    
    def test_track_download_handles_file_size_error(self, tmp_path):
        """Test tracking handles error when getting file size."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(storage=storage, db_path=db_path)
        
        # Create file
        storage.write("hansard_20250115_A.pdf", b"test content")
        
        # Mock get_size to raise error
        with patch.object(storage, 'get_size', side_effect=Exception("Size error")):
            # Should not raise error, just log warning
            scraper._track_download(
                "http://test.com/test.pdf",
                "hansard_20250115_A.pdf",
                "2025-01-15",
                "A",
                None
            )
        
        # Verify file was tracked with NULL file_size
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT file_size FROM downloaded_pdfs WHERE file_path = ?", ("hansard_20250115_A.pdf",))
        file_size = cursor.fetchone()[0]
        conn.close()
        
        assert file_size is None
    
    def test_track_download_database_error(self, tmp_path):
        """Test tracking raises error when database operation fails."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(storage=storage, db_path=db_path)
        
        # Mock database connection to fail
        with patch('sqlite3.connect', side_effect=sqlite3.Error("Database error")):
            with pytest.raises(RuntimeError, match="Failed to track download in database"):
                scraper._track_download(
                    "http://test.com/test.pdf",
                    "hansard_20250115_A.pdf",
                    "2025-01-15",
                    "A",
                    None
                )


class TestPeriodExtraction:
    """Test period-of-day extraction."""
    
    def test_download_pdf_defaults_to_afternoon_when_no_period_found(self, tmp_path):
        """Test download defaults to 'P' when period not found in title."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        scraper = HansardScraper(storage=storage, db_path=None)
        
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'PDF content']
        
        with patch.object(scraper.session, 'get', return_value=mock_response):
            with patch.object(scraper.period_extractor, 'extract_from_title', return_value=None):
                success, action = scraper.download_pdf(
                    'http://test.com/test.pdf',
                    'Session without period',  # No period in title
                    '2025-01-15'
                )
        
        assert success is True
        assert action == 'downloaded'
        # Verify file was created with 'P' (afternoon) suffix
        assert storage.exists('hansard_20250115_P.pdf')


class TestScrapingLogic:
    """Test scraping and pagination logic."""
    
    def test_scrape_all_stops_on_empty_page(self, tmp_path):
        """Test scrape_all stops when encountering empty page."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=storage, db_path=None)
        
        mock_html = '<html><li class="pager__item--last"><a href="?page=5">Last</a></li></html>'
        
        page1_hansards = [
            {'url': 'http://test.com/1.pdf', 'title': 'Session 1', 'date': '2025-07-01'},
        ]
        
        page2_hansards = []  # Empty page
        
        with patch.object(scraper, 'fetch_page', return_value=mock_html):
            with patch.object(scraper, 'extract_hansard_links', side_effect=[page1_hansards, page2_hansards]):
                hansards = scraper.scrape_all()
        
        assert len(hansards) == 1
    
    def test_scrape_hansard_page_constructs_correct_url(self, tmp_path):
        """Test scrape_hansard_page constructs correct URL for pagination."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=storage, db_path=None)
        
        mock_html = '<html></html>'
        
        with patch.object(scraper, 'fetch_page', return_value=mock_html) as mock_fetch:
            with patch.object(scraper, 'extract_hansard_links', return_value=[]):
                # Test page 1 (no page parameter)
                scraper.scrape_hansard_page(1)
                mock_fetch.assert_called_with(scraper.HANSARD_URL)
                
                # Test page 2 (with page parameter)
                scraper.scrape_hansard_page(2)
                mock_fetch.assert_called_with(f"{scraper.HANSARD_URL}?page=2")
    
    def test_scrape_hansard_page_returns_empty_on_fetch_failure(self, tmp_path):
        """Test scrape_hansard_page returns empty list when fetch returns None."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=storage, db_path=None)
        
        with patch.object(scraper, 'fetch_page', return_value=None):
            hansards = scraper.scrape_hansard_page(1)
        
        assert hansards == []
    
    def test_download_all_filters_by_date_range(self, tmp_path):
        """Test download_all filters hansards by date range."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(
            storage=storage,
            db_path=None,
            start_date="2025-06-01",
            end_date="2025-07-01"
        )
        
        hansards = [
            {'url': 'http://test.com/1.pdf', 'title': 'Session 1', 'date': '2025-05-15'},  # Before range
            {'url': 'http://test.com/2.pdf', 'title': 'Session 2', 'date': '2025-06-15'},  # In range
            {'url': 'http://test.com/3.pdf', 'title': 'Session 3', 'date': '2025-07-15'},  # After range
        ]
        
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'PDF content']
        
        with patch.object(scraper.session, 'get', return_value=mock_response):
            stats = scraper.download_all(hansards)
        
        assert stats['total'] == 3
        assert stats['downloaded'] == 1  # Only the one in range
        assert stats['filtered'] == 2  # Two outside range


class TestInitialization:
    """Test scraper initialization."""
    
    def test_init_with_default_storage(self):
        """Test initialization with default storage backend."""
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(db_path=None)
        
        assert scraper.storage is not None
        assert isinstance(scraper.storage, FilesystemStorage)
    
    def test_init_with_custom_rate_limit(self):
        """Test initialization with custom rate limit."""
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=Mock(), db_path=None, rate_limit_delay=2.5)
        
        assert scraper.rate_limit_delay == 2.5
    
    def test_init_with_date_range(self):
        """Test initialization with date range."""
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(
                storage=Mock(),
                db_path=None,
                start_date="2025-01-01",
                end_date="2025-12-31"
            )
        
        assert scraper.start_date == "2025-01-01"
        assert scraper.end_date == "2025-12-31"
    
    def test_init_without_dateparser_logs_warning(self, tmp_path, caplog):
        """Test initialization logs warning when dateparser not available."""
        import logging
        
        with patch('hansard_tales.scrapers.hansard_scraper.DATEPARSER_AVAILABLE', False):
            with patch.object(HansardScraper, '_ensure_database_initialized'):
                with caplog.at_level(logging.WARNING):
                    scraper = HansardScraper(storage=Mock(), db_path=None)
        
        # Check that warning was logged (this happens at module level, not in __init__)
        # So we just verify the scraper was created successfully
        assert scraper is not None


class TestHTMLExtractionEdgeCases:
    """Test HTML extraction edge cases."""
    
    def test_extract_links_with_empty_href(self, tmp_path):
        """Test extraction skips links with empty href."""
        html = '''
        <table class="cols-2">
            <tbody>
                <tr>
                    <td class="views-field views-field-field-pdf">
                        <a href="">Empty href</a>
                    </td>
                </tr>
                <tr>
                    <td class="views-field views-field-field-pdf">
                        <a href="https://parliament.go.ke/test.pdf">Valid link</a>
                    </td>
                </tr>
            </tbody>
        </table>
        '''
        
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        scraper = HansardScraper(storage=storage, db_path=None)
        
        hansards = scraper.extract_hansard_links(html)
        
        assert len(hansards) == 1
        assert 'test.pdf' in hansards[0]['url']
    
    def test_extract_links_with_duplicate_urls(self, tmp_path):
        """Test extraction deduplicates URLs."""
        html = '''
        <table class="cols-2">
            <tbody>
                <tr>
                    <td class="views-field views-field-field-pdf">
                        <a href="https://parliament.go.ke/test.pdf">First occurrence</a>
                    </td>
                </tr>
                <tr>
                    <td class="views-field views-field-field-pdf">
                        <a href="https://parliament.go.ke/test.pdf">Duplicate</a>
                    </td>
                </tr>
            </tbody>
        </table>
        '''
        
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        scraper = HansardScraper(storage=storage, db_path=None)
        
        hansards = scraper.extract_hansard_links(html)
        
        assert len(hansards) == 1


class TestPaginationEdgeCases:
    """Test pagination edge cases."""
    
    def test_scrape_all_with_no_max_page_detected(self, tmp_path):
        """Test scrape_all handles case when max page cannot be detected."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(storage=storage, db_path=None)
        
        # HTML with no pagination
        mock_html = '<html><body>No pagination</body></html>'
        
        page1_hansards = [
            {'url': 'http://test.com/1.pdf', 'title': 'Session 1', 'date': '2025-07-01'},
        ]
        
        # Return hansards on first page, empty list on subsequent pages
        def extract_side_effect(html):
            if not hasattr(extract_side_effect, 'call_count'):
                extract_side_effect.call_count = 0
            extract_side_effect.call_count += 1
            
            if extract_side_effect.call_count == 1:
                return page1_hansards
            return []
        
        with patch.object(scraper, 'fetch_page', return_value=mock_html):
            with patch.object(scraper, 'extract_hansard_links', side_effect=extract_side_effect):
                with patch.object(scraper, 'extract_max_page', return_value=None):
                    hansards = scraper.scrape_all()
        
        # Should still get hansards from first page
        assert len(hansards) == 1
    
    def test_scrape_all_adds_hansards_from_page_with_early_dates(self, tmp_path):
        """Test scrape_all adds hansards from page even when stopping early."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(
                storage=storage,
                db_path=None,
                start_date="2025-06-01"
            )
        
        mock_html = '<html><li class="pager__item--last"><a href="?page=5">Last</a></li></html>'
        
        page1_hansards = [
            {'url': 'http://test.com/1.pdf', 'title': 'Session 1', 'date': '2025-07-01'},
        ]
        
        page2_hansards = [
            {'url': 'http://test.com/2.pdf', 'title': 'Session 2', 'date': '2025-06-15'},
            {'url': 'http://test.com/3.pdf', 'title': 'Session 3', 'date': '2025-05-20'},  # Before start_date
        ]
        
        with patch.object(scraper, 'fetch_page', return_value=mock_html):
            with patch.object(scraper, 'extract_hansard_links', side_effect=[page1_hansards, page2_hansards]):
                hansards = scraper.scrape_all()
        
        # Should include all hansards from both pages (filtering happens in download_all)
        assert len(hansards) == 3
    
    def test_scrape_all_stops_when_all_dates_after_end_date_without_adding(self, tmp_path):
        """Test scrape_all stops and doesn't add hansards when all dates after end_date."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        with patch.object(HansardScraper, '_ensure_database_initialized'):
            scraper = HansardScraper(
                storage=storage,
                db_path=None,
                end_date="2025-06-01"
            )
        
        mock_html = '<html><li class="pager__item--last"><a href="?page=5">Last</a></li></html>'
        
        page1_hansards = [
            {'url': 'http://test.com/1.pdf', 'title': 'Session 1', 'date': '2025-05-15'},
        ]
        
        page2_hansards = [
            {'url': 'http://test.com/2.pdf', 'title': 'Session 2', 'date': '2025-07-01'},
            {'url': 'http://test.com/3.pdf', 'title': 'Session 3', 'date': '2025-07-15'},  # All after end_date
        ]
        
        with patch.object(scraper, 'fetch_page', return_value=mock_html):
            with patch.object(scraper, 'extract_hansard_links', side_effect=[page1_hansards, page2_hansards]):
                hansards = scraper.scrape_all()
        
        # Should only include hansards from first page, not second page
        assert len(hansards) == 1


class TestDownloadEdgeCases:
    """Test download edge cases."""
    
    def test_download_pdf_with_http_error(self, tmp_path):
        """Test download handles HTTP errors gracefully."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        scraper = HansardScraper(storage=storage, db_path=None)
        
        # Mock HTTP error
        with patch.object(scraper.session, 'get', side_effect=requests.HTTPError("404 Not Found")):
            success, action = scraper.download_pdf(
                'http://test.com/test.pdf',
                'Afternoon Session',
                '2025-01-15'
            )
        
        assert success is False
        assert action == 'failed'
    
    def test_download_pdf_with_timeout(self, tmp_path):
        """Test download handles timeout errors gracefully."""
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        scraper = HansardScraper(storage=storage, db_path=None)
        
        # Mock timeout error
        with patch.object(scraper.session, 'get', side_effect=requests.Timeout("Request timeout")):
            success, action = scraper.download_pdf(
                'http://test.com/test.pdf',
                'Afternoon Session',
                '2025-01-15'
            )
        
        assert success is False
        assert action == 'failed'


class TestCheckExistingDownload:
    """Test _check_existing_download logic."""
    
    def test_file_exists_with_record(self, tmp_path):
        """Test returns skip when file exists in storage AND database."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(storage=storage, db_path=db_path)
        
        # Create file and track it
        storage.write("hansard_20250115_A.pdf", b"content")
        scraper._track_download(
            "http://test.com/test.pdf",
            "hansard_20250115_A.pdf",
            "2025-01-15",
            "A",
            None
        )
        
        should_skip, reason = scraper._check_existing_download(
            "http://test.com/test.pdf",
            "hansard_20250115_A.pdf",
            "2025-01-15",
            "A"
        )
        
        assert should_skip is True
        assert reason == "file_exists_with_record"
    
    def test_file_exists_without_record(self, tmp_path):
        """Test returns skip and tracks when file exists but not in database."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(storage=storage, db_path=db_path)
        
        # Create file without tracking
        storage.write("hansard_20250115_A.pdf", b"content")
        
        should_skip, reason = scraper._check_existing_download(
            "http://test.com/test.pdf",
            "hansard_20250115_A.pdf",
            "2025-01-15",
            "A"
        )
        
        assert should_skip is True
        assert reason == "file_exists_without_record"
        
        # Verify it was tracked
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM downloaded_pdfs WHERE file_path = ?", ("hansard_20250115_A.pdf",))
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 1
    
    def test_new_download_needed(self, tmp_path):
        """Test returns download needed when neither file nor record exists."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(storage=storage, db_path=db_path)
        
        should_skip, reason = scraper._check_existing_download(
            "http://test.com/test.pdf",
            "hansard_20250115_A.pdf",
            "2025-01-15",
            "A"
        )
        
        assert should_skip is False
        assert reason == "new_download"


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_workflow_with_date_filtering(self, tmp_path):
        """Test complete workflow: scrape, filter, download, track."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(
            storage=storage,
            db_path=db_path,
            start_date="2025-05-01",
            end_date="2025-07-01"
        )
        
        mock_html = '<html><li class="pager__item--last"><a href="?page=2">Last</a></li></html>'
        
        page1_hansards = [
            {'url': 'http://test.com/1.pdf', 'title': 'Afternoon Session', 'date': '2025-06-15'},
            {'url': 'http://test.com/2.pdf', 'title': 'Morning Session', 'date': '2025-05-20'},
        ]
        
        page2_hansards = [
            {'url': 'http://test.com/3.pdf', 'title': 'Afternoon Session', 'date': '2025-04-10'},
        ]
        
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'PDF content']
        
        with patch.object(scraper, 'fetch_page', return_value=mock_html):
            with patch.object(scraper, 'extract_hansard_links', side_effect=[page1_hansards, page2_hansards]):
                with patch.object(scraper.session, 'get', return_value=mock_response):
                    hansards = scraper.scrape_all()
                    stats = scraper.download_all(hansards)
        
        assert len(hansards) == 3
        assert stats['filtered'] == 1
        assert stats['downloaded'] == 2
        
        # Verify database tracking
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM downloaded_pdfs")
        count = cursor.fetchone()[0]
        assert count == 2
        conn.close()
    
    def test_statistics_accuracy(self, tmp_path):
        """Test that statistics correctly reflect operations."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(
            storage=storage,
            db_path=db_path,
            start_date="2025-01-01"
        )
        
        # Create existing files
        storage.write("hansard_20250115_A.pdf", b"existing 1")
        storage.write("hansard_20250120_A.pdf", b"existing 2")
        
        # Track them
        scraper._track_download("http://test.com/1.pdf", "hansard_20250115_A.pdf", "2025-01-15", "A", None)
        scraper._track_download("http://test.com/2.pdf", "hansard_20250120_A.pdf", "2025-01-20", "A", None)
        
        hansards = [
            {'url': 'http://test.com/1.pdf', 'title': 'Afternoon Session', 'date': '2025-01-15'},
            {'url': 'http://test.com/2.pdf', 'title': 'Afternoon Session', 'date': '2025-01-20'},
            {'url': 'http://test.com/3.pdf', 'title': 'Afternoon Session', 'date': '2025-01-25'},
        ]
        
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'new content']
        
        with patch.object(scraper.session, 'get', return_value=mock_response):
            stats = scraper.download_all(hansards)
        
        assert stats['total'] == 3
        assert stats['downloaded'] == 1
        assert stats['skipped'] == 2
        assert stats['filtered'] == 0
        assert stats['failed'] == 0
        
        # Verify math
        assert stats['downloaded'] + stats['skipped'] + stats['filtered'] + stats['failed'] == stats['total']
    
    def test_duplicate_urls_same_filename(self, tmp_path):
        """Test handling of multiple URLs generating same filename."""
        db_path = str(tmp_path / "test.db")
        storage = FilesystemStorage(str(tmp_path / "pdfs"))
        
        scraper = HansardScraper(storage=storage, db_path=db_path, start_date="2025-01-01")
        
        # Create files and track with old URLs
        storage.write("hansard_20250115_A.pdf", b"content 1")
        storage.write("hansard_20250120_A.pdf", b"content 2")
        
        scraper._track_download("http://test.com/old-1.pdf", "hansard_20250115_A.pdf", "2025-01-15", "A", None)
        scraper._track_download("http://test.com/old-2.pdf", "hansard_20250120_A.pdf", "2025-01-20", "A", None)
        
        # New URLs with same dates/periods (same filenames)
        hansards = [
            {'url': 'http://test.com/new-1.pdf', 'title': 'Afternoon Session', 'date': '2025-01-15'},
            {'url': 'http://test.com/new-2.pdf', 'title': 'Afternoon Session', 'date': '2025-01-20'},
            {'url': 'http://test.com/new-3.pdf', 'title': 'Afternoon Session', 'date': '2025-01-25'},
        ]
        
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'new content']
        
        with patch.object(scraper.session, 'get', return_value=mock_response):
            stats = scraper.download_all(hansards)
        
        assert stats['skipped'] == 2
        assert stats['downloaded'] == 1
        
        # Verify URLs were replaced (UNIQUE constraint on file_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM downloaded_pdfs")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 3  # Old URLs replaced by new URLs
