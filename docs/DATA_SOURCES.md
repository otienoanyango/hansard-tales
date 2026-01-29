# Data Sources Documentation

## Overview

This document provides comprehensive information about all data sources used by the Hansard Tales system. It includes URLs, data formats, update frequencies, and scraping strategies.

## Table of Contents

1. [Parliament of Kenya Website](#parliament-of-kenya-website)
2. [Data Types](#data-types)
3. [URL Patterns](#url-patterns)
4. [HTML Structure](#html-structure)
5. [Update Frequencies](#update-frequencies)
6. [Scraping Strategies](#scraping-strategies)
7. [Data Quality](#data-quality)
8. [Troubleshooting](#troubleshooting)

---

## Parliament of Kenya Website

### Base URL

```
https://parliament.go.ke
```

### Chambers

The Parliament of Kenya consists of two chambers:

1. **National Assembly**: Lower house, 349 members
2. **Senate**: Upper house, 67 members

---

## Data Types

### 1. Hansard Reports

**Description**: Verbatim transcripts of parliamentary proceedings

**Chambers**: National Assembly, Senate

**Format**: PDF documents

**Content**:
- Date and time of sitting
- Speaker and Deputy Speaker remarks
- MP statements and debates
- Questions and answers
- Procedural motions
- Division results

**Typical Size**: 50-200 pages per session

**Language**: English (official), some Swahili

### 2. Votes & Proceedings

**Description**: Official record of votes and parliamentary business

**Chambers**: National Assembly, Senate

**Format**: PDF documents

**Content**:
- Date and time of sitting
- Attendance records
- Bills presented
- Motions moved
- Division results (vote counts)
- Committee reports tabled

**Typical Size**: 5-20 pages per session

### 3. Bills

**Description**: Proposed legislation

**Chambers**: National Assembly, Senate

**Format**: PDF documents

**Content**:
- Bill number and title
- Sponsor information
- Bill text (clauses and schedules)
- Explanatory memorandum
- Financial implications

**Typical Size**: 10-100 pages

**Status**: Tracked through legislative stages

### 4. Questions

**Description**: Parliamentary questions to government

**Chambers**: National Assembly, Senate

**Format**: PDF documents

**Types**:
- Oral questions (answered in chamber)
- Written questions (written responses)

**Content**:
- Question number
- Asker (MP/Senator)
- Respondent (Minister/official)
- Question text
- Answer text

### 5. Petitions

**Description**: Public petitions to parliament

**Chambers**: National Assembly, Senate

**Format**: PDF documents

**Content**:
- Petition number
- Petitioner information
- Sponsor (MP/Senator)
- Petition text
- Prayer (request)
- Committee response

### 6. Trackers

**Description**: Status tracking documents

**Types**:
- Statement Tracker
- Motion Tracker
- Bill Tracker

**Format**: PDF documents (tables)

**Content**:
- Item number
- Title/description
- Status
- Date submitted
- Responsible committee

---

## URL Patterns

### National Assembly

#### Hansard

```
https://parliament.go.ke/the-national-assembly/house-business/hansard
```

**Parameters**:
- `field_parliament_value`: Parliament term (e.g., 2022 for 13th Parliament)
- `page`: Page number (0-indexed)

**Example**:
```
https://parliament.go.ke/the-national-assembly/house-business/hansard?field_parliament_value=2022&page=0
```

#### Votes & Proceedings

```
https://parliament.go.ke/the-national-assembly/house-business/votes-proceedings
```

**Parameters**: Same as Hansard

**Example**:
```
https://parliament.go.ke/the-national-assembly/house-business/votes-proceedings?field_parliament_value=2022&page=0
```

#### Bills

```
https://parliament.go.ke/the-national-assembly/house-business/bills
```

#### Questions

```
https://parliament.go.ke/the-national-assembly/house-business/questions
```

#### Petitions

```
https://parliament.go.ke/the-national-assembly/house-business/petitions
```

### Senate

Replace `/the-national-assembly/` with `/the-senate/` in all URLs.

**Example**:
```
https://parliament.go.ke/the-senate/house-business/hansard?field_parliament_value=2022&page=0
```

---

## HTML Structure

### Document Listing Pages

**Structure**:
```html
<table class="cols-2">
  <tbody>
    <tr>
      <td class="views-field-field-pdf">
        <a href="/sites/default/files/2025-11/hansard.pdf">
          Hansard Report - Tuesday, 4th November 2025 (P)
        </a>
      </td>
      <td class="views-field-field-date">
        04/11/2025
      </td>
    </tr>
  </tbody>
</table>
```

**CSS Selector for PDF Links**:
```css
table.cols-2 td.views-field-field-pdf a[href$=".pdf"]
```

### Pagination

**Structure**:
```html
<nav class="pager">
  <ul>
    <li class="pager__item"><a href="?page=0">1</a></li>
    <li class="pager__item"><a href="?page=1">2</a></li>
    <li class="pager__item"><a href="?page=2">3</a></li>
  </ul>
</nav>
```

**Detection**:
```python
pager = soup.select_one('nav.pager, ul.pager, div.pager')
page_links = pager.select('a') if pager else []
```

---

## Update Frequencies

### Hansard Reports

**Frequency**: Daily (when parliament is in session)

**Publication Delay**: 1-3 days after sitting

**Sessions**:
- Morning: 9:00 AM - 1:00 PM
- Afternoon: 2:30 PM - 6:30 PM
- Evening: Rare, special sessions

**Parliamentary Calendar**:
- Sittings: Tuesday - Thursday (typically)
- Recess: Several weeks per year
- Check official calendar for exact dates

### Votes & Proceedings

**Frequency**: Daily (when parliament is in session)

**Publication Delay**: 1-2 days after sitting

### Bills

**Frequency**: As introduced (irregular)

**Updates**: When amended or progressed through stages

### Questions

**Frequency**: Weekly (question time sessions)

**Publication**: After answers provided

### Petitions

**Frequency**: As submitted (irregular)

**Updates**: When committee responds

---

## Scraping Strategies

### Rate Limiting

**Recommended Delay**: 1-2 seconds between requests

**Implementation**:
```python
time.sleep(config.retry_delay)  # Default: 1.0 seconds
```

**Rationale**: Avoid overloading parliament.go.ke servers

### Pagination

**Strategy**: Automatic detection and iteration

**Implementation**:
1. Fetch first page
2. Detect total pages from pagination element
3. Iterate through all pages with rate limiting

**Example**:
```python
for page_num in range(total_pages):
    time.sleep(retry_delay)
    url = f"{base_url}?field_parliament_value={term}&page={page_num}"
    # Fetch and process page
```

### Duplicate Prevention

**Strategy**: Hash-based deduplication

**Implementation**:
1. Compute SHA256 hash of PDF content
2. Check `downloaded_files` table for existing hash
3. Skip if already downloaded

**Benefits**:
- Avoid re-downloading same document
- Detect duplicate documents with different URLs
- Save bandwidth and storage

### Error Handling

**Strategy**: Continue on error, log failures

**Implementation**:
```python
for url in urls:
    try:
        doc = download_document(url)
        process_document(doc)
    except Exception as e:
        logger.error(f"Error processing {url}: {e}")
        continue  # Continue with remaining documents
```

**Rationale**: One failed document shouldn't stop entire scrape

### Retry Logic

**Strategy**: Exponential backoff

**Implementation**:
```python
for attempt in range(max_retries):
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        if attempt == max_retries - 1:
            raise
        time.sleep(retry_delay * (2 ** attempt))
```

**Parameters**:
- `max_retries`: 3
- `retry_delay`: 1.0 seconds
- `timeout`: 30 seconds

---

## Data Quality

### Known Issues

#### 1. Inconsistent Filenames

**Issue**: Filenames vary in format and encoding

**Examples**:
- "Hansard Report - Tuesday, 4th November 2025 (P).pdf"
- "Hansard%20Report%20-%20Tuesday%2C%204th%20November%202025%20%28P%29.pdf"

**Solution**: Standardized filename generation (see ADR 005)

#### 2. Missing Metadata

**Issue**: Some PDFs lack embedded metadata

**Impact**: Date/time extraction relies on filename parsing

**Mitigation**: Robust parsing with fallbacks

#### 3. OCR Quality

**Issue**: Older documents may have poor OCR quality

**Impact**: Text extraction may be inaccurate

**Mitigation**: Manual review for critical documents

#### 4. Incomplete Documents

**Issue**: Some PDFs may be truncated or corrupted

**Detection**: File size validation, PDF parsing errors

**Handling**: Log error, flag for manual review

### Validation Checks

**File Size**:
- Minimum: 10 KB (likely incomplete if smaller)
- Maximum: 50 MB (unusually large)

**PDF Validity**:
- Can be opened by PDF library
- Has at least one page
- Text extraction succeeds

**Metadata Completeness**:
- Date can be extracted
- Document type identified
- Chamber identified

---

## Troubleshooting

### No Documents Found

**Symptom**: Scraper returns empty list

**Possible Causes**:
1. HTML structure changed
2. Wrong parliament term parameter
3. Network issues
4. Website maintenance

**Diagnosis**:
```python
# Check if selector still works
soup = BeautifulSoup(html, 'html.parser')
links = soup.select('table.cols-2 td.views-field-field-pdf a[href$=".pdf"]')
print(f"Found {len(links)} links")
```

**Solutions**:
1. Inspect HTML in browser
2. Update CSS selector
3. Check parliament term parameter
4. Verify website is accessible

### Download Failures

**Symptom**: HTTP errors (404, 500, timeout)

**Possible Causes**:
1. Document removed from website
2. Server issues
3. Network issues
4. Rate limiting

**Solutions**:
1. Retry with exponential backoff
2. Check URL validity
3. Reduce request rate
4. Contact parliament IT support

### Parsing Errors

**Symptom**: Cannot extract date/metadata

**Possible Causes**:
1. Filename format changed
2. Unexpected characters
3. Missing information

**Solutions**:
1. Update regex patterns
2. Add fallback patterns
3. Log for manual review

### Duplicate Detection Issues

**Symptom**: Same document downloaded multiple times

**Possible Causes**:
1. Hash computation error
2. Database query error
3. Different file content (updated version)

**Solutions**:
1. Verify hash computation
2. Check database connection
3. Compare file contents manually

---

## Parliament Terms

### 13th Parliament (2022-2027)

**Start Date**: September 13, 2022

**End Date**: August 2027 (expected)

**URL Parameter**: `field_parliament_value=2022`

**National Assembly**:
- Total Members: 349
- Elected: 290
- Women Representatives: 47
- Nominated: 12

**Senate**:
- Total Members: 67
- Elected: 47
- Nominated: 20

### 12th Parliament (2017-2022)

**Start Date**: August 31, 2017

**End Date**: August 8, 2022

**URL Parameter**: `field_parliament_value=2017`

### Historical Data

Earlier parliaments may have limited online availability.

---

## Contact Information

### Parliament of Kenya

**Website**: https://parliament.go.ke

**Email**: info@parliament.go.ke

**Phone**: +254 20 221291

**Address**:
Parliament Buildings
Parliament Road
P.O. Box 41842-00100
Nairobi, Kenya

### Technical Support

For website issues or data access:
- Email: webmaster@parliament.go.ke
- Report issues through website contact form

---

## Data Usage Guidelines

### Terms of Use

Parliamentary data is public information, but:

1. **Attribution**: Credit Parliament of Kenya as source
2. **Accuracy**: Verify critical information against official records
3. **Respect**: Don't overload servers with excessive requests
4. **Purpose**: Use for legitimate research/analysis purposes

### Best Practices

1. **Rate Limiting**: 1-2 seconds between requests
2. **User Agent**: Identify your application
3. **Caching**: Store downloaded documents locally
4. **Updates**: Check for new documents periodically, not continuously
5. **Errors**: Handle gracefully, don't retry excessively

---

## Changelog

### 2025-01-15

- Initial documentation
- Documented Hansard and Votes sources
- Added URL patterns and HTML structure
- Included scraping strategies

---

## References

- [Parliament of Kenya Official Website](https://parliament.go.ke)
- [Kenya Constitution](http://www.parliament.go.ke/the-constitution-of-kenya)
- [Standing Orders](http://www.parliament.go.ke/the-national-assembly/house-business/standing-orders)

---

## Appendix: Example Data

### Example Hansard Filename

```
Hansard Report - Tuesday, 4th November 2025 (P).pdf
```

**Extracted Metadata**:
- Date: 2025-11-04
- Day: Tuesday
- Period: P (Morning)
- Chamber: National Assembly (from URL)

**Standardized Filename**:
```
hansard_20251104_P.pdf
```

### Example Votes Filename

```
Tuesday ,November 4, 2025 at 2.30pm.pdf
```

**Extracted Metadata**:
- Date: 2025-11-04
- Time: 14:30 (2:30 PM)
- Chamber: National Assembly (from URL)

**Standardized Filename**:
```
votes_20251104T143000Z.pdf
```

---

## Future Data Sources

### Planned Additions

1. **Committee Reports**: Committee meeting reports and recommendations
2. **Order Papers**: Daily agenda and business
3. **Legislative Proposals**: Pre-bill proposals
4. **Auditor Reports**: Financial audit reports
5. **MP Profiles**: Biographical information and constituencies

### API Access

Currently, parliament.go.ke does not provide a public API. All data access is via web scraping.

**Future**: Monitor for official API announcements.
