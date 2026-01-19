# Hansard Tales MVP

**Transparency platform tracking Kenyan MPs through parliamentary records**

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
├── data/                    # Data storage (Git-versioned)
│   ├── pdfs/               # Downloaded Hansard PDFs (gitignored)
│   └── hansard.db          # SQLite database
├── scripts/                # Python processing scripts
│   ├── init_db.py         # Database initialization
│   ├── scraper.py         # Hansard PDF scraper
│   ├── processor.py       # PDF text extraction & parsing
│   ├── generate_site.py   # Static site generator
│   └── main.py            # Main processing pipeline
├── templates/              # Jinja2 HTML templates
│   ├── base.html          # Base template
│   ├── mp_profile.html    # MP profile page
│   ├── homepage.html      # Homepage with search
│   └── party.html         # Party pages
├── output/                 # Generated static site (gitignored)
│   ├── index.html         # Homepage
│   ├── mp/                # MP profile pages
│   ├── party/             # Party pages
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript (search)
│   └── data/              # Search index JSON
├── .github/
│   └── workflows/
│       └── weekly-update.yml  # GitHub Actions workflow
├── requirements.txt        # Python dependencies
├── .gitignore
└── README.md
```

## Getting Started

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

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. **Initialize database**:
   ```bash
   python scripts/init_db.py
   ```

5. **Run the processing pipeline** (with sample data):
   ```bash
   python scripts/main.py
   ```

6. **Serve the site locally**:
   ```bash
   cd output
   python -m http.server 8000
   ```
   Visit http://localhost:8000

## Development Workflow

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

# Run full pipeline
python scripts/main.py

# Or run individual steps
python scripts/scraper.py          # Download new PDFs
python scripts/processor.py        # Process PDFs
python scripts/generate_site.py    # Generate static site
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
