# Mock Structure Validation - Property Test Implementation

## Overview

This document describes the implementation of Property 2: Mock Structure Contract Validation for the Hansard Tales test suite.

## Property 2: Mock Structure Contract Validation

**Statement**: For any mock data used in tests (HTML, HTTP responses, fixtures), contract tests should verify the mock structure matches production data structure, and fail with descriptive errors when divergence is detected.

**Validates**: Requirements 2.1, 2.3, 4.5, 8.5

## Implementation

### File: `tests/contract/test_mock_structure_validation.py`

This module implements comprehensive property-based tests that validate all HTML fixtures maintain structural consistency with production parliament.go.ke data.

### Property Tests Implemented

1. **test_all_html_fixtures_are_valid_html**
   - Validates that all HTML fixtures are parseable
   - Ensures proper HTML structure (html, head, body tags)
   - Prevents empty or None fixtures
   - Uses Hypothesis to test all fixture samples

2. **test_html_fixtures_with_pdfs_have_valid_link_structure**
   - Validates PDF link structure matches production
   - Ensures links are relative URLs (start with '/')
   - Verifies links point to .pdf files
   - Checks link text contains month names (British date format)
   - Tests all fixtures that should contain PDF links

3. **test_html_fixtures_are_documented**
   - Ensures all fixtures have source URL documentation
   - Verifies capture date is documented
   - Checks for description comments
   - Enables fixture maintenance when production changes

4. **test_empty_page_fixture_has_no_pdf_links**
   - Validates empty state representation
   - Ensures HANSARD_EMPTY_PAGE has no PDF links
   - Maintains edge case accuracy

5. **test_pagination_fixture_has_pagination_controls**
   - Validates pagination structure matches production
   - Checks for nav.pagination element
   - Verifies ul.pager structure
   - Ensures page links use ?page=N format

6. **test_pdf_links_use_url_encoding**
   - Validates URL encoding in PDF links
   - Ensures special characters are encoded (e.g., %20 for spaces)
   - Matches production parliament.go.ke URL structure

7. **test_all_fixtures_accessible_via_get_sample**
   - Validates consistent API access pattern
   - Ensures all fixtures work with get_sample() method
   - Prevents API inconsistencies

## Test Results

All 7 property tests pass successfully:

```
tests/contract/test_mock_structure_validation.py::TestMockStructureValidation::test_all_html_fixtures_are_valid_html PASSED
tests/contract/test_mock_structure_validation.py::TestMockStructureValidation::test_html_fixtures_with_pdfs_have_valid_link_structure PASSED
tests/contract/test_mock_structure_validation.py::TestMockStructureValidation::test_html_fixtures_are_documented PASSED
tests/contract/test_mock_structure_validation.py::TestMockStructureValidation::test_empty_page_fixture_has_no_pdf_links PASSED
tests/contract/test_mock_structure_validation.py::TestMockStructureValidation::test_pagination_fixture_has_pagination_controls PASSED
tests/contract/test_mock_structure_validation.py::TestMockStructureValidation::test_pdf_links_use_url_encoding PASSED
tests/contract/test_mock_structure_validation.py::TestMockStructureValidation::test_all_fixtures_accessible_via_get_sample PASSED

7 passed in 0.23s
```

## Benefits

1. **Early Detection**: Catches fixture structure issues before they cause test failures
2. **Clear Errors**: Provides descriptive error messages when structure diverges
3. **Maintainability**: Documents expected structure for future updates
4. **Consistency**: Ensures all fixtures follow the same patterns
5. **Production Alignment**: Validates fixtures match real parliament.go.ke structure

## Usage

Run the property tests:

```bash
# Run all mock validation tests
pytest tests/contract/test_mock_structure_validation.py -v

# Run with hypothesis verbosity
pytest tests/contract/test_mock_structure_validation.py -v --hypothesis-show-statistics
```

## Maintenance

When parliament.go.ke structure changes:

1. Property tests will fail with descriptive errors
2. Update HTML fixtures in `tests/fixtures/html_samples.py`
3. Update fixture documentation (source URL, capture date)
4. Re-run property tests to verify fixes
5. Update contract tests if assumptions changed

## Integration with Test Suite

These property tests complement the existing contract tests:

- `test_html_structure.py`: Tests specific HTML structure assumptions
- `test_date_formats.py`: Tests date format assumptions
- `test_pdf_links.py`: Tests PDF link format assumptions
- `test_mock_structure_validation.py`: Tests universal fixture properties (NEW)

Together, they provide comprehensive validation that mocks match production structure.
