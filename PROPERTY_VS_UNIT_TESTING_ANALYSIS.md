# Property-Based Testing vs Unit Testing: When to Use Each

## The Fundamental Difference

### Unit Tests
**What they test:** Specific examples that demonstrate correct behavior

```python
def test_parse_british_date():
    """Test parsing a specific British date."""
    result = extract_date("15th October 2025")
    assert result == "2025-10-15"
```

**Characteristics:**
- Tests ONE specific input
- Developer chooses the example
- Fast to write and understand
- Documents expected behavior through examples

### Property-Based Tests
**What they test:** Universal rules that should hold for ALL inputs

```python
@given(st.dates())
def test_date_parsing_never_crashes(date):
    """Date parsing should never crash for any date."""
    # Tests with 100+ random dates
    result = extract_date(format_date(date))
    assert result is None or isinstance(result, str)
```

**Characteristics:**
- Tests MANY random inputs (100+ by default)
- Framework generates examples
- Finds edge cases developers miss
- Documents invariants and universal rules

## When They're Complementary (Both Needed)

### 1. Testing Parsing/Transformation Logic

**Unit Test:** Documents expected behavior with examples
```python
def test_parse_british_date_with_ordinal():
    """Test parsing '15th October 2025'."""
    assert extract_date("15th October 2025") == "2025-10-15"

def test_parse_british_date_1st():
    """Test parsing '1st December 2025'."""
    assert extract_date("1st December 2025") == "2025-12-01"
```

**Property Test:** Validates universal rules
```python
@given(st.dates())
def test_date_roundtrip_property(date):
    """For ANY date, format→parse→format should be idempotent."""
    formatted = format_british_date(date)
    parsed = extract_date(formatted)
    reformatted = format_iso_date(parsed)
    assert reformatted == date.isoformat()
```

**Why both?**
- Unit tests show HOW it works (documentation)
- Property test proves it ALWAYS works (correctness)
- **Not duplication** - they test different things

### 2. Testing State Machines

**Unit Test:** Documents specific state transitions
```python
def test_download_when_file_exists_and_db_exists():
    """Test: file exists + DB exists → skip download."""
    # Setup: create file and DB record
    storage.write("test.pdf", b"content")
    insert_db_record("test.pdf")
    
    # Test
    should_skip, reason = check_existing_download("test.pdf")
    
    # Verify
    assert should_skip is True
    assert reason == "file_exists_with_record"
```

**Property Test:** Validates all state combinations
```python
@given(file_exists=st.booleans(), db_exists=st.booleans())
def test_download_decision_logic(file_exists, db_exists):
    """For ANY combination of file/DB state, decision logic is correct."""
    # Setup state
    if file_exists:
        storage.write("test.pdf", b"content")
    if db_exists:
        insert_db_record("test.pdf")
    
    # Test
    should_skip, reason = check_existing_download("test.pdf")
    
    # Verify correct logic for this state
    if file_exists and db_exists:
        assert should_skip and reason == "file_exists_with_record"
    elif file_exists and not db_exists:
        assert should_skip and reason == "file_exists_without_record"
    # ... etc for all 4 states
```

**Why both?**
- Unit tests document each state clearly
- Property test ensures ALL states are handled
- **Not duplication** - property test is more comprehensive

### 3. Testing Error Handling

**Unit Test:** Documents specific error scenarios
```python
def test_download_with_network_error():
    """Test handling of network errors."""
    mock_session.get.side_effect = ConnectionError("Network down")
    
    result = download_pdf("http://test.com/test.pdf")
    
    assert result is False
    assert "Network down" in get_last_log()
```

**Property Test:** Validates error handling is complete
```python
@given(st.sampled_from([ConnectionError, Timeout, HTTPError]))
def test_download_handles_all_network_errors(error_type):
    """For ANY network error, download should handle gracefully."""
    mock_session.get.side_effect = error_type("Error")
    
    result = download_pdf("http://test.com/test.pdf")
    
    # Should never crash, always return False
    assert result is False
    assert get_last_log() is not None
```

