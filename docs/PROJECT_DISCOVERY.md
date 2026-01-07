# Hansard Tales - Project Discovery & Planning Document

## Project Overview
A transparency platform tracking performance of Kenyan Members of Parliament through analysis of official parliamentary records (Hansard transcripts) and Auditor-General reports. The platform aims to make political accountability accessible to ordinary citizens through data visualization and engaging content.

---

## CLIENT DECISIONS SUMMARY

### Scope & Timeline
- **Target**: All 349 current MPs with historical data back to 2022
- **Timeline**: 3 months to launch
- **Future Expansion**: Yes - Senators, Governors in later phases
- **MVP Focus**: Website informing public on MP participation levels in parliament

### Data Sources (Confirmed)
- **Hansard Transcripts**: https://www.parliament.go.ke/the-national-assembly/house-business/hansard
  - Format: PDF and YouTube video links
  - Frequency: Daily
  - Method: Web scraping (design for potential API later)
- **Auditor-General Reports**: https://www.parliament.go.ke/the-national-assembly/house-business/auditors-general-reports
  - Format: PDF
  - Method: Web scraping

### Performance Metrics (All Confirmed)
1. **Bills Sponsored** - Track legislative initiatives
2. **Debate Quality** - Analyze substantive contributions vs. heckling
3. **Attendance Rates** - Critical metric (MPs can attend briefly for allowance)
4. **Committee Participation** - Oversight responsibilities
5. **Constituency Development Fund (CDF) Usage** - From Auditor-General reports

**Ranking Approach**:
- Overall ranking across all MPs
- Per-behavior rankings
- Party comparison (primary)
- County-level comparison (secondary, for later phases)
- Note: MPs can switch parties easily; parties lack well-defined objectives

**Special Considerations**:
- Ministers are first and foremost MPs
- Constitutional requirement: Cabinet should be composed of non-MPs
- Equal treatment regardless of role (minister vs. backbencher)

### Corruption Index Criteria
**Sources** (Verified/Proven Only):
- Auditor-General reports on CDF usage (primary)
- Wealth declarations (where available and verified)
- Court cases and outcomes
- Contract awards to related entities (where verifiable)
- Failed oversight responsibilities
- Reputable news articles (they take liability)

**Risk Management**:
- Very low risk tolerance for libel/defamation
- No legal counsel available
- Stick to proven cases, not allegations
- Each data point must have source citation

### Content Features

#### Daily Cartoons
- **Creation**: AI-generated
- **Approval Process**: Email to client with options; client replies "approved" or provides revised AI prompt
- **Content Source**: Hansard transcripts analyzed by AI for out-of-the-box comments
- **Archive**: Yes, searchable like xkcd
- **Budget**: Minimal; generate multiple options daily for approval, store at ingestion

#### Weekly Infographics
- **Creation**: AI-generated
- **Equivalences** (Relatable to Kenyans):
  - Education: Schools, teachers, scholarships
  - Healthcare: Hospitals, medicine
  - Infrastructure: Roads, water systems
  - Food security: Maize bags, milk liters, eggs, kilos of sugar
- **Localization**: No regional differences (avoid tribal stereotyping)
- **Frequency**: Weekly

### User Experience

#### Primary Audience
1. Voters researching their MP (PRIMARY)
2. Journalists and researchers
3. Civil society organizations
4. International observers (SECONDARY)

#### Platform
- **Device**: Mobile-first design (most Kenyan users)
- **Language**: English (cartoons may include Swahili/Sheng elements)
- **User Accounts**: No
- **Search**: By Name and Constituency
- **Filtering**: By party, parliament period
- **Comparison**: Up to 4 MPs side-by-side
- **Hansard Search**: No advanced search needed
  - Hansard data processed and compressed
  - Archive in AWS Glacier for cost savings
  - Weekly model refinement

#### Engagement Strategy
- **Social Sharing**: Yes - watermarked for visibility
- **Monetization of Sharing**: Non-individual voters will be charged
- **Community Features**: Not initially
- **Social Media**: Post to Facebook/X/Instagram for engagement

### Technical Requirements

