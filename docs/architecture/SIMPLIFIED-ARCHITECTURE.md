# Hansard Tales - Simplified Architecture

## Overview

This document describes the simplified, cost-optimized architecture for Hansard Tales MVP. This architecture prioritizes **simplicity**, **cost efficiency**, and **solo maintainability** over premature optimization.

## Architecture Diagram

```mermaid
graph TB
    subgraph "GitHub Repository (Free)"
        subgraph "Weekly Processing (GitHub Actions)"
            CRON[⏰ Cron Trigger<br/>Every Sunday 2 AM]
            SCRAPE[📥 Scrape Hansard PDFs<br/>requests + BeautifulSoup]
            EXTRACT[📄 Extract Text<br/>pdfplumber]
            PARSE[🔍 Parse & Identify<br/>regex + spaCy NER]
            UPDATE[💾 Update Database<br/>SQLite]
            INDEX[📇 Generate Search Index<br/>JSON export]
            GENERATE[🏗️ Generate Static Site<br/>Hugo or Jinja2]
            COMMIT[📤 Commit & Push<br/>Git]
        end
        
        subgraph "Data Storage (Git-versioned)"
            DB[(📊 SQLite Database<br/>hansard.db)]
            PDFS[📁 Downloaded PDFs<br/>data/pdfs/]
            OUTPUT[🌐 Static HTML<br/>output/]
        end
    end
    
    subgraph "Cloudflare Pages (Free)"
        CDN[🌍 Global CDN<br/>Auto HTTPS<br/>DDoS Protection]
        STATIC[📄 Static Website<br/>349 MP Pages<br/>Search Index<br/>Party Pages]
    end
    
    subgraph "End Users"
        MOBILE[📱 Mobile Users<br/>Primary Audience]
        DESKTOP[💻 Desktop Users<br/>Secondary]
    end
    
    CRON --> SCRAPE
    SCRAPE --> EXTRACT
    EXTRACT --> PARSE
    PARSE --> UPDATE
    UPDATE --> DB
    DB --> INDEX
    INDEX --> GENERATE
    GENERATE --> OUTPUT
    OUTPUT --> COMMIT
    COMMIT --> CDN
    CDN --> STATIC
    STATIC --> MOBILE
    STATIC --> DESKTOP
    
    classDef free fill:#90EE90
    classDef processing fill:#87CEEB
    classDef storage fill:#FFE4B5
    classDef delivery fill:#DDA0DD
    classDef users fill:#FFB6C1
    
    class CRON,SCRAPE,EXTRACT,PARSE,UPDATE,INDEX,GENERATE,COMMIT processing
    class DB,PDFS,OUTPUT storage
    class CDN,STATIC delivery
    class MOBILE,DESKTOP users
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant GHA as GitHub Actions
    participant PK as Parliament.go.ke
    participant DB as SQLite Database
    participant GIT as Git Repository
    participant CF as Cloudflare Pages
    participant USER as End User
    
    Note over GHA: Every Sunday 2 AM
    GHA->>PK: Scrape for new Hansard PDFs
    PK-->>GHA: Return PDF URLs
    GHA->>GHA: Download PDFs
    GHA->>GHA: Extract text (pdfplumber)
    GHA->>GHA: Parse MPs & statements (regex + spaCy)
    GHA->>DB: Update with new data
    DB-->>GHA: Confirm update
    GHA->>GHA: Generate search index JSON
    GHA->>GHA: Generate static HTML (Hugo/Jinja2)
    GHA->>GIT: Commit changes (data + output)
    GIT->>CF: Trigger deployment
    CF->>CF: Deploy static site to CDN
    USER->>CF: Request MP page
    CF-->>USER: Serve static HTML (fast!)
    USER->>USER: Client-side search (Fuse.js)
```

## Component Architecture

