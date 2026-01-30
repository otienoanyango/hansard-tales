"""
Unit tests for FillerDetector.

Tests statement classification functionality including:
- Procedural detection
- Interruption detection
- Administrative detection
- Short acknowledgment detection
- Substantive classification
"""

import pytest

from hansard_tales.analysis.filler_detector import FillerDetector, StatementType
from hansard_tales.analysis.statement_segmenter import Statement


class TestFillerDetector:
    """Test suite for FillerDetector class."""

    @pytest.fixture
    def detector(self):
        """Create FillerDetector instance."""
        return FillerDetector()

    @pytest.fixture
    def sample_statement(self):
        """Create sample statement for testing."""
        return Statement(
            text="Sample statement text",
            mp_id="test-mp-id",
            start_pos=0,
            end_pos=100,
            page_number=1,
        )

    def test_initialization(self, detector):
        """Test FillerDetector initialization."""
        assert detector is not None
        assert len(detector.filler_patterns) == 4
        assert StatementType.PROCEDURAL in detector.filler_patterns
        assert StatementType.INTERRUPTION in detector.filler_patterns
        assert StatementType.ADMINISTRATIVE in detector.filler_patterns
        assert StatementType.SHORT_ACK in detector.filler_patterns

    def test_patterns_compiled(self, detector):
        """Test that patterns are compiled."""
        assert len(detector.compiled_patterns) == 4
        for patterns in detector.compiled_patterns.values():
            assert len(patterns) > 0
            for pattern in patterns:
                assert hasattr(pattern, "search")