#### Infrastructure
- **Hosting Budget**: £1,000/month maximum
- **Operations Budget**: £200/month (mostly S3 storage and DB costs)
- **Preferred Stack**: GCP, Python, Vertex AI (open to cost-cutting alternatives)
- **Update Frequency**: Weekly (new pages generated once per week)
- **Image Quality**: Two levels (mobile and desktop)
- **Traffic**: Static pages, expect DDOS from politician cronies
- **Offline Support**: Not needed

#### Data Management
- **Update Schedule**: Weekly
- **Maintenance**: Client will handle initially
- **CMS**: Not needed
- **Archive Strategy**: AWS Glacier for processed Hansard data

### Legal & Compliance
- **Legal Counsel**: None available
- **Complaints Process**: Each quote linked to Hansard document; client reviews context for infographics/cartoons
- **Regulatory Bodies**: None identified
- **Privacy Policy**: Need to generate one
- **Political Restrictions**: Non-partisan approach; data factually correct
- **Source Attribution**: Critical - every claim must link to source

### Monetization Strategy
- **Initial Phase**: Non-profit
- **Revenue Streams**:
  - Ad revenue (need to define restrictions for non-lewd ads)
  - Copyright licensing for journalistic use
  - Future: Sell analyzed data to interested parties
- **Premium Features**: None - everything free
- **Funding**: Will seek grants/donations after prototype is live

---

## REVISED MVP ROADMAP

### Phase 1 - Foundation (Month 1)
**Core Infrastructure**
1. ✓ Set up GCP project with cost monitoring
2. ✓ Design database schema for MPs, Hansard data, metrics
3. ✓ Build web scraper for Hansard PDFs
4. ✓ Build web scraper for Auditor-General reports
5. ✓ Set up data pipeline: Scrape → Process → Store → Archive (Glacier)
6. ✓ Implement PDF text extraction and cleaning
7. ✓ Set up Vertex AI for NLP processing

**Data Processing**
1. ✓ MP attribution model (link statements to MPs)
2. ✓ Performance metrics calculation engine
3. ✓ Corruption index calculation from audit reports
4. ✓ Historical data ingestion (2022-present)

**Basic Website**
1. ✓ Static site generator setup
2. ✓ Mobile-first design system
3. ✓ Individual MP profile pages (349 pages)
4. ✓ Basic search (by name and constituency)
5. ✓ Performance metrics display

### Phase 2 - Enhanced Features (Month 2)
**Advanced Features**
1. ✓ MP comparison tool (up to 4 MPs)
2. ✓ Filter by party and parliament period
3. ✓ Ranking tables (overall and per-metric)
4. ✓ Party performance aggregations
5. ✓ Responsive image optimization (2 quality levels)

**AI Content Generation**
1. ✓ Daily cartoon generation pipeline
   - AI analysis of Hansard for ridiculous quotes
   - Generate 2-3 cartoon options
   - Email approval workflow
   - Archive system
2. ✓ Weekly infographic generation
   - Corruption cost calculators
   - Kenyan equivalences
   - Template system

**Content Management**
1. ✓ Email-based approval system
2. ✓ Cartoon archive and search
3. ✓ Social sharing with watermarks

### Phase 3 - Launch & Optimization (Month 3)
**Pre-Launch**
1. ✓ Privacy policy generation and integration
2. ✓ Source citation system for all claims
3. ✓ DDOS protection setup
4. ✓ Performance testing and optimization
5. ✓ Cost monitoring and optimization
6. ✓ Manual QA of all MP profiles

**Launch**
1. ✓ Soft launch with beta testers
2. ✓ Social media presence (Facebook/X/Instagram)
3. ✓ Press outreach to journalists
4. ✓ Monitoring and bug fixes

**Post-Launch**
1. ✓ Weekly automated updates
2. ✓ Analytics tracking
3. ✓ Ad integration (with content restrictions)
4. ✓ Grant/donation page

---

## RECOMMENDED TECHNICAL ARCHITECTURE

### Option 1: GCP Python Stack (RECOMMENDED based on your preferences)

**Frontend**
- **Framework**: Next.js (React) with Static Site Generation (SSG)
- **Styling**: Tailwind CSS (mobile-first, lightweight)
- **Hosting**: GCP Cloud Storage + Cloud CDN (static hosting)
- **Cost**: ~$50-100/month for CDN + storage

