"""
Unit tests for BillSummarizer.
"""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from hansard_tales.analysis.bill_summarizer import BillSummarizer, BillSummary


@pytest.fixture
def mock_llm_analyzer():
    """Create a mock LLM analyzer."""
    return MagicMock()


@pytest.fixture
def mock_citation_verifier():
    """Create a mock citation verifier."""
    return MagicMock()


@pytest.fixture
def mock_cost_manager():
    """Create a mock cost manager."""
    return MagicMock()


@pytest.fixture
def bill_summarizer(mock_llm_analyzer, mock_citation_verifier, mock_cost_manager):
    """Create a bill summarizer instance."""
    return BillSummarizer(mock_llm_analyzer, mock_citation_verifier, mock_cost_manager)


@pytest.fixture
def sample_bill_text():
    """Sample bill text for testing."""
    return """
    THE AGRICULTURE AND FOOD SECURITY BILL, 2024

    PREAMBLE
    An Act of Parliament to establish and regulate agricultural production,
    food security, and related matters.

    PART I: PRELIMINARY PROVISIONS

    SECTION 1: Short title
    This Act may be cited as the Agriculture and Food Security Act, 2024.

    SECTION 2: Commencement
    This Act shall come into force on the date of assent by the President.

    SECTION 3: Interpretation
    In this Act, unless the context otherwise requires:
    "agricultural production" means the cultivation of crops and rearing of livestock
    "food security" means access by all people at all times to sufficient food

    PART II: ESTABLISHMENT OF AGRICULTURE AUTHORITY

    SECTION 4: Establishment
    There is established an Agriculture Authority to oversee agricultural development.

    SECTION 5: Functions
    The Authority shall:
    (a) promote agricultural development
    (b) ensure food security
    (c) regulate agricultural inputs
    """


class TestBillSummaryModel:
    """Tests for BillSummary Pydantic model."""

    def test_create_bill_summary(self):
        """Test creating a BillSummary."""
        summary = BillSummary(
            bill_number="5/2024",
            title="Agriculture Bill",
            summary="This bill establishes agricultural authority.",
            key_provisions=["Establish Authority", "Regulate inputs"],
            objectives=["Promote development", "Ensure food security"],
            affected_parties=["Farmers", "Government"],
        )

        assert summary.bill_number == "5/2024"
        assert summary.title == "Agriculture Bill"
        assert len(summary.key_provisions) == 2

    def test_bill_summary_validation(self):
        """Test BillSummary validation."""
        with pytest.raises(ValidationError):
            BillSummary(
                bill_number="5/2024",
                # Missing required 'title' field
                summary="Summary text",
            )

    def test_bill_summary_defaults(self):
        """Test BillSummary default values."""
        summary = BillSummary(
            bill_number="5/2024",
            title="Test Bill",
            summary="Test summary",
        )

        assert summary.key_provisions == []
        assert summary.objectives == []
        assert summary.cost_usd == 0.0
        assert summary.model == "claude-3.5-sonnet"


class TestBillSummarizerPromptBuilding:
    """Tests for prompt building."""

    def test_build_prompt_basic(self, bill_summarizer, sample_bill_text):
        """Test building a basic prompt."""
        prompt = bill_summarizer._build_prompt(
            sample_bill_text,
            "5/2024",
            "Agriculture Bill",
            "NATIONAL_ASSEMBLY",
            include_implementation=False,
            include_budget=False,
        )

        assert "5/2024" in prompt
        assert "Agriculture Bill" in prompt
        assert "NATIONAL_ASSEMBLY" in prompt
        assert "Main Summary" in prompt
        assert "Key Provisions" in prompt

    def test_build_prompt_with_implementation(self, bill_summarizer, sample_bill_text):
        """Test building prompt with implementation."""
        prompt = bill_summarizer._build_prompt(
            sample_bill_text,
            "5/2024",
            "Agriculture Bill",
            "NATIONAL_ASSEMBLY",
            include_implementation=True,
            include_budget=False,
        )

        assert "Implementation Timeline" in prompt

    def test_build_prompt_with_budget(self, bill_summarizer, sample_bill_text):
        """Test building prompt with budget implications."""
        prompt = bill_summarizer._build_prompt(
            sample_bill_text,
            "5/2024",
            "Agriculture Bill",
            "NATIONAL_ASSEMBLY",
            include_implementation=False,
            include_budget=True,
        )

        assert "Budget Implications" in prompt

    def test_build_prompt_truncates_text(self, bill_summarizer):
        """Test that prompt truncates very long text."""
        long_text = "section " * 1000  # Create long text
        prompt = bill_summarizer._build_prompt(
            long_text,
            "5/2024",
            "Agriculture Bill",
            "NATIONAL_ASSEMBLY",
            False,
            False,
        )

        # Should include truncation indicator
        assert "..." in prompt or len(prompt) < len(long_text)


