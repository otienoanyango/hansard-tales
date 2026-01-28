# Hansard Tales: Complete System Specification

## Overview

This directory contains the complete product specification for Hansard Tales, a comprehensive parliamentary accountability platform for Kenya. The system tracks and analyzes all parliamentary activities from both the National Assembly and Senate.

**Status**: Clean slate design (MVP complete, this is full product roadmap)

**Timeline**: 6 months (24 weeks) across 5 phases

**Total Estimated Cost**: 
- Development: ~$50
- Production (Year 1): $84-144/year (self-hosted) or $360-600/year (AWS-based)

## Document Structure

```
./
├── README.md (this file)
├── MASTER_ARCHITECTURE.md (complete system architecture)
│
├── phase-0-foundation/
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
│
├── phase-1-core-analysis/
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
│
├── phase-2-extended-documents/
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
│
├── phase-3-senate-integration/
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
│
├── phase-4-trackers-reports/
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
│
└── phase-5-advanced-features/
    ├── requirements.md
    ├── design.md
    └── tasks.md
```

## Implementation Phases

### Phase 0: Foundation (Weeks 1-2)
**Goal**: Set up core infrastructure and data models

**Key Deliverables**:
- PostgreSQL/SQLite database schema
- Qdrant/ChromaDB vector database
- Document data models
- Basic scrapers (Hansard + Votes)
- CI/CD pipeline
- Development environment

**Document Types**: None (infrastructure only)

**Cost**: $0 (local development)

**Status**: 📝 Spec in progress

---

### Phase 1: Core Analysis Pipeline (Weeks 3-6)
**Goal**: Process Hansard and Votes with AI-powered analysis

**Key Deliverables**:
- Statement classifier (filler detection)
- Sentiment analyzer (LLM + RAG)
- Citation verifier (anti-hallucination)
- Quality scorer
- Topic classifier
- Basic MP profiles
- Static site generation

**Document Types**: 
- ✅ Hansard (National Assembly)
- ✅ Votes & Proceedings (National Assembly)

**Cost**: ~$20/month (LLM API + hosting)

**Status**: 📋 Spec pending

---

### Phase 2: Extended Documents (Weeks 7-10)
**Goal**: Add Bills, Questions, Petitions with cross-document correlation

**Key Deliverables**:
- Bill version tracking
- Bill-statement correlation
- Question-Answer pairing
- Petition categorization
- Enhanced MP profiles with Q&A activity
- Bill tracking pages

**Document Types**: 
- ✅ Bills (National Assembly)
- ✅ Questions (National Assembly)
- ✅ Petitions (National Assembly)

**Cost**: ~$30/month (increased LLM usage)

**Status**: 📋 Spec pending

---

### Phase 3: Senate Integration (Weeks 11-14)
**Goal**: Duplicate all functionality for Senate chamber

**Key Deliverables**:
- Senate document scrapers
- Senator profiles
- Bicameral bill tracking
- Joint committee tracking
- Senate-specific pages

**Document Types**: 
- ✅ All Phase 1-2 documents for Senate
- ✅ Hansard (Senate)
- ✅ Votes & Proceedings (Senate)
- ✅ Bills (Senate)
- ✅ Questions (Senate)
- ✅ Petitions (Senate)

**Cost**: ~$50/month (doubled processing)

**Status**: 📋 Spec pending

---

### Phase 4: Trackers and Reports (Weeks 15-18)
**Goal**: Add tracker documents and audit reports

**Key Deliverables**:
- Statements Tracker processing
- Motions Tracker processing
- Bills Tracker processing
- Legislative Proposals tracking
- Auditor General Report analysis
- Order Paper parsing
- Constituency representation tracking

**Document Types**: 
- ✅ Statements Tracker (both chambers)
- ✅ Motions Tracker (both chambers)
- ✅ Bills Tracker (both chambers)
- ✅ Legislative Proposals (both chambers)
- ✅ Auditor General Reports
- ✅ Order Papers (both chambers)

**Cost**: ~$60/month (full system operational)

**Status**: 📋 Spec pending

---

### Phase 5: Advanced Features (Weeks 19-24)
**Goal**: Add content features, optimizations, and API

**Key Deliverables**:
- "This Week in Parliament" generator
- "This Day in History" generator
- Party position analysis
- Performance optimizations
- API layer (optional)
- Advanced search
- Data export features

**Document Types**: All (analysis and presentation)

**Cost**: ~$60/month (stable)

**Status**: 📋 Spec pending

---

## Architectural Decisions Summary

All architectural decisions are documented in MASTER_ARCHITECTURE.md. Key decisions:

| Component | Decision | Cost | Rationale |
|-----------|----------|------|-----------|
| **Structured DB** | PostgreSQL (prod), SQLite (dev) | $0-30/month | ACID, JSON support, scalable |
| **Vector DB** | Qdrant (prod), ChromaDB (dev) | $0 | Fast, self-hosted, production-ready |
| **Embeddings** | sentence-transformers (local) | $0 | Good quality, no API costs |
| **LLM** | Claude 3.5 Haiku | $5-10/month | Best cost/quality balance |
| **Processing** | GitHub Actions → Lambda | $0-10/month | Simple, scalable, cost-effective |
| **Hosting** | Cloudflare Pages | $0 | Free, fast CDN, unlimited bandwidth |
| **Monitoring** | Prometheus + Grafana + Sentry | $0 | Self-hosted, free tier sufficient |
| **CI/CD** | GitHub Actions | $0 | Integrated, free for public repos |

