"""
Tests for date range filtering functionality.
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


class TestDateRangeFiltering:
    """Test suite for date range filtering functionality."""
    
    def test_is_date_in_range_no_range_specified(self, scraper):
        """Test _is_date_in_range() with no range specified."""
        # No start or end date - should include all
        assert scraper._is_date_in_range('2024-01-01') is True
        assert scraper._is_date_in_range('2025-12-31') is True
        assert scraper._is_date_in_range(None) is True
    
    def test_is_date_in_range_start_date_only(self):
        """Test _is_date_in_range() with start date only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(
                storage=storage,
                start_date='2024-06-01'
            )
            
            # Before start date - should exclude
            assert scraper._is_date_in_range('2024-05-31') is False
            
            # On start date - should include
            assert scraper._is_date_in_range('2024-06-01') is True
            
            # After start date - should include
            assert scraper._is_date_in_range('2024-06-02') is True
            assert scraper._is_date_in_range('2025-01-01') is True
    
    def test_is_date_in_range_end_date_only(self):
        """Test _is_date_in_range() with end date only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(
                storage=storage,
                end_date='2024-06-30'
            )
            
            # Before end date - should include
            assert scraper._is_date_in_range('2024-01-01') is True
            assert scraper._is_date_in_range('2024-06-29') is True
            
            # On end date - should include
            assert scraper._is_date_in_range('2024-06-30') is True
            
            # After end date - should exclude
            assert scraper._is_date_in_range('2024-07-01') is False
    
    def test_is_date_in_range_both_dates(self):
        """Test _is_date_in_range() with both start and end dates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(
                storage=storage,
                start_date='2024-06-01',
                end_date='2024-06-30'
            )
            
            # Before range - should exclude
            assert scraper._is_date_in_range('2024-05-31') is False
            
            # Within range - should include
            assert scraper._is_date_in_range('2024-06-01') is True
            assert scraper._is_date_in_range('2024-06-15') is True
            assert scraper._is_date_in_range('2024-06-30') is True
            
            # After range - should exclude
            assert scraper._is_date_in_range('2024-07-01') is False
    
    def test_is_date_in_range_invalid_date(self, scraper):
        """Test _is_date_in_range() with invalid date."""
        # Invalid date format - should include with warning
        assert scraper._is_date_in_range('invalid-date') is True
        
        # None date - should include
        assert scraper._is_date_in_range(None) is True