class TestBillSummarizerResponseParsing:
    """Tests for response parsing."""

    def test_extract_section(self, bill_summarizer):
        """Test extracting a section from response."""
        text = """
        **Main Summary**: This bill establishes an agricultural authority.
        **Key Provisions**: The bill creates a new authority.
        """

        section = bill_summarizer._extract_section(text, "Main Summary")

        assert "authority" in section.lower()

    def test_extract_list_section(self, bill_summarizer):
        """Test extracting a list section."""
        text = """
        **Key Provisions**:
        1. Establish an agricultural authority
        2. Regulate agricultural inputs
        3. Promote food security
        """

        items = bill_summarizer._extract_list_section(text, "Key Provisions")

        assert len(items) >= 2

    def test_parse_response(self, bill_summarizer, sample_bill_text):
        """Test parsing a complete response."""
        response = {
            "summary": """**Main Summary**: Establishes agricultural authority.
**Key Provisions**:
1. Create authority
2. Regulate inputs
**Objectives**:
1. Promote development""",
        }

        result = bill_summarizer._parse_response(response, "5/2024", "Ag Bill", sample_bill_text)

        assert result["bill_number"] == "5/2024"
        assert result["title"] == "Ag Bill"
        assert isinstance(result["key_provisions"], list)
        assert isinstance(result["objectives"], list)


class TestBillSummarizerIntegration:
    """Tests for full summarization."""

    def test_summarize_bill_empty_text(self, bill_summarizer):
        """Test summarizing with empty text raises error."""
        with pytest.raises(ValueError):
            bill_summarizer.summarize_bill(
                "",
                "5/2024",
                "Test Bill",
            )

    def test_summarize_bill_llm_failure(self, bill_summarizer, mock_llm_analyzer, sample_bill_text):
        """Test handling LLM analysis failure."""
        mock_llm_analyzer.analyze.side_effect = Exception("LLM error")

        with pytest.raises(ValueError):
            bill_summarizer.summarize_bill(
                sample_bill_text,
                "5/2024",
                "Test Bill",
            )

    def test_summarize_bill_success(self, bill_summarizer, mock_llm_analyzer, sample_bill_text):
        """Test successful bill summarization."""
        mock_llm_analyzer.analyze.return_value = {
            "summary": "**Main Summary**: Test summary.",
            "cost_usd": 0.05,
        }

        summary = bill_summarizer.summarize_bill(
            sample_bill_text,
            "5/2024",
            "Agriculture Bill",
        )

        assert isinstance(summary, BillSummary)
        assert summary.bill_number == "5/2024"
        assert summary.title == "Agriculture Bill"

    def test_summarize_bill_with_citations(
        self, bill_summarizer, mock_llm_analyzer, mock_citation_verifier, sample_bill_text
    ):
        """Test summarization with citation verification."""
        mock_llm_analyzer.analyze.return_value = {
            "summary": """
            **Main Summary**: Test summary.
            **Important Claims**:
            - Agricultural production affects 80% of rural population
            - Food security requires multi-sector approach
            """,
            "cost_usd": 0.05,
        }

        mock_citation_verifier.verify_claim.return_value = {"verified": True, "confidence": 0.9}

        summary = bill_summarizer.summarize_bill(
            sample_bill_text,
            "5/2024",
            "Agriculture Bill",
        )

        assert len(summary.citations) > 0


class TestBillSummarizerBatch:
    """Tests for batch summarization."""

    def test_summarize_batch_empty(self, bill_summarizer):
        """Test batch summarization with empty list."""
        summaries = bill_summarizer.summarize_batch([])

        assert summaries == []

    def test_summarize_batch_single(self, bill_summarizer, mock_llm_analyzer, sample_bill_text):
        """Test batch summarization with single bill."""
        mock_llm_analyzer.analyze.return_value = {
            "summary": "**Main Summary**: Test.",
            "cost_usd": 0.05,
        }

        bills = [
            {
                "bill_number": "5/2024",
                "bill_text": sample_bill_text,
                "title": "Ag Bill",
                "chamber": "NATIONAL_ASSEMBLY",
            }
        ]

        summaries = bill_summarizer.summarize_batch(bills)

        assert len(summaries) == 1
        assert summaries[0].bill_number == "5/2024"

    def test_summarize_batch_with_failure(
        self, bill_summarizer, mock_llm_analyzer, sample_bill_text
    ):
        """Test batch summarization handles failures gracefully."""
        mock_llm_analyzer.analyze.side_effect = Exception("LLM error")

        bills = [
            {
                "bill_number": "5/2024",
                "bill_text": sample_bill_text,
                "title": "Ag Bill",
                "chamber": "NATIONAL_ASSEMBLY",
            }
        ]

        summaries = bill_summarizer.summarize_batch(bills)

        # Should handle error and continue
        assert isinstance(summaries, list)


class TestBillSummarizerCostTracking:
    """Tests for cost tracking."""

    def test_cost_tracking_called(
        self, bill_summarizer, mock_llm_analyzer, mock_cost_manager, sample_bill_text
    ):
        """Test that cost manager is called."""
        mock_llm_analyzer.analyze.return_value = {
            "summary": "**Main Summary**: Test.",
            "cost_usd": 0.05,
        }

        bill_summarizer.summarize_bill(sample_bill_text, "5/2024", "Test Bill")

        mock_cost_manager.track_usage.assert_called_once()

    def test_cost_tracking_without_manager(self, mock_llm_analyzer, sample_bill_text):
        """Test summarization works without cost manager."""
        mock_llm_analyzer.analyze.return_value = {
            "summary": "**Main Summary**: Test.",
            "cost_usd": 0.05,
        }

        summarizer = BillSummarizer(mock_llm_analyzer, cost_manager=None)
        summary = summarizer.summarize_bill(sample_bill_text, "5/2024", "Test Bill")

        assert isinstance(summary, BillSummary)
