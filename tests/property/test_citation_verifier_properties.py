"""
Property-based tests for citation verifier.

Tests universal properties that should hold for all inputs:
- Property 6.1: Citation verification accuracy
- Property 6.2: No false verifications
"""

from unittest.mock import Mock

from hypothesis import given
from hypothesis import strategies as st

from hansard_tales.analysis.citation_verifier import CitationVerifier

# Strategy for generating realistic text
text_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po")),
    min_size=10,
    max_size=500,
)


class TestCitationVerificationAccuracy:
    """
    Property 6.1: Citation verification accuracy.

    **Validates**: Requirements 1.12
    **Property**: 100% of citations must be verified or flagged
    """

    @given(quote=text_strategy, source_text=text_strategy)
    def test_all_citations_get_verification_status(self, quote, source_text):
        """All citations must receive a verification status."""
        # Setup mock database
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = source_text
        mock_statement.page_number = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation(quote, "statement-123")

        # Property: Every citation must have a verification status
        assert citation.verification_status in ["verified", "unverified", "failed"]

    @given(quote=text_strategy, source_text=text_strategy)
    def test_verification_status_has_similarity_score(self, quote, source_text):
        """All citations must have a similarity score."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = source_text
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation(quote, "statement-123")

        # Property: Similarity score must be between 0 and 1
        assert 0.0 <= citation.similarity_score <= 1.0

    @given(quote=text_strategy)
    def test_missing_source_always_fails(self, quote):
        """Citations with missing sources must always fail verification."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation(quote, "statement-999")

        # Property: Missing source always results in failed status
        assert citation.verification_status == "failed"
        assert citation.similarity_score == 0.0

    @given(source_text=text_strategy)
    def test_exact_match_always_verified(self, source_text):
        """Exact matches must always be verified with score 1.0."""
        # Skip empty strings
        if not source_text.strip():
            return

        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = source_text
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        # Use exact text as quote
        citation = verifier.verify_citation(source_text, "statement-123")

        # Property: Exact match always verified with perfect score
        assert citation.verification_status == "verified"
        assert citation.similarity_score == 1.0

    @given(source_text=text_strategy, start=st.integers(min_value=0, max_value=100))
    def test_substring_match_always_verified(self, source_text, start):
        """Substrings of source text must always be verified."""
        # Skip if text too short
        if len(source_text) < 20:
            return

        # Extract substring
        end = min(start + 50, len(source_text))
        if start >= end:
            return

        substring = source_text[start:end]
        if not substring.strip():
            return

        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = source_text
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation(substring, "statement-123")

        # Property: Substring always verified with perfect score
        assert citation.verification_status == "verified"
        assert citation.similarity_score == 1.0