**Why both?**
- Unit test shows HOW errors are handled
- Property test proves ALL errors are handled
- **Not duplication** - property test is more exhaustive

## When They're Duplicative (Choose One)

### 1. Simple Validation Logic

**Duplicative:**
```python
# Unit test
def test_period_of_day_morning():
    assert extract_period("Morning Session") == "P"

def test_period_of_day_afternoon():
    assert extract_period("Afternoon Session") == "A"

def test_period_of_day_evening():
    assert extract_period("Evening Session") == "E"

# Property test
@given(st.sampled_from(['Morning', 'Afternoon', 'Evening']))
def test_period_extraction_property(period):
    result = extract_period(f"{period} Session")
    expected = {'Morning': 'P', 'Afternoon': 'A', 'Evening': 'E'}[period]
    assert result == expected
```

**Better: Just use unit tests**
```python
@pytest.mark.parametrize("text,expected", [
    ("Morning Session", "P"),
    ("Afternoon Session", "A"),
    ("Evening Session", "E"),
])
def test_period_extraction(text, expected):
    assert extract_period(text) == expected
```

**Why?**
- Only 3 possible inputs (not a large space)
- Mapping is deterministic
- Unit test with parametrize is clearer
- **Property test is overkill**

### 2. Format Validation with Fixed Patterns

**Duplicative:**
```python
# Unit test
def test_filename_format():
    filename = generate_filename("2024-01-15", "P")
    assert filename == "hansard_20240115_P.pdf"

# Property test
@given(st.dates(), st.sampled_from(['A', 'P', 'E']))
def test_filename_format_property(date, period):
    filename = generate_filename(date.isoformat(), period)
    assert re.match(r'^hansard_\d{8}_[APE]\.pdf$', filename)
```

**Better: Use property test only**
```python
@given(st.dates(), st.sampled_from(['A', 'P', 'E']))
def test_filename_format(date, period):
    """For ANY date and period, filename matches pattern."""
    filename = generate_filename(date.isoformat(), period)
    
    # Validate format
    assert re.match(r'^hansard_\d{8}_[APE]\.pdf$', filename)
    
    # Validate date is correct
    date_str = date.strftime('%Y%m%d')
    assert date_str in filename
    
    # Validate period is correct
    assert f'_{period}.pdf' in filename
```

**Why?**
- Property test covers infinite dates
- Unit test only covers one example
- **Unit test is redundant**

### 3. Idempotency Testing

**Duplicative:**
```python
# Unit test
def test_migration_idempotent():
    migrate(db_path)
    migrate(db_path)  # Run twice
    # Check schema is correct

# Property test
@given(st.integers(min_value=1, max_value=10))
def test_migration_idempotent_property(times):
    for _ in range(times):
        migrate(db_path)
    # Check schema is correct
```

**Better: Use property test only**
```python
@given(st.integers(min_value=1, max_value=10))
def test_migration_idempotent(times):
    """Migration can be run ANY number of times safely."""
    for _ in range(times):
        migrate(db_path)
    
    # Verify schema is correct
    columns = get_columns(db_path, 'downloaded_pdfs')
    assert 'period_of_day' in columns
    assert 'session_id' in columns
```

**Why?**
- Property test proves it works for any number of runs
- Unit test only proves it works for 2 runs
- **Unit test is insufficient**

## Decision Framework

### Use ONLY Unit Tests When:

✅ **Small, fixed input space**
- Example: 3 period types (A, P, E)
- Example: 5 error types
- Example: Boolean flags

✅ **Documenting specific examples**
- Example: "This is how we handle British dates"
- Example: "This is the expected output format"

✅ **Testing specific edge cases**
- Example: Empty string input
- Example: None input
- Example: Maximum length input

✅ **Integration points**
- Example: Component A calls Component B correctly
- Example: Database transaction commits

### Use ONLY Property Tests When:

✅ **Large or infinite input space**
- Example: All possible dates
- Example: All possible strings
- Example: All possible integers

✅ **Testing universal invariants**
- Example: "Parsing never crashes"
- Example: "Output always matches format"
- Example: "Function is idempotent"

