# Testing Strategy for Hansard Tales

## Overview

This document provides guidance on selecting the right testing approach for different scenarios in the Hansard Tales project. It explains when to use unit tests, property-based tests, parametrized tests, and how to avoid test duplication while maintaining comprehensive coverage.

## Testing Philosophy

Our testing strategy follows these principles:

1. **Complementary, Not Duplicative**: Different test types should validate different aspects of correctness
2. **Maintainability First**: Fewer, more valuable tests are better than many redundant tests
3. **Coverage Through Properties**: Use property-based tests to validate universal invariants
4. **Examples Through Unit Tests**: Use unit tests to document specific behaviors and edge cases
5. **Realistic Data**: All tests should use realistic data that matches production

## Test Type Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│ What are you testing?                                        │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │ Is it a universal invariant?       │
        │ (never crashes, always valid       │
        │  format, always returns X type)    │
        └────────────────────────────────────┘
                 │                    │
                YES                  NO
                 │                    │
                 ▼                    ▼
        ┌─────────────────┐   ┌──────────────────┐
        │ Property-Based  │   │ Is input space   │
        │ Test ONLY       │   │ small (< 10)?    │
        └─────────────────┘   └──────────────────┘
                                      │
                              ┌───────┴───────┐
                             YES             NO
                              │               │
                              ▼               ▼
                    ┌──────────────┐  ┌─────────────────┐
                    │ Parametrized │  │ Does it need    │
                    │ Unit Test    │  │ documentation?  │
                    └──────────────┘  └─────────────────┘
                                              │
                                      ┌───────┴───────┐
                                     YES             NO
                                      │               │
                                      ▼               ▼
                            ┌──────────────┐  ┌─────────────┐
                            │ Unit Test +  │  │ Property    │
                            │ Property Test│  │ Test ONLY   │
                            │ (Complement) │  └─────────────┘
                            └──────────────┘
```

## When to Use Each Test Type

### Property-Based Tests

**Use When:**
- Testing universal invariants (never crashes, always valid format)
- Testing format validation across many inputs
- Testing robustness with generated data
- Input space is large or unbounded
- You want to find edge cases automatically

**Examples:**
```python
from hypothesis import given, strategies as st

@given(st.text())
def test_date_extraction_never_crashes(date_string):
    """Date extraction should never crash, even with invalid input."""
    result = extract_date(date_string)
    assert result is None or isinstance(result, str)

@given(st.integers(min_value=0), st.text(min_size=1))
def test_filename_always_valid_format(timestamp, period):
    """Generated filenames should always match expected pattern."""
    filename = generate_filename(timestamp, period)
    assert re.match(r'hansard_\d{8}_\d+_[APE]\.pdf', filename)
```

**Don't Use When:**
- Input space is small (< 10 cases) - use parametrized tests instead
- Testing specific business logic examples - use unit tests
- Testing state machine transitions - use both unit and property tests

### Unit Tests

**Use When:**
- Documenting specific examples of correct behavior
- Testing important edge cases explicitly
- Testing complex business logic with specific scenarios
- Providing regression tests for bugs
- Input space is small and well-defined

**Examples:**
```python
def test_parse_british_date_with_ordinal():
    """Test parsing British date with ordinal suffix."""
    result = parse_date("Thursday, 4th December 2025")
    assert result == "2025-12-04"

def test_extract_mp_name_with_honorific():
    """Test MP name extraction with honorific."""
    result = extract_mp_name("Hon. John Doe")
    assert result == {"honorific": "Hon.", "first": "John", "last": "Doe"}

def test_download_decision_already_downloaded():
    """Test that already downloaded PDFs are skipped."""
    # Specific regression test for duplicate prevention
    result = should_download(url, db_path)
    assert result is False
```

**Don't Use When:**
- Testing format validation across many inputs - use property tests
- Testing universal invariants - use property tests
- You have many similar test cases - use parametrized tests

### Parametrized Tests

**Use When:**
- Input space is small (< 10 cases)
- Testing the same logic with different inputs
- You have a list of known examples to test
- Converting multiple similar unit tests

**Examples:**
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

@pytest.mark.parametrize("british,iso", [
    ("Thursday, 4th December 2025", "2025-12-04"),
    ("Tuesday, 15th October 2025", "2025-10-15"),
    ("Wednesday, 1st January 2025", "2025-01-01"),
])
def test_british_date_parsing(british, iso):
    """Test British date format parsing."""
    result = parse_date(british)
    assert result == iso
```

**Don't Use When:**
- Input space is large - use property tests
- You need to test universal invariants - use property tests
- Each case needs different setup/teardown - use separate unit tests

### Integration Tests

**Use When:**
- Testing multiple components working together
- Testing realistic data flows
- Testing component interactions
- Validating end-to-end workflows

**Examples:**
```python
def test_scrape_and_store_integration(temp_workspace, mocked_parliament_http):
    """Test scraping and storage work together."""
    scraper = HansardScraper(storage=temp_workspace['storage'])
    results = scraper.scrape_all(max_pages=1)
    
    # Verify files were stored
    files = temp_workspace['storage'].list_files()
    assert len(files) > 0
```

