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
│   └── QUICK_START.md     # Quick start guide
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

### Weekly Processing (Automated via GitHub Actions)

The system automatically runs every Sunday at 2 AM EAT:

1. Scrapes new Hansard PDFs from parliament.go.ke
2. Extracts text and identifies MP statements
3. Updates SQLite database
4. Regenerates static site
5. Commits changes to Git
6. Deploys to Cloudflare Pages

### Manual Processing

To process new data manually:

```bash
# Activate virtual environment
source venv/bin/activate

# Scrape MP data
hansard-mp-scraper --term 2022 --output data/mps_13th_parliament.json

# Import MP data
hansard-import-mps --file data/mps_13th_parliament.json --current

# Scrape Hansard PDFs
hansard-scraper --output data/pdfs --max-pages 5

# Process a specific PDF
hansard-pdf-processor --pdf data/pdfs/Hansard_Report_2025-12-04.pdf
```

## Data Model

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

## Data Sources

- **Hansard Transcripts**: parliament.go.ke/hansard
- **MP Database**: Manually compiled from official sources
- **Parliamentary Terms**: Official parliamentary records

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
