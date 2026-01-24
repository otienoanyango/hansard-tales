# Workflow Orchestration Guide

## Overview

The Hansard Tales workflow orchestrator automates the complete end-to-end pipeline from scraping parliamentary data to generating a static website. This guide explains how to use the orchestrator and customize the workflow.

## Quick Start

### Basic Usage

Run the complete workflow with default settings:

```bash
python scripts/run_workflow.py
```

This executes all five steps:
1. Scrape MPs from parliament website
2. Scrape Hansard PDFs
3. Process PDFs to extract statements
4. Generate search index
5. Generate static site

### Common Options

```bash
# Process specific date range
python scripts/run_workflow.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31

# Use more workers for faster processing
python scripts/run_workflow.py --workers 8

# Custom database and output paths
python scripts/run_workflow.py \
  --db-path data/hansard.db \
  --output-dir output/ \
  --storage-dir data/pdfs/hansard
```

## Workflow Steps

### Step 1: Scrape MPs

**Purpose**: Download current MP data from parliament website

**What it does**:
- Scrapes MP profiles from parliament.go.ke
- Extracts name, constituency, party, contact info
- Saves to JSON file for import
- Limited to 1 page in tests for speed

**Output**:
- JSON file: `data/mps_2022_parliament.json`
- Statistics: Number of MPs scraped

**Configuration**:
- Parliamentary term year (default: 2022 for 13th Parliament)
- Rate limiting delay (default: 1.0 seconds)

### Step 2: Scrape Hansards

**Purpose**: Download Hansard PDF files from parliament website

**What it does**:
- Scrapes Hansard listings from parliament.go.ke
- Checks for existing files (duplicate detection)
- Extracts period-of-day from PDF metadata
- Generates standardized filenames
- Downloads new PDFs only
- Tracks all downloads in database

**Output**:
- PDF files in storage directory
- Database records in `downloaded_pdfs` table
- Statistics: Downloaded, skipped, failed counts

**Configuration**:
- Date range filtering (start_date, end_date)
- Storage backend (filesystem, S3, etc.)
- Rate limiting and retry logic

**Duplicate Detection**:
The scraper implements smart duplicate detection:
1. **File + DB record exists**: Skip download
2. **File exists, no DB record**: Create record, skip download
3. **DB record exists, no file**: Re-download file
4. **Neither exists**: Download and create record

### Step 3: Process PDFs

**Purpose**: Extract text and identify MP statements from PDFs

**What it does**:
- Reads PDF files from storage
- Extracts text using pdfplumber
- Identifies MP names using NLP (spaCy)
- Extracts bill references
- Detects duplicate statements (content hashing)
- Links PDFs to hansard_sessions
- Updates session_id in downloaded_pdfs table

**Output**:
- Database records in:
  - `hansard_sessions` table
  - `statements` table
  - `bills` table (if bill references found)
- Statistics: PDFs processed, statements extracted, MPs identified

**Configuration**:
- Number of parallel workers (default: 4)
- Date range filtering
- Force reprocess flag
- Dry run mode

**Performance**:
- Parallel processing with ThreadPoolExecutor
- Thread-safe database operations
- Progress tracking with tqdm

### Step 4: Generate Search Index

**Purpose**: Create searchable index of MPs and statements

**What it does**:
- Queries database for all MPs
- Aggregates statement counts
- Generates JSON search index
- Optimized for client-side fuzzy search (Fuse.js)

**Output**:
- JSON file: `output/data/mp-search-index.json`
- Statistics: Number of MPs indexed, file size

**Index Structure**:
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "constituency": "Nairobi",
    "party": "Party Name",
    "statement_count": 150
  }
]
```

### Step 5: Generate Static Site

**Purpose**: Generate HTML pages for all MPs

**What it does**:
- Generates homepage with search
- Generates individual MP profile pages
- Generates party pages
- Copies static assets (CSS, JS)
- Creates mobile-friendly responsive design

**Output**:
- HTML files in `output/` directory
- Statistics: Number of pages generated

**Page Types**:
- Homepage: `index.html`
- MP profiles: `mp/{mp-id}.html`
- Party pages: `party/{party-name}.html`

## Configuration

### Command-Line Options

```bash
python scripts/run_workflow.py --help
```

**Available Options**:

| Option | Default | Description |
|--------|---------|-------------|
| `--db-path` | `data/hansard.db` | Path to SQLite database |
| `--start-date` | None | Start date (YYYY-MM-DD) |
| `--end-date` | None | End date (YYYY-MM-DD) |
| `--workers` | 4 | Number of parallel workers |
| `--output-dir` | `output` | Output directory for site |
| `--storage-dir` | `data/pdfs/hansard` | Storage directory for PDFs |

### Programmatic Usage

```python
from hansard_tales.workflow.orchestrator import WorkflowOrchestrator
from hansard_tales.storage.filesystem import FilesystemStorage

