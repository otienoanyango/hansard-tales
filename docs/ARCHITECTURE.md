# Hansard Tales - Architecture Documentation

## Overview

Hansard Tales is a parliamentary transparency platform that tracks Kenyan MPs through parliamentary Hansard records. The system scrapes, processes, and presents parliamentary data in an accessible format.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Collection Layer                    │
├─────────────────────────────────────────────────────────────┤
│  • Hansard PDF Scraper (parliament.go.ke)                   │
│  • MP Data Scraper (parliament.go.ke/mps)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Layer                          │
├─────────────────────────────────────────────────────────────┤
│  • PDF Text Extraction (pdfplumber)                         │
│  • MP Identification (regex + spaCy NER)                    │
│  • Bill Reference Extraction (regex patterns)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Storage Layer                       │
├─────────────────────────────────────────────────────────────┤
│  • SQLite Database (hansard.db)                             │
│  • Parliamentary Terms, MPs, Sessions, Statements           │
│  • Indexes and Views for Performance                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                         │
├─────────────────────────────────────────────────────────────┤
│  • Static Site Generation (Jinja2)                          │
│  • Client-Side Search (Fuse.js)                             │
│  • MP Profiles, Party Pages, Search Index                   │
└─────────────────────────────────────────────────────────────┘
```

## Package Structure

```
hansard_tales/
├── __init__.py                 # Package initialization
├── scrapers/                   # Web scraping modules
│   ├── __init__.py
│   ├── hansard_scraper.py     # Scrapes Hansard PDFs from parliament.go.ke
│   └── mp_data_scraper.py     # Scrapes MP data (names, constituencies, parties)
├── processors/                 # Data processing modules
│   ├── __init__.py
│   ├── pdf_processor.py       # Extracts text from PDF files
│   ├── mp_identifier.py       # Identifies MPs in Hansard text
│   └── bill_extractor.py      # Extracts bill references from text
└── database/                   # Database management modules
    ├── __init__.py
    ├── init_db.py             # Database schema initialization
    ├── init_parliament_data.py # Loads parliamentary term data
    ├── import_mps.py          # Imports MP data from JSON
    └── db_updater.py          # Updates database with processed Hansard data
