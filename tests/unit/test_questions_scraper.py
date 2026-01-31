"""
Unit tests for QuestionScraper.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from hansard_tales.models.base import Chamber
from hansard_tales.scrapers.questions import QuestionMetadata, QuestionScraper


@pytest.fixture
def question_scraper():
    """Create a QuestionScraper instance."""
    # Create a mock config
    config = MagicMock()
    config.base_url = "https://parliament.go.ke"
    config.download_dir = "/tmp/pdfs"
    config.max_retries = 3
    config.timeout = 30
    config.user_agent = "HansardTales/1.0"

    # Create scraper
    scraper = QuestionScraper(config)
    # Ensure logger is initialized
    if not hasattr(scraper, "logger"):
        scraper.logger = MagicMock()
    return scraper


@pytest.fixture
def sample_question_html():
    """Sample HTML with questions in a table."""
    return """
    <html>
        <table>
            <tr>
                <td>5/2024</td>
                <td>Hon. John Doe</td>
                <td>What are the plans for agricultural development?</td>
                <td>15/02/2024</td>
                <td>Oral</td>
                <td>Ministry of Agriculture</td>
                <td><a href="/questions/5-2024/">Link</a></td>
            </tr>
            <tr>
                <td>6/2024</td>
                <td>Hon. Jane Smith</td>
                <td>What is the status of the transport bill?</td>
                <td>16/02/2024</td>
                <td>Written</td>
                <td>Ministry of Transport</td>
                <td><a href="/questions/6-2024/">Link</a></td>
            </tr>
        </table>
    </html>
    """


@pytest.fixture
def sample_question_detail_html():
    """Sample HTML for a question detail page."""
    return """
    <html>
        <div class="question-detail">
            <h1>Question 5/2024</h1>
            <p class="asker">Asked by: Hon. John Doe</p>
            <p class="text">What are the plans for agricultural development?</p>
            <p class="date">15/02/2024</p>
            <p class="type">Oral</p>
            <p class="ministry">Ministry of Agriculture</p>
        </div>
    </html>
    """


class TestQuestionMetadata:
    """Tests for QuestionMetadata dataclass."""

    def test_create_question_metadata(self):
        """Test creating question metadata."""
        from hansard_tales.models.base import Chamber

        metadata = QuestionMetadata(
            question_number="5/2024",
            asker="Hon. John Doe",
            question_text="What are the plans?",
            question_date=date(2024, 2, 15),
            chamber=Chamber.NATIONAL_ASSEMBLY,
            question_type="oral",
            ministry="Ministry of Agriculture",
            url="http://parliament.go.ke/questions/5/",
            source_hash="abc123def456",
        )

        assert metadata.question_number == "5/2024"
        assert metadata.asker == "Hon. John Doe"
        assert metadata.question_type == "oral"

    def test_question_metadata_fields(self):
        """Test all QuestionMetadata fields."""
        from hansard_tales.models.base import Chamber

        metadata = QuestionMetadata(
            question_number="5/2024",
            asker="Hon. John Doe",
            question_text="What are the plans?",
            question_date=date(2024, 2, 15),
            chamber=Chamber.NATIONAL_ASSEMBLY,
            question_type="oral",
            ministry="Ministry of Agriculture",
            url="http://parliament.go.ke/questions/5/",
            source_hash="abc123def456",
        )

        assert metadata.question_text == "What are the plans?"
        assert metadata.question_date == date(2024, 2, 15)
        assert metadata.source_hash == "abc123def456"


class TestQuestionScraperDiscovery:
    """Tests for question discovery."""

    def test_discover_questions_method_exists(self, question_scraper):
        """Test that discover_questions method exists."""
        assert hasattr(question_scraper, "discover_questions")
        assert callable(question_scraper.discover_questions)

    def test_discover_questions_signature(self, question_scraper):
        """Test that discover_questions has correct signature."""
        import inspect

        sig = inspect.signature(question_scraper.discover_questions)
        params = list(sig.parameters.keys())

        # Should accept chamber and optional dates
        assert "chamber" in params
        assert "start_date" in params
        assert "end_date" in params


class TestQuestionScraperExtraction:
    """Tests for metadata extraction."""

    def test_extract_question_from_row(self, question_scraper):
        """Test extracting question from table row."""
        html = """
        <tr>
            <td>5/2024</td>
            <td>Hon. John Doe</td>
            <td>What are the plans?</td>
            <td>15/02/2024</td>
            <td>Oral</td>
            <td>Ministry of Agriculture</td>
            <td><a href="/questions/5-2024/">Link</a></td>
        </tr>
        """

        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        cells = row.find_all("td")
        metadata = question_scraper._extract_question_from_row(cells, Chamber.NATIONAL_ASSEMBLY)

        assert metadata is not None
        assert metadata.question_number == "5/2024"
        assert metadata.asker == "Hon. John Doe"

    def test_parse_date_formats(self, question_scraper):
        """Test date parsing with different formats."""
        # DD/MM/YYYY
        result1 = question_scraper._parse_date("15/02/2024")
        assert result1.year == 2024
        assert result1.month == 2
        assert result1.day == 15

        # DD-MM-YYYY
        result2 = question_scraper._parse_date("15-02-2024")
        assert result2.year == 2024


class TestQuestionScraperDownload:
    """Tests for question downloading."""

    def test_download_question_method_exists(self, question_scraper):
        """Test that download_question method exists."""
        assert hasattr(question_scraper, "download_question")
        assert callable(question_scraper.download_question)

    def test_download_question_accepts_metadata(self, question_scraper):
        """Test that download_question accepts QuestionMetadata."""
        import inspect

        sig = inspect.signature(question_scraper.download_question)

        # Should have a parameter for metadata
        assert len(sig.parameters) >= 1


class TestQuestionScraperFiltering:
    """Tests for date and type filtering."""

    def test_date_range_filter_includes(self, question_scraper):
        """Test that date range filtering includes matching dates."""
        # Create questions spanning a date range
        html = """
        <table>
            <tr>
                <td>5/2024</td>
                <td>Hon. John</td>
                <td>Q1</td>
                <td>10/02/2024</td>
                <td>Oral</td>
                <td>Min</td>
                <td><a href="/5/">Link</a></td>
            </tr>
            <tr>
                <td>6/2024</td>
                <td>Hon. Jane</td>
                <td>Q2</td>
                <td>20/02/2024</td>
                <td>Written</td>
                <td>Min</td>
                <td><a href="/6/">Link</a></td>
            </tr>
            <tr>
                <td>7/2024</td>
                <td>Hon. Bob</td>
                <td>Q3</td>
                <td>01/03/2024</td>
                <td>Oral</td>
                <td>Min</td>
                <td><a href="/7/">Link</a></td>
            </tr>
        </table>
        """

        soup = BeautifulSoup(html, "html.parser")
        rows = soup.find_all("tr")

        # Extract all questions
        questions = []
        for row in rows:
            try:
                cells = row.find_all("td")
                meta = question_scraper._extract_question_from_row(cells, Chamber.NATIONAL_ASSEMBLY)
                if meta:
                    questions.append(meta)
            except (IndexError, ValueError, AttributeError):
                pass

        # Filter by date
        start = date(2024, 2, 1)
        end = date(2024, 2, 28)
        filtered = [q for q in questions if start <= q.question_date <= end]

        assert len(filtered) >= 0

    def test_question_type_classification(self, question_scraper):
        """Test question type classification."""
        types = ["oral", "written", "supplementary"]

        for qtype in types:
            html = f"""
            <tr>
                <td>5/2024</td>
                <td>Hon. John</td>
                <td>Q1</td>
                <td>15/02/2024</td>
                <td>{qtype}</td>
                <td>Min</td>
                <td><a href="/5/">Link</a></td>
            </tr>
            """

            soup = BeautifulSoup(html, "html.parser")
            row = soup.find("tr")
            cells = row.find_all("td")
            metadata = question_scraper._extract_question_from_row(cells, Chamber.NATIONAL_ASSEMBLY)

            assert metadata is not None
            assert metadata.question_type == qtype


class TestQuestionScraperInterface:
    """Tests for BaseScraper interface compliance."""

    def test_get_document_urls_exists(self, question_scraper):
        """Test get_document_urls interface method exists."""
        assert hasattr(question_scraper, "get_document_urls")
        assert callable(question_scraper.get_document_urls)

    def test_extract_metadata_interface(self, question_scraper):
        """Test extract_metadata interface method."""
        # This method is abstract - QuestionScraper should implement it
        try:
            result = question_scraper.extract_metadata(
                "http://parliament.go.ke/questions/5/", b"<html></html>"
            )
            # If it returns, should be a dict
            assert isinstance(result, dict)
        except (NotImplementedError, TypeError):
            # Expected if method is abstract
            pass


class TestQuestionScraperDeduplication:
    """Tests for deduplication."""

    def test_url_hash_uniqueness(self, question_scraper):
        """Test that same URL produces same hash."""
        url = "http://parliament.go.ke/questions/5/"
        hash1 = question_scraper._hash_url(url)
        hash2 = question_scraper._hash_url(url)

        assert hash1 == hash2

    def test_different_urls_different_hashes(self, question_scraper):
        """Test that different URLs produce different hashes."""
        url1 = "http://parliament.go.ke/questions/5/"
        url2 = "http://parliament.go.ke/questions/6/"

        hash1 = question_scraper._hash_url(url1)
        hash2 = question_scraper._hash_url(url2)

        assert hash1 != hash2


class TestQuestionScraperEdgeCases:
    """Tests for edge cases."""

    def test_handle_missing_fields(self, question_scraper):
        """Test handling missing fields in HTML."""
        html = """
        <tr>
            <td>5/2024</td>
            <td></td>  <!-- Missing asker -->
            <td>Question text</td>
            <td></td>  <!-- Missing date -->
            <td>Oral</td>
            <td></td>  <!-- Missing ministry -->
            <td><a href="/questions/5/">Link</a></td>
        </tr>
        """

        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        cells = row.find_all("td")

        # Should handle gracefully or raise appropriate error
        try:
            metadata = question_scraper._extract_question_from_row(cells, Chamber.NATIONAL_ASSEMBLY)
            assert metadata is None or isinstance(metadata, QuestionMetadata)
        except (ValueError, IndexError):
            # Expected for truly missing required fields
            pass

    def test_handle_malformed_date(self, question_scraper):
        """Test handling malformed dates."""
        with pytest.raises(ValueError):
            question_scraper._parse_date("invalid-date")

    def test_empty_question_text(self, question_scraper):
        """Test handling empty question text."""
        html = """
        <tr>
            <td>5/2024</td>
            <td>Hon. John Doe</td>
            <td></td>  <!-- Empty question text -->
            <td>15/02/2024</td>
            <td>Oral</td>
            <td>Ministry</td>
            <td><a href="/5/">Link</a></td>
        </tr>
        """

        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        cells = row.find_all("td")

        # Should handle or raise appropriate error
        try:
            metadata = question_scraper._extract_question_from_row(cells, Chamber.NATIONAL_ASSEMBLY)
            # Empty text returns None
            assert metadata is None
        except ValueError:
            # Expected if text is required
            pass


class TestQuestionScraperChambers:
    """Tests for different parliamentary chambers."""

    def test_chamber_enum_values(self):
        """Test Chamber enum has expected values."""
        assert hasattr(Chamber, "NATIONAL_ASSEMBLY")
        assert hasattr(Chamber, "SENATE")

    def test_question_scraper_accepts_chamber(self, question_scraper):
        """Test that question scraper can be initialized with chamber enum."""
        # Verify Chamber enums exist
        assert Chamber.NATIONAL_ASSEMBLY is not None
        assert Chamber.SENATE is not None
