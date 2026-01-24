# Quick Reference: --force and --clean Flags

## TL;DR

- **`--force`**: Reprocess PDFs even if already in database. **Duplicates are automatically skipped.**
- **`--clean`**: Backup database and remove all data before processing. **Creates timestamped backup.**
- **Date filtering**: `--start-date` and `--end-date` filter **existing PDFs** in `data/pdfs/hansard-report/`, they do NOT download historical PDFs from parliament website.
- **PDF Migration**: If you have PDFs in `data/pdfs/`, migrate them first with `python scripts/migrate_pdfs.py`

## Before You Start: PDF Migration

If you have existing PDFs in `data/pdfs/` (not in the `hansard-report` subdirectory), you need to migrate them first:

```bash
# Preview migration
python scripts/migrate_pdfs.py --dry-run

# Perform migration
python scripts/migrate_pdfs.py
```

This will:
- Rename PDFs to standardized format (`YYYYMMDD_n_TYPE.pdf`)
- Move them to `data/pdfs/hansard-report/`
- Preserve session type information (A/P/E)

See [PDF Migration Guide](PDF_MIGRATION_GUIDE.md) for details.

## Important: How Date Filtering Works

⚠️ **The parliament website typically only has recent PDFs (last few days/weeks).**

When you use `--start-date` or `--end-date`:
1. The scraper downloads whatever PDFs are currently on parliament website (recent ones)
2. The processor then filters **existing PDFs in `data/pdfs/hansard-report/`** by your date range
3. Only PDFs matching your date range are processed

**Example:**
```bash
hansard-process-historical --start-date "5 months ago" --force
```

This will:
- Download any new PDFs from parliament website (probably just recent ones)
- Filter all PDFs in `data/pdfs/hansard-report/` to only those from 5 months ago onwards
- Process only the matching PDFs
- If you don't have PDFs from 5 months ago in `data/pdfs/hansard-report/`, nothing will be processed

**To process historical data:**
1. Ensure you have the historical PDFs in `data/pdfs/hansard-report/` directory (manually downloaded, migrated, or from previous scrapes)
2. Run with date range to filter and process them

## When to Use What

### Normal Processing (No Flags)
```bash
hansard-process-historical --year 2024
```
- ✅ Fastest option
- ✅ Only processes new PDFs
- ✅ Skips already-processed PDFs
- 📌 Use for: Daily/weekly updates

### Force Reprocessing (`--force`)
```bash
hansard-process-historical --year 2024 --force
```
- ✅ Reprocesses all PDFs
- ✅ Duplicates automatically skipped
- ✅ Safe to use repeatedly
- 📌 Use for: Bug fixes, algorithm improvements, data refresh

### Clean Start (`--clean`)
```bash
hansard-process-historical --year 2024 --clean
```
- ✅ Creates backup first
- ✅ Removes all old data
- ✅ Fresh start
- 📌 Use for: Complete reprocessing, testing, corruption recovery

### Both Together
```bash
hansard-process-historical --year 2024 --clean --force
```
- ✅ Clean database + force reprocess
- 📌 Use for: Complete fresh start with all PDFs

## Examples

### Reprocess Last 5 Months
```bash
hansard-process-historical --start-date "5 months ago" --force --workers 6
```

### Clean and Process 2024
```bash
hansard-process-historical --year 2024 --clean --workers 8
```

### Process Specific Range (Force)
```bash
hansard-process-historical --start-date 2024-01-01 --end-date 2024-06-30 --force
```

## What Happens

### With `--force`
1. ✅ Processes all PDFs (even if already processed)
2. ✅ Extracts statements from PDFs
3. ✅ Attempts to insert into database
4. ✅ Duplicates detected by content hash
5. ✅ Duplicates silently skipped
6. ✅ Statistics show: "Duplicate statements skipped: X"

### With `--clean`
1. ✅ Creates backup: `data/hansard_backup_20260121_143022.db`
2. ✅ Removes all statements
3. ✅ Removes all hansard_sessions
4. ✅ Resets autoincrement counters
5. ✅ Processes PDFs into clean database
6. ✅ Shows backup location in output

## Backup and Restore

### List Backups
```bash
ls -lh data/hansard_backup_*.db
```

### Restore from Backup
```bash
# Copy backup to main database
cp data/hansard_backup_20260121_143022.db data/hansard.db
```

### Delete Old Backups
```bash
# Keep only last 5 backups
ls -t data/hansard_backup_*.db | tail -n +6 | xargs rm
```

## Statistics

### Normal Processing
```
Processing Statistics:
  PDFs processed successfully: 10
  Statements extracted: 2,450
```

### With `--force` (Duplicates Detected)
```
Processing Statistics:
  PDFs processed successfully: 10
  Statements extracted: 2,450
  Duplicate statements skipped: 2,450  ← All were duplicates
```

### With `--clean` (Fresh Start)
```
Step 0: Cleaning database...
  Creating backup: data/hansard_backup_20260121_143022.db
  ✓ Backup created
  Removing 12,450 statements and 50 sessions...
  ✓ Database cleaned
  ℹ️  To restore: cp data/hansard_backup_20260121_143022.db data/hansard.db

Processing Statistics:
  PDFs processed successfully: 10
  Statements extracted: 2,450  ← All new
```

## Common Scenarios

### Scenario 1: Fixed a Bug in MP Identification
```bash
# Reprocess to get better MP identification
hansard-process-historical --year 2024 --force
```
**Result:** Duplicate statements skipped, only new/different statements added.

### Scenario 2: Want to Start Completely Fresh
```bash
# Clean everything and reprocess
hansard-process-historical --year 2024 --clean
```
**Result:** Backup created, database cleaned, fresh processing.

### Scenario 3: Database Corrupted
```bash
# Restore from backup
cp data/hansard_backup_20260121_143022.db data/hansard.db

# Or clean and reprocess
hansard-process-historical --year 2024 --clean
```

### Scenario 4: Testing New Features
```bash
# Clean database for testing
hansard-process-historical --start-date "1 week ago" --clean --workers 4
```

## Safety Features

✅ **Duplicate Prevention:** Content hash prevents duplicate statements  
✅ **Automatic Backup:** `--clean` always creates backup first  
✅ **Timestamped Backups:** Never overwrites previous backups  
✅ **Statistics Tracking:** Shows how many duplicates were skipped  
✅ **Error Handling:** Graceful handling of integrity errors  

## Migration Required

For existing databases, run migration once:

```bash
python -m hansard_tales.database.migrate_add_content_hash --db-path data/hansard.db
```

This adds the `content_hash` field needed for duplicate prevention.

## Help

```bash
# Show all options
hansard-process-historical --help

# See examples
hansard-process-historical --help | grep -A 50 "Examples:"
```

## Troubleshooting

### "Duplicate statements skipped: 0" but I used --force
- Migration not run yet
- Run: `python -m hansard_tales.database.migrate_add_content_hash`

### Backup not created with --clean
- Check disk space
- Check permissions on data/ directory
- Look for error messages in output

### Want to remove all backups
```bash
rm data/hansard_backup_*.db
```

## Performance

- **`--force`**: Slower (reprocesses all PDFs)
- **`--clean`**: Fast (just deletes data)
- **Duplicate detection**: < 1% overhead
- **Backup creation**: ~1 second for 100MB database

## Best Practices

1. **Regular backups:** Use `--clean` periodically to create backups
2. **Test first:** Try on small date range before full reprocessing
3. **Monitor duplicates:** Check statistics to understand data quality
4. **Keep backups:** Don't delete backups immediately
5. **Use workers:** Add `--workers 6-8` for faster processing
