---
inclusion: always
---

# Testing Guidelines for Hansard Tales

## Overview

This project maintains high test coverage (≥90%) using pytest. All new code should include comprehensive tests covering both happy paths and error cases.

## Test Structure

### File Organization
```
tests/
├── test_<module_name>.py  # Mirror source structure
├── conftest.py            # Shared fixtures (if needed)
└── __init__.py
```

### Test Class Organization
```python
class TestFunctionName:
    """Test suite for specific function."""
    
    def test_success_case(self):
        """Test normal operation."""
        
    def test_error_handling(self):
        """Test error scenarios."""
        
    def test_edge_cases(self):
        """Test boundary conditions."""
```

## Fixtures

### Standard Fixtures

**temp_db**: Temporary SQLite database with schema
```python
@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Initialize schema
    conn = sqlite3.Connection(db_path)
    # ... create tables
    
    yield db_path
    
    Path(db_path).unlink()
```

**temp_pdf_dir**: Temporary directory with sample PDFs
```python
@pytest.fixture
def temp_pdf_dir():
    """Create temporary directory with sample PDFs."""
    temp_dir = tempfile.mkdtemp()
    pdf_dir = Path(temp_dir) / "pdfs"
    pdf_dir.mkdir(parents=True)
    
    # Create sample files
    for name in ["20240101_0_P.pdf", "20240115_0_A.pdf"]:
        (pdf_dir / name).touch()
    
    yield pdf_dir
    
    shutil.rmtree(temp_dir)
```

## Mocking Strategy

### External Dependencies
Always mock:
- File I/O operations
- Network requests
- Database connections (use temp_db instead)
- External APIs
- Time-dependent operations

### Example Mocking Pattern
```python
@patch('module.ExternalClass')
def test_with_mock(self, mock_class):
    """Test with mocked dependency."""
    # Setup mock
    mock_instance = Mock()
    mock_instance.method.return_value = expected_value
    mock_class.return_value = mock_instance
    
    # Test code
    result = function_under_test()
    
    # Verify
    assert result == expected_value
    mock_instance.method.assert_called_once()
```

## Test Coverage Requirements

### Minimum Coverage
- Overall project: ≥90%
- New modules: ≥90%
- Modified modules: Maintain or improve existing coverage

### Running Coverage
```bash
# Single file
pytest tests/test_module.py --cov=module --cov-report=term-missing

# Full suite
pytest --cov=hansard_tales --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

## Test Categories

### 1. Unit Tests
Test individual functions in isolation.

**Example:**
```python
def test_parse_date_string_iso_format(self):
    """Test parsing ISO format dates."""
    result = parse_date_string("2024-01-01")
    assert result == "2024-01-01"
```

### 2. Integration Tests
Test multiple components working together.

**Example:**
```python
@patch('module.PDFProcessor')
@patch('module.MPIdentifier')
def test_process_pdf_integration(self, mock_mp, mock_pdf):
    """Test PDF processing with multiple components."""
    # Setup mocks for integration
    # Test workflow
    # Verify interactions
```

### 3. Error Handling Tests
Test all error paths.

**Example:**
```python
def test_invalid_input(self):
    """Test handling of invalid input."""
    result = function(None)
    assert result is None
    
def test_exception_handling(self):
    """Test exception handling."""
    with pytest.raises(ValueError):
        function("invalid")
```

### 4. Edge Case Tests
Test boundary conditions.

**Example:**
```python
def test_empty_input(self):
    """Test with empty input."""
    result = function([])
    assert result == []

def test_large_input(self):
    """Test with large dataset."""
    result = function(range(10000))
    assert len(result) == 10000
```

## Best Practices

### 1. Test Naming
- Use descriptive names: `test_<what>_<condition>_<expected>`
- Examples:
  - `test_parse_date_iso_format`
  - `test_process_pdf_already_processed`
  - `test_download_with_network_error`

### 2. Test Documentation
```python
def test_function_name(self):
    """
    Test description explaining what is being tested.
    
    This test verifies that [specific behavior] works correctly
    when [specific conditions].
    """
```

### 3. Arrange-Act-Assert Pattern
```python
def test_example(self):
    """Test example function."""
    # Arrange: Setup test data
    input_data = create_test_data()
    
    # Act: Execute function
    result = function_under_test(input_data)
    
    # Assert: Verify results
    assert result.status == 'success'
    assert result.count == 10
```

### 4. Avoid Test Interdependence
- Each test should be independent
- Use fixtures for shared setup
- Don't rely on test execution order

### 5. Mock External Resources
```python
# Good: Mock file operations
@patch('pathlib.Path.glob')
def test_with_mock(self, mock_glob):
    mock_glob.return_value = [Path("test.pdf")]
    # Test code

# Bad: Use actual files
def test_without_mock(self):
    files = Path("/actual/path").glob("*.pdf")  # Don't do this
