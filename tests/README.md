# Test Organization

This directory contains all tests for the Hansard Tales project, organized by test type.

## Directory Structure

```
tests/
├── unit/              # Unit tests - test individual functions/classes in isolation
├── integration/       # Integration tests - test multiple components working together
├── end_to_end/        # End-to-end tests - test complete workflows
├── contract/          # Contract tests - validate assumptions about external systems
├── scraper/           # Scraper-specific tests (unit and integration)
├── fixtures/          # Shared test fixtures and realistic test data
├── historical_processing/  # Historical data processing tests
├── conftest.py        # Shared pytest fixtures
└── test_*.py          # Infrastructure and fixture tests
```

## Test Categories

### Unit Tests (`tests/unit/`)
Test individual functions or classes in isolation with mocked dependencies.

**Examples:**
- `test_bill_extractor.py` - Tests bill extraction logic
- `test_filename_generator.py` - Tests filename generation functions
- `test_mp_identifier.py` - Tests MP identification logic

**Characteristics:**
- Fast execution (< 1 second per test)
- No external dependencies
- Use mocks for I/O operations
- Test specific examples and edge cases

### Integration Tests (`tests/integration/`)
Test multiple components working together with minimal mocking.

**Examples:**
- `test_database.py` - Tests database operations
- `test_workflow_orchestrator.py` - Tests workflow coordination
- `test_scraper.py` - Tests scraper with storage and database

**Characteristics:**
- Moderate execution time (1-5 seconds per test)
- Test real component interactions
- Use realistic test data
- Mock only external dependencies (HTTP, file system)

### End-to-End Tests (`tests/end_to_end/`)
Test complete workflows from start to finish.

**Examples:**
- `test_end_to_end.py` - Tests complete processing pipeline

**Characteristics:**
- Slower execution (5-30 seconds per test)
- Minimal mocking
- Test realistic data flows
- Validate complete system behavior

### Contract Tests (`tests/contract/`)
Validate assumptions about external systems (parliament.go.ke).

**Examples:**
- `test_html_structure.py` - Validates HTML structure assumptions
- `test_date_formats.py` - Validates date format assumptions
- `test_pdf_links.py` - Validates PDF link format assumptions

**Characteristics:**
- Fast execution
- Validate mock data matches production
- Detect external system changes early
- Provide clear failure guidance

### Scraper Tests (`tests/scraper/`)
Specialized tests for the scraper component.

**Examples:**
- `test_date_extraction.py` - Tests date extraction logic
- `test_pagination.py` - Tests pagination handling
- `test_download_tracking.py` - Tests download tracking

### Fixtures (`tests/fixtures/`)
Shared test fixtures with realistic data from parliament.go.ke.

**Examples:**
- `html_samples.py` - Real HTML samples
- `date_formats.py` - Real date format examples
- `pdf_metadata.py` - Real PDF link structures

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# End-to-end tests only
pytest tests/end_to_end/

# Contract tests only
pytest tests/contract/
```

### Run with Coverage
```bash
# Coverage is enabled by default in pytest.ini
pytest

# View HTML coverage report
open htmlcov/index.html
```

### Run with Markers
```bash
# Run tests marked as 'unit'
pytest -m unit

# Run tests marked as 'integration'
pytest -m integration

# Run tests marked as 'contract'
pytest -m contract

# Run tests marked as 'property' (property-based tests)
pytest -m property
```

### Run Specific Test Files
```bash
# Single file
pytest tests/unit/test_filename_generator.py

# Multiple files
pytest tests/unit/test_filename_generator.py tests/unit/test_mp_identifier.py
```

### Performance Monitoring
```bash
# Show slowest 10 tests (enabled by default)
pytest

# Show slowest 20 tests
pytest --durations=20
```

## Test Markers

Tests can be marked with pytest markers to categorize them:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.contract` - Contract tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.performance` - Performance-sensitive tests
- `@pytest.mark.property` - Property-based tests

## Coverage Requirements

- Overall project: ≥90%
- New modules: ≥90%
- Modified modules: Maintain or improve existing coverage

## Best Practices

1. **Use realistic test data** - Use fixtures from `tests/fixtures/` instead of synthetic data
2. **Mock external dependencies** - Mock HTTP requests, file I/O, and external APIs
3. **Use production database schema** - Use `production_db` fixture for database tests
4. **Keep tests focused** - Each test should test one thing
5. **Write descriptive test names** - Use `test_<what>_<condition>_<expected>` format
6. **Document test purpose** - Add docstrings explaining what is being tested

## See Also

- [Testing Guidelines](../.kiro/steering/testing-guidelines.md) - Detailed testing patterns and guidelines
- [Testing Patterns](../docs/TESTING_PATTERNS.md) - Common testing patterns and examples
- [Fixtures README](fixtures/README.md) - How to use and update test fixtures
