# ADR-001: Hansard Scraper Implementation with CSS Selectors and Pagination

**Status**: Accepted  
**Date**: 2026-01-28  
**Decision Makers**: Development Team  
**Related Requirements**: Requirement 4 (Basic Web Scrapers)

## Context

The Hansard scraper needs to extract PDF links from parliament.go.ke. Initial implementation used generic table parsing with fallbacks, but testing against the live website revealed specific HTML structure that could be leveraged for more reliable extraction.

## Decision

We decided to implement the Hansard scraper with the following approach:

### 1. CSS Selectors for Precise Extraction

Use BeautifulSoup's `.select()` method with specific CSS selectors:
```python
pdf_links = soup.select('table.cols-2 td.views-field-field-pdf a[href$=".pdf"]')
```

**Rationale:**
- More concise than nested `find_all()` calls
- Precisely targets the correct table structure
- Easier to maintain and understand
- Matches actual parliament.go.ke HTML structure

### 2. Pagination Support

Implement automatic pagination to fetch all available documents:
- Detect total pages from pagination element (`nav.pager`)
- Iterate through all pages (zero-indexed)
- Add rate limiting delays between requests

**Rationale:**
- Parliament.go.ke uses pagination (19 pages for 2022 term)
- Single page only returns 25 documents
- Full scrape yields 452 documents across all pages
- Prevents overwhelming the server with rapid requests

### 3. Parliament Term Parameter

Use URL format with parliament term parameter:
```
https://parliament.go.ke/the-national-assembly/house-business/hansard?field_parliament_value=2022&page=0
```

**Rationale:**
- Matches actual parliament.go.ke URL structure
- Allows filtering by parliament term (13th Parliament started 2022)
- Enables future support for historical data from previous terms
- More reliable than scraping without parameters

### 4. Rate Limiting

Add `time.sleep(config.retry_delay)` between page requests.

**Rationale:**
- Prevents server connection issues
- Respectful of parliament.go.ke infrastructure
- Uses existing `retry_delay` configuration (default: 1.0 second)
- Tested successfully with 19 consecutive page requests

## Consequences

### Positive

- **Reliability**: CSS selectors precisely target correct elements
- **Completeness**: Pagination ensures all documents are fetched
- **Maintainability**: Concise code is easier to understand and modify
- **Performance**: Efficient extraction with minimal parsing overhead
- **Verified**: Successfully tested against live website (452 PDFs)

### Negative

- **Brittleness**: CSS selectors are tightly coupled to HTML structure
- **Performance**: Sequential page fetching takes longer (19 seconds with 1s delays)
- **Mitigation**: Fail-fast error handling alerts when HTML structure changes
- **Mitigation**: Rate limiting is necessary to avoid server issues

### Neutral

- Parliament term parameter defaults to 2022 (current term)
- Future enhancement: Support multiple parliament terms
- Future enhancement: Parallel page fetching with connection pooling

## Implementation Details

### Files Modified
- `hansard_tales/scrapers/hansard.py`: Complete rewrite with pagination
- `tests/unit/test_scrapers.py`: Updated 19 tests to match new structure
- `requirements.txt`: Added `beautifulsoup4>=4.12.0` and `requests>=2.31.0`

### Test Coverage
- 19 tests for Hansard scraper
- 98.53% code coverage
- All tests passing
- Includes pagination test with multi-page mock

### Live Verification
```
✓ 452 PDF links from 19 pages
✓ Parliament term: 2022 (13th Parliament)
✓ Date range: January 2022 - December 2025
✓ All URLs properly formatted
```

## Alternatives Considered

### Alternative 1: Generic Table Parsing
- Use `find_all('table')` with keyword filtering
- **Rejected**: Less precise, more prone to false positives

### Alternative 2: XPath Selectors
- Use lxml with XPath expressions
- **Rejected**: CSS selectors are more readable and BeautifulSoup native

### Alternative 3: Parallel Page Fetching
- Use ThreadPoolExecutor for concurrent page requests
- **Deferred**: Adds complexity, may trigger rate limiting

### Alternative 4: No Pagination
- Only fetch first page (25 documents)
- **Rejected**: Incomplete data collection

## References

- Parliament.go.ke Hansard page: https://parliament.go.ke/the-national-assembly/house-business/hansard
- BeautifulSoup CSS selectors: https://www.crummy.com/software/BeautifulSoup/bs4/doc/#css-selectors
- Design 5: Web Scrapers (design.md)
- Requirement 4: Basic Web Scrapers (requirements.md)

## Review Notes

This ADR documents implementation decisions made during development that differ from or extend the original design specifications. The decisions were validated through live testing against parliament.go.ke and comprehensive unit testing.
