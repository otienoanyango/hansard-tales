# Hansard Tales: Complete System Architecture

## Executive Summary

This document defines the complete architecture for Hansard Tales, a comprehensive parliamentary accountability platform that tracks and analyzes all parliamentary activities from both the National Assembly and Senate of Kenya. The system processes multiple document types, performs AI-powered analysis with anti-hallucination measures, and generates an accessible static website for citizens, journalists, and researchers.

**Scope**: Complete product from clean slate (MVP is complete, this is the full product roadmap)

**Document Types Covered**:
- National Assembly: Hansard, Votes & Proceedings, Bills, Order Papers, Legislative Proposals, Petitions, Questions, Statements, Motions, Auditor General Reports
- Senate: All of the above for Senate chamber

**Key Capabilities**:
- Multi-session bill tracking with full context
- AI-powered statement analysis with citation verification
- Cross-document correlation (votes ↔ statements ↔ bills ↔ questions)
- MP/Senator performance tracking
- Party position analysis
- Constituency representation tracking

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Data Collection Layer                         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐      │
│  │  Hansard   │ │   Votes    │ │   Bills    │ │  Questions │ ...  │
│  │  Scraper   │ │  Scraper   │ │  Scraper   │ │  Scraper   │      │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘      │
└────────┼──────────────┼──────────────┼──────────────┼──────────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Document Processing Layer                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  PDF Parsing → Text Extraction → Entity Recognition         │  │
│  │  → Embedding Generation → Metadata Extraction               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Storage Layer                                │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐   │
│  │  PostgreSQL/SQLite       │  │  ChromaDB/Qdrant             │   │
│  │  • Structured metadata   │  │  • Full document text        │   │
│  │  • MP/Senator profiles   │  │  • Semantic embeddings       │   │
│  │  • Votes, attendance     │  │  • Multi-session context     │   │
│  │  • Analysis results      │  │  • Cross-doc correlation     │   │
│  └──────────────────────────┘  └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Analysis Pipeline                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Statement   │  │  Context     │  │  LLM         │             │
│  │  Classifier  │  │  Retriever   │  │  Analyzer    │             │
│  │  (spaCy)     │  │  (RAG)       │  │  (Claude)    │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                  │                  │                      │
│  ┌──────┴──────────────────┴──────────────────┴──────────────┐    │
│  │  Citation Verifier → Quality Scorer → Topic Classifier    │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Static Site Generation                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  MP/Senator  │  │  Party       │  │  Bill        │             │
│  │  Profiles    │  │  Pages       │  │  Tracking    │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Deployment Layer                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  S3/Netlify (Static Site) + CloudFront/CDN                   │  │
│  │  Lambda/EC2 (Processing) + CloudWatch/Prometheus (Monitoring)│  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Document Types and Data Model

### National Assembly Documents

| Document Type | Update Frequency | Avg Size | Processing Complexity | Priority |
|--------------|------------------|----------|----------------------|----------|
| Hansard | Daily (sitting days) | 50-200 pages | High (NLP, entity extraction) | P0 |
| Votes & Proceedings | Per vote | 5-20 pages | Medium (structured data) | P0 |
| Bills | Per bill lifecycle | 10-100 pages | High (version tracking) | P0 |
| Questions | Daily (sitting days) | 20-50 pages | Medium (Q&A pairing) | P1 |
| Petitions | Weekly | 5-30 pages | Medium (categorization) | P1 |
| Statements Tracker | Weekly | 10-20 pages | Low (tabular data) | P1 |
| Motions Tracker | Weekly | 10-20 pages | Low (tabular data) | P1 |
| Bills Tracker | Weekly | 5-15 pages | Low (status tracking) | P1 |
| Order Papers | Daily (sitting days) | 10-30 pages | Low (agenda parsing) | P2 |
| Legislative Proposals | Per proposal | 10-50 pages | Medium (proposal tracking) | P2 |
| Auditor General Reports | Quarterly/Annually | 100-500 pages | High (financial analysis) | P2 |

### Senate Documents

Same document types as National Assembly, with similar characteristics.

### Unified Data Model

