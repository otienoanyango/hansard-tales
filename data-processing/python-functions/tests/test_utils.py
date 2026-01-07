"""
Unit tests for Python shared utilities
"""

import pytest
from datetime import datetime
from shared.utils import (
    MP,
    StatementAnalysis,
    validate_mp,
    normalize_mp_name,
    extract_date_from_text,
    calculate_performance_score,
    filter_procedural_statements,
    estimate_ai_cost,
    build_analysis_prompt,
)


class TestMPValidation:
    """Test MP validation functionality"""

    def test_validate_mp_success(self):
        """Test successful MP validation"""
        mp = MP(
            id="mp001",
            name="John Mbadi",
            constituency="Suba South", 
            party="ODM"
        )
        assert validate_mp(mp) is True

    def test_validate_mp_empty_name(self):
        """Test validation fails for empty name"""
        mp = MP(id="mp002", name="", constituency="Test", party="ODM")
        with pytest.raises(ValueError, match="MP name cannot be empty"):
            validate_mp(mp)

    def test_validate_mp_whitespace_name(self):
        """Test validation fails for whitespace-only name"""
        mp = MP(id="mp003", name="   ", constituency="Test", party="ODM")
        with pytest.raises(ValueError, match="MP name cannot be empty"):
            validate_mp(mp)

    def test_validate_mp_empty_constituency(self):
        """Test validation fails for empty constituency"""
        mp = MP(id="mp004", name="Test MP", constituency="", party="ODM")
        with pytest.raises(ValueError, match="MP constituency cannot be empty"):
            validate_mp(mp)

    def test_validate_mp_empty_party(self):
        """Test validation fails for empty party"""
        mp = MP(id="mp005", name="Test MP", constituency="Test", party="")
        with pytest.raises(ValueError, match="MP party cannot be empty"):
            validate_mp(mp)


class TestMPNameNormalization:
    """Test MP name normalization functionality"""

    def test_normalize_empty_name(self):
        """Test normalization with empty string"""
        assert normalize_mp_name("") == ""

    def test_normalize_none_name(self):
        """Test normalization with None input"""
        assert normalize_mp_name(None) == ""

    def test_remove_honorific_prefix(self):
        """Test removal of Hon. prefix"""
        assert normalize_mp_name("Hon. John Mbadi") == "John Mbadi"

    def test_remove_doctor_prefix(self):
        """Test removal of (Dr) prefix"""
        assert normalize_mp_name("Hon. (Dr) James Opiyo") == "James Opiyo"

    def test_remove_engineer_prefix(self):
        """Test removal of (Eng) prefix"""
        assert normalize_mp_name("(Eng) Peter Kihungi") == "Peter Kihungi"

    def test_normalize_spacing(self):
        """Test spacing normalization"""
        assert normalize_mp_name("John    Mbadi   Ng'ongo") == "John Mbadi Ng'ongo"

    def test_trim_whitespace(self):
        """Test whitespace trimming"""
        assert normalize_mp_name("  John Mbadi  ") == "John Mbadi"

    def test_complex_normalization(self):
        """Test complex name normalization"""
        input_name = "  Hon. (Dr)  James   Opiyo   Wandayi  "
        expected = "James Opiyo Wandayi"
        assert normalize_mp_name(input_name) == expected


class TestDateExtraction:
    """Test date extraction functionality"""

    def test_extract_iso_date(self):
        """Test ISO date format extraction"""
        text = "Hansard Report - Thursday, 2025-12-04"
        result = extract_date_from_text(text)
        assert result is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 4

    def test_extract_no_date(self):
        """Test when no date is found"""
        text = "Random text without any date"
        result = extract_date_from_text(text)
        assert result is None

    def test_extract_empty_text(self):
        """Test with empty text"""
        assert extract_date_from_text("") is None

    def test_extract_none_text(self):
        """Test with None text"""
        assert extract_date_from_text(None) is None


class TestPerformanceScoreCalculation:
    """Test performance score calculation"""

    def test_perfect_scores(self):
        """Test calculation with perfect scores"""
        result = calculate_performance_score(100, 100, 100)
        assert result == 100.0

    def test_zero_scores(self):
        """Test calculation with zero scores"""
        result = calculate_performance_score(0, 0, 0)
        assert result == 0.0

    def test_mixed_scores(self):
        """Test calculation with mixed scores"""
        # 80*0.4 + 60*0.3 + 90*0.3 = 32 + 18 + 27 = 77
        result = calculate_performance_score(80, 60, 90)
        assert abs(result - 77.0) < 0.1

    def test_score_capping_high(self):
        """Test score capping at maximum"""
        result = calculate_performance_score(150, 150, 150)
        assert result == 100.0

    def test_score_capping_low(self):
        """Test score capping at minimum"""
        result = calculate_performance_score(-50, -50, -50)
        assert result == 0.0


class TestProceduralFiltering:
    """Test procedural statement filtering"""

    def test_filter_adjournment_statements(self):
        """Test filtering of house adjournment statements"""
        statements = [
            "The house stands adjourned until tomorrow",
            "Hon. Member makes substantive point about budget",
            "The house rose at 6 PM"
        ]
        filtered = filter_procedural_statements(statements)
        assert len(filtered) == 1
        assert "substantive point about budget" in filtered[0]

    def test_filter_question_statements(self):
        """Test filtering of question procedural statements"""
        statements = [
            "Question put and agreed to",
            "The Member raises important policy question",
            "Question proposed by the Chair"
        ]
        filtered = filter_procedural_statements(statements)
        assert len(filtered) == 1
        assert "important policy question" in filtered[0]

    def test_filter_empty_list(self):
        """Test filtering with empty list"""
        assert filter_procedural_statements([]) == []

    def test_no_procedural_statements(self):
        """Test with no procedural statements"""
        statements = [
            "MP discusses important policy",
            "Budget allocation concerns raised",
            "Constitutional matters debated"
        ]
        filtered = filter_procedural_statements(statements)
        assert len(filtered) == 3  # All should remain


