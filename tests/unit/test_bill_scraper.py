"""
Unit tests for BillScraper.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from hansard_tales.config.settings import ScraperConfig
from hansard_tales.models.base import Chamber
from hansard_tales.scrapers.bills import BillMetadata, BillScraper


@pytest.fixture
def scraper_config():
    """Create a test scraper configuration."""
    return ScraperConfig(
        base_url="https://parliament.go.ke",
        timeout=30,
        user_agent="Test Agent",
        max_retries=3,
    )


@pytest.fixture
def bill_scraper(scraper_config):
    """Create a bill scraper instance."""
    return BillScraper(scraper_config)


class TestBillScraperDiscoverBills:
    """Tests for discover_bills method."""

    def test_discover_bills_national_assembly(self, bill_scraper):
        """Test discovering bills for National Assembly."""
        # Mock HTML response
        html_content = """
        <html>
            <table class="views-table">
                <tr>
                    <td><strong>Bill No. 5 of 2023</strong></td>
                    <td>The Agriculture Bill</td>
                    <td>Hon. Smith</td>
                    <td>15/01/2023</td>
                    <td>First Reading</td>
                    <td><a href="/sites/default/files/bill_5_2023.pdf">Download</a></td>
                </tr>
            </table>
        </html>
        """

        with patch.object(bill_scraper, "_fetch_page_with_retry") as mock_fetch:
            mock_response = MagicMock()
            mock_response.content = html_content.encode()
            mock_fetch.return_value = mock_response

            bills = bill_scraper.discover_bills(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

            assert len(bills) == 1
            assert bills[0].bill_number == "Bill No. 5 of 2023"
            assert bills[0].title == "The Agriculture Bill"
            assert bills[0].sponsor == "Hon. Smith"
            assert bills[0].chamber == Chamber.NATIONAL_ASSEMBLY

    def test_discover_bills_senate(self, bill_scraper):
        """Test discovering bills for Senate."""
        html_content = """
        <html>
            <table class="views-table">
                <tr>
                    <td>Bill No. 2 of 2023</td>
                    <td>The County Government Bill</td>
                    <td>Hon. Jones</td>
                    <td>20/02/2023</td>
                    <td>Committee</td>
                    <td><a href="/sites/default/files/bill_2_2023.pdf">Download</a></td>
                </tr>
            </table>
        </html>
        """

        with patch.object(bill_scraper, "_fetch_page_with_retry") as mock_fetch:
            mock_response = MagicMock()
            mock_response.content = html_content.encode()
            mock_fetch.return_value = mock_response

            bills = bill_scraper.discover_bills(Chamber.SENATE, parliament_term=2022)

            assert len(bills) == 1
            assert bills[0].chamber == Chamber.SENATE

    def test_discover_bills_multiple(self, bill_scraper):
        """Test discovering multiple bills."""
        html_content = """
        <html>
            <table class="views-table">
                <tr>
                    <td>Bill 1</td>
                    <td>Title 1</td>
                    <td>Sponsor 1</td>
                    <td>01/01/2023</td>
                    <td>Reading 1</td>
                    <td><a href="/file1.pdf">Download</a></td>
                </tr>
                <tr>
                    <td>Bill 2</td>
                    <td>Title 2</td>
                    <td>Sponsor 2</td>
                    <td>02/02/2023</td>
                    <td>Reading 2</td>
                    <td><a href="/file2.pdf">Download</a></td>
                </tr>
            </table>
        </html>
        """

        with patch.object(bill_scraper, "_fetch_page_with_retry") as mock_fetch:
            mock_response = MagicMock()
            mock_response.content = html_content.encode()
            mock_fetch.return_value = mock_response

            bills = bill_scraper.discover_bills(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

            assert len(bills) == 2

    def test_discover_bills_no_results(self, bill_scraper):
        """Test discovering bills when none found."""
        html_content = "<html><body>No bills</body></html>"

        with patch.object(bill_scraper, "_fetch_page_with_retry") as mock_fetch:
            mock_response = MagicMock()
            mock_response.content = html_content.encode()
            mock_fetch.return_value = mock_response

            from hansard_tales.scrapers.base import DataCollectionError

            with pytest.raises(DataCollectionError):
                bill_scraper.discover_bills(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

    def test_discover_bills_invalid_chamber(self, bill_scraper):
        """Test discovering bills with invalid chamber."""

        # Create invalid chamber-like object
        invalid_chamber = MagicMock()
        invalid_chamber.value = "INVALID"

        with pytest.raises((ValueError, AttributeError)):
            bill_scraper.discover_bills(invalid_chamber, parliament_term=2022)


class TestBillScraperExtraction:
    """Tests for bill extraction methods."""

    def test_parse_date_multiple_formats(self, bill_scraper):
        """Test date parsing with various formats."""
        dates_to_test = [
            ("15/01/2023", date(2023, 1, 15)),
            ("15-01-2023", date(2023, 1, 15)),
            ("2023-01-15", date(2023, 1, 15)),
            ("15 January 2023", date(2023, 1, 15)),
            ("15 Jan 2023", date(2023, 1, 15)),
        ]

        for date_str, expected in dates_to_test:
            result = bill_scraper._parse_date(date_str)
            assert result == expected, f"Failed for format: {date_str}"

    def test_parse_date_invalid(self, bill_scraper):
        """Test date parsing with invalid date."""
        with pytest.raises(ValueError):
            bill_scraper._parse_date("not-a-date")

    def test_hash_url(self, bill_scraper):
        """Test URL hashing."""
        url = "https://parliament.go.ke/files/bill.pdf"
        hash_result = bill_scraper._hash_url(url)

        # Should be SHA256 hex (64 characters)
        assert len(hash_result) == 64
        assert isinstance(hash_result, str)

        # Same URL should produce same hash
        hash_result2 = bill_scraper._hash_url(url)
        assert hash_result == hash_result2

    def test_extract_bill_from_row(self, bill_scraper):
        """Test extracting bill from table row."""
        html = """
        <tr>
            <td>Bill No. 5 of 2023</td>
            <td>The Agriculture Bill</td>
            <td>Hon. Smith</td>
            <td>15/01/2023</td>
            <td>First Reading</td>
            <td><a href="/files/bill.pdf">Download</a></td>
        </tr>
        """
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        cells = row.find_all("td")

        with patch.object(bill_scraper, "_hash_url", return_value="abc123"):
            bill = bill_scraper._extract_bill_from_row(cells, Chamber.NATIONAL_ASSEMBLY)

            assert bill is not None
            assert bill.bill_number == "Bill No. 5 of 2023"
            assert bill.title == "The Agriculture Bill"
            assert bill.sponsor == "Hon. Smith"

    def test_extract_bill_missing_fields(self, bill_scraper):
        """Test extracting bill with missing fields."""
        html = "<tr><td>Too few cells</td><td>Data</td></tr>"
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        cells = row.find_all("td")

        bill = bill_scraper._extract_bill_from_row(cells, Chamber.NATIONAL_ASSEMBLY)
        assert bill is None


class TestBillScraperDownload:
    """Tests for bill download methods."""

    def test_download_bill_success(self, bill_scraper):
        """Test successful bill download."""
        bill_metadata = BillMetadata(
            bill_number="5/2023",
            title="Test Bill",
            chamber=Chamber.NATIONAL_ASSEMBLY,
            sponsor="Test Sponsor",
            introduction_date=date(2023, 1, 15),
            status="Reading 1",
            url="https://parliament.go.ke/files/bill.pdf",
            source_hash="abc123",
        )

        pdf_content = b"%PDF-1.4\n..."

        with patch.object(bill_scraper, "_fetch_page_with_retry") as mock_fetch:
            mock_response = MagicMock()
            mock_response.content = pdf_content
            mock_response.raise_for_status = MagicMock()
            mock_fetch.return_value = mock_response

            result = bill_scraper.download_bill(bill_metadata)

            assert result == pdf_content

    def test_download_bill_failure(self, bill_scraper):
        """Test failed bill download."""
        bill_metadata = BillMetadata(
            bill_number="5/2023",
            title="Test Bill",
            chamber=Chamber.NATIONAL_ASSEMBLY,
            sponsor="Test Sponsor",
            introduction_date=date(2023, 1, 15),
            status="Reading 1",
            url="https://parliament.go.ke/files/bill.pdf",
            source_hash="abc123",
        )

        from hansard_tales.scrapers.base import DataCollectionError

        with patch.object(bill_scraper, "_fetch_page_with_retry") as mock_fetch:
            mock_fetch.side_effect = Exception("Network error")

            with pytest.raises(DataCollectionError):
                bill_scraper.download_bill(bill_metadata)


class TestBillScraperInterface:
    """Tests for BaseScraper interface compatibility."""

    def test_get_document_urls(self, bill_scraper):
        """Test get_document_urls compatibility method."""
        html_content = """
        <html>
            <table class="views-table">
                <tr>
                    <td>Bill 1</td>
                    <td>Title 1</td>
                    <td>Sponsor</td>
                    <td>01/01/2023</td>
                    <td>Status</td>
                    <td><a href="/file1.pdf">Download</a></td>
                </tr>
            </table>
        </html>
        """

        with patch.object(bill_scraper, "_fetch_page_with_retry") as mock_fetch:
            mock_response = MagicMock()
            mock_response.content = html_content.encode()
            mock_fetch.return_value = mock_response

            urls = bill_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

            assert len(urls) == 1
            assert isinstance(urls[0], str)
            assert urls[0].startswith("http")
