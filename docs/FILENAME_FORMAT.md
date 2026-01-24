# Filename Format and Migration Guide

## Overview

Hansard Tales uses a standardized filename format for all PDF files to ensure consistency, enable period-of-day tracking, and support efficient duplicate detection. This guide explains the filename format, how it's generated, and how to migrate existing files.

## Standardized Filename Format

### Format Specification

All Hansard PDF files follow this format:

```
hansard_YYYYMMDD_{A|P|E}.pdf
```

**Components**:
- `hansard_`: Fixed prefix
- `YYYYMMDD`: Date in compact format (e.g., 20240101 for January 1, 2024)
- `_`: Separator
- `{A|P|E}`: Period-of-day indicator
  - `A`: Afternoon sitting
  - `P`: Morning/Plenary sitting (default)
  - `E`: Evening sitting
- `.pdf`: File extension

### Examples

```
hansard_20240101_P.pdf    # Morning sitting on January 1, 2024
hansard_20240101_A.pdf    # Afternoon sitting on January 1, 2024
hansard_20240115_E.pdf    # Evening sitting on January 15, 2024
hansard_20241204_P.pdf    # Morning sitting on December 4, 2024
```

### Duplicate Handling

When multiple PDFs exist for the same date and period, a numeric suffix is appended:

```
hansard_20240101_A.pdf      # First afternoon sitting
hansard_20240101_A_2.pdf    # Second afternoon sitting
hansard_20240101_A_3.pdf    # Third afternoon sitting
```

**Suffix Rules**:
- Starts at 2 (no suffix for first file)
- Increments sequentially
- No gaps in sequence

## Period-of-Day Extraction

### Automatic Detection

The system automatically extracts the period-of-day from PDF metadata:

1. **Check PDF Title**: Search for keywords in the PDF title
2. **Check PDF Content**: If not found in title, search first page
3. **Default to P**: If no keywords found, use P (Morning)

### Keyword Mapping

| Period | Code | Keywords |
|--------|------|----------|
| Afternoon | A | "afternoon" |
| Morning/Plenary | P | "morning", "plenary" |
| Evening | E | "evening" |

**Matching Rules**:
- Case-insensitive matching
- First match wins (if multiple keywords found)
- Partial word matching (e.g., "Afternoon Session" matches "afternoon")

### Examples

```python
from hansard_tales.processors.period_extractor import PeriodOfDayExtractor

extractor = PeriodOfDayExtractor()

# Extract from title
period = extractor.extract_from_title("Afternoon Session - January 1, 2024")
# Returns: "A"

# Extract from PDF content
period = extractor.extract_from_content("hansard.pdf")
# Returns: "P", "A", or "E" based on content

# Extract with fallback
period = extractor.extract("hansard.pdf", title="Unknown Session")
# Returns: "P" (default if not found)
```

## Filename Generation

### Using FilenameGenerator

```python
from hansard_tales.utils.filename_generator import FilenameGenerator

generator = FilenameGenerator()

# Generate filename
filename = generator.generate(
    date="2024-01-01",
    period_of_day="A",
    existing_files=[]
)
# Returns: "hansard_20240101_A.pdf"

# Generate with existing files (handles duplicates)
existing = ["hansard_20240101_A.pdf"]
filename = generator.generate(
    date="2024-01-01",
    period_of_day="A",
    existing_files=existing
)
# Returns: "hansard_20240101_A_2.pdf"
```

### Parsing Filenames

```python
# Parse filename
result = generator.parse("hansard_20240101_A.pdf")
print(result)
# Output: {'date': '2024-01-01', 'period_of_day': 'A', 'suffix': None}

# Parse filename with suffix
result = generator.parse("hansard_20240101_A_2.pdf")
print(result)
# Output: {'date': '2024-01-01', 'period_of_day': 'A', 'suffix': '2'}

# Parse invalid filename
result = generator.parse("invalid_filename.pdf")
print(result)
# Output: {'date': None, 'period_of_day': None, 'suffix': None}
```

## Integration with Scraper

### Automatic Filename Generation

The scraper automatically generates standardized filenames:

```python
from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.storage.filesystem import FilesystemStorage

storage = FilesystemStorage("data/pdfs/hansard")
scraper = HansardScraper(storage=storage, db_path="data/hansard.db")

# Scraper automatically:
# 1. Extracts period-of-day from PDF title
# 2. Generates standardized filename
# 3. Checks for existing files
# 4. Handles duplicates with numeric suffix
# 5. Downloads and tracks in database

hansards = scraper.scrape_all(max_pages=5)
scraper.download_all(hansards)
```

### Download Process