✅ **Finding edge cases**
- Example: Hypothesis finds weird inputs you didn't think of
- Example: Boundary conditions
- Example: Unusual combinations

### Use BOTH When:

✅ **Complex transformation logic**
- Unit: Document specific examples
- Property: Prove universal rules

✅ **State machines with many states**
- Unit: Document each state transition clearly
- Property: Prove all state combinations work

✅ **Error handling**
- Unit: Document how specific errors are handled
- Property: Prove all errors are handled

## Practical Guidelines for Hansard Tales

### Current Situation Analysis

Let me check what we actually have:

```python
# Date extraction - BOTH needed
# Unit tests: Document specific formats
def test_extract_date_british_format_with_ordinal():
    assert extract_date("15th October 2025") == "2025-10-15"

# Property test: Prove it works for all dates
@given(st.dates())
def test_date_extraction_never_crashes(date):
    result = extract_date(format_date(date))
    assert result is None or isinstance(result, str)
```
**Verdict: ✅ Keep both** - Different purposes

```python
# Filename format - DUPLICATIVE
# Unit test
def test_filename_format():
    assert generate_filename("2024-01-15", "P") == "hansard_20240115_P.pdf"

# Property test
@given(st.dates(), st.sampled_from(['A', 'P', 'E']))
def test_filename_format_property(date, period):
    filename = generate_filename(date.isoformat(), period)
    assert re.match(r'^hansard_\d{8}_[APE]\.pdf$', filename)
```
**Verdict: ❌ Remove unit test** - Property test is better

```python
# Download decision logic - BOTH needed
# Unit tests: Document each of 4 cases clearly
def test_download_file_and_db_exist():
    # Clear documentation of this specific case
    
def test_download_file_only():
    # Clear documentation of this specific case

# Property test: Prove all combinations work
@given(file_exists=st.booleans(), db_exists=st.booleans())
def test_download_decision_property(file_exists, db_exists):
    # Tests all 4 combinations
```
**Verdict: ✅ Keep both** - Unit tests are clearer documentation

## Recommendations for Hansard Tales

### Remove These Duplicative Tests:

1. **Filename format unit tests** - Property test is sufficient
2. **Period extraction unit tests** - Use parametrize instead
3. **Simple validation unit tests** - Property test covers them

### Keep Both For:

1. **Date extraction** - Unit tests document formats, property tests prove robustness
2. **Download decision logic** - Unit tests document each case, property tests prove completeness
3. **Error handling** - Unit tests document specific errors, property tests prove all errors handled
4. **Session linking** - Unit tests document workflow, property tests prove it always works

### Maintainability Ranking

**Most Maintainable → Least Maintainable:**

1. **Property tests for universal rules** ⭐⭐⭐⭐⭐
   - One test covers infinite inputs
   - Finds bugs you didn't think of
   - Self-documenting invariants

2. **Parametrized unit tests** ⭐⭐⭐⭐
   - Multiple examples in one test
   - Clear and concise
   - Easy to add new cases

3. **Individual unit tests** ⭐⭐⭐
   - Very clear documentation
   - Easy to understand
   - Can become verbose

4. **Duplicative property + unit tests** ⭐⭐
   - Maintenance burden
   - Confusion about which to update
   - Slower test suite

## Specific Recommendations

### For Date Extraction:
```python
# KEEP: Unit tests for documentation
def test_british_format_examples():
    """Document the specific formats we support."""
    assert extract_date("15th October 2025") == "2025-10-15"
    assert extract_date("1st December 2025") == "2025-12-01"

# KEEP: Property test for robustness
@given(st.text())
def test_date_extraction_never_crashes(text):
    """For ANY text, extraction should never crash."""
    result = extract_date(text)
    assert result is None or isinstance(result, str)
```

### For Filename Generation:
```python
# REMOVE: Unit test (redundant)
def test_filename_format():
    assert generate_filename("2024-01-15", "P") == "hansard_20240115_P.pdf"

# KEEP: Property test (comprehensive)
@given(st.dates(), st.sampled_from(['A', 'P', 'E']))
def test_filename_format(date, period):
    """For ANY date and period, filename matches pattern."""
    filename = generate_filename(date.isoformat(), period)
    assert re.match(r'^hansard_\d{8}_[APE]\.pdf$', filename)
```

