# Hansard Tales MVP

**Transparency platform tracking Kenyan MPs through parliamentary records**

[![CI](https://github.com/otienoanyango/hansard-tales/actions/workflows/ci.yml/badge.svg)](https://github.com/otienoanyango/hansard-tales/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/otienoanyango/hansard-tales/branch/main/graph/badge.svg)](https://codecov.io/gh/otienoanyango/hansard-tales)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Live Demo**: https://otienoanyango.github.io/hansard-tales/

## Overview

Hansard Tales makes political accountability accessible to ordinary citizens by analyzing official parliamentary records (Hansard transcripts) and presenting MP performance data in an easy-to-understand format.

### Key Features

- **349 MP Profiles**: Complete profiles for all current Members of Parliament
- **Parliamentary Term Tracking**: View current (13th Parliament: 2022-2027) and historical performance
- **Smart Search**: Search by MP name or constituency (mobile-friendly)
- **Source Attribution**: Every statement links back to official Hansard documents
- **Mobile-First**: Optimized for 3G networks and mobile devices

## Project Goals

- **Target Audience**: Kenyan voters researching their MP
- **Data Coverage**: All 349 current MPs with historical data back to 2022
- **Update Frequency**: Weekly batch processing of new Hansard documents
- **Cost Target**: £10-30/month operational costs

## Architecture

This is a **static site generator** that:

1. **Scrapes** Hansard PDFs from parliament.go.ke weekly
2. **Extracts** text and identifies MP statements using NLP
3. **Stores** data in SQLite database (versioned in Git)
4. **Generates** static HTML pages for all MPs
5. **Deploys** to Cloudflare Pages (free tier)

### Technology Stack

- **Language**: Python 3.11+
- **PDF Processing**: pdfplumber
- **NLP**: spaCy (Named Entity Recognition)
- **Database**: SQLite (serverless, Git-versioned)
- **Templates**: Jinja2
- **Search**: Fuse.js (client-side fuzzy search)
- **Hosting**: Cloudflare Pages (free tier)
- **CI/CD**: GitHub Actions (free for public repos)

## Project Structure

```
hansard-tales/
├── hansard_tales/          # Main Python package
│   ├── scrapers/          # Web scraping modules
│   │   ├── hansard_scraper.py    # Hansard PDF scraper
│   │   └── mp_data_scraper.py    # MP data scraper
│   ├── processors/        # Data processing modules
│   │   ├── pdf_processor.py      # PDF text extraction
│   │   ├── mp_identifier.py      # MP identification (NLP)
│   │   └── bill_extractor.py     # Bill reference extraction
│   └── database/          # Database management
│       ├── init_db.py            # Database initialization
│       ├── init_parliament_data.py  # Parliament data setup
│       ├── import_mps.py         # MP data import
│       └── db_updater.py         # Database updates
├── tests/                  # Test suite (200+ tests)
│   ├── test_scraper.py
│   ├── test_mp_data_scraper.py
│   ├── test_pdf_processor.py
│   ├── test_mp_identifier.py
│   ├── test_bill_extractor.py
│   ├── test_database.py
│   ├── test_parliament_data.py
│   ├── test_import_mps.py
│   └── test_db_updater.py
├── data/                   # Data storage (Git-versioned)
│   ├── pdfs/              # Downloaded Hansard PDFs (gitignored)
│   ├── hansard.db         # SQLite database
│   ├── mps_13th_parliament.json  # MP data (349 MPs)
│   └── mps_12th_parliament.json  # Historical MP data
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md    # System architecture
│   ├── DEVELOPMENT.md     # Development guide
│   ├── MP_DATA_SCRAPING.md  # MP scraping guide
│   ├── PROJECT_SETUP.md   # Setup instructions
│   ├── QUICK_START.md     # Quick start guide
│   ├── WORKFLOW_ORCHESTRATION.md  # Workflow automation guide
│   ├── STORAGE_ABSTRACTION.md     # Storage backend guide
│   └── FILENAME_FORMAT.md         # Filename format and migration
├── templates/              # Jinja2 HTML templates (future)
│   ├── base.html          # Base template
│   ├── mp_profile.html    # MP profile page
│   ├── homepage.html      # Homepage with search
│   └── party.html         # Party pages
├── output/                 # Generated static site (future, gitignored)
│   ├── index.html         # Homepage
│   ├── mp/                # MP profile pages
│   ├── party/             # Party pages
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript (search)
│   └── data/              # Search index JSON
├── .github/
│   └── workflows/
│       ├── ci.yml         # Continuous Integration (tests, coverage)
│       ├── auto-merge.yml # Auto-merge feature branches
│       └── weekly-update.yml  # Weekly data processing (future)
├── pyproject.toml          # Package configuration
├── requirements.txt        # Python dependencies
├── pytest.ini             # Test configuration
├── .gitignore
└── README.md
```

## Getting Started

### Quick Start

See [Quick Start Guide](docs/QUICK_START.md) for a 5-minute setup.

### Prerequisites

- Python 3.11 or higher
- Git
- Virtual environment (recommended)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/hansard-tales.git
   cd hansard-tales
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package in development mode**:
   ```bash
   pip install -e .
   python -m spacy download en_core_web_sm
   ```

4. **Initialize database**:
   ```bash
   hansard-init-db
   hansard-init-parliament
   ```

5. **Import MP data**:
   ```bash
   hansard-import-mps --file data/mps_13th_parliament.json --current
   ```

6. **Run tests** (optional):
   ```bash
   pytest -n auto
   ```

## Development Workflow

See [Development Guide](docs/DEVELOPMENT.md) for detailed development workflow, testing, and troubleshooting.

### CI/CD Pipeline

The project uses GitHub Actions for automated testing and deployment:

- **CI Workflow** (`ci.yml`): Runs on every push and PR
  - Tests on Python 3.11 and 3.12
  - Parallel test execution with pytest-xdist
  - Coverage reporting (85% minimum threshold)
  - Automatic coverage upload to Codecov

- **Auto-Merge Workflow** (`auto-merge.yml`): Automatically merges feature branches
  - Triggers on PRs from `feat/` branches
  - Waits for CI checks to pass
  - Auto-merges with squash strategy
  - Automatically deletes merged branches

See [GitHub Actions README](.github/workflows/README.md) for setup instructions.

### Workflow Orchestration

The system provides an end-to-end workflow orchestrator that automates the complete pipeline:

```bash
# Run complete workflow (scrape → process → index → generate)
python scripts/run_workflow.py

# Run with date range filtering
python scripts/run_workflow.py --start-date 2024-01-01 --end-date 2024-12-31

# Run with custom workers for faster processing
python scripts/run_workflow.py --workers 8

# Run with custom paths
python scripts/run_workflow.py --db-path data/hansard.db --output-dir output/
```

The workflow orchestrator executes these steps in sequence:
1. **Scrape MPs**: Download MP data from parliament website
2. **Scrape Hansards**: Download Hansard PDFs with duplicate detection
3. **Process PDFs**: Extract text and identify MP statements
4. **Generate Search Index**: Create searchable MP index
5. **Generate Static Site**: Build HTML pages for all MPs

### Weekly Processing (Automated via GitHub Actions)

The system automatically runs every Sunday at 2 AM EAT:

1. Scrapes new Hansard PDFs from parliament.go.ke
2. Extracts text and identifies MP statements
3. Updates SQLite database
4. Regenerates static site
5. Commits changes to Git
6. Deploys to Cloudflare Pages

### Manual Processing

#### Individual Components

To process components manually:

```bash
# Activate virtual environment
source venv/bin/activate

# Scrape MP data
hansard-mp-scraper --term 2022 --output data/mps_13th_parliament.json

# Import MP data
hansard-import-mps --file data/mps_13th_parliament.json --current

# Scrape Hansard PDFs (with enhanced duplicate detection)
hansard-scraper --output data/pdfs/hansard --max-pages 5

# Process a specific PDF
hansard-pdf-processor --pdf data/pdfs/hansard/hansard_20240101_P.pdf
```

#### Database Management

The system provides utilities for database backup and maintenance:

```bash
# Create a timestamped backup
python scripts/db_manager.py backup --db-path data/hansard.db

# Clean database (preserves downloaded_pdfs table)
python scripts/db_manager.py clean --db-path data/hansard.db

# Clean without confirmation prompt
python scripts/db_manager.py clean --db-path data/hansard.db --no-confirm

# Preserve additional tables during clean
python scripts/db_manager.py clean --db-path data/hansard.db --preserve-tables downloaded_pdfs mps
```

Backups are stored in `data/backups/` with format: `hansard_YYYYMMDD_HHMMSS.db`

## Data Model

### Storage Abstraction

The system uses a storage abstraction layer to support multiple storage backends:

**Current Backend**: Filesystem storage (local directory)
**Future Support**: S3, cloud storage, etc.

#### Storage Configuration

```python
from hansard_tales.storage.filesystem import FilesystemStorage
from hansard_tales.storage.config import get_storage_backend

# Use default filesystem storage
storage = get_storage_backend()

# Use custom directory
storage = get_storage_backend(
    backend_type="filesystem",
    config={"base_dir": "custom/path"}
)

# Use storage in scraper
from hansard_tales.scrapers.hansard_scraper import HansardScraper
scraper = HansardScraper(storage=storage, db_path="data/hansard.db")
```

#### Standardized Filename Format

All Hansard PDFs use a standardized naming convention:

**Format**: `hansard_YYYYMMDD_{A|P|E}.pdf`

Where:
- `YYYYMMDD`: Date in compact format (e.g., 20240101)
- `A`: Afternoon sitting
- `P`: Morning/Plenary sitting (default)
- `E`: Evening sitting

**Examples**:
- `hansard_20240101_P.pdf` - Morning sitting on January 1, 2024
- `hansard_20240101_A.pdf` - Afternoon sitting on January 1, 2024
- `hansard_20240101_A_2.pdf` - Second afternoon sitting (duplicate handling)

**Period-of-Day Extraction**:
The system automatically extracts the period-of-day from PDF metadata:
- Searches PDF title and first page for keywords
- Keywords: "afternoon" → A, "morning" → P, "evening" → E
- Defaults to P (Morning) if not found
- Case-insensitive matching

**Duplicate Handling**:
When multiple PDFs exist for the same date and period, a numeric suffix is appended:
- First file: `hansard_20240101_A.pdf`
- Second file: `hansard_20240101_A_2.pdf`
- Third file: `hansard_20240101_A_3.pdf`

### Download Tracking

All downloaded PDFs are tracked in the `downloaded_pdfs` database table with comprehensive metadata:

**Tracked Information**:
- Original URL from parliament website
- File path in storage
- Date and period-of-day
- Session ID (linked after processing)
- File size
- Download timestamp

**Duplicate Prevention**:
The scraper checks both storage and database before downloading:
1. **File exists + DB record**: Skip download
2. **File exists, no DB record**: Create record, skip download
3. **No file, DB record exists**: Re-download file
4. **Neither exists**: Download and create record

This ensures efficient bandwidth usage and maintains accurate download history.

### Parliamentary Terms

The system tracks MPs across multiple parliamentary terms:

- **13th Parliament** (2022-2027): Current term
- **12th Parliament** (2017-2022): Historical data (optional)

### Core Entities

- **MPs**: 349 current Members of Parliament
- **Parliamentary Terms**: 5-year periods (e.g., 13th Parliament)
- **MP Terms**: Junction table linking MPs to terms (handles constituency/party changes)
- **Hansard Sessions**: Daily parliamentary sittings
- **Statements**: Individual MP statements in sessions
- **Downloaded PDFs**: Tracking table for all downloaded Hansard files

### Performance Metrics

- **Statement Count**: Number of times MP spoke
- **Session Attendance**: Sessions where MP participated
- **Bills Mentioned**: Bills discussed by MP
- **Active Periods**: Timeline of parliamentary activity

## Deployment

### Cloudflare Pages Setup

1. Connect GitHub repository to Cloudflare Pages
2. Set build command: (none - pre-built by GitHub Actions)
3. Set output directory: `output/`
4. Enable automatic deployments on push to main

### GitHub Actions

The `.github/workflows/weekly-update.yml` workflow:

- Runs weekly (Sunday 2 AM EAT)
- Can be triggered manually
- Processes new data and deploys automatically

## Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| GitHub Actions | £0 | 2,000 minutes/month free |
| Cloudflare Pages | £0 | Unlimited bandwidth |
| SQLite | £0 | No database server |
| Domain (.ke) | £1/month | ~£12/year |
| **Total** | **£1/month** | 95% cost reduction vs cloud |

## Performance Targets

- **Page Load**: <2 seconds on 3G networks
- **Search Response**: <100ms (client-side)
- **Processing Time**: <30 minutes weekly
- **MP Attribution Accuracy**: >90%
- **Uptime**: 99%+

## Contributing

This is a solo-maintainer project optimized for simplicity. Contributions welcome!

### Development Principles

1. **Simplicity First**: Single language (Python), minimal dependencies
2. **Cost Optimization**: Use free tiers aggressively
3. **Solo Maintainable**: One person can build and maintain
4. **No Vendor Lock-in**: Can run anywhere
5. **Ship Fast**: Focus on core value, defer complexity

## Common Operations

### Complete Workflow

Run the entire pipeline from scraping to site generation:

```bash
# Full workflow with defaults
python scripts/run_workflow.py

# With date filtering (process only specific date range)
python scripts/run_workflow.py --start-date 2024-01-01 --end-date 2024-12-31

# With more workers for faster processing
python scripts/run_workflow.py --workers 8

# With custom database and output paths
python scripts/run_workflow.py \
  --db-path data/hansard.db \
  --output-dir output/ \
  --storage-dir data/pdfs/hansard
```

### Database Operations

#### Backup Before Major Operations

Always create a backup before processing new data:

```bash
# Create timestamped backup
python scripts/db_manager.py backup --db-path data/hansard.db

# Backup to custom directory
python scripts/db_manager.py backup \
  --db-path data/hansard.db \
  --backup-dir backups/
```

Backups are stored with format: `hansard_YYYYMMDD_HHMMSS.db`

#### Clean Database

Remove all data except download tracking (useful for reprocessing):

```bash
# Clean with confirmation prompt
python scripts/db_manager.py clean --db-path data/hansard.db

# Clean without confirmation (use with caution!)
python scripts/db_manager.py clean --db-path data/hansard.db --no-confirm

# Preserve additional tables
python scripts/db_manager.py clean \
  --db-path data/hansard.db \
  --preserve-tables downloaded_pdfs mps parliamentary_terms
```

The clean operation:
- Deletes all data from most tables
- Preserves `downloaded_pdfs` table (maintains download history)
- Preserves any additional tables specified with `--preserve-tables`
- Requires confirmation unless `--no-confirm` is used

### Scraping Operations

#### Scrape New Hansard PDFs

```bash
# Scrape with date range
hansard-scraper \
  --output data/pdfs/hansard \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --max-pages 10

# Scrape all available (use with caution - may take hours)
hansard-scraper --output data/pdfs/hansard --max-pages 100
```

The scraper:
- Automatically detects and skips existing files
- Extracts period-of-day from PDF metadata
- Generates standardized filenames
- Tracks all downloads in database
- Logs skip reasons for transparency

#### Scrape MP Data

```bash
# Scrape current parliament (13th Parliament, 2022-2027)
hansard-mp-scraper --term 2022 --output data/mps_13th_parliament.json

# Import scraped MP data
hansard-import-mps --file data/mps_13th_parliament.json --current
```

### Processing Operations

#### Process Historical PDFs

```bash
# Process all PDFs in directory
python -m hansard_tales.process_historical_data \
  --pdf-dir data/pdfs/hansard \
  --db-path data/hansard.db \
  --workers 4

# Process with date filtering
python -m hansard_tales.process_historical_data \
  --pdf-dir data/pdfs/hansard \
  --db-path data/hansard.db \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --workers 8

# Dry run (preview without making changes)
python -m hansard_tales.process_historical_data \
  --pdf-dir data/pdfs/hansard \
  --db-path data/hansard.db \
  --dry-run

# Force reprocess (ignore already processed PDFs)
python -m hansard_tales.process_historical_data \
  --pdf-dir data/pdfs/hansard \
  --db-path data/hansard.db \
  --force
```

#### Process Single PDF

```bash
# Process specific PDF
hansard-pdf-processor --pdf data/pdfs/hansard/hansard_20240101_P.pdf

# Process with custom database
hansard-pdf-processor \
  --pdf data/pdfs/hansard/hansard_20240101_P.pdf \
  --db-path data/hansard.db
```

### Site Generation

#### Generate Static Site

```bash
# Generate complete site
python -m hansard_tales.site_generator \
  --db-path data/hansard.db \
  --output-dir output/

# Generate search index only
python -m hansard_tales.search_index_generator \
  --db-path data/hansard.db \
  --output-dir output/data/
```

### Troubleshooting

#### Check Download Status

```bash
# Query database for download statistics
sqlite3 data/hansard.db "
  SELECT 
    period_of_day,
    COUNT(*) as count,
    SUM(file_size) / 1024 / 1024 as total_mb
  FROM downloaded_pdfs
  GROUP BY period_of_day;
"
```

#### Verify File Integrity

```bash
# Check for missing files
sqlite3 data/hansard.db "
  SELECT file_path 
  FROM downloaded_pdfs 
  WHERE file_path NOT IN (
    SELECT file_path FROM downloaded_pdfs 
    WHERE file_size > 0
  );
"
```

#### Re-download Missing Files

If files are tracked in database but missing from storage:

```bash
# The scraper will automatically detect and re-download
hansard-scraper --output data/pdfs/hansard --max-pages 10
```

### Development Workflow

#### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hansard_tales --cov-report=html

# Run specific test file
pytest tests/test_scraper.py

# Run with parallel execution
pytest -n auto
```

#### Check Code Quality

```bash
# Run linter
flake8 hansard_tales/

# Run type checker
mypy hansard_tales/

# Format code
black hansard_tales/
```

## Data Sources

- **Hansard Transcripts**: parliament.go.ke/hansard
- **MP Database**: Manually compiled from official sources
- **Parliamentary Terms**: Official parliamentary records

## Documentation

### Core Documentation

- **[Quick Start Guide](docs/QUICK_START.md)**: Get started in 5 minutes
- **[Development Guide](docs/DEVELOPMENT.md)**: Development workflow and testing
- **[Architecture](docs/ARCHITECTURE.md)**: System architecture overview
- **[Project Setup](docs/PROJECT_SETUP.md)**: Detailed setup instructions

### Feature Documentation

- **[Workflow Orchestration](docs/WORKFLOW_ORCHESTRATION.md)**: End-to-end workflow automation
  - Complete pipeline execution
  - Individual step control
  - Performance optimization
  - Error handling and recovery

- **[Storage Abstraction](docs/STORAGE_ABSTRACTION.md)**: Storage backend system
  - Filesystem storage (current)
  - Future cloud storage support
  - Custom backend implementation
  - Migration between backends

- **[Filename Format](docs/FILENAME_FORMAT.md)**: Standardized PDF naming
  - Format specification
  - Period-of-day extraction
  - Duplicate handling
  - Migration from old formats

### Specialized Guides

- **[MP Data Scraping](docs/MP_DATA_SCRAPING.md)**: Scraping MP information
- **[GitHub Actions](docs/.github/workflows/README.md)**: CI/CD setup

## Legal & Compliance

- **Source Attribution**: Every claim links to official source
- **Non-Partisan**: Factual data only, no political bias
- **Privacy**: No user accounts, no personal data collection
- **Transparency**: Open methodology, open source code

## Roadmap

### Phase 1: MVP (Weeks 1-4) ✅ Current

- [x] Project setup and database schema
- [ ] Hansard PDF scraper
- [ ] MP identification system
- [ ] Static site generation
- [ ] Search functionality
- [ ] Deployment automation

### Phase 2: Enhancements (Months 2-3)

- [ ] Bill-centric pages
- [ ] Party comparison pages
- [ ] Enhanced search filters
- [ ] Social sharing features

### Phase 3: Growth (Months 4-6)

- [ ] AI-generated cartoons (optional)
- [ ] Basic infographics
- [ ] API for partners
- [ ] Historical data expansion

## Success Criteria

**Technical**:
- ✅ All 349 MPs have profiles
- ✅ Processing completes in <30 minutes
- ✅ Page load time <2 seconds
- ✅ Monthly costs <£30

**Business**:
- 🎯 1,000+ unique visitors/month
- 🎯 2+ pages per session
- 🎯 60%+ mobile traffic
- 🎯 5+ media mentions

## Support

For questions or issues:
- Open an issue on GitHub
- Email: [your-email]
- Twitter: [@hansardtales]

## License

[Choose appropriate license - MIT, Apache 2.0, etc.]

## Acknowledgments

- Parliament of Kenya for making Hansard records publicly available
- Open source community for excellent Python libraries
- Kenyan citizens demanding political accountability

---

**Built with ❤️ for Kenyan democracy**