**Backend / Data Processing**
- **Language**: Python 3.11+
- **Framework**: FastAPI (for any dynamic APIs if needed)
- **Data Processing**: 
  - Pandas for data manipulation
  - BeautifulSoup4/Scrapy for web scraping
  - PyPDF2/pdfplumber for PDF extraction
  - spaCy/NLTK for NLP tasks
- **Hosting**: Cloud Functions (serverless, cost-effective)

**AI/ML**
- **Platform**: Vertex AI
  - Generative AI for cartoons (Imagen, Gemini)
  - NLP for Hansard analysis
  - Text extraction and entity recognition
- **Cost**: Pay-per-use, ~$50-150/month depending on usage

**Database**
- **Primary DB**: Cloud SQL (PostgreSQL) - structured MP data, metrics
  - Small instance: ~$50-100/month
- **Document Store**: Firestore for processed Hansard text
  - ~$20-50/month
- **Search**: Built-in PostgreSQL full-text search (cost-effective)
  - Alternative: Cloud Firestore search if needed

**Storage**
- **Active Data**: Cloud Storage Standard (~$20/TB/month)
- **Archive**: Cloud Storage Nearline/Coldline for Hansard archives
  - Nearline: $10/TB/month (monthly access)
  - Coldline: $4/TB/month (quarterly access)
  - Comparable to AWS Glacier

**Workflow Automation**
- **Orchestration**: Cloud Scheduler + Cloud Functions
  - Daily scraping triggers
  - Weekly update generation
  - Cartoon/infographic generation
- **Email**: SendGrid or Cloud Functions with Gmail API

**Estimated Monthly Costs**
- Compute (Cloud Functions): $20-50
- Cloud SQL: $50-100
- Storage (active + archive): $50-100
- CDN/Hosting: $50-100
- Vertex AI: $50-150
- Misc (networking, etc.): $30-50
- **Total**: ~£150-400/month well within budget

### Alternative: Hybrid Approach (Cost Optimization)

If costs run high, consider:
- Static site hosted on Vercel/Netlify (free tier)
- GCP only for data processing and storage
- Reduce Vertex AI usage (batch processing vs. real-time)
- Use free/open-source AI models (Stable Diffusion for cartoons)

---

## KEY TECHNICAL CHALLENGES & SOLUTIONS

### 1. PDF Processing at Scale
**Challenge**: Processing hundreds of PDF Hansard documents
**Solution**:
- Use pdfplumber or PyMuPDF (faster than PyPDF2)
- Implement OCR fallback for scanned documents (Cloud Vision API)
- Parallel processing with Cloud Functions
- Cache processed text in Firestore

### 2. MP Attribution Accuracy
**Challenge**: Correctly attributing statements to MPs in Hansard
**Solution**:
- Pattern matching for "Hon. [Name]:" indicators
- Named Entity Recognition (NER) with spaCy
- Manual verification system for controversial statements
- Confidence scoring (display only high-confidence attributions)
- Link every quote to source PDF page

### 3. YouTube Video Processing
**Challenge**: Extracting data from YouTube Hansard videos
**Solution**:
- Phase 1: Focus on PDF transcripts only
- Phase 2: Use YouTube API to extract video metadata
- Phase 3: Transcription via Google Speech-to-Text (if needed)

### 4. AI Cartoon Generation
**Challenge**: Creating relevant, non-offensive political cartoons
**Solution**:
- Use Gemini to analyze Hansard for absurd/ridiculous quotes
- Generate cartoon prompts for Imagen
- Create multiple options (2-3) for client approval
- Store rejected cartoons for future review
- Watermark system to prevent misuse

### 5. Cost Management
**Challenge**: Staying within £200/month operations budget
**Solution**:
- Weekly batch processing (not real-time)
- Aggressive caching of generated pages
- Archive old Hansard data to Coldline storage
- Use Cloud Functions (pay-per-execution)
- Monitor costs with GCP budgets and alerts
- Static site hosting (no server costs)