```python
@dataclass
class Document:
    """Base document model for all parliamentary documents"""
    id: str
    type: DocumentType  # hansard, bill, vote, question, petition, etc.
    chamber: Chamber  # national_assembly, senate
    title: str
    date: date
    session_id: str
    parliament_term: int
    
    # Source tracking (anti-hallucination)
    source_url: str
    source_hash: str  # SHA256 of original PDF
    download_date: datetime
    
    # Vector DB reference
    vector_doc_id: str
    
    # Metadata (JSON, varies by document type)
    metadata: dict

@dataclass
class Statement:
    """Parliamentary statement (from Hansard)"""
    id: str
    document_id: str  # Reference to parent Hansard document
    mp_id: str
    text: str
    timestamp: datetime
    
    # Source references (immutable)
    source_pdf_url: str
    source_pdf_hash: str
    page_number: int
    line_number: int
    
    # Vector DB reference
    vector_doc_id: str
    
    # Analysis results (populated by pipeline)
    classification: Optional[str]  # filler, substantive
    sentiment: Optional[str]  # support, oppose, neutral
    quality_score: Optional[float]  # 0-100
    topics: List[str]
    related_bills: List[str]
    related_questions: List[str]

@dataclass
class Bill:
    """Parliamentary bill"""
    id: str
    bill_number: str
    title: str
    chamber: Chamber
    status: BillStatus  # introduced, first_reading, second_reading, etc.
    
    # Version tracking
    versions: List[BillVersion]
    amendments: List[Amendment]
    
    # Source tracking
    source_urls: List[str]  # One per version
    source_hashes: List[str]
    
    # Vector DB references (one per version)
    vector_doc_ids: List[str]
    
    # Related documents
    related_statements: List[str]
    related_votes: List[str]
    related_questions: List[str]
    related_petitions: List[str]
    
    # Analysis
    topics: List[str]
    sponsor_id: str
    co_sponsors: List[str]

@dataclass
class Vote:
    """Parliamentary vote record"""
    id: str
    bill_id: str
    vote_date: date
    chamber: Chamber
    vote_type: str  # division, voice, etc.
    
    # Individual votes
    votes: List[MPVote]  # [(mp_id, direction)]
    
    # Results
    ayes: int
    noes: int
    abstentions: int
    result: str  # passed, failed

@dataclass
class Question:
    """Parliamentary question"""
    id: str
    question_number: str
    asker_id: str  # MP/Senator who asked
    respondent_id: str  # Minister/official who responded
    question_text: str
    answer_text: Optional[str]
    question_date: date
    answer_date: Optional[date]
    chamber: Chamber
    
    # Categorization
    question_type: str  # oral, written
    ministry: str
    topics: List[str]
    
    # Source tracking
    source_url: str
    source_hash: str
    vector_doc_id: str

@dataclass
class Petition:
    """Public petition to parliament"""
    id: str
    petition_number: str
    title: str
    petitioner: str
    sponsor_id: str  # MP/Senator who sponsored
    submission_date: date
    chamber: Chamber
    
    # Content
    petition_text: str
    prayer: str  # What petitioners are asking for
    
    # Status tracking
    status: str  # submitted, committee_review, response_pending, etc.
    committee: Optional[str]
    response: Optional[str]
    
    # Categorization
    topics: List[str]
    
    # Source tracking
    source_url: str
    source_hash: str
    vector_doc_id: str
```

## Architectural Decision Records (ADRs)

### ADR-001: Database Selection (Structured Data)

**Decision**: Use PostgreSQL for production, SQLite for development

**Context**:
- Need ACID transactions for data integrity
- Need complex queries across multiple tables
- Need full-text search capabilities
- Solo developer needs simple local development

**Options Considered**:

| Option | Pros | Cons | Cost |
|--------|------|------|------|
| **PostgreSQL** | ACID, JSON support, full-text search, mature, scalable | Requires server management | AWS RDS: $15-30/month (t3.micro)<br>Self-hosted: $0 (on existing server) |
| **SQLite** | Zero config, file-based, perfect for dev, fast for reads | No concurrent writes, limited scalability | $0 |
| **MySQL** | Mature, widely used, good performance | Less feature-rich than PostgreSQL | AWS RDS: $15-30/month |
| **MongoDB** | Flexible schema, good for documents | No ACID, overkill for structured data | Atlas: $0-57/month |

