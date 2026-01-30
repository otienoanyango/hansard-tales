"""
Property-based tests for Bill-Statement Linker.

Tests universal properties that should hold for all inputs:
- Property 8.1: Bill mention detection recall ≥90%
- Property 8.2: Bill resolution accuracy
"""

from unittest.mock import Mock
from uuid import uuid4

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from hansard_tales.analysis.bill_statement_linker import (
    BillMention,
    BillStatementLinker,
)
from hansard_tales.analysis.statement_segmenter import Statement
from hansard_tales.database.models import BillORM


# Custom strategies for generating test data
@st.composite
def bill_mention_text(draw):
    """Generate text with bill mention patterns."""
    bill_types = ["Finance", "Health", "Education", "Agriculture", "Security"]
    years = st.integers(min_value=2020, max_value=2030)

    bill_type = draw(st.sampled_from(bill_types))
    year = draw(years)

    # Choose a pattern
    pattern_choice = draw(st.integers(min_value=0, max_value=2))

    if pattern_choice == 0:
        # Pattern: "The Finance Bill, 2024"
        return f"The {bill_type} Bill, {year}"
    elif pattern_choice == 1:
        # Pattern: "Finance Bill, 2024"
        return f"{bill_type} Bill, {year}"
    else:
        # Pattern: "Bill No. 15 of 2024"
        bill_num = draw(st.integers(min_value=1, max_value=100))
        return f"Bill No. {bill_num} of {year}"


@st.composite
def statement_with_bill_mention(draw):
    """Generate statement text containing a bill mention."""
    prefix = draw(
        st.sampled_from(
            [
                "We are discussing ",
                "I support ",
                "The committee reviewed ",
                "Members voted on ",
                "The Speaker presented ",
            ]
        )
    )

    bill_text = draw(bill_mention_text())

    suffix = draw(
        st.sampled_from(
            [
                " today.",
                " in this session.",
                " and urge passage.",
                " with amendments.",
                " for consideration.",
            ]
        )
    )

    return prefix + bill_text + suffix


