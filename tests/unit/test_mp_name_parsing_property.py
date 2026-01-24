"""
Property-based tests for MP name parsing.

Property 8: MP Name Parsing
For any MP name string containing honorifics (Hon., Dr., Prof., etc.),
parsing should correctly separate the honorific from the first and last names.

Validates: Requirements 5.10
"""

import re
import pytest
from hypothesis import given, strategies as st, example


# Name parsing function (extracted from test logic)
def parse_mp_name(name: str) -> dict:
    """
    Parse MP name into components.
    
    Args:
        name: Full name string (e.g., "Hon. John Doe")
        
    Returns:
        Dictionary with keys: honorific, first_name, last_name
        - honorific: The honorific title or None
        - first_name: First name
        - last_name: Last name (may be empty string or multi-part)
    """
    # Try to match honorific pattern (case-insensitive)
    honorific_match = re.match(
        r'^(Hon\.|Dr\.|Prof\.)\s+(.+)$',
        name,
        re.IGNORECASE
    )
    
    if honorific_match:
        honorific = honorific_match.group(1)
        remaining_name = honorific_match.group(2)
    else:
        honorific = None
        remaining_name = name
    
    # Split remaining name into first and last
    name_parts = remaining_name.split()
    first_name = name_parts[0] if len(name_parts) > 0 else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
    
    return {
        'honorific': honorific,
        'first_name': first_name,
        'last_name': last_name
    }