**Total Monthly Cost**: $7-12/month (minimal) or $30-50/month (AWS-based)

## Document Types Coverage

### National Assembly (11 document types)
1. ✅ Hansard - Daily parliamentary debates
2. ✅ Votes & Proceedings - Voting records
3. ✅ Bills - Legislation in progress
4. ✅ Questions - MP questions to government
5. ✅ Petitions - Public petitions to parliament
6. ✅ Statements Tracker - Constituency representation
7. ✅ Motions Tracker - Motion status tracking
8. ✅ Bills Tracker - Bill progress tracking
9. ✅ Order Papers - Parliamentary agenda
10. ✅ Legislative Proposals - Proposed legislation
11. ✅ Auditor General Reports - Financial audits

### Senate (11 document types)
Same as National Assembly, for Senate chamber.

**Total**: 22 document types across both chambers

## Key Features

### Core Analysis
- ✅ Statement classification (filler vs substantive)
- ✅ Sentiment analysis (support/oppose/neutral)
- ✅ Quality scoring (0-100)
- ✅ Topic classification
- ✅ Citation verification (anti-hallucination)
- ✅ Multi-session context (RAG)

### Cross-Document Correlation
- ✅ Bill ↔ Statement correlation
- ✅ Bill ↔ Vote correlation
- ✅ Bill ↔ Question correlation
- ✅ Bill ↔ Petition correlation
- ✅ MP ↔ All activities correlation

### Profiles and Pages
- ✅ MP/Senator profiles
- ✅ Party pages
- ✅ Bill tracking pages
- ✅ Session day pages
- ✅ Weekly summaries
- ✅ Historical pages

### Anti-Hallucination Measures
- ✅ Structured LLM output with citations
- ✅ Citation verification (≥90% similarity)
- ✅ No content generation (only classification)
- ✅ Immutable source references
- ✅ Audit logs for all LLM decisions
- ✅ Human review queue

## Technology Stack

### Backend
- **Language**: Python 3.12+
- **Web Framework**: FastAPI (optional API layer)
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Task Queue**: None (scheduled processing)

### Databases
- **Structured**: PostgreSQL (prod), SQLite (dev)
- **Vector**: Qdrant (prod), ChromaDB (dev)

### AI/ML
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: Claude 3.5 Haiku (Anthropic API)
- **NLP**: spaCy (for rule-based tasks)

### Infrastructure
- **Compute**: GitHub Actions, AWS Lambda (optional)
- **Storage**: S3 (optional), local filesystem
- **Hosting**: Cloudflare Pages
- **Monitoring**: Prometheus, Grafana, Sentry
- **CI/CD**: GitHub Actions

### Frontend
- **Static Site**: HTML, CSS, JavaScript
- **Templating**: Jinja2
- **Search**: Lunr.js (client-side)

## Development Workflow

### Setup
```bash
# Clone repository
git clone https://github.com/yourusername/hansard-tales.git
cd hansard-tales

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start infrastructure
docker-compose up -d

# Run migrations
alembic upgrade head

# Run tests
pytest --cov=hansard_tales --cov-report=term
```

### Common Commands
```bash
# Run tests
make test

# Run linting
make lint

# Run type checking
make typecheck

# Generate static site
make generate

# Deploy
make deploy

# Run scrapers
make scrape

# Process documents
make process
```

## Testing Strategy

### Test Types
1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component interactions
3. **Property Tests**: Test universal properties (Hypothesis)
4. **End-to-End Tests**: Test complete workflows

### Coverage Requirements
- Overall: ≥90%
- New code: ≥90%
- Critical paths: 100%

### Property-Based Testing
- Minimum 100 iterations per property
- Use Hypothesis for generating test data
- Test all correctness properties from design docs

## Deployment

### Development
```bash
# Local development
docker-compose up -d
python -m hansard_tales.main
```

### Staging
```bash
# Deploy to staging
git push origin staging
# GitHub Actions automatically deploys
```

### Production
```bash
# Deploy to production
git push origin main
# GitHub Actions automatically deploys after tests pass
```

## Monitoring

### Metrics
- Documents processed per day
- Processing time per document
- Error rate
- LLM API usage
- Storage usage

### Alerts
- Processing failures
- High error rate (>5%)
- LLM API errors
- Storage capacity warnings

### Dashboards
- System overview (Grafana)
- Processing pipeline (Grafana)
- Error tracking (Sentry)
- Uptime monitoring (Uptime Robot)

## Contributing

See CONTRIBUTING.md for:
- Development workflow
- Code style guide
- Testing requirements
- Pull request process

## License

[Your chosen license]

## Contact

[Your contact information]

---

## Next Steps

1. **Review MASTER_ARCHITECTURE.md** for complete system design
2. **Review phase-0-foundation/** for infrastructure setup
3. **Start implementation** following phase order
4. **Track progress** using GitHub Projects or similar

Each phase builds on the previous, so follow the order:
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

