# Hansard Scraper Date Extraction Fix

## Problem

The workflow was failing to download Hansard PDFs because:

1. **Date extraction was failing** - The scraper only had regex patterns for American date format ("December 4, 2025") but the Kenyan parliament uses British date format ("4th December 2025")

2. **Crash on None date** - When date extraction failed and returned `None`, the `download_pdf` method crashed trying to call `date.replace('-', '')` on None

3. **No downloads occurred** - The workflow showed "Hansards downloaded: 0 (0 skipped, 0 failed) (error)"

## Root Cause

The `extract_date()` method in `hansard_scraper.py` only used regex patterns and didn't leverage the `dateparser` library that was already installed and used elsewhere in the codebase.

Example failing title: `"Hansard Report - Wednesday, 15th October 2025 - Evening Sitting"`

The regex patterns couldn't match:
- British format with ordinal suffixes: "15th October 2025"
- Day-before-month format: "4th December 2025"

## Solution Implemented

### 1. Added dateparser Integration

Updated `hansard_tales/scrapers/hansard_scraper.py`:

```python
# Import dateparser with fallback
try:
    import dateparser
    DATEPARSER_AVAILABLE = True
except ImportError:
    DATEPARSER_AVAILABLE = False
    logger.warning("dateparser not installed...")
```

### 2. Enhanced extract_date() Method

The method now:
1. **First tries dateparser** (if available) using `search_dates()` to find dates within text
2. **Falls back to regex patterns** if dateparser fails or isn't installed
3. **Added British date format pattern** as additional fallback

Key improvements:
- Uses `DATE_ORDER='DMY'` for British/Kenyan format
- Handles ordinal suffixes (1st, 2nd, 3rd, 4th, etc.)
- Can extract dates from text with surrounding content
- More robust and flexible

### 3. Fixed None Date Crash

Added validation in `download_pdf()`:

```python
# Handle None or empty date
if not date:
    logger.warning(f"No date provided for {url}, cannot generate standardized filename")
    return False
```

Now returns `False` instead of crashing when date is None.

### 4. Added Comprehensive Tests

Updated `tests/scraper/test_date_extraction.py` with new tests:
- British format with ordinals (1st, 2nd, 3rd, 15th, etc.)
- British format without ordinals
- Dateparser-specific formats
- Edge cases (empty string, None, URL-encoded text)

## Test Results

All 18 date extraction tests pass:

```
tests/scraper/test_date_extraction.py::TestDateExtraction::test_extract_date_british_format_with_ordinal PASSED
tests/scraper/test_date_extraction.py::TestDateExtraction::test_extract_date_british_format_1st PASSED
tests/scraper/test_date_extraction.py::TestDateExtraction::test_extract_date_british_format_2nd PASSED
tests/scraper/test_date_extraction.py::TestDateExtraction::test_extract_date_british_format_3rd PASSED
tests/scraper/test_date_extraction.py::TestDateExtraction::test_extract_date_with_dateparser PASSED
... (18 passed total)
```

## Verification

Tested with real parliament website data:

```
Found 29 hansards on page 1
Dates extracted: 29/29 ✅

Examples:
1. 2025-12-04 - Order Paper For Thursday, 4th December 2025 - Evening Sitting
2. 2025-12-04 - Hansard Report - Thursday, 4th December 2025 - Evening Sitting
3. 2025-12-04 - Hansard Report - Thursday, 4th December 2025 - Afternoon Sitting
```

**Before fix:** 0/29 dates extracted (all None)
**After fix:** 29/29 dates extracted (100% success)

## Impact

This fix enables:
- ✅ Successful Hansard PDF downloads
- ✅ Proper date-based filtering
- ✅ Standardized filename generation
- ✅ Complete end-to-end workflow execution

## Files Modified

1. `hansard_tales/scrapers/hansard_scraper.py`
   - Added dateparser import with fallback
   - Enhanced `extract_date()` method
   - Added None date validation in `download_pdf()`

2. `tests/scraper/test_date_extraction.py`
   - Added 10 new test cases
   - Total: 18 tests covering all date formats

## Next Steps

The workflow should now work correctly. You can run:

```bash
./scripts/run_workflow.py --start-date 2022-09-08 --end-date 2027-09-07
```

This will:
1. Scrape MPs (already working)
2. Scrape Hansards with proper date extraction ✅ (now fixed)
3. Download PDFs with standardized filenames ✅ (now fixed)
4. Process PDFs and extract statements
5. Generate search index
6. Generate static site

## Dependencies

The fix requires `dateparser` which is already installed:
```bash
pip install dateparser  # Already in requirements.txt
```

If dateparser is not available, the scraper falls back to regex patterns including the new British date format pattern.