### For Period Extraction:
```python
# REMOVE: Individual unit tests
def test_period_morning():
    assert extract_period("Morning") == "P"
def test_period_afternoon():
    assert extract_period("Afternoon") == "A"

# KEEP: Parametrized test (cleaner)
@pytest.mark.parametrize("text,expected", [
    ("Morning Session", "P"),
    ("Afternoon Session", "A"),
    ("Evening Session", "E"),
])
def test_period_extraction(text, expected):
    assert extract_period(text) == expected
```

### For Download Decision Logic:
```python
# KEEP: Unit tests (clear documentation of each case)
def test_download_file_and_db_exist():
    """When file AND DB record exist, skip download."""
    # Very clear what this case means
    
def test_download_file_only():
    """When only file exists, insert DB record and skip."""
    # Very clear what this case means

# KEEP: Property test (proves all combinations)
@given(file_exists=st.booleans(), db_exists=st.booleans())
def test_download_decision_property(file_exists, db_exists):
    """For ANY file/DB state combination, logic is correct."""
    # Tests all 4 combinations systematically
```

## Summary: When to Use Each

### Use Unit Tests ONLY:
- ✅ Small fixed input space (< 10 cases)
- ✅ Documenting specific examples
- ✅ Integration points
- ✅ Specific edge cases you want to highlight

### Use Property Tests ONLY:
- ✅ Large/infinite input space
- ✅ Universal invariants (never crashes, always valid format)
- ✅ Idempotency
- ✅ Roundtrip properties

### Use BOTH:
- ✅ Complex parsing/transformation (unit for examples, property for robustness)
- ✅ State machines (unit for each state, property for all combinations)
- ✅ Error handling (unit for specific errors, property for all errors)

### NEVER Use Both:
- ❌ Simple validation (property test is sufficient)
- ❌ Format checking (property test is sufficient)
- ❌ Enum-like mappings (parametrized unit test is sufficient)

## Recommendation for Hansard Tales

### Remove These Property Tests (Duplicative):

1. **Property 1: Filename Format Validation** - Unit test with parametrize is clearer
2. **Property 2: Period-of-Day Keyword Mapping** - Only 3 values, parametrize is better
3. **Property 8: Backup Filename Format** - Simple format, unit test sufficient

### Keep These Property Tests (Valuable):

1. **Property 4: Download Decision Logic** - 4 state combinations, property test ensures completeness
2. **Property 6: Download Tracking Metadata Completeness** - Validates all fields populated
3. **Property 7: Session Linking Updates Database** - Validates database updates work
4. **Property 11-13: Logging Properties** - Validates logging is complete

### Convert These to Parametrized Unit Tests:

```python
# Instead of separate unit tests + property test
@pytest.mark.parametrize("date,period,expected", [
    ("2024-01-15", "P", "hansard_20240115_P.pdf"),
    ("2024-12-31", "A", "hansard_20241231_A.pdf"),
    ("2025-06-15", "E", "hansard_20250615_E.pdf"),
])
def test_filename_generation(date, period, expected):
    """Test filename generation with various dates and periods."""
    assert generate_filename(date, period, []) == expected
```

## Final Answer

**When is duplication wasteful?**
- When property test covers the same ground as unit test
- When input space is small (< 10 cases)
- When the property test doesn't find additional bugs

**Which is better?**
- **Property tests** for universal rules and large input spaces
- **Unit tests** for documentation and specific examples
- **Parametrized unit tests** for small fixed input spaces

**Most maintainable approach:**
1. Start with unit tests for clarity
2. Add property tests for universal rules
3. Remove unit tests that are redundant with property tests
4. Use parametrize for multiple similar examples

**For Hansard Tales specifically:**
- Keep ~60% of current property tests (the valuable ones)
- Remove ~40% that duplicate unit tests
- Convert some unit tests to parametrized tests
- Focus property tests on finding edge cases and proving invariants