### 6. DDOS Protection
**Challenge**: Political opponents may attempt to take down site
**Solution**:
- Cloud CDN with built-in DDOS protection
- Cloud Armor (GCP's WAF) for advanced protection
- Rate limiting on any dynamic endpoints
- Static site = harder to DDOS
- Backup/failover strategy

### 7. Mobile Performance
**Challenge**: Fast loading on slow Kenyan mobile networks
**Solution**:
- Aggressive image optimization (WebP format, 2 quality levels)
- Lazy loading for images
- Minimal JavaScript
- Service Worker for offline caching
- CDN for fast global delivery
- Progressive Web App (PWA) for better mobile experience

### 8. Legal Risk Mitigation
**Challenge**: Avoiding defamation lawsuits
**Solution**:
- Every claim must link to official source
- Only publish verified/proven information
- Disclaimer on every page
- Fact-checking workflow before publication
- Client review for sensitive content
- Copyright attribution for news sources

---

## DATA SCHEMA OUTLINE

### MPs Table
```
- id (primary key)
- name
- constituency
- party
- current_status (active/inactive)
- elected_year
- photo_url
- contact_info
- created_at
- updated_at
```

### Hansard Records
```
- id (primary key)
- date
- session_type
- pdf_url
- youtube_url (optional)
- processed_text (full text)
- archive_url (Glacier/Coldline)
- processed_at
```

### Statements
```
- id (primary key)
- hansard_id (foreign key)
- mp_id (foreign key)
- statement_text
- page_number
- confidence_score
- context (surrounding text)
- created_at
```

### Performance Metrics
```
- id (primary key)
- mp_id (foreign key)
- period_start
- period_end
- bills_sponsored
- debate_contributions
- attendance_rate
- committee_participations
- overall_score
- updated_at
```

### Corruption Records
```
- id (primary key)
- mp_id (foreign key)
- source_type (audit_report, court_case, news_article)
- source_url
- amount (if applicable)
- description
- date_recorded
- status (alleged, proven)
```

### Cartoons
```
- id (primary key)
- date
- quote_text
- hansard_reference
- image_url
- status (pending, approved, rejected)
- created_at
- approved_at
```

### Infographics
```
- id (primary key)
- week_start_date
- title
- corruption_amount
- equivalences (JSON: schools, teachers, etc.)
- image_url
- created_at
```

---

## CONTENT POLICIES

### Ad Content Restrictions
**Prohibited**:
- Adult/explicit content
- Gambling
- Alcohol/tobacco
- Political campaign ads
- Misleading claims

**Allowed**:
- General business services
- Education/training
- Technology products
- NGO/charity promotions
- News organizations

### Social Sharing Monetization
**Free Users** (Individual voters):
- Unlimited sharing
- Watermarked content
- Attribution required

**Paid Users** (Organizations):
- News organizations
- Research institutions
- Political analysis firms
- NGOs/advocacy groups
- Licensing fee structure to be determined

---

## PRIVACY POLICY REQUIREMENTS

Must Include:
1. **Data Collection**: What data we collect (analytics only, no user accounts)
2. **Third-Party Services**: GCP, analytics, ad networks
3. **Cookies**: Usage and types
4. **User Rights**: Access, deletion (GDPR-like even if not required)
5. **Updates**: How we notify of policy changes
6. **Contact**: How to reach us with concerns
7. **Public Data**: Clarify that MP data is from public sources
8. **Copyright**: Terms of use for our content
9. **Disclaimer**: Not responsible for third-party data accuracy

---

## SUCCESS METRICS

### Launch Targets (First 3 Months)
1. **Data Coverage**
   - 100% of current MPs with profiles
   - 2022-2025 Hansard data processed
   - 50+ cartoons archived
   - 12+ infographics published

2. **User Engagement**
   - 10,000 unique visitors/month
   - 3+ pages per session
   - 40%+ mobile traffic
   - 2+ minutes average session

3. **Social Impact**
   - 10+ media mentions
   - 5,000+ social media shares
   - 3+ journalist citations
   - Viral cartoon (100K+ views)

4. **Technical Performance**
   - <3 seconds page load on mobile
   - 99.9% uptime
   - Costs under £200/month operations

### Long-Term Goals (12 Months)
- 100,000 unique visitors/month
- Self-sustaining through ads/licensing
- Grant funding secured
- Expansion to Senators data
- Partnership with 3+ media organizations

---

## RISK MITIGATION STRATEGIES

### High Risk: Legal Action
**Mitigation**:
- Only publish verified data with sources
- Prominent disclaimers on every page
- Quick-response system for corrections
- Insurance consideration (if revenue allows)
- Terms of service limiting liability

### High Risk: Political Interference
**Mitigation**:
- Host on international cloud (GCP)
- Domain registered outside Kenya
- Backup/mirror sites ready
- Document everything for transparency
- Build relationship with press freedom organizations

### High Risk: Funding Sustainability
**Mitigation**:
- Keep operational costs minimal
- Multiple revenue streams (ads, licensing, donations)
- Grant applications ready
- Transparent cost reporting
- Community of supporters

### Medium Risk: Data Access Restriction
**Mitigation**:
- Archive all source documents
- Multiple scraping methods
- Manual backup process
- Build relationships with parliament staff
- FOI requests if needed

### Medium Risk: Technical Complexity
**Mitigation**:
- Start simple, iterate
- Use managed services (less maintenance)
- Document everything
- Modular architecture (easy to replace components)
- Regular backups

---

## IMMEDIATE NEXT STEPS

### Week 1: Project Setup
1. ✓ Create GCP project and set up billing alerts
2. ✓ Design detailed database schema
3. ✓ Set up development environment
4. ✓ Create GitHub repository
5. ✓ Test data access (scrape 1 Hansard PDF, 1 Auditor-General report)

### Week 2: Data Pipeline MVP
1. ✓ Build basic Hansard PDF scraper
2. ✓ Implement PDF text extraction
3. ✓ Create MP attribution logic
4. ✓ Set up database and insert sample data
5. ✓ Test with 10 Hansard documents

### Week 3: AI Integration
1. ✓ Set up Vertex AI project
2. ✓ Test Gemini for Hansard analysis
3. ✓ Test Imagen for cartoon generation
4. ✓ Build approval workflow (email-based)
5. ✓ Generate first test cartoon

### Week 4: Frontend Foundation
1. ✓ Set up Next.js project
2. ✓ Design mobile-first components
3. ✓ Create sample MP profile page
4. ✓ Implement search functionality
5. ✓ Design comparison tool

### Weeks 5-12: Full Development
- Continue with Phase 1, 2, 3 roadmap above
- Weekly check-ins on progress
- Adjust based on learnings

---

## OPEN QUESTIONS FOR FUTURE DISCUSSION

1. **Cartoon Tone**: How satirical vs. serious should cartoons be?
2. **Ranking Algorithm**: Specific weights for each metric?
3. **Party Switching**: How to handle MPs who change parties mid-term?
4. **Data Corrections**: Process for MPs to submit corrections?
5. **Ad Network**: Google AdSense or alternatives?
6. **Equivalences**: Specific current prices for sugar, maize, etc.?
7. **Committee Data**: Where to source committee participation data?
8. **Bill Sponsorship**: How to verify which bills MPs sponsored?

---

## COMPETITIVE LANDSCAPE

### Similar Platforms (Global)
- **TheyWorkForYou (UK)**: Parliamentary monitoring
- **GovTrack (USA)**: Legislative tracking
- **Mzalendo (Kenya)**: Exists but less comprehensive

### Differentiation
- AI-generated engaging content (cartoons, infographics)
- Mobile-first for Kenyan users
- Corruption index from official audits
- Relatable cost equivalences
- Non-partisan, data-driven approach

---

## DOCUMENTATION TO GENERATE

1. ✓ Functional Requirements Document
2. ✓ Non-Functional Requirements Document  
3. ✓ Technical Architecture Diagram
4. ✓ Database Schema Documentation
5. ✓ API Documentation (if needed)
6. ✓ Deployment Guide
7. ✓ User Guide
8. ✓ Content Moderation Guidelines
9. ✓ Privacy Policy
10. ✓ Terms of Service

---

**Document Status**: v2.0 - Client Decisions Incorporated  
**Date**: January 6, 2026  
**Next Action**: Create Functional & Non-Functional Requirements Documents
