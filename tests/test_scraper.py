"""
Tests for Hansard PDF scraper.

This module tests the scraper functionality including
date extraction, URL parsing, and PDF metadata extraction.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Import the scraper module
from hansard_tales.scrapers.hansard_scraper import HansardScraper


@pytest.fixture
def scraper():
    """Create a scraper instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield HansardScraper(output_dir=tmpdir, rate_limit_delay=0.1)


class TestDateExtraction:
    """Test suite for date extraction from text."""
    
    def test_extract_date_dd_mm_yyyy_slash(self, scraper):
        """Test extracting date in DD/MM/YYYY format."""
        text = "Hansard 15/03/2024"
        date = scraper.extract_date(text)
        assert date == "2024-03-15"
    
    def test_extract_date_dd_mm_yyyy_dash(self, scraper):
        """Test extracting date in DD-MM-YYYY format."""
        text = "Hansard 15-03-2024"
        date = scraper.extract_date(text)
        assert date == "2024-03-15"
    
    def test_extract_date_yyyy_mm_dd(self, scraper):
        """Test extracting date in YYYY-MM-DD format."""
        text = "Hansard 2024-03-15"
        date = scraper.extract_date(text)
        assert date == "2024-03-15"
    
    def test_extract_date_month_name(self, scraper):
        """Test extracting date with month name."""
        text = "Hansard March 15, 2024"
        date = scraper.extract_date(text)
        assert date == "2024-03-15"
    
    def test_extract_date_month_name_no_comma(self, scraper):
        """Test extracting date with month name without comma."""
        text = "Hansard March 15 2024"
        date = scraper.extract_date(text)
        assert date == "2024-03-15"
    
    def test_extract_date_single_digit_day(self, scraper):
        """Test extracting date with single digit day."""
        text = "Hansard 5/3/2024"
        date = scraper.extract_date(text)
        assert date == "2024-03-05"
    
    def test_extract_date_no_date(self, scraper):
        """Test extracting date when no date present."""
        text = "Hansard Report"
        date = scraper.extract_date(text)
        assert date is None
    
    def test_extract_date_multiple_dates(self, scraper):
        """Test extracting first date when multiple dates present."""
        text = "Hansard 15/03/2024 and 16/03/2024"
        date = scraper.extract_date(text)
        assert date == "2024-03-15"


class TestHansardLinkExtraction:
    """Test suite for extracting Hansard links from HTML."""
    
    def test_extract_simple_pdf_link(self, scraper):
        """Test extracting a simple PDF link."""
        html = '''
        <html>
            <body>
                <a href="/hansard/2024-03-15.pdf">Hansard March 15, 2024</a>
            </body>
        </html>
        '''
        
        links = scraper.extract_hansard_links(html)
        
        assert len(links) == 1
        assert links[0]['filename'] == '2024-03-15.pdf'
        assert links[0]['title'] == 'Hansard March 15, 2024'
        assert links[0]['date'] == '2024-03-15'
    
    def test_extract_multiple_pdf_links(self, scraper):
        """Test extracting multiple PDF links."""
        html = '''
        <html>
            <body>
                <a href="/hansard/2024-03-15.pdf">Hansard March 15, 2024</a>
                <a href="/hansard/2024-03-16.pdf">Hansard March 16, 2024</a>
            </body>
        </html>
        '''
        
        links = scraper.extract_hansard_links(html)
        
        assert len(links) == 2
        assert links[0]['date'] == '2024-03-15'
        assert links[1]['date'] == '2024-03-16'
    
    def test_extract_absolute_url(self, scraper):
        """Test that relative URLs are converted to absolute."""
        html = '''
        <html>
            <body>
                <a href="/hansard/2024-03-15.pdf">Hansard</a>
            </body>
        </html>
        '''
        
        links = scraper.extract_hansard_links(html)
        
        assert len(links) == 1
        assert links[0]['url'].startswith('https://parliament.go.ke')
    
    def test_extract_no_pdf_links(self, scraper):
        """Test extracting when no PDF links present."""
        html = '''
        <html>
            <body>
                <a href="/page.html">Regular Link</a>
            </body>
        </html>
        '''
        
        links = scraper.extract_hansard_links(html)
        
        assert len(links) == 0
    
    def test_extract_case_insensitive_pdf(self, scraper):
        """Test that PDF extension matching is case-insensitive."""
        html = '''
        <html>
            <body>
                <a href="/hansard/doc.PDF">Document</a>
                <a href="/hansard/doc.Pdf">Document</a>
            </body>
        </html>
        '''
        
        links = scraper.extract_hansard_links(html)
        
        assert len(links) == 2


