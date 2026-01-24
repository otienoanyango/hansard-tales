# PDF Migration and Date Filtering Fix - Summary

## Problem Statement

The user reported two issues:

1. **Existing PDFs not being used**: 251 PDFs already downloaded in `data/pdfs/` were not being processed
2. **Date filtering not working**: Running `hansard-process-historical --start-date "5 months ago"` showed "Date range: 2025-12-03 to 2025-12-04" and didn't process historical PDFs

## Root Causes

### Issue 1: PDF Location Mismatch
- Processing pipeline expected PDFs in `data/pdfs/hansard-report/`
- Existing PDFs were in `data/pdfs/` (root level)
- Filenames were URL-encoded and non-standardized

### Issue 2: Date Extraction Failure
- Date extraction regex didn't support the new standardized filename format
- After migration, filenames changed from:
  - `Hansard%20Report%20-%20Thursday%2C%204th%20December%202025%20%28P%29.pdf`
  - To: `20251204_0_P.pdf`
- The regex only looked for `YYYY-MM-DD` format with dashes, not `YYYYMMDD` format

## Solutions Implemented

### 1. PDF Migration Script (`scripts/migrate_pdfs.py`)

Created a comprehensive migration script that:

**Features:**
- Extracts dates from various filename formats (URL-encoded, long format, ISO format)
- Generates standardized filenames: `YYYYMMDD_n_TYPE.pdf`
  - `YYYYMMDD`: Date in ISO format (e.g., `20250314`)
  - `n`: Counter for multiple PDFs on same date (0, 1, 2, ...)
  - `TYPE`: Session type - `A` (Afternoon), `P` (Plenary), `E` (Evening)
- Handles multiple PDFs per date with automatic counters
- Preserves session type information from original filenames
- Tracks migrations in database (if `downloaded_pdfs` table exists)
- Supports dry-run mode for preview
- Optional deletion of originals (with confirmation)

**Usage:**
```bash
# Preview migration
python scripts/migrate_pdfs.py --dry-run

# Perform migration
python scripts/migrate_pdfs.py

# Delete originals after migration (with confirmation)
python scripts/migrate_pdfs.py --delete-originals
```

**Results:**
- Successfully migrated 250 out of 251 PDFs
- 1 PDF skipped (ORDER PAPER, not a Hansard report)
- PDFs now in standardized location: `data/pdfs/hansard-report/`
- Date range: September 2023 to December 2025

### 2. Date Extraction Fix

Updated `_extract_date_from_filename()` in `hansard_tales/process_historical_data.py`:

**Before:**
```python
# Only supported YYYY-MM-DD format
iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
```

**After:**
```python
# Try standardized format first: YYYYMMDD_n.pdf or YYYYMMDD_n_TYPE.pdf
standardized_match = re.search(r'^(\d{4})(\d{2})(\d{2})_\d+', filename)
if standardized_match:
    return date(int(standardized_match.group(1)), int(standardized_match.group(2)), int(standardized_match.group(3)))

# Then try ISO format: YYYY-MM-DD
iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
```

**Supported Formats:**
1. Standardized: `20250314_0_A.pdf`, `20251204_2.pdf`
2. ISO with dashes: `Hansard_Report_2025-12-04.pdf`
3. Long format: `Hansard Report - Wednesday, 3rd December 2025 (P).pdf`

### 3. Documentation

Created comprehensive documentation:

1. **PDF Migration Guide** (`docs/PDF_MIGRATION_GUIDE.md`)
   - Complete migration workflow
   - Supported filename formats
   - Troubleshooting guide
   - Best practices

2. **Updated Quick Reference** (`docs/QUICK_REFERENCE_FORCE_AND_CLEAN.md`)
   - Added PDF migration section
   - Updated paths to reflect new structure
   - Clarified date filtering behavior

## Verification

### Before Fix
```bash
$ hansard-process-historical --start-date "5 months ago" --dry-run
Date range: 2025-12-03 to 2025-12-04
Found 250 PDFs, 250 within date range  # WRONG!
```

### After Fix
```bash
$ hansard-process-historical --start-date "5 months ago" --dry-run
Parsed start date: '5 months ago' → 2025-08-21
Date range: 2025-08-21 to present
Found 250 PDFs, 26 within date range  # CORRECT!
Skipped 224 PDFs outside date range
```

## Usage Examples

### Complete Workflow

```bash
# 1. Migrate existing PDFs
python scripts/migrate_pdfs.py

# 2. Process all migrated PDFs
hansard-process-historical --force --workers 6

# 3. Process specific date range
hansard-process-historical --start-date "5 months ago" --force --workers 6

# 4. Process specific year
hansard-process-historical --year 2024 --force --workers 6

# 5. Clean database and reprocess
hansard-process-historical --clean --start-date "2024-01-01" --force --workers 6
```

### Date Filtering Examples

```bash
# Last 5 months (natural language)
hansard-process-historical --start-date "5 months ago" --force --workers 6

# Specific date range (ISO format)
hansard-process-historical --start-date 2024-01-01 --end-date 2024-12-31 --force --workers 6

# From date onwards
hansard-process-historical --start-date 2024-06-01 --force --workers 6

# Up to date
hansard-process-historical --end-date 2024-12-31 --force --workers 6
```

## Benefits

1. **Reusability**: Existing PDFs can now be processed without re-downloading
2. **Standardization**: Consistent naming convention across all PDFs
3. **Date Filtering**: Accurate date-based filtering for targeted processing
4. **Performance**: Process only relevant PDFs, saving time and resources
5. **Maintainability**: Clear documentation and migration path for future PDFs

## Files Changed

### New Files
- `scripts/migrate_pdfs.py` - PDF migration script
- `docs/PDF_MIGRATION_GUIDE.md` - Migration documentation
- `docs/PDF_MIGRATION_SUMMARY.md` - This summary

### Modified Files
- `hansard_tales/process_historical_data.py` - Fixed date extraction
- `docs/QUICK_REFERENCE_FORCE_AND_CLEAN.md` - Added migration section

## Next Steps

1. **Run the migration** (if not already done):
   ```bash
   python scripts/migrate_pdfs.py
   ```

2. **Process historical data**:
   ```bash
   hansard-process-historical --start-date "5 months ago" --force --workers 6
   ```

3. **Monitor processing**:
   ```bash
   hansard-process-historical --start-date "2024-01-01" --force --workers 6 2>&1 | tee processing.log
   ```

4. **Verify results**:
   ```bash
   # Check database
   sqlite3 data/hansard.db "SELECT COUNT(*) FROM statements"
   sqlite3 data/hansard.db "SELECT MIN(date), MAX(date) FROM hansard_sessions WHERE processed = 1"
   ```

## See Also

- [PDF Migration Guide](PDF_MIGRATION_GUIDE.md)
- [Quick Reference: Force and Clean Options](QUICK_REFERENCE_FORCE_AND_CLEAN.md)
- [Database Duplicate Prevention](DATABASE_DUPLICATE_PREVENTION.md)
- [Parallelization Design](PARALLELIZATION_DESIGN.md)
