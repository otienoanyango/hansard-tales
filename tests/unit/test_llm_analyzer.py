"""
Unit tests for LLM analyzer.

Tests LLM-based analysis of parliamentary statements including:
- Prompt building with context
- Response parsing
- Error handling
- Batch processing
"""

from unittest.mock import Mock, patch

import pytest

from hansard_tales.analysis.llm_analyzer import (
    LLMAnalyzer,
    RetrievedContext,
    Statement,
    StatementAnalysis,
)


class TestPromptBuilding:
    """Test prompt building functionality."""

    @patch.object(LLMAnalyzer, "_init_client")
    def test_build_prompt_basic(self, mock_init_client):
        """Test basic prompt building without context."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")
        statement = Statement(text="We must increase healthcare funding by 20%")

        prompt = analyzer._build_prompt(statement)

        assert "We must increase healthcare funding by 20%" in prompt
        assert "STATEMENT:" in prompt
        assert "JSON format" in prompt

    @patch.object(LLMAnalyzer, "_init_client")
    def test_build_prompt_with_historical_context(self, mock_init_client):
        """Test prompt building with historical statements."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")
        statement = Statement(text="Healthcare is critical")

        context = RetrievedContext(
            historical_statements=[
                {"text": "I have always supported healthcare initiatives"},
                {"text": "Rural hospitals need more funding"},
            ]
        )

        prompt = analyzer._build_prompt(statement, context)

        assert "HISTORICAL CONTEXT" in prompt
        assert "I have always supported healthcare initiatives" in prompt
        assert "Rural hospitals need more funding" in prompt

    @patch.object(LLMAnalyzer, "_init_client")
    def test_build_prompt_with_related_bills(self, mock_init_client):
        """Test prompt building with related bills."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")
        statement = Statement(text="This bill will help")

        context = RetrievedContext(
            related_bills=[
                {"title": "The Healthcare Financing Bill, 2024"},
                {"title": "The Medical Insurance Bill, 2024"},
            ]
        )

        prompt = analyzer._build_prompt(statement, context)

        assert "RELATED BILLS" in prompt
        assert "The Healthcare Financing Bill, 2024" in prompt

    @patch.object(LLMAnalyzer, "_init_client")
    def test_build_prompt_with_related_votes(self, mock_init_client):
        """Test prompt building with related votes."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")
        statement = Statement(text="We voted on this")

        context = RetrievedContext(
            related_votes=[
                {"motion_text": "Motion to increase healthcare budget"},
            ]
        )

        prompt = analyzer._build_prompt(statement, context)

        assert "RELATED VOTES" in prompt
        assert "Motion to increase healthcare budget" in prompt

    @patch.object(LLMAnalyzer, "_init_client")
    def test_build_prompt_truncates_long_historical_statements(self, mock_init_client):
        """Test that long historical statements are truncated."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")
        statement = Statement(text="Short statement")

        long_text = "A" * 300  # Longer than 200 char limit
        context = RetrievedContext(historical_statements=[{"text": long_text}])

        prompt = analyzer._build_prompt(statement, context)

        # Should be truncated to 200 chars + "..."
        assert long_text[:200] in prompt
        assert "..." in prompt
        assert long_text not in prompt  # Full text should not be present

    @patch.object(LLMAnalyzer, "_init_client")
    def test_build_prompt_limits_context_items(self, mock_init_client):
        """Test that context items are limited to reasonable numbers."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")
        statement = Statement(text="Test")

        # Provide more items than should be included
        context = RetrievedContext(
            historical_statements=[{"text": f"Statement {i}"} for i in range(10)],
            related_bills=[{"title": f"Bill {i}"} for i in range(10)],
            related_votes=[{"motion_text": f"Vote {i}"} for i in range(10)],
        )

        prompt = analyzer._build_prompt(statement, context)

        # Should only include first 3 historical statements
        assert "Statement 0" in prompt
        assert "Statement 1" in prompt
        assert "Statement 2" in prompt
        assert "Statement 3" not in prompt

        # Should only include first 2 bills
        assert "Bill 0" in prompt
        assert "Bill 1" in prompt
        assert "Bill 2" not in prompt


