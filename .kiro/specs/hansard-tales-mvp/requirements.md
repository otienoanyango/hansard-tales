# Hansard Tales MVP - Requirements

## 1. Project Overview

Hansard Tales is a transparency platform tracking the performance of Kenyan Members of Parliament through analysis of official parliamentary records (Hansard transcripts) and Auditor-General reports. The platform makes political accountability accessible to ordinary citizens through data visualization and engaging content.

**Target**: All 349 current MPs with historical data back to 2022  
**Timeline**: 3 months to MVP launch  
**Primary Audience**: Kenyan voters researching their MP (mobile-first)

## 2. User Stories

### 2.1 Voter Research (Current Term)
**As a** Kenyan voter  
**I want to** view my MP's performance in the current parliament (13th: 2022-2027)  
**So that** I can make informed decisions about their current accountability

**Acceptance Criteria**:
- User can search for MP by name or constituency
- User can view MP profile with current term performance
- User can see statements from current parliamentary term
- User can see attendance and participation in current term
- All data links back to official Hansard sources

### 2.2 Historical Performance Research
**As a** researcher or journalist  
**I want to** view an MP's performance across multiple parliamentary terms  
**So that** I can analyze trends and long-term patterns

**Acceptance Criteria**:
- User can see which parliamentary terms an MP served in
- User can compare MP's performance across different terms
- User can filter statements by parliamentary term
- User can see if MP changed constituency or party between terms
- Historical data clearly labeled with term number and years

### 2.3 Content Discovery
**As a** social media user  
**I want to** discover engaging political content (cartoons, infographics)  
**So that** I can stay informed and share with my network

**Acceptance Criteria**:
- Daily AI-generated cartoons based on parliamentary quotes (optional for MVP)
- Weekly infographics showing corruption costs (Phase 2)
- Searchable cartoon archive (Phase 2)
- Social sharing with watermarks (Phase 2)
- Mobile-optimized content loading

### 2.4 Parliamentary Term Context
**As a** user  
**I want to** understand which parliamentary term I'm viewing  
**So that** I can contextualize the data appropriately

**Acceptance Criteria**:
- Clear indication of current parliamentary term (13th: 2022-2027)
- Ability to view historical terms (12th, 11th, etc.)
- Term-specific performance metrics
- Timeline showing when MP served in each term

## 3. Functional Requirements

### 3.1 Data Collection & Processing

#### 3.1.1 Hansard PDF Scraping
- Scrape parliament.go.ke/hansard for new PDF documents
- Download PDFs locally or to simple storage
- Extract text from PDFs using pdfplumber
- Process weekly in batch mode (GitHub Actions or simple cron)
- Handle rate limiting and throttling

#### 3.1.2 MP Attribution
- Identify speaker names in Hansard text using regex patterns
- Link statements to MP database
- Use spaCy NER for name entity recognition
- Store bill references when mentioned (for future use)

#### 3.1.3 Basic Statement Classification (MVP)
- Extract bill references using regex (e.g., "Bill No. 123")
- Simple rule-based stance detection (keyword matching)
- Store raw statements with metadata
- **Defer complex AI analysis to Phase 2**

### 3.2 Performance Metrics (Simplified for MVP)

#### 3.2.1 Core Metrics
- **Statement Count**: Number of times MP spoke in parliament
- **Session Attendance**: Count of sessions where MP participated
- **Bills Mentioned**: List of bills MP discussed (extracted from statements)
- **Active Periods**: Timeline of parliamentary activity

#### 3.2.2 Simple Rankings (MVP)
- Rank by statement count (most active MPs)
- Rank by session attendance
- Group by party for comparison
- **Defer**: Complex quality scoring, CDF analysis, committee tracking

### 3.3 Content Generation (Simplified)

#### 3.3.1 Weekly Cartoons (Optional for MVP)
- Manual selection of notable quotes initially
- AI generation (Imagen) if budget allows
- Simple approval workflow (email or manual)
- Archive with dates
- **Defer**: Automated AI analysis of quotes

#### 3.3.2 Basic Infographics (Phase 2)
- **Defer to Phase 2**: Corruption cost calculators
- **Defer to Phase 2**: Kenyan equivalences
- Focus MVP on core MP data

### 3.4 Website Features (MVP Focus)

#### 3.4.1 MP Profiles (349 pages)
- Photo, name, constituency, party
- **Current parliamentary term** (13th Parliament: 2022-2027)
- **Historical terms** (if MP served in previous parliaments)
- Statement count and session attendance (per term)
- List of statements with dates and links to source
- Bills mentioned (simple list)
- Social sharing functionality
- **Term filtering**: View performance by parliamentary term

#### 3.4.2 Search & Discovery (CRITICAL)
- **Search by MP name** (primary use case)
- **Search by constituency** (critical - users may not know their MP)
- Filter by party
- Client-side search using Fuse.js (no backend needed)
- Fast, fuzzy matching

#### 3.4.3 Simple Listings
- All MPs page with sorting
- Party pages with member lists
- Recent statements feed
- **Defer**: Comparison tool, advanced filtering

#### 3.4.4 Statement Display
- Show statements by MP
- Link to source Hansard PDF (page number)
- Date and session information
- Bill references if mentioned
- **Defer**: Stance indicators, quality scores

### 3.5 Mobile Experience (Simplified)

#### 3.5.1 Performance Requirements
- Page load <3 seconds on 3G networks
- Responsive design (mobile-first)
- Simple, lightweight HTML/CSS
- Minimal JavaScript (search only)

#### 3.5.2 Network Optimization
- Optimized images (WebP, compressed)
- Lazy loading for images
- Static files (fast CDN delivery)
- **Defer**: PWA features, offline functionality, service workers

