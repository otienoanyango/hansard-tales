"""
Tests for pagination logic in scrape_all().
"""

import tempfile
from unittest.mock import Mock, patch

import pytest

from hansard_tales.scrapers.hansard_scraper import HansardScraper


@pytest.fixture
def scraper():
    """Create a scraper instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from hansard_tales.storage.filesystem import FilesystemStorage
        storage = FilesystemStorage(tmpdir)
        yield HansardScraper(storage=storage, rate_limit_delay=0.1)


class TestPagination:
    """Test suite for pagination logic in scrape_all()."""
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper.scrape_hansard_page')
    def test_scrape_all_multiple_pages(self, mock_scrape_page, scraper):
        """Test scrape_all() with multiple pages."""
        # Mock pages with different content
        mock_scrape_page.side_effect = [
            [{'title': 'Page 1 PDF 1', 'date': '2024-01-01', 'url': 'url1', 'filename': 'file1.pdf'}],
            [{'title': 'Page 2 PDF 1', 'date': '2024-01-02', 'url': 'url2', 'filename': 'file2.pdf'}],
            [{'title': 'Page 3 PDF 1', 'date': '2024-01-03', 'url': 'url3', 'filename': 'file3.pdf'}]
        ]
        
        # Scrape 3 pages
        results = scraper.scrape_all(max_pages=3)
        
        # Should have results from all 3 pages
        assert len(results) == 3
        assert mock_scrape_page.call_count == 3
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper.scrape_hansard_page')
    def test_scrape_all_stop_on_empty_page(self, mock_scrape_page, scraper):
        """Test scrape_all() stops on empty page."""
        # Mock pages - second page is empty
        mock_scrape_page.side_effect = [
            [{'title': 'Page 1 PDF 1', 'date': '2024-01-01', 'url': 'url1', 'filename': 'file1.pdf'}],
            [],  # Empty page
            [{'title': 'Page 3 PDF 1', 'date': '2024-01-03', 'url': 'url3', 'filename': 'file3.pdf'}]
        ]
        
        # Scrape up to 5 pages
        results = scraper.scrape_all(max_pages=5)
        
        # Should stop after page 2 (empty)
        assert len(results) == 1
        assert mock_scrape_page.call_count == 2
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper.scrape_hansard_page')
    def test_scrape_all_stop_when_outside_date_range(self, mock_scrape_page):
        """Test scrape_all() stops when all PDFs are outside date range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create scraper with date range
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(
                storage=storage,
                start_date='2024-06-01',
                end_date='2024-06-30'
            )
            
            # Mock pages - second page has all PDFs outside range
            # Note: extract_hansard_links filters PDFs, so page 2 will return empty list
            mock_scrape_page.side_effect = [
                [{'title': 'Page 1 PDF 1', 'date': '2024-06-15', 'url': 'url1', 'filename': 'file1.pdf'}],
                [],  # Page 2 returns empty because all PDFs were filtered out
                [{'title': 'Page 3 PDF 1', 'date': '2024-03-01', 'url': 'url4', 'filename': 'file4.pdf'}]
            ]
            
            # Scrape up to 5 pages
            results = scraper.scrape_all(max_pages=5)
            
            # Should stop after page 2 (empty)
            assert len(results) == 1  # Only the one from page 1
            assert mock_scrape_page.call_count == 2
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper.scrape_hansard_page')
    def test_scrape_all_max_pages_limit(self, mock_scrape_page, scraper):
        """Test scrape_all() respects max_pages limit."""
        # Mock pages that always return content
        mock_scrape_page.return_value = [
            {'title': 'PDF', 'date': '2024-01-01', 'url': 'url', 'filename': 'file.pdf'}
        ]
        
        # Scrape with max_pages=2
        results = scraper.scrape_all(max_pages=2)
        
        # Should stop after 2 pages
        assert mock_scrape_page.call_count == 2
        assert len(results) == 2
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper.fetch_page')
    def test_scrape_hansard_page_first_page(self, mock_fetch, scraper):
        """Test scrape_hansard_page() for first page."""
        # Mock HTML response
        mock_fetch.return_value = '''
        <html>
            <body>
                <a href="/test.pdf">Test PDF 2024-01-01</a>
            </body>
        </html>
        '''
        
        # Scrape first page
        results = scraper.scrape_hansard_page(1)
        
        # Should call fetch_page with base URL
        mock_fetch.assert_called_once()
        assert scraper.HANSARD_URL in mock_fetch.call_args[0][0]
        assert len(results) == 1
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper.fetch_page')
    def test_scrape_hansard_page_subsequent_page(self, mock_fetch, scraper):
        """Test scrape_hansard_page() for subsequent pages."""
        # Mock HTML response
        mock_fetch.return_value = '''
        <html>
            <body>
                <a href="/test.pdf">Test PDF 2024-01-01</a>
            </body>
        </html>
        '''
        
        # Scrape page 2
        results = scraper.scrape_hansard_page(2)
        
        # Should call fetch_page with page parameter
        mock_fetch.assert_called_once()
        assert '?page=2' in mock_fetch.call_args[0][0]
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper.fetch_page')
    def test_scrape_hansard_page_fetch_failure(self, mock_fetch, scraper):
        """Test scrape_hansard_page() when fetch fails."""
        # Mock fetch failure
        mock_fetch.return_value = None
        
        # Scrape page
        results = scraper.scrape_hansard_page(1)
        
        # Should return empty list
        assert results == []


class TestDownloadAll:
    """Test suite for download_all() functionality."""
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper.download_pdf')
    def test_download_all_success(self, mock_download, scraper):
        """Test download_all() with successful downloads."""
        # Mock successful downloads
        mock_download.return_value = True
        
        # Create test file to simulate successful download using storage
        # The download_all method checks for files matching the date pattern
        scraper.storage.write('hansard_20240101_P.pdf', b'content')
        
        hansards = [
            {'url': 'url1', 'filename': 'test.pdf', 'title': 'Test 1', 'date': '2024-01-01'}
        ]
        
        stats = scraper.download_all(hansards)
        
        assert stats['total'] == 1
        assert stats['downloaded'] == 1
        assert stats['failed'] == 0
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper.download_pdf')
    def test_download_all_failures(self, mock_download, scraper):
        """Test download_all() with failed downloads."""
        # Mock failed downloads
        mock_download.return_value = False
        
        hansards = [
            {'url': 'url1', 'filename': 'test1.pdf', 'title': 'Test 1', 'date': '2024-01-01'},
            {'url': 'url2', 'filename': 'test2.pdf', 'title': 'Test 2', 'date': '2024-01-02'}
        ]
        
        stats = scraper.download_all(hansards)
        
        assert stats['total'] == 2
        assert stats['failed'] == 2
        assert stats['downloaded'] == 0
