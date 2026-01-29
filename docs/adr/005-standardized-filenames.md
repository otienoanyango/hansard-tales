# ADR 005: Standardized Filename Generation

## Status

Accepted

## Context

Downloaded PDFs from parliament.go.ke have inconsistent filenames:
- "Hansard Report - Tuesday, 4th November 2025 (P).pdf"
- "Tuesday ,November 4, 2025 at 2.30pm.pdf"
- URL-encoded characters, spaces, special characters

We need standardized filenames for:
1. Consistent file organization
2. Easy sorting and filtering
3. Duplicate detection
4. Programmatic access

## Decision

We will generate **standardized filenames** based on document type and metadata.

### Filename Formats

**Hansard Documents:**
```
hansard_YYYYMMDD_<P|A|E>.pdf
```
- P = Morning (Plenary)
- A = Afternoon
- E = Evening

Example: `hansard_20251104_P.pdf`

**Votes & Proceedings:**
```
votes_YYYYMMDDTHHMMSSZ.pdf
```
- ISO 8601 datetime format
- UTC timezone (Z suffix)

Example: `votes_20251104T143000Z.pdf`

**Other Documents:**
```
<type>_YYYYMMDD_<sequence>.pdf
```

Example: `bill_20251104_001.pdf`

## Rationale

### Benefits of Standardization

1. **Sortable**: Lexicographic sort = chronological sort
2. **Parseable**: Easy to extract date/time programmatically
3. **Unique**: Date + period/time ensures uniqueness
4. **Consistent**: Same format across all documents
5. **No Special Characters**: Safe for all filesystems
6. **ISO 8601**: International standard for dates

### Filename Components

**Date Format (YYYYMMDD):**
- Year: 4 digits
- Month: 2 digits (01-12)
- Day: 2 digits (01-31)
- No separators (for sorting)

**Time Format (HHMMSS):**
- Hour: 2 digits (00-23, 24-hour format)
- Minute: 2 digits (00-59)
- Second: 2 digits (00-59)
- UTC timezone indicator (Z)

**Period Codes:**
- P: Morning/Plenary (typically 9:00-13:00)
- A: Afternoon (typically 14:30-18:30)
- E: Evening (rare, special sessions)

## Implementation

### Extraction from Original Filename

```python
def _generate_filename(self, url: str) -> str:
    """Generate standardized filename from URL."""
    original = urllib.parse.unquote(url.split('/')[-1])

    # Extract date: "4th November 2025"
    date_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s+(\d{4})', original)

    # Extract period: "(P)", "(A)", "(E)"
    period_match = re.search(r'\(([APE])\)', original)

    if date_match and period_match:
        day, month_name, year = date_match.groups()
        period = period_match.group(1)

        month = MONTH_MAP.get(month_name.lower(), '01')
        return f"hansard_{year}{month}{day.zfill(2)}_{period}.pdf"

    # Fallback to original filename
    return original
```

### Fallback Strategy

If metadata extraction fails:
1. Try alternative patterns
2. Use original filename
3. Log warning for manual review

```python
if not standardized_filename:
    logger.warning(f"Could not standardize filename: {original}")
    return original
```

## Consequences

### Positive

- **Organization**: Files sort chronologically
- **Discovery**: Easy to find documents by date
- **Automation**: Scripts can parse filenames reliably
- **Deduplication**: Consistent names help detect duplicates
- **Cross-Platform**: No filesystem compatibility issues

### Negative

- **Information Loss**: Original filename not preserved in filename
  - Mitigation: Store original filename in database metadata
- **Extraction Complexity**: Need robust parsing logic
  - Mitigation: Comprehensive tests and fallback to original

### Neutral

- **Migration**: Existing files need renaming
  - One-time operation with script

## Testing Strategy

### Property-Based Tests

```python
from hypothesis import given, strategies as st

@given(st.dates(), st.sampled_from(["P", "A", "E"]))
def test_hansard_filename_format(date, period):
    """Generated filenames should always match expected pattern."""
    filename = generate_hansard_filename(date, period)
    assert re.match(r'hansard_\d{8}_[PAE]\.pdf', filename)

@given(st.datetimes())
def test_votes_filename_format(dt):
    """Generated filenames should always be valid ISO 8601."""
    filename = generate_votes_filename(dt)
    assert re.match(r'votes_\d{8}T\d{6}Z\.pdf', filename)
```

### Unit Tests

```python
def test_hansard_filename_generation():
    filename = generate_hansard_filename(date(2025, 11, 4), "P")
    assert filename == "hansard_20251104_P.pdf"

def test_votes_filename_generation():
    dt = datetime(2025, 11, 4, 14, 30, 0)
    filename = generate_votes_filename(dt)
    assert filename == "votes_20251104T143000Z.pdf"

def test_filename_fallback():
    """Should fallback to original if extraction fails."""
    filename = generate_filename("unknown_format.pdf")
    assert filename == "unknown_format.pdf"
```

## Examples

### Hansard Filenames

| Original | Standardized |
|----------|-------------|
| Hansard Report - Tuesday, 4th November 2025 (P).pdf | hansard_20251104_P.pdf |
| Hansard Report - Wednesday, 5th November 2025 (A).pdf | hansard_20251105_A.pdf |
| Hansard Report - Thursday, 6th November 2025 (E).pdf | hansard_20251106_E.pdf |

### Votes Filenames

| Original | Standardized |
|----------|-------------|
| Tuesday ,November 4, 2025 at 2.30pm.pdf | votes_20251104T143000Z.pdf |
| Wednesday, November 5, 2025 at 9.00am.pdf | votes_20251105T090000Z.pdf |

## Database Storage

Store both filenames:

```python
class DownloadedFileORM(Base):
    standardized_filename = Column(String(255), nullable=False)
    original_filename = Column(String(500), nullable=False)
```

This preserves original information while using standardized names.

## References

- [ISO 8601 Date/Time Format](https://en.wikipedia.org/wiki/ISO_8601)
- [Filesystem Naming Conventions](https://en.wikipedia.org/wiki/Filename)

## Related ADRs

- [ADR 004: CSS Selectors for Scraping](004-css-selectors-for-scraping.md)
- [ADR 006: Download Tracking Table](006-download-tracking-table.md)

## Date

2025-01-15
