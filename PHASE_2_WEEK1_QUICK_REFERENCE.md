# Phase 2 Week 1 - Quick Reference Guide

## Component Quick Start

### BillScraper - Bill Discovery & Download

```python
from hansard_tales.config.settings import ScraperConfig
from hansard_tales.scrapers.bills import BillScraper
from hansard_tales.models.base import Chamber

# Initialize
config = ScraperConfig(base_url="https://parliament.go.ke")
scraper = BillScraper(config)

# Discover bills
bills = scraper.discover_bills(
    chamber=Chamber.NATIONAL_ASSEMBLY,
    parliament_term=2022
)

# Download a bill
pdf_content = scraper.download_bill(bills[0])

# Get URLs for batch processing
urls = scraper.get_document_urls(Chamber.SENATE)
```

**Output**: List of `BillMetadata` objects with:
- `bill_number`: e.g., "5/2023"
- `title`: Bill title
- `chamber`: Chamber enum
- `sponsor`: Sponsoring MP name
- `introduction_date`: date object
- `status`: Bill status (e.g., "First Reading")
- `url`: PDF URL
- `source_hash`: SHA256 for deduplication

---

### BillTextExtractor - Text & Structure Extraction

```python
from hansard_tales.processors.bill_processor import BillTextExtractor

# Initialize
extractor = BillTextExtractor()

# Extract raw text
text = extractor.extract_text(pdf_content)

# Extract metadata
metadata = extractor.extract_metadata(text)
# Returns: {
#   "bill_number": "5/2023",
#   "title": "Agriculture Bill",
#   "date": "15 January 2024",
#   "chapter": None
# }

# Extract full structure
structure = extractor.extract_structure(pdf_content)
# Returns BillStructure with:
#   - preamble: str
#   - parts: list[dict]  # Each with part_number, text, sections
#   - schedules: list[dict]  # Each with schedule_number, text
#   - explanatory_memo: str or None
```

**Use Case**: Parse bills for database storage and search indexing.

---

### BillVersionTracker - Change Detection

```python
from hansard_tales.analysis.bill_version_tracker import BillVersionTracker

# Initialize
tracker = BillVersionTracker()

# Add versions
tracker.add_version(
    version_number=1,
    text=original_bill_text,
    date="2024-01-15",
    title="Agriculture Bill v1"
)

tracker.add_version(
    version_number=2,
    text=amended_bill_text,
    date="2024-02-20",
    title="Agriculture Bill v2"
)

# Generate diff
changes = tracker.generate_diff(1, 2)
# Returns list of BillChange objects:
# - change_type: "addition", "deletion", or "modification"
# - section_number: Affected section
# - old_text: Previous text (if applicable)
# - new_text: New text (if applicable)
# - description: Human-readable summary

# Get summary
summary = tracker.get_changes_summary(1, 2)
# Returns formatted string with counts and highlights

# Manage versions
all_versions = tracker.list_versions()  # [1, 2, 3, ...]
info = tracker.get_version_info(1)  # Version metadata
```

**Use Case**: Track amendments and changes across bill versions.

---

## Data Flow

```
parliament.go.ke
      ↓
BillScraper.discover_bills() → BillMetadata list
      ↓
BillScraper.download_bill() → PDF bytes
      ↓
BillTextExtractor.extract_structure() → BillStructure
      ↓
Store in Database (bills, bill_versions ORM)
      ↓
BillVersionTracker (for amendments)
      ↓
Vector DB for Search/RAG (Week 2)
      ↓
LLM Analysis (Week 2)
```

---

## Testing Examples

### Unit Test Pattern

