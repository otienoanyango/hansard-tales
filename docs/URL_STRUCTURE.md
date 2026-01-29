# Parliament.go.ke URL Structure

This document clarifies the URL structure for different document types on parliament.go.ke.

## Votes & Proceedings

### Page URL (Listing)
The page that lists Votes & Proceedings documents uses **singular** form:
```
https://parliament.go.ke/the-national-assembly/house-business/votes-proceeding?title=%20&field_parliament_value=2022&page=0
```

Key points:
- Uses `votes-proceeding` (singular, no "and")
- Includes `title=%20` parameter (empty title filter)
- Includes `field_parliament_value` for parliament term
- Includes `page` parameter for pagination

### PDF URLs (Direct Links)
The actual PDF files are stored in a different location:
```
https://parliament.go.ke/sites/default/files/2025-12/Thursday%2CDecember%204%2C2025%20at%204.15pm.pdf
```

Key points:
- Located in `/sites/default/files/YYYY-MM/` directory
- Filename format: `DayName%2CMonth%20Day%2CYYYY%20at%20Time.pdf`
- URL-encoded spaces and commas
- No "votes" keyword in the filename itself

## Hansard

### Page URL (Listing)
```
https://parliament.go.ke/the-national-assembly/house-business/hansard?field_parliament_value=2022&page=0
```

### PDF URLs (Direct Links)
```
https://parliament.go.ke/sites/default/files/2024-11/4th%20November%202024%20(P).pdf
```

Key points:
- Located in `/sites/default/files/YYYY-MM/` directory
- Filename format: `Day%20Month%20YYYY%20(P|A|E).pdf`
- Period indicator: P=Morning, A=Afternoon, E=Evening

## Important Distinctions

1. **Page URLs vs PDF URLs**: The listing page URL is different from the actual PDF file URLs
2. **Singular vs Plural**: Votes page uses "votes-proceeding" (singular), not "votes-and-proceedings"
3. **URL Encoding**: PDF filenames are URL-encoded (%20 for space, %2C for comma)
4. **Directory Structure**: PDFs are stored in date-based directories under `/sites/default/files/`

## Scraper Implementation

The scrapers handle this by:
1. Fetching the listing page (e.g., `/votes-proceeding`)
2. Parsing HTML tables to extract PDF links
3. Converting relative URLs to absolute URLs
4. Filtering for relevant documents (by keyword matching)
5. Downloading PDFs from their actual storage location

## Testing Considerations

When writing tests:
- Mock the listing page URL with correct format (`votes-proceeding`)
- Include "votes" or "proceedings" keyword in test HTML for proper filtering
- Use realistic PDF URLs in test data
- Verify URL construction in assertions
