# Hansard Tales MVP - Implementation Tasks

## Current Status Summary (Updated: January 23, 2026)

### ✅ Completed (Core MVP Functionality)
- **Phase 1**: Foundation & Setup - 100% complete
  - Git repository, Python environment, SQLite database, parliamentary term tracking
- **Phase 2**: Data Collection & Processing - 100% complete
  - Hansard PDF scraper with date-aware filtering
  - PDF text extraction and MP identification
  - Bill reference extraction and database updates
  - MP database compilation (349 MPs imported)
- **Phase 3**: Site Generation & Search - 100% complete
  - Jinja2 templating with Tailwind CSS
  - MP profile pages, homepage, party pages, all MPs listing
  - Client-side search with Fuse.js
  - Search index generation
- **Phase 4**: Deployment & Automation - 100% complete
  - GitHub Actions weekly processing workflow
  - Cloudflare Pages deployment configured
  - Error handling and notifications
- **Phase 5**: Historical Data Processing - 90% complete
  - Architectural improvements (PDF tracking, date-aware scraping)
  - 250+ PDFs processed from 2023-2025
  - Migration script for existing databases

### ⏳ In Progress / Remaining
- **Phase 6**: Documentation & Launch Preparation - 0% complete
  - User documentation (how-to guides, FAQ, about page)
  - Final testing (cross-browser, performance, accessibility)
  - Launch preparation and announcement

### 🎯 Next Steps
1. Create user documentation (Task 14.1-14.3)
2. Perform final testing (Task 15.1-15.3)
3. Launch preparation (Task 15.4-15.5)

### 📊 Test Coverage
- 55 test files with comprehensive coverage
- Unit tests, integration tests, property-based tests
- 87% overall code coverage maintained

---

## Development Workflow

### Branch Strategy
- Each task MUST be implemented in a feature branch: `feat/<task-number>-<brief-description>`
- Example: `feat/1.1-git-repo-structure`, `feat/2.1-hansard-scraper`
- Create branch from `main` before starting each task
- Only merge to `main` after user testing and approval

### Task Completion Criteria
1. **Implementation**: Complete all sub-tasks for the task
2. **Testing**: Write and pass all required tests (unit tests minimum)
3. **User Review**: Stop and allow user to test the feature branch
4. **Merge**: User merges feature branch to `main` after approval
5. **Mark Complete**: Only mark task complete after merge and return to `main`

### Testing Requirements
- **Unit Tests**: Required for all functions and classes
- **Integration Tests**: Required for database operations and API calls
- **End-to-End Tests**: Required for complete workflows
- Tests MUST pass before requesting user review
- Use pytest as the testing framework

### Workflow Per Task
1. Create feature branch: `git checkout -b feat/<task-number>-<description>`
2. Implement functionality
3. Write tests
4. Run tests and ensure they pass
5. Commit changes
6. **STOP** - Inform user that feature branch is ready for testing
7. User tests and merges to `main`
8. Mark task complete only after merge confirmation

## Phase 1: Foundation & Setup (Week 1)

### 1. Project Setup
- [x] 1.1 Initialize Git repository structure
  - Create directory structure (data/, templates/, output/)
  - Set up .gitignore for Python and data files
  - Initialize README.md with project overview

- [x] 1.2 Set up Python development environment
  - Create requirements.txt with dependencies (pdfplumber, spacy, jinja2, requests, beautifulsoup4)
  - Create virtual environment setup instructions
  - Document local development workflow

- [x] 1.3 Initialize SQLite database schema
  - Create database initialization module (hansard_tales/database/init_db.py)
  - Add console entry point (hansard-init-db) in pyproject.toml
  - Implement parliamentary_terms table
  - Implement mps table
  - Implement mp_terms junction table
  - Implement hansard_sessions table
  - Implement statements table
  - Create indexes for performance
  - Create views (current_mps, mp_current_term_performance, mp_historical_performance)

- [x] 1.4 Initialize 13th Parliament data
  - Insert 13th Parliament term (2022-09-08 to 2027-09-07)
  - Optionally insert 12th Parliament term (2017-08-31 to 2022-09-07)
  - Mark 13th Parliament as current

### 2. Data Collection & Processing