1. **Extract Period-of-Day**:
   ```python
   period = extractor.extract_from_title(pdf_title)
   # Returns: "A", "P", or "E"
   ```

2. **Generate Filename**:
   ```python
   existing_files = storage.list_files(f"hansard_{date_compact}")
   filename = generator.generate(date, period, existing_files)
   # Returns: "hansard_20240101_A.pdf" or with suffix
   ```

3. **Check for Duplicates**:
   ```python
   should_skip, reason = scraper._check_existing_download(url, filename)
   # Returns: (True, "file_exists_with_record") or (False, "new_download")
   ```

4. **Download and Track**:
   ```python
   storage.write(filename, pdf_content)
   scraper._track_download(url, filename, date, period, session_id=None)
   ```

## Migration from Old Format

### Old Format

Previous filename format (if applicable):

```
YYYYMMDD_n.pdf
20240101_0.pdf
20240101_1.pdf
20240115_0.pdf
```

Where:
- `YYYYMMDD`: Date in compact format
- `n`: Sequential number (0, 1, 2, ...)

### Migration Process

**Note**: The migration utility (Task 9) is marked as optional and was not implemented in this phase. If you have existing PDFs in the old format, you can either:

1. **Download fresh**: Re-download all PDFs using the new scraper (recommended)
2. **Manual migration**: Rename files manually following the new format
3. **Implement migration utility**: Complete Task 9 if needed

### Manual Migration Example

If you need to migrate files manually:

```bash
# Example: Rename old format to new format
# Old: 20240101_0.pdf
# New: hansard_20240101_P.pdf (assuming morning sitting)

cd data/pdfs/hansard/

# Rename files (adjust period-of-day as needed)
for file in *.pdf; do
    if [[ $file =~ ^([0-9]{8})_[0-9]+\.pdf$ ]]; then
        date="${BASH_REMATCH[1]}"
        new_name="hansard_${date}_P.pdf"
        echo "Renaming: $file -> $new_name"
        mv "$file" "$new_name"
    fi
done
```

### Database Updates

After renaming files, update the database:

```sql
-- Update file paths in downloaded_pdfs table
UPDATE downloaded_pdfs
SET file_path = 'hansard_' || substr(file_path, 1, 8) || '_P.pdf'
WHERE file_path LIKE '________\_%.pdf' ESCAPE '\';

-- Verify updates
SELECT file_path FROM downloaded_pdfs LIMIT 10;
```

## Validation

### Validate Filename Format

```python
import re

def validate_filename(filename):
    """Validate filename matches standardized format."""
    pattern = r'^hansard_(\d{8})_([APE])(?:_(\d+))?\.pdf$'
    match = re.match(pattern, filename)
    
    if not match:
        return False, "Invalid format"
    
    date_str = match.group(1)
    period = match.group(2)
    suffix = match.group(3)
    
    # Validate date components
    year = int(date_str[:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    
    if not (2020 <= year <= 2030):
        return False, f"Invalid year: {year}"
    
    if not (1 <= month <= 12):
        return False, f"Invalid month: {month}"
    
    if not (1 <= day <= 31):
        return False, f"Invalid day: {day}"
    
    return True, "Valid"

# Test validation
print(validate_filename("hansard_20240101_P.pdf"))
# Output: (True, "Valid")

print(validate_filename("hansard_20240101_X.pdf"))
# Output: (False, "Invalid format")
```

### Validate All Files

```bash
# Check all files in storage directory
cd data/pdfs/hansard/

# List files that don't match format
for file in *.pdf; do
    if ! [[ $file =~ ^hansard_[0-9]{8}_[APE](_[0-9]+)?\.pdf$ ]]; then
        echo "Invalid: $file"
    fi
done
```

### Database Consistency Check

```sql
-- Check for files in database but not in storage
SELECT file_path
FROM downloaded_pdfs
WHERE file_path NOT IN (
    -- List of actual files (would need to be populated)
    SELECT file_path FROM actual_files
);

-- Check for duplicate URLs
SELECT original_url, COUNT(*) as count
FROM downloaded_pdfs
GROUP BY original_url
HAVING count > 1;

-- Check for missing period_of_day
SELECT file_path, period_of_day
FROM downloaded_pdfs
WHERE period_of_day IS NULL;
```

## Best Practices

### 1. Always Use FilenameGenerator

**Good**:
```python
from hansard_tales.utils.filename_generator import FilenameGenerator

generator = FilenameGenerator()
filename = generator.generate(date, period, existing_files)
```

**Bad**:
```python
# Manual filename construction (don't do this!)
filename = f"hansard_{date.replace('-', '')}_{period}.pdf"
```

### 2. Check for Existing Files

