"""
Property-based tests for MP profile generator.

Tests universal properties that must hold for all MP profiles:
- Profile completeness (all required fields populated)
- Statistics accuracy (aggregated values match raw data)
"""

from hypothesis import given
from hypothesis import strategies as st

from hansard_tales.analysis.mp_profile_generator import MPProfile


class TestMPProfileProperties:
    """Property-based tests for MPProfile dataclass."""

    @given(
        mp_id=st.text(min_size=1, max_size=50),
        name=st.text(min_size=1, max_size=200),
        constituency=st.text(min_size=0, max_size=200),
        party=st.text(min_size=0, max_size=100),
        total_statements=st.integers(min_value=0, max_value=10000),
        substantive_statements=st.integers(min_value=0, max_value=10000),
        avg_quality_score=st.floats(min_value=-100, max_value=200),
        votes_cast=st.integers(min_value=0, max_value=1000),
        votes_aye=st.integers(min_value=0, max_value=1000),
        votes_no=st.integers(min_value=0, max_value=1000),
        votes_abstain=st.integers(min_value=0, max_value=1000),
    )
    def test_profile_completeness(
        self,
        mp_id,
        name,
        constituency,
        party,
        total_statements,
        substantive_statements,
        avg_quality_score,
        votes_cast,
        votes_aye,
        votes_no,
        votes_abstain,
    ):
        """
        Property 9.1: Profile completeness.

        **Validates**: Requirements 1.16

        **Property**: All profile fields must be populated (no None for required fields).

        All MP profiles must have all required fields populated with valid values.
        Optional fields can be empty but must not be None.
        """
        profile = MPProfile(
            mp_id=mp_id,
            name=name,
            constituency=constituency,
            party=party,
            total_statements=total_statements,
            substantive_statements=substantive_statements,
            avg_quality_score=avg_quality_score,
            votes_cast=votes_cast,
            votes_aye=votes_aye,
            votes_no=votes_no,
            votes_abstain=votes_abstain,
        )

        # Required fields must not be None
        assert profile.mp_id is not None
        assert profile.name is not None
        assert profile.constituency is not None
        assert profile.party is not None

        # Numeric fields must be valid numbers
        assert isinstance(profile.total_statements, int)
        assert isinstance(profile.substantive_statements, int)
        assert isinstance(profile.avg_quality_score, float)
        assert isinstance(profile.votes_cast, int)
        assert isinstance(profile.votes_aye, int)
        assert isinstance(profile.votes_no, int)
        assert isinstance(profile.votes_abstain, int)

        # List fields must be lists (not None)
        assert isinstance(profile.top_topics, list)
        assert isinstance(profile.bills_sponsored, list)
        assert isinstance(profile.bills_discussed, list)
        assert isinstance(profile.key_positions, list)

        # Dict fields must be dicts (not None)
        assert isinstance(profile.sentiment_distribution, dict)
        assert isinstance(profile.metadata, dict)

        # String fields must be strings (not None)
        assert isinstance(profile.summary, str)
        assert isinstance(profile.avg_sentiment, str)

    @given(
        total_statements=st.integers(min_value=0, max_value=10000),
        substantive_statements=st.integers(min_value=0, max_value=10000),
    )
    def test_participation_rate_bounds(self, total_statements, substantive_statements):
        """
        Property: Participation rate must be between 0 and 100.

        The participation rate (percentage of substantive statements) must
        always be a valid percentage.
        """
        profile = MPProfile(
            mp_id="test",
            name="Test MP",
            constituency="Test",
            party="Test",
            total_statements=total_statements,
            substantive_statements=substantive_statements,
        )

        rate = profile.participation_rate
        assert 0.0 <= rate <= 100.0

    @given(
        votes_cast=st.integers(min_value=0, max_value=1000),
        votes_aye=st.integers(min_value=0, max_value=1000),
        votes_no=st.integers(min_value=0, max_value=1000),
        votes_abstain=st.integers(min_value=0, max_value=1000),
    )
    def test_voting_alignment_bounds(self, votes_cast, votes_aye, votes_no, votes_abstain):
        """
        Property: Voting alignment percentages must sum to 100 or all be 0.

        The voting alignment (aye, no, abstain percentages) must be valid
        percentages that sum to approximately 100% (or all 0 if no votes).
        """
        profile = MPProfile(
            mp_id="test",
            name="Test MP",
            constituency="Test",
            party="Test",
            votes_cast=votes_cast,
            votes_aye=votes_aye,
            votes_no=votes_no,
            votes_abstain=votes_abstain,
        )

        alignment = profile.voting_alignment
        assert 0.0 <= alignment["aye"] <= 100.0
        assert 0.0 <= alignment["no"] <= 100.0
        assert 0.0 <= alignment["abstain"] <= 100.0

        # Sum should be 100 or all 0
        total = alignment["aye"] + alignment["no"] + alignment["abstain"]
        if votes_cast > 0:
            # Allow small floating point error
            assert abs(total - 100.0) < 0.01 or total == 0.0
        else:
            assert total == 0.0

    @given(
        avg_quality_score=st.floats(
            min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False
        ),
    )
    def test_quality_score_normalization(self, avg_quality_score):
        """
        Property: Quality score must be normalized to 0-100 range.

        The post_init validation should ensure quality scores are always
        within the valid 0-100 range, even if invalid values are provided.
        """
        profile = MPProfile(
            mp_id="test",
            name="Test MP",
            constituency="Test",
            party="Test",
            avg_quality_score=avg_quality_score,
        )

        assert 0.0 <= profile.avg_quality_score <= 100.0

    @given(
        total_statements=st.integers(min_value=0, max_value=10000),
        substantive_statements=st.integers(min_value=0, max_value=10000),
    )
    def test_substantive_never_exceeds_total(self, total_statements, substantive_statements):
        """
        Property: Substantive statements cannot exceed total statements.

        The post_init validation should ensure substantive statements
        never exceed total statements.
        """
        profile = MPProfile(
            mp_id="test",
            name="Test MP",
            constituency="Test",
            party="Test",
            total_statements=total_statements,
            substantive_statements=substantive_statements,
        )

        assert profile.substantive_statements <= profile.total_statements

    @given(
        votes_cast=st.integers(min_value=-100, max_value=1000),
        votes_aye=st.integers(min_value=-100, max_value=1000),
        votes_no=st.integers(min_value=-100, max_value=1000),
        votes_abstain=st.integers(min_value=-100, max_value=1000),
    )
    def test_vote_counts_non_negative(self, votes_cast, votes_aye, votes_no, votes_abstain):
        """
        Property: Vote counts must be non-negative.

        The post_init validation should ensure all vote counts are
        non-negative, even if negative values are provided.
        """
        profile = MPProfile(
            mp_id="test",
            name="Test MP",
            constituency="Test",
            party="Test",
            votes_cast=votes_cast,
            votes_aye=votes_aye,
            votes_no=votes_no,
            votes_abstain=votes_abstain,
        )

        assert profile.votes_cast >= 0
        assert profile.votes_aye >= 0
        assert profile.votes_no >= 0
        assert profile.votes_abstain >= 0

    @given(
        mp_id=st.text(min_size=1, max_size=50),
        name=st.text(min_size=1, max_size=200),
        constituency=st.text(min_size=0, max_size=200),
        party=st.text(min_size=0, max_size=100),
    )
    def test_to_dict_completeness(self, mp_id, name, constituency, party):
        """
        Property: to_dict() must include all profile fields.

        The dictionary representation must include all profile fields
        including computed properties.
        """
        profile = MPProfile(mp_id=mp_id, name=name, constituency=constituency, party=party)

        data = profile.to_dict()

        # Check all required fields are present
        assert "mp_id" in data
        assert "name" in data
        assert "constituency" in data
        assert "party" in data
        assert "total_statements" in data
        assert "substantive_statements" in data
        assert "avg_quality_score" in data
        assert "votes_cast" in data
        assert "top_topics" in data
        assert "bills_sponsored" in data
        assert "bills_discussed" in data
        assert "summary" in data
        assert "participation_rate" in data
        assert "voting_alignment" in data