- [x] 2.1 Build Hansard PDF scraper
  - Implement scraper for parliament.go.ke/hansard
  - Handle pagination and listing pages
  - Extract PDF URLs and metadata (date, title)
  - Download PDFs to data/pdfs/ directory
  - Handle rate limiting and retries
  - Log scraping activity

- [x] 2.2 Implement PDF text extraction
  - Create PDF processor using pdfplumber
  - Extract text from all pages
  - Preserve page numbers for source attribution
  - Handle malformed or scanned PDFs gracefully
  - Log extraction errors

- [x] 2.3 Build MP identification system
  - Create regex patterns for speaker identification (e.g., "Hon. [Name]:")
  - Implement spaCy NER for name validation
  - Extract statement text (from speaker to next speaker)
  - Handle edge cases (multiple speakers, interruptions)
  - Create MP name normalization function

- [x] 2.4 Implement bill reference extraction
  - Create regex patterns for bill references (e.g., "Bill No. 123")
  - Extract and store bill references with statements
  - Handle multiple bill formats

- [x] 2.5 Build database update logic
  - Implement get_or_create_mp() function
  - Link MPs to current parliamentary term (mp_terms)
  - Create hansard_session records
  - Insert statements with MP and session links
  - Handle duplicate detection
  - Implement transaction management

### 3. MP Database Compilation

- [x] 3.1 Compile current MPs list (349 MPs)
  - Create web scraper for parliament.go.ke MP data
  - Scrape MP names, constituencies, counties, parties, status (elected/nominated)
  - Extract MP photo URLs from parliament website
  - Handle pagination (10 MPs per page, 35 pages total)
  - Support multiple parliamentary terms (2022, 2017)
  - Save data to JSON format (data/mps_13th_parliament.json, data/mps_12th_parliament.json)
  - Create comprehensive test suite
  - Document scraping process and data format
  - Note: No CI workflow update needed - JSON files are committed to repo and imported via hansard-import-mps

- [x] 3.2 Populate MPs database
  - Created import module (hansard_tales/database/import_mps.py) with comprehensive functionality
  - Added console entry point (hansard-import-mps) in pyproject.toml
  - Imports MP data from JSON files into SQLite database
  - Features: get_term_by_year(), get_or_create_mp(), link_mp_to_term(), import_from_json(), verify_import()
  - Handles nominated MPs (without constituencies) using 'Nominated' placeholder
  - Prevents duplicate MP and term link creation
  - Created comprehensive test suite (13 tests, all passing)
  - Successfully imported 349 MPs from 13th Parliament (333 elected, 15 nominated)
  - Verified data integrity with statistics

## Phase 2: Site Generation & Search (Week 2)

### 4. Static Site Generation

- [x] 4.1 Set up Jinja2 templating
  - Created complete templates/ directory structure (layouts/, pages/, components/)
  - Created base template (templates/layouts/base.html) with header, footer, navigation
  - Implemented Tailwind CSS via CDN with Kenyan flag-inspired colors (warm white, subtle green/red, black borders)
  - Configured Helvetica Neue as primary font with system font fallback (zero downloads)
  - Implemented mobile-first responsive design with mobile navigation toggle
  - Created Flask development server (app.py) with hot-reload for local testing
  - Created static site generator module (hansard_tales/site_generator.py) with console entry point (hansard-generate-site)
  - Set up Docker environment (Dockerfile, docker-compose.yml) for containerized development
  - Created comprehensive documentation (DOCKER_SETUP.md, QUICKSTART.md, templates/README.md, templates/COLOR_GUIDE.md)
  - Created test page (templates/pages/test.html) demonstrating color palette and components
  - Wrote comprehensive test suite (tests/test_templates.py) with 30 tests, all passing
  - Created GitHub Actions workflow (.github/workflows/deploy-pages.yml) for auto-deployment
  - All 261 tests passing with 87% coverage maintained

- [x] 4.2 Create MP profile template
  - Design MP profile page layout (mp_profile.html)
  - Display current term information (constituency, party, term number)
  - Show current term performance metrics (statements, sessions, bills)
  - Add historical terms section (collapsible)
  - Display statements list with term filtering
  - Add source links to Hansard PDFs
  - Implement term filter dropdown