class TestMPNameParsingProperty:
    """
    Property-based tests for MP name parsing.
    
    Validates: Requirement 5.10 - When testing MP name parsing, THE System SHALL
    verify that honorifics are correctly split from first and last names.
    """
    
    @given(
        honorific=st.sampled_from(['Hon.', 'Dr.', 'Prof.']),
        first_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
            min_size=2,
            max_size=20
        ).filter(lambda x: ' ' not in x and x.strip() == x),
        last_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
            min_size=2,
            max_size=30
        ).filter(lambda x: x.strip() == x)
    )
    @example(honorific='Hon.', first_name='John', last_name='Doe')
    @example(honorific='Dr.', first_name='Jane', last_name='Smith')
    @example(honorific='Prof.', first_name='Peter', last_name='Parker')
    @example(honorific='Hon.', first_name='Maria', last_name='De La Cruz')
    def test_name_with_honorific_property(self, honorific, first_name, last_name):
        """
        Property: For ANY name with honorific, parsing correctly separates components.
        
        Given a name in format "Honorific FirstName LastName",
        parsing should extract:
        - honorific: The honorific title
        - first_name: The first name
        - last_name: The last name (may contain spaces)
        """
        # Construct full name
        full_name = f"{honorific} {first_name} {last_name}"
        
        # Parse the name
        result = parse_mp_name(full_name)
        
        # Verify honorific is extracted
        assert result['honorific'] is not None, \
            f"Failed to extract honorific from: {full_name}"
        
        # Verify honorific matches (case-insensitive comparison)
        assert result['honorific'].lower() == honorific.lower(), \
            f"Honorific mismatch: expected {honorific}, got {result['honorific']}"
        
        # Verify first name is extracted
        assert result['first_name'] == first_name, \
            f"First name mismatch: expected {first_name}, got {result['first_name']}"
        
        # Verify last name is extracted
        assert result['last_name'] == last_name, \
            f"Last name mismatch: expected {last_name}, got {result['last_name']}"
    
    @given(
        first_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
            min_size=2,
            max_size=20
        ).filter(lambda x: ' ' not in x and x.strip() == x),
        last_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
            min_size=2,
            max_size=30
        ).filter(lambda x: x.strip() == x)
    )
    @example(first_name='Alice', last_name='Johnson')
    @example(first_name='Bob', last_name='Williams')
    def test_name_without_honorific_property(self, first_name, last_name):
        """
        Property: For ANY name without honorific, parsing correctly separates names.
        
        Given a name in format "FirstName LastName" (no honorific),
        parsing should extract:
        - honorific: None
        - first_name: The first name
        - last_name: The last name
        """
        # Construct full name (no honorific)
        full_name = f"{first_name} {last_name}"
        
        # Parse the name
        result = parse_mp_name(full_name)
        
        # Verify no honorific is extracted
        assert result['honorific'] is None, \
            f"Should not find honorific in: {full_name}"
        
        # Verify first name is extracted
        assert result['first_name'] == first_name, \
            f"First name mismatch: expected {first_name}, got {result['first_name']}"
        
        # Verify last name is extracted
        assert result['last_name'] == last_name, \
            f"Last name mismatch: expected {last_name}, got {result['last_name']}"
    
    @given(
        honorific=st.sampled_from(['Hon.', 'Dr.', 'Prof.']),
        single_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
            min_size=2,
            max_size=20
        ).filter(lambda x: ' ' not in x and x.strip() == x)
    )
    @example(honorific='Hon.', single_name='Madonna')
    @example(honorific='Dr.', single_name='Cher')
    def test_single_name_with_honorific_property(self, honorific, single_name):
        """
        Property: For ANY single name with honorific, parsing handles it correctly.
        
        Given a name in format "Honorific SingleName",
        parsing should extract:
        - honorific: The honorific title
        - first_name: The single name
        - last_name: Empty string
        """
        # Construct full name
        full_name = f"{honorific} {single_name}"
        
        # Parse the name
        result = parse_mp_name(full_name)
        
        # Verify honorific is extracted
        assert result['honorific'] is not None, \
            f"Failed to extract honorific from: {full_name}"
        
        # Verify honorific matches
        assert result['honorific'].lower() == honorific.lower(), \
            f"Honorific mismatch: expected {honorific}, got {result['honorific']}"
        
        # Verify single name is in first_name
        assert result['first_name'] == single_name, \
            f"First name mismatch: expected {single_name}, got {result['first_name']}"
        
        # Verify last_name is empty
        assert result['last_name'] == "", \
            f"Last name should be empty, got: {result['last_name']}"
    
    @given(
        honorific=st.sampled_from(['HON.', 'DR.', 'PROF.', 'hon.', 'dr.', 'prof.']),
        first_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
            min_size=2,
            max_size=20
        ).filter(lambda x: ' ' not in x and x.strip() == x),
        last_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
            min_size=2,
            max_size=30
        ).filter(lambda x: x.strip() == x)
    )
    @example(honorific='HON.', first_name='JOHN', last_name='DOE')
    @example(honorific='hon.', first_name='jane', last_name='smith')
    def test_case_insensitive_honorific_property(self, honorific, first_name, last_name):
        """
        Property: For ANY case variation of honorific, parsing works correctly.
        
        The parser should handle honorifics in any case (HON., hon., Hon.)
        and extract them correctly.
        """
        # Construct full name
        full_name = f"{honorific} {first_name} {last_name}"
        
        # Parse the name
        result = parse_mp_name(full_name)
        
        # Verify honorific is extracted (case-insensitive)
        assert result['honorific'] is not None, \
            f"Failed to extract honorific from: {full_name}"
        
        # Verify honorific matches the input (preserves case)
        assert result['honorific'] == honorific, \
            f"Honorific should preserve case: expected {honorific}, got {result['honorific']}"
        
        # Verify names are extracted
        assert result['first_name'] == first_name
        assert result['last_name'] == last_name
    
    def test_parsing_never_crashes(self):
        """
        Property: For ANY string input, parsing never crashes.
        
        The parser should handle any input gracefully, even invalid ones.
        """
        # Test with various edge cases
        test_cases = [
            "",  # Empty string
            " ",  # Whitespace only
            "Hon.",  # Honorific only
            "Hon. ",  # Honorific with trailing space
            " Hon. John Doe",  # Leading space
            "Hon.  John  Doe",  # Multiple spaces
            "Hon.\tJohn\tDoe",  # Tabs
            "Hon.\nJohn\nDoe",  # Newlines
            "123",  # Numbers
            "!@#$%",  # Special characters
            "Hon. John Doe Jr.",  # Suffix
            "Hon. John-Paul Smith",  # Hyphenated
            "Hon. O'Brien",  # Apostrophe
        ]
        
        for test_input in test_cases:
            try:
                result = parse_mp_name(test_input)
                # Should return a dict with the expected keys
                assert isinstance(result, dict)
                assert 'honorific' in result
                assert 'first_name' in result
                assert 'last_name' in result
            except Exception as e:
                pytest.fail(f"Parser crashed on input '{test_input}': {e}")