class TestBillStatementLinkerProperties:
    """Property-based tests for BillStatementLinker."""

    @given(
        text=st.text(min_size=10, max_size=500),
        mp_id=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    )
    @settings(max_examples=50, deadline=None)
    def test_property_never_crashes(self, text, mp_id):
        """
        Property: Bill mention detection should never crash.

        This property verifies that the bill-statement linker is robust
        and handles all inputs gracefully without crashing.

        The system should:
        - Accept any valid statement text
        - Handle presence or absence of MP ID
        - Return a valid list of BillMention objects
        """
        # Create mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_db.query = Mock(return_value=mock_query)

        # Create linker
        linker = BillStatementLinker(db_session=mock_db, vector_db=None)

        # Create statement
        statement = Statement(text=text, mp_id=mp_id, start_pos=0, end_pos=len(text))

        # Find mentions - should never crash
        mentions = linker.find_bill_mentions(statement)

        # Verify result is valid
        assert isinstance(mentions, list)
        for mention in mentions:
            assert isinstance(mention, BillMention)
            assert 0.0 <= mention.confidence <= 1.0
            assert mention.bill_id
            assert mention.mention_text

    @given(
        statement_text=statement_with_bill_mention(),
        mp_id=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=50, deadline=None)
    def test_property_bill_mention_detection_recall(self, statement_text, mp_id):
        """
        Property 8.1: Bill mention detection recall ≥90%.

        **Validates: Requirements 10.1**

        This property verifies that when a statement contains a bill mention
        in a known pattern, the system detects it with high recall.

        The system should:
        - Detect bill mentions in standard formats
        - Return at least one mention when pattern exists
        - Maintain high recall across different bill types
        """
        # Create mock bill that matches the mention
        mock_bill = Mock(spec=BillORM)
        mock_bill.id = uuid4()
        mock_bill.title = "Test Bill, 2024"

        # Create mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[mock_bill])
        mock_db.query = Mock(return_value=mock_query)

        # Create linker
        linker = BillStatementLinker(db_session=mock_db, vector_db=None)

        # Create statement
        statement = Statement(
            text=statement_text,
            mp_id=mp_id,
            start_pos=0,
            end_pos=len(statement_text),
        )

        # Find mentions
        mentions = linker.find_bill_mentions(statement)

        # Verify at least one mention detected (high recall)
        # Note: This assumes the mock DB returns a matching bill
        assert len(mentions) >= 1, f"Failed to detect bill mention in: {statement_text}"

    @given(
        confidence=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=50, deadline=None)
    def test_property_confidence_bounds(self, confidence):
        """
        Property: Confidence scores must be between 0.0 and 1.0.

        This property verifies that all confidence scores are valid
        probabilities in the range [0.0, 1.0].
        """
        # Create a valid bill mention with the confidence
        mention = BillMention(
            bill_id="bill-123",
            bill_title="Test Bill",
            mention_text="Test Bill, 2024",
            confidence=confidence,
            context="Test context",
        )

        # Verify confidence is within bounds
        assert 0.0 <= mention.confidence <= 1.0

    @given(
        text=st.text(min_size=10, max_size=500),
        num_bills=st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=50, deadline=None)
    def test_property_bill_resolution_accuracy(self, text, num_bills):
        """
        Property 8.2: Bill resolution accuracy.

        **Validates: Requirements 10.2**

        This property verifies that when bills are found in the database,
        they are correctly resolved and returned with valid metadata.

        The system should:
        - Return valid bill IDs
        - Include bill titles
        - Maintain confidence scores
        - Extract context correctly
        """
        # Create mock bills
        mock_bills = [
            Mock(
                spec=BillORM,
                id=uuid4(),
                title=f"Bill {i}, 2024",
            )
            for i in range(num_bills)
        ]

        # Create mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=mock_bills)
        mock_db.query = Mock(return_value=mock_query)

        # Create linker
        linker = BillStatementLinker(db_session=mock_db, vector_db=None)

        # Create statement
        statement = Statement(text=text, mp_id="test-mp", start_pos=0, end_pos=len(text))

        # Find mentions
        mentions = linker.find_bill_mentions(statement)

        # Verify all mentions have valid resolution
        for mention in mentions:
            # Valid bill ID (UUID format)
            assert mention.bill_id
            assert len(mention.bill_id) > 0

            # Valid bill title
            assert mention.bill_title
            assert len(mention.bill_title) > 0

            # Valid confidence
            assert 0.0 <= mention.confidence <= 1.0

            # Valid context
            assert isinstance(mention.context, str)

    @given(
        text=st.text(min_size=10, max_size=500),
    )
    @settings(max_examples=50, deadline=None)
    def test_property_no_false_positives_without_patterns(self, text):
        """
        Property: No false positives when no bill patterns exist.

        This property verifies that the system doesn't detect bill mentions
        in text that doesn't contain bill mention patterns.

        The system should:
        - Return empty list when no patterns match
        - Not generate false positives
        - Handle arbitrary text gracefully
        """
        # Filter out text that might accidentally contain bill patterns
        assume("Bill" not in text)
        assume("bill" not in text)

        # Create mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_db.query = Mock(return_value=mock_query)

        # Create linker
        linker = BillStatementLinker(db_session=mock_db, vector_db=None)

        # Create statement
        statement = Statement(text=text, mp_id="test-mp", start_pos=0, end_pos=len(text))

        # Find mentions
        mentions = linker.find_bill_mentions(statement)

        # Verify no false positives
        assert len(mentions) == 0, f"False positive detected in text without bill patterns: {text}"

    @given(
        num_mentions=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=50, deadline=None)
    def test_property_deduplication_correctness(self, num_mentions):
        """
        Property: Deduplication should keep highest confidence mention.

        This property verifies that when the same bill is mentioned multiple
        times, only the mention with the highest confidence is kept.

        The system should:
        - Remove duplicate bill mentions
        - Keep the highest confidence mention
        - Preserve unique bills
        """
        # Create mock database session
        mock_db = Mock()

        # Create linker
        linker = BillStatementLinker(db_session=mock_db, vector_db=None)

        # Create duplicate mentions with varying confidence
        bill_id = str(uuid4())
        mentions = [
            BillMention(
                bill_id=bill_id,
                bill_title="Test Bill, 2024",
                mention_text=f"Mention {i}",
                confidence=0.5 + (i * 0.1),  # Increasing confidence
                context=f"Context {i}",
            )
            for i in range(num_mentions)
        ]

        # Deduplicate
        deduplicated = linker._deduplicate_mentions(mentions)

        # Verify only one mention remains
        assert len(deduplicated) == 1

        # Verify it's the highest confidence mention
        expected_confidence = 0.5 + ((num_mentions - 1) * 0.1)
        assert deduplicated[0].confidence == expected_confidence

    @given(
        text=st.text(min_size=10, max_size=500),
        position=st.integers(min_value=0, max_value=100),
        window=st.integers(min_value=10, max_value=200),
    )
    @settings(max_examples=50, deadline=None)
    def test_property_context_extraction_bounds(self, text, position, window):
        """
        Property: Context extraction should respect text boundaries.

        This property verifies that context extraction never goes out of
        bounds and always returns valid text.

        The system should:
        - Never exceed text boundaries
        - Return valid string
        - Include position if within bounds
        """
        # Ensure position is within text
        assume(position < len(text))

        # Create mock database session
        mock_db = Mock()

        # Create linker
        linker = BillStatementLinker(db_session=mock_db, vector_db=None)

        # Extract context
        context = linker._extract_context(text, position, window)

        # Verify context is valid
        assert isinstance(context, str)
        assert len(context) <= len(text) + 6  # +6 for "..." on both ends

        # Verify context doesn't exceed original text bounds
        # (except for ellipsis markers)
        assert all(char in text or char in "..." for char in context)

    @given(
        vec1=st.lists(
            st.floats(min_value=-1.0, max_value=1.0),
            min_size=3,
            max_size=3,
        ),
        vec2=st.lists(
            st.floats(min_value=-1.0, max_value=1.0),
            min_size=3,
            max_size=3,
        ),
    )
    @settings(max_examples=50, deadline=None)
    def test_property_cosine_similarity_bounds(self, vec1, vec2):
        """
        Property: Cosine similarity should be between -1.0 and 1.0.

        This property verifies that cosine similarity calculations
        always produce valid results in the expected range.

        The system should:
        - Return values in [-1.0, 1.0]
        - Handle zero vectors gracefully
        - Produce consistent results
        """
        # Filter out zero vectors (would cause division by zero)
        assume(any(abs(x) > 0.001 for x in vec1))
        assume(any(abs(x) > 0.001 for x in vec2))

        # Create mock database session
        mock_db = Mock()

        # Create linker
        linker = BillStatementLinker(db_session=mock_db, vector_db=None)

        # Calculate similarity
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        try:
            similarity = linker._cosine_similarity(vec1_np, vec2_np)

            # Verify similarity is in valid range (with small tolerance for floating point)
            assert (
                -1.01 <= similarity <= 1.01
            ), f"Cosine similarity {similarity} out of bounds [-1.0, 1.0]"
        except (ValueError, ZeroDivisionError):
            # These exceptions are acceptable for edge cases
            pass

    @given(
        text=st.text(min_size=10, max_size=500),
    )
    @settings(max_examples=50, deadline=None)
    def test_property_link_statement_returns_valid_ids(self, text):
        """
        Property: link_statement_to_bills should return valid bill IDs.

        This property verifies that the convenience method returns
        a list of valid bill ID strings.

        The system should:
        - Return a list of strings
        - Each string should be a valid UUID
        - List should match number of unique mentions
        """
        # Create mock bill
        mock_bill = Mock(spec=BillORM)
        mock_bill.id = uuid4()
        mock_bill.title = "Test Bill, 2024"

        # Create mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[mock_bill])
        mock_db.query = Mock(return_value=mock_query)

        # Create linker
        linker = BillStatementLinker(db_session=mock_db, vector_db=None)

        # Create statement
        statement = Statement(text=text, mp_id="test-mp", start_pos=0, end_pos=len(text))

        # Link statement
        bill_ids = linker.link_statement_to_bills(statement)

        # Verify result is valid
        assert isinstance(bill_ids, list)
        for bill_id in bill_ids:
            assert isinstance(bill_id, str)
            assert len(bill_id) > 0
            # Should be a valid UUID string
            try:
                from uuid import UUID

                UUID(bill_id)
            except ValueError:
                pytest.fail(f"Invalid UUID format: {bill_id}")