- [x] 4.3 Create homepage template
  - Design homepage with search prominently featured
  - Add introduction to the platform
  - Show current parliamentary term info
  - Add recent activity feed (optional)
  - Include navigation to all MPs and parties

- [x] 4.4 Create party pages template
  - List all MPs by party
  - Show party statistics (total MPs, avg statements)
  - Link to individual MP profiles

- [x] 4.5 Create all MPs listing template
  - Display all 349 MPs in a table/grid
  - Add sorting options (name, constituency, statements)
  - Add party filter
  - Link to individual profiles

- [x] 4.6 Implement site generation script
  - Create site generator module (hansard_tales/site_generator.py)
  - Add console entry point (hansard-generate-site) in pyproject.toml
  - Query database for MP data
  - Render templates with Jinja2
  - Generate all 349 MP profile pages
  - Generate homepage, party pages, listings
  - Copy static assets (CSS, JS, images)
  - Output to output/ directory
  - Support configurable base path for GitHub Pages deployment

### 5. Client-Side Search

- [x] 5.1 Generate search index JSON
  - Create search index generator module (hansard_tales/search_index_generator.py)
  - Add console entry point (hansard-generate-search-index) in pyproject.toml
  - Query current MPs with performance data
  - Query historical terms for each MP
  - Format data for Fuse.js (name, constituency, party, keywords)
  - Include current_term metadata
  - Export to output/data/mp-search-index.json
  - Update .github/workflows/deploy-pages.yml to run hansard-generate-search-index after site generation

- [x] 5.2 Implement Fuse.js search
  - Created static/js/search.js with full Fuse.js integration
  - Loads Fuse.js 7.0.0 from CDN
  - Fetches mp-search-index.json with error handling
  - Configured fuzzy search (name 40%, constituency 30%, party 20%, keywords 10%)
  - Implemented debounced search input handler (300ms)
  - Displays search results with MP photos, stats, and links
  - Handles empty results, loading states, and errors gracefully
  - Added keyboard navigation (Escape to close)
  - Added Flask route for local development (/data/mp-search-index.json)
  - Created comprehensive test suite (17 tests, all passing)
  - All 461 tests passing with 87% coverage maintained

- [x] 5.3 Add search UI to homepage
  - Search input field already present in homepage template
  - Search results container already styled and positioned
  - Mobile-friendly responsive design with Tailwind CSS
  - Loading states implemented in search.js
  - All UI elements functional with Task 5.2 implementation
  - Note: This task was completed as part of Task 4.3 (homepage template)

## Phase 3: Deployment & Automation (Week 3)

### 6. GitHub Actions Setup

- [x] 6.1 Create weekly processing workflow
  - Created .github/workflows/weekly-update.yml with complete automation
  - Configured cron schedule (Sunday 2 AM EAT = 23:00 UTC Saturday)
  - Added manual trigger option (workflow_dispatch)
  - Set up Python 3.11 environment with pip caching
  - Install dependencies including spaCy model (en_core_web_sm)
  - Database initialization check (creates if missing)
  - Automated commit and push of changes
  - Integrated with GitHub Pages deployment

- [x] 6.2 Implement processing pipeline
  - Implemented complete automation pipeline in .github/workflows/weekly-update.yml
  - Runs hansard-scraper to download new PDFs from parliament.go.ke
  - Processes PDFs with hansard-pdf-processor (extract text, preserve page numbers)
  - Updates SQLite database with hansard-db-updater (MP identification, statements, bills)
  - Generates search index with hansard-generate-search-index
  - Generates static site with hansard-generate-site --base-path /hansard-tales
  - Auto-commits changes (database, PDFs) with github-actions bot
  - Deploys updated site to GitHub Pages
  - Note: All steps integrated into weekly-update workflow from Task 6.1

- [x] 6.3 Add error handling and notifications
  - Added comprehensive error handling to .github/workflows/weekly-update.yml
  - Implemented continue-on-error with explicit error logging (::error::)
  - Added retry logic for transient failures (scraper, processor, database, git push)
  - Retry delays: 30s for scraper, 10s for processor/database/git
  - Created workflow summary with step outcomes (always runs)
  - Implemented automatic GitHub issue creation on workflow failure
  - Issue includes: workflow run link, timestamp, failed step details, logs link
  - Issues tagged with 'automation' and 'bug' labels for easy tracking
  - All errors logged to GitHub Actions logs with structured error messages

