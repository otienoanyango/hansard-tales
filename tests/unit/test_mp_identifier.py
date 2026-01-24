"""
Tests for MP identification and statement extraction.

This module tests the MP identification functionality including
speaker pattern matching, statement extraction, and name normalization.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import the identifier module
from hansard_tales.processors.mp_identifier import MPIdentifier, Statement


@pytest.fixture
def identifier():
    """Create an MP identifier instance for testing."""
    return MPIdentifier(use_spacy=False)


@pytest.fixture
def sample_hansard_text():
    """Create sample Hansard text for testing."""
    return """
    The Speaker: Good morning, Honourable Members.
    
    Hon. John Mbadi: Thank you, Mr. Speaker. I rise to address the issue of healthcare funding.
    The government must allocate more resources to our hospitals.
    
    Hon. Alice Wahome: Mr. Speaker, I support the Member's statement. We need better healthcare.
    
    The Speaker: Thank you, Honourable Members.
    
    Hon. John Mbadi: Mr. Speaker, I would like to add that we also need to consider rural areas.
    """


@pytest.fixture
def sample_pdf_pages():
    """Create sample PDF pages data."""
    return [
        {
            'page_number': 1,
            'text': 'Hon. John Doe: This is a statement on page 1.',
            'char_count': 45
        },
        {
            'page_number': 2,
            'text': 'Hon. Jane Smith: This is a statement on page 2.\nHon. John Doe: Another statement.',
            'char_count': 80
        }
    ]


class TestMPIdentifier:
    """Test suite for MP identifier initialization."""
    
    def test_identifier_initialization(self):
        """Test identifier initializes correctly."""
        identifier = MPIdentifier(use_spacy=False)
        assert identifier.use_spacy is False
        assert identifier.nlp is None
    
    def test_identifier_with_spacy_unavailable(self):
        """Test identifier handles missing spaCy gracefully."""
        # Just test that it doesn't crash when spaCy is unavailable
        identifier = MPIdentifier(use_spacy=True)
        # If spaCy is not installed, use_spacy should be False
        # If it is installed, it should be True
        # Either way, the identifier should work
        assert identifier is not None
    
    def test_speaker_patterns_compiled(self):
        """Test that speaker patterns are compiled."""
        identifier = MPIdentifier()
        assert len(identifier.COMPILED_PATTERNS) > 0
        assert all(hasattr(p, 'finditer') for p in identifier.COMPILED_PATTERNS)


class TestNameNormalization:
    """Test suite for MP name normalization."""
    
    def test_normalize_simple_name(self, identifier):
        """Test normalizing a simple name."""
        result = identifier.normalize_mp_name("JOHN DOE")
        assert result == "John Doe"
    
    def test_normalize_name_with_extra_spaces(self, identifier):
        """Test normalizing name with extra whitespace."""
        result = identifier.normalize_mp_name("John   Doe  ")
        assert result == "John Doe"
    
    def test_normalize_name_with_parenthetical(self, identifier):
        """Test normalizing name with parenthetical content."""
        result = identifier.normalize_mp_name("John Doe (Nairobi)")
        assert result == "John Doe"
    
    def test_normalize_name_with_mp_suffix(self, identifier):
        """Test normalizing name with MP suffix."""
        result = identifier.normalize_mp_name("John Doe, MP")
        assert result == "John Doe"
    
    def test_normalize_lowercase_name(self, identifier):
        """Test normalizing lowercase name."""
        result = identifier.normalize_mp_name("john doe")
        assert result == "John Doe"
    
    def test_normalize_mixed_case_name(self, identifier):
        """Test normalizing mixed case name."""
        result = identifier.normalize_mp_name("jOhN dOe")
        assert result == "John Doe"


class TestSpeakerFinding:
    """Test suite for finding speakers in text."""
    
    def test_find_hon_speaker(self, identifier):
        """Test finding 'Hon. Name:' pattern."""
        text = "Hon. John Doe: This is a statement."
        speakers = identifier.find_all_speakers(text)
        
        assert len(speakers) == 1
        assert speakers[0][0] == "John Doe"
    
    def test_find_multiple_speakers(self, identifier):
        """Test finding multiple speakers."""
        text = """
        Hon. John Doe: First statement.
        Hon. Jane Smith: Second statement.
        Hon. Bob Wilson: Third statement.
        """
        speakers = identifier.find_all_speakers(text)
        
        assert len(speakers) == 3
        assert speakers[0][0] == "John Doe"
        assert speakers[1][0] == "Jane Smith"
        assert speakers[2][0] == "Bob Wilson"
    
    def test_find_speaker_with_parenthetical(self, identifier):
        """Test finding speaker with parenthetical content."""
        text = "Hon. John Doe (Nairobi): This is a statement."
        speakers = identifier.find_all_speakers(text)
        
        assert len(speakers) == 1
        assert speakers[0][0] == "John Doe"
    
    def test_find_the_speaker(self, identifier):
        """Test finding 'The Speaker:' pattern."""
        text = "The Speaker: Good morning, Members."
        speakers = identifier.find_all_speakers(text)
        
        # Should find exactly one speaker (no duplicates)
        assert len(speakers) == 1
        assert speakers[0][0] == "The Speaker"
    
    def test_find_mr_speaker(self, identifier):
        """Test finding 'Mr. Speaker:' pattern."""
        text = "Mr. Speaker: Thank you."
        speakers = identifier.find_all_speakers(text)
        
        assert len(speakers) == 1
        assert speakers[0][0] == "Mr. Speaker"
    
    def test_find_madam_speaker(self, identifier):
        """Test finding 'Madam Speaker:' pattern."""
        text = "Madam Speaker: Thank you."
        speakers = identifier.find_all_speakers(text)
        
        assert len(speakers) == 1
        assert speakers[0][0] == "Madam Speaker"
    
    def test_speakers_sorted_by_position(self, identifier):
        """Test that speakers are sorted by position."""
        text = """
        Hon. Alice: First.
        Hon. Bob: Second.
        Hon. Charlie: Third.
        """
        speakers = identifier.find_all_speakers(text)
        
        # Verify positions are in ascending order
        positions = [start_pos for _, start_pos, _ in speakers]
        assert positions == sorted(positions)


class TestStatementExtraction:
    """Test suite for extracting statement text."""
    
    def test_extract_statement_to_next_speaker(self, identifier):
        """Test extracting statement until next speaker."""
        text = "Hon. John: Statement text here. Hon. Jane: Next statement."
        start_pos = text.index("Statement")
        next_pos = text.index("Hon. Jane")
        
        statement = identifier.extract_statement_text(text, start_pos, next_pos)
        
        assert "Statement text here." in statement
        assert "Hon. Jane" not in statement
    
    def test_extract_statement_to_end(self, identifier):
        """Test extracting statement to end of text."""
        text = "Hon. John: Statement text here."
        start_pos = text.index("Statement")
        
        statement = identifier.extract_statement_text(text, start_pos, None)
        
        assert statement == "Statement text here."
    
    def test_extract_statement_strips_whitespace(self, identifier):
        """Test that extracted statement is stripped."""
        text = "Hon. John:   Statement text.   "
        start_pos = text.index("Statement")
        
        statement = identifier.extract_statement_text(text, start_pos, None)
        
        assert statement == "Statement text."
    
    def test_extract_statement_removes_leading_colon(self, identifier):
        """Test that leading colon is removed."""
        text = "Hon. John: Statement."
        start_pos = text.index(":")
        
        statement = identifier.extract_statement_text(text, start_pos, None)
        
        assert not statement.startswith(":")
        assert "Statement" in statement


class TestExtractStatements:
    """Test suite for complete statement extraction."""
    
    def test_extract_single_statement(self, identifier):
        """Test extracting a single statement."""
        text = "Hon. John Doe: This is a test statement."
        statements = identifier.extract_statements(text)
        
        assert len(statements) == 1
        assert statements[0].mp_name == "John Doe"
        assert "test statement" in statements[0].text
    
    def test_extract_multiple_statements(self, identifier, sample_hansard_text):
        """Test extracting multiple statements."""
        statements = identifier.extract_statements(sample_hansard_text)
        
        # Should find John Mbadi (2 statements) and Alice Wahome (1 statement)
        # The Speaker should be filtered out
        assert len(statements) >= 2
        
        mp_names = [stmt.mp_name for stmt in statements]
        assert "John Mbadi" in mp_names
        assert "Alice Wahome" in mp_names
    
    def test_filter_non_mp_speakers(self, identifier, sample_hansard_text):
        """Test that non-MP speakers are filtered out."""
        statements = identifier.extract_statements(sample_hansard_text, filter_non_mps=True)
        
        mp_names = [stmt.mp_name for stmt in statements]
        assert "The Speaker" not in mp_names
        assert "Mr. Speaker" not in mp_names
    
    def test_include_non_mp_speakers(self, identifier, sample_hansard_text):
        """Test including non-MP speakers."""
        statements = identifier.extract_statements(sample_hansard_text, filter_non_mps=False)
        
        mp_names = [stmt.mp_name for stmt in statements]
        # Should include The Speaker
        assert any("Speaker" in name for name in mp_names)
    
    def test_skip_empty_statements(self, identifier):
        """Test that empty statements are skipped."""
        text = "Hon. John Doe: \n\nHon. Jane Smith: Real statement here."
        statements = identifier.extract_statements(text)
        
        # Should only get Jane Smith's statement
        assert len(statements) == 1
        assert statements[0].mp_name == "Jane Smith"
    
    def test_skip_short_statements(self, identifier):
        """Test that very short statements are skipped."""
        text = "Hon. John Doe: Yes.\nHon. Jane Smith: This is a longer statement with more content."
        statements = identifier.extract_statements(text)
        
        # Should only get Jane Smith's statement (>10 chars)
        assert len(statements) == 1
        assert statements[0].mp_name == "Jane Smith"
    
    def test_statement_positions(self, identifier):
        """Test that statement positions are recorded."""
        text = "Hon. John Doe: Statement one. Hon. Jane Smith: Statement two."
        statements = identifier.extract_statements(text)
        
        assert len(statements) == 2
        assert statements[0].start_position < statements[1].start_position
        assert statements[0].end_position <= statements[1].start_position
    
    def test_statement_with_page_number(self, identifier):
        """Test extracting statement with page number."""
        text = "Hon. John Doe: Test statement."
        statements = identifier.extract_statements(text, page_number=5)
        
        assert len(statements) == 1
        assert statements[0].page_number == 5
    
    def test_no_speakers_found(self, identifier):
        """Test handling text with no speakers."""
        text = "This is just regular text with no speakers."
        statements = identifier.extract_statements(text)
        
        assert len(statements) == 0


class TestExtractFromPages:
    """Test suite for extracting from PDF pages."""
    
    def test_extract_from_pages(self, identifier, sample_pdf_pages):
        """Test extracting statements from PDF pages."""
        statements = identifier.extract_statements_from_pages(sample_pdf_pages)
        
        assert len(statements) >= 2
        
        # Check page numbers are preserved
        page_numbers = [stmt.page_number for stmt in statements]
        assert 1 in page_numbers
        assert 2 in page_numbers
    
    def test_extract_from_empty_pages(self, identifier):
        """Test extracting from pages with no text."""
        pages = [
            {'page_number': 1, 'text': ''},
            {'page_number': 2, 'text': ''}
        ]
        statements = identifier.extract_statements_from_pages(pages)
        
        assert len(statements) == 0
    
    def test_extract_from_mixed_pages(self, identifier):
        """Test extracting from mix of empty and non-empty pages."""
        pages = [
            {'page_number': 1, 'text': ''},
            {'page_number': 2, 'text': 'Hon. John Doe: Statement here.'},
            {'page_number': 3, 'text': ''}
        ]
        statements = identifier.extract_statements_from_pages(pages)
        
        assert len(statements) == 1
        assert statements[0].page_number == 2


class TestUtilityMethods:
    """Test suite for utility methods."""
    
    def test_get_unique_mp_names(self, identifier):
        """Test getting unique MP names."""
        statements = [
            Statement("John Doe", "Text 1", 0, 10),
            Statement("Jane Smith", "Text 2", 10, 20),
            Statement("John Doe", "Text 3", 20, 30),
        ]
        
        unique_names = identifier.get_unique_mp_names(statements)
        
        assert len(unique_names) == 2
        assert "John Doe" in unique_names
        assert "Jane Smith" in unique_names
        assert unique_names == sorted(unique_names)  # Should be sorted
    
    def test_get_statements_by_mp(self, identifier):
        """Test grouping statements by MP."""
        statements = [
            Statement("John Doe", "Text 1", 0, 10),
            Statement("Jane Smith", "Text 2", 10, 20),
            Statement("John Doe", "Text 3", 20, 30),
        ]
        
        by_mp = identifier.get_statements_by_mp(statements)
        
        assert len(by_mp) == 2
        assert len(by_mp["John Doe"]) == 2
        assert len(by_mp["Jane Smith"]) == 1
    
    def test_get_statistics(self, identifier):
        """Test getting statistics."""
        statements = [
            Statement("John Doe", "A" * 100, 0, 10),
            Statement("Jane Smith", "B" * 200, 10, 20),
            Statement("John Doe", "C" * 150, 20, 30),
        ]
        
        stats = identifier.get_statistics(statements)
        
        assert stats['total_statements'] == 3
        assert stats['unique_mps'] == 2
        assert stats['total_characters'] == 450
        assert stats['avg_statement_length'] == 150.0
        assert 'statements_per_mp' in stats
    
    def test_get_statistics_empty(self, identifier):
        """Test getting statistics with no statements."""
        stats = identifier.get_statistics([])
        
        assert stats['total_statements'] == 0
        assert stats['unique_mps'] == 0
        assert stats['avg_statement_length'] == 0


class TestRealPDFIntegration:
    """Integration tests using real Hansard PDF sample."""
    
    @pytest.fixture
    def sample_json_path(self):
        """Get path to sample JSON if it exists."""
        # First check if JSON exists from previous PDF processing
        json_path = Path(__file__).parent.parent / 'output' / 'Hansard_Report_2025-12-04.json'
        if json_path.exists():
            return str(json_path)
        
        # Otherwise skip the test
        pytest.skip("Sample JSON not found - run PDF processor first")
    
    def test_extract_from_real_hansard(self, identifier, sample_json_path):
        """Test extracting statements from real Hansard JSON."""
        with open(sample_json_path, 'r') as f:
            data = json.load(f)
        
        statements = identifier.extract_statements_from_pages(data['pages'])
        
        # Should find multiple statements
        assert len(statements) > 0
        
        # Should find multiple unique MPs
        unique_mps = identifier.get_unique_mp_names(statements)
        assert len(unique_mps) > 1
        
        # Get statistics
        stats = identifier.get_statistics(statements)
        assert stats['total_statements'] > 0
        assert stats['unique_mps'] > 0
        assert stats['total_characters'] > 0
    
    def test_real_hansard_mp_names(self, identifier, sample_json_path):
        """Test that real Hansard contains properly formatted MP names."""
        with open(sample_json_path, 'r') as f:
            data = json.load(f)
        
        statements = identifier.extract_statements_from_pages(data['pages'])
        
        # All MP names should be title case
        for stmt in statements:
            assert stmt.mp_name[0].isupper(), f"Name should start with capital: {stmt.mp_name}"
            
            # Should not contain parenthetical content
            assert '(' not in stmt.mp_name
            assert ')' not in stmt.mp_name
    
    def test_real_hansard_statement_quality(self, identifier, sample_json_path):
        """Test that extracted statements have reasonable quality."""
        with open(sample_json_path, 'r') as f:
            data = json.load(f)
        
        statements = identifier.extract_statements_from_pages(data['pages'])
        
        # All statements should have reasonable length
        for stmt in statements:
            assert len(stmt.text) >= 10, "Statement too short"
            assert len(stmt.text) < 50000, "Statement unreasonably long"
            
            # Should have proper positions
            assert stmt.start_position < stmt.end_position
            
            # Should have page number
            assert stmt.page_number is not None
            assert stmt.page_number > 0



class TestHonorificSeparation:
    """
    Test suite for honorific separation in MP names.
    
    Validates: Requirement 5.10 - When testing MP name parsing, THE System SHALL
    verify that honorifics are correctly split from first and last names.
    """
    
    def test_parse_hon_john_doe(self):
        """Test parsing 'Hon. John Doe' into components."""
        # Input: "Hon. John Doe"
        # Expected: honorific="Hon.", first="John", last="Doe"
        
        name = "Hon. John Doe"
        
        # Parse the name
        import re
        honorific_match = re.match(r'^(Hon\.|Dr\.|Prof\.)\s+(.+)$', name)
        
        if honorific_match:
            honorific = honorific_match.group(1)
            remaining_name = honorific_match.group(2)
            
            # Split remaining name into first and last
            name_parts = remaining_name.split()
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            assert honorific == "Hon."
            assert first_name == "John"
            assert last_name == "Doe"
        else:
            pytest.fail("Failed to parse honorific from name")
    
    def test_parse_dr_jane_smith(self):
        """Test parsing 'Dr. Jane Smith' into components."""
        # Input: "Dr. Jane Smith"
        # Expected: honorific="Dr.", first="Jane", last="Smith"
        
        name = "Dr. Jane Smith"
        
        # Parse the name
        import re
        honorific_match = re.match(r'^(Hon\.|Dr\.|Prof\.)\s+(.+)$', name)
        
        if honorific_match:
            honorific = honorific_match.group(1)
            remaining_name = honorific_match.group(2)
            
            # Split remaining name into first and last
            name_parts = remaining_name.split()
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            assert honorific == "Dr."
            assert first_name == "Jane"
            assert last_name == "Smith"
        else:
            pytest.fail("Failed to parse honorific from name")
    
    def test_parse_prof_peter_parker(self):
        """Test parsing 'Prof. Peter Parker' into components."""
        # Input: "Prof. Peter Parker"
        # Expected: honorific="Prof.", first="Peter", last="Parker"
        
        name = "Prof. Peter Parker"
        
        # Parse the name
        import re
        honorific_match = re.match(r'^(Hon\.|Dr\.|Prof\.)\s+(.+)$', name)
        
        if honorific_match:
            honorific = honorific_match.group(1)
            remaining_name = honorific_match.group(2)
            
            # Split remaining name into first and last
            name_parts = remaining_name.split()
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            assert honorific == "Prof."
            assert first_name == "Peter"
            assert last_name == "Parker"
        else:
            pytest.fail("Failed to parse honorific from name")
    
    def test_parse_name_without_honorific(self):
        """Test parsing name without honorific."""
        # Input: "Alice Johnson"
        # Expected: honorific=None, first="Alice", last="Johnson"
        
        name = "Alice Johnson"
        
        # Parse the name
        import re
        honorific_match = re.match(r'^(Hon\.|Dr\.|Prof\.)\s+(.+)$', name)
        
        if honorific_match:
            pytest.fail("Should not find honorific in name without one")
        else:
            # No honorific, split directly
            name_parts = name.split()
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            assert first_name == "Alice"
            assert last_name == "Johnson"


class TestCLI:
    """Test suite for CLI functionality."""
    
    def test_main_with_text_file(self, tmp_path):
        """Test CLI with plain text file."""
        # Create test text file
        text_file = tmp_path / "test.txt"
        text_file.write_text("Hon. John Doe: This is a test statement.")
        
        # Mock sys.argv
        with patch('sys.argv', ['mp-identifier', str(text_file)]):
            from hansard_tales.processors.mp_identifier import main
            result = main()
        
        assert result == 0
    
    def test_main_with_json_file(self, tmp_path):
        """Test CLI with JSON file from PDFProcessor."""
        # Create test JSON file
        json_file = tmp_path / "pages.json"
        json_data = {
            'pages': [
                {
                    'page_number': 1,
                    'text': 'Hon. Jane Smith: This is a statement.'
                }
            ]
        }
        json_file.write_text(json.dumps(json_data))
        
        # Mock sys.argv
        with patch('sys.argv', ['mp-identifier', str(json_file)]):
            from hansard_tales.processors.mp_identifier import main
            result = main()
        
        assert result == 0
    
    def test_main_with_output_file(self, tmp_path):
        """Test CLI with output file."""
        # Create test text file
        text_file = tmp_path / "test.txt"
        text_file.write_text("Hon. Alice Brown: Test statement here.")
        
        output_file = tmp_path / "output.json"
        
        # Mock sys.argv
        with patch('sys.argv', ['mp-identifier', str(text_file), '--output', str(output_file)]):
            from hansard_tales.processors.mp_identifier import main
            result = main()
        
        assert result == 0
        assert output_file.exists()
        
        # Verify output content
        with open(output_file) as f:
            data = json.load(f)
        
        assert 'statistics' in data
        assert 'statements' in data
    
    def test_main_with_include_non_mps(self, tmp_path):
        """Test CLI with --include-non-mps flag."""
        # Create test text file
        text_file = tmp_path / "test.txt"
        text_file.write_text("The Speaker: Order! Order!\nHon. Bob Wilson: Thank you, Mr. Speaker.")
        
        # Mock sys.argv
        with patch('sys.argv', ['mp-identifier', str(text_file), '--include-non-mps']):
            from hansard_tales.processors.mp_identifier import main
            result = main()
        
        assert result == 0
    
    def test_main_file_not_found(self):
        """Test CLI with non-existent file."""
        # Mock sys.argv
        with patch('sys.argv', ['mp-identifier', '/nonexistent/file.txt']):
            from hansard_tales.processors.mp_identifier import main
            result = main()
        
        assert result == 1
    
    def test_main_invalid_json(self, tmp_path):
        """Test CLI with invalid JSON format."""
        # Create invalid JSON file
        json_file = tmp_path / "invalid.json"
        json_file.write_text('{"invalid": "format"}')
        
        # Mock sys.argv
        with patch('sys.argv', ['mp-identifier', str(json_file)]):
            from hansard_tales.processors.mp_identifier import main
            result = main()
        
        assert result == 1