## 4. Non-Functional Requirements

### 4.1 Performance
- Website loads in <3 seconds on mobile (3G)
- Support 1,000+ concurrent users (sufficient for MVP)
- 99% uptime target
- Static site = inherently fast

### 4.2 Cost Constraints (CRITICAL)
- **Target: £10-30/month maximum**
- Operations budget: £200/month absolute maximum
- Use free tiers wherever possible:
  - GitHub Actions (free for public repos)
  - Cloudflare Pages (free tier)
  - SQLite (no database costs)
- Weekly batch processing (not real-time)
- Minimize paid AI usage

### 4.3 Simplicity & Maintainability (NEW PRIORITY)
- **Single language**: Python only
- **Single maintainer**: Must be manageable by one person
- **No cloud vendor lock-in**: Can run anywhere
- **Git as backup**: Version control = free backup
- **Local development**: Can test everything locally
- Clear, simple architecture

### 4.4 Security & Legal
- Every claim must link to official source
- Only publish verified/proven information
- Prominent disclaimers on every page
- HTTPS enforcement (via Cloudflare)
- Static site = minimal attack surface

### 4.5 Scalability (Deferred)
- Start simple, optimize later
- Static site can handle significant traffic
- Can migrate to cloud services if needed
- **Don't** over-engineer for scale

## 5. Technical Constraints (Simplified)

### 5.1 Technology Stack
- **Language**: Python only (simplicity)
- **Static Site Generator**: Hugo or Jinja2 templates
- **Database**: SQLite (in Git repo)
- **Hosting**: Cloudflare Pages (free)
- **CI/CD**: GitHub Actions (free)
- **Search**: Fuse.js (client-side, free)
- **AI**: Minimal usage (cartoons only, if budget allows)

### 5.2 Data Sources
- Parliament of Kenya Hansard (PDFs)
- MP database (manual compilation initially)
- **Defer**: Auditor-General reports, YouTube videos

### 5.3 Update Frequency
- Weekly batch processing (GitHub Actions cron)
- Static pages regenerated weekly
- Manual content approval (simple email)
- **No real-time updates needed**

## 6. Success Criteria (Realistic MVP)

### 6.1 Launch Targets (First 3 Months)
- 100% of current MPs with profiles (349 MPs)
- 2024-2025 Hansard data processed (focus on recent data)
- Working search by name and constituency
- 1,000+ unique visitors/month (realistic for MVP)
- 2+ pages per session
- 60%+ mobile traffic

### 6.2 Quality Targets
- MP attribution accuracy >90% (rule-based is sufficient)
- Statement extraction accuracy >95%
- System uptime >99%
- Costs <£30/month operations (stretch: <£10/month)

### 6.3 Engagement Targets (Modest)
- 5+ media mentions
- 1,000+ social media shares
- 2+ journalist citations
- Organic growth through word-of-mouth

## 7. Out of Scope (Future Phases)

### 7.1 Not in MVP
- Complex AI semantic analysis (use simple rules)
- Auditor-General report processing
- CDF usage tracking
- Committee participation tracking
- Debate quality scoring
- Voting record analysis
- Bill-centric stance tracking (store references only)
- Comparison tools (side-by-side MPs)
- User accounts and authentication
- Advanced Hansard search
- YouTube video processing
- Real-time updates
- Mobile app (native)
- Multiple languages (English only for MVP)
- Infographics and corruption calculators
- Social media auto-posting

### 7.2 Phase 2 Features (Post-MVP)
- Bill-centric pages with MP stances
- Advanced AI analysis (if budget allows)
- Comparison tools
- Infographics with Kenyan equivalences
- Corruption index from audit reports
- Committee tracking
- Enhanced search and filtering

### 7.3 Future Expansion (Phase 3+)
- Senators data
- County government tracking
- Historical data back to 2013
- API marketplace for data licensing
- Premium features and subscriptions
- International expansion (Nigeria, Ghana, South Africa)

## 8. Risks & Mitigation

### 8.1 Political Risks
- **Risk**: Government interference or website blocking
- **Mitigation**: International hosting, multiple domains, decentralized distribution

### 8.2 Legal Risks
- **Risk**: Defamation lawsuits from MPs
- **Mitigation**: Source everything, fact-check rigorously, legal insurance

### 8.3 Technical Risks
- **Risk**: AI costs spiral out of control
- **Mitigation**: Hierarchical filtering, hard budget limits, weekly monitoring

### 8.4 Data Access Risks
- **Risk**: Parliament restricts access to Hansard
- **Mitigation**: Archive all documents, multiple scraping methods, FOI requests

## 9. Dependencies (Simplified)

### 9.1 External Services (Minimal)
- Cloudflare Pages (free tier - hosting & CDN)
- GitHub (free - code hosting & CI/CD)
- **Optional**: Imagen API for cartoons (£10-20/month)
- **No other paid services required**

### 9.2 Data Dependencies
- Parliament of Kenya website availability
- Hansard PDF format consistency
- MP database accuracy (manual compilation)

### 9.3 Team Dependencies
- Single maintainer can handle everything
- Manual content approval (simple email)
- Manual validation of MP attribution (spot checks)
- Community feedback for improvements

## 10. Compliance & Privacy

### 10.1 Privacy Requirements
- No user accounts (no personal data collection)
- Analytics only (anonymous)
- Cookie consent
- Privacy policy
- GDPR-like data protection

### 10.2 Content Policies
- Non-partisan approach
- Factually correct data only
- Source attribution required
- Transparent methodology
- Correction policy

### 10.3 Advertising Restrictions
- No adult/explicit content
- No gambling or alcohol
- No political campaign ads
- No misleading claims
- General business services only