```

### 6. Test Both Success and Failure
```python
class TestFunction:
    def test_success_case(self):
        """Test successful operation."""
        result = function(valid_input)
        assert result.status == 'success'
    
    def test_failure_case(self):
        """Test failure handling."""
        result = function(invalid_input)
        assert result.status == 'error'
        assert result.error_message is not None
```

## Common Patterns

### Testing Database Operations
```python
def test_database_operation(self, temp_db):
    """Test database operation."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Perform operation
    cursor.execute("INSERT INTO table VALUES (?)", (value,))
    conn.commit()
    
    # Verify
    cursor.execute("SELECT * FROM table")
    result = cursor.fetchone()
    assert result[0] == value
    
    conn.close()
```

### Testing Async/Parallel Code
```python
@patch('concurrent.futures.ThreadPoolExecutor')
def test_parallel_processing(self, mock_executor):
    """Test parallel processing."""
    # Mock executor behavior
    mock_executor.return_value.__enter__.return_value.submit.return_value.result.return_value = expected
    
    # Test code
    result = parallel_function()
    
    # Verify
    assert result == expected
```

### Testing CLI Arguments
```python
@patch('sys.argv', ['prog', '--arg', 'value'])
def test_cli_argument(self):
    """Test command-line argument parsing."""
    from module import main
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 0
```

## Debugging Failed Tests

### 1. Use pytest options
```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Run specific test
pytest tests/test_module.py::TestClass::test_method
```

### 2. Add debug output
```python
def test_debug(self):
    """Test with debug output."""
    result = function(input)
    print(f"Result: {result}")  # Will show with -s flag
    assert result == expected
```

### 3. Use pytest.set_trace()
```python
def test_with_breakpoint(self):
    """Test with breakpoint."""
    result = function(input)
    pytest.set_trace()  # Debugger will stop here
    assert result == expected
```

## Performance Considerations

### Test Execution Speed
- Target: < 5 minutes for full suite
- Individual tests: < 1 second each
- Use mocking to avoid slow I/O
- Consider parallel test execution: `pytest -n auto`

### Memory Usage
- Clean up resources in fixtures
- Use `yield` for proper teardown
- Avoid loading large datasets

## Continuous Integration

Tests run automatically on:
- Every push to main branch
- Every pull request
- Weekly scheduled runs

### CI Requirements
- All tests must pass
- Coverage must be ≥90%
- No new linting errors

## Quick Reference

### Run Tests
```bash
# All tests
pytest

# Specific file
pytest tests/test_module.py

# With coverage
pytest --cov=hansard_tales --cov-report=term

# Parallel execution
pytest -n auto

# Verbose with coverage
pytest -v --cov=hansard_tales --cov-report=term-missing
```

### Common Assertions
```python
assert value == expected
assert value is None
assert value is not None
assert len(list) == 5
assert 'key' in dict
assert value > 0
assert callable(function)

# Exceptions
with pytest.raises(ValueError):
    function()

# Approximate equality
assert value == pytest.approx(3.14, rel=0.01)
```

### Common Fixtures
```python
@pytest.fixture
def sample_data():
    """Provide sample data."""
    return {"key": "value"}

@pytest.fixture(autouse=True)
def setup_teardown():
    """Run before/after each test."""
    # Setup
    yield
    # Teardown
```

## Resources

- pytest documentation: https://docs.pytest.org/
- Coverage.py: https://coverage.readthedocs.io/
- unittest.mock: https://docs.python.org/3/library/unittest.mock.html

## Property-Based Testing vs Unit Testing

### When to Use Property-Based Tests

Property-based tests validate universal invariants across many generated inputs. Use them when:

- Testing format validation (filenames, dates, URLs)
- Testing robustness (function never crashes)
- Testing universal properties (always returns valid type)
- Input space is large or unbounded

**Example:**
```python
from hypothesis import given, strategies as st

@given(st.text())
def test_date_extraction_never_crashes(date_string):
    """Date extraction should never crash, even with invalid input."""
    result = extract_date(date_string)
    assert result is None or isinstance(result, str)

@given(st.dates(), st.sampled_from(["Morning", "Afternoon", "Evening"]))
def test_filename_always_valid_format(date, period):
    """Generated filenames should always match expected pattern."""
    filename = generate_filename(date, period)
    assert re.match(r'hansard_\d{8}_\d+_[APE]\.pdf', filename)
```

### When to Use Unit Tests

Unit tests document specific examples and edge cases. Use them when:

- Documenting specific business logic examples
- Testing important edge cases explicitly
- Providing regression tests for bugs
- Input space is small (< 10 cases)

**Example:**
```python
def test_parse_british_date_with_ordinal():
    """Test parsing British date with ordinal suffix."""
    result = parse_date("Thursday, 4th December 2025")
    assert result == "2025-12-04"

def test_extract_mp_name_with_honorific():
    """Test MP name extraction with honorific."""
    result = extract_mp_name("Hon. John Doe")
    assert result == {"honorific": "Hon.", "first": "John", "last": "Doe"}
```

### When to Use Parametrized Tests

Parametrized tests are ideal for small input spaces with known examples:

**Example:**
```python
@pytest.mark.parametrize("period,expected", [
    ("Morning", "A"),
    ("Afternoon", "P"),
    ("Evening", "E"),
])
def test_period_to_code(period, expected):
    """Test period code extraction."""
    result = extract_period_code(period)
    assert result == expected
```

### Complementary vs Duplicative Tests

**Complementary Tests (Keep Both):**
Tests are complementary when they validate different aspects:

```python
# Unit test: Documents specific example
def test_extract_date_british_format():
    """Test extraction of British date format."""
    result = extract_date("Thursday, 4th December 2025")
    assert result == "2025-12-04"

# Property test: Validates robustness
@given(st.text())
def test_extract_date_never_crashes(text):
    """Date extraction should never crash."""
    result = extract_date(text)
    assert result is None or isinstance(result, str)
```

These are complementary because:
- Unit test shows what valid input looks like
- Property test ensures function handles any input gracefully
- They validate different aspects: correctness vs robustness

**Duplicative Tests (Remove Redundant):**
Tests are duplicative when they validate the same aspect:

```python
# ❌ Remove these individual unit tests
def test_filename_format_morning():
    result = generate_filename(date, "Morning")
    assert result == "hansard_20240101_0_A.pdf"

def test_filename_format_afternoon():
    result = generate_filename(date, "Afternoon")
    assert result == "hansard_20240101_0_P.pdf"

# ✅ Keep only the property test
@given(st.dates(), st.sampled_from(["Morning", "Afternoon", "Evening"]))
def test_filename_always_valid_format(date, period):
    """Generated filenames should always match expected pattern."""
    filename = generate_filename(date, period)
    assert re.match(r'hansard_\d{8}_\d+_[APE]\.pdf', filename)
```

These are duplicative because all tests validate the same thing: format correctness.

### Examples of Well-Balanced Test Suites

**Example 1: Date Parsing**
```python
# Unit tests: Document specific examples (2 tests)
def test_parse_british_date_with_ordinal():
    result = parse_date("Thursday, 4th December 2025")
    assert result == "2025-12-04"

def test_parse_british_date_without_day():
    result = parse_date("4th December 2025")
    assert result == "2025-12-04"

# Property tests: Validate robustness and format (2 tests)
@given(st.text())
def test_parse_date_never_crashes(text):
    result = parse_date(text)
    assert result is None or isinstance(result, str)

@given(st.dates())
def test_parsed_dates_always_iso_format(date):
    british = format_british(date)
    result = parse_date(british)
    assert re.match(r'\d{4}-\d{2}-\d{2}', result)
```

**Balance:** 4 tests total - 2 for examples, 2 for properties

**Example 2: Filename Generation**
```python
# Parametrized test: Small input space (1 test)
@pytest.mark.parametrize("period,code", [
    ("Morning", "A"),
    ("Afternoon", "P"),
    ("Evening", "E"),
])
def test_period_to_code(period, code):
    result = extract_period_code(period)
    assert result == code

# Property test: Validate format (1 test)
@given(st.dates(), st.sampled_from(["Morning", "Afternoon", "Evening"]))
def test_filename_always_valid_format(date, period):
    filename = generate_filename(date, period)
    assert re.match(r'hansard_\d{8}_\d+_[APE]\.pdf', filename)
```

**Balance:** 2 tests total - 1 parametrized, 1 property

### Maintenance Benefits

**Reduced Test Count:**
- Fewer tests to maintain when code changes
- Property tests find more bugs with less code
- Clearer intent with less duplication

**Faster Execution:**
- Fewer tests = faster CI/CD
- More efficient test suite

**Better Documentation:**
- Unit tests show specific examples
- Property tests show universal rules
- Less duplication = clearer intent

### Quick Decision Guide

| Scenario | Use This |
|----------|----------|
| Format validation (large input space) | Property Test |
| Specific business logic example | Unit Test |
| Universal invariant (never crashes) | Property Test |
| Small input space (< 10 cases) | Parametrized Test |
| State machine transitions | Unit + Property (complementary) |
| Complex parsing with examples | Unit + Property (complementary) |
| Simple validation (3-5 cases) | Parametrized Test |

For more detailed guidance, see [docs/TESTING_STRATEGY.md](../../docs/TESTING_STRATEGY.md).

## Questions?

When in doubt:
1. Look at existing tests for patterns
2. Aim for clarity over cleverness
3. Test behavior, not implementation
4. Keep tests simple and focused
5. Avoid duplicative tests - use complementary tests instead