**Decision Rationale**:
- PostgreSQL offers best balance of features and cost
- SQLite perfect for development and testing
- Can start with SQLite, migrate to PostgreSQL when needed
- PostgreSQL JSON support handles variable metadata well

**Cost Analysis**:
- **AWS RDS PostgreSQL**: $15-30/month (t3.micro, 20GB storage)
- **Self-hosted PostgreSQL**: $0 (on existing EC2/VPS)
- **Managed alternatives**: DigitalOcean ($15/month), Supabase (free tier available)

**Recommendation**: Start with SQLite, migrate to self-hosted PostgreSQL on existing infrastructure when concurrent access needed.

### ADR-002: Vector Database Selection

**Decision**: Use Qdrant (self-hosted) for production, ChromaDB for development

**Context**:
- Need semantic search across 50k+ documents
- Need to store full document text with embeddings
- Need metadata filtering (date, chamber, document type)
- Need persistence and backup
- Cost-conscious (avoid API fees)

**Options Considered**:

| Option | Pros | Cons | Cost |
|--------|------|------|------|
| **Qdrant** | Fast, Rust-based, production-ready, good docs, REST API | Requires server | Self-hosted: $0<br>Cloud: $25+/month |
| **ChromaDB** | Python-native, simple API, good for dev | Less mature, slower at scale | Self-hosted: $0 |
| **Weaviate** | Feature-rich, good scaling, GraphQL API | Complex setup, heavier resource usage | Self-hosted: $0<br>Cloud: $25+/month |
| **Pinecone** | Managed, fast, good docs | Expensive, vendor lock-in | $70+/month |
| **Milvus** | Scalable, feature-rich, open-source | Complex setup, overkill for our scale | Self-hosted: $0 |

**Decision Rationale**:
- Qdrant offers best performance/simplicity balance
- Self-hosted = $0 cost
- ChromaDB perfect for development (Python-native)
- Can run Qdrant in Docker on same server as app

**Storage Requirements**:
- 50k documents × 10KB avg = 500MB text
- 50k documents × 1536 dims × 4 bytes = 300MB embeddings
- Total: ~1GB with metadata

**Cost Analysis**:
- **Self-hosted Qdrant**: $0 (runs on existing server, ~1GB RAM, ~2GB disk)
- **Qdrant Cloud**: $25/month (starter tier)
- **Pinecone**: $70/month (1M vectors)

**Recommendation**: Self-host Qdrant in Docker. Estimated resource usage: 1GB RAM, 2GB disk, negligible CPU.

### ADR-003: Embedding Model Selection

**Decision**: Use sentence-transformers (all-MiniLM-L6-v2) locally

**Context**:
- Need to generate embeddings for semantic search
- Want to avoid API costs
- Need reasonable quality for parliamentary text
- Solo developer needs simple deployment

**Options Considered**:

| Option | Dims | Quality | Speed | Cost |
|--------|------|---------|-------|------|
| **all-MiniLM-L6-v2** | 384 | Good | Fast | $0 (local) |
| **all-mpnet-base-v2** | 768 | Better | Medium | $0 (local) |
| **OpenAI text-embedding-3-small** | 1536 | Best | API call | $0.02/1M tokens (~$100/year) |
| **Cohere embed-english-v3.0** | 1024 | Best | API call | $0.10/1M tokens (~$500/year) |

**Decision Rationale**:
- all-MiniLM-L6-v2 offers 80% of quality at 0% of cost
- Fast enough for batch processing (1000 docs/minute on CPU)
- No API dependencies = more reliable
- Can upgrade to larger model if needed

**Performance Benchmarks**:
- Embedding generation: ~1ms per document (CPU)
- 50k documents: ~50 seconds total
- Model size: 80MB (easily cached)

**Cost Analysis**:
- **Local (sentence-transformers)**: $0
- **OpenAI API**: ~$100/year (50k docs × 500 tokens avg × $0.02/1M)
- **Cohere API**: ~$500/year

