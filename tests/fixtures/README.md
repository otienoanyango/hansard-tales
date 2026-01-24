# Test Fixtures: Realistic Data from parliament.go.ke

## Overview

This directory contains realistic test fixtures captured from parliament.go.ke. These fixtures ensure that our tests validate against real-world data structures rather than convenient synthetic data.

## Purpose

**Problem**: Unit tests that pass with synthetic data often fail in integration because the synthetic data doesn't match production reality.

**Solution**: Capture real HTML, date formats, and link structures from parliament.go.ke and use them in tests.

## Directory Structure

```
tests/fixtures/
├── __init__.py           # Module initialization
├── README.md             # This file
├── html_samples.py       # Real HTML from parliament.go.ke
├── date_formats.py       # Real British date formats
└── pdf_metadata.py       # Real PDF link structures
```

## Fixture Modules

### html_samples.py

Contains real HTML samples from parliament.go.ke pages:
- Hansard list pages with PDF links
- Pagination structures
- Navigation elements
- Content sections

**Usage**:
```python
from tests.fixtures.html_samples import ParliamentHTMLSamples

html = ParliamentHTMLSamples.HANSARD_LIST_PAGE
# Use in tests with BeautifulSoup or mock HTTP responses
```

### date_formats.py

Contains real British date formats used in Hansard reports:
- Full date formats with day names (e.g., "Thursday, 4th December 2025")
- Date formats with ordinals (e.g., "15th October 2025")
- Expected ISO format conversions

**Usage**:
```python
from tests.fixtures.date_formats import DateFormatExamples

for british, iso in DateFormatExamples.get_pairs():
    # Test date parsing with real formats
    assert parse_date(british) == iso
```

### pdf_metadata.py

Contains real PDF link structures from parliament.go.ke:
- PDF URL patterns
- Link text patterns
- Metadata structures

**Usage**:
```python
from tests.fixtures.pdf_metadata import PDFLinkExamples

for link in PDFLinkExamples.REAL_LINKS:
    # Test link extraction with real structures
    assert extract_pdf_link(link.html) == link.expected_url
```

## Capturing New Fixtures

### When to Capture

Capture new fixtures when:
1. Adding tests for new features
2. Parliament.go.ke structure changes
3. Contract tests fail indicating structure changes
4. New date formats or link patterns are discovered

### How to Capture

#### 1. Visit parliament.go.ke

Navigate to the relevant page:
- Hansard list: https://parliament.go.ke/the-national-assembly/house-business/hansard
- MP list: https://parliament.go.ke/the-national-assembly/members
- Committee pages: https://parliament.go.ke/the-national-assembly/committees

#### 2. Capture HTML

Use browser developer tools:
1. Right-click on the element → Inspect
2. Right-click on the HTML in DevTools → Copy → Copy outerHTML
3. Paste into the appropriate fixture file

#### 3. Document the Capture

**REQUIRED**: Every fixture must include:
- Source URL
- Capture date (YYYY-MM-DD)
- Description of what the fixture represents
- Any relevant notes about the structure

**Example**:
```python
class ParliamentHTMLSamples:
    """Real HTML samples from parliament.go.ke."""
    
    # Source: https://parliament.go.ke/the-national-assembly/house-business/hansard
    # Captured: 2024-01-15
    # Description: Hansard list page with PDF links for December 2025
    HANSARD_LIST_PAGE = """
    <html>
        <!-- Real HTML here -->
    </html>
    """
```

#### 4. Validate the Fixture

Run contract tests to ensure the fixture matches production:
```bash
pytest tests/contract/ -v
```

### Updating Existing Fixtures

When parliament.go.ke structure changes:

1. **Contract tests will fail** - This is the early warning system
2. **Capture new HTML** from the production site
3. **Update the fixture** with new HTML and update capture date
4. **Update contract tests** if assumptions changed
5. **Verify all tests pass** with the new fixture

**Example Update**:
```python
# OLD (captured 2024-01-15):
HANSARD_LIST_PAGE = """<div class="hansard-list">...</div>"""

# NEW (captured 2024-06-20):
# Note: Structure changed from div.hansard-list to div.reports-list
HANSARD_LIST_PAGE = """<div class="reports-list">...</div>"""
```

## Best Practices

### DO ✅

- **Capture complete structures**: Include parent elements for context
- **Document thoroughly**: Always include source URL and capture date
- **Use real data**: Capture actual dates, names, and links
- **Keep it minimal**: Only include relevant HTML, remove unnecessary elements
- **Update regularly**: Check fixtures quarterly or when contract tests fail
- **Version control**: Commit fixture updates with clear messages

