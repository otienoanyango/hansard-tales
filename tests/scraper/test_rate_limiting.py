"""
Tests for rate limiting and retry logic.
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