**Recommendation**: Use all-MiniLM-L6-v2 locally. Can upgrade to all-mpnet-base-v2 if quality insufficient.

### ADR-004: LLM Selection for Analysis

**Decision**: Use Claude 3.5 Haiku via API

**Context**:
- Need sentiment analysis with context understanding
- Need quality scoring with nuance detection
- Need citation generation for verification
- Want to avoid hallucination
- Cost-conscious but quality-critical

**Options Considered**:

| Option | Context | Quality | Cost (20k statements) | Latency |
|--------|---------|---------|----------------------|---------|
| **Claude 3.5 Haiku** | 200K tokens | Excellent | $50-80/year | ~1s |
| **GPT-4o-mini** | 128K tokens | Excellent | $60-100/year | ~1s |
| **Llama 3.1 8B (local)** | 128K tokens | Good | $0 (local) | ~5s (CPU) |
| **Mistral 7B (local)** | 32K tokens | Good | $0 (local) | ~5s (CPU) |

**Decision Rationale**:
- Claude 3.5 Haiku best balance of cost/quality/speed
- API = no infrastructure management
- 200K context window handles multi-session analysis
- Structured output support for citation verification
- Cost is negligible (~$5/month)

**Cost Breakdown** (20k statements/year):
- Average prompt: 2000 tokens (context) + 500 tokens (statement) = 2500 tokens
- Average response: 200 tokens (structured JSON)
- Total: 20k × (2500 input + 200 output) = 50M input + 4M output tokens
- Claude 3.5 Haiku: $0.25/M input + $1.25/M output = $12.50 + $5 = **$17.50/year**
- With retries/errors: ~$50-80/year

**Recommendation**: Use Claude 3.5 Haiku. Can switch to GPT-4o-mini if needed. Local LLMs not worth the quality/speed trade-off at this scale.

### ADR-005: Processing Infrastructure

**Decision**: Use AWS Lambda for scheduled processing, EC2 for on-demand

**Context**:
- Need to process documents daily (scheduled)
- Need to reprocess historical data (on-demand)
- Want to minimize costs
- Solo developer needs simple operations

**Options Considered**:

| Option | Pros | Cons | Cost (monthly) |
|--------|------|------|----------------|
| **Lambda (scheduled)** | No server management, pay per use, auto-scaling | 15min timeout, cold starts | $5-10 (daily runs) |
| **EC2 t3.micro** | No timeout, full control, persistent | Always-on cost, manual scaling | $7.50 (reserved) |
| **EC2 Spot** | Very cheap, good for batch | Can be terminated, complex setup | $2-3 |
| **GitHub Actions** | Free for public repos, simple CI/CD | 6hr timeout, limited resources | $0 (public repo) |
| **Local cron** | Free, full control | Requires always-on machine, no redundancy | $0 |

**Decision Rationale**:
- Lambda perfect for daily scheduled processing (< 15min)
- EC2 Spot for historical reprocessing (hours-long jobs)
- GitHub Actions for CI/CD and light processing
- Can run locally for development

**Cost Analysis** (daily processing):
- **Lambda**: 30 runs/month × 10 min × 2GB = 600 GB-min = $10/month
- **EC2 t3.micro**: $7.50/month (reserved) + $0 (idle most of time)
- **GitHub Actions**: $0 (public repo, 2000 min/month free)

**Recommendation**: 
- Phase 1-2: GitHub Actions (free, simple)
- Phase 3+: Lambda for scheduled, EC2 Spot for batch reprocessing

### ADR-006: Static Site Hosting

**Decision**: Use Cloudflare Pages (free tier)

**Context**:
- Need to host static HTML/CSS/JS
- Need global CDN for fast access
- Need SSL/HTTPS
- Want zero cost if possible

**Options Considered**:

