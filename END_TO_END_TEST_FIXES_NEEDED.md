# End-to-End Test Failures - Root Causes and Fixes

## Test Failures Summary

From the earlier test run:
- **12 failed**, 2 passed, 3 skipped
- Tests are slow because they're making **real HTTP requests**
- Tests expect exceptions but workflow returns error status instead

## Root Causes

### 1. Incomplete Mocking

**Problem:** Tests mock some components but not all, causing real network calls.

**Example from `test_workflow_step_failure_stops_execution`:**
```python
# Mocks MP scraper
with patch('hansard_tales.workflow.orchestrator.MPDataScraper') as mock_mp_scraper:
    mock_mp_instance.scrape_all.side_effect = Exception("Network error")
    
    # But doesn't mock Hansard scraper!
    # When MP scraper fails, workflow continues to Hansard scraping
    # Hansard scraper makes REAL HTTP requests
```

### 2. Workflow Doesn't Raise Exceptions

**Problem:** Workflow catches all exceptions and returns error status, but continues execution.

**Current behavior:**
```python
def _scrape_mps(self):
    try:
        # ... scraping logic
    except Exception as e:
        logger.error(f"MP scraping failed: {e}")
        return {'status': 'error', 'error': str(e)}  # Returns, doesn't raise!

def run_full_workflow(self):
    results['mps'] = self._scrape_mps()  # Gets error status
    # No check here!
    results['hansards'] = self._scrape_hansards()  # Continues anyway!
```

**Expected behavior (per docstring):**
```python
def run_full_workflow(self):
    """
    Raises:
        Exception: If any step fails  # <-- This doesn't happen!
    """
```

### 3. Database Schema Mismatch

**Problem:** Tests use `initialize_database()` which doesn't include migrations from Task 4.

**Missing columns:**
- `downloaded_pdfs.period_of_day`
- `downloaded_pdfs.session_id`
- `mps.county`

**Error:**
```
sqlite3.OperationalError: table downloaded_pdfs has no column named period_of_day
```

### 4. HTTP Mocking Doesn't Work

**Problem:** Patching `requests.Session` after scraper instantiation doesn't prevent real requests.

**Why:**
```python
class HansardScraper:
    def __init__(self, ...):
        self.session = requests.Session()  # Created in __init__
        
# Test patches after instantiation
scraper = HansardScraper(...)  # Session already created
with patch('requests.Session'):  # Too late!
    scraper.download_pdf(...)  # Uses real session
```

## Detailed Issues

### Issue 1: test_workflow_step_failure_stops_execution

**What happens:**
1. Test mocks MP scraper to raise exception
2. Workflow catches exception, returns `{'status': 'error'}`
3. Workflow continues to Hansard scraping (not mocked)
4. Hansard scraper makes real HTTP request to parliament.go.ke
5. Test hangs waiting for network call
6. Eventually fails: "DID NOT RAISE <class 'Exception'>"

**Fix needed:**
- Either: Make workflow raise exceptions on step failure
- Or: Update test to check for error status instead of exception

### Issue 2: test_download_tracking_records_metadata

**What happens:**
1. Test creates scraper without mocking HTTP
2. Calls `scraper.download_pdf()` with test URL
3. Scraper tries to make real HTTP request
4. Request fails with network error
5. Test fails: `assert False is True`

**Fix needed:**
- Mock `requests.Session` before creating scraper
- Or: Inject mock session into scraper constructor

### Issue 3: test_duplicate_detection_* tests

**What happens:**
1. Test tries to insert into `downloaded_pdfs` table
2. SQL includes `period_of_day` column
3. Column doesn't exist (migration not run)
4. Error: `sqlite3.OperationalError: table downloaded_pdfs has no column named period_of_day`

**Fix needed:**
- Run migration after `initialize_database()`
- Or: Update `initialize_database()` to include all columns

### Issue 4: test_complete_workflow_with_mocked_scrapers

**What happens:**
1. Test tries to insert MP with `county` column
2. Column doesn't exist in schema
3. Error: `sqlite3.OperationalError: table mps has no column named county`