## Complementary vs Duplicative Tests

### Complementary Tests (Keep Both)

Tests are complementary when they validate different aspects of correctness:

**Example 1: Date Extraction**
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

**Why Complementary:**
- Unit test: Shows what valid input looks like
- Property test: Ensures function handles any input gracefully
- Different aspects: Correctness vs Robustness

**Example 2: Download Decision Logic**
```python
# Unit test: Documents business logic
def test_download_decision_already_exists():
    """Test that existing files are skipped."""
    result = should_download(url, db_path)
    assert result is False

# Property test: Validates state consistency
@given(st.booleans(), st.booleans())
def test_download_decision_consistent(file_exists, db_has_record):
    """Download decision should be consistent with state."""
    result = should_download(url, db_path, file_exists, db_has_record)
    # Should download only if neither exists
    assert result == (not file_exists and not db_has_record)
```

**Why Complementary:**
- Unit test: Documents specific business rule
- Property test: Validates logical consistency
- Different aspects: Business Logic vs State Consistency

### Duplicative Tests (Remove Redundant)

Tests are duplicative when they validate the same aspect of correctness:

**Example 1: Filename Format (Duplicative)**
```python
# ❌ Remove these individual unit tests
def test_filename_format_morning():
    """Test filename format for morning session."""
    result = generate_filename(date, "Morning")
    assert result == "hansard_20240101_0_A.pdf"

def test_filename_format_afternoon():
    """Test filename format for afternoon session."""
    result = generate_filename(date, "Afternoon")
    assert result == "hansard_20240101_0_P.pdf"

def test_filename_format_evening():
    """Test filename format for evening session."""
    result = generate_filename(date, "Evening")
    assert result == "hansard_20240101_0_E.pdf"

# ✅ Keep only the property test
@given(st.integers(min_value=0), st.sampled_from(["Morning", "Afternoon", "Evening"]))
def test_filename_always_valid_format(timestamp, period):
    """Generated filenames should always match expected pattern."""
    filename = generate_filename(timestamp, period)
    assert re.match(r'hansard_\d{8}_\d+_[APE]\.pdf', filename)
```

**Why Duplicative:**
- All unit tests validate the same thing: format correctness
- Property test covers all cases and more
- No additional value from individual examples

**Example 2: Period Extraction (Convert to Parametrized)**
```python
# ❌ Remove these individual unit tests
def test_extract_period_morning():
    result = extract_period("Morning Session")
    assert result == "A"

def test_extract_period_afternoon():
    result = extract_period("Afternoon Session")
    assert result == "P"

def test_extract_period_evening():
    result = extract_period("Evening Session")
    assert result == "E"

# ❌ Remove property test (only 3 values)
@given(st.sampled_from(["Morning", "Afternoon", "Evening"]))
def test_extract_period_property(period):
    result = extract_period(f"{period} Session")
    assert result in ["A", "P", "E"]

# ✅ Keep only parametrized test
@pytest.mark.parametrize("period,expected", [
    ("Morning Session", "A"),
    ("Afternoon Session", "P"),
    ("Evening Session", "E"),
])
def test_extract_period(period, expected):
    """Test period code extraction."""
    result = extract_period(period)
    assert result == expected
```

**Why Duplicative:**
- Small input space (3 values)
- Property test adds no value over parametrized test
- Parametrized test is clearer and more maintainable

## Decision Matrix

| Scenario | Test Type | Rationale |
|----------|-----------|-----------|
| Format validation (large input space) | Property Test | Validates format across all inputs |
| Specific business logic example | Unit Test | Documents expected behavior |
| Universal invariant (never crashes) | Property Test | Validates robustness |
| Small input space (< 10 cases) | Parametrized Test | Clear and maintainable |
| State machine transitions | Unit + Property | Unit for examples, Property for completeness |
| Complex parsing with examples | Unit + Property | Unit for documentation, Property for robustness |
| Simple validation (3-5 cases) | Parametrized Test | Avoid property test overhead |
| Error handling | Unit Test | Document specific error scenarios |
| Component integration | Integration Test | Test realistic interactions |

## Refactoring Guidelines

### When to Remove Unit Tests

Remove unit tests when:
1. A property test covers the same ground
2. The unit tests only validate format/structure
3. There are many similar unit tests testing the same thing
4. The property test provides better coverage

**Example:**
```python
# Remove these 10 unit tests for different date formats
def test_filename_format_case_1(): ...
def test_filename_format_case_2(): ...
# ... 8 more similar tests

# Keep this one property test
@given(st.dates(), st.text())
def test_filename_always_valid_format(date, period):
    """Filenames should always match expected pattern."""
    ...
```

### When to Remove Property Tests

Remove property tests when:
1. Input space is very small (< 10 cases)
2. A parametrized test is clearer
3. The property test doesn't add value over unit tests

**Example:**
```python
# Remove this property test (only 3 values)
@given(st.sampled_from(["A", "P", "E"]))
def test_period_code_property(code): ...

# Keep this parametrized test
@pytest.mark.parametrize("code,expected", [("A", "Morning"), ("P", "Afternoon"), ("E", "Evening")])
def test_period_code(code, expected): ...
```

