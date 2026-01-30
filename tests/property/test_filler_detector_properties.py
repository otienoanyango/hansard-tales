"""
Property-based tests for FillerDetector.

Tests universal properties and invariants:
- Property 3.1: Filler detection precision ≥90%
- Property 3.2: No false negatives on substantive content
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hansard_tales.analysis.filler_detector import FillerDetector, StatementType
from hansard_tales.analysis.statement_segmenter import Statement


# Strategy for generating statements
@st.composite
def statement_strategy(draw):
    """Generate random Statement objects."""
    text = draw(st.text(min_size=0, max_size=500))
    mp_id = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    start_pos = draw(st.integers(min_value=0, max_value=1000))
    end_pos = draw(st.integers(min_value=start_pos, max_value=start_pos + 500))
    page_number = draw(st.one_of(st.none(), st.integers(min_value=1, max_value=100)))

    return Statement(
        text=text,
        mp_id=mp_id,
        start_pos=start_pos,
        end_pos=end_pos,
        page_number=page_number,
    )


class TestFillerDetectorProperties:
    """Property-based tests for FillerDetector."""

    @given(statement_strategy())
    def test_classify_never_crashes(self, statement):
        """
        Property: Classification should never crash.

        **Validates: Requirements 3.1, 3.2**

        The classify method should handle any input gracefully
        and always return a valid StatementType and confidence score.
        """
        detector = FillerDetector()
        try:
            stmt_type, confidence = detector.classify(statement)

            # Verify return types
            assert isinstance(stmt_type, StatementType)
            assert isinstance(confidence, float)
            assert 0.0 <= confidence <= 1.0

        except Exception as e:
            pytest.fail(f"classify() crashed with: {e}")

    @given(statement_strategy())
    def test_is_substantive_never_crashes(self, statement):
        """
        Property: is_substantive should never crash.

        **Validates: Requirements 3.1, 3.2**

        The is_substantive method should handle any input gracefully
        and always return a boolean.
        """
        detector = FillerDetector()
        try:
            result = detector.is_substantive(statement)
            assert isinstance(result, bool)
        except Exception as e:
            pytest.fail(f"is_substantive() crashed with: {e}")

    @given(statement_strategy())
    def test_confidence_in_valid_range(self, statement):
        """
        Property: Confidence scores must be in [0.0, 1.0].

        **Validates: Requirements 3.1**

        All confidence scores returned by classify must be
        valid probabilities between 0.0 and 1.0 inclusive.
        """
        detector = FillerDetector()
        stmt_type, confidence = detector.classify(statement)
        assert 0.0 <= confidence <= 1.0

    @given(statement_strategy())
    def test_classification_consistency(self, statement):
        """
        Property: Classification should be consistent.

        **Validates: Requirements 3.1**

        Calling classify multiple times on the same statement
        should return the same result.
        """
        detector = FillerDetector()
        result1 = detector.classify(statement)
        result2 = detector.classify(statement)
        assert result1 == result2

    @given(statement_strategy())
    def test_is_substantive_matches_classify(self, statement):
        """
        Property: is_substantive should match classify result.

        **Validates: Requirements 3.1, 3.2**

        The is_substantive helper should return True if and only if
        classify returns StatementType.SUBSTANTIVE.
        """
        detector = FillerDetector()
        stmt_type, _ = detector.classify(statement)
        is_subst = detector.is_substantive(statement)

        if stmt_type == StatementType.SUBSTANTIVE:
            assert is_subst is True
        else:
            assert is_subst is False

    @given(st.text(min_size=0, max_size=9))
    def test_very_short_text_classified_as_short_ack(self, text):
        """
        Property: Text < 10 chars should be SHORT_ACK.

        **Validates: Requirements 3.1**

        Any statement with text length < 10 characters should
        be classified as SHORT_ACK with confidence 1.0.
        """
        detector = FillerDetector()
        statement = Statement(text=text, mp_id="test", start_pos=0, end_pos=len(text))
        stmt_type, confidence = detector.classify(statement)

        assert stmt_type == StatementType.SHORT_ACK
        assert confidence == 1.0

    @given(st.text(min_size=100, max_size=500))
    def test_long_text_not_short_ack(self, text):
        """
        Property: Long text should not be SHORT_ACK by length.

        **Validates: Requirements 3.2**

        Statements with text length >= 100 characters should not
        be classified as SHORT_ACK based on length alone (though
        they could match a pattern).
        """
        detector = FillerDetector()
        statement = Statement(text=text, mp_id="test", start_pos=0, end_pos=len(text))
        stmt_type, confidence = detector.classify(statement)

        # If it's SHORT_ACK, it must be from pattern match (0.95), not length (1.0)
        if stmt_type == StatementType.SHORT_ACK:
            assert confidence == 0.95

    @given(st.text(min_size=50, max_size=500))
    def test_substantive_text_without_patterns(self, text):
        """
        Property: Text without filler patterns should be substantive.

        **Validates: Requirements 3.2**

        Long text that doesn't match any filler patterns should
        be classified as SUBSTANTIVE.
        """
        detector = FillerDetector()
        # Filter out text that starts with known patterns
        filler_starts = [
            "I beg to move",
            "I second",
            "Question put",
            "(Applause)",
            "(Laughter)",
            "The House rose",
            "Prayers",
            "ADJOURNMENT",
        ]

        if not any(text.strip().startswith(pattern) for pattern in filler_starts):
            statement = Statement(text=text, mp_id="test", start_pos=0, end_pos=len(text))
            stmt_type, confidence = detector.classify(statement)

            # Should be substantive if no patterns match
            assert stmt_type == StatementType.SUBSTANTIVE
            assert confidence == 0.90


class TestFillerDetectionPrecision:
    """
    Test Property 3.1: Filler detection precision ≥90%.

    **Validates: Requirements 3.4**

    This test validates that the filler detector achieves at least
    90% precision on a manually labeled test set.
    """

    @pytest.fixture
    def detector(self):
        """Create FillerDetector instance."""
        return FillerDetector()

    def test_filler_detection_precision(self, detector):
        """
        Property 3.1: Filler detection precision ≥90%.

        **Validates: Requirements 3.4**

        Test with manually labeled examples to ensure precision
        is at least 90%.
        """
        # Manually labeled test cases: (text, expected_type)
        test_cases = [
            # Procedural (should be detected as filler)
            ("I beg to move that this House adopts", StatementType.PROCEDURAL),
            ("I second the motion", StatementType.PROCEDURAL),
            ("Question put and agreed to", StatementType.PROCEDURAL),
            ("Motion made and Question proposed", StatementType.PROCEDURAL),
            ("I beg to lay the following papers", StatementType.PROCEDURAL),
            ("Point of order, Mr. Speaker", StatementType.PROCEDURAL),
            ("I rise on a point of order", StatementType.PROCEDURAL),
            # Interruptions (should be detected as filler)
            ("(Applause)", StatementType.INTERRUPTION),
            ("(Laughter)", StatementType.INTERRUPTION),
            ("(Interruptions)", StatementType.INTERRUPTION),
            ("(Loud consultations)", StatementType.INTERRUPTION),
            ("(Consultations)", StatementType.INTERRUPTION),
            # Administrative (should be detected as filler)
            ("The House rose at 6:30 p.m.", StatementType.ADMINISTRATIVE),
            ("ADJOURNMENT", StatementType.ADMINISTRATIVE),
            ("COMMUNICATION FROM THE CHAIR", StatementType.ADMINISTRATIVE),
            ("PAPERS LAID", StatementType.ADMINISTRATIVE),
            ("The House met at 2:30 p.m.", StatementType.ADMINISTRATIVE),
            ("Quorum bell was rung", StatementType.ADMINISTRATIVE),
            # Short acknowledgments (should be detected as filler)
            ("Yes", StatementType.SHORT_ACK),
            ("No", StatementType.SHORT_ACK),
            ("Thank you", StatementType.SHORT_ACK),
            ("I agree", StatementType.SHORT_ACK),
            ("Agreed", StatementType.SHORT_ACK),
            ("I support.", StatementType.SHORT_ACK),
            ("Hear! Hear!", StatementType.SHORT_ACK),
            # Substantive (should NOT be detected as filler)
            (
                "Mr. Speaker, I rise to address the healthcare funding issue",
                StatementType.SUBSTANTIVE,
            ),
            (
                "The proposed amendments will impact small businesses significantly",
                StatementType.SUBSTANTIVE,
            ),
            (
                "We must consider the economic implications before proceeding",
                StatementType.SUBSTANTIVE,
            ),
            (
                "The current allocation is insufficient for our growing population",
                StatementType.SUBSTANTIVE,
            ),
            (
                "This policy will create jobs and stimulate economic growth",
                StatementType.SUBSTANTIVE,
            ),
        ]

        correct = 0
        total = len(test_cases)

        for text, expected_type in test_cases:
            statement = Statement(text=text, mp_id="test", start_pos=0, end_pos=len(text))
            actual_type, _ = detector.classify(statement)

            if actual_type == expected_type:
                correct += 1

        precision = correct / total
        assert (
            precision >= 0.90
        ), f"Precision {precision:.2%} is below 90% threshold ({correct}/{total} correct)"


class TestNoFalseNegativesOnSubstantive:
    """
    Test Property 3.2: No false negatives on substantive content.

    **Validates: Requirements 3.5**

    This test validates that substantive statements are never
    incorrectly classified as filler.
    """

    @pytest.fixture
    def detector(self):
        """Create FillerDetector instance."""
        return FillerDetector()

    def test_no_false_negatives_on_substantive(self, detector):
        """
        Property 3.2: No false negatives on substantive content.

        **Validates: Requirements 3.5**

        Substantive statements should never be classified as filler.
        This is critical to avoid losing important content.
        """
        # Known substantive statements (manually verified)
        substantive_statements = [
            "Mr. Speaker, I rise to address the issue of healthcare funding in our constituency.",
            "The proposed amendments to the Finance Bill will have significant implications.",
            "We must consider the impact on job creation and economic growth.",
            "The current allocation is insufficient to meet the needs of our population.",
            "This policy will create thousands of jobs across the country.",
            "I want to discuss the education sector and the challenges we face.",
            "The infrastructure development in rural areas requires immediate attention.",
            "We need to address the rising cost of living affecting our citizens.",
            "The agricultural sector needs more support from the government.",
            "Security concerns in the region must be addressed urgently.",
        ]

        false_negatives = 0
        total = len(substantive_statements)

        for text in substantive_statements:
            statement = Statement(text=text, mp_id="test", start_pos=0, end_pos=len(text))
            stmt_type, _ = detector.classify(statement)

            if stmt_type != StatementType.SUBSTANTIVE:
                false_negatives += 1
                print(f"False negative: '{text}' classified as {stmt_type}")

        # We want ZERO false negatives on substantive content
        assert (
            false_negatives == 0
        ), f"Found {false_negatives}/{total} false negatives on substantive content"

    @given(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po"),
                blacklist_characters="()",
            ),
            min_size=50,
            max_size=200,
        )
    )
    def test_long_text_without_parentheses_is_substantive(self, text):
        """
        Property: Long text without special patterns should be substantive.

        **Validates: Requirements 3.5**

        Long statements (50+ chars) without parentheses or procedural
        patterns should be classified as substantive.
        """
        detector = FillerDetector()
        # Skip if text starts with known procedural patterns
        procedural_starts = [
            "I beg to move",
            "I second",
            "Question put",
            "The House rose",
            "The House met",
            "ADJOURNMENT",
            "COMMUNICATION",
            "PAPERS LAID",
        ]

        text_stripped = text.strip()
        if len(text_stripped) >= 50 and not any(
            text_stripped.startswith(p) for p in procedural_starts
        ):
            statement = Statement(text=text, mp_id="test", start_pos=0, end_pos=len(text))
            stmt_type, _ = detector.classify(statement)

            # Should be substantive
            assert (
                stmt_type == StatementType.SUBSTANTIVE
            ), f"Long text incorrectly classified as {stmt_type}: {text[:50]}..."
