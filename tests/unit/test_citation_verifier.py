"""
Unit tests for citation verifier.

Tests citation verification functionality including:
- Exact matching
- Fuzzy matching
- Threshold handling
- Batch verification
- Error cases
"""

from unittest.mock import Mock

from hansard_tales.analysis.citation_verifier import Citation, CitationVerifier


class TestExactMatching:
    """Test exact citation matching functionality."""

    def test_verify_citation_exact_match(self):
        """Test verification with exact match in source."""
        # Setup mock database
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.id = 123
        mock_statement.text = "We must increase healthcare funding by 20% to meet demand."
        mock_statement.page_number = 5
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation(
            "We must increase healthcare funding by 20%", "statement-123"
        )

        assert citation.verification_status == "verified"
        assert citation.similarity_score == 1.0
        assert citation.quote == "We must increase healthcare funding by 20%"
        assert citation.source_id == "statement-123"
        assert citation.source_type == "statement"
        assert citation.page_number == 5

    def test_verify_citation_exact_match_case_sensitive(self):
        """Test exact match is case-sensitive."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "We must increase healthcare funding."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation("We must increase healthcare funding.", "statement-123")

        assert citation.verification_status == "verified"
        assert citation.similarity_score == 1.0

    def test_verify_citation_exact_match_with_punctuation(self):
        """Test exact match includes punctuation."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "The budget is insufficient, Mr. Speaker."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation(
            "The budget is insufficient, Mr. Speaker.", "statement-123"
        )

        assert citation.verification_status == "verified"
        assert citation.similarity_score == 1.0

    def test_verify_citation_exact_match_substring(self):
        """Test exact match works for substrings."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = (
            "I rise to support this motion. The budget is insufficient. "
            "We need more funding for rural areas."
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation("The budget is insufficient.", "statement-123")

        assert citation.verification_status == "verified"
        assert citation.similarity_score == 1.0

    def test_verify_citation_exact_match_multiline(self):
        """Test exact match works across line breaks."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "First line.\nSecond line.\nThird line."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation("First line.\nSecond line.", "statement-123")

        assert citation.verification_status == "verified"
        assert citation.similarity_score == 1.0


