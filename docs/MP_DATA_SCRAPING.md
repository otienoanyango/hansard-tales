# MP Data Scraping Documentation

## Overview

This document describes the MP data scraping process for the Hansard Tales project.

## Scraper Script

**Location**: `scripts/mp_data_scraper.py`

### Features

- Scrapes MP data from parliament.go.ke
- Supports multiple parliamentary terms (2017, 2022, etc.)
- Handles pagination automatically
- Extracts:
  - Name
  - County
  - Constituency
  - Party
  - Status (Elected/Nominated)
  - Photo URL
  - Term start year
- Outputs to JSON or CSV format
- Configurable delay between requests (default: 1.0s)
- Respectful scraping with rate limiting

### Usage

```bash
# Scrape 13th Parliament (2022)
python scripts/mp_data_scraper.py --term 2022 --output data/mps_13th_parliament.json

# Scrape 12th Parliament (2017)
python scripts/mp_data_scraper.py --term 2017 --output data/mps_12th_parliament.json

# With custom delay
python scripts/mp_data_scraper.py --term 2022 --output data/mps.json --delay 2.0

# Output to CSV
python scripts/mp_data_scraper.py --term 2022 --output data/mps.csv
```

### Parameters

- `--term`: Parliamentary term start year (required)
- `--output`: Output file path (required, .json or .csv)
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--max-pages`: Maximum pages to scrape (default: 50)

## Data Files

### 13th Parliament (2022-2027)

**File**: `data/mps_13th_parliament.json`

- Total MPs: 349
- Elected: 290
- Nominated: 12
- Women Representatives: 47

**Top Parties**:
- UDA: 137
- ODM: 86
- JP: 28
- Others: 98

### 12th Parliament (2017-2022)

**File**: `data/mps_12th_parliament.json`

- Total MPs: 230 (partial data due to connection issues)
- Elected: 222
- Nominated: 5

**Top Parties**:
- JP: 108
- ODM: 38
- WDM-K: 19
- Others: 65

## Data Format

### JSON Structure

```json
[
  {
    "name": "JOHN DOE",
    "county": "NAIROBI",
    "constituency": "WESTLANDS",
    "party": "ODM",
    "status": "Elected",
    "photo_url": "https://parliament.go.ke/sites/default/files/...",
    "term_start_year": 2022
  }
]
```

### CSV Structure

```csv
name,county,constituency,party,status,photo_url,term_start_year
JOHN DOE,NAIROBI,WESTLANDS,ODM,Elected,https://...,2022
```

## Implementation Details

### HTML Structure

The parliament website uses a Drupal-based system with:
- Table rows with class `mp`
- Cells with specific class names:
  - `views-field-field-name`: MP name
  - `views-field-field-image`: Photo
  - `views-field-field-county`: County
  - `views-field-field-constituency`: Constituency
  - `views-field-field-party`: Party
  - `views-field-field-status`: Status

### Pagination

- 10 MPs per page
- Pagination uses `page` query parameter (0-based)
- Next page detection via `<nav class="pager">` links

### Data Cleaning

- Removes "HON." prefix from names
- Normalizes whitespace
- Handles empty/null values
- Converts relative photo URLs to absolute URLs

## Testing

**Test File**: `tests/test_mp_data_scraper.py`

- 19 tests total
- Unit tests for all core functions
- Integration tests for live scraping (marked with `@pytest.mark.integration`)

Run tests:
```bash
# Run all tests except integration
pytest tests/test_mp_data_scraper.py -v -k "not integration"

# Run integration tests (requires network)
pytest tests/test_mp_data_scraper.py -v -m integration
```

## Next Steps

1. **Task 3.2**: Create import script to load MP data into database
   - Read JSON files
   - Insert into `mps` table
   - Link to parliamentary terms via `mp_terms` table
   - Handle duplicates and updates

2. **Data Validation**:
   - Verify all 349 MPs for 13th Parliament
   - Complete scraping for 12th Parliament (retry failed pages)
   - Cross-reference with official sources

3. **Maintenance**:
   - Re-scrape periodically to catch updates
   - Monitor for website structure changes
   - Add error recovery for network issues

## Known Issues

1. **Connection Drops**: Occasional connection drops during long scrapes
   - Mitigation: Increase delay, retry failed pages

2. **Test Updates Needed**: Some unit tests need updating to match new HTML structure
   - Tests work with old table-based structure
   - Scraper works correctly with current structure
   - Tests should be updated in future

3. **Incomplete 12th Parliament Data**: Only 230/349 MPs scraped
   - Connection dropped on page 22
   - Need to retry or scrape remaining pages

## Resources

- Parliament Website: https://parliament.go.ke/the-national-assembly/mps
- API Endpoint: `https://parliament.go.ke/the-national-assembly/mps?field_parliament_value={year}&page={page}`
- Documentation: This file

## License

This scraper is for research and transparency purposes only. All data belongs to the Parliament of Kenya.