class TestProceduralDetection:
    """Test procedural statement detection."""

    @pytest.fixture
    def detector(self):
        """Create FillerDetector instance."""
        return FillerDetector()

    def test_i_beg_to_move(self, detector):
        """Test detection of 'I beg to move' pattern."""
        statement = Statement(
            text="I beg to move that this House adopts the report",
            mp_id="test-mp",
            start_pos=0,
            end_pos=50,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.PROCEDURAL
        assert confidence == 0.95

    def test_i_second(self, detector):
        """Test detection of 'I second' pattern."""
        statement = Statement(text="I second the motion", mp_id="test-mp", start_pos=0, end_pos=20)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.PROCEDURAL
        assert confidence == 0.95

    def test_question_put_and_agreed(self, detector):
        """Test detection of 'Question put and agreed to' pattern."""
        statement = Statement(
            text="Question put and agreed to",
            mp_id="test-mp",
            start_pos=0,
            end_pos=30,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.PROCEDURAL
        assert confidence == 0.95

    def test_motion_made(self, detector):
        """Test detection of 'Motion made and Question proposed' pattern."""
        statement = Statement(
            text="Motion made and Question proposed",
            mp_id="test-mp",
            start_pos=0,
            end_pos=35,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.PROCEDURAL
        assert confidence == 0.95

    def test_i_beg_to_lay(self, detector):
        """Test detection of 'I beg to lay' pattern."""
        statement = Statement(
            text="I beg to lay the following papers on the Table",
            mp_id="test-mp",
            start_pos=0,
            end_pos=50,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.PROCEDURAL
        assert confidence == 0.95

    def test_point_of_order(self, detector):
        """Test detection of point of order patterns."""
        statement1 = Statement(
            text="I rise on a point of order",
            mp_id="test-mp",
            start_pos=0,
            end_pos=30,
        )
        stmt_type1, confidence1 = detector.classify(statement1)
        assert stmt_type1 == StatementType.PROCEDURAL
        assert confidence1 == 0.95

        statement2 = Statement(
            text="Point of order, Mr. Speaker",
            mp_id="test-mp",
            start_pos=0,
            end_pos=30,
        )
        stmt_type2, confidence2 = detector.classify(statement2)
        assert stmt_type2 == StatementType.PROCEDURAL
        assert confidence2 == 0.95

    def test_case_insensitive_procedural(self, detector):
        """Test case-insensitive matching for procedural patterns."""
        statement = Statement(
            text="i beg to move that this house",
            mp_id="test-mp",
            start_pos=0,
            end_pos=30,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.PROCEDURAL
        assert confidence == 0.95


class TestInterruptionDetection:
    """Test interruption statement detection."""

    @pytest.fixture
    def detector(self):
        """Create FillerDetector instance."""
        return FillerDetector()

    def test_applause(self, detector):
        """Test detection of applause."""
        statement = Statement(text="(Applause)", mp_id="test-mp", start_pos=0, end_pos=10)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.INTERRUPTION
        assert confidence == 0.95

    def test_laughter(self, detector):
        """Test detection of laughter."""
        statement = Statement(text="(Laughter)", mp_id="test-mp", start_pos=0, end_pos=10)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.INTERRUPTION
        assert confidence == 0.95

    def test_interruptions(self, detector):
        """Test detection of interruptions."""
        statement = Statement(text="(Interruptions)", mp_id="test-mp", start_pos=0, end_pos=15)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.INTERRUPTION
        assert confidence == 0.95

    def test_loud_consultations(self, detector):
        """Test detection of loud consultations."""
        statement = Statement(text="(Loud consultations)", mp_id="test-mp", start_pos=0, end_pos=20)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.INTERRUPTION
        assert confidence == 0.95

    def test_consultations(self, detector):
        """Test detection of consultations."""
        statement = Statement(text="(Consultations)", mp_id="test-mp", start_pos=0, end_pos=15)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.INTERRUPTION
        assert confidence == 0.95

    def test_interjections(self, detector):
        """Test detection of interjections."""
        statement = Statement(text="(Interjections)", mp_id="test-mp", start_pos=0, end_pos=15)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.INTERRUPTION
        assert confidence == 0.95

    def test_members_walked_out(self, detector):
        """Test detection of members walking out."""
        statement = Statement(text="(Members walked out)", mp_id="test-mp", start_pos=0, end_pos=20)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.INTERRUPTION
        assert confidence == 0.95

    def test_hon_member_interjection(self, detector):
        """Test detection of hon. member interjections."""
        statement = Statement(
            text="(An hon. Member spoke off record)",
            mp_id="test-mp",
            start_pos=0,
            end_pos=35,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.INTERRUPTION
        assert confidence == 0.95


class TestAdministrativeDetection:
    """Test administrative statement detection."""

    @pytest.fixture
    def detector(self):
        """Create FillerDetector instance."""
        return FillerDetector()

    def test_house_rose(self, detector):
        """Test detection of 'The House rose at' pattern."""
        statement = Statement(
            text="The House rose at 6:30 p.m.",
            mp_id="test-mp",
            start_pos=0,
            end_pos=30,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.ADMINISTRATIVE
        assert confidence == 0.95

    def test_prayers(self, detector):
        """Test detection of prayers."""
        statement = Statement(text="Prayers", mp_id="test-mp", start_pos=0, end_pos=10)
        stmt_type, confidence = detector.classify(statement)
        # "Prayers" is 7 chars, so caught by length check first
        assert stmt_type == StatementType.SHORT_ACK
        assert confidence == 1.0

    def test_adjournment(self, detector):
        """Test detection of adjournment."""
        statement = Statement(text="ADJOURNMENT", mp_id="test-mp", start_pos=0, end_pos=15)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.ADMINISTRATIVE
        assert confidence == 0.95

    def test_communication_from_chair(self, detector):
        """Test detection of communication from the chair."""
        statement = Statement(
            text="COMMUNICATION FROM THE CHAIR",
            mp_id="test-mp",
            start_pos=0,
            end_pos=30,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.ADMINISTRATIVE
        assert confidence == 0.95

    def test_papers_laid(self, detector):
        """Test detection of papers laid."""
        statement = Statement(text="PAPERS LAID", mp_id="test-mp", start_pos=0, end_pos=15)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.ADMINISTRATIVE
        assert confidence == 0.95

    def test_house_met(self, detector):
        """Test detection of 'The House met at' pattern."""
        statement = Statement(
            text="The House met at 2:30 p.m.",
            mp_id="test-mp",
            start_pos=0,
            end_pos=30,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.ADMINISTRATIVE
        assert confidence == 0.95

    def test_quorum(self, detector):
        """Test detection of quorum statements."""
        statement1 = Statement(text="QUORUM", mp_id="test-mp", start_pos=0, end_pos=10)
        stmt_type1, confidence1 = detector.classify(statement1)
        # "QUORUM" is 6 chars, so caught by length check first
        assert stmt_type1 == StatementType.SHORT_ACK
        assert confidence1 == 1.0

        statement2 = Statement(
            text="Quorum bell was rung", mp_id="test-mp", start_pos=0, end_pos=20
        )
        stmt_type2, confidence2 = detector.classify(statement2)
        assert stmt_type2 == StatementType.ADMINISTRATIVE
        assert confidence2 == 0.95


class TestShortAcknowledgmentDetection:
    """Test short acknowledgment detection."""

    @pytest.fixture
    def detector(self):
        """Create FillerDetector instance."""
        return FillerDetector()

    def test_very_short_text(self, detector):
        """Test detection based on length (< 10 chars)."""
        statement = Statement(text="Yes", mp_id="test-mp", start_pos=0, end_pos=5)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.SHORT_ACK
        assert confidence == 1.0

    def test_thank_you(self, detector):
        """Test detection of 'Thank you' pattern."""
        statement = Statement(text="Thank you", mp_id="test-mp", start_pos=0, end_pos=10)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.SHORT_ACK
        # "Thank you" is 9 chars, caught by length check
        assert confidence == 1.0

    def test_i_agree(self, detector):
        """Test detection of 'I agree' pattern."""
        statement = Statement(text="I agree", mp_id="test-mp", start_pos=0, end_pos=10)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.SHORT_ACK
        # "I agree" is 7 chars, caught by length check
        assert confidence == 1.0

    def test_yes_no(self, detector):
        """Test detection of yes/no patterns."""
        statement1 = Statement(text="Yes.", mp_id="test-mp", start_pos=0, end_pos=5)
        stmt_type1, confidence1 = detector.classify(statement1)
        assert stmt_type1 == StatementType.SHORT_ACK

        statement2 = Statement(text="No.", mp_id="test-mp", start_pos=0, end_pos=5)
        stmt_type2, confidence2 = detector.classify(statement2)
        assert stmt_type2 == StatementType.SHORT_ACK

    def test_agreed(self, detector):
        """Test detection of 'Agreed' pattern."""
        statement = Statement(text="Agreed.", mp_id="test-mp", start_pos=0, end_pos=10)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.SHORT_ACK
        # "Agreed." is 7 chars, caught by length check
        assert confidence == 1.0

    def test_i_support_oppose(self, detector):
        """Test detection of support/oppose patterns."""
        statement1 = Statement(text="I support.", mp_id="test-mp", start_pos=0, end_pos=12)
        stmt_type1, confidence1 = detector.classify(statement1)
        assert stmt_type1 == StatementType.SHORT_ACK
        # "I support." is 10 chars, so pattern match (not length check)
        assert confidence1 == 0.95

        statement2 = Statement(text="I oppose.", mp_id="test-mp", start_pos=0, end_pos=12)
        stmt_type2, confidence2 = detector.classify(statement2)
        assert stmt_type2 == StatementType.SHORT_ACK
        # "I oppose." is 9 chars, caught by length check
        assert confidence2 == 1.0

    def test_hear_hear(self, detector):
        """Test detection of 'Hear! Hear!' pattern."""
        statement = Statement(text="Hear! Hear!", mp_id="test-mp", start_pos=0, end_pos=12)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.SHORT_ACK
        assert confidence == 0.95


class TestSubstantiveClassification:
    """Test substantive statement classification."""

    @pytest.fixture
    def detector(self):
        """Create FillerDetector instance."""
        return FillerDetector()

    def test_substantive_statement(self, detector):
        """Test classification of substantive statement."""
        statement = Statement(
            text="Mr. Speaker, I rise to address the issue of healthcare funding in our constituency. "
            "The current allocation is insufficient to meet the needs of our growing population.",
            mp_id="test-mp",
            start_pos=0,
            end_pos=150,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.SUBSTANTIVE
        assert confidence == 0.90

    def test_long_policy_statement(self, detector):
        """Test classification of long policy statement."""
        statement = Statement(
            text="The proposed amendments to the Finance Bill will have significant implications "
            "for small businesses across the country. We must consider the impact on job creation "
            "and economic growth before proceeding with these changes.",
            mp_id="test-mp",
            start_pos=0,
            end_pos=250,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.SUBSTANTIVE
        assert confidence == 0.90

    def test_is_substantive_helper(self, detector):
        """Test is_substantive helper method."""
        substantive_stmt = Statement(
            text="This is a substantive statement about policy matters.",
            mp_id="test-mp",
            start_pos=0,
            end_pos=60,
        )
        assert detector.is_substantive(substantive_stmt) is True

        filler_stmt = Statement(text="I beg to move", mp_id="test-mp", start_pos=0, end_pos=15)
        assert detector.is_substantive(filler_stmt) is False

    def test_substantive_with_whitespace(self, detector):
        """Test substantive classification with leading/trailing whitespace."""
        statement = Statement(
            text="  \n  This is a substantive statement with whitespace.  \n  ",
            mp_id="test-mp",
            start_pos=0,
            end_pos=60,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.SUBSTANTIVE
        assert confidence == 0.90


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def detector(self):
        """Create FillerDetector instance."""
        return FillerDetector()

    def test_empty_statement(self, detector):
        """Test classification of empty statement."""
        statement = Statement(text="", mp_id="test-mp", start_pos=0, end_pos=0)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.SHORT_ACK
        assert confidence == 1.0

    def test_whitespace_only(self, detector):
        """Test classification of whitespace-only statement."""
        statement = Statement(text="   \n  \t  ", mp_id="test-mp", start_pos=0, end_pos=10)
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.SHORT_ACK
        assert confidence == 1.0

    def test_mixed_case_patterns(self, detector):
        """Test pattern matching with mixed case."""
        statement = Statement(
            text="I BEG TO MOVE that this House",
            mp_id="test-mp",
            start_pos=0,
            end_pos=30,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.PROCEDURAL
        assert confidence == 0.95

    def test_pattern_in_middle_of_text(self, detector):
        """Test that patterns must be at start of text."""
        statement = Statement(
            text="The member said I beg to move but this is substantive content.",
            mp_id="test-mp",
            start_pos=0,
            end_pos=70,
        )
        stmt_type, confidence = detector.classify(statement)
        # Should be substantive because pattern is not at start
        assert stmt_type == StatementType.SUBSTANTIVE
        assert confidence == 0.90

    def test_multiple_patterns_first_wins(self, detector):
        """Test that first matching pattern determines classification."""
        # This starts with procedural pattern
        statement = Statement(
            text="I beg to move (Applause)",
            mp_id="test-mp",
            start_pos=0,
            end_pos=25,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.PROCEDURAL
        assert confidence == 0.95

    def test_none_mp_id(self, detector):
        """Test classification with None mp_id."""
        statement = Statement(
            text="This is a substantive statement.",
            mp_id=None,
            start_pos=0,
            end_pos=35,
        )
        stmt_type, confidence = detector.classify(statement)
        assert stmt_type == StatementType.SUBSTANTIVE
        assert confidence == 0.90
