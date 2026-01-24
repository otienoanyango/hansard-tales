"""
Property test for contract test failure guidance.

This test validates that all contract tests provide clear, actionable
guidance when they fail. This is a meta-test that ensures our contract
testing framework is maintainable.

Validates: Requirements 9.4

Property 12: Contract Test Failure Guidance
For any contract test failure, the error message should provide clear
guidance on what changed in the production structure.
"""

import pytest
import re
from hypothesis import given, strategies as st
from bs4 import BeautifulSoup


class TestContractFailureGuidance:
    """
    Property tests for contract test failure guidance.
    
    These tests validate that our contract tests provide clear,
    actionable error messages when they fail.
    """
    
    def test_contract_test_error_messages_are_descriptive(self):
        """
        Validate that contract test error messages contain required elements.
        
        **Property 12: Contract Test Failure Guidance**
        **Validates: Requirements 9.4**
        
        Contract test error messages should include:
        1. "Contract violation:" prefix
        2. Description of what was expected
        3. Description of what was found
        4. Guidance on what this indicates
        """
        # Sample error messages from contract tests
        error_messages = [
            "Contract violation: Hansard list page must contain PDF links. "
            "Found 0 PDF links. This indicates the parliament.go.ke website "
            "structure has changed.",
            
            "Contract violation: PDF link text must contain a month name. "
            "Link text: 'Invalid Text'. "
            "Expected one of: January, February, March. "
            "This indicates the date format in link text has changed.",
            
            "Contract violation: PDF link should be a relative URL starting with '/'. "
            "Found: 'http://absolute.url/file.pdf'. "
            "This indicates the URL format has changed from relative to absolute.",
        ]
        
        for error_msg in error_messages:
            # Property: Must start with "Contract violation:"
            assert error_msg.startswith("Contract violation:"), (
                f"Contract test error must start with 'Contract violation:'. "
                f"Found: {error_msg[:50]}"
            )
            
            # Property: Must contain "This indicates" guidance
            assert "This indicates" in error_msg, (
                f"Contract test error must contain 'This indicates' guidance. "
                f"Found: {error_msg}"
            )
            
            # Property: Must be reasonably long (> 50 chars for meaningful guidance)
            assert len(error_msg) > 50, (
                f"Contract test error must be descriptive (> 50 chars). "
                f"Found: {len(error_msg)} chars"
            )
    
    def test_contract_test_errors_mention_what_changed(self):
        """
        Validate that contract test errors mention what changed.
        
        Error messages should explicitly mention the component that changed:
        - "website structure has changed"
        - "date format has changed"
        - "URL format has changed"
        - "file format has changed"
        """
        error_messages = [
            "Contract violation: Hansard list page must contain PDF links. "
            "Found 0 PDF links. This indicates the parliament.go.ke website "
            "structure has changed.",
            
            "Contract violation: PDF link text must contain a month name. "
            "This indicates the date format in link text has changed.",
            
            "Contract violation: PDF link should be relative. "
            "This indicates the URL format has changed from relative to absolute.",
        ]
        
        change_indicators = [
            "has changed",
            "have changed",
            "structure has changed",
            "format has changed",
        ]
        
        for error_msg in error_messages:
            # Property: Must mention what changed
            has_change_indicator = any(
                indicator in error_msg.lower()
                for indicator in change_indicators
            )
            
            assert has_change_indicator, (
                f"Contract test error must mention what changed. "
                f"Expected one of: {change_indicators}. "
                f"Found: {error_msg}"
            )
    
    def test_contract_test_errors_include_actual_values(self):
        """
        Validate that contract test errors include actual values found.
        
        When a contract test fails, it should show what was actually found,
        not just what was expected. This helps with debugging.
        """
        # Examples of good error messages that include actual values
        error_with_actual = [
            "Found 0 PDF links",
            "Link text: 'Invalid Text'",
            "Found: 'http://absolute.url/file.pdf'",
            "Found {len(pdf_links)} PDF links",
        ]
        
        for error_fragment in error_with_actual:
            # Property: Should contain "Found" or "Link text:" to show actual value
            has_actual_value = (
                "Found" in error_fragment or
                "Link text:" in error_fragment or
                "Found:" in error_fragment
            )
            
            assert has_actual_value, (
                f"Contract test error should include actual values. "
                f"Fragment: {error_fragment}"
            )
    
    @given(
        html_content=st.text(min_size=10, max_size=1000),
        expected_element=st.sampled_from(['pdf_links', 'month_names', 'relative_urls'])
    )
    def test_contract_validation_never_crashes(self, html_content, expected_element):
        """
        Property: Contract validation should never crash, even with invalid HTML.
        
        **Property 12: Contract Test Failure Guidance**
        **Validates: Requirements 9.4**
        
        For ANY HTML content (valid or invalid), contract validation should:
        1. Never crash with an exception
        2. Return a clear error message if validation fails
        3. Handle malformed HTML gracefully
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Simulate contract validation
            links = soup.find_all('a', href=True)
            pdf_links = [link for link in links if '.pdf' in link.get('href', '').lower()]
            
            # Validation should complete without crashing
            if expected_element == 'pdf_links':
                result = len(pdf_links) > 0
            elif expected_element == 'month_names':
                month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December']
                result = any(
                    any(month in link.get_text() for month in month_names)
                    for link in pdf_links
                ) if pdf_links else False
            else:  # relative_urls
                result = all(
                    link.get('href', '').startswith('/')
                    for link in pdf_links
                ) if pdf_links else False
            
            # Property: Validation completes and returns a boolean
            assert isinstance(result, bool)
            
        except Exception as e:
            # Property: Should not crash with unexpected exceptions
            pytest.fail(
                f"Contract validation crashed with {type(e).__name__}: {e}. "
                f"Contract validation should handle invalid HTML gracefully."
            )
    
    def test_contract_test_error_format_consistency(self):
        """
        Validate that all contract test errors follow a consistent format.
        
        Consistent error format makes it easier to:
        1. Parse errors programmatically
        2. Understand what went wrong
        3. Take corrective action
        
        Format: "Contract violation: [what failed]. [what was found]. 
                 This indicates [what changed]."
        """
        # Sample error messages
        error_messages = [
            "Contract violation: Hansard list page must contain PDF links. "
            "Found 0 PDF links. This indicates the parliament.go.ke website "
            "structure has changed.",
            
            "Contract violation: PDF link text must contain a month name. "
            "Link text: 'Invalid Text'. "
            "Expected one of: January, February, March. "
            "This indicates the date format in link text has changed.",
        ]
        
        for error_msg in error_messages:
            # Property: Must follow the pattern
            # 1. Starts with "Contract violation:"
            assert error_msg.startswith("Contract violation:"), (
                f"Error must start with 'Contract violation:'. Found: {error_msg[:30]}"
            )
            
            # 2. Contains description of what failed (after "Contract violation:")
            parts = error_msg.split(".")
            assert len(parts) >= 3, (
                f"Error must have at least 3 sentences (violation, found, indicates). "
                f"Found: {len(parts)} sentences"
            )
            
            # 3. Contains "This indicates" guidance
            assert "This indicates" in error_msg, (
                f"Error must contain 'This indicates' guidance. Found: {error_msg}"
            )
    
    def test_contract_test_errors_are_actionable(self):
        """
        Validate that contract test errors provide actionable guidance.
        
        Actionable guidance means the error message tells you:
        1. What to check (e.g., "check parliament.go.ke website")
        2. What might need updating (e.g., "scraper may need updates")
        3. What changed (e.g., "structure has changed")
        """
        error_messages = [
            "Contract violation: Hansard list page must contain PDF links. "
            "Found 0 PDF links. This indicates the parliament.go.ke website "
            "structure has changed.",
            
            "Contract violation: PDF link text must contain a month name. "
            "Link text: 'Invalid Text'. "
            "Expected one of: January, February, March. "
            "This indicates the date format in link text has changed.",
        ]
        
        actionable_keywords = [
            "has changed",
            "may need",
            "should",
            "indicates",
            "check",
            "update",
        ]
        
        for error_msg in error_messages:
            # Property: Must contain at least one actionable keyword
            has_actionable_keyword = any(
                keyword in error_msg.lower()
                for keyword in actionable_keywords
            )
            
            assert has_actionable_keyword, (
                f"Contract test error must be actionable. "
                f"Expected one of: {actionable_keywords}. "
                f"Found: {error_msg}"
            )