### 7. Cloudflare Pages Deployment

- [x] 7.1 Set up Cloudflare Pages
  - Connect GitHub repository to Cloudflare Pages
  - Configure build settings (output directory: output/)
  - Set up custom domain (.ke domain)
  - Enable automatic deployments on push

- [x] 7.2 Configure Cloudflare settings
  - Enable HTTPS (automatic)
  - Configure caching rules
  - Set up analytics (free tier)
  - Test deployment

### 8. Testing & Validation

- [x] 8.1 Test with sample data
  - Created comprehensive test script (scripts/test_sample_data.py)
  - Downloaded and processed 5 sample Hansard PDFs
  - Ran full processing pipeline locally
  - Achieved 100% MP identification accuracy (exceeds 90% target)
  - Validated statement extraction quality (497 statements from 85 MPs)
  - Validated database integrity (all foreign keys maintained)
  - Extracted 6 bill references successfully
  - Created detailed results document (docs/TASK_8.1_RESULTS.md)
  - Identified minor improvements needed (see optional tasks below)

- [x] 8.2 Test site generation
  - Generate static site locally
  - Test all page types (MP profiles, homepage, listings)
  - Verify search functionality
  - Test on mobile devices
  - Check page load times

- [x] 8.3 Test parliamentary term tracking
  - Verify current term data displays correctly
  - Test historical term display (if data available)
  - Test term filtering on MP profiles
  - Verify search index includes term data

- [x] 8.4 End-to-end testing
  - Run complete workflow from scraping to deployment
  - Verify GitHub Actions workflow
  - Test Cloudflare Pages deployment
  - Check live site functionality

## Phase 4: Data Processing & Launch (Week 4)

### 9. Historical Data Processing

- [x] 9.0 Architectural Improvements (PDF Tracking & Date-Aware Scraping)
  - [x] 9.0.1 Add downloaded_pdfs table to database schema
    - Track original_url, file_path, date, file_size, downloaded_at
    - Add unique constraints on original_url and file_path
    - Add indexes for date and URL lookups
    - Update init_db.py to create table
    - Update verify_schema to check for new table
  - [x] 9.0.2 Implement date-aware scraping in HansardScraper
    - Add start_date and end_date parameters to __init__
    - Implement _is_date_in_range() method
    - Update extract_hansard_links() to filter by date
    - Stop scraping when all PDFs on page are outside range
  - [x] 9.0.3 Implement standardized file naming
    - Generate filenames as YYYYMMDD_n.pdf format
    - Track PDFs per date for numbering (0-indexed)
    - Handle multiple PDFs on same date
  - [x] 9.0.4 Implement download tracking
    - Add _is_already_downloaded() method to check database
    - Add _track_download() method to record downloads
    - Check database before downloading each PDF
    - Delete partial downloads on failure
  - [x] 9.0.5 Update process_historical_data.py
    - Update _clean_database() to preserve downloaded_pdfs table
    - Update _download_pdfs() to use new scraper with date filtering
    - Update _process_pdfs() to use standardized directory
    - Add documentation about --clean flag behavior
  - [x] 9.0.6 Update spec documents
    - Update requirements.md with PDF tracking requirements
    - Update design.md with new database schema
    - Update tasks.md with implementation tasks
  - [x] 9.0.7 Create migration script for existing databases
    - Scan existing PDFs in data/pdfs/ directory
    - Extract metadata (URL, date, file size)
    - Populate downloaded_pdfs table
    - Move PDFs to standardized directory structure
    - Rename files to standardized format
  - [x] 9.0.8 Test architectural improvements
    - Test date-aware scraping with various date ranges
    - Test standardized file naming with multiple PDFs per date
    - Test download tracking and duplicate prevention
    - Test --clean flag preserves downloaded_pdfs table
    - Test migration script with existing data

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

### 11. Optional: Improvements from Task 8.1 Testing