class TestPDFDownload:
    """Test suite for PDF download functionality."""
    
    @patch('hansard_tales.scrapers.hansard_scraper.requests.Session')
    def test_download_pdf_success(self, mock_session_class, scraper):
        """Test successful PDF download."""
        # Mock response
        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b'PDF content'])
        mock_response.raise_for_status = Mock()
        
        mock_session = Mock()
        mock_session.get = Mock(return_value=mock_response)
        scraper.session = mock_session
        
        # Download
        success = scraper.download_pdf(
            'https://example.com/test.pdf',
            'test.pdf'
        )
        
        assert success is True
        assert (scraper.output_dir / 'test.pdf').exists()
    
    def test_download_pdf_already_exists(self, scraper):
        """Test that existing PDFs are skipped."""
        # Create existing file
        test_file = scraper.output_dir / 'existing.pdf'
        test_file.write_bytes(b'existing content')
        
        # Try to download
        success = scraper.download_pdf(
            'https://example.com/existing.pdf',
            'existing.pdf'
        )
        
        assert success is True
        # Content should be unchanged
        assert test_file.read_bytes() == b'existing content'
    
    @patch('hansard_tales.scrapers.hansard_scraper.requests.Session')
    def test_download_pdf_failure(self, mock_session_class, scraper):
        """Test PDF download failure handling."""
        # Mock failed response
        import requests
        mock_session = Mock()
        mock_session.get = Mock(side_effect=requests.RequestException("Network error"))
        scraper.session = mock_session
        
        # Download
        success = scraper.download_pdf(
            'https://example.com/test.pdf',
            'test.pdf'
        )
        
        assert success is False
        assert not (scraper.output_dir / 'test.pdf').exists()


class TestScraperConfiguration:
    """Test suite for scraper configuration."""
    
    def test_scraper_initialization(self):
        """Test scraper initializes with correct defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scraper = HansardScraper(output_dir=tmpdir)
            
            assert scraper.output_dir == Path(tmpdir)
            assert scraper.rate_limit_delay == 1.0
            assert scraper.max_retries == 3
    
    def test_scraper_custom_config(self):
        """Test scraper with custom configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scraper = HansardScraper(
                output_dir=tmpdir,
                rate_limit_delay=2.0,
                max_retries=5
            )
            
            assert scraper.rate_limit_delay == 2.0
            assert scraper.max_retries == 5
    
    def test_output_directory_created(self):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / 'pdfs' / 'nested'
            scraper = HansardScraper(output_dir=str(output_dir))
            
            assert output_dir.exists()
            assert output_dir.is_dir()


class TestURLConstruction:
    """Test suite for URL construction."""
    
    def test_base_url(self, scraper):
        """Test base URL is correct."""
        assert scraper.BASE_URL == "https://parliament.go.ke"
    
    def test_hansard_url(self, scraper):
        """Test Hansard URL is correct."""
        expected = "https://parliament.go.ke/the-national-assembly/house-business/hansard"
        assert scraper.HANSARD_URL == expected


class TestRateLimiting:
    """Test suite for rate limiting."""
    
    @patch('hansard_tales.scrapers.hansard_scraper.time.sleep')
    @patch('hansard_tales.scrapers.hansard_scraper.requests.Session')
    def test_rate_limit_applied(self, mock_session_class, mock_sleep, scraper):
        """Test that rate limiting delay is applied."""
        # Mock response
        mock_response = Mock()
        mock_response.text = '<html></html>'
        mock_response.raise_for_status = Mock()
        
        mock_session = Mock()
        mock_session.get = Mock(return_value=mock_response)
        scraper.session = mock_session
        
        # Fetch page
        scraper.fetch_page('https://example.com')
        
        # Verify sleep was called with rate limit delay
        mock_sleep.assert_called_with(scraper.rate_limit_delay)