class TestResponseParsing:
    """Test response parsing functionality."""

    @patch.object(LLMAnalyzer, "_init_client")
    def test_parse_response_valid_json(self, mock_init_client):
        """Test parsing valid JSON response."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")

        response_text = """{
  "sentiment": "positive",
  "sentiment_confidence": 0.85,
  "sentiment_explanation": "MP expresses strong support",
  "quality_score": 75,
  "quality_factors": {"clarity": 80, "depth": 70, "evidence": 75},
  "primary_topic": "Healthcare",
  "secondary_topics": ["Budget", "Infrastructure"],
  "topic_confidence": 0.90,
  "key_points": ["Increase funding", "Rural hospitals"],
  "citations": ["We must increase healthcare funding"]
}"""

        analysis = analyzer._parse_response(response_text)

        assert isinstance(analysis, StatementAnalysis)
        assert analysis.sentiment == "positive"
        assert analysis.sentiment_confidence == 0.85
        assert analysis.quality_score == 75
        assert analysis.primary_topic == "Healthcare"
        assert len(analysis.secondary_topics) == 2
        assert len(analysis.key_points) == 2
        assert len(analysis.citations) == 1

    @patch.object(LLMAnalyzer, "_init_client")
    def test_parse_response_json_in_markdown(self, mock_init_client):
        """Test parsing JSON wrapped in markdown code blocks."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")

        response_text = """Here's the analysis:

```json
{
  "sentiment": "neutral",
  "sentiment_confidence": 0.70,
  "sentiment_explanation": "Balanced statement",
  "quality_score": 60,
  "quality_factors": {"clarity": 60, "depth": 60, "evidence": 60},
  "primary_topic": "Education",
  "secondary_topics": [],
  "topic_confidence": 0.80,
  "key_points": ["Point 1"],
  "citations": ["Quote 1"]
}
```

That's the result."""

        analysis = analyzer._parse_response(response_text)

        assert isinstance(analysis, StatementAnalysis)
        assert analysis.sentiment == "neutral"
        assert analysis.primary_topic == "Education"

    @patch.object(LLMAnalyzer, "_init_client")
    def test_parse_response_invalid_json(self, mock_init_client):
        """Test error handling for invalid JSON."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")

        response_text = "This is not JSON at all"

        with pytest.raises(ValueError, match="No JSON found"):
            analyzer._parse_response(response_text)

    @patch.object(LLMAnalyzer, "_init_client")
    def test_parse_response_malformed_json(self, mock_init_client):
        """Test error handling for malformed JSON."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")

        response_text = '{"sentiment": "positive", invalid}'

        with pytest.raises(ValueError, match="Invalid JSON"):
            analyzer._parse_response(response_text)

    @patch.object(LLMAnalyzer, "_init_client")
    def test_parse_response_missing_required_fields(self, mock_init_client):
        """Test error handling for missing required fields."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")

        # Missing sentiment_confidence
        response_text = """{
  "sentiment": "positive",
  "sentiment_explanation": "Good",
  "quality_score": 75,
  "quality_factors": {"clarity": 80},
  "primary_topic": "Healthcare",
  "topic_confidence": 0.90
}"""

        with pytest.raises(ValueError, match="Invalid analysis data"):
            analyzer._parse_response(response_text)

    @patch.object(LLMAnalyzer, "_init_client")
    def test_parse_response_invalid_sentiment_value(self, mock_init_client):
        """Test error handling for invalid sentiment value."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")

        response_text = """{
  "sentiment": "invalid_sentiment",
  "sentiment_confidence": 0.85,
  "sentiment_explanation": "Test",
  "quality_score": 75,
  "quality_factors": {"clarity": 80},
  "primary_topic": "Healthcare",
  "topic_confidence": 0.90,
  "key_points": [],
  "citations": []
}"""

        with pytest.raises(ValueError):
            analyzer._parse_response(response_text)

    @patch.object(LLMAnalyzer, "_init_client")
    def test_parse_response_quality_score_out_of_range(self, mock_init_client):
        """Test error handling for quality score out of range."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")

        response_text = """{
  "sentiment": "positive",
  "sentiment_confidence": 0.85,
  "sentiment_explanation": "Test",
  "quality_score": 150,
  "quality_factors": {"clarity": 80},
  "primary_topic": "Healthcare",
  "topic_confidence": 0.90,
  "key_points": [],
  "citations": []
}"""

        with pytest.raises(ValueError):
            analyzer._parse_response(response_text)


class TestErrorHandling:
    """Test error handling functionality."""

    def test_init_without_api_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(ValueError, match="API key required"):
            LLMAnalyzer()

    @patch.object(LLMAnalyzer, "_init_client")
    def test_init_with_api_key_parameter(self, mock_init_client):
        """Test initialization with API key parameter."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")
        assert analyzer.api_key == "test-key"

    @patch.dict("os.environ", {"LLM_API_KEY": "env-key"})
    @patch.object(LLMAnalyzer, "_init_client")
    def test_init_with_env_var(self, mock_init_client):
        """Test initialization with environment variable."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer()
        assert analyzer.api_key == "env-key"

    @patch.object(LLMAnalyzer, "_init_client")
    def test_api_call_retry_on_failure(self, mock_init_client):
        """Test API call retries on failure."""
        # Mock client to fail twice then succeed
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Success")]

        mock_client.messages.create.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            mock_response,
        ]

        mock_init_client.return_value = mock_client
        analyzer = LLMAnalyzer(api_key="test-key")

        result = analyzer._call_api("test prompt")

        assert result == "Success"
        assert mock_client.messages.create.call_count == 3

    @patch.object(LLMAnalyzer, "_init_client")
    def test_api_call_fails_after_max_retries(self, mock_init_client):
        """Test API call fails after max retries."""
        # Mock client to always fail
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("Network error")
        mock_init_client.return_value = mock_client
        analyzer = LLMAnalyzer(api_key="test-key")

        with pytest.raises(ValueError, match="API call failed after 3 retries"):
            analyzer._call_api("test prompt")

        assert mock_client.messages.create.call_count == 3

    @patch.object(LLMAnalyzer, "_init_client")
    def test_api_call_empty_response(self, mock_init_client):
        """Test API call handles empty response."""
        # Mock client to return empty response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = []
        mock_client.messages.create.return_value = mock_response
        mock_init_client.return_value = mock_client
        analyzer = LLMAnalyzer(api_key="test-key")

        with pytest.raises(ValueError, match="Empty response"):
            analyzer._call_api("test prompt")


class TestBatchProcessing:
    """Test batch processing functionality."""

    @patch.object(LLMAnalyzer, "_init_client")
    @patch.object(LLMAnalyzer, "analyze")
    def test_analyze_batch_basic(self, mock_analyze, mock_init_client):
        """Test basic batch analysis."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")

        statements = [
            Statement(text="Statement 1"),
            Statement(text="Statement 2"),
            Statement(text="Statement 3"),
        ]

        # Mock analyze to return different results
        mock_analyze.side_effect = [
            StatementAnalysis(
                sentiment="positive",
                sentiment_confidence=0.8,
                sentiment_explanation="Good",
                quality_score=70,
                quality_factors={"clarity": 70},
                primary_topic="Topic1",
                topic_confidence=0.8,
            ),
            StatementAnalysis(
                sentiment="negative",
                sentiment_confidence=0.7,
                sentiment_explanation="Bad",
                quality_score=60,
                quality_factors={"clarity": 60},
                primary_topic="Topic2",
                topic_confidence=0.7,
            ),
            StatementAnalysis(
                sentiment="neutral",
                sentiment_confidence=0.9,
                sentiment_explanation="Neutral",
                quality_score=80,
                quality_factors={"clarity": 80},
                primary_topic="Topic3",
                topic_confidence=0.9,
            ),
        ]

        results = analyzer.analyze_batch(statements)

        assert len(results) == 3
        assert results[0].sentiment == "positive"
        assert results[1].sentiment == "negative"
        assert results[2].sentiment == "neutral"
        assert mock_analyze.call_count == 3

    @patch.object(LLMAnalyzer, "_init_client")
    @patch.object(LLMAnalyzer, "analyze")
    def test_analyze_batch_with_contexts(self, mock_analyze, mock_init_client):
        """Test batch analysis with contexts."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")

        statements = [Statement(text="S1"), Statement(text="S2")]
        contexts = [
            RetrievedContext(historical_statements=[{"text": "H1"}]),
            RetrievedContext(historical_statements=[{"text": "H2"}]),
        ]

        mock_analyze.return_value = StatementAnalysis(
            sentiment="neutral",
            sentiment_confidence=0.5,
            sentiment_explanation="Test",
            quality_score=50,
            quality_factors={"clarity": 50},
            primary_topic="Test",
            topic_confidence=0.5,
        )

        results = analyzer.analyze_batch(statements, contexts)

        assert len(results) == 2
        # Verify contexts were passed
        assert mock_analyze.call_args_list[0][0][1] == contexts[0]
        assert mock_analyze.call_args_list[1][0][1] == contexts[1]

    @patch.object(LLMAnalyzer, "_init_client")
    @patch.object(LLMAnalyzer, "analyze")
    def test_analyze_batch_handles_errors(self, mock_analyze, mock_init_client):
        """Test batch analysis handles individual errors."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")

        statements = [
            Statement(text="S1"),
            Statement(text="S2"),
            Statement(text="S3"),
        ]

        # Mock analyze to fail on second statement
        mock_analyze.side_effect = [
            StatementAnalysis(
                sentiment="positive",
                sentiment_confidence=0.8,
                sentiment_explanation="Good",
                quality_score=70,
                quality_factors={"clarity": 70},
                primary_topic="Topic1",
                topic_confidence=0.8,
            ),
            Exception("API error"),
            StatementAnalysis(
                sentiment="neutral",
                sentiment_confidence=0.9,
                sentiment_explanation="Neutral",
                quality_score=80,
                quality_factors={"clarity": 80},
                primary_topic="Topic3",
                topic_confidence=0.9,
            ),
        ]

        results = analyzer.analyze_batch(statements)

        # Should still return 3 results
        assert len(results) == 3
        assert results[0].sentiment == "positive"
        # Second result should be error placeholder
        assert results[1].sentiment == "neutral"
        assert results[1].quality_score == 0
        assert "Analysis failed" in results[1].sentiment_explanation
        assert results[2].sentiment == "neutral"
        assert results[2].quality_score == 80

    @patch.object(LLMAnalyzer, "_init_client")
    def test_analyze_batch_contexts_length_mismatch(self, mock_init_client):
        """Test error when contexts length doesn't match statements."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")

        statements = [Statement(text="S1"), Statement(text="S2")]
        contexts = [RetrievedContext()]  # Only one context

        with pytest.raises(ValueError, match="contexts list must match"):
            analyzer.analyze_batch(statements, contexts)

    @patch.object(LLMAnalyzer, "_init_client")
    @patch.object(LLMAnalyzer, "analyze")
    def test_analyze_batch_respects_batch_size(self, mock_analyze, mock_init_client):
        """Test batch processing respects batch_size parameter."""
        mock_init_client.return_value = Mock()
        analyzer = LLMAnalyzer(api_key="test-key")

        statements = [Statement(text=f"S{i}") for i in range(25)]

        mock_analyze.return_value = StatementAnalysis(
            sentiment="neutral",
            sentiment_confidence=0.5,
            sentiment_explanation="Test",
            quality_score=50,
            quality_factors={"clarity": 50},
            primary_topic="Test",
            topic_confidence=0.5,
        )

        results = analyzer.analyze_batch(statements, batch_size=10)

        assert len(results) == 25
        assert mock_analyze.call_count == 25


class TestMockedAPIIntegration:
    """Test full analysis flow with mocked API calls."""

    @patch.object(LLMAnalyzer, "_init_client")
    def test_analyze_with_mocked_api(self, mock_init_client):
        """Test full analyze flow with mocked API."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text="""{
  "sentiment": "positive",
  "sentiment_confidence": 0.85,
  "sentiment_explanation": "MP strongly supports healthcare",
  "quality_score": 75,
  "quality_factors": {"clarity": 80, "depth": 70, "evidence": 75},
  "primary_topic": "Healthcare",
  "secondary_topics": ["Budget"],
  "topic_confidence": 0.90,
  "key_points": ["Increase funding", "Rural hospitals"],
  "citations": ["We must increase healthcare funding"]
}"""
            )
        ]
        mock_client.messages.create.return_value = mock_response
        mock_init_client.return_value = mock_client

        # Create analyzer and analyze
        analyzer = LLMAnalyzer(api_key="test-key")
        statement = Statement(text="We must increase healthcare funding by 20%")

        analysis = analyzer.analyze(statement)

        # Verify results
        assert analysis.sentiment == "positive"
        assert analysis.sentiment_confidence == 0.85
        assert analysis.quality_score == 75
        assert analysis.primary_topic == "Healthcare"
        assert "Budget" in analysis.secondary_topics
        assert len(analysis.key_points) == 2
        assert len(analysis.citations) == 1

        # Verify API was called correctly
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert call_args[1]["model"] == "claude-3-5-haiku-20241022"
        assert call_args[1]["max_tokens"] == 1024
        assert call_args[1]["temperature"] == 0.0

    @patch.object(LLMAnalyzer, "_init_client")
    def test_analyze_with_context_mocked_api(self, mock_init_client):
        """Test analyze with context using mocked API."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text="""{
  "sentiment": "positive",
  "sentiment_confidence": 0.90,
  "sentiment_explanation": "Consistent support based on history",
  "quality_score": 80,
  "quality_factors": {"clarity": 85, "depth": 75, "evidence": 80},
  "primary_topic": "Healthcare",
  "secondary_topics": [],
  "topic_confidence": 0.95,
  "key_points": ["Consistent position"],
  "citations": ["Healthcare is my priority"]
}"""
            )
        ]
        mock_client.messages.create.return_value = mock_response
        mock_init_client.return_value = mock_client

        # Create analyzer with context
        analyzer = LLMAnalyzer(api_key="test-key")
        statement = Statement(text="Healthcare is my priority")
        context = RetrievedContext(
            historical_statements=[{"text": "I have always supported healthcare"}]
        )

        analysis = analyzer.analyze(statement, context)

        # Verify results
        assert analysis.sentiment == "positive"
        assert analysis.sentiment_confidence == 0.90

        # Verify prompt included context
        call_args = mock_client.messages.create.call_args
        prompt = call_args[1]["messages"][0]["content"]
        assert "HISTORICAL CONTEXT" in prompt
        assert "I have always supported healthcare" in prompt

    @patch.object(LLMAnalyzer, "_init_client")
    def test_analyze_handles_markdown_wrapped_json(self, mock_init_client):
        """Test analyze handles JSON wrapped in markdown."""
        # Setup mock with markdown-wrapped JSON
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text="""Here's my analysis:

```json
{
  "sentiment": "neutral",
  "sentiment_confidence": 0.70,
  "sentiment_explanation": "Balanced view",
  "quality_score": 65,
  "quality_factors": {"clarity": 70, "depth": 60, "evidence": 65},
  "primary_topic": "Education",
  "secondary_topics": [],
  "topic_confidence": 0.80,
  "key_points": ["Point 1"],
  "citations": ["Quote 1"]
}
```

That's my assessment."""
            )
        ]
        mock_client.messages.create.return_value = mock_response
        mock_init_client.return_value = mock_client

        # Create analyzer and analyze
        analyzer = LLMAnalyzer(api_key="test-key")
        statement = Statement(text="Education needs reform")

        analysis = analyzer.analyze(statement)

        # Verify results
        assert analysis.sentiment == "neutral"
        assert analysis.primary_topic == "Education"