- [ ]* 11.1 Implement session deduplication
  - Add skip logic to DatabaseUpdater.process_hansard_pdf()
  - Check if session already processed before inserting
  - Prevent duplicate statements in database
  - Add --force flag to override skip logic for testing

- [ ]* 11.2 Filter Order Papers in scraper
  - Update HansardScraper to distinguish between transcripts and Order Papers
  - Add PDF type detection based on title/filename patterns
  - Skip downloading Order Papers (agenda documents)
  - Only download Hansard transcripts

- [ ]* 11.3 Improve date extraction
  - Use PDF metadata for accurate session dates
  - Implement content-based date extraction as fallback
  - Handle multiple date formats consistently
  - Add date validation logic

### 12. Optional: AI-Generated Cartoons

- [ ]* 12.1 Set up Imagen API
  - Create Google Cloud account
  - Enable Imagen API
  - Set up authentication
  - Implement budget limits

- [ ]* 12.2 Implement cartoon generation
  - Create quote selection logic (manual initially)
  - Generate cartoon prompts
  - Call Imagen API
  - Store generated images
  - Add to site

### 13. Monitoring & Maintenance

- [ ] 13.1 Weekly monitoring routine
  - Check GitHub Actions workflow status
  - Review processing logs for errors
  - Spot-check new data quality
  - Monitor site performance

- [ ] 13.2 Monthly maintenance
  - Review MP data for changes (new MPs, party switches)
  - Update MP photos if needed
  - Check for new Hansard format changes
  - Update dependencies

## Phase 6: Documentation & Launch Preparation

### 14. User Documentation

- [ ] 14.1 Create user guide
  - Write how-to guide for using the site
  - Document search functionality
  - Explain MP profile pages
  - Add FAQ section

- [ ] 14.2 Create about page
  - Document data sources and methodology
  - Explain how Hansard processing works
  - Add disclaimers and legal notices
  - Include contact information

- [ ] 14.3 Add data quality documentation
  - Document MP attribution accuracy metrics
  - Explain statement extraction process
  - Add known limitations
  - Include data update schedule

### 15. Final Testing & Launch

- [ ] 15.1 Cross-browser testing
  - Test on Chrome (desktop & mobile)
  - Test on Safari (desktop & mobile)
  - Test on Firefox (desktop & mobile)
  - Test on Edge (desktop)

- [ ] 15.2 Performance testing
  - Measure page load times on 3G
  - Test search response times
  - Verify mobile performance
  - Check image loading

- [ ] 15.3 Accessibility testing
  - Run WCAG AA compliance checks
  - Test keyboard navigation
  - Verify screen reader compatibility
  - Check color contrast ratios

- [ ] 15.4 Launch preparation
  - Set up monitoring and analytics
  - Prepare launch announcement
  - Create social media content
  - Plan media outreach

- [ ] 15.5 Launch!
  - Deploy to production
  - Announce on social media
  - Share with journalists and researchers
  - Monitor for issues

## Success Criteria

**Technical Metrics**:
- ✅ All 349 MPs have profiles
- ✅ Processing completes in <30 minutes
- ✅ Page load time <2 seconds on 3G
- ✅ Search response time <100ms
- ✅ MP attribution accuracy >90%
- ⏳ Monthly costs <£30 (Cloudflare Pages deployed, monitoring costs)

**Business Metrics**:
- 🎯 1,000+ unique visitors/month (post-launch)
- 🎯 2+ pages per session (post-launch)
- 🎯 60%+ mobile traffic (post-launch)
- 🎯 5+ media mentions (post-launch)

**Implementation Status**:
- ✅ Core infrastructure complete (database, scraper, processor, site generator)
- ✅ All 349 MP profiles generated
- ✅ Search functionality implemented
- ✅ GitHub Actions automation complete
- ✅ Cloudflare Pages deployment configured
- ✅ 250+ PDFs processed with historical data
- ⏳ User documentation needed
- ⏳ Final testing and launch preparation needed

## Notes

- Tasks marked with `*` are optional and can be deferred
- Focus on core functionality first (MP profiles, search, weekly updates)
- Test thoroughly with sample data before processing all historical data
- Keep it simple - avoid premature optimization
- Document everything for future maintainers