| Option | Pros | Cons | Cost |
|--------|------|------|------|
| **Cloudflare Pages** | Free, fast CDN, auto SSL, Git integration | 500 builds/month limit | $0 |
| **Netlify** | Free tier, great DX, auto SSL | 100GB bandwidth/month limit | $0 (free tier) |
| **GitHub Pages** | Free, simple, Git integration | No server-side, slower CDN | $0 |
| **S3 + CloudFront** | Scalable, full control | Complex setup, costs add up | $10-15/month |
| **Vercel** | Free tier, fast, great DX | Vendor lock-in | $0 (free tier) |

**Decision Rationale**:
- Cloudflare Pages offers best free tier
- Unlimited bandwidth (unlike Netlify)
- Fast global CDN
- Simple Git-based deployment
- Can upgrade to paid if needed

**Cost Analysis**:
- **Cloudflare Pages**: $0 (free tier: unlimited bandwidth, 500 builds/month)
- **Netlify**: $0 (free tier: 100GB bandwidth/month)
- **S3 + CloudFront**: $10-15/month (10GB storage + 100GB transfer)

**Recommendation**: Cloudflare Pages. Zero cost, excellent performance.

### ADR-007: Monitoring and Observability

**Decision**: Use Prometheus + Grafana (self-hosted) + Sentry (free tier)

**Context**:
- Need to monitor processing pipeline
- Need to track errors and performance
- Need alerting for failures
- Want to minimize costs

**Options Considered**:

| Option | Pros | Cons | Cost |
|--------|------|------|------|
| **Prometheus + Grafana** | Free, powerful, self-hosted | Requires setup, storage | $0 (self-hosted) |
| **CloudWatch** | Integrated with AWS, simple | Expensive at scale, limited free tier | $10-30/month |
| **Datadog** | Feature-rich, great UX | Expensive | $15+/month |
| **Sentry** | Excellent error tracking | Limited free tier | $0 (free: 5k events/month) |
| **Uptime Robot** | Simple uptime monitoring | Limited features | $0 (free: 50 monitors) |

**Decision Rationale**:
- Prometheus + Grafana for metrics (self-hosted = free)
- Sentry for error tracking (free tier sufficient)
- Uptime Robot for simple uptime checks
- Can run Prometheus on same server as app

**Cost Analysis**:
- **Self-hosted (Prometheus + Grafana)**: $0 (runs on existing server, ~500MB RAM)
- **CloudWatch**: $10-30/month (custom metrics + logs)
- **Datadog**: $15/month (infrastructure monitoring)
- **Sentry**: $0 (free tier: 5k events/month)

**Recommendation**: Self-host Prometheus + Grafana, use Sentry free tier for errors.

### ADR-008: CI/CD Pipeline

**Decision**: Use GitHub Actions

**Context**:
- Need automated testing on every commit
- Need automated deployment on merge to main
- Need to run property-based tests
- Want simple setup

**Options Considered**:

| Option | Pros | Cons | Cost |
|--------|------|------|------|
| **GitHub Actions** | Free for public repos, integrated, simple | 2000 min/month limit (public) | $0 (public repo) |
| **GitLab CI** | Free, powerful, self-hosted option | More complex setup | $0 (free tier) |
| **CircleCI** | Fast, good caching | Limited free tier | $0 (free: 6k min/month) |
| **Jenkins** | Free, self-hosted, very flexible | Complex setup, maintenance burden | $0 (self-hosted) |

**Decision Rationale**:
- GitHub Actions perfect for open-source project
- 2000 minutes/month sufficient for our needs
- Simple YAML configuration
- Integrated with GitHub (no external service)

**Cost Analysis**:
- **GitHub Actions**: $0 (public repo: 2000 min/month free)
- **Self-hosted runner**: $0 (can run on existing server if needed)

**Recommendation**: GitHub Actions. Zero cost, simple, sufficient.

## Implementation Phases

### Phase 0: Foundation (Weeks 1-2)

**Goal**: Set up core infrastructure and data models

**Deliverables**:
- Database schema (PostgreSQL/SQLite)
- Vector database setup (Qdrant/ChromaDB)
- Document data models
- Basic scrapers for Hansard + Votes
- CI/CD pipeline

**Cost**: $0 (all local development)

### Phase 1: Core Analysis Pipeline (Weeks 3-6)

**Goal**: Process Hansard and Votes with basic analysis

