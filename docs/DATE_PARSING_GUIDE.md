# Date Parsing Guide

## Overview

The Hansard scraper uses `dateparser` with British locale settings to handle various date formats commonly found in Kenyan parliamentary documents.

## Locale Configuration

The scraper is configured for **British/Kenyan date format (DMY)**:

```python
settings={
    'PREFER_DATES_FROM': 'past',
    'STRICT_PARSING': False,
    'DATE_ORDER': 'DMY',  # Day-Month-Year (British/Kenyan)
    'PREFER_DAY_OF_MONTH': 'first',  # Interpret ambiguous dates as DMY
    'PREFER_LOCALE_DATE_ORDER': True,  # Use locale date order
    'RETURN_AS_TIMEZONE_AWARE': False,
},
languages=['en-GB', 'en']  # British English first, then general English
```

## Supported Date Formats

### 1. British Long Format (Primary)

**With day of week and ordinals:**
- `Thursday, 4th December 2025` → `2025-12-04`
- `Monday, 1st January 2025` → `2025-01-01`
- `Friday, 22nd November 2024` → `2024-11-22`
- `Wednesday, 3rd March 2025` → `2025-03-03`

**Without day of week:**
- `4th December 2025` → `2025-12-04`
- `1st January 2025` → `2025-01-01`
- `22nd November 2024` → `2024-11-22`

**Without ordinals:**
- `4 December 2025` → `2025-12-04`
- `1 January 2025` → `2025-01-01`
- `22 November 2024` → `2024-11-22`

### 2. ISO Format

**Standard ISO 8601:**
- `2025-12-04` → `2025-12-04`
- `2024-01-15` → `2024-01-15`

### 3. Slash/Dash Separated (DMY)

**DD/MM/YYYY:**
- `04/12/2025` → `2025-12-04` (4th December, not April 12th)
- `15/01/2024` → `2024-01-15` (15th January)

**DD-MM-YYYY:**
- `04-12-2025` → `2025-12-04`
- `15-01-2024` → `2024-01-15`

### 4. American Format (Supported but not preferred)

**Month DD, YYYY:**
- `December 4, 2025` → `2025-12-04`
- `January 1, 2025` → `2025-01-01`

### 5. Embedded in Text

**Dates within sentences:**
- `Hansard for Thursday, 4th December 2025 - Afternoon` → `2025-12-04`
- `Session on 15/01/2024` → `2024-01-15`
- `Meeting scheduled for 4th December 2025` → `2025-12-04`

## Parsing Strategy

The scraper uses a multi-layered approach:

1. **dateparser (Primary)**: Handles complex British formats with locale awareness
2. **Regex fallback**: For edge cases where dateparser might fail

### Priority Order

1. Try dateparser with British locale (`en-GB`)
2. If dateparser fails, try regex patterns:
   - ISO format (YYYY-MM-DD)
   - British DMY format (DD/MM/YYYY or DD-MM-YYYY)
   - British with month names (DD Month YYYY)
   - American format (Month DD, YYYY)

## Examples

### Correct Interpretation (British Locale)

```python
# Ambiguous dates are interpreted as DMY (British)
"04/12/2025" → "2025-12-04"  # 4th December, NOT April 12th
"12/04/2025" → "2025-04-12"  # 12th April, NOT December 4th
"01/02/2025" → "2025-02-01"  # 1st February, NOT January 2nd
```

### Invalid Dates

```python
"No date here" → None
"" → None
"Invalid text" → None
```

## Testing

All date formats are tested in `tests/scraper/test_scraper_improvements.py`:

```bash
# Run date parsing tests
pytest tests/scraper/test_scraper_improvements.py::TestDateParsing -v

# Expected: 26 tests passing
```

## Common Pitfalls

### ❌ American Locale Interpretation

If using American locale (MDY), dates would be misinterpreted:

```python
# WRONG (American locale)
"04/12/2025" → "2025-04-12"  # April 12th (WRONG!)

# CORRECT (British locale)
"04/12/2025" → "2025-12-04"  # 4th December (CORRECT!)
```

### ✅ British Locale Interpretation

With British locale configured correctly:

```python
# All interpreted as DMY
"04/12/2025" → "2025-12-04"  # 4th December ✓
"15/01/2024" → "2024-01-15"  # 15th January ✓
"22/11/2024" → "2024-11-22"  # 22nd November ✓
```

## Configuration

The locale is configured in `HansardScraper.extract_date()`:

```python
results = search_dates(
    text,
    settings={
        'DATE_ORDER': 'DMY',  # British/Kenyan format
        'PREFER_DAY_OF_MONTH': 'first',
        'PREFER_LOCALE_DATE_ORDER': True,
    },
    languages=['en-GB', 'en']  # British English first
)
```

## Debugging

To debug date parsing issues:

```python
from hansard_tales.scrapers.hansard_scraper import HansardScraper
from unittest.mock import Mock, patch

with patch.object(HansardScraper, '_ensure_database_initialized'):
    scraper = HansardScraper(storage=Mock(), db_path=None)

# Test a specific date
result = scraper.extract_date("Thursday, 4th December 2025")
print(f"Parsed: {result}")  # Should be: 2025-12-04
```

## References

- [dateparser documentation](https://dateparser.readthedocs.io/)
- [British date format (DMY)](https://en.wikipedia.org/wiki/Date_format_by_country)
- [ISO 8601 standard](https://en.wikipedia.org/wiki/ISO_8601)
