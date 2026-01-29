# Hansard Period Codes

## Overview

Hansard documents on parliament.go.ke use period codes to indicate the session time (Morning, Afternoon, or Evening).

## Period Code Mapping

| Code | Session | Link Text Display |
|------|---------|-------------------|
| A    | Morning | "Morning Sitting" |
| P    | Afternoon | "Afternoon Sitting" |
| E    | Evening | "Evening Sitting" |

## Where to Extract From

**Extract from the URL (href attribute), NOT the link text!**

### Example HTML Structure

```html
<a href="https://parliament.go.ke/files/Hansard%20Report%20-%20Thursday%2C%204th%20December%202025%20%28P%29.pdf"
   title="Hansard Report - Thursday, 4th December 2025 (P).pdf">
   Hansard Report - Thursday, 4th December 2025 - Afternoon Sitting
</a>
```

**What to use:**
- ✅ **href**: `...%28P%29.pdf` → Extract `(P)` → Period code: P
- ✅ **title**: `...(P).pdf` → Extract `(P)` → Period code: P
- ❌ **link text**: "Afternoon Sitting" → Don't parse this, use href instead

## Standardized Filename Format

Format: `hansard_YYYYMMDD_<A|P|E>.pdf`

Examples:
- `hansard_20251204_P.pdf` - Afternoon session on Dec 4, 2025
- `hansard_20251203_A.pdf` - Morning session on Dec 3, 2025
- `hansard_20251204_E.pdf` - Evening session on Dec 4, 2025

## Implementation Notes

### Date Extraction
- Use `dateparser` library with UTC+3 timezone (Africa/Nairobi)
- Handles British format dates: "4th December 2025", "Thursday, 4th December 2025"
- Robust to variations: missing spaces, lowercase months, etc.

### Period Extraction
- Extract from URL using regex: `\(([APE])\)`
- Case-insensitive matching (handles both `(P)` and `(p)`)
- Always uppercase the result for consistency

## Edge Cases Handled

1. **No space after comma**: "Thursday,16th January 2025 (P).pdf" ✅
2. **Lowercase period**: "Tuesday, 5th November 2024 (p).pdf" ✅
3. **Missing period code**: Defaults to P (Afternoon) ✅
4. **Various date formats**: dateparser handles automatically ✅

## Testing

See `tests/unit/test_scrapers.py::TestDateParserIntegration` for comprehensive tests covering:
- 15 real-world Hansard URL examples
- 13 real-world Votes URL examples
- Edge cases and format variations
- Consistency verification

Run tests:
```bash
pytest tests/unit/test_scrapers.py::TestDateParserIntegration -v
```
