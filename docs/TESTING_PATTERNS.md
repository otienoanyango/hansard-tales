# Testing Patterns and Best Practices

## Overview

This document describes the testing patterns used in Hansard Tales, with emphasis on realistic test data, proper mocking, and database schema consistency.

## Core Principles

### 1. Realistic Test Data Pattern

**Problem**: Unit tests that pass with synthetic data often fail in integration because the synthetic data doesn't match production reality.

**Solution**: Use realistic fixtures captured from parliament.go.ke.

**Example**:
```python
# ❌ BAD: Synthetic data
def test_date_extraction_bad():
    # Convenient but unrealistic format
    result = extract_date("2024-01-15")
    assert result == "2024-01-15"

# ✅ GOOD: Realistic data from fixtures
from tests.fixtures.date_formats import DateFormatExamples

def test_date_extraction_good():
    # Real British format from parliament.go.ke
    for british, iso in DateFormatExamples.get_pairs():
        result = extract_date(british)
        assert result == iso
```

### 2. HTTP Mocking Pattern

**Problem**: Mocking after object creation doesn't prevent real network calls.

**Solution**: Mock HTTP dependencies BEFORE creating objects that use them.

**Example**:
```python
# ❌ BAD: Mock after object creation
def test_scraper_bad():
    scraper = HansardScraper(storage=storage)  # Creates real session!
    
    with patch('requests.Session'):  # Too late!
        result = scraper.scrape_hansard_page(1)  # Makes real call

# ✅ GOOD: Mock before object creation
@patch('hansard_tales.scrapers.hansard_scraper.requests.Session')
def test_scraper_good(mock_session_class):
    # Setup mock
    mock_session = Mock()
    mock_response = Mock()
    mock_response.text = ParliamentHTMLSamples.HANSARD_LIST_PAGE
    mock_session.get.return_value = mock_response
    mock_session_class.return_value = mock_session
    
    # NOW create scraper (will use mocked session)
    scraper = HansardScraper(storage=storage)
    result = scraper.scrape_hansard_page(1)
```

### 3. Database Fixture Pattern

**Problem**: Tests creating custom schemas diverge from production schema.

**Solution**: Always use the production database initialization function.

**Example**:
```python
# ❌ BAD: Custom schema
@pytest.fixture
def temp_db_bad():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE mps (name TEXT)")  # Custom schema!
    return conn

# ✅ GOOD: Production schema
@pytest.fixture
def temp_db_good(production_db):
    # Uses production initialize_database() function
    return production_db
```

## Test Categories

### Unit Tests

**Purpose**: Test individual functions with realistic data

**Pattern**:
```python
from tests.fixtures.date_formats import DateFormatExamples

class TestDateExtraction:
    """Unit tests for date extraction."""
    
    def test_british_date_formats(self):
        """Test with real British date formats."""
        for british, iso in DateFormatExamples.get_pairs():
            result = extract_date(british)
            assert result == iso
    
    def test_invalid_date_returns_none(self):
        """Test error handling."""
        result = extract_date("invalid")
        assert result is None
```

**When to use**:
- Testing individual functions
- Testing with realistic data from fixtures
- Testing error handling
- Fast execution (< 0.1s per test)

### Integration Tests

**Purpose**: Test component interactions with minimal mocking

**Pattern**:
```python
class TestScraperIntegration:
    """Integration tests for scraper."""
    
    def test_scrape_and_store(self, temp_workspace, mocked_parliament_http):
        """Test scraper → storage integration."""
        storage = temp_workspace['storage']
        db_path = temp_workspace['db_path']
        
        # Create scraper (uses mocked HTTP)
        scraper = HansardScraper(storage=storage, db_path=str(db_path))
        
        # Scrape first page only
        results = scraper.scrape_all(max_pages=1)
        
        # Verify integration
        assert len(results) > 0
        
        # Verify database was updated
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM downloaded_pdfs")
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count > 0
```

**When to use**:
- Testing multiple components together
- Testing real data flows
- Minimal mocking (only external dependencies)
- Moderate execution time (< 1s per test)

### Contract Tests

**Purpose**: Validate assumptions about external systems

**Pattern**:
```python
from tests.fixtures.html_samples import ParliamentHTMLSamples

class TestHTMLStructureContract:
    """Contract tests for HTML structure."""
    
    def test_hansard_list_has_pdf_links(self):
        """Validate that Hansard list page contains PDF links."""
        html = ParliamentHTMLSamples.HANSARD_LIST_PAGE
        soup = BeautifulSoup(html, 'html.parser')
        
        pdf_links = soup.find_all('a', href=lambda h: h and '.pdf' in h.lower())
        
        assert len(pdf_links) > 0, (
            "Contract violation: Hansard list page must contain PDF links. "
            "Found 0 PDF links. This indicates the parliament.go.ke website "
            "structure has changed."
        )
```

**When to use**:
- Validating fixture accuracy
- Early warning for external system changes
- Documenting assumptions about external systems
- Fast execution (< 0.5s per test)