class TestAICostEstimation:
    """Test AI cost estimation"""

    def test_estimate_default_cost(self):
        """Test cost estimation with default rate"""
        statements = ["Statement 1", "Statement 2", "Statement 3"]
        cost = estimate_ai_cost(statements)
        assert cost == 0.003  # 3 * 0.001

    def test_estimate_custom_cost(self):
        """Test cost estimation with custom rate"""
        statements = ["Statement 1", "Statement 2"]
        cost = estimate_ai_cost(statements, cost_per_statement=0.005)
        assert cost == 0.01  # 2 * 0.005

    def test_estimate_empty_statements(self):
        """Test cost estimation with empty statements"""
        cost = estimate_ai_cost([])
        assert cost == 0.0


class TestPromptBuilding:
    """Test AI prompt building"""

    def test_build_basic_prompt(self):
        """Test basic prompt building"""
        statements = ["Test statement 1", "Test statement 2"]
        prompt = build_analysis_prompt(statements)
        
        assert "Analyze these parliamentary statements" in prompt
        assert "1. Test statement 1" in prompt
        assert "2. Test statement 2" in prompt
        assert "JSON with: stance, quality, confidence" in prompt

    def test_build_prompt_with_context(self):
        """Test prompt building with context"""
        statements = ["Test statement"]
        prompt = build_analysis_prompt(statements, context="Budget Debate")
        
        assert "from Budget Debate" in prompt

    def test_build_prompt_empty_statements(self):
        """Test prompt building with empty statements"""
        prompt = build_analysis_prompt([])
        assert prompt == ""

    def test_build_prompt_limits_statements(self):
        """Test prompt limits statements to 25"""
        statements = [f"Statement {i}" for i in range(30)]  # 30 statements
        prompt = build_analysis_prompt(statements)
        
        # Should only include up to 25
        assert "25. Statement 24" in prompt  # 0-indexed, so 24 is the 25th
        assert "26. Statement 25" not in prompt

    def test_build_prompt_none_statements(self):
        """Test prompt building with None statements"""
        prompt = build_analysis_prompt(None)
        assert prompt == ""


class TestStatementAnalysisDataClass:
    """Test StatementAnalysis data structure"""

    def test_statement_analysis_creation(self):
        """Test creating StatementAnalysis object"""
        analysis = StatementAnalysis(
            statement_id="stmt001",
            mp_id="mp001",
            topic="Budget",
            stance="for",
            quality="substantive",
            confidence=0.85,
            reasoning="Clear support for budget allocation"
        )
        
        assert analysis.statement_id == "stmt001"
        assert analysis.mp_id == "mp001"
        assert analysis.topic == "Budget"
        assert analysis.stance == "for"
        assert analysis.quality == "substantive"
        assert analysis.confidence == 0.85
        assert "budget allocation" in analysis.reasoning.lower()

    def test_statement_analysis_serialization(self):
        """Test StatementAnalysis can be converted to dict"""
        analysis = StatementAnalysis(
            statement_id="stmt001",
            mp_id="mp001",
            topic="Budget",
            stance="against",
            quality="heckling",
            confidence=0.3,
            reasoning="Interruption without substance"
        )
        
        # Test that dataclass can be converted to dict (useful for JSON serialization)
        from dataclasses import asdict
        analysis_dict = asdict(analysis)
        
        assert analysis_dict['statement_id'] == "stmt001"
        assert analysis_dict['stance'] == "against"
        assert analysis_dict['quality'] == "heckling"
        assert analysis_dict['confidence'] == 0.3


# Integration-style tests
class TestUtilityIntegration:
    """Test utilities working together"""

    def test_mp_workflow(self):
        """Test complete MP processing workflow"""
        # Create and validate MP
        raw_mp = MP(
            id="mp001",
            name="  Hon. (Dr) John   Mbadi  Ng'ongo  ",
            constituency="Suba South",
            party="ODM"
        )
        
        # Validate
        assert validate_mp(raw_mp) is True
        
        # Normalize name
        normalized_name = normalize_mp_name(raw_mp.name)
        assert normalized_name == "John Mbadi Ng'ongo"
        
        # Calculate performance
        score = calculate_performance_score(85, 70, 80)
        assert 75 < score < 85  # Should be around 78

    def test_statement_processing_workflow(self):
        """Test statement processing workflow"""
        # Raw statements from parliament
        raw_statements = [
            "The house stands adjourned until tomorrow",
            "Hon. Member raises budget concerns",
            "Question put and agreed to",
            "Committee recommends policy changes",
            "Hon. Members please take your seats"
        ]
        
        # Filter procedural
        filtered = filter_procedural_statements(raw_statements)
        assert len(filtered) == 2  # Only substantive statements remain
        
        # Estimate cost
        cost = estimate_ai_cost(filtered)
        assert cost == 0.002  # 2 statements * 0.001
        
        # Build prompt
        prompt = build_analysis_prompt(filtered, "Budget Session")
        assert "budget concerns" in prompt.lower()
        assert "policy changes" in prompt.lower()
        assert "from Budget Session" in prompt
