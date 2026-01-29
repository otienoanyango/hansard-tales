# ADR 004: Use CSS Selectors for Web Scraping

## Status

Accepted

## Context

The Hansard Tales system needs to scrape parliamentary documents from parliament.go.ke. We need to extract PDF links from HTML pages reliably and maintainably.

Options for HTML parsing:

- **CSS Selectors**: Concise, readable, widely understood
- **XPath**: Powerful, complex, harder to read
- **Regex**: Fast, brittle, error-prone
- **Manual parsing**: Full control, high maintenance

## Decision

We will use **CSS selectors with BeautifulSoup** for all web scraping.

### Rationale

**CSS Selectors Advantages:**
- **Readable**: `table.cols-2 td.views-field-field-pdf a[href$=".pdf"]`
- **Maintainable**: Easy to update when HTML changes
- **Familiar**: Most developers know CSS selectors
- **Precise**: Can target exact elements
- **Testable**: Easy to verify in browser DevTools
- **Robust**: Less brittle than regex

**BeautifulSoup Advantages:**
- Standard Python library for HTML parsing
- Excellent CSS selector support via `.select()`
- Handles malformed HTML gracefully
- Good error messages
- Well-documented

### Example

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, 'html.parser')

# Extract PDF links from specific table
pdf_links = soup.select('table.cols-2 td.views-field-field-pdf a[href$=".pdf"]')

for link in pdf_links:
    url = link.get('href')
    print(url)
```

## Consequences

### Positive

- **Maintainability**: Selectors are easy to read and update
- **Reliability**: CSS selectors are more stable than regex
- **Debugging**: Can test selectors in browser DevTools
- **Documentation**: Selectors serve as documentation
- **Fail Fast**: If HTML structure changes, selectors return empty (not wrong data)

### Negative

- **Performance**: Slightly slower than regex (negligible for our use case)
- **Dependency**: Requires BeautifulSoup library
  - Mitigation: BeautifulSoup is standard and stable

### Neutral

- **Learning Curve**: Developers need to know CSS selectors
  - Mitigation: CSS selectors are widely known

## Design Patterns

### Specific Table Targeting

```python
# Target specific table by class
pdf_links = soup.select('table.cols-2 td.views-field-field-pdf a[href$=".pdf"]')
```

### Pagination Detection

```python
# Find pagination element
pager = soup.select_one('nav.pager, ul.pager, div.pager')

# Extract page numbers
page_links = pager.select('a') if pager else []
```

### Fallback Selectors

```python
# Try multiple selectors
pdf_links = (
    soup.select('table.cols-2 td.views-field-field-pdf a[href$=".pdf"]') or
    soup.select('td.views-field-field-pdf a[href$=".pdf"]') or
    soup.select('a[href$=".pdf"]')
)
```

## Error Handling

### Fail Fast on HTML Changes

```python
urls = self._extract_urls_from_page(soup)

if not urls:
    raise DataCollectionError(
        f"No documents found at {url}. "
        "This may indicate that the website structure has changed."
    )
```

This ensures we detect HTML changes immediately rather than silently failing.

### Selector Validation

Document selectors in code comments:

```python
def _extract_urls_from_page(self, soup: BeautifulSoup) -> List[str]:
    """
    Extract PDF URLs from a single page using CSS selectors.

    Selector: table.cols-2 td.views-field-field-pdf a[href$=".pdf"]

    This targets:
    - table with class "cols-2"
    - td with class "views-field-field-pdf"
    - a tags with href ending in ".pdf"
    """
    pdf_links = soup.select('table.cols-2 td.views-field-field-pdf a[href$=".pdf"]')
    ...
```

## Testing Strategy

### Unit Tests

```python
def test_extract_urls_from_page():
    html = '''
    <table class="cols-2">
        <tr>
            <td class="views-field-field-pdf">
                <a href="/files/hansard.pdf">Hansard</a>
            </td>
        </tr>
    </table>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    urls = scraper._extract_urls_from_page(soup)
    assert len(urls) == 1
    assert urls[0].endswith('hansard.pdf')
```

### Integration Tests

Test against real HTML (saved snapshots):

```python
def test_extract_urls_from_real_page():
    with open('tests/fixtures/hansard_page.html') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    urls = scraper._extract_urls_from_page(soup)
    assert len(urls) > 0
```

## Comparison with XPath

| Aspect | CSS Selector | XPath |
|--------|-------------|-------|
| Readability | ✅ High | ❌ Low |
| Learning curve | ✅ Easy | ❌ Steep |
| Power | ✅ Sufficient | ✅ More powerful |
| Browser support | ✅ Native | ⚠️ Via JS |
| Python support | ✅ BeautifulSoup | ✅ lxml |

For our use case, CSS selectors provide sufficient power with better readability.

## References

- [CSS Selectors Reference](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Web Scraping Best Practices](https://www.scrapingbee.com/blog/web-scraping-best-practices/)

## Related ADRs

- [ADR 005: Standardized Filename Generation](005-standardized-filenames.md)

## Date

2025-01-15