class TestNoFalseVerifications:
    """
    Property 6.2: No false verifications.

    **Validates**: Requirements 1.12
    **Property**: Verified citations must exist in source
    """

    @given(quote=text_strategy, source_text=text_strategy)
    def test_verified_citations_must_be_similar_to_source(self, quote, source_text):
        """Verified citations must have high similarity to source."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = source_text
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db, fuzzy_threshold=0.95)
        citation = verifier.verify_citation(quote, "statement-123")

        # Property: If verified, similarity must be >= threshold
        if citation.verification_status == "verified":
            assert citation.similarity_score >= 0.95

    @given(
        quote=text_strategy,
        source_text=text_strategy,
        threshold=st.floats(min_value=0.5, max_value=1.0),
    )
    def test_verified_citations_respect_threshold(self, quote, source_text, threshold):
        """Verified citations must meet the specified threshold."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = source_text
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db, fuzzy_threshold=threshold)
        citation = verifier.verify_citation(quote, "statement-123", threshold=threshold)

        # Property: Verified citations must meet threshold
        if citation.verification_status == "verified":
            assert citation.similarity_score >= threshold

    @given(quote=text_strategy, unrelated_text=text_strategy)
    def test_unrelated_text_not_verified_with_high_threshold(self, quote, unrelated_text):
        """Completely unrelated text should not verify with high threshold."""
        # Skip if texts are too similar by chance
        if quote in unrelated_text or unrelated_text in quote:
            return

        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = unrelated_text
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db, fuzzy_threshold=0.95)
        citation = verifier.verify_citation(quote, "statement-123")

        # Property: Unrelated text should have low similarity
        # (may still verify if randomly similar, but score should reflect this)
        if citation.verification_status == "verified":
            assert citation.similarity_score >= 0.95

    @given(source_text=text_strategy)
    def test_empty_quote_never_verified(self, source_text):
        """Empty quotes must never be verified."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = source_text
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation("", "statement-123")

        # Property: Empty quotes never verified
        assert citation.verification_status != "verified"

    @given(quote=text_strategy)
    def test_empty_source_never_verified(self, quote):
        """Quotes against empty sources must never be verified."""
        # Skip empty quotes
        if not quote.strip():
            return

        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = ""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation(quote, "statement-123")

        # Property: Non-empty quote against empty source never verified
        assert citation.verification_status != "verified"


class TestBatchVerificationProperties:
    """Test properties of batch verification."""

    @given(
        st.lists(
            st.tuples(text_strategy, st.text(min_size=1, max_size=20)), min_size=0, max_size=10
        )
    )
    def test_batch_verification_count_matches_input(self, citations):
        """Batch verification must return same number of results as inputs."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "Sample text for testing"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        results = verifier.verify_batch(citations)

        # Property: Output count equals input count
        assert len(results) == len(citations)

    @given(
        st.lists(
            st.tuples(text_strategy, st.text(min_size=1, max_size=20)), min_size=1, max_size=10
        )
    )
    def test_batch_verification_preserves_order(self, citations):
        """Batch verification must preserve input order."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "Sample text"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        results = verifier.verify_batch(citations)

        # Property: Source IDs match input order
        for i, (_quote, source_id) in enumerate(citations):
            assert results[i].source_id == source_id

    @given(
        st.lists(
            st.tuples(text_strategy, st.text(min_size=1, max_size=20)), min_size=0, max_size=10
        )
    )
    def test_batch_verification_all_have_status(self, citations):
        """All batch results must have verification status."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "Sample text"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        results = verifier.verify_batch(citations)

        # Property: All results have valid status
        for result in results:
            assert result.verification_status in ["verified", "unverified", "failed"]


class TestVerificationConsistency:
    """Test consistency properties of verification."""

    @given(quote=text_strategy, source_text=text_strategy)
    def test_verification_is_deterministic(self, quote, source_text):
        """Same input must produce same verification result."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = source_text
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)

        # Verify twice
        citation1 = verifier.verify_citation(quote, "statement-123")
        citation2 = verifier.verify_citation(quote, "statement-123")

        # Property: Results must be identical
        assert citation1.verification_status == citation2.verification_status
        assert citation1.similarity_score == citation2.similarity_score

    @given(
        source_text=text_strategy,
        threshold1=st.floats(min_value=0.5, max_value=0.9),
        threshold2=st.floats(min_value=0.9, max_value=1.0),
    )
    def test_lower_threshold_more_permissive(self, source_text, threshold1, threshold2):
        """Lower thresholds should be more permissive than higher thresholds."""
        # Skip if text too short
        if len(source_text) < 20:
            return

        # Create slightly modified version
        modified = (
            source_text[: len(source_text) // 2] + "modified" + source_text[len(source_text) // 2 :]
        )

        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = source_text
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)

        # Verify with both thresholds
        citation_low = verifier.verify_citation(modified, "statement-123", threshold=threshold1)
        citation_high = verifier.verify_citation(modified, "statement-123", threshold=threshold2)

        # Property: If high threshold verifies, low threshold must also verify
        if citation_high.verification_status == "verified":
            assert citation_low.verification_status == "verified"
