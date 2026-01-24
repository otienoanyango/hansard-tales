# PDF Migration Guide

## Overview

This guide explains how to migrate existing Hansard PDFs to the standardized naming convention and directory structure used by the Hansard Tales processing pipeline.

## Why Migrate?

The processing pipeline expects PDFs to be:
1. Located in `data/pdfs/hansard-report/`
2. Named in standardized format: `YYYYMMDD_n_TYPE.pdf`
   - `YYYYMMDD`: Date in ISO format (e.g., `20250314`)
   - `n`: Counter for multiple PDFs on same date (0, 1, 2, ...)
   - `TYPE`: Session type - `A` (Afternoon), `P` (Plenary), `E` (Evening), or omitted

## Migration Script

The `scripts/migrate_pdfs.py` script handles the migration automatically.

### Features

- Extracts dates from various filename formats
- Generates standardized filenames
- Handles multiple PDFs per date
- Preserves session type information (A/P/E)
- Tracks migrations in database (if available)
- Supports dry-run mode for preview

### Usage

#### 1. Preview Migration (Dry Run)

```bash
python scripts/migrate_pdfs.py --dry-run
```

This shows what would be migrated without making changes.

#### 2. Perform Migration

```bash
python scripts/migrate_pdfs.py
```

This copies PDFs to the standardized location with new names.

#### 3. Delete Originals (Optional)

```bash
python scripts/migrate_pdfs.py --delete-originals
```

⚠️ **Warning**: This deletes original files after migration. Use with caution!

### Options

```
--source-dir PATH       Source directory (default: data/pdfs)
--target-dir PATH       Target directory (default: data/pdfs/hansard-report)
--db-path PATH          Database path (default: data/hansard.db)
--dry-run               Preview without making changes
--delete-originals      Delete originals after migration (requires confirmation)
```

## Supported Filename Formats

The migration script recognizes these formats:

### 1. URL-Encoded Format
```
Hansard%20Report%20-%20Thursday%2C%204th%20December%202025%20%28P%29.pdf
→ 20251204_0_P.pdf
```

### 2. Long Format
```
Hansard Report - Wednesday, 3rd December 2025 (A).pdf
→ 20251203_0_A.pdf
```

### 3. ISO Format
```
Hansard_Report_2025-12-04.pdf
→ 20251204_0.pdf
```

## Migration Example

### Before Migration

```
data/pdfs/
├── Hansard%20Report%20-%20Thursday%2C%204th%20December%202025%20%28P%29.pdf
├── Hansard%20Report%20-%20Thursday%2C%204th%20December%202025%20%28E%29.pdf
└── Hansard_Report_2025-12-04.pdf
```

### After Migration

```
data/pdfs/hansard-report/
├── 20251204_0_P.pdf  (Plenary session)
├── 20251204_1_E.pdf  (Evening session)
└── 20251204_2.pdf    (No session type)
```

## Processing After Migration

Once PDFs are migrated, you can process them with date filtering:

```bash
# Process all migrated PDFs
hansard-process-historical --force --workers 6

# Process specific date range
hansard-process-historical --start-date "5 months ago" --force --workers 6

# Process specific year
hansard-process-historical --year 2024 --force --workers 6
```

## Troubleshooting

### PDFs Not Being Processed

If PDFs aren't being processed after migration:

1. **Check filename format**: Ensure PDFs are in standardized format
   ```bash
   ls data/pdfs/hansard-report/ | head -10
   ```

2. **Verify date extraction**: Test date extraction
   ```bash
   python -c "from pathlib import Path; from hansard_tales.process_historical_data import _extract_date_from_filename; print(_extract_date_from_filename(Path('data/pdfs/hansard-report/20251204_0_P.pdf')))"
   ```

3. **Check date range**: Ensure PDFs are within specified date range
   ```bash
   hansard-process-historical --start-date "2024-01-01" --dry-run
   ```

### Date Extraction Failures

If dates cannot be extracted from filenames:

1. Check the filename format matches supported patterns
2. Ensure the date is valid (e.g., not February 30th)
3. Check for URL encoding issues

The script will report files where date extraction failed:
```
⚠️  Cannot extract date from: filename.pdf
```

### Database Tracking

The migration script tracks PDFs in the `downloaded_pdfs` table if it exists. If the table doesn't exist yet:

```
ℹ️  downloaded_pdfs table doesn't exist yet, skipping database tracking
```

This is normal and doesn't affect migration. The table will be created when you run the processing pipeline.

## Best Practices

1. **Always run dry-run first**: Preview changes before migrating
   ```bash
   python scripts/migrate_pdfs.py --dry-run
   ```

2. **Keep originals initially**: Don't use `--delete-originals` until you've verified the migration

3. **Backup database**: Before processing, backup your database
   ```bash
   cp data/hansard.db data/hansard_backup_$(date +%Y%m%d).db
   ```

4. **Process incrementally**: Start with a small date range to verify everything works
   ```bash
   hansard-process-historical --start-date "1 week ago" --force --workers 2
   ```

5. **Monitor processing**: Watch for errors during processing
   ```bash
   hansard-process-historical --start-date "2024-01-01" --force --workers 6 2>&1 | tee processing.log
   ```

## See Also

- [Quick Reference: Force and Clean Options](QUICK_REFERENCE_FORCE_AND_CLEAN.md)
- [Database Duplicate Prevention](DATABASE_DUPLICATE_PREVENTION.md)
- [Parallelization Design](PARALLELIZATION_DESIGN.md)
