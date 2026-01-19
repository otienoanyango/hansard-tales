# Hansard Tales MVP - Implementation Tasks

## Phase 1: Foundation & Setup (Week 1)

### 1. Project Setup
- [ ] 1.1 Initialize Git repository structure
  - Create directory structure (data/, scripts/, templates/, output/)
  - Set up .gitignore for Python and data files
  - Initialize README.md with project overview

- [ ] 1.2 Set up Python development environment
  - Create requirements.txt with dependencies (pdfplumber, spacy, jinja2, requests, beautifulsoup4)
  - Create virtual environment setup instructions
  - Document local development workflow

- [ ] 1.3 Initialize SQLite database schema
  - Create database initialization script (scripts/init_db.py)
  - Implement parliamentary_terms table
  - Implement mps table
  - Implement mp_terms junction table
  - Implement hansard_sessions table
  - Implement statements table
  - Create indexes for performance
  - Create views (current_mps, mp_current_term_performance, mp_historical_performance)

- [ ] 1.4 Initialize 13th Parliament data
  - Insert 13th Parliament term (2022-09-08 to 2027-09-07)
  - Optionally insert 12th Parliament term (2017-08-31 to 2022-09-07)
  - Mark 13th Parliament as current

### 2. Data Collection & Processing

- [ ] 2.1 Build Hansard PDF scraper
  - Implement scraper for parliament.go.ke/hansard
  - Handle pagination and listing pages
  - Extract PDF URLs and metadata (date, title)
  - Download PDFs to data/pdfs/ directory
  - Handle rate limiting and retries
  - Log scraping activity

- [ ] 2.2 Implement PDF text extraction
  - Create PDF processor using pdfplumber
  - Extract text from all pages
  - Preserve page numbers for source attribution
  - Handle malformed or scanned PDFs gracefully
  - Log extraction errors

- [ ] 2.3 Build MP identification system
  - Create regex patterns for speaker identification (e.g., "Hon. [Name]:")
  - Implement spaCy NER for name validation
  - Extract statement text (from speaker to next speaker)
  - Handle edge cases (multiple speakers, interruptions)
  - Create MP name normalization function

- [ ] 2.4 Implement bill reference extraction
  - Create regex patterns for bill references (e.g., "Bill No. 123")
  - Extract and store bill references with statements
  - Handle multiple bill formats

- [ ] 2.5 Build database update logic
  - Implement get_or_create_mp() function
  - Link MPs to current parliamentary term (mp_terms)
  - Create hansard_session records
  - Insert statements with MP and session links
  - Handle duplicate detection
  - Implement transaction management

### 3. MP Database Compilation

- [ ] 3.1 Compile current MPs list (349 MPs)
  - Research and compile MP names
  - Collect constituency information
  - Collect party affiliations
  - Collect election dates (2022-09-08 for most)
  - Find MP photo URLs (parliament.go.ke or other sources)

- [ ] 3.2 Populate MPs database
  - Create CSV or JSON file with MP data
  - Write import script (scripts/import_mps.py)
  - Insert MPs into mps table
  - Link MPs to 13th Parliament via mp_terms table
  - Verify data integrity

## Phase 2: Site Generation & Search (Week 2)

### 4. Static Site Generation

- [ ] 4.1 Set up Jinja2 templating
  - Create templates/ directory structure
  - Create base template (base.html) with header, footer, navigation
  - Set up CSS framework (Tailwind CSS or simple custom CSS)
  - Implement mobile-first responsive design

- [ ] 4.2 Create MP profile template
  - Design MP profile page layout (mp_profile.html)
  - Display current term information (constituency, party, term number)
  - Show current term performance metrics (statements, sessions, bills)
  - Add historical terms section (collapsible)
  - Display statements list with term filtering
  - Add source links to Hansard PDFs
  - Implement term filter dropdown

- [ ] 4.3 Create homepage template
  - Design homepage with search prominently featured
  - Add introduction to the platform
  - Show current parliamentary term info
  - Add recent activity feed (optional)
  - Include navigation to all MPs and parties

- [ ] 4.4 Create party pages template
  - List all MPs by party
  - Show party statistics (total MPs, avg statements)
  - Link to individual MP profiles

- [ ] 4.5 Create all MPs listing template
  - Display all 349 MPs in a table/grid
  - Add sorting options (name, constituency, statements)
  - Add party filter
  - Link to individual profiles

- [ ] 4.6 Implement site generation script
  - Create scripts/generate_site.py
  - Query database for MP data
  - Render templates with Jinja2
  - Generate all 349 MP profile pages
  - Generate homepage, party pages, listings
  - Copy static assets (CSS, JS, images)
  - Output to output/ directory

### 5. Client-Side Search

- [ ] 5.1 Generate search index JSON
  - Create scripts/generate_search_index.py
  - Query current MPs with performance data
  - Query historical terms for each MP
  - Format data for Fuse.js (name, constituency, party, keywords)
  - Include current_term metadata
  - Export to output/data/mp-search-index.json

- [ ] 5.2 Implement Fuse.js search
  - Create js/search.js
  - Load Fuse.js from CDN
  - Fetch mp-search-index.json
  - Configure fuzzy search (name, constituency, party)
  - Implement search input handler
  - Display search results with links
  - Handle empty results gracefully