# Create storage backend
storage = FilesystemStorage("data/pdfs/hansard")

# Create orchestrator
orchestrator = WorkflowOrchestrator(
    db_path="data/hansard.db",
    storage=storage,
    start_date="2024-01-01",
    end_date="2024-12-31",
    workers=8,
    output_dir="output"
)

# Run workflow
results = orchestrator.run_full_workflow()

# Check results
print(f"Status: {results['workflow']['status']}")
print(f"MPs scraped: {results['mps']['mps_scraped']}")
print(f"PDFs processed: {results['processing']['pdfs_processed']}")
print(f"Statements: {results['processing']['statements']:,}")
```

## Error Handling

### Workflow Behavior

The workflow stops on the first error:
- If Step 1 fails, Steps 2-5 are not executed
- If Step 3 fails, Steps 4-5 are not executed
- Errors are logged with full stack traces
- Results dictionary includes error information

### Error Recovery

```python
try:
    results = orchestrator.run_full_workflow()
except Exception as e:
    print(f"Workflow failed: {e}")
    
    # Check which step failed
    if 'workflow' in results:
        failed_step = results['workflow'].get('failed_at_step')
        print(f"Failed at step: {failed_step}")
```

### Common Issues

#### Issue: No MPs Scraped

**Cause**: Parliament website may be down or structure changed

**Solution**:
1. Check parliament.go.ke is accessible
2. Verify MP scraper selectors are correct
3. Use pre-downloaded MP JSON file

#### Issue: PDF Download Failures

**Cause**: Network issues, rate limiting, or invalid URLs

**Solution**:
1. Check network connectivity
2. Reduce scraping speed (increase delay)
3. Retry failed downloads manually

#### Issue: Processing Failures

**Cause**: Corrupted PDFs, missing dependencies, or database issues

**Solution**:
1. Verify PDF files are valid
2. Check spaCy model is installed
3. Verify database schema is up to date

## Performance Optimization

### Parallel Processing

Increase workers for faster processing:

```bash
# Use 8 workers (good for 8+ CPU cores)
python scripts/run_workflow.py --workers 8