```python
# Get existing files before generating
existing_files = storage.list_files(f"hansard_{date_compact}")
filename = generator.generate(date, period, existing_files)
```

### 3. Validate Period-of-Day

```python
# Validate before generating
if period not in ('A', 'P', 'E'):
    raise ValueError(f"Invalid period: {period}")

filename = generator.generate(date, period, existing_files)
```

### 4. Handle Errors Gracefully

```python
try:
    filename = generator.generate(date, period, existing_files)
except ValueError as e:
    logger.error(f"Filename generation failed: {e}")
    # Use default or skip
```

### 5. Log Filename Changes

```python
import logging

logger = logging.getLogger(__name__)

# Log generated filename
logger.info(f"Generated filename: {filename} for date={date}, period={period}")

# Log duplicate handling
if "_2" in filename:
    logger.warning(f"Duplicate detected: {filename}")
```

## Troubleshooting

### Issue: Wrong Period-of-Day

**Symptoms**: Files have incorrect period code (A/P/E)

**Causes**:
- PDF title doesn't contain keywords
- First page doesn't contain keywords
- Keywords are ambiguous

**Solutions**:
1. Check PDF title and content manually
2. Update keyword mapping if needed
3. Manually correct filename and database

### Issue: Duplicate Suffixes

**Symptoms**: Multiple files with same date/period but different suffixes

**Causes**:
- Multiple parliamentary sittings on same day
- Re-downloads of same session
- Manual file additions

**Solutions**:
1. Verify each file is unique (different content)
2. Consolidate duplicates if same content
3. Update database records

### Issue: Invalid Filenames

**Symptoms**: Files don't match standardized format

**Causes**:
- Manual file additions
- Migration incomplete
- Old scraper version

**Solutions**:
1. Run validation script
2. Rename invalid files
3. Update database records

### Issue: Missing Files

**Symptoms**: Database records exist but files missing

**Causes**:
- Files deleted manually
- Storage migration incomplete
- Disk failure

**Solutions**:
1. Re-download missing files:
   ```python
   scraper = HansardScraper(storage, db_path)
   # Scraper will detect missing files and re-download
   hansards = scraper.scrape_all(max_pages=10)
   scraper.download_all(hansards)
   ```

2. Or remove orphaned database records:
   ```sql
   DELETE FROM downloaded_pdfs
   WHERE file_path NOT IN (
       -- List of actual files
       SELECT file_path FROM actual_files
   );
   ```

## Testing

### Unit Tests

```python
import pytest
from hansard_tales.utils.filename_generator import FilenameGenerator

def test_generate_basic():
    """Test basic filename generation."""
    generator = FilenameGenerator()
    filename = generator.generate("2024-01-01", "A", [])
    assert filename == "hansard_20240101_A.pdf"

def test_generate_with_duplicate():
    """Test duplicate handling."""
    generator = FilenameGenerator()
    existing = ["hansard_20240101_A.pdf"]
    filename = generator.generate("2024-01-01", "A", existing)
    assert filename == "hansard_20240101_A_2.pdf"

def test_parse_basic():
    """Test filename parsing."""
    generator = FilenameGenerator()
    result = generator.parse("hansard_20240101_A.pdf")
    assert result['date'] == "2024-01-01"
    assert result['period_of_day'] == "A"
    assert result['suffix'] is None

def test_parse_with_suffix():
    """Test parsing filename with suffix."""
    generator = FilenameGenerator()
    result = generator.parse("hansard_20240101_A_2.pdf")
    assert result['date'] == "2024-01-01"
    assert result['period_of_day'] == "A"
    assert result['suffix'] == "2"
```

### Integration Tests

```python
def test_scraper_filename_generation(temp_storage, temp_db):
    """Test scraper generates correct filenames."""
    scraper = HansardScraper(
        storage=temp_storage,
        db_path=temp_db
    )
    
    # Mock download
    hansards = [
        {
            'url': 'http://example.com/hansard.pdf',
            'title': 'Afternoon Session - January 1, 2024',
            'date': '2024-01-01'
        }
    ]
    
    scraper.download_all(hansards)
    
    # Verify filename
    files = temp_storage.list_files("")
    assert len(files) == 1
    assert files[0] == "hansard_20240101_A.pdf"
```

## Related Documentation

- [Storage Abstraction](STORAGE_ABSTRACTION.md) - Storage backend details
- [Workflow Orchestration](WORKFLOW_ORCHESTRATION.md) - Using filenames in workflows
- [Development Guide](DEVELOPMENT.md) - Development workflow

## Support

For issues or questions:
- Check filename format with validation script
- Review this documentation
- Open an issue on GitHub
- Contact maintainer

---

**Last Updated**: January 2025
