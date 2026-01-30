"""
Property-based tests for VoteProcessor.

Tests universal properties and invariants:
- Property 7.1: Vote extraction completeness
- Property 7.2: MP vote accuracy
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hansard_tales.analysis.mp_identifier import MPMatch
from hansard_tales.processors.vote_processor import (
    MPVote,
    VoteProcessor,
    VoteRecord,
)

# Strategy for generating vote values
vote_values = st.sampled_from(["aye", "no", "abstain", "absent"])


# Strategy for generating MP votes
@st.composite
def mp_vote_strategy(draw):
    """Generate random MPVote objects."""
    mp_id = draw(st.text(min_size=1, max_size=50))
    vote = draw(vote_values)
    return MPVote(mp_id=mp_id, vote=vote)


# Strategy for generating vote tables
@st.composite
def vote_table_strategy(draw):
    """Generate random vote tables."""
    # Header row
    headers = draw(
        st.lists(
            st.sampled_from(["MP Name", "Vote", "Constituency", "Ayes", "Noes"]),
            min_size=2,
            max_size=5,
            unique=True,
        )
    )

    # Data rows
    num_rows = draw(st.integers(min_value=0, max_value=20))
    rows = []
    for _ in range(num_rows):
        row = []
        for _ in range(len(headers)):
            cell = draw(st.one_of(st.none(), st.text(min_size=0, max_size=50)))
            row.append(cell)
        rows.append(row)

    return [headers] + rows


class TestVoteProcessorProperties:
    """Property-based tests for VoteProcessor."""

    @given(st.text(min_size=0, max_size=100))
    def test_parse_vote_value_never_crashes(self, vote_text):
        """
        Property: Vote value parsing should never crash.

        **Validates: Requirements 9.1**

        The _parse_vote_value method should handle any input gracefully
        and always return a valid vote value.
        """
        # Create processor inside test
        mock_db_session = Mock()
        mock_mp_identifier = Mock()
        processor = VoteProcessor(mock_db_session, mock_mp_identifier)

        try:
            result = processor._parse_vote_value(vote_text)
            assert result in ["aye", "no", "abstain", "absent"]
        except Exception as e:
            pytest.fail(f"_parse_vote_value() crashed with: {e}")

    @given(st.text(min_size=0, max_size=100))
    def test_parse_vote_value_consistency(self, vote_text):
        """
        Property: Vote value parsing should be consistent.

        **Validates: Requirements 9.1**

        Calling _parse_vote_value multiple times on the same input
        should return the same result.
        """
        # Create processor inside test
        mock_db_session = Mock()
        mock_mp_identifier = Mock()
        processor = VoteProcessor(mock_db_session, mock_mp_identifier)

        result1 = processor._parse_vote_value(vote_text)
        result2 = processor._parse_vote_value(vote_text)
        assert result1 == result2

    @given(vote_table_strategy())
    def test_is_vote_table_never_crashes(self, table):
        """
        Property: Vote table detection should never crash.

        **Validates: Requirements 9.1**

        The _is_vote_table method should handle any table structure
        gracefully and always return a boolean.
        """
        # Create processor inside test
        mock_db_session = Mock()
        mock_mp_identifier = Mock()
        processor = VoteProcessor(mock_db_session, mock_mp_identifier)

        try:
            result = processor._is_vote_table(table)
            assert isinstance(result, bool)
        except Exception as e:
            pytest.fail(f"_is_vote_table() crashed with: {e}")

    @given(vote_table_strategy())
    def test_parse_vote_table_never_crashes(self, table):
        """
        Property: Vote table parsing should never crash.

        **Validates: Requirements 9.1**

        The _parse_vote_table method should handle any table structure
        gracefully and return either a VoteRecord or None.
        """
        # Create processor inside test
        mock_db_session = Mock()
        mock_mp_identifier = Mock()
        processor = VoteProcessor(mock_db_session, mock_mp_identifier)

        try:
            result = processor._parse_vote_table(table)
            assert result is None or isinstance(result, VoteRecord)
        except Exception as e:
            pytest.fail(f"_parse_vote_table() crashed with: {e}")

    @given(st.lists(mp_vote_strategy(), min_size=0, max_size=50))
    def test_vote_totals_accuracy(self, mp_votes):
        """
        Property: Vote totals must match individual votes.

        **Validates: Requirements 9.2**

        The sum of ayes, noes, and abstentions should equal
        the total number of MP votes (excluding absent).
        """
        # Create processor inside test
        mock_db_session = Mock()
        mock_mp_identifier = Mock()
        processor = VoteProcessor(mock_db_session, mock_mp_identifier)

        # Count votes manually
        expected_ayes = sum(1 for v in mp_votes if v.vote == "aye")
        expected_noes = sum(1 for v in mp_votes if v.vote == "no")
        expected_abstentions = sum(1 for v in mp_votes if v.vote == "abstain")

        # Create a mock table
        table = [["MP Name", "Vote"]]
        for i, vote in enumerate(mp_votes):
            table.append([f"MP {i}", vote.vote])

        # Mock MP identifier to return different MPs
        mock_mp_identifier.identify = Mock(
            side_effect=[
                MPMatch(mp_id=f"mp-{i}", name=f"MP {i}", confidence=0.95)
                for i in range(len(mp_votes))
            ]
        )

        result = processor._parse_vote_table(table)

        if result:
            assert result.ayes == expected_ayes
            assert result.noes == expected_noes
            assert result.abstentions == expected_abstentions

    @given(st.lists(mp_vote_strategy(), min_size=1, max_size=50))
    def test_vote_result_determination(self, mp_votes):
        """
        Property: Vote result should match vote counts.

        **Validates: Requirements 9.2**

        If ayes > noes, result should be "passed".
        If noes >= ayes, result should be "failed".
        """
        # Create processor inside test
        mock_db_session = Mock()
        mock_mp_identifier = Mock()
        processor = VoteProcessor(mock_db_session, mock_mp_identifier)

        # Count votes
        ayes = sum(1 for v in mp_votes if v.vote == "aye")
        noes = sum(1 for v in mp_votes if v.vote == "no")

        # Create a mock table
        table = [["MP Name", "Vote"]]
        for i, vote in enumerate(mp_votes):
            table.append([f"MP {i}", vote.vote])

        # Mock MP identifier
        mock_mp_identifier.identify = Mock(
            side_effect=[
                MPMatch(mp_id=f"mp-{i}", name=f"MP {i}", confidence=0.95)
                for i in range(len(mp_votes))
            ]
        )

        result = processor._parse_vote_table(table)

        if result:
            if ayes > noes:
                assert result.result == "passed"
            else:
                assert result.result == "failed"

    @given(st.lists(st.text(min_size=2, max_size=50), min_size=0, max_size=20))
    def test_mp_matching_completeness(self, mp_names):
        """
        Property: All matched MPs should be in result.

        **Validates: Requirements 9.2**

        Every MP that is successfully matched should appear
        in the final vote record.
        """
        # Create processor inside test
        mock_db_session = Mock()
        mock_mp_identifier = Mock()
        processor = VoteProcessor(mock_db_session, mock_mp_identifier)

        # Create a mock table
        table = [["MP Name", "Vote"]]
        for name in mp_names:
            table.append([name, "Aye"])

        # Mock MP identifier to match some MPs
        matches = []
        for i, name in enumerate(mp_names):
            if i % 2 == 0:  # Match every other MP
                matches.append(MPMatch(mp_id=f"mp-{i}", name=name, confidence=0.95))
            else:
                matches.append(None)

        mock_mp_identifier.identify = Mock(side_effect=matches)

        result = processor._parse_vote_table(table)

        if result:
            # Number of matched MPs should equal number of votes
            expected_matches = sum(1 for m in matches if m is not None)
            assert len(result.mp_votes) == expected_matches

    def test_empty_table_returns_none(self):
        """
        Property: Empty tables should return None.

        **Validates: Requirements 9.1**

        Tables with no data rows should return None.
        """
        # Create processor inside test
        mock_db_session = Mock()
        mock_mp_identifier = Mock()
        processor = VoteProcessor(mock_db_session, mock_mp_identifier)

        assert processor._parse_vote_table([]) is None
        assert processor._parse_vote_table([[]]) is None
        assert processor._parse_vote_table([["Header"]]) is None


class TestVoteExtractionCompleteness:
    """
    Test Property 7.1: Vote extraction completeness.

    **Validates: Requirements 9.3**

    This test validates that all votes in a PDF are extracted.
    """

    @patch("pdfplumber.open")
    def test_all_vote_tables_extracted(self, mock_pdfplumber):
        """
        Property 7.1: All vote tables should be extracted.

        **Validates: Requirements 9.3**

        Every table that contains vote data should be extracted
        and processed.
        """
        # Create processor inside test
        mock_db_session = Mock()
        mock_mp_identifier = Mock()
        processor = VoteProcessor(mock_db_session, mock_mp_identifier)

        # Create mock PDF with multiple pages and tables
        vote_table_1 = [["MP Name", "Vote"], ["MP 1", "Aye"], ["MP 2", "No"]]
        vote_table_2 = [["MP Name", "Vote"], ["MP 3", "Aye"]]
        non_vote_table = [["Name", "Age"], ["John", "30"]]

        mock_page1 = Mock()
        mock_page1.extract_tables.return_value = [vote_table_1, non_vote_table]

        mock_page2 = Mock()
        mock_page2.extract_tables.return_value = [vote_table_2]

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value.pages = [mock_page1, mock_page2]
        mock_pdfplumber.return_value = mock_pdf

        # Mock MP identifier
        mock_mp_identifier.identify = Mock(
            side_effect=[
                MPMatch(mp_id=f"mp-{i}", name=f"MP {i}", confidence=0.95) for i in range(1, 4)
            ]
        )

        pdf_path = Path("test.pdf")

        with patch.object(Path, "exists", return_value=True):
            results = processor.process_pdf(pdf_path)

        # Should extract 2 vote tables (not the non-vote table)
        assert len(results) == 2


class TestMPVoteAccuracy:
    """
    Test Property 7.2: MP vote accuracy.

    **Validates: Requirements 9.4**

    This test validates that MP votes match the source document.
    """

    def test_mp_vote_accuracy(self):
        """
        Property 7.2: MP votes must match source.

        **Validates: Requirements 9.4**

        Each MP's vote in the result should match their vote
        in the source table.
        """
        # Create processor inside test
        mock_db_session = Mock()
        mock_mp_identifier = Mock()
        processor = VoteProcessor(mock_db_session, mock_mp_identifier)

        # Test cases: (mp_name, vote_text, expected_vote)
        test_cases = [
            ("John Doe", "Aye", "aye"),
            ("Jane Smith", "No", "no"),
            ("Bob Johnson", "Abstain", "abstain"),
            ("Alice Brown", "Yes", "aye"),
            ("Charlie Wilson", "Nay", "no"),
        ]

        table = [["MP Name", "Vote"]]
        for mp_name, vote_text, _ in test_cases:
            table.append([mp_name, vote_text])

        # Mock MP identifier to return different MPs
        mock_mp_identifier.identify.side_effect = [
            MPMatch(mp_id=f"mp-{i}", name=mp_name, confidence=0.95)
            for i, (mp_name, _, _) in enumerate(test_cases)
        ]

        result = processor._parse_vote_table(table)

        assert result is not None
        assert len(result.mp_votes) == len(test_cases)

        # Verify each vote matches expected
        for i, (_, _, expected_vote) in enumerate(test_cases):
            assert result.mp_votes[i].vote == expected_vote

    @given(
        st.lists(
            st.tuples(
                st.text(min_size=2, max_size=50),  # MP name (min 2 to avoid single space)
                st.sampled_from(["Aye", "No", "Abstain", "Yes", "Nay"]),  # Vote text
            ),
            min_size=1,
            max_size=20,
        )
    )
    def test_vote_parsing_accuracy(self, vote_data):
        """
        Property: Vote parsing should be accurate.

        **Validates: Requirements 9.4**

        The parsed vote value should correctly represent the
        vote text from the source.
        """
        # Create processor and mock MP identifier inside test
        mock_db_session = Mock()
        mock_mp_identifier = Mock()
        processor = VoteProcessor(mock_db_session, mock_mp_identifier)

        table = [["MP Name", "Vote"]]
        for mp_name, vote_text in vote_data:
            table.append([mp_name, vote_text])

        # Mock MP identifier
        mock_mp_identifier.identify.side_effect = [
            MPMatch(mp_id=f"mp-{i}", name=mp_name, confidence=0.95)
            for i, (mp_name, _) in enumerate(vote_data)
        ]

        result = processor._parse_vote_table(table)

        if result:
            # Verify vote count matches input
            assert len(result.mp_votes) == len(vote_data)

            # Verify each vote is correctly parsed
            for i, (_, vote_text) in enumerate(vote_data):
                expected = processor._parse_vote_value(vote_text)
                assert result.mp_votes[i].vote == expected