```mermaid
graph LR
    subgraph "Processing Layer (Python)"
        MAIN[main.py<br/>Orchestrator]
        SCRAPER[scraper.py<br/>PDF Download]
        EXTRACTOR[extractor.py<br/>Text Extraction]
        PARSER[parser.py<br/>MP Identification]
        GENERATOR[generator.py<br/>Site Generation]
    end
    
    subgraph "Data Layer"
        SQLITE[(SQLite<br/>hansard.db)]
        JSON[Search Index<br/>JSON]
    end
    
    subgraph "Presentation Layer"
        TEMPLATES[Jinja2 Templates<br/>or Hugo Themes]
        HTML[Static HTML<br/>349 MP Pages]
        CSS[Tailwind CSS<br/>Mobile-first]
        JS[Fuse.js<br/>Client Search]
    end
    
    MAIN --> SCRAPER
    MAIN --> EXTRACTOR
    MAIN --> PARSER
    MAIN --> GENERATOR
    
    SCRAPER --> SQLITE
    EXTRACTOR --> SQLITE
    PARSER --> SQLITE
    
    SQLITE --> JSON
    SQLITE --> GENERATOR
    
    GENERATOR --> TEMPLATES
    TEMPLATES --> HTML
    HTML --> CSS
    HTML --> JS
    
    classDef python fill:#3776AB,color:#fff
    classDef data fill:#FFA500
    classDef web fill:#61DAFB
    
    class MAIN,SCRAPER,EXTRACTOR,PARSER,GENERATOR python
    class SQLITE,JSON data
    class TEMPLATES,HTML,CSS,JS web
```

## Technology Stack

```mermaid
graph TD
    subgraph "Development"
        PYTHON[Python 3.11+<br/>Single Language]
        SPACY[spaCy<br/>NLP & NER]
        PDFPLUMBER[pdfplumber<br/>PDF Extraction]
        JINJA[Jinja2 or Hugo<br/>Static Site Gen]
    end
    
    subgraph "Data"
        SQLITE[SQLite<br/>Embedded DB]
        GIT[Git<br/>Version Control]
    end
    
    subgraph "Deployment"
        ACTIONS[GitHub Actions<br/>Free CI/CD]
        PAGES[Cloudflare Pages<br/>Free Hosting]
    end
    
    subgraph "Frontend"
        HTML5[HTML5<br/>Semantic]
        TAILWIND[Tailwind CSS<br/>Mobile-first]
        FUSE[Fuse.js<br/>Client Search]
    end
    
    PYTHON --> SPACY
    PYTHON --> PDFPLUMBER
    PYTHON --> JINJA
    PYTHON --> SQLITE
    
    SQLITE --> GIT
    GIT --> ACTIONS
    ACTIONS --> PAGES
    
    JINJA --> HTML5
    HTML5 --> TAILWIND
    HTML5 --> FUSE
    
    classDef free fill:#90EE90
    classDef python fill:#3776AB,color:#fff
    
    class ACTIONS,PAGES,FUSE,GIT free
    class PYTHON,SPACY,PDFPLUMBER,JINJA,SQLITE python
```

## Cost Breakdown

```mermaid
pie title Monthly Costs MVP
    "GitHub Actions" : 0
    "Cloudflare Pages" : 0
    "SQLite" : 0
    "Domain" : 1
    "Optional Imagen API" : 15
```

**Total: £1-16/month** (vs £150-286/month in original architecture)

## Deployment Flow

```mermaid
flowchart LR
    DEV[👨‍💻 Local Development]
    TEST[🧪 Local Testing]
    COMMIT[📝 Git Commit]
    PUSH[⬆️ Git Push]
    ACTIONS[⚙️ GitHub Actions]
    BUILD[🏗️ Build & Process]
    DEPLOY[🚀 Deploy to CF]
    LIVE[✅ Live Site]
    
    DEV --> TEST
    TEST --> COMMIT
    COMMIT --> PUSH
    PUSH --> ACTIONS
    ACTIONS --> BUILD
    BUILD --> DEPLOY
    DEPLOY --> LIVE
    
    style DEV fill:#87CEEB
    style TEST fill:#FFE4B5
    style ACTIONS fill:#90EE90
    style LIVE fill:#98FB98
```

## Search Architecture

```mermaid
graph TB
    subgraph "Build Time (GitHub Actions)"
        DB[(SQLite)]
        EXPORT[Export to JSON]
        INDEX[mp-search-index.json]
        
        DB --> EXPORT
        EXPORT --> INDEX
    end
    
    subgraph "Runtime (Client Browser)"
        USER[User Types Query]
        FUSE[Fuse.js<br/>Fuzzy Search]
        RESULTS[Display Results]
        
        USER --> FUSE
        FUSE --> RESULTS
    end
    
    INDEX -.->|Loaded once| FUSE
    
    classDef build fill:#FFE4B5
    classDef runtime fill:#87CEEB
    
    class DB,EXPORT,INDEX build
    class USER,FUSE,RESULTS runtime
```

**Key Insight**: Search happens entirely in the browser. No backend API needed!

## Database Schema

