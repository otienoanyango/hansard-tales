"""
Property-based test for pagination limits in tests.

This module validates that all scraping operations in tests
respect the max_pages=1 limit to ensure fast test execution.
"""

import ast
import inspect
from pathlib import Path
from typing import List, Tuple

import pytest
from hypothesis import given, settings, strategies as st


class TestPaginationLimitsProperty:
    """Property-based tests for test pagination limits."""
    
    def _find_test_files(self) -> List[Path]:
        """Find all test files in the tests directory."""
        tests_dir = Path(__file__).parent.parent
        test_files = []
        
        # Find all test_*.py files
        for test_file in tests_dir.rglob('test_*.py'):
            # Skip this file
            if test_file.name == 'test_pagination_limits_property.py':
                continue
            test_files.append(test_file)
        
        return test_files
    
    def _extract_scrape_all_calls(self, file_path: Path) -> List[Tuple[int, str, int]]:
        """
        Extract all scrape_all() calls from a test file.
        
        Returns:
            List of (line_number, function_name, max_pages_value) tuples
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            calls = []
            
            class ScrapeAllVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.current_function = None
                    self.calls = []
                
                def visit_FunctionDef(self, node):
                    # Track current function name
                    old_function = self.current_function
                    self.current_function = node.name
                    self.generic_visit(node)
                    self.current_function = old_function
                
                def visit_Call(self, node):
                    # Check if this is a scrape_all() call
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr == 'scrape_all':
                            # Extract max_pages value
                            max_pages = None
                            
                            # Check keyword arguments
                            for keyword in node.keywords:
                                if keyword.arg == 'max_pages':
                                    if isinstance(keyword.value, ast.Constant):
                                        max_pages = keyword.value.value
                                    elif isinstance(keyword.value, ast.Num):  # Python 3.7 compatibility
                                        max_pages = keyword.value.n
                            
                            # If max_pages not found, it's using default (not ideal for tests)
                            if max_pages is None:
                                max_pages = -1  # Sentinel value for "not specified"
                            
                            self.calls.append((
                                node.lineno,
                                self.current_function or '<module>',
                                max_pages
                            ))
                    
                    self.generic_visit(node)
            
            visitor = ScrapeAllVisitor()
            visitor.visit(tree)
            calls = visitor.calls
            
            return calls
        
        except Exception as e:
            # If we can't parse the file, skip it
            return []
    
    def test_pagination_limits_in_tests(self):
        """
        Property 6: Test Pagination Limits
        
        For all test files that call scrape_all(), the max_pages parameter
        should be set to 1 to ensure fast test execution.
        
        Exception: Tests that specifically test pagination behavior
        (e.g., test_pagination.py, tests named *pagination*, *max_pages*)
        are allowed to use max_pages > 1.
        
        Validates: Requirements 5.6
        
        Requirement 5.6: WHEN scraping in tests, THE System SHALL limit 
        scraping to the first page only to avoid excessive test duration.
        """
        test_files = self._find_test_files()
        violations = []
        
        # Tests that are allowed to use max_pages > 1 (testing pagination behavior)
        pagination_test_patterns = [
            'test_pagination',
            'pagination',
            'max_pages',
            'multiple_pages',
            'stop_on_empty',
            'stop_when_outside'
        ]
        
        for test_file in test_files:
            calls = self._extract_scrape_all_calls(test_file)
            
            for line_num, func_name, max_pages in calls:
                # Check if this is a pagination-specific test (allowed exception)
                is_pagination_test = any(
                    pattern in test_file.name.lower() or pattern in func_name.lower()
                    for pattern in pagination_test_patterns
                )
                
                # Skip pagination-specific tests
                if is_pagination_test:
                    continue
                
                # Check if max_pages is set to 1
                if max_pages != 1:
                    relative_path = test_file.relative_to(Path(__file__).parent.parent)
                    
                    if max_pages == -1:
                        violation_msg = (
                            f"{relative_path}:{line_num} in {func_name}() - "
                            f"scrape_all() called without max_pages parameter. "
                            f"Should use max_pages=1 for fast test execution."
                        )
                    else:
                        violation_msg = (
                            f"{relative_path}:{line_num} in {func_name}() - "
                            f"scrape_all() called with max_pages={max_pages}. "
                            f"Should use max_pages=1 for fast test execution."
                        )
                    
                    violations.append(violation_msg)
        
        # Assert no violations found
        if violations:
            violation_report = "\n\nPagination limit violations found:\n" + "\n".join(
                f"  - {v}" for v in violations
            )
            violation_report += (
                "\n\nRequirement 5.6: All test scraping operations should use max_pages=1 "
                "to avoid excessive test duration."
                "\n\nNote: Tests specifically testing pagination behavior are exempt from this requirement."
            )
            pytest.fail(violation_report)
    
    @given(
        max_pages=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=20, deadline=None)
    def test_scraper_respects_max_pages_limit_property(self, max_pages):
        """
        Property 6 (Extended): Scraper Respects max_pages Limit
        
        For any max_pages value, the scraper should never scrape more than
        max_pages pages, even if more pages are available.
        
        This validates that the max_pages parameter correctly limits
        the number of pages scraped.
        
        Validates: Requirements 5.6 (indirectly - validates the mechanism works)
        """
        import tempfile
        from unittest.mock import Mock, patch
        from hansard_tales.scrapers.hansard_scraper import HansardScraper
        from hansard_tales.storage.filesystem import FilesystemStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create scraper
            storage = FilesystemStorage(tmpdir)
            
            # Mock the scrape_hansard_page method to always return results
            # This simulates infinite pages available
            with patch.object(HansardScraper, 'scrape_hansard_page') as mock_scrape:
                mock_scrape.return_value = [
                    {'url': 'http://test.com/test.pdf', 'title': 'Test', 'date': '2024-01-01'}
                ]
                
                scraper = HansardScraper(storage=storage)
                
                # Scrape with the given max_pages
                results = scraper.scrape_all(max_pages=max_pages)
                
                # Verify that scrape_hansard_page was called at most max_pages times
                call_count = mock_scrape.call_count
                
                # The scraper should respect the max_pages limit
                assert call_count <= max_pages, (
                    f"Scraper called scrape_hansard_page {call_count} times, "
                    f"but max_pages was set to {max_pages}. "
                    f"The scraper should never exceed the max_pages limit."
                )
                
                # For this test, since we always return results, it should call exactly max_pages times
                assert call_count == max_pages, (
                    f"Scraper called scrape_hansard_page {call_count} times, "
                    f"but should have called it exactly {max_pages} times "
                    f"(since pages always have results in this test)."
                )


    
    def test_pagination_limits_documentation(self):
        """
        Verify that pagination limits are documented in test guidelines.
        
        This test ensures that the testing guidelines document the
        requirement to use max_pages=1 in tests.
        
        Validates: Requirements 5.6, 10.2
        """
        # Check if testing guidelines exist
        guidelines_paths = [
            Path(__file__).parent.parent.parent / '.kiro' / 'steering' / 'testing-guidelines.md',
            Path(__file__).parent.parent.parent / 'docs' / 'TESTING_PATTERNS.md',
            Path(__file__).parent.parent / 'fixtures' / 'README.md'
        ]
        
        found_documentation = False
        
        for guidelines_path in guidelines_paths:
            if guidelines_path.exists():
                with open(guidelines_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if pagination limits are mentioned
                if 'max_pages' in content.lower() or 'pagination' in content.lower():
                    found_documentation = True
                    break
        
        # We should have documentation about pagination limits
        assert found_documentation, (
            "Testing guidelines should document the requirement to use max_pages=1 "
            "in test scraping operations. Add documentation to testing-guidelines.md "
            "or TESTING_PATTERNS.md explaining why tests should limit pagination."
        )