```

## Component Details

### 1. Data Collection Layer

#### Hansard Scraper (`hansard_scraper.py`)
- **Purpose**: Downloads Hansard PDF files from parliament.go.ke
- **Key Features**:
  - Pagination handling
  - Rate limiting (respectful scraping)
  - Retry logic for failed requests
  - PDF metadata extraction (date, title)
- **Output**: PDF files saved to `data/pdfs/`

#### MP Data Scraper (`mp_data_scraper.py`)
- **Purpose**: Scrapes current MP information
- **Key Features**:
  - Handles multiple parliamentary terms (2022, 2017)
  - Extracts: name, constituency, county, party, status, photo URL
  - Pagination support (10 MPs per page)
  - Handles both elected and nominated MPs
- **Output**: JSON files (`data/mps_13th_parliament.json`, etc.)

### 2. Processing Layer

#### PDF Processor (`pdf_processor.py`)
- **Purpose**: Extracts text from Hansard PDF files
- **Technology**: pdfplumber library
- **Key Features**:
  - Page-by-page text extraction
  - Preserves page numbers for source attribution
  - Handles malformed/scanned PDFs gracefully
  - Extraction statistics (pages, characters, etc.)
- **Output**: Structured text data with page metadata

#### MP Identifier (`mp_identifier.py`)
- **Purpose**: Identifies speakers (MPs) in Hansard text
- **Technology**: Regex patterns + spaCy NER
- **Key Features**:
  - Speaker pattern matching ("Hon. [Name]:")
  - Statement extraction (from speaker to next speaker)
  - Name normalization (removes titles, standardizes format)
  - Handles edge cases (interruptions, multiple speakers)
- **Output**: List of Statement objects (speaker, text, page)

#### Bill Extractor (`bill_extractor.py`)
- **Purpose**: Extracts bill references from Hansard text
- **Technology**: Regex patterns
- **Key Features**:
  - Multiple bill format support:
    - "Bill No. 123"
    - "The Finance Bill, 2024"
    - "Bill 2024/123"
  - Deduplication
  - Position tracking for context
- **Output**: List of BillReference objects

### 3. Data Storage Layer

#### Database Schema

**Parliamentary Terms Table**
```sql
CREATE TABLE parliamentary_terms (
    id INTEGER PRIMARY KEY,
    term_number INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    is_current BOOLEAN DEFAULT 0
);
```

**MPs Table**
```sql
CREATE TABLE mps (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    constituency TEXT,
    party TEXT,
    photo_url TEXT,
    first_elected_year INTEGER
);
```

**MP Terms Junction Table** (tracks MPs across multiple terms)
```sql
CREATE TABLE mp_terms (
    id INTEGER PRIMARY KEY,
    mp_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,
    constituency TEXT,
    party TEXT,
    elected_date DATE,
    left_date DATE,
    is_current BOOLEAN DEFAULT 0,
    FOREIGN KEY (mp_id) REFERENCES mps(id),
    FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id),
    UNIQUE(mp_id, term_id)
);
```

**Hansard Sessions Table**
```sql
CREATE TABLE hansard_sessions (
    id INTEGER PRIMARY KEY,
    session_date DATE NOT NULL,
    title TEXT,
    pdf_url TEXT,
    pdf_filename TEXT,
    term_id INTEGER,
    FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id)
);
```

**Statements Table**
```sql
CREATE TABLE statements (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    mp_id INTEGER,
    statement_text TEXT NOT NULL,
    page_number INTEGER,
    bill_references TEXT,  -- JSON array
    FOREIGN KEY (session_id) REFERENCES hansard_sessions(id),
    FOREIGN KEY (mp_id) REFERENCES mps(id)
);
```

#### Database Views

**Current MPs View**
```sql
CREATE VIEW current_mps AS
SELECT m.*, mt.constituency, mt.party, mt.elected_date
FROM mps m
JOIN mp_terms mt ON m.id = mt.mp_id
WHERE mt.is_current = 1;
```

**MP Performance Views**
- `mp_current_term_performance`: Statement counts for current term
- `mp_historical_performance`: Statement counts across all terms

### 4. Presentation Layer

#### Static Site Generator (Future)
- **Technology**: Jinja2 templates
- **Output**: Static HTML/CSS/JS files
- **Pages**:
  - MP profiles (349 individual pages)
  - Homepage with search
  - Party pages
  - All MPs listing

#### Client-Side Search (Future)
- **Technology**: Fuse.js
- **Features**:
  - Fuzzy search (name, constituency, party)
  - Fast client-side performance
  - Mobile-friendly interface

## Data Flow

### Complete Processing Pipeline

```
1. Scrape Hansard PDFs
   └─> hansard_scraper.py
       └─> data/pdfs/*.pdf

2. Scrape MP Data
   └─> mp_data_scraper.py
       └─> data/mps_*.json

3. Import MP Data
   └─> import_mps.py
       └─> Populates mps and mp_terms tables

4. Process Hansard PDFs
   └─> pdf_processor.py
       └─> Extract text from PDFs
           └─> mp_identifier.py
               └─> Identify speakers and statements
                   └─> bill_extractor.py
                       └─> Extract bill references
                           └─> db_updater.py
                               └─> Update database

5. Generate Static Site (Future)
   └─> generate_site.py
       └─> Query database
           └─> Render templates
               └─> output/*.html

6. Generate Search Index (Future)
   └─> generate_search_index.py
       └─> Query database
           └─> output/data/mp-search-index.json
```

## Technology Stack

### Core Technologies
- **Python 3.11+**: Primary programming language
- **SQLite**: Embedded database (no server required)
- **pdfplumber**: PDF text extraction
- **spaCy**: Natural Language Processing (NER)
- **BeautifulSoup4**: HTML parsing for web scraping
- **requests**: HTTP client for web scraping

### Development Tools
- **pytest**: Testing framework
- **pytest-cov**: Code coverage
- **pytest-xdist**: Parallel test execution
- **pytest-mock**: Mocking for tests

### Future Technologies
- **Jinja2**: Template engine for static site generation
- **Fuse.js**: Client-side fuzzy search
- **Cloudflare Pages**: Static site hosting
- **GitHub Actions**: CI/CD automation

## Design Principles

### 1. Modularity
- Each component has a single, well-defined responsibility
- Components can be tested and developed independently
- Clear interfaces between layers

### 2. Testability
- Comprehensive test coverage (200+ tests)
- Unit tests for individual functions
- Integration tests for complete workflows
- Mock external dependencies (web requests, file I/O)

### 3. Maintainability
- Clean code structure with proper package organization
- Comprehensive documentation
- Type hints for better IDE support
- Logging for debugging and monitoring

### 4. Performance
- Database indexes for fast queries
- Views for common query patterns
- Batch processing for large datasets
- Parallel test execution

### 5. Reliability
- Graceful error handling
- Retry logic for transient failures
- Data validation at each stage
- Idempotent operations (can be run multiple times safely)

## Deployment Architecture (Future)

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Repository                       │
│  • Source code                                              │
│  • SQLite database (committed weekly)                       │
│  • Generated static site (output/)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions                           │
│  • Weekly cron job (Sunday 2 AM EAT)                        │
│  • Scrape new Hansard PDFs                                  │
│  • Process and update database                              │
│  • Generate static site                                     │
│  • Commit and push changes                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Cloudflare Pages                          │
│  • Automatic deployment on push                             │
│  • CDN for fast global access                               │
│  • HTTPS enabled                                            │
│  • Custom .ke domain                                        │
└─────────────────────────────────────────────────────────────┘
```

## Performance Considerations

### Database Optimization
- Indexes on frequently queried columns (mp_id, session_id, term_id)
- Views for complex queries (avoid repeated joins)
- Batch inserts for large datasets

### Scraping Optimization
- Rate limiting to avoid overwhelming servers
- Retry logic with exponential backoff
- Parallel processing where appropriate

### Site Generation Optimization (Future)
- Static site generation (no server-side processing)
- Client-side search (no backend queries)
- CDN caching for fast global access

## Security Considerations

### Data Privacy
- No personal data beyond public parliamentary records
- MP information is already public on parliament.go.ke

### Web Scraping Ethics
- Respectful rate limiting (1 second delay between requests)
- User-Agent identification
- Robots.txt compliance

### Database Security
- SQLite file permissions (read-only for web serving)
- No SQL injection risks (parameterized queries)
- Regular backups via Git

## Monitoring and Maintenance

### Automated Monitoring (Future)
- GitHub Actions workflow status
- Processing error logs
- Data quality checks (MP attribution accuracy >90%)

### Manual Monitoring
- Weekly spot-checks of new data
- Monthly review of MP data changes
- Quarterly dependency updates

## Future Enhancements

### Phase 1 (Current)
- ✅ Data collection and processing
- ✅ Database schema and management
- ✅ MP data import

### Phase 2 (Next)
- Static site generation
- Client-side search
- MP profile pages

### Phase 3 (Future)
- Cloudflare Pages deployment
- GitHub Actions automation
- Analytics and monitoring

### Phase 4 (Optional)
- AI-generated cartoons (Imagen API)
- Advanced search filters
- Data visualizations
- API for third-party access

## References

- [Project Setup Guide](PROJECT_SETUP.md)
- [Development Guide](DEVELOPMENT.md)
- [MP Data Scraping Guide](MP_DATA_SCRAPING.md)
- [Quick Start Guide](QUICK_START.md)
