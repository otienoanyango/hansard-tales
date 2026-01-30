"""
LLM-based analysis of parliamentary statements.

This module provides LLM-powered analysis using Claude 3.5 Haiku for:
- Sentiment analysis
- Quality scoring
- Topic classification
- Key point extraction
- Citation generation

All analysis includes verifiable citations to prevent hallucination.
"""

import json
import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


class StatementAnalysis(BaseModel):
    """
    LLM analysis result for a parliamentary statement.

    This model captures all analysis outputs from the LLM including
    sentiment, quality, topics, and citations for verification.
    """

    model_config = {
        "json_schema_extra": {
            "example": {
                "sentiment": "positive",
                "sentiment_confidence": 0.85,
                "sentiment_explanation": "MP expresses strong support for the bill",
                "quality_score": 75,
                "quality_factors": {"clarity": 80, "depth": 70, "evidence": 75},
                "primary_topic": "Healthcare",
                "secondary_topics": ["Budget", "Infrastructure"],
                "topic_confidence": 0.90,
                "key_points": [
                    "Proposes increased healthcare funding",
                    "Cites rural hospital shortages",
                    "Suggests partnership with private sector",
                ],
                "citations": [
                    "We must increase healthcare funding by 20%",
                    "Rural hospitals are severely understaffed",
                ],
            }
        }
    }

    # Sentiment analysis
    sentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
        description="Overall sentiment of the statement"
    )
    sentiment_confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in sentiment classification"
    )
    sentiment_explanation: str = Field(description="Brief explanation of sentiment determination")

    # Quality scoring
    quality_score: int = Field(ge=0, le=100, description="Overall quality score (0-100)")
    quality_factors: dict[str, int] = Field(
        description="Breakdown of quality factors (clarity, depth, evidence, etc.)"
    )

    # Topic classification
    primary_topic: str = Field(description="Main topic of the statement")
    secondary_topics: list[str] = Field(
        default_factory=list, description="Additional topics discussed"
    )
    topic_confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in topic classification"
    )

    # Key points
    key_points: list[str] = Field(
        default_factory=list, max_length=5, description="Key points from the statement (max 5)"
    )

    # Citations (for verification)
    citations: list[str] = Field(
        default_factory=list, description="Direct quotes from statement for verification"
    )


@dataclass
class Statement:
    """Statement data for analysis (temporary until proper model is imported)."""

    text: str
    mp_id: str | None = None
    session_id: str | None = None


@dataclass
class RetrievedContext:
    """Context retrieved for a statement (temporary until proper import)."""

    historical_statements: list[dict] = None
    related_bills: list[dict] = None
    related_votes: list[dict] = None
    session_context: list[dict] = None

    def __post_init__(self):
        """Initialize empty lists if None."""
        if self.historical_statements is None:
            self.historical_statements = []
        if self.related_bills is None:
            self.related_bills = []
        if self.related_votes is None:
            self.related_votes = []
        if self.session_context is None:
            self.session_context = []


class LLMAnalyzer:
    """
    Analyze parliamentary statements using Claude LLM.

    This class provides AI-powered analysis of statements including:
    - Sentiment analysis (positive/negative/neutral/mixed)
    - Quality scoring (0-100 based on clarity, depth, evidence)
    - Topic classification (primary and secondary topics)
    - Key point extraction (max 5 points)
    - Citation generation for verification

    All analysis includes citations to prevent hallucination.

    Example:
        >>> analyzer = LLMAnalyzer(api_key="sk-...")
        >>> statement = Statement(text="We must increase healthcare funding...")
        >>> analysis = analyzer.analyze(statement)
        >>> print(analysis.sentiment)
        'positive'
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-5-haiku-20241022",
        max_tokens: int = 1024,
        temperature: float = 0.0,
        timeout: int = 60,
    ):
        """
        Initialize LLM analyzer with Anthropic client.

        Args:
            api_key: Anthropic API key (if None, reads from LLM_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 for deterministic)
            timeout: Request timeout in seconds

        Raises:
            ValueError: If api_key is not provided and LLM_API_KEY env var is not set
        """
        import os

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Provide via api_key parameter or LLM_API_KEY env var"
            )

        # Initialize Anthropic client (lazy import for testing)
        self.client = self._init_client(timeout)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # System prompt for analysis
        self.system_prompt = """You are analyzing Kenyan parliamentary statements.

Your task:
1. Determine sentiment (positive/negative/neutral/mixed)
2. Score quality (0-100) based on clarity, depth, evidence
3. Identify primary and secondary topics
4. Extract key points (max 5)
5. Provide direct quotes as citations

CRITICAL: Only use information from the statement itself.
Do not make assumptions or add external knowledge.
All citations must be exact quotes from the statement."""

    def _init_client(self, timeout: int):
        """Initialize Anthropic client (separate method for easier mocking)."""
        try:
            import anthropic
        except ImportError as e:
            raise ImportError(
                "anthropic package required. Install with: pip install anthropic"
            ) from e

        return anthropic.Anthropic(api_key=self.api_key, timeout=timeout)

    def _build_prompt(self, statement: Statement, context: RetrievedContext | None = None) -> str:
        """
        Build analysis prompt with optional context.

        Args:
            statement: Statement to analyze
            context: Optional retrieved context (historical statements, bills, votes)

        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze this parliamentary statement:

STATEMENT:
{statement.text}