```mermaid
erDiagram
    PARLIAMENTARY_TERMS ||--o{ HANSARD_SESSIONS : contains
    PARLIAMENTARY_TERMS ||--o{ MP_TERMS : "has MPs in"
    MPS ||--o{ MP_TERMS : "serves in"
    MPS ||--o{ STATEMENTS : makes
    HANSARD_SESSIONS ||--o{ STATEMENTS : contains
    
    PARLIAMENTARY_TERMS {
        int id PK
        int term_number
        date start_date
        date end_date
        boolean is_current
        timestamp created_at
    }
    
    MPS {
        int id PK
        string name
        int first_elected_year
        string photo_url
        timestamp created_at
        timestamp updated_at
    }
    
    MP_TERMS {
        int id PK
        int mp_id FK
        int term_id FK
        string constituency
        string party
        date elected_date
        date left_date
        boolean is_current
    }
    
    HANSARD_SESSIONS {
        int id PK
        int term_id FK
        date date
        string title
        string pdf_url
        string pdf_path
        boolean processed
        timestamp created_at
    }
    
    STATEMENTS {
        int id PK
        int mp_id FK
        int session_id FK
        text text
        int page_number
        string bill_reference
        timestamp created_at
    }
```

## Comparison: Original vs Simplified

| Aspect | Original Architecture | Simplified Architecture |
|--------|----------------------|------------------------|
| **Languages** | Go + Python + Node.js | Python only |
| **Cloud Services** | GCP (7+ services) | None (GitHub + Cloudflare) |
| **Database** | Supabase/Cloud SQL | SQLite (in Git) |
| **AI/ML** | Vertex AI (Gemini + Imagen) | spaCy + optional Imagen |
| **Deployment** | Complex (Terraform, Cloud Functions) | Simple (Git push) |
| **Cost** | £150-286/month | £1-21/month |
| **Complexity** | Very High | Low |
| **Maintainability** | Requires team | Solo maintainable |
| **Development Time** | 12 weeks | 4 weeks |
| **Vendor Lock-in** | High (GCP) | None |

## Key Architectural Decisions

### 1. **Parliamentary Term Tracking**
**Decision**: Track MPs across multiple parliamentary terms with historical data

**Rationale**:
- MPs can serve multiple terms (e.g., 12th and 13th Parliament)
- Constituency and party can change between terms
- Users want to see both current and historical performance
- Enables comparison across terms

**Implementation**:
- `parliamentary_terms` table tracks each parliament (e.g., 13th: 2022-2027)
- `mp_terms` junction table links MPs to terms with term-specific data
- `hansard_sessions` linked to specific parliamentary term
- Views provide easy access to current vs historical data

**Example**:
```sql
-- Get MP's performance in current term (13th Parliament)
SELECT * FROM mp_current_term_performance WHERE name = 'John Doe';

-- Get MP's performance across all terms
SELECT * FROM mp_historical_performance WHERE name = 'John Doe';
```

### 2. **Python-Only Stack**
**Decision**: Use Python for everything (scraping, processing, site generation)

**Rationale**:
- Single language = simpler development and maintenance
- Python has excellent libraries for all our needs
- No performance issues for weekly batch processing
- Easier to find help and debug

**Trade-off**: Slightly slower PDF processing (but irrelevant for weekly batches)

### 2. **SQLite + Git**
**Decision**: Use SQLite database versioned in Git

**Rationale**:
- Zero database costs
- Version control = free backup
- Perfect for read-heavy workloads
- Can handle millions of rows
- Easy to migrate to PostgreSQL later if needed

**Trade-off**: No concurrent writes (but we only write weekly)

### 3. **Static Site Generation**
**Decision**: Generate static HTML pages, no backend API

**Rationale**:
- Fastest possible page loads
- Unlimited scalability (CDN)
- Zero hosting costs (Cloudflare Pages)
- Minimal attack surface
- Works offline

**Trade-off**: No real-time updates (but we only update weekly anyway)

### 4. **Client-Side Search**
**Decision**: Use Fuse.js for client-side search

**Rationale**:
- No backend API needed
- Instant search results
- Works offline
- Zero cost
- 349 MPs = tiny dataset (~50KB JSON)

**Trade-off**: Search index loaded on first page load (negligible)

### 5. **GitHub Actions for CI/CD**
**Decision**: Use GitHub Actions for weekly processing

**Rationale**:
- Free for public repositories (2,000 minutes/month)
- Simple YAML configuration
- Integrated with Git
- Email notifications on failure
- Can run anywhere (not cloud-specific)

**Trade-off**: 2,000 minute limit (but we only use ~25 minutes/week)

### 6. **Defer AI Until Necessary**
**Decision**: Use rule-based processing, add AI only for cartoons