### Property-Based Tests

**Purpose**: Test universal properties with generated inputs

**Pattern**:
```python
from hypothesis import given, strategies as st

class TestDateParsingProperties:
    """Property-based tests for date parsing."""
    
    @given(st.text())
    def test_date_parsing_never_crashes(self, text):
        """For ANY text, date parsing should never crash."""
        result = extract_date(text)
        assert result is None or isinstance(result, str)
    
    @given(st.dates())
    def test_filename_format_property(self, date):
        """For ANY date, filename should match pattern."""
        filename = generate_filename(date.isoformat(), 'P')
        assert re.match(r'^hansard_\d{8}_P\.pdf$', filename)
```

**When to use**:
- Testing universal invariants
- Finding edge cases automatically
- Large or infinite input spaces
- Complementing unit tests (not replacing them)

## Shared Fixtures

### production_db

**Purpose**: Temporary database with production schema

**Usage**:
```python
def test_database_operation(production_db):
    """Test with production database schema."""
    conn = sqlite3.connect(production_db)
    cursor = conn.cursor()
    
    # All production tables and columns available
    cursor.execute("INSERT INTO mps (name, constituency) VALUES (?, ?)", 
                   ("John Doe", "Test Constituency"))
    conn.commit()
    conn.close()
```

### mocked_parliament_http

**Purpose**: Mock HTTP responses from parliament.go.ke

**Usage**:
```python
def test_with_mocked_http(temp_workspace, mocked_parliament_http):
    """Test with mocked HTTP responses."""
    storage = temp_workspace['storage']
    
    # Scraper will use mocked HTTP (no real network calls)
    scraper = HansardScraper(storage=storage)
    results = scraper.scrape_hansard_page(1)
    
    assert len(results) > 0
```

### temp_workspace

**Purpose**: Temporary workspace with storage and database

**Usage**:
```python
def test_with_workspace(temp_workspace):
    """Test with temporary workspace."""
    storage = temp_workspace['storage']
    db_path = temp_workspace['db_path']
    pdf_dir = temp_workspace['pdf_dir']
    
    # Use storage and database
    scraper = HansardScraper(storage=storage, db_path=str(db_path))
```

## Common Patterns

### Pattern: Comprehensive Test Validation

**Purpose**: Validate file downloads thoroughly

**Pattern**:
```python
def test_download_with_validation(temp_workspace, mocked_parliament_http):
    """Test download with comprehensive validation."""
    storage = temp_workspace['storage']
    db_path = temp_workspace['db_path']
    
    # Mock PDF download
    mock_pdf_response = Mock()
    mock_pdf_response.iter_content = lambda chunk_size: [b'PDF content']
    mocked_parliament_http.get.return_value = mock_pdf_response
    
    # Download PDF
    scraper = HansardScraper(storage=storage, db_path=str(db_path))
    success = scraper.download_pdf('http://test.com/test.pdf', 'Morning', '2024-01-15')
    
    assert success is True
    
    # Validation 1: File exists
    files = storage.list_files('hansard_20240115')
    assert len(files) > 0
    
    # Validation 2: File has content
    content = storage.read(files[0])
    assert len(content) > 0
    
    # Validation 3: Database metadata populated
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, file_size FROM downloaded_pdfs")
    record = cursor.fetchone()
    conn.close()
    
    assert record is not None
    assert record[1] > 0  # file_size
    
    # Validation 4: File path is valid
    assert storage.exists(record[0])
```

### Pattern: Pagination Limits in Tests

**Purpose**: Keep test execution fast

**Pattern**:
```python
def test_scraping_with_pagination_limit(temp_workspace, mocked_parliament_http):
    """Test scraping limited to first page."""
    storage = temp_workspace['storage']
    
    scraper = HansardScraper(storage=storage)
    
    # ALWAYS limit to first page in tests
    results = scraper.scrape_all(max_pages=1)
    
    assert len(results) > 0
    
    # Verify only one HTTP call was made
    assert mocked_parliament_http.get.call_count == 1
```

### Pattern: Error Message Validation

**Purpose**: Ensure errors are descriptive

**Pattern**:
```python
def test_error_message_is_descriptive():
    """Test that error messages are clear."""
    with pytest.raises(ValueError) as exc_info:
        process_invalid_data(None)
    
    error_msg = str(exc_info.value)
    
    # Error message should be descriptive
    assert "Invalid" in error_msg
    assert "None" in error_msg
    assert len(error_msg) > 20  # Not just "Invalid"
```

## When to Use Each Test Type

### Decision Tree

```
Is this testing a universal invariant (never crashes, always valid)?
├─ YES → Use property-based test
└─ NO → Continue

Is the input space small (< 10 values)?
├─ YES → Use parametrized unit test
└─ NO → Continue

Is this testing multiple components together?
├─ YES → Use integration test
└─ NO → Continue

Is this validating assumptions about external systems?
├─ YES → Use contract test
└─ NO → Use unit test
```