```python
import pytest
from unittest.mock import patch, MagicMock
from hansard_tales.scrapers.bills import BillScraper
from hansard_tales.config.settings import ScraperConfig

@pytest.fixture
def scraper():
    config = ScraperConfig(base_url="https://parliament.go.ke")
    return BillScraper(config)

def test_discover_bills(scraper):
    html_content = """
    <html>
        <table class="views-table">
            <tr>
                <td>Bill No. 5 of 2023</td>
                <td>The Agriculture Bill</td>
                <td>Hon. Smith</td>
                <td>15/01/2023</td>
                <td>First Reading</td>
                <td><a href="/files/bill.pdf">Download</a></td>
            </tr>
        </table>
    </html>
    """

    with patch.object(scraper, '_fetch_page_with_retry') as mock_fetch:
        mock_response = MagicMock()
        mock_response.content = html_content.encode()
        mock_fetch.return_value = mock_response

        bills = scraper.discover_bills(Chamber.NATIONAL_ASSEMBLY)

        assert len(bills) == 1
        assert bills[0].bill_number == "Bill No. 5 of 2023"
```

---

## Configuration

### ScraperConfig (from Phase 1)
```python
from hansard_tales.config.settings import ScraperConfig

config = ScraperConfig(
    base_url="https://parliament.go.ke",
    timeout=30,
    user_agent="HansardTales/1.0",
    max_retries=3,
    delay_between_requests=1.0
)
```

### Environment Variables
```bash
PARLIAMENT_BASE_URL=https://parliament.go.ke
SCRAPER_TIMEOUT=30
SCRAPER_USER_AGENT=HansardTales/1.0
SCRAPER_MAX_RETRIES=3
```

---

## Error Handling

### BillScraper Errors
```python
from hansard_tales.scrapers.base import DataCollectionError

try:
    bills = scraper.discover_bills(chamber)
except DataCollectionError as e:
    print(f"Scraping failed: {e}")
    # Handle: No bills found, website structure changed
```

### BillTextExtractor Errors
```python
try:
    text = extractor.extract_text(pdf_content)
except ValueError as e:
    print(f"PDF extraction failed: {e}")
    # Handle: Invalid PDF, unreadable content
```

### BillVersionTracker Errors
```python
try:
    changes = tracker.generate_diff(1, 2)
except ValueError as e:
    print(f"Diff generation failed: {e}")
    # Handle: Version not found
```

---

## Performance Tips

1. **Batch Processing**: Use `get_document_urls()` with `xdist` for parallel downloads
2. **Caching**: Cache extracted text to avoid re-parsing PDFs
3. **Database Indexes**: Use pre-created indexes on bill_number, status, chamber
4. **Vector DB**: Batch embeddings for efficiency
5. **Cost Control**: Track LLM calls with CostManager (Phase 1)

---

## Test Coverage

| Component | Coverage | Tests | Status |
|-----------|----------|-------|--------|
| BillScraper | 80.18% | 13 | ✅ Pass |
| BillTextExtractor | 89.13% | 17 | ✅ Pass |
| BillVersionTracker | 100% | 26 | ✅ Pass |
| **Total New** | **~86%** | **56** | ✅ Pass |

---

## Integration Checklist

- [x] BillScraper extends BaseScraper
- [x] Extract_metadata() abstract method implemented
- [x] Database models exist (BillORM, BillVersionORM)
- [x] Alembic migrations ready
- [x] CostManager integration point identified
- [x] Vector DB integration planned
- [x] Error handling with retry logic
- [x] Comprehensive unit tests (56)
- [ ] Integration tests with real bills (Week 2)
- [ ] Performance benchmarks (Week 2)
- [ ] End-to-end pipeline test (Week 2)

---

## Related Files

- Implementation: [bills.py](hansard_tales/scrapers/bills.py), [bill_processor.py](hansard_tales/processors/bill_processor.py), [bill_version_tracker.py](hansard_tales/analysis/bill_version_tracker.py)
- Tests: [test_bill_scraper.py](tests/unit/test_bill_scraper.py), [test_bill_processor.py](tests/unit/test_bill_processor.py), [test_bill_version_tracker.py](tests/unit/test_bill_version_tracker.py)
- Database: [models.py](hansard_tales/database/models.py) (ORM definitions)
- Migrations: [alembic/versions/](alembic/versions/) (all 4 migration files)

---

## Week 2 Roadmap

- Task 5: BillSummarizer with LLM (8-10 tests)
- Task 6: QuestionScraper (12-15 tests)
- Task 7: PetitionScraper (12-15 tests)
- Task 8: Pipeline integration (10-15 tests)

**Target**: 50-60 additional tests, 775→830+ passing
