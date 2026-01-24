# Detailed Analysis of Remaining 18 Test Failures

## Category 1: Database Schema Issues (6 failures)
**File**: `tests/integration/test_process_historical_data.py`

### Root Cause
All 6 failures are due to: **NOT NULL constraint failed: hansard_sessions.pdf_url**

The database schema requires `pdf_url` to be NOT NULL, but tests are inserting records without it.

### Affected Tests
1. `TestProcessSinglePDF::test_already_processed` (line 182)
2. `TestHistoricalDataProcessor::test_clean_database_data_deletion` (line 350)
3. `TestHistoricalDataProcessor::test_quality_assurance` (line 535)
4. `TestEdgeCases::test_process_single_pdf_with_force` (line 783)
5. `TestFinalCoverage::test_quality_assurance_with_duplicates` (line 1207)
6. `TestFinalCoverage::test_quality_assurance_with_bills` (line ~1250)

### Example Error
```python
cursor.execute("INSERT INTO hansard_sessions (term_id, date, title) VALUES (1, '2024-01-01', 'test')")
# Error: NOT NULL constraint failed: hansard_sessions.pdf_url
```

### Fix Strategy
**Option 1**: Add `pdf_url` to all INSERT statements
```python
cursor.execute("""
    INSERT INTO hansard_sessions (term_id, date, title, pdf_url) 
    VALUES (1, '2024-01-01', 'test', 'http://example.com/test.pdf')
""")
```

**Option 2**: Make `pdf_url` nullable in schema (if appropriate)

**Recommendation**: **FIX** - Add pdf_url to test data (Option 1)
- Simple fix
- Aligns with actual schema requirements
- Tests should reflect real data structure

---

## Category 2: Property-Based Test Content Mismatch (3 failures)
**File**: `tests/integration/test_comprehensive_validation.py`

### Root Cause
Property-based tests are generating random content, but the validation expects exact matches.

### Affected Tests
1. `test_download_validation_checks_file_existence`
2. `test_download_validation_checks_database_metadata`
3. `test_download_validation_checks_file_path_validity`

### Example Error
```
AssertionError: Comprehensive validation failed: File content must match downloaded content. 
Expected 100 bytes, found 181 bytes.
```

### Issue
The test generates random PDF content but then expects it to match exactly. The random generation is producing different sizes.

### Fix Strategy
**Option 1**: Use fixed test data instead of random generation
**Option 2**: Adjust validation to check content hash instead of exact bytes
**Option 3**: Remove these tests if they're testing implementation details

**Recommendation**: **INVESTIGATE** - Need to see test code to determine intent
- If testing file integrity: use content hashing
- If testing validation logic: use fixed test data
- May be over-testing implementation details

---

## Category 3: Missing Test Fixture (2 failures)
**File**: `tests/unit/test_session_linking_property.py`

### Root Cause
```python
NameError: name 'create_temp_db' is not defined
```

### Affected Tests
1. `test_session_linking_updates_database`
2. `test_session_linking_without_existing_pdf_record`

### Issue
Tests reference `create_temp_db()` function that doesn't exist or isn't imported.

### Fix Strategy
**Option 1**: Import the fixture from conftest or another module
**Option 2**: Define the fixture in the test file
**Option 3**: Use existing temp_db fixture from conftest

**Recommendation**: **FIX** - Import or define missing fixture
- Check conftest.py for existing temp_db fixtures
- Likely a simple import issue

---

## Category 4: Log Message Mismatch (2 failures)
**File**: `tests/integration/test_scraper.py`

### Root Cause
Test expects log message "Skipping download" but actual log says "Download skipped"

### Affected Tests
1. `TestSkipReasonLoggingProperty::test_skip_reason_logging_property`
2. `TestDownloadDecisionLogicProperties::test_download_decision_logic_property`

### Example Error
```python
assert 'Skipping download' in log_output
# But log contains: "Download skipped: URL=..."
```

### Fix Strategy
**Option 1**: Update test to match actual log message
```python
assert 'Download skipped' in log_output
```

**Option 2**: Update code to use expected log message

**Recommendation**: **FIX** - Update test assertion (Option 1)
- Log message is more descriptive as-is
- Simple test update

---

## Category 5: Property-Based Test in Scraper (1 failure)
**File**: `tests/scraper/test_properties.py`

### Root Cause
Same as Category 4 - log message mismatch

### Affected Test
1. `TestDownloadDecisionLogicProperties::test_download_decision_logic_property`

### Fix Strategy
Same as Category 4

**Recommendation**: **FIX** - Update test assertion

---

## Category 6: File Performance Tests (2 failures)
**File**: `tests/integration/test_file_performance_property.py`

### Root Cause
**NEED INVESTIGATION** - Not yet examined

### Affected Tests
1. `test_individual_file_performance`
2. `test_all_files_performance_summary`

### Likely Issues
- Performance thresholds too strict
- Environment-specific timing issues
- Missing test data

**Recommendation**: **INVESTIGATE** - Run individually to see errors

---

## Category 7: Suite Performance Test (1 failure)
**File**: `tests/integration/test_suite_performance_property.py`

### Root Cause
**NEED INVESTIGATION** - Not yet examined

### Affected Test
1. `test_complete_suite_performance`

### Likely Issues
- Performance threshold too strict
- Environment-specific
- May be flaky

**Recommendation**: **INVESTIGATE or REMOVE** - Performance tests are often flaky

---

## Category 8: End-to-End Test (1 failure)
**File**: `tests/end_to_end/test_end_to_end.py`

### Root Cause
**NEED INVESTIGATION** - Not yet examined

### Affected Test
1. `TestDownloadTrackingIntegration::test_session_linking_after_processing`

### Likely Issues
- May be related to pdf_url schema issue
- Integration test dependencies

**Recommendation**: **INVESTIGATE** - Run individually to see error

---

## Summary by Fix Difficulty

### Easy Fixes (11 tests - 61%)
1. **Database schema issues** (6 tests) - Add pdf_url to INSERT statements
2. **Log message mismatch** (3 tests) - Update assertion strings
3. **Missing fixture** (2 tests) - Import or define create_temp_db

### Need Investigation (7 tests - 39%)
1. **Property-based validation** (3 tests) - Understand test intent
2. **Performance tests** (3 tests) - May be flaky/environment-specific
3. **End-to-end test** (1 test) - Need to see error

## Recommended Action Plan

### Phase 1: Quick Wins (11 tests)
1. Fix database schema issues (6 tests) - 10 minutes
2. Fix log message assertions (3 tests) - 5 minutes
3. Fix missing fixture (2 tests) - 5 minutes

### Phase 2: Investigation (7 tests)
1. Run performance tests individually
2. Run end-to-end test individually
3. Review property-based validation tests
4. Decide: fix, adjust, or remove

### Expected Outcome
- After Phase 1: 7 failures remaining (0.8% failure rate)
- After Phase 2: 0-3 failures remaining (0-0.3% failure rate)

## Next Steps
1. Start with Phase 1 fixes (easy wins)
2. Re-run test suite
3. Investigate remaining failures
4. Make final decisions on problematic tests