### DON'T ❌

- **Don't create synthetic data**: Always capture from production
- **Don't modify captured HTML**: Keep it as-is from the source
- **Don't remove documentation**: Source URL and date are mandatory
- **Don't capture sensitive data**: Avoid personal information if present
- **Don't capture entire pages**: Focus on relevant sections only

## Fixture Maintenance

### Quarterly Review

Every 3 months:
1. Run contract tests: `pytest tests/contract/ -v`
2. If tests pass: Fixtures are still valid
3. If tests fail: Update fixtures from production

### When Parliament.go.ke Changes

When you notice changes to parliament.go.ke:
1. Contract tests should fail (early warning)
2. Capture new HTML from production
3. Update fixtures with new structure
4. Update contract tests if needed
5. Update any affected unit/integration tests

### Fixture Versioning

If you need to maintain multiple versions:
```python
class ParliamentHTMLSamples:
    # Current version (2024-06-20)
    HANSARD_LIST_PAGE = """..."""
    
    # Legacy version (2024-01-15) - kept for migration tests
    HANSARD_LIST_PAGE_LEGACY = """..."""
```

## Contract Testing

Contract tests validate that fixtures match production assumptions:

```python
# tests/contract/test_html_structure.py

def test_hansard_list_has_pdf_links():
    """Validate that Hansard list page contains PDF links."""
    html = ParliamentHTMLSamples.HANSARD_LIST_PAGE
    soup = BeautifulSoup(html, 'html.parser')
    
    pdf_links = soup.find_all('a', href=lambda h: h and '.pdf' in h.lower())
    assert len(pdf_links) > 0, "Contract violation: No PDF links found"
```

Run contract tests separately:
```bash
pytest tests/contract/ -v
```

## Integration with Tests

### Unit Tests

Use fixtures directly:
```python
from tests.fixtures.html_samples import ParliamentHTMLSamples

def test_pdf_link_extraction():
    """Test PDF link extraction with real HTML."""
    html = ParliamentHTMLSamples.HANSARD_LIST_PAGE
    links = extract_pdf_links(html)
    assert len(links) > 0
```

### Integration Tests

Use fixtures in mocked HTTP responses:
```python
from tests.fixtures.html_samples import ParliamentHTMLSamples

@patch('requests.Session')
def test_scraper_integration(mock_session_class):
    """Test scraper with realistic HTML."""
    mock_session = Mock()
    mock_response = Mock()
    mock_response.text = ParliamentHTMLSamples.HANSARD_LIST_PAGE
    mock_session.get.return_value = mock_response
    mock_session_class.return_value = mock_session
    
    scraper = HansardScraper(storage=storage)
    results = scraper.scrape_hansard_page(1)
    assert len(results) > 0
```

### Property-Based Tests

Use fixtures as examples:
```python
from hypothesis import given, example
from tests.fixtures.date_formats import DateFormatExamples

@given(st.text())
@example(DateFormatExamples.BRITISH_FORMATS[0])  # Use real example
def test_date_parsing_never_crashes(date_string):
    """Date parsing should never crash."""
    result = parse_date(date_string)
    assert result is None or isinstance(result, str)
```

## Troubleshooting

### Contract Tests Failing

**Symptom**: Contract tests fail after parliament.go.ke update

**Solution**:
1. Visit parliament.go.ke and inspect the current structure
2. Capture new HTML with updated structure
3. Update fixtures with new capture date
4. Update contract tests if assumptions changed
5. Verify all tests pass

### Tests Passing Locally but Failing in CI

**Symptom**: Tests pass with fixtures but fail in integration

**Solution**:
1. Verify fixtures are up-to-date (check capture date)
2. Run contract tests to validate assumptions
3. Capture fresh HTML from production
4. Update fixtures if structure changed

### Fixtures Too Large

**Symptom**: Fixture files are becoming unwieldy

**Solution**:
1. Extract only relevant sections of HTML
2. Remove unnecessary attributes (class, style, etc.)
3. Keep only structural elements needed for tests
4. Consider splitting into multiple fixture classes

## Questions?

When in doubt:
1. **Capture from production**: Always use real data
2. **Document thoroughly**: Source URL and date are mandatory
3. **Run contract tests**: Validate fixtures match production
4. **Keep it simple**: Only include what's needed for tests

## Resources

- Parliament.go.ke: https://parliament.go.ke
- Hansard Reports: https://parliament.go.ke/the-national-assembly/house-business/hansard
- Contract Testing Guide: See tests/contract/README.md
- Testing Guidelines: See testing-guidelines.md