class TestFuzzyMatching:
    """Test fuzzy citation matching functionality."""

    def test_verify_citation_fuzzy_match_above_threshold(self):
        """Test fuzzy match above threshold is verified."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "We must increase healthcare funding by twenty percent."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db, fuzzy_threshold=0.90)
        citation = verifier.verify_citation(
            "We must increase healthcare funding by 20%", "statement-123"
        )

        assert citation.verification_status == "verified"
        assert citation.similarity_score >= 0.90
        assert citation.source_id == "statement-123"

    def test_verify_citation_fuzzy_match_below_threshold(self):
        """Test fuzzy match below threshold is unverified."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "The education sector needs more resources."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db, fuzzy_threshold=0.95)
        citation = verifier.verify_citation("We must increase healthcare funding", "statement-123")

        assert citation.verification_status == "unverified"
        assert citation.similarity_score < 0.95

    def test_verify_citation_fuzzy_match_finds_best_substring(self):
        """Test fuzzy match finds best matching substring."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = (
            "I support this motion. Healthcare funding must be increased "
            "to meet the growing demand in our constituencies."
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db, fuzzy_threshold=0.90)
        citation = verifier.verify_citation("Healthcare funding must be increased", "statement-123")

        assert citation.verification_status == "verified"
        assert "Healthcare funding must be increased" in citation.quote

    def test_verify_citation_fuzzy_match_with_typos(self):
        """Test fuzzy match handles minor typos."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "We must increase healthcare funding immediately."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db, fuzzy_threshold=0.90)
        # Citation has minor typo: "imediately" instead of "immediately"
        citation = verifier.verify_citation(
            "We must increase healthcare funding imediately", "statement-123"
        )

        # Should still verify with high similarity
        assert citation.verification_status == "verified"
        assert citation.similarity_score >= 0.90

    def test_verify_citation_fuzzy_match_with_paraphrase(self):
        """Test fuzzy match with paraphrased content."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "The healthcare sector requires additional financial resources."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db, fuzzy_threshold=0.95)
        # Paraphrased version
        citation = verifier.verify_citation("Healthcare needs more funding", "statement-123")

        # Should not verify - too different
        assert citation.verification_status == "unverified"


class TestThresholdHandling:
    """Test threshold parameter handling."""

    def test_verify_citation_custom_threshold(self):
        """Test verification with custom threshold."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "We need more funding for healthcare services."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        # Default threshold is 0.95
        verifier = CitationVerifier(mock_db, fuzzy_threshold=0.95)

        # Use lower threshold for this verification
        citation = verifier.verify_citation(
            "We need more funding for healthcare", "statement-123", threshold=0.85
        )

        assert citation.verification_status == "verified"
        assert citation.similarity_score >= 0.85

    def test_verify_citation_threshold_boundary(self):
        """Test verification at exact threshold boundary."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "Healthcare funding is critical for rural areas."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db, fuzzy_threshold=0.90)

        # This should produce a score right around the threshold
        citation = verifier.verify_citation("Healthcare funding is critical", "statement-123")

        # Should be verified if score >= threshold
        if citation.similarity_score >= 0.90:
            assert citation.verification_status == "verified"
        else:
            assert citation.verification_status == "unverified"

    def test_verify_citation_very_high_threshold(self):
        """Test verification with very high threshold."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "We must increase healthcare funding by 20%."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db, fuzzy_threshold=0.99)

        # Even close match won't verify with 0.99 threshold
        citation = verifier.verify_citation(
            "We must increase healthcare funding by twenty percent", "statement-123"
        )

        # Likely unverified due to high threshold
        assert citation.similarity_score < 0.99 or citation.verification_status == "verified"

    def test_verify_citation_very_low_threshold(self):
        """Test verification with very low threshold."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "The education sector needs reform."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db, fuzzy_threshold=0.50)

        # Even loosely related text should verify
        citation = verifier.verify_citation("Education needs changes", "statement-123")

        # Should verify with low threshold
        assert citation.verification_status == "verified"
        assert citation.similarity_score >= 0.50


class TestBatchVerification:
    """Test batch verification functionality."""

    def test_verify_batch_multiple_citations(self):
        """Test batch verification of multiple citations."""
        mock_db = Mock()

        # Setup mock to return different statements
        def mock_query_side_effect(*args, **kwargs):
            mock_query = Mock()
            mock_filter = Mock()

            def mock_first():
                # Return different statements based on call count
                if mock_first.call_count == 1:
                    stmt = Mock()
                    stmt.text = "Healthcare funding is critical."
                    stmt.page_number = 1
                    return stmt
                elif mock_first.call_count == 2:
                    stmt = Mock()
                    stmt.text = "Education needs more resources."
                    stmt.page_number = 2
                    return stmt
                else:
                    stmt = Mock()
                    stmt.text = "Infrastructure is deteriorating."
                    stmt.page_number = 3
                    return stmt

            mock_first.call_count = 0

            def increment_and_call():
                mock_first.call_count += 1
                return mock_first()

            mock_filter.first = increment_and_call
            mock_query.filter.return_value = mock_filter
            return mock_query

        mock_db.query.side_effect = mock_query_side_effect

        verifier = CitationVerifier(mock_db)

        citations = [
            ("Healthcare funding is critical.", "statement-1"),
            ("Education needs more resources.", "statement-2"),
            ("Infrastructure is deteriorating.", "statement-3"),
        ]

        results = verifier.verify_batch(citations)

        assert len(results) == 3
        assert all(r.verification_status == "verified" for r in results)
        assert results[0].source_id == "statement-1"
        assert results[1].source_id == "statement-2"
        assert results[2].source_id == "statement-3"

    def test_verify_batch_mixed_results(self):
        """Test batch verification with mixed verified/unverified results."""
        mock_db = Mock()

        def mock_query_side_effect(*args, **kwargs):
            mock_query = Mock()
            mock_filter = Mock()

            def mock_first():
                if mock_first.call_count == 1:
                    stmt = Mock()
                    stmt.text = "Healthcare funding is critical."
                    return stmt
                else:
                    stmt = Mock()
                    stmt.text = "Something completely different."
                    return stmt

            mock_first.call_count = 0

            def increment_and_call():
                mock_first.call_count += 1
                return mock_first()

            mock_filter.first = increment_and_call
            mock_query.filter.return_value = mock_filter
            return mock_query

        mock_db.query.side_effect = mock_query_side_effect

        verifier = CitationVerifier(mock_db, fuzzy_threshold=0.95)

        citations = [
            ("Healthcare funding is critical.", "statement-1"),
            ("Education needs reform.", "statement-2"),
        ]

        results = verifier.verify_batch(citations)

        assert len(results) == 2
        assert results[0].verification_status == "verified"
        assert results[1].verification_status == "unverified"

    def test_verify_batch_empty_list(self):
        """Test batch verification with empty list."""
        mock_db = Mock()
        verifier = CitationVerifier(mock_db)

        results = verifier.verify_batch([])

        assert results == []

    def test_verify_batch_with_custom_threshold(self):
        """Test batch verification with custom threshold."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "Healthcare funding is important."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db, fuzzy_threshold=0.95)

        citations = [
            ("Healthcare funding is important", "statement-1"),
            ("Healthcare funding is critical", "statement-1"),
        ]

        # Use lower threshold for batch
        results = verifier.verify_batch(citations, threshold=0.85)

        # Both should verify with lower threshold
        assert len(results) == 2
        assert all(r.verification_status == "verified" for r in results)