# Use 16 workers (for high-end machines)
python scripts/run_workflow.py --workers 16
```

**Guidelines**:
- Use 1 worker per CPU core
- More workers = more memory usage
- Diminishing returns beyond 8-12 workers

### Date Range Filtering

Process only recent data:

```bash
# Process last month only
python scripts/run_workflow.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31
```

**Benefits**:
- Faster processing
- Less memory usage
- Incremental updates

### Incremental Updates

For weekly updates, use date filtering:

```bash
# Process last 7 days
python scripts/run_workflow.py \
  --start-date $(date -d '7 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d)
```

## Monitoring and Logging

### Log Output

The workflow logs to stdout with timestamps:

```
2024-01-15 10:00:00 - INFO - Starting End-to-End Workflow
2024-01-15 10:00:00 - INFO - Step 1/5: Scraping MPs...
2024-01-15 10:01:30 - INFO - ✓ Step 1 complete: success
2024-01-15 10:01:30 - INFO - Step 2/5: Scraping Hansards...
```

### Redirect to File

Save logs for later analysis:

```bash
python scripts/run_workflow.py 2>&1 | tee workflow.log
```

### Statistics Output

The workflow prints a summary at the end:

```
======================================================================
WORKFLOW SUMMARY
======================================================================
Status: SUCCESS
Total time: 1234.56s

✓ MPs scraped: 349 (success)
✓ Hansards downloaded: 25 (10 skipped, 0 failed) (success)
✓ PDFs processed: 25 (success)
  └─ Statements extracted: 5,432
✓ Search index: 349 MPs indexed (success)
✓ Site generated: 400 pages (success)
======================================================================

✓ Workflow completed successfully!
  Output directory: output/
```

## Integration with CI/CD

### GitHub Actions

Example workflow for weekly updates:

```yaml
name: Weekly Update

on:
  schedule:
    - cron: '0 2 * * 0'  # Sunday 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e .
          python -m spacy download en_core_web_sm
      
      - name: Run workflow
        run: |
          python scripts/run_workflow.py \
            --start-date $(date -d '7 days ago' +%Y-%m-%d) \
            --end-date $(date +%Y-%m-%d)
      
      - name: Commit changes
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add data/ output/
          git commit -m "Weekly update: $(date +%Y-%m-%d)" || true
          git push
```

## Best Practices

### Before Running Workflow

1. **Create a backup**:
   ```bash
   python scripts/db_manager.py backup --db-path data/hansard.db
   ```

2. **Check disk space**:
   ```bash
   df -h data/
   ```

3. **Verify dependencies**:
   ```bash
   pip list | grep -E "pdfplumber|spacy|beautifulsoup4"
   ```

### After Running Workflow

1. **Verify output**:
   ```bash
   ls -lh output/
   ```

2. **Check statistics**:
   ```bash
   sqlite3 data/hansard.db "
     SELECT COUNT(*) FROM statements;
     SELECT COUNT(*) FROM downloaded_pdfs;
   "
   ```

3. **Test generated site**:
   ```bash
   cd output/
   python -m http.server 8000
   # Visit http://localhost:8000
   ```

### Maintenance

1. **Clean old backups** (keep last 10):
   ```bash
   cd data/backups/
   ls -t | tail -n +11 | xargs rm -f
   ```

2. **Vacuum database** (reclaim space):
   ```bash
   sqlite3 data/hansard.db "VACUUM;"
   ```

3. **Update MP data** (quarterly):
   ```bash
   hansard-mp-scraper --term 2022 --output data/mps_13th_parliament.json
   hansard-import-mps --file data/mps_13th_parliament.json --current
   ```

## Troubleshooting

### Workflow Hangs

**Symptoms**: Workflow stops responding, no progress

**Causes**:
- Network timeout
- Database lock
- Memory exhaustion

**Solutions**:
1. Kill process: `Ctrl+C`
2. Check system resources: `top`, `free -h`
3. Reduce workers: `--workers 2`
4. Add timeout to scraper

### Incomplete Results

**Symptoms**: Some steps succeed, others fail

**Causes**:
- Partial data availability
- Network interruptions
- Database constraints

**Solutions**:
1. Check logs for specific errors
2. Re-run workflow with date filtering
3. Process failed items manually

### Memory Issues

**Symptoms**: Out of memory errors, system slowdown

**Causes**:
- Too many parallel workers
- Large PDF files
- Insufficient RAM

**Solutions**:
1. Reduce workers: `--workers 2`
2. Process in smaller batches (date ranges)
3. Increase system swap space

## Advanced Usage

### Custom Storage Backend

Implement custom storage for S3, Azure, etc.:

```python
from hansard_tales.storage.base import StorageBackend

class S3Storage(StorageBackend):
    def __init__(self, bucket, prefix):
        self.bucket = bucket
        self.prefix = prefix
        # Initialize S3 client
    
    def exists(self, path):
        # Check if object exists in S3
        pass
    
    # Implement other methods...

# Use custom storage
storage = S3Storage("my-bucket", "hansard")
orchestrator = WorkflowOrchestrator(
    db_path="data/hansard.db",
    storage=storage
)
```

### Custom Workflow Steps

Run individual steps programmatically:

```python
orchestrator = WorkflowOrchestrator(db_path="data/hansard.db")

# Run only scraping steps
mps_result = orchestrator._scrape_mps()
hansards_result = orchestrator._scrape_hansards()

# Run only processing steps
processing_result = orchestrator._process_pdfs()
index_result = orchestrator._generate_search_index()
site_result = orchestrator._generate_site()
```

### Workflow Hooks

Add custom logic between steps:

```python
class CustomOrchestrator(WorkflowOrchestrator):
    def run_full_workflow(self):
        results = {}
        
        # Step 1: Scrape MPs
        results['mps'] = self._scrape_mps()
        
        # Custom hook: Validate MP data
        if results['mps']['mps_scraped'] < 300:
            raise ValueError("Too few MPs scraped")
        
        # Continue with remaining steps...
        results['hansards'] = self._scrape_hansards()
        
        return results
```

## Related Documentation

- [Development Guide](DEVELOPMENT.md) - Development workflow and testing
- [Architecture](ARCHITECTURE.md) - System architecture overview
- [Database Management](../scripts/db_manager.py) - Database utilities
- [Storage Abstraction](../hansard_tales/storage/) - Storage backends

## Support

For issues or questions:
- Check logs for error messages
- Review this documentation
- Open an issue on GitHub
- Contact maintainer

---

**Last Updated**: January 2025