"""

        # Add historical context if available
        if context and context.historical_statements:
            prompt += "\nHISTORICAL CONTEXT (previous statements by this MP):\n"
            for hist in context.historical_statements[:3]:
                # Truncate long statements
                hist_text = hist.get("text", "")[:200]
                if len(hist.get("text", "")) > 200:
                    hist_text += "..."
                prompt += f"- {hist_text}\n"

        # Add related bills context if available
        if context and context.related_bills:
            prompt += "\nRELATED BILLS:\n"
            for bill in context.related_bills[:2]:
                bill_title = bill.get("title", "Unknown")
                prompt += f"- {bill_title}\n"

        # Add related votes context if available
        if context and context.related_votes:
            prompt += "\nRELATED VOTES:\n"
            for vote in context.related_votes[:2]:
                vote_text = vote.get("motion_text", "Unknown")[:100]
                prompt += f"- {vote_text}\n"

        prompt += """
Provide analysis in JSON format:
{
  "sentiment": "positive|negative|neutral|mixed",
  "sentiment_confidence": 0.0-1.0,
  "sentiment_explanation": "brief explanation",
  "quality_score": 0-100,
  "quality_factors": {"clarity": 0-100, "depth": 0-100, "evidence": 0-100},
  "primary_topic": "main topic",
  "secondary_topics": ["topic1", "topic2"],
  "topic_confidence": 0.0-1.0,
  "key_points": ["point1", "point2", ...],
  "citations": ["exact quote 1", "exact quote 2", ...]
}"""

        return prompt

    def _call_api(self, prompt: str) -> str:
        """
        Call Anthropic API with error handling.

        Args:
            prompt: User prompt to send

        Returns:
            Response text from API

        Raises:
            ValueError: If API call fails after retries
        """
        import time

        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=self.system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Extract text from response
                if response.content and len(response.content) > 0:
                    return response.content[0].text

                raise ValueError("Empty response from API")

            except Exception as e:
                if attempt == max_retries - 1:
                    raise ValueError(f"API call failed after {max_retries} retries: {e}") from e

                # Exponential backoff
                time.sleep(retry_delay * (2**attempt))
                continue

        raise ValueError("API call failed")

    def _parse_response(self, response_text: str) -> StatementAnalysis:
        """
        Parse LLM response into structured format.

        Args:
            response_text: Raw response text from API

        Returns:
            Parsed StatementAnalysis object

        Raises:
            ValueError: If response cannot be parsed
        """
        # Extract JSON from response (may be wrapped in markdown code blocks)
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if not json_match:
                raise ValueError(f"No JSON found in response: {response_text[:200]}")
            json_str = json_match.group(0)

        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in response: {e}") from e

        # Validate and create StatementAnalysis
        try:
            return StatementAnalysis(**data)
        except Exception as e:
            raise ValueError(f"Invalid analysis data: {e}") from e

    def analyze(
        self, statement: Statement, context: RetrievedContext | None = None
    ) -> StatementAnalysis:
        """
        Analyze a parliamentary statement.

        Args:
            statement: Statement to analyze
            context: Optional retrieved context for better analysis

        Returns:
            StatementAnalysis with sentiment, quality, topics, and citations

        Raises:
            ValueError: If analysis fails

        Example:
            >>> analyzer = LLMAnalyzer(api_key="sk-...")
            >>> statement = Statement(text="We must increase healthcare funding...")
            >>> analysis = analyzer.analyze(statement)
            >>> print(f"Sentiment: {analysis.sentiment}")
            >>> print(f"Quality: {analysis.quality_score}")
        """
        # Build prompt
        prompt = self._build_prompt(statement, context)

        # Call API
        response_text = self._call_api(prompt)

        # Parse response
        analysis = self._parse_response(response_text)

        return analysis

    def analyze_batch(
        self,
        statements: list[Statement],
        contexts: list[RetrievedContext | None] | None = None,
        batch_size: int = 10,
    ) -> list[StatementAnalysis]:
        """
        Analyze multiple statements in batches.

        Args:
            statements: List of statements to analyze
            contexts: Optional list of contexts (one per statement)
            batch_size: Number of statements to process at once

        Returns:
            List of StatementAnalysis results (same order as input)

        Example:
            >>> analyzer = LLMAnalyzer(api_key="sk-...")
            >>> statements = [Statement(text="..."), Statement(text="...")]
            >>> results = analyzer.analyze_batch(statements)
            >>> print(f"Analyzed {len(results)} statements")
        """
        results = []

        # Ensure contexts list matches statements length
        if contexts is None:
            contexts = [None] * len(statements)
        elif len(contexts) != len(statements):
            raise ValueError("contexts list must match statements length")

        # Process in batches
        for i in range(0, len(statements), batch_size):
            batch_statements = statements[i : i + batch_size]
            batch_contexts = contexts[i : i + batch_size]

            # Process each statement in batch
            for statement, context in zip(batch_statements, batch_contexts, strict=False):
                try:
                    analysis = self.analyze(statement, context)
                    results.append(analysis)
                except Exception as e:
                    # Log error but continue processing
                    print(f"Error analyzing statement: {e}")
                    # Create error analysis
                    results.append(
                        StatementAnalysis(
                            sentiment="neutral",
                            sentiment_confidence=0.0,
                            sentiment_explanation=f"Analysis failed: {str(e)[:100]}",
                            quality_score=0,
                            quality_factors={"clarity": 0, "depth": 0, "evidence": 0},
                            primary_topic="Unknown",
                            secondary_topics=[],
                            topic_confidence=0.0,
                            key_points=[],
                            citations=[],
                        )
                    )

        return results