- [ ] 5.3 Add search UI to homepage
  - Add search input field
  - Add search results container
  - Style search results (mobile-friendly)
  - Add loading states

## Phase 3: Deployment & Automation (Week 3)

### 6. GitHub Actions Setup

- [ ] 6.1 Create weekly processing workflow
  - Create .github/workflows/weekly-update.yml
  - Configure cron schedule (Sunday 2 AM EAT)
  - Add manual trigger option (workflow_dispatch)
  - Set up Python environment (3.11+)
  - Install dependencies (requirements.txt, spaCy model)

- [ ] 6.2 Implement processing pipeline
  - Run scraper to download new PDFs
  - Process PDFs (extract, parse, identify)
  - Update SQLite database
  - Generate search index
  - Generate static site
  - Commit and push changes to Git

- [ ] 6.3 Add error handling and notifications
  - Implement try-catch blocks
  - Log errors to GitHub Actions logs
  - Send email notifications on failure
  - Add retry logic for transient failures

### 7. Cloudflare Pages Deployment

- [ ] 7.1 Set up Cloudflare Pages
  - Connect GitHub repository to Cloudflare Pages
  - Configure build settings (output directory: output/)
  - Set up custom domain (.ke domain)
  - Enable automatic deployments on push

- [ ] 7.2 Configure Cloudflare settings
  - Enable HTTPS (automatic)
  - Configure caching rules
  - Set up analytics (free tier)
  - Test deployment

### 8. Testing & Validation

- [ ] 8.1 Test with sample data
  - Download 5 sample Hansard PDFs
  - Run full processing pipeline locally
  - Verify MP identification accuracy
  - Check statement extraction quality
  - Validate database integrity

- [ ] 8.2 Test site generation
  - Generate static site locally
  - Test all page types (MP profiles, homepage, listings)
  - Verify search functionality
  - Test on mobile devices
  - Check page load times

- [ ] 8.3 Test parliamentary term tracking
  - Verify current term data displays correctly
  - Test historical term display (if data available)
  - Test term filtering on MP profiles
  - Verify search index includes term data

- [ ] 8.4 End-to-end testing
  - Run complete workflow from scraping to deployment
  - Verify GitHub Actions workflow
  - Test Cloudflare Pages deployment
  - Check live site functionality

## Phase 4: Data Processing & Launch (Week 4)

### 9. Historical Data Processing

- [ ] 9.1 Process 2024-2025 Hansard data
  - Download all available 2024-2025 PDFs
  - Run batch processing script
  - Monitor for errors and edge cases
  - Validate data quality (spot checks)

- [ ] 9.2 Process 2022-2023 Hansard data (optional)
  - Download 2022-2023 PDFs if available
  - Process in batches
  - Link to 13th Parliament term
  - Validate historical data

- [ ] 9.3 Data quality assurance
  - Review MP attribution accuracy (target >90%)
  - Check for duplicate statements
  - Verify bill references extracted correctly
  - Spot-check random statements against source PDFs

### 10. Launch Preparation

- [ ] 10.1 Create documentation
  - Write user guide (how to use the site)
  - Document data sources and methodology
  - Create FAQ page
  - Add disclaimers and legal notices

- [ ] 10.2 Add analytics and monitoring
  - Set up Cloudflare Analytics
  - Configure GitHub Actions monitoring
  - Create manual spot-check checklist

- [ ] 10.3 Final testing and polish
  - Cross-browser testing (Chrome, Safari, Firefox)
  - Mobile device testing (iOS, Android)
  - Performance testing (page load times)
  - Accessibility testing (basic WCAG compliance)

- [ ] 10.4 Launch!
  - Deploy to production
  - Announce on social media
  - Share with journalists and researchers
  - Monitor for issues

## Phase 5: Post-Launch (Optional Enhancements)

### 11. Optional: AI-Generated Cartoons

- [ ]* 11.1 Set up Imagen API
  - Create Google Cloud account
  - Enable Imagen API
  - Set up authentication
  - Implement budget limits

- [ ]* 11.2 Implement cartoon generation
  - Create quote selection logic (manual initially)
  - Generate cartoon prompts
  - Call Imagen API
  - Store generated images
  - Add to site

### 12. Monitoring & Maintenance

- [ ] 12.1 Weekly monitoring routine
  - Check GitHub Actions workflow status
  - Review processing logs for errors
  - Spot-check new data quality
  - Monitor site performance

- [ ] 12.2 Monthly maintenance
  - Review MP data for changes (new MPs, party switches)
  - Update MP photos if needed
  - Check for new Hansard format changes
  - Update dependencies

## Success Criteria

**Technical Metrics**:
- ✅ All 349 MPs have profiles
- ✅ Processing completes in <30 minutes
- ✅ Page load time <2 seconds on 3G
- ✅ Search response time <100ms
- ✅ MP attribution accuracy >90%
- ✅ Monthly costs <£30

**Business Metrics**:
- 🎯 1,000+ unique visitors/month
- 🎯 2+ pages per session
- 🎯 60%+ mobile traffic
- 🎯 5+ media mentions

## Notes

- Tasks marked with `*` are optional and can be deferred
- Focus on core functionality first (MP profiles, search, weekly updates)
- Test thoroughly with sample data before processing all historical data
- Keep it simple - avoid premature optimization
- Document everything for future maintainers