### Examples

**Universal Invariant** → Property Test:
```python
@given(st.text())
def test_never_crashes(text):
    """For ANY text, function never crashes."""
    result = process(text)
    assert result is not None
```

**Small Input Space** → Parametrized Unit Test:
```python
@pytest.mark.parametrize("period,expected", [
    ("Morning", "P"),
    ("Afternoon", "A"),
    ("Evening", "E"),
])
def test_period_extraction(period, expected):
    assert extract_period(period) == expected
```

**Multiple Components** → Integration Test:
```python
def test_scraper_storage_integration(temp_workspace):
    """Test scraper → storage → database integration."""
    # Test real component interactions
```

**External System Assumption** → Contract Test:
```python
def test_html_structure_contract():
    """Validate HTML structure assumption."""
    # Test that fixtures match production
```

## Well-Calibrated Test Examples

### Example 1: Date Extraction

**Complementary Tests** (Keep Both):
```python
# Unit test: Documents specific examples
@pytest.mark.parametrize("text,expected", [
    ("Thursday, 4th December 2025", "2025-12-04"),
    ("15th October 2025", "2025-10-15"),
])
def test_british_date_formats(text, expected):
    """Document the British date formats we support."""
    assert extract_date(text) == expected

# Property test: Proves robustness
@given(st.text())
def test_date_extraction_never_crashes(text):
    """For ANY text, extraction never crashes."""
    result = extract_date(text)
    assert result is None or isinstance(result, str)
```

### Example 2: Filename Generation

**Property Test Only** (Sufficient):
```python
@given(st.dates(), st.sampled_from(['A', 'P', 'E']))
def test_filename_format(date, period):
    """For ANY date and period, filename matches pattern."""
    filename = generate_filename(date.isoformat(), period)
    
    # Validate format
    assert re.match(r'^hansard_\d{8}_[APE]\.pdf$', filename)
    
    # Validate components
    date_str = date.strftime('%Y%m%d')
    assert date_str in filename
    assert f'_{period}.pdf' in filename
```

### Example 3: Download Decision Logic

**Complementary Tests** (Keep Both):
```python
# Unit tests: Document each state clearly
def test_download_when_file_and_db_missing():
    """When file AND DB missing → download."""
    assert should_download(file_exists=False, db_exists=False) is True

def test_skip_when_file_and_db_exist():
    """When file AND DB exist → skip."""
    assert should_download(file_exists=True, db_exists=True) is False

# Property test: Proves all combinations work
@given(file_exists=st.booleans(), db_exists=st.booleans())
def test_download_decision_property(file_exists, db_exists):
    """For ANY file/DB state, logic is correct."""
    result = should_download(file_exists, db_exists)
    assert isinstance(result, bool)
```

## Performance Guidelines

### Target Execution Times

- Unit tests: < 0.1s each
- Integration tests: < 1s each
- Contract tests: < 0.5s each
- Property tests: < 2s each
- Full test suite: < 30s total

### Performance Tips

1. **Use in-memory databases**: `sqlite3.connect(':memory:')`
2. **Limit pagination in tests**: Always use `max_pages=1`
3. **Mock I/O operations**: Mock file and network operations
4. **Use fixtures efficiently**: Reuse expensive setup
5. **Run tests in parallel**: `pytest -n auto`

### Measuring Performance

```bash
# Show slowest tests
pytest --durations=10

# Show all test durations
pytest --durations=0

# Profile specific test
pytest tests/test_module.py::test_function --durations=0
```

## Troubleshooting

### Tests Pass Locally but Fail in CI

**Cause**: Fixtures out of date or environment differences

**Solution**:
1. Run contract tests: `pytest tests/contract/ -v`
2. If contract tests fail: Update fixtures from production
3. Verify database schema matches production
4. Check for environment-specific paths or settings

### Integration Tests Fail but Unit Tests Pass

**Cause**: Synthetic data in unit tests doesn't match production

**Solution**:
1. Replace synthetic data with realistic fixtures
2. Run contract tests to validate fixtures
3. Update unit tests to use fixtures from `tests/fixtures/`

### Tests Are Slow

**Cause**: Not using mocking or pagination limits

**Solution**:
1. Mock HTTP requests: Use `mocked_parliament_http` fixture
2. Limit pagination: Always use `max_pages=1` in tests
3. Use in-memory databases: Avoid disk I/O
4. Run tests in parallel: `pytest -n auto`

### Real Network Calls in Tests

**Cause**: Mocking after object creation

**Solution**:
1. Mock BEFORE creating objects
2. Use `@patch` decorator at function level
3. Use `mocked_parliament_http` fixture
4. Verify with: `pytest tests/ --tb=short | grep "http://"`

## Resources

- Realistic Fixtures: `tests/fixtures/README.md`
- Contract Testing: `tests/contract/README.md`
- Testing Guidelines: `testing-guidelines.md`
- Code Style: `code-style.md`
