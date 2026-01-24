# Contract Tests

## Purpose

Contract tests validate that our mock data and test fixtures match the actual structure of production data from parliament.go.ke. They serve as an early warning system when the external system changes.

## What Are Contract Tests?

Contract tests are different from unit tests and integration tests:

- **Unit Tests**: Test individual functions with realistic data
- **Integration Tests**: Test multiple components working together
- **Contract Tests**: Validate assumptions about external systems

## Structure

```
tests/contract/
├── __init__.py                    # Package initialization
├── README.md                      # This file
├── test_html_structure.py         # HTML structure contract tests (Task 8.2)
├── test_date_formats.py           # Date format contract tests (Task 8.3)
└── test_pdf_links.py              # PDF link contract tests (Task 8.4)
```

## When to Run Contract Tests

### During Development
Run contract tests separately to verify assumptions:
```bash
pytest tests/contract/ -v
```

### In CI/CD
Contract tests should run as part of the full test suite:
```bash
pytest  # Runs all tests including contract tests
```

### When Fixtures Are Updated
After capturing new HTML samples from parliament.go.ke:
```bash
pytest tests/contract/ -v
```

## What Contract Tests Validate

### HTML Structure (test_html_structure.py)
- Hansard list pages contain PDF links
- PDF link text contains date information
- PDF links are relative URLs
- Pagination structure is present
- Expected HTML elements exist

### Date Formats (test_date_formats.py)
- British date formats parse correctly
- Date patterns match expected formats
- Ordinal suffixes are handled (1st, 2nd, 3rd, 4th)
- Day names are present (Monday, Tuesday, etc.)
- Month names are spelled correctly

### PDF Links (test_pdf_links.py)
- PDF URLs follow expected patterns
- Link text contains session information
- File paths match expected structure
- URL encoding is consistent

## When Contract Tests Fail

Contract test failures indicate one of two things:

1. **Parliament.go.ke Changed**: The external system structure changed
   - Update fixtures in `tests/fixtures/` to match new structure
   - Update contract tests if assumptions changed
   - Update scraper code if necessary

2. **Test Bug**: The contract test itself has a bug
   - Fix the contract test
   - Verify against real parliament.go.ke data

## Maintenance

### Updating Fixtures
When parliament.go.ke changes:

1. Capture new HTML samples from the live site
2. Update `tests/fixtures/html_samples.py`
3. Run contract tests: `pytest tests/contract/ -v`
4. Fix any failures by updating mocks or scraper code
5. Document the change in fixtures/README.md

### Adding New Contract Tests
When adding new assumptions about parliament.go.ke:

1. Add the assumption to the appropriate contract test file
2. Document what the test validates
3. Include clear error messages for failures
4. Add examples of valid and invalid structures

## Example Contract Test

```python
def test_hansard_list_has_pdf_links():
    """
    Contract: Hansard list page must contain PDF links.
    
    This validates that our assumption about the page structure
    is still valid. If this fails, parliament.go.ke changed.
    """
    html = ParliamentHTMLSamples.HANSARD_LIST_PAGE
    soup = BeautifulSoup(html, 'html.parser')
    
    links = soup.find_all('a', href=True)
    pdf_links = [link for link in links if '.pdf' in link['href'].lower()]
    
    assert len(pdf_links) > 0, (
        "Contract violation: Hansard list page must contain PDF links. "
        "Parliament.go.ke may have changed its structure."
    )
```

## Benefits

1. **Early Detection**: Catch external system changes before they break production
2. **Clear Failures**: Know exactly what changed when tests fail
3. **Documentation**: Contract tests document our assumptions
4. **Confidence**: Know that mocks match reality

## Related Documentation

- `tests/fixtures/README.md` - Documentation of test fixtures
- `.kiro/specs/test-calibration-and-integration-fixes/design.md` - Design document
- `.kiro/specs/test-calibration-and-integration-fixes/requirements.md` - Requirements

## Requirements Validated

Contract tests validate the following requirements:

- **Requirement 2.2**: Mock data validation and contract testing
- **Requirement 9.1**: HTML structure contract tests
- **Requirement 9.2**: PDF link format contract tests
- **Requirement 9.3**: Date format contract tests
- **Requirement 9.5**: Separate contract test execution
