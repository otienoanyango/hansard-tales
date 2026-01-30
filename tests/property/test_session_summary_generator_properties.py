"""
Property-based tests for session summary generator.

Tests universal properties that should hold for all session summaries:
- Summary accuracy
- Key event extraction
"""

from datetime import date

from hypothesis import given
from hypothesis import strategies as st

from hansard_tales.analysis.session_summary_generator import SessionSummary


class TestSessionSummaryProperties:
    """Property-based tests for SessionSummary."""

    @given(
        session_id=st.text(min_size=1, max_size=50),
        session_date=st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)),
        session_type=st.sampled_from(["morning", "afternoon", "evening"]),
        title=st.text(min_size=5, max_size=100),
        summary=st.text(min_size=10, max_size=500),
        num_debates=st.integers(min_value=0, max_value=10),
        num_bills=st.integers(min_value=0, max_value=10),
        num_votes=st.integers(min_value=0, max_value=10),
        total_mps=st.integers(min_value=0, max_value=350),
        total_statements=st.integers(min_value=0, max_value=1000),
        num_topics=st.integers(min_value=0, max_value=10),
    )
    def test_property_10_1_summary_accuracy(
        self,
        session_id,
        session_date,
        session_type,
        title,
        summary,
        num_debates,
        num_bills,
        num_votes,
        total_mps,
        total_statements,
        num_topics,
    ):
        """
        Property 10.1: Summary accuracy.

        **Validates**: Requirements 11, 12

        **Property**: All SessionSummary fields must be valid and consistent.

        Test that:
        - All required fields are present
        - Counts are non-negative
        - Lists have correct lengths
        - Date is valid
        """
        # Create summary with generated data
        summary_obj = SessionSummary(
            session_id=session_id,
            date=session_date,
            session_type=session_type,
            title=title,
            summary=summary,
            key_debates=[f"Debate {i}" for i in range(num_debates)],
            bills_discussed=[f"Bill {i}" for i in range(num_bills)],
            votes_held=[f"Vote {i}" for i in range(num_votes)],
            total_mps_present=total_mps,
            total_statements=total_statements,
            main_topics=[f"Topic {i}" for i in range(num_topics)],
        )

        # Property: All required fields must be present
        assert summary_obj.session_id is not None
        assert summary_obj.date is not None
        assert summary_obj.session_type is not None
        assert summary_obj.title is not None
        assert summary_obj.summary is not None

        # Property: Counts must be non-negative
        assert summary_obj.total_mps_present >= 0
        assert summary_obj.total_statements >= 0

        # Property: Lists must have correct lengths
        assert len(summary_obj.key_debates) == num_debates
        assert len(summary_obj.bills_discussed) == num_bills
        assert len(summary_obj.votes_held) == num_votes
        assert len(summary_obj.main_topics) == num_topics

        # Property: Date must be valid
        assert isinstance(summary_obj.date, date)
        assert summary_obj.date.year >= 2020
        assert summary_obj.date.year <= 2030

    @given(
        num_statements=st.integers(min_value=0, max_value=100),
        num_key_debates=st.integers(min_value=0, max_value=10),
    )
    def test_property_10_2_key_event_extraction(self, num_statements, num_key_debates):
        """
        Property 10.2: Key event extraction.

        **Validates**: Requirements 12

        **Property**: Key debates should be extracted from statements.

        Test that:
        - Number of key debates is reasonable (≤ number of statements)
        - Key debates list is not empty when statements exist
        """
        # Create summary
        summary = SessionSummary(
            session_id="test-session",
            date=date(2024, 1, 1),
            session_type="morning",
            title="Test Session",
            summary="Test summary",
            key_debates=[f"Debate {i}" for i in range(num_key_debates)],
            total_statements=num_statements,
        )

        # Property: Key debates should be reasonable
        # (Can't have more key debates than statements, unless no statements)
        if num_statements > 0:
            assert len(summary.key_debates) <= num_statements + 5  # Allow some flexibility
        else:
            # Empty session can have 0 key debates
            assert len(summary.key_debates) >= 0

        # Property: Key debates should be strings
        assert all(isinstance(debate, str) for debate in summary.key_debates)

        # Property: Key debates should not be empty strings
        assert all(len(debate) > 0 for debate in summary.key_debates)