**Fix needed:**
- Check actual `mps` table schema
- Update test to match schema or update schema to include `county`

## Recommended Fixes

### Fix 1: Complete the Mocking

Mock ALL external dependencies in each test:

```python
def test_workflow_step_failure_stops_execution(self, temp_workspace):
    with patch('hansard_tales.workflow.orchestrator.MPDataScraper') as mock_mp:
        with patch('hansard_tales.workflow.orchestrator.HansardScraper') as mock_hansard:
            with patch('hansard_tales.workflow.orchestrator.HistoricalDataProcessor') as mock_proc:
                mock_mp.return_value.scrape_all.side_effect = Exception("Network error")
                
                orchestrator = WorkflowOrchestrator(...)
                
                # Now test behavior - either check for error status or exception
                results = orchestrator.run_full_workflow()
                assert results['mps']['status'] == 'error'
```

### Fix 2: Decide on Error Handling Strategy

**Option A: Make workflow raise exceptions (breaking change)**
```python
def run_full_workflow(self):
    results['mps'] = self._scrape_mps()
    if results['mps']['status'] == 'error':
        raise Exception(f"MP scraping failed: {results['mps']['error']}")
    
    results['hansards'] = self._scrape_hansards()
    if results['hansards']['status'] == 'error':
        raise Exception(f"Hansard scraping failed: {results['hansards']['error']}")
    # ... etc
```

**Option B: Update tests to check status (simpler)**
```python
def test_workflow_step_failure_stops_execution(self, temp_workspace):
    # ... setup mocks
    
    results = orchestrator.run_full_workflow()
    
    # Check for error status instead of exception
    assert results['mps']['status'] == 'error'
    assert 'Network error' in results['mps']['error']
```

### Fix 3: Run Migrations in Tests

```python
@pytest.fixture
def temp_workspace(self):
    # ... create database
    initialize_database(str(db_path))
    
    # Run migrations
    from hansard_tales.database.migrations.add_download_metadata import migrate
    migrate(str(db_path))
    
    yield {...}
```

### Fix 4: Mock HTTP at Session Level

```python
def test_download_tracking_records_metadata(self, temp_workspace):
    from hansard_tales.scrapers.hansard_scraper import HansardScraper
    
    db_path = temp_workspace['db_path']
    storage = temp_workspace['storage']
    
    # Mock at the requests module level BEFORE creating scraper
    with patch('hansard_tales.scrapers.hansard_scraper.requests.Session') as MockSession:
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content = lambda chunk_size: [b'PDF content']
        mock_session.get.return_value = mock_response
        MockSession.return_value = mock_session
        
        # Now create scraper - it will use mocked session
        scraper = HansardScraper(storage=storage, db_path=str(db_path))
        
        # Test will use mocked HTTP
        result = scraper.download_pdf(url, title, date)
```

## Priority Order

1. **HIGH: Fix database schema** - Blocks most tests
   - Run migrations in test fixtures
   - Or update `initialize_database()` to include all columns

2. **HIGH: Complete mocking** - Prevents real network calls
   - Mock all scrapers in workflow tests
   - Mock HTTP session in scraper tests

3. **MEDIUM: Clarify error handling** - Fixes test expectations
   - Decide: raise exceptions or return status?
   - Update either code or tests to match

4. **LOW: Improve test isolation** - Better test design
   - Use dependency injection for easier mocking
   - Consider using `responses` library for HTTP mocking

## Next Steps

1. Fix database schema issues first (blocks everything)
2. Update tests to mock all external dependencies
3. Decide on error handling strategy and implement consistently
4. Re-run tests to verify fixes
5. Add integration tests that DO make real requests (marked with `@pytest.mark.integration`)

## Conclusion

The tests revealed good integration issues but need fixes to:
- Use complete mocking to avoid real network calls
- Match database schema with migrations
- Align expectations with actual workflow behavior

Once fixed, these tests will provide valuable validation of the end-to-end workflow.