**Rationale**:
- 80% of "AI" is pattern matching
- spaCy handles NER well
- Saves £100-200/month
- Can add AI later when we have training data

**Trade-off**: Less sophisticated analysis (but good enough for MVP)

## Scalability Path

```mermaid
graph LR
    MVP[MVP<br/>Static Site<br/>£1-21/month]
    PHASE2[Phase 2<br/>+ API<br/>£10-40/month]
    PHASE3[Phase 3<br/>+ Real-time<br/>£50-100/month]
    SCALE[Scale<br/>Full Cloud<br/>£150-300/month]
    
    MVP -->|Add features| PHASE2
    PHASE2 -->|Add real-time| PHASE3
    PHASE3 -->|10K+ DAU| SCALE
    
    MVP -.->|Skip if not needed| SCALE
    
    style MVP fill:#90EE90
    style PHASE2 fill:#FFE4B5
    style PHASE3 fill:#FFA500
    style SCALE fill:#FF6347
```

**Key Principle**: Don't scale until you have to. Start simple, add complexity only when users demand it.

## Security Model

```mermaid
graph TB
    subgraph "Attack Surface"
        STATIC[Static HTML<br/>No Backend]
        NOSQL[No Database Queries<br/>No SQL Injection]
        NOINPUT[No User Input<br/>No XSS]
        HTTPS[HTTPS Only<br/>Cloudflare]
    end
    
    subgraph "Data Security"
        SOURCE[Source Attribution<br/>Every Claim Linked]
        GIT[Git History<br/>Audit Trail]
        BACKUP[Automatic Backup<br/>Git Clones]
    end
    
    subgraph "DDoS Protection"
        CDN[Cloudflare CDN<br/>Built-in Protection]
        CACHE[Edge Caching<br/>Absorbs Traffic]
    end
    
    STATIC --> NOSQL
    NOSQL --> NOINPUT
    NOINPUT --> HTTPS
    
    SOURCE --> GIT
    GIT --> BACKUP
    
    CDN --> CACHE
    
    classDef secure fill:#90EE90
    class STATIC,NOSQL,NOINPUT,HTTPS,SOURCE,GIT,BACKUP,CDN,CACHE secure
```

## Monitoring & Observability

```mermaid
graph LR
    subgraph "Automated Monitoring"
        ACTIONS[GitHub Actions<br/>Workflow Status]
        EMAIL[Email Alerts<br/>On Failure]
        LOGS[Action Logs<br/>Debugging]
    end
    
    subgraph "Analytics"
        CF_ANALYTICS[Cloudflare Analytics<br/>Traffic Stats]
        GIT_INSIGHTS[GitHub Insights<br/>Repo Activity]
    end
    
    subgraph "Manual Checks"
        SPOT[Weekly Spot Checks<br/>Data Quality]
        REVIEW[Monthly Review<br/>Performance]
    end
    
    ACTIONS --> EMAIL
    ACTIONS --> LOGS
    
    CF_ANALYTICS --> REVIEW
    GIT_INSIGHTS --> REVIEW
    
    SPOT --> REVIEW
    
    classDef auto fill:#87CEEB
    classDef manual fill:#FFE4B5
    
    class ACTIONS,EMAIL,LOGS,CF_ANALYTICS,GIT_INSIGHTS auto
    class SPOT,REVIEW manual
```

## Development Workflow

```mermaid
graph TB
    LOCAL[💻 Local Development]
    TEST[🧪 Test with Sample Data]
    COMMIT[📝 Commit to Feature Branch]
    PR[🔀 Pull Request]
    REVIEW[👀 Code Review]
    MERGE[✅ Merge to Main]
    AUTO[⚙️ Auto-deploy to Production]
    
    LOCAL --> TEST
    TEST --> COMMIT
    COMMIT --> PR
    PR --> REVIEW
    REVIEW -->|Approved| MERGE
    MERGE --> AUTO
    REVIEW -->|Changes Requested| LOCAL
    
    style LOCAL fill:#87CEEB
    style TEST fill:#FFE4B5
    style AUTO fill:#90EE90
```

## Conclusion

This simplified architecture achieves the project goals with:

✅ **90% cost reduction** (£1-21/month vs £150-286/month)  
✅ **90% complexity reduction** (single language, no cloud lock-in)  
✅ **Solo maintainable** (one person can handle everything)  
✅ **Fast to ship** (4 weeks to MVP vs 12 weeks)  
✅ **Scalable when needed** (clear migration path)  

**The key insight**: Optimize for simplicity and cost, not premature scale. You can always add complexity later when users demand it.
