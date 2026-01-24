# PDF Migration Complete ✅

## Summary

Successfully migrated 250 PDFs from `data/pdfs/` to `data/pdfs/hansard-report/` with standardized naming.

## What Was Done

### 1. Created Migration Script
- **File**: `scripts/migrate_pdfs.py`
- **Features**:
  - Extracts dates from various filename formats
  - Generates standardized names: `YYYYMMDD_n_TYPE.pdf`
  - Preserves session type (A/P/E)
  - Supports dry-run mode

### 2. Fixed Date Extraction
- **File**: `hansard_tales/process_historical_data.py`
- **Fix**: Updated regex to support standardized filename format
- **Result**: Date filtering now works correctly

### 3. Migrated PDFs
- **Source**: `data/pdfs/` (251 PDFs)
- **Target**: `data/pdfs/hansard-report/` (250 PDFs)
- **Skipped**: 1 PDF (ORDER PAPER, not a Hansard report)
- **Date Range**: September 2023 to December 2025

### 4. Created Documentation
- `docs/PDF_MIGRATION_GUIDE.md` - Complete migration guide
- `docs/PDF_MIGRATION_SUMMARY.md` - Technical summary
- Updated `docs/QUICK_REFERENCE_FORCE_AND_CLEAN.md`

## Verification

### Date Filtering Test

**Before Fix:**
```bash
$ hansard-process-historical --start-date "5 months ago" --dry-run
Found 250 PDFs, 250 within date range  # WRONG - all PDFs included
```

**After Fix:**
```bash
$ hansard-process-historical --start-date "5 months ago" --dry-run
Parsed start date: '5 months ago' → 2025-08-21
Found 250 PDFs, 26 within date range  # CORRECT - only recent PDFs
Skipped 224 PDFs outside date range
```

## Next Steps

### 1. Process Historical Data

Now you can process your historical PDFs with date filtering:

```bash
# Process last 5 months
hansard-process-historical --start-date "5 months ago" --force --workers 6

# Process all 2024 data
hansard-process-historical --year 2024 --force --workers 6

# Process specific date range
hansard-process-historical --start-date 2024-01-01 --end-date 2024-12-31 --force --workers 6
```

### 2. Clean Database (Optional)

If you want to start fresh:

```bash
# Backup and clean database, then process
hansard-process-historical --clean --start-date "2024-01-01" --force --workers 6
```

This will:
- Create backup: `data/hansard_backup_YYYYMMDD_HHMMSS.db`
- Remove all hansard_sessions and statements
- Process PDFs from 2024 onwards

### 3. Monitor Processing

```bash
# Save output to log file
hansard-process-historical --start-date "2024-01-01" --force --workers 6 2>&1 | tee processing.log
```

## Key Features

### Duplicate Prevention
- Content hashing prevents duplicate statements
- Safe to use `--force` flag
- Duplicates automatically skipped during insertion

### Parallel Processing
- Use `--workers 4-8` for faster processing
- Default: 4 workers
- Recommended: 6-8 workers for large datasets

### Date Filtering
- Natural language: `"5 months ago"`, `"last week"`, `"yesterday"`
- ISO format: `2024-01-01`
- Filters existing PDFs in `data/pdfs/hansard-report/`

## Files Structure

```
data/
├── pdfs/
│   ├── hansard-report/          # Standardized PDFs (250 files)
│   │   ├── 20230926_0_P.pdf
│   │   ├── 20251204_0_E.pdf
│   │   └── ...
│   └── [old PDFs]               # Original PDFs (can be deleted)
└── hansard.db                   # Database

scripts/
└── migrate_pdfs.py              # Migration script

docs/
├── PDF_MIGRATION_GUIDE.md       # Migration documentation
├── PDF_MIGRATION_SUMMARY.md     # Technical summary
└── QUICK_REFERENCE_FORCE_AND_CLEAN.md  # Updated reference
```

## Troubleshooting

### PDFs Not Being Processed

1. **Check PDF location**:
   ```bash
   ls data/pdfs/hansard-report/ | wc -l
   ```

2. **Verify date extraction**:
   ```bash
   python -c "from pathlib import Path; from hansard_tales.process_historical_data import _extract_date_from_filename; print(_extract_date_from_filename(Path('data/pdfs/hansard-report/20251204_0_P.pdf')))"
   ```

3. **Test with dry-run**:
   ```bash
   hansard-process-historical --start-date "2024-01-01" --dry-run
   ```

### Date Range Issues

If date filtering isn't working:

1. Check the parsed date:
   ```bash
   hansard-process-historical --start-date "5 months ago" --dry-run | head -5
   ```

2. Verify PDFs exist in that range:
   ```bash
   ls data/pdfs/hansard-report/2024*.pdf | wc -l
   ```

## Documentation

- **Migration Guide**: `docs/PDF_MIGRATION_GUIDE.md`
- **Technical Summary**: `docs/PDF_MIGRATION_SUMMARY.md`
- **Quick Reference**: `docs/QUICK_REFERENCE_FORCE_AND_CLEAN.md`
- **Duplicate Prevention**: `docs/DATABASE_DUPLICATE_PREVENTION.md`
- **Parallelization**: `docs/PARALLELIZATION_DESIGN.md`

## Success Metrics

✅ 250 PDFs migrated successfully  
✅ Date extraction working correctly  
✅ Date filtering working correctly  
✅ Standardized naming convention  
✅ Comprehensive documentation  
✅ Ready for historical data processing  

## Questions Answered

1. **Does reprocessing of PDF via --force lead to duplicates?**
   - ✅ No, duplicates are automatically prevented using content hashing

2. **Can we use existing PDFs instead of redownloading?**
   - ✅ Yes, migration script moves them to standardized location

3. **Why doesn't --start-date work?**
   - ✅ Fixed - date extraction now supports standardized filenames

4. **How to clean database before processing?**
   - ✅ Use `--clean` flag (creates backup first)

## Ready to Process! 🚀

Your PDFs are now migrated and ready for processing. Run:

```bash
hansard-process-historical --start-date "5 months ago" --force --workers 6
```

This will process all PDFs from the last 5 months with 6 parallel workers, automatically skipping duplicates.