### When to Convert to Parametrized

Convert to parametrized tests when:
1. You have 3-10 similar unit tests
2. Each test has the same structure
3. Only inputs and expected outputs differ

**Example:**
```python
# Before: 5 similar unit tests
def test_case_1(): assert func(input1) == output1
def test_case_2(): assert func(input2) == output2
# ... 3 more

# After: One parametrized test
@pytest.mark.parametrize("input,expected", [
    (input1, output1),
    (input2, output2),
    # ... 3 more
])
def test_func(input, expected):
    assert func(input) == expected
```

## Maintenance Benefits

### Reduced Test Count
- **Before refactoring**: 450 tests
- **After refactoring**: 360 tests (20% reduction)
- **Coverage**: Maintained at 90%+

### Faster Execution
- Fewer tests = faster CI/CD
- Property tests find more bugs with less code
- Parametrized tests are more efficient than individual tests

### Easier Maintenance
- Fewer tests to update when code changes
- Property tests document invariants clearly
- Parametrized tests make patterns obvious

### Better Documentation
- Unit tests show specific examples
- Property tests show universal rules
- Less duplication = clearer intent

## Examples of Well-Balanced Test Suites

### Example 1: Date Parsing Module

```python
# Unit tests: Document specific examples
def test_parse_british_date_with_ordinal():
    """Test parsing British date with ordinal suffix."""
    result = parse_date("Thursday, 4th December 2025")
    assert result == "2025-12-04"

def test_parse_british_date_without_day():
    """Test parsing British date without day of week."""
    result = parse_date("4th December 2025")
    assert result == "2025-12-04"

# Property test: Validate robustness
@given(st.text())
def test_parse_date_never_crashes(text):
    """Date parsing should never crash."""
    result = parse_date(text)
    assert result is None or isinstance(result, str)

# Property test: Validate format
@given(st.dates())
def test_parsed_dates_always_iso_format(date):
    """Parsed dates should always be ISO format."""
    british = format_british(date)
    result = parse_date(british)
    assert re.match(r'\d{4}-\d{2}-\d{2}', result)
```

**Balance:**
- 2 unit tests: Document specific formats
- 2 property tests: Validate robustness and format
- Total: 4 tests covering all aspects

### Example 2: Filename Generation Module

```python
# Parametrized test: Small input space
@pytest.mark.parametrize("period,code", [
    ("Morning", "A"),
    ("Afternoon", "P"),
    ("Evening", "E"),
])
def test_period_to_code(period, code):
    """Test period code extraction."""
    result = extract_period_code(period)
    assert result == code

# Property test: Validate format
@given(st.dates(), st.sampled_from(["Morning", "Afternoon", "Evening"]))
def test_filename_always_valid_format(date, period):
    """Generated filenames should always match expected pattern."""
    filename = generate_filename(date, period)
    assert re.match(r'hansard_\d{8}_\d+_[APE]\.pdf', filename)
```

**Balance:**
- 1 parametrized test: Document period codes (3 cases)
- 1 property test: Validate filename format
- Total: 2 tests covering all aspects

### Example 3: MP Name Parsing Module

```python
# Unit tests: Document specific examples
def test_parse_name_with_honorific():
    """Test parsing name with honorific."""
    result = parse_mp_name("Hon. John Doe")
    assert result == {"honorific": "Hon.", "first": "John", "last": "Doe"}

def test_parse_name_without_honorific():
    """Test parsing name without honorific."""
    result = parse_mp_name("John Doe")
    assert result == {"honorific": None, "first": "John", "last": "Doe"}

# Property test: Validate structure
@given(st.text(min_size=1), st.text(min_size=1))
def test_parse_name_always_returns_dict(first, last):
    """Name parsing should always return dict with expected keys."""
    name = f"{first} {last}"
    result = parse_mp_name(name)
    assert isinstance(result, dict)
    assert "first" in result
    assert "last" in result
    assert "honorific" in result
```

**Balance:**
- 2 unit tests: Document specific behaviors
- 1 property test: Validate structure consistency
- Total: 3 tests covering all aspects

## Quick Reference

### ✅ Do This

- Use property tests for universal invariants
- Use unit tests for specific examples
- Use parametrized tests for small input spaces (< 10)
- Keep complementary tests (different aspects)
- Remove duplicative tests (same aspect)
- Document why tests are complementary

### ❌ Don't Do This

- Don't write 10 unit tests when 1 property test suffices
- Don't use property tests for tiny input spaces
- Don't keep duplicative tests "just in case"
- Don't test the same thing in multiple ways without reason
- Don't sacrifice clarity for coverage

## Summary

The key to a well-balanced test suite is understanding what each test type validates:

- **Property Tests**: Universal invariants, format validation, robustness
- **Unit Tests**: Specific examples, business logic, edge cases
- **Parametrized Tests**: Small input spaces, known examples
- **Integration Tests**: Component interactions, realistic workflows

When tests validate different aspects of correctness, they're complementary and should be kept. When they validate the same aspect, they're duplicative and should be refactored.

The goal is not maximum test count, but maximum confidence with minimum maintenance burden.
