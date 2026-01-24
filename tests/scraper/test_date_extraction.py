"""
Tests for date extraction from text.
"""

import tempfile

import pytest

from hansard_tales.scrapers.hansard_scraper import HansardScraper, DATEPARSER_AVAILABLE


@pytest.fixture
def scraper():
    """Create a scraper instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from hansard_tales.storage.filesystem import FilesystemStorage
        storage = FilesystemStorage(tmpdir)
        yield HansardScraper(storage=storage, rate_limit_delay=0.1)


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
    
    def test_extract_date_british_format_with_ordinal(self, scraper):
        """Test extracting date in British format with ordinal suffix (15th October 2025)."""
        text = "Hansard Report - Wednesday, 15th October 2025 - Evening Sitting"
        date = scraper.extract_date(text)
        assert date == "2025-10-15"
    
    def test_extract_date_british_format_1st(self, scraper):
        """Test extracting date with 1st ordinal."""
        text = "Hansard Report - 1st December 2025"
        date = scraper.extract_date(text)
        assert date == "2025-12-01"
    
    def test_extract_date_british_format_2nd(self, scraper):
        """Test extracting date with 2nd ordinal."""
        text = "Hansard Report - 2nd November 2025"
        date = scraper.extract_date(text)
        assert date == "2025-11-02"
    
    def test_extract_date_british_format_3rd(self, scraper):
        """Test extracting date with 3rd ordinal."""
        text = "Hansard Report - 3rd September 2025"
        date = scraper.extract_date(text)
        assert date == "2025-09-03"
    
    def test_extract_date_british_format_no_ordinal(self, scraper):
        """Test extracting date in British format without ordinal suffix."""
        text = "Hansard Report - 15 October 2025"
        date = scraper.extract_date(text)
        assert date == "2025-10-15"
    
    @pytest.mark.skipif(not DATEPARSER_AVAILABLE, reason="dateparser not installed")
    def test_extract_date_with_dateparser(self, scraper):
        """Test that dateparser is used when available."""
        # This format should only work with dateparser
        text = "Hansard Report for the 4th of December, 2025"
        date = scraper.extract_date(text)
        assert date == "2025-12-04"
    
    def test_extract_date_from_url_encoded(self, scraper):
        """Test extracting date from URL-encoded text."""
        # URL-encoded: "15th October 2025"
        text = "Hansard%20Report%20-%20Wednesday%2C%2015th%20October%202025%20%28A%29.pdf"
        # Note: This won't work with URL encoding, but the scraper should handle decoded URLs
        date = scraper.extract_date(text)
        # Should be None because it's URL-encoded
        assert date is None
    
    def test_extract_date_from_decoded_url(self, scraper):
        """Test extracting date from decoded URL."""
        text = "Hansard Report - Wednesday, 15th October 2025 (A).pdf"
        date = scraper.extract_date(text)
        assert date == "2025-10-15"
    
    def test_extract_date_empty_string(self, scraper):
        """Test extracting date from empty string."""
        date = scraper.extract_date("")
        assert date is None
    
    def test_extract_date_none(self, scraper):
        """Test extracting date from None."""
        date = scraper.extract_date(None)
        assert date is None
