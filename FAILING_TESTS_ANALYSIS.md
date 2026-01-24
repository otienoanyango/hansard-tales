# Failing Tests Analysis

## Summary (UPDATED)
- **Total Tests**: 921
- **Passing**: 896 (97.3%) ⬆️ +32
- **Failing**: 18 (2.0%) ⬇️ -32
- **Skipped**: 7 (0.8%)

## Previous Status
- **Passing**: 864 (93.8%)
- **Failing**: 50 (5.4%)

## Breakdown by Category

### 1. Template Tests (30 failures) - `tests/unit/test_templates.py` ✅ FIXED
**Status**: **FIXED** - All 30 tests now passing

**Issue**: Path calculation error - tests looked for templates in wrong location

**Root Cause**: 
```python
template_dir = Path(__file__).parent.parent / 'templates'
```
This resolved to `tests/templates` but should be `hansard-tales/templates`

**Fix Applied**: Changed to:
```python
template_dir = Path(__file__).parent.parent.parent / 'templates'
```

**Result**: 30/30 tests passing (100%)

---

### 2. Historical Data Processing Tests (6 failures) - `tests/integration/test_process_historical_data.py`
**Affected Tests**:
- `test_already_processed`
- `test_clean_database_data_deletion`
- `test_quality_assurance`
- `test_process_single_pdf_with_force`
- `test_quality_assurance_with_duplicates`
- `test_quality_assurance_with_bills`

**Need Investigation**: Run individually to see specific error messages

---

### 3. Comprehensive Validation Tests (3 failures) - `tests/integration/test_comprehensive_validation.py`
**Affected Tests**:
- `test_download_validation_checks_file_existence`
- `test_download_validation_checks_database_metadata`
- `test_download_validation_checks_file_path_validity`

**Need Investigation**: Run individually to see specific error messages

---

### 4. Session Linking Property Tests (2 failures) - `tests/unit/test_session_linking_property.py`
**Affected Tests**:
- `test_session_linking_updates_database`
- `test_session_linking_without_existing_pdf_record`

**Need Investigation**: Property-based tests - may need adjustment or removal

---

### 5. File Performance Property Tests (2 failures) - `tests/integration/test_file_performance_property.py`
**Affected Tests**:
- `test_individual_file_performance`
- `test_all_files_performance_summary`

**Need Investigation**: Performance tests - may be environment-specific

---

### 6. Scraper Integration Tests (2 failures) - `tests/integration/test_scraper.py`
**Affected Tests**:
- `test_skip_reason_logging_property`
- `test_download_decision_logic_property`

**Need Investigation**: Property-based tests

---

### 7. Scraper Property Tests (1 failure) - `tests/scraper/test_properties.py`
**Affected Test**:
- `test_download_decision_logic_property`

**Need Investigation**: Property-based test

---

### 8. Suite Performance Property Test (1 failure) - `tests/integration/test_suite_performance_property.py`
**Affected Test**:
- `test_complete_suite_performance`

**Need Investigation**: Performance test - may be environment-specific

---

### 9. End-to-End Test (1 failure) - `tests/end_to_end/test_end_to_end.py`
**Affected Test**:
- `test_session_linking_after_processing`

**Need Investigation**: Integration test

---

### 10. MP Data Scraper Test (1 failure) - `tests/unit/test_mp_data_scraper.py`
**Affected Test**:
- `test_fetch_page_real`

**Likely Issue**: Network-dependent test that should be mocked or removed

**Recommendation**: **REMOVE or MOCK** - Real network calls in tests are unreliable

---

## Recommended Actions

### Immediate Fixes (High Confidence)
1. **Fix template tests** (30 tests) - Simple path correction
2. **Review MP data scraper test** - Remove or mock network call

### Investigation Required
3. **Historical data processing tests** (6 tests) - Need to see error details
4. **Comprehensive validation tests** (3 tests) - Need to see error details
5. **Property-based tests** (5 tests across multiple files) - May need adjustment
6. **Performance tests** (3 tests) - May be environment-specific, consider removing
7. **End-to-end test** (1 test) - Need to see error details

### Priority Order
1. Fix template tests (30 failures → 0, easy win)
2. Investigate and fix/remove MP scraper network test (1 failure)
3. Investigate historical data processing tests (6 failures)
4. Investigate comprehensive validation tests (3 failures)
5. Review property-based tests (5 failures) - may need design review
6. Review performance tests (3 failures) - may be flaky
7. Review end-to-end test (1 failure)

## Next Steps
1. Fix template path issue
2. Run tests again to confirm fix
3. Investigate remaining failures one category at a time
4. Decide: fix, adjust, or remove each failing test