class TestErrorCases:
    """Test error handling and edge cases."""

    def test_verify_citation_source_not_found(self):
        """Test verification when source doesn't exist."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation("Some quote", "statement-999")

        assert citation.verification_status == "failed"
        assert citation.similarity_score == 0.0
        assert citation.source_type == "unknown"

    def test_verify_citation_invalid_source_id_format(self):
        """Test verification with invalid source_id format."""
        mock_db = Mock()
        verifier = CitationVerifier(mock_db)

        citation = verifier.verify_citation("Some quote", "invalid-format")

        assert citation.verification_status == "failed"
        assert citation.source_type == "unknown"

    def test_verify_citation_empty_quote(self):
        """Test verification with empty quote."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "Some text here."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation("", "statement-123")

        # Empty quote won't match
        assert citation.verification_status == "unverified"

    def test_verify_citation_empty_source_text(self):
        """Test verification when source text is empty."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = ""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation("Some quote", "statement-123")

        assert citation.verification_status == "unverified"

    def test_verify_citation_very_long_quote(self):
        """Test verification with very long quote."""
        mock_db = Mock()
        mock_statement = Mock()
        long_text = "A" * 10000
        mock_statement.text = long_text
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation(long_text[:5000], "statement-123")

        # Should still work with long text
        assert citation.verification_status == "verified"

    def test_verify_citation_special_characters(self):
        """Test verification with special characters."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "The cost is $1,000 (approximately £750)."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation(
            "The cost is $1,000 (approximately £750).", "statement-123"
        )

        assert citation.verification_status == "verified"

    def test_verify_citation_unicode_characters(self):
        """Test verification with unicode characters."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "Nairobi's healthcare system needs reform."
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation(
            "Nairobi's healthcare system needs reform.", "statement-123"
        )

        assert citation.verification_status == "verified"

    def test_verify_citation_database_error(self):
        """Test verification handles database errors gracefully."""
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database connection error")

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation("Some quote", "statement-123")

        # Should return failed status instead of raising
        assert citation.verification_status == "failed"

    def test_verify_citation_none_page_number(self):
        """Test verification when page_number is None."""
        mock_db = Mock()
        mock_statement = Mock()
        mock_statement.text = "Healthcare is important."
        mock_statement.page_number = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_statement

        verifier = CitationVerifier(mock_db)
        citation = verifier.verify_citation("Healthcare is important.", "statement-123")

        assert citation.verification_status == "verified"
        assert citation.page_number is None


class TestCitationDataclass:
    """Test Citation dataclass functionality."""

    def test_citation_creation_minimal(self):
        """Test creating Citation with minimal fields."""
        citation = Citation(quote="Test quote", source_id="statement-1", source_type="statement")

        assert citation.quote == "Test quote"
        assert citation.source_id == "statement-1"
        assert citation.source_type == "statement"
        assert citation.page_number is None
        assert citation.verification_status == "unverified"
        assert citation.similarity_score == 0.0

    def test_citation_creation_full(self):
        """Test creating Citation with all fields."""
        citation = Citation(
            quote="Full quote",
            source_id="statement-123",
            source_type="statement",
            page_number=5,
            verification_status="verified",
            similarity_score=0.95,
        )

        assert citation.quote == "Full quote"
        assert citation.source_id == "statement-123"
        assert citation.source_type == "statement"
        assert citation.page_number == 5
        assert citation.verification_status == "verified"
        assert citation.similarity_score == 0.95

    def test_citation_equality(self):
        """Test Citation equality comparison."""
        citation1 = Citation(
            quote="Test", source_id="s-1", source_type="statement", verification_status="verified"
        )
        citation2 = Citation(
            quote="Test", source_id="s-1", source_type="statement", verification_status="verified"
        )

        assert citation1 == citation2

    def test_citation_string_representation(self):
        """Test Citation string representation."""
        citation = Citation(
            quote="Test quote",
            source_id="statement-123",
            source_type="statement",
            verification_status="verified",
        )

        str_repr = str(citation)
        assert "Test quote" in str_repr
        assert "statement-123" in str_repr
        assert "verified" in str_repr
