"""
Tests for extracting Hansard links from HTML.
"""

import tempfile

import pytest

from hansard_tales.scrapers.hansard_scraper import HansardScraper


@pytest.fixture
def scraper():
    """Create a scraper instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from hansard_tales.storage.filesystem import FilesystemStorage
        storage = FilesystemStorage(tmpdir)
        yield HansardScraper(storage=storage, rate_limit_delay=0.1)


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
        assert links[0]['filename'] == '20240315_0.pdf'  # Standardized format
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