**Deliverables**:
- Statement classifier (filler detection)
- Sentiment analyzer (LLM-based with RAG)
- Citation verifier (anti-hallucination)
- Quality scorer
- Topic classifier
- Basic MP profiles

**Document Types**: Hansard, Votes & Proceedings (National Assembly only)

**Cost**: ~$20/month (LLM API + hosting)

### Phase 2: Extended Documents (Weeks 7-10)

**Goal**: Add Bills, Questions, Petitions

**Deliverables**:
- Bill version tracking
- Question-Answer pairing
- Petition categorization
- Cross-document correlation
- Enhanced MP profiles with Q&A activity

**Document Types**: + Bills, Questions, Petitions (National Assembly)

**Cost**: ~$30/month (increased LLM usage)

### Phase 3: Senate Integration (Weeks 11-14)

**Goal**: Duplicate all functionality for Senate

**Deliverables**:
- Senate document scrapers
- Senator profiles
- Bicameral bill tracking
- Joint committee tracking

**Document Types**: All Phase 1-2 documents for Senate

**Cost**: ~$50/month (doubled processing)

### Phase 4: Trackers and Reports (Weeks 15-18)

**Goal**: Add tracker documents and audit reports

**Deliverables**:
- Statements Tracker processing
- Motions Tracker processing
- Bills Tracker processing
- Legislative Proposals tracking
- Auditor General Report analysis
- Order Paper parsing

**Document Types**: + All tracker documents, AG reports, Order Papers

**Cost**: ~$60/month (full system operational)

### Phase 5: Advanced Features (Weeks 19-24)

**Goal**: Add content features and optimizations

**Deliverables**:
- "This Week in Parliament" generator
- "This Day in History" generator
- Party position analysis
- Constituency representation tracking
- Performance optimizations
- API layer (optional)

**Cost**: ~$60/month (stable)

## Total Cost Analysis

### Development Phase (6 months)

| Component | Cost |
|-----------|------|
| Development machine | $0 (existing) |
| Cloud services | $0 (local dev) |
| LLM API (testing) | ~$50 total |
| **Total** | **~$50** |

### Production (Monthly)

| Component | Option | Cost |
|-----------|--------|------|
| **Compute** | GitHub Actions (free tier) | $0 |
| | Lambda (if needed) | $5-10 |
| **Database** | Self-hosted PostgreSQL | $0 |
| | AWS RDS (if needed) | $15-30 |
| **Vector DB** | Self-hosted Qdrant | $0 |
| **Embeddings** | Local (sentence-transformers) | $0 |
| **LLM API** | Claude 3.5 Haiku | $5-10 |
| **Static Hosting** | Cloudflare Pages | $0 |
| **Monitoring** | Self-hosted Prometheus + Grafana | $0 |
| | Sentry (free tier) | $0 |
| **CDN** | Cloudflare (free tier) | $0 |
| **Domain** | .ke domain | $2 |
| **Server** | VPS (if self-hosting) | $5-10 |
| **Total (minimal)** | | **$7-12/month** |
| **Total (AWS-based)** | | **$30-50/month** |

### Annual Cost Comparison

| Scenario | Year 1 | Year 2+ |
|----------|--------|---------|
| **Minimal (self-hosted)** | $50 (dev) + $84-144 (prod) = **$134-194** | **$84-144** |
| **AWS-based** | $50 (dev) + $360-600 (prod) = **$410-650** | **$360-600** |

**Recommendation**: Start with minimal self-hosted setup. Migrate to AWS only if scaling requires it.

## Next Steps

This master architecture document will be broken down into phase-specific specs:

1. **Phase 0 Spec**: Foundation and infrastructure setup
2. **Phase 1 Spec**: Core analysis pipeline (Hansard + Votes)
3. **Phase 2 Spec**: Extended documents (Bills + Questions + Petitions)
4. **Phase 3 Spec**: Senate integration
5. **Phase 4 Spec**: Trackers and reports
6. **Phase 5 Spec**: Advanced features

Each phase spec will include:
- Detailed requirements
- Component designs
- Implementation tasks
- Test specifications
- Deployment procedures

