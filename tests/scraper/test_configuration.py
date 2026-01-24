"""
Tests for scraper configuration.
"""

import tempfile
from pathlib import Path

import pytest

from hansard_tales.scrapers.hansard_scraper import HansardScraper


@pytest.fixture
def scraper():
    """Create a scraper instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from hansard_tales.storage.filesystem import FilesystemStorage
        storage = FilesystemStorage(tmpdir)
        yield HansardScraper(storage=storage, rate_limit_delay=0.1)


class TestScraperConfiguration:
    """Test suite for scraper configuration."""
    
    def test_scraper_initialization(self):
        """Test scraper initializes with correct defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage)
            
            assert scraper.storage == storage
            assert scraper.rate_limit_delay == 1.0
            assert scraper.max_retries == 3
    
    def test_scraper_custom_config(self):
        """Test scraper with custom configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(
                storage=storage,
                rate_limit_delay=2.0,
                max_retries=5
            )
            
            assert scraper.rate_limit_delay == 2.0
            assert scraper.max_retries == 5
    
    def test_storage_directory_created(self):
        """Test that storage directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            storage_dir = Path(tmpdir) / 'pdfs' / 'nested'
            storage = FilesystemStorage(str(storage_dir))
            scraper = HansardScraper(storage=storage)
            
            assert storage_dir.exists()
            assert storage_dir.is_dir()


class TestURLConstruction:
    """Test suite for URL construction."""
    
    def test_base_url(self, scraper):
        """Test base URL is correct."""
        assert scraper.BASE_URL == "https://parliament.go.ke"
    
    def test_hansard_url(self, scraper):
        """Test Hansard URL is correct."""
        expected = "https://parliament.go.ke/the-national-assembly/house-business/hansard"
        assert scraper.HANSARD_URL == expected