class TestRetryLogic:
    """Test suite for retry logic."""
    
    @patch('hansard_tales.scrapers.hansard_scraper.time.sleep')
    @patch('hansard_tales.scrapers.hansard_scraper.requests.Session')
    def test_retry_on_failure(self, mock_session_class, mock_sleep, scraper):
        """Test that failed requests are retried."""
        import requests
        # Mock session that fails twice then succeeds
        mock_response = Mock()
        mock_response.text = '<html></html>'
        mock_response.raise_for_status = Mock()
        
        mock_session = Mock()
        mock_session.get = Mock(
            side_effect=[
                requests.RequestException("Fail 1"),
                requests.RequestException("Fail 2"),
                mock_response
            ]
        )
        scraper.session = mock_session
        
        # Fetch page
        result = scraper.fetch_page('https://example.com')
        
        # Should succeed after retries
        assert result == '<html></html>'
        assert mock_session.get.call_count == 3
    
    @patch('hansard_tales.scrapers.hansard_scraper.time.sleep')
    @patch('hansard_tales.scrapers.hansard_scraper.requests.Session')
    def test_max_retries_exceeded(self, mock_session_class, mock_sleep, scraper):
        """Test that max retries limit is respected."""
        import requests
        # Mock session that always fails
        mock_session = Mock()
        mock_session.get = Mock(side_effect=requests.RequestException("Always fails"))
        scraper.session = mock_session
        
        # Fetch page
        result = scraper.fetch_page('https://example.com')
        
        # Should return None after max retries
        assert result is None
        assert mock_session.get.call_count == scraper.max_retries + 1



class TestCLI:
    """Test suite for CLI argument parsing and main() function."""
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper')
    @patch('sys.argv', ['hansard-scraper', '--max-pages', '3', '--output-dir', 'test_output'])
    def test_main_with_arguments(self, mock_scraper_class):
        """Test main() with custom arguments."""
        from hansard_tales.scrapers.hansard_scraper import main
        
        # Mock scraper instance
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = [
            {'title': 'Test Hansard', 'date': '2024-01-01', 'url': 'http://test.pdf'}
        ]
        mock_scraper.download_all.return_value = {
            'total': 1, 'downloaded': 1, 'skipped': 0, 'failed': 0
        }
        mock_scraper_class.return_value = mock_scraper
        
        # Run main
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Should exit with 0 (success)
        assert exc_info.value.code == 0
        
        # Verify scraper was initialized with correct args
        mock_scraper_class.assert_called_once_with(
            output_dir='test_output',
            rate_limit_delay=1.0
        )
        
        # Verify scrape_all was called
        mock_scraper.scrape_all.assert_called_once_with(max_pages=3)
        
        # Verify download_all was called
        mock_scraper.download_all.assert_called_once()
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper')
    @patch('sys.argv', ['hansard-scraper', '--dry-run'])
    def test_main_dry_run(self, mock_scraper_class):
        """Test main() with --dry-run flag."""
        from hansard_tales.scrapers.hansard_scraper import main
        
        # Mock scraper instance
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = [
            {'title': 'Test Hansard', 'date': '2024-01-01', 'url': 'http://test.pdf'}
        ]
        mock_scraper_class.return_value = mock_scraper
        
        # Run main
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Should exit with 0 (success)
        assert exc_info.value.code == 0
        
        # Verify download_all was NOT called (dry run)
        mock_scraper.download_all.assert_not_called()
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper')
    @patch('sys.argv', ['hansard-scraper'])
    def test_main_no_hansards_found(self, mock_scraper_class):
        """Test main() when no Hansards are found."""
        from hansard_tales.scrapers.hansard_scraper import main
        
        # Mock scraper instance that returns empty list
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = []
        mock_scraper_class.return_value = mock_scraper
        
        # Run main
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Should exit with 1 (failure)
        assert exc_info.value.code == 1
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper')
    @patch('sys.argv', ['hansard-scraper'])
    def test_main_download_failures(self, mock_scraper_class):
        """Test main() when downloads fail."""
        from hansard_tales.scrapers.hansard_scraper import main
        
        # Mock scraper instance
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = [
            {'title': 'Test Hansard', 'date': '2024-01-01', 'url': 'http://test.pdf'}
        ]
        mock_scraper.download_all.return_value = {
            'total': 1, 'downloaded': 0, 'skipped': 0, 'failed': 1
        }
        mock_scraper_class.return_value = mock_scraper
        
        # Run main
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Should exit with 1 (failure due to failed downloads)
        assert exc_info.value.code == 1
