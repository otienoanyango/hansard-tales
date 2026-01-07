# ADR-001: Architectural Decisions for Hansard Tales Platform

## Status
**PROPOSED** - Awaiting client approval

## Date
January 6, 2026

---

## Context

Hansard Tales requires a cost-effective, performant architecture for processing large volumes of PDF documents, storing structured data, and serving a mobile-first website to Kenyan users. Key constraints:

- **Budget**: £200/month operations, £1,000/month max hosting
- **Timeline**: 3 months to launch
- **Scale**: 349 MPs, 3+ years of daily Hansard PDFs, 1000s of pages
- **Performance**: Mobile-first for slow networks
- **Maintenance**: Single maintainer (client) initially
- **Update Frequency**: Weekly batch processing (not real-time)
- **Historical Data**: Can be processed slowly over extended period

### Critical Requirements
1. Fast PDF text extraction and processing
2. **GenAI-powered semantic analysis** of all statements (context understanding, stance detection, quality assessment)
3. Cost-effective storage and compute
4. AI/ML capabilities for cartoons, NLP, and deep content analysis
5. Static site generation for low hosting costs
6. Minimal ongoing maintenance

---

## Decision Drivers

1. **PDF Processing Speed**: Hansard documents are 50-200 pages each, 1000+ documents total
2. **GenAI Processing Volume**: Every statement needs context analysis, stance detection, quality scoring (potentially 1000s of API calls per document)
3. **Cost Efficiency**: Tight budget requires pay-per-use or free-tier services
4. **Maintainability**: Single maintainer needs simple, well-documented tools
5. **AI/ML Integration**: Need generative AI for:
   - Content semantic analysis (context understanding)
   - Stance detection (pro/against bill)
   - Quality assessment (substantive vs. heckling)
   - Cartoon generation
6. **Mobile Performance**: Fast loading on slow Kenyan networks
7. **Scalability**: Start small, grow as traffic increases
8. **Development Speed**: 3-month timeline to launch

---

## ADR 1: Programming Language for Data Processing

### Options Considered

#### Option A: Python
**Pros**:
- Excellent PDF libraries (pdfplumber, PyMuPDF)
- Rich data processing ecosystem (Pandas, NumPy)
- Native AI/ML support (scikit-learn, spaCy)
- Easy to learn and maintain
- Great for prototyping

**Cons**:
- Slower execution speed than compiled languages
- Higher memory usage
- GIL (Global Interpreter Lock) limits true parallelism

**Cost Estimate**: Moderate compute costs

#### Option B: Go (Golang)
**Pros**:
- **2-10x faster than Python** for text processing
- Excellent concurrency (goroutines)
- Low memory footprint
- Fast compilation
- Good PDF libraries (unipdf, pdfcpu)
- Single binary deployment

**Cons**:
- Smaller AI/ML ecosystem
- Steeper learning curve than Python
- Less data science tooling
- Would need Python/external API for AI tasks

**Cost Estimate**: Lower compute costs (faster = less runtime)

#### Option C: Rust
**Pros**:
- **10-100x faster than Python** for I/O operations
- Extremely low memory usage
- Memory safety guarantees
- Growing PDF ecosystem (pdf-extract, lopdf)

**Cons**:
- Steep learning curve
- Longer development time
- Limited AI/ML libraries
- Harder to maintain for solo developer

**Cost Estimate**: Lowest compute costs

#### Option D: Java/Kotlin
**Pros**:
- Excellent PDF processing (Apache PDFBox, iText)
- Strong typing and reliability
- Good concurrency support
- Mature ecosystem

**Cons**:
- Verbose code
- Slower startup times (JVM)
- Higher memory usage than Go/Rust
- Heavier deployment footprint

**Cost Estimate**: Moderate-high compute costs

#### Option E: Node.js (JavaScript/TypeScript)
**Pros**:
- Same language as frontend
- Good async I/O
- PDF libraries available (pdf-parse, pdf-lib)

**Cons**:
- Slower than compiled languages
- Limited PDF processing capabilities
- Memory-intensive for large files

**Cost Estimate**: Moderate-high compute costs

### Performance Comparison (PDF Processing)

```
Processing 100-page PDF:
- Python (pdfplumber):    8-12 seconds
- Go (unipdf):           1-2 seconds   (6-10x faster)
- Rust (pdf-extract):    0.5-1 second  (10-20x faster)
- Java (PDFBox):         2-4 seconds   (3-5x faster)
- Node.js (pdf-parse):   10-15 seconds
```

### DECISION: **Hybrid Approach - Go for Data Processing + Python for AI/ML**

**Rationale**:
1. **Go for PDF Processing Pipeline**:
   - 6-10x faster than Python = 6-10x lower compute costs
   - Process historical data much faster
   - Low memory footprint = can run on smaller instances
   - Easy to deploy as serverless functions
   - Concurrent processing of multiple PDFs

2. **Python for AI/ML Tasks**:
   - Vertex AI integration
   - Gemini API for text analysis
   - Imagen API for cartoons
   - spaCy for NER (Named Entity Recognition)

3. **Communication**:
   - Go processes PDFs → saves to database
   - Python reads from database → performs AI analysis
   - Or: Go calls Python via HTTP/gRPC for AI tasks

### Cost Impact
- **Estimated Savings**: 60-80% reduction in compute costs for PDF processing
- **With Python alone**: ~$100-150/month for processing
- **With Go + Python**: ~$20-40/month for processing

---

## ADR 2: Cloud Platform

### Options Considered

#### Option A: Google Cloud Platform (GCP)
**Pros**:
- Client's preference
- Vertex AI integration (Gemini, Imagen)
- Cloud Functions (serverless, pay-per-use)
- Cloud SQL (managed PostgreSQL)
- Cloud Storage (Nearline/Coldline for archives)
- Cloud CDN (global, DDoS protection)
- Free tier: 2M Cloud Functions invocations/month

**Cons**:
- Slightly more expensive than AWS for some services
- Smaller community than AWS

**Cost Estimate**: $150-400/month

#### Option B: AWS
**Pros**:
- Largest cloud provider
- Lambda (serverless)
- S3 + Glacier (cost-effective storage)
- RDS (managed databases)
- Bedrock (AI models)
- More mature, larger community

**Cons**:
- Client mentioned GCP preference
- Slightly more complex pricing
- AI capabilities less integrated than GCP

**Cost Estimate**: $150-350/month

#### Option C: Azure
**Pros**:
- Good AI services (Azure OpenAI)
- Functions (serverless)
- Competitive pricing

**Cons**:
- Smaller in market share
- Less experience with Kenyan users
- Steeper learning curve

**Cost Estimate**: $150-400/month

#### Option D: Hybrid (Multiple Clouds)
**Pros**:
- Use best features from each
- Avoid vendor lock-in
- Cost optimization

**Cons**:
- Complexity in management
- Data transfer costs between clouds
- More maintenance overhead

**Cost Estimate**: Varies

#### Option E: Budget/Alternative Providers
**Pros**:
- DigitalOcean: Simpler, cheaper
- Hetzner: Very cost-effective
- Cloudflare: Free CDN, Pages, Workers

**Cons**:
- Limited AI/ML capabilities
- Less scalability
- Manual setup and maintenance

**Cost Estimate**: $50-150/month

### DECISION: **Hybrid GCP + Cloudflare**

**Rationale**:
1. **GCP for Core Services**:
   - Vertex AI (Gemini, Imagen) - no good alternative
   - Cloud Functions for data processing
   - Cloud SQL for structured data (or consider alternatives)
   - Cloud Storage Coldline for archives

2. **Cloudflare for Frontend**:
   - **FREE CDN** with DDoS protection
   - Cloudflare Pages for static hosting (FREE)
   - Global edge network
   - Faster than GCP CDN for static content
   - 100GB bandwidth FREE, then $0.01/GB

3. **Cost Optimization**:
   - Avoid GCP CDN costs (~$50-100/month)
   - Use Cloudflare's generous free tier
   - GCP only for compute and AI

### Cost Impact
- **GCP Alone**: $150-400/month
- **GCP + Cloudflare**: $100-300/month
- **Savings**: ~$50-100/month

---

## ADR 3: Database

### Options Considered

#### Option A: Cloud SQL (PostgreSQL)
**Pros**:
- Managed service (backups, updates)
- PostgreSQL full-text search
- Strong data integrity
- Well-known, reliable

**Cons**:
- Most expensive option (~$50-100/month)
- Fixed costs even with low usage

**Cost Estimate**: $50-100/month

#### Option B: Cloud Firestore
**Pros**:
- NoSQL, flexible schema
- Pay-per-use pricing
- Real-time capabilities
- Good full-text search
- Free tier: 1GB storage, 50K reads/day

**Cons**:
- Query limitations
- Can be expensive at scale
- Less familiar to most developers

**Cost Estimate**: $20-50/month

#### Option C: SQLite + Cloud Storage
**Pros**:
- **FREE** (no database server)
- Serverless, portable
- Fast for reads
- Simple to backup
- Good for static data

**Cons**:
- No concurrent writes (not an issue for weekly updates)
- Manual backup management
- Limited to single-instance processing

**Cost Estimate**: ~$5-10/month (storage only)

#### Option D: PlanetScale (MySQL)
**Pros**:
- Generous free tier (5GB storage, 1B row reads/month)
- Branching for development
- Automatic backups
- Pay only for overages

**Cons**:
- Vendor lock-in
- MySQL vs. PostgreSQL

**Cost Estimate**: $0-30/month

#### Option E: Supabase (PostgreSQL)
**Pros**:
- PostgreSQL with extras
- Generous free tier (500MB database, 2GB storage)
- RESTful API auto-generated
- Real-time subscriptions
- Open source

**Cons**:
- Free tier limits
- Less enterprise support

**Cost Estimate**: $0-25/month

### DECISION: **Supabase PostgreSQL (Free Tier) or SQLite for MVP**

**Rationale**:

**For MVP (First 3 Months) - SQLite**:
- **Cost**: $0 (free)
- Weekly updates = no concurrent write issues
- Simple, portable, fast
- Easy to migrate later if needed
- Perfect for 349 MPs + historical data (under 1GB)
- Can be backed up to GCP Storage

**For Growth Phase - Supabase**:
- **Free tier**: 500MB database (sufficient for our needs)
- PostgreSQL (upgrade path from SQLite)
- Auto-generated REST API
- Backups included
- Upgrade to $25/month if needed

**Migration Path**: SQLite → PostgreSQL (straightforward)

### Cost Impact
- **Cloud SQL**: $50-100/month
- **Supabase**: $0-25/month
- **Savings**: $50-75/month

---

## ADR 4: Frontend Framework & Hosting

### Options Considered

#### Option A: Next.js + Vercel
**Pros**:
- Excellent SSG (Static Site Generation)
- Great performance
- Image optimization
- Vercel free tier: Unlimited static sites

**Cons**:
- Vercel can be expensive at scale
- Vendor lock-in

**Cost Estimate**: $0-50/month

#### Option B: Next.js + Cloudflare Pages
**Pros**:
- **FREE** hosting (unlimited static sites)
- **FREE** CDN globally
- Fast edge network
- Easy deployment (Git push)
- Built-in DDoS protection

**Cons**:
- None significant

**Cost Estimate**: $0/month

#### Option C: Gatsby + Netlify
**Pros**:
- GraphQL data layer
- Plugin ecosystem
- Netlify free tier

**Cons**:
- Heavier than Next.js
- Slower build times
- GraphQL overhead

**Cost Estimate**: $0-20/month

#### Option D: Hugo (Static Site Generator)
**Pros**:
- **Extremely fast** builds (Go-based)
- No JavaScript required
- Simple templating
- Lightweight sites

**Cons**:
- Less flexible than Next.js
- Smaller ecosystem
- Limited dynamic features

**Cost Estimate**: $0/month

#### Option E: Astro
**Pros**:
- Modern, fast
- Component framework agnostic
- Excellent performance
- Partial hydration

**Cons**:
- Newer, smaller community
- Less mature

**Cost Estimate**: $0/month

### DECISION: **Next.js + Cloudflare Pages**

**Rationale**:
1. **Next.js**:
   - Industry standard for SSG
   - Excellent mobile performance
   - Image optimization built-in
   - TypeScript support
   - Large community, good documentation
   - Easy to find developers

2. **Cloudflare Pages**:
   - **Completely FREE** hosting
   - **FREE** global CDN
   - Automatic HTTPS
   - DDoS protection included
   - Git-based deployment
   - Preview deployments

3. **Alternative for Ultra-Low Budget**: Hugo + Cloudflare Pages
   - Faster builds (Go-based)
   - Simpler, more lightweight
   - Consider if Next.js build times become issue

### Cost Impact
- **FREE** for hosting and CDN
- Only pay for domain (~$12/year)

---

## ADR 5: AI/ML Platform

### Options Considered

#### Option A: Google Vertex AI (Gemini, Imagen)
**Pros**:
- Gemini for text analysis (powerful, multimodal)
- Imagen for image generation
- Integrated with GCP
- Pay-per-use pricing

**Cons**:
- Can be expensive (~$50-150/month)
- Requires careful prompt optimization

**Cost Estimate**: $50-150/month

#### Option B: OpenAI API (GPT-4, DALL-E)
**Pros**:
- Powerful models
- Good documentation
- Easy to use

**Cons**:
- Similar or higher costs
- Not integrated with GCP

**Cost Estimate**: $50-200/month

#### Option C: Open Source Models (Stable Diffusion, Llama)
**Pros**:
- **FREE** (except compute)
- Full control
- No API limits
- Can run on GCP or locally

**Cons**:
- Requires GPU ($100-300/month for instance)
- More complex setup
- Quality may be lower

**Cost Estimate**: $50-150/month (compute)

#### Option D: Hybrid (Open Source + API)
**Pros**:
- Use free models for bulk processing
- Use paid APIs for quality-critical tasks
- Cost optimization

**Cons**:
- More complexity
- Need to manage two systems

**Cost Estimate**: $20-80/month

### DECISION: **Start with Vertex AI, Optimize with Open Source Models**

**Rationale**:

**Phase 1 (MVP - Months 1-3)**:
- Use Vertex AI (Gemini + Imagen)
- Optimize prompts to reduce costs
- Generate cartoons in batches (weekly)
- Focus on functionality

**Phase 2 (Optimization - Months 4-6)**:
- Evaluate open-source alternatives
- Test Stable Diffusion for cartoons
- Test Llama 3 for text analysis
- Compare quality vs. cost

**Cost Optimization Strategies**:
1. Batch processing (weekly, not daily)
2. Cache AI-generated content
3. Generate multiple cartoon options in one batch
4. Limit Gemini to analytical tasks only
5. Use smaller models where possible

### Cost Impact
- **Initial**: $50-150/month (cartoons + limited analysis)
- **With Full Semantic Analysis**: $150-400/month (see ADR 8 for details)
- **Optimized**: $50-100/month (if move to open source models)

---

## ADR 6: Data Processing Architecture

### Options Considered

#### Option A: Monolithic Python Application
**Pros**:
- Simple to develop
- All in one language
- Easy to debug

**Cons**:
- Slower PDF processing
- Higher compute costs
- Harder to scale components independently

**Cost Estimate**: $100-150/month

#### Option B: Microservices (Go + Python)
**Pros**:
- Fast PDF processing (Go)
- Specialized AI/ML (Python)
- Scale components independently
- Lower costs per component

**Cons**:
- More complexity
- Need inter-service communication

**Cost Estimate**: $40-80/month

#### Option C: Serverless Functions
**Pros**:
- Pay only for execution time
- Auto-scaling
- No server management
- Free tier benefits

**Cons**:
- Cold start times
- Execution time limits (9 min GCP, 15 min AWS)
- State management complexity

**Cost Estimate**: $20-60/month

### DECISION: **Serverless Microservices (Cloud Functions)**

**Rationale**:

**Architecture**:
```
1. Hansard Scraper (Go Cloud Function)
   - Runs weekly
   - Downloads PDFs
   - Stores in Cloud Storage

2. PDF Processor (Go Cloud Function)
   - Triggered by new PDF
   - Extracts text
   - Stores raw text in database
   - Fast, efficient

3. MP Attribution (Python Cloud Function)
   - Reads raw text
   - Uses spaCy/NER
   - Links statements to MPs
   - Updates database

4. Metrics Calculator (Python Cloud Function)
   - Runs weekly
   - Calculates performance metrics
   - Updates MP profiles

5. Cartoon Generator (Python Cloud Function)
   - Runs weekly
   - Analyzes Hansard with Gemini
   - Generates cartoons with Imagen
   - Sends email for approval

6. Infographic Generator (Python Cloud Function)
   - Runs weekly
   - Calculates corruption costs
   - Generates infographics
   - Stores results

7. Site Builder (Node.js Cloud Function)
   - Triggered weekly
   - Generates static pages
   - Deploys to Cloudflare Pages
```

**Benefits**:
- Each function optimized for its task
- Pay only for what you use
- Easy to debug and update
- Can scale independently
- Free tier covers development

### Cost Impact
- **Estimated**: $20-60/month (mostly free tier)
- **Compared to always-on servers**: $100-200/month savings

---

## ADR 7: Data Archival Strategy

### Options Considered

#### Option A: Keep Everything Hot (Standard Storage)
**Pros**:
- Fast access
- Simple

**Cons**:
- Expensive at scale (~$20/TB/month)

**Cost Estimate**: $40-80/month

#### Option B: Tiered Storage (Hot → Cold)
**Pros**:
- Cost-effective
- Appropriate access patterns
- Can retrieve if needed

**Cons**:
- Slightly complex
- Retrieval costs if accessed

**Cost Estimate**: $10-25/month

#### Option C: Process and Delete Originals
**Pros**:
- Minimal storage costs
- Keep only processed data

**Cons**:
- Can't reprocess if algorithm improves
- Loss of source documents

**Cost Estimate**: $5-10/month

### DECISION: **Tiered Storage with Processed Data Retention**

**Rationale**:

**Storage Tiers**:
1. **Hot Storage** (Standard):
   - Current year Hansard PDFs
   - Database (MPs, metrics, recent statements)
   - Generated images (cartoons, infographics)
   - Cost: ~$20/TB/month

2. **Cold Storage** (Nearline/Coldline):
   - Historical Hansard PDFs (2022-2023)
   - Processed text archives
   - Old cartoons/infographics
   - Cost: ~$4-10/TB/month

3. **Database**:
   - Keep processed/structured data hot
   - Summary statistics
   - MP profiles
   - Recent statements (last 6 months)

**Data Lifecycle**:
```
PDF → Process → Extract Text → Store Structured Data
                   ↓
              Move PDF to Cold Storage (after 3 months)
                   ↓
              Delete original PDF (after 2 years, keep text)
```

### Cost Impact
- **All Hot Storage**: $40-80/month
- **Tiered Storage**: $10-25/month
- **Savings**: $30-55/month

---

## ADR 8: GenAI Semantic Analysis Strategy

**CRITICAL DECISION** - This is the most significant cost and architectural driver for the platform.

### The Challenge

Every MP statement in Hansard needs deep semantic analysis:
1. **Context Understanding**: What is being discussed? Which bill/motion/topic?
2. **Stance Detection**: Is the MP for or against the bill/motion?
3. **Quality Assessment**: Is this substantive contribution or just heckling/noise?

**Volume**: 
- 1000+ Hansard documents × 50-200 pages each
- 10-50 statements per page
- **Est. 500,000-1,000,000+ statements to analyze**

### Critical Trade-offs

#### Cost vs. Quality Matrix

```
High Quality + High Cost:
├─ Gemini Pro for every statement
└─ Est. $300-800/month

Medium Quality + Medium Cost:
├─ Gemini Flash for bulk analysis
├─ Gemini Pro for edge cases only
└─ Est. $100-200/month

Lower Quality + Low Cost:
├─ Open-source models (Llama 3)
├─ Rule-based heuristics
└─ Est. $20-50/month
```

### Options Considered

#### Option A: Individual Statement Analysis (Naive Approach)
**Approach**: Send each statement individually to Gemini API

**Pros**:
- Highest accuracy
- Detailed per-statement analysis
- Easy to implement

**Cons**:
- **EXTREMELY EXPENSIVE** ($300-800/month)
- Slow (1000s of API calls)
- 500K+ API calls for historical data
- Vertex AI pricing: ~$0.001-0.003 per statement

**Cost Estimate**: $300-800/month (PROHIBITIVE)

#### Option B: Batch Analysis with Context Windows
**Approach**: Group multiple statements, analyze in batches

**Pros**:
- 70-90% cost reduction vs. individual
- Still good accuracy
- Gemini can see context across statements
- Fewer API calls

**Cons**:
- More complex prompt engineering
- Need to parse batch responses
- May miss nuanced individual statements

**Cost Estimate**: $100-200/month

#### Option C: Hierarchical Analysis (Smart Filtering)
**Approach**: Multi-stage analysis with increasing sophistication

**Stages**:
1. **Rule-based Pre-filter** (FREE)
   - Identify obvious heckling (short statements, no substance)
   - Detect procedural statements (voting, adjournment)
   - Filter out ~40-60% of statements

2. **Light Analysis** (Gemini Flash - cheap)
   - Quick categorization of remaining statements
   - Basic stance detection
   - Cost: ~$0.0001 per statement

3. **Deep Analysis** (Gemini Pro - expensive)
   - Only for substantive, ambiguous statements
   - Detailed context and quality assessment
   - Cost: ~$0.003 per statement

**Pros**:
- **80-95% cost reduction** vs. naive approach
- Smart resource allocation
- Fast processing (fewer API calls)
- Maintains quality where it matters

**Cons**:
- Most complex to implement
- Need careful threshold tuning
- Risk of missing important statements

**Cost Estimate**: $50-100/month

#### Option D: Open Source Models (Local/Cloud)
**Approach**: Use Llama 3 or similar for bulk analysis

**Pros**:
- Fixed compute costs
- No per-call charges
- Full control over processing

**Cons**:
- Lower accuracy than Gemini
- Requires GPU instance ($100-200/month)
- More complex setup and maintenance
- May need Gemini for validation

**Cost Estimate**: $100-200/month (compute) + time investment

#### Option E: Hybrid (MVP → Optimize)
**Approach**: Start with Gemini, optimize over time

**Phase 1 (MVP)**:
- Use Batch Analysis (Option B)
- Accept higher costs initially
- Focus on getting it working

**Phase 2 (Optimization)**:
- Implement Hierarchical Analysis (Option C)
- Add rule-based filters
- Test open-source alternatives

**Phase 3 (Scale)**:
- Fine-tune custom model on annotated data
- Use Gemini only for edge cases
- Achieve optimal cost/quality

**Pros**:
- Pragmatic approach
- Learn from real data
- Optimize based on actual patterns

**Cons**:
- Higher initial costs
- Need to budget for optimization phase

**Cost Estimate**: 
- Month 1-3: $150-250/month
- Month 4-6: $80-150/month
- Month 7+: $50-100/month

### DECISION: **Hybrid Approach (Option E) with Hierarchical Analysis as Goal**

**Rationale**:

**Phase 1: MVP (Months 1-3) - Batch Analysis**
```python
# Pseudo-code for batch analysis
def analyze_hansard_page(statements):
    """
    Analyze 20-30 statements in one Gemini call
    """
    prompt = f"""
    Analyze these parliamentary statements:
    
    {format_statements(statements)}
    
    For each statement, provide:
    1. Context: What topic/bill is being discussed?
    2. Stance: For/Against/Neutral/Unclear
    3. Quality: Substantive/Heckling/Procedural/Empty
    4. Confidence: High/Medium/Low
    
    Return as structured JSON.
    """
    
    response = gemini_api.generate(prompt)
    return parse_response(response)
```

**Cost per Hansard Document** (100 pages):
- ~3000 statements ÷ 25 per batch = 120 API calls
- Gemini Flash: ~$0.05 per call
- **Total: ~$6 per document**
- **Monthly (20 documents)**: ~$120

**Phase 2: Optimization (Months 4-6) - Add Hierarchical Filtering**
```python
def analyze_statement_smart(statement):
    """
    Multi-stage analysis with cost optimization
    """
    # Stage 1: Rule-based filter (FREE)
    if is_obviously_empty(statement):
        return {"quality": "empty", "confidence": "high"}
    
    if is_procedural(statement):
        return {"quality": "procedural", "confidence": "high"}
    
    # Stage 2: Light analysis (cheap)
    light_result = gemini_flash.analyze_quick(statement)
    
    if light_result.confidence == "high":
        return light_result  # 80% of cases
    
    # Stage 3: Deep analysis (expensive)
    deep_result = gemini_pro.analyze_detailed(statement)
    return deep_result  # 20% of cases
```

**Estimated Cost Reduction**: 60-70%
- **Monthly**: ~$70-100

**Phase 3: Scale (Months 7+) - Custom Model**
- Fine-tune Llama 3 on 10K+ annotated statements
- Use Gemini only for validation
- **Monthly**: ~$50-70

### Implementation Strategy

#### Data Model Extension

```sql
-- Add to Statements table
CREATE TABLE statement_analysis (
    id UUID PRIMARY KEY,
    statement_id UUID REFERENCES statements(id),
    
    -- Context
    topic TEXT,
    bill_reference TEXT,
    motion_reference TEXT,
    
    -- Stance
    stance VARCHAR(20), -- for/against/neutral/unclear
    stance_confidence FLOAT,
    stance_reasoning TEXT,
    
    -- Quality
    quality_score VARCHAR(20), -- substantive/heckling/procedural/empty
    quality_confidence FLOAT,
    quality_reasoning TEXT,
    
    -- Metadata
    analyzed_at TIMESTAMP,
    model_version TEXT,
    processing_cost_usd FLOAT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_stmt_quality ON statement_analysis(quality_score);
CREATE INDEX idx_stmt_stance ON statement_analysis(stance);
```

#### Processing Pipeline

```
Weekly Batch Job:
1. PDF Extraction (Go) → Raw text
2. Statement Segmentation (Python/spaCy) → Individual statements
3. Batch Grouping → Groups of 25 statements
4. Semantic Analysis (Gemini) → Structured results
5. Database Storage → statement_analysis table
6. Metrics Aggregation → MP profiles
```

#### Prompt Optimization

**Key Strategies**:
1. **Structured Output**: Always request JSON format
2. **Examples**: Include 2-3 examples in prompt (few-shot learning)
3. **Context**: Provide session date, topic, speaker info
4. **Batch Processing**: Analyze 20-30 statements per call
5. **Caching**: Cache prompts that repeat (session context)

**Example Optimized Prompt**:
```
You are analyzing Kenyan parliamentary proceedings from {date}.

Current topic: {bill_name}

Analyze these statements and return JSON:

[Examples of 2-3 statements with expected output]

Now analyze these {n} statements:
{statements}

Return:
{
  "statements": [
    {
      "id": "1",
      "topic": "infrastructure bill",
      "stance": "for|against|neutral|unclear",
      "stance_confidence": 0-1.0,
      "quality": "substantive|heckling|procedural|empty",
      "quality_confidence": 0-1.0,
      "reasoning": "brief explanation"
    }
  ]
}
```

### Cost Monitoring & Control

#### Weekly Monitoring
- Track cost per statement analyzed
- Monitor confidence scores (low = need better prompts)
- Identify most expensive processing patterns

#### Cost Thresholds
- Alert if weekly cost > £50
- Auto-pause if monthly cost > £200
- Review and optimize if cost/statement > $0.01

#### Optimization Tactics

**Immediate** (Week 1):
1. Batch size optimization (test 10, 25, 50 statements)
2. Filter obvious non-statements (speaker names, dates)
3. Use Gemini Flash instead of Pro where possible

**Short-term** (Month 2-3):
1. Implement rule-based pre-filtering
2. Cache common session contexts
3. A/B test different prompt structures

**Long-term** (Month 4+):
1. Collect 10K+ annotations (gold standard)
2. Fine-tune open-source model
3. Use Gemini only for validation/edge cases

### Risk Mitigation

**Risk**: Costs spiral out of control
- **Mitigation**: Hard limits, weekly monitoring, pause mechanism

**Risk**: Analysis quality insufficient
- **Mitigation**: Manual validation of 100-200 random statements, confidence scoring

**Risk**: Processing too slow for historical data
- **Mitigation**: Parallel processing, start with recent data first

**Risk**: Prompt injection / adversarial inputs
- **Mitigation**: Input sanitization, output validation, confidence thresholds

---

## ADR 9: Alternative High-Quality Semantic Analysis (Advanced Option)

**NOTE**: This section explores a premium alternative that prioritizes quality over cost constraints.

### High-Quality Options Not Fully Considered

While the main ADR focused on cost-effective solutions within budget, several high-quality semantic analysis approaches were not fully explored:

#### 1. **Fine-Tuned Domain-Specific Models**
**Approach**: Custom models trained specifically on parliamentary/political discourse
- **Quality**: Potentially superior to general-purpose models (90%+ accuracy vs 70-80%)
- **Implementation**: Fine-tune Llama 3.1 70B, Mistral, or Claude on parliamentary transcripts
- **Cost**: $200-500/month (GPU compute) + $2,000-3,000 initial training
- **Timeline**: 2-4 weeks training period

#### 2. **Ensemble Methods with Consensus**
**Approach**: Multiple specialized models with voting/weighted consensus
- **Quality**: Significantly higher accuracy through disagreement resolution
- **Models**: Combine fine-tuned Llama, Claude, GPT-4 for consensus
- **Benefit**: Flag statements where models disagree for human review
- **Cost**: $300-600/month but much higher confidence scores

#### 3. **Retrieval-Augmented Generation (RAG)**
**Approach**: Augment analysis with structured knowledge about bills, MPs, voting records
- **Quality**: Much more accurate context understanding and stance prediction
- **Implementation**: Build knowledge base of all bills, MP backgrounds, voting histories
- **Enhancement**: Works with any base model for dramatic accuracy improvements
- **Cost**: $150-300/month (vector database + enhanced prompts)

#### 4. **Human-in-the-Loop (HITL) Systems**
**Approach**: Semi-automated analysis with targeted human verification
- **Quality**: Near 100% accuracy for verified statements
- **Workflow**: AI bulk analysis + humans verify edge cases and train system
- **Scalability**: Start with 10% human verification, decrease as model improves
- **Cost**: $100-200/month AI + $500-1,000/month human verification

### PREMIUM RECOMMENDATION: RAG + Fine-tuned Ensemble + HITL

For clients prioritizing maximum quality over cost, the optimal approach combines:

#### Architecture Overview
```
┌─────────────────────────────────────────────────────────┐
│                   DATA INGESTION                        │
├─────────────────────────────────────────────────────────┤
│ Hansard PDFs → Text Extraction → Statement Segmentation │
│ MP Database → Bill Database → Voting Records            │
│ News Articles → Court Cases → Audit Reports             │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  KNOWLEDGE BASE (RAG)                   │
├─────────────────────────────────────────────────────────┤
│ Vector Database (Pinecone/Weaviate)                    │
│ ├─ MP Profiles & Voting History                        │
│ ├─ Bill Summaries & Status                             │
│ ├─ Historical Statements by Topic                      │
│ ├─ Context Windows (session info, ongoing debates)     │
│ └─ Domain Knowledge (parliamentary procedures)         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                 ENSEMBLE ANALYSIS                       │
├─────────────────────────────────────────────────────────┤
│ Model 1: Fine-tuned Llama 3.1 70B (Parliamentary)     │
│ Model 2: Claude 3.5 Sonnet (General Reasoning)        │
│ Model 3: Fine-tuned Mistral 7B (Efficiency/Speed)     │
│                                                         │
│ Consensus Engine → Confidence Scoring → HITL Queue     │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              HUMAN-IN-THE-LOOP WORKFLOW                │
├─────────────────────────────────────────────────────────┤
│ High Confidence (>90%) → Auto-approve                  │
│ Medium Confidence (70-90%) → Sample review (10%)       │
│ Low Confidence (<70%) → Full human review              │
│ Disagreement between models → Expert annotation        │
└─────────────────────────────────────────────────────────┘
```

#### Implementation Stack
**Platform**: AWS (for comprehensive AI services)
- **Compute**: EKS (Kubernetes), SageMaker, ECS
- **AI Services**: Bedrock (Claude), SageMaker (custom models)
- **Storage**: S3, RDS, OpenSearch (vector database)
- **Models**: 
  - Together AI (fine-tuned Llama 70B): $200/month
  - AWS Bedrock (Claude): ~$150/month
  - SageMaker (Mistral 7B): $100/month

#### Data Pipeline
```python
# Knowledge Base Components
knowledge_base = {
    "mp_profiles": "349 current MPs + historical data",
    "bill_database": "All bills since 2010 with summaries",
    "voting_records": "How each MP voted on each bill",
    "session_contexts": "What was being discussed when",
    "domain_knowledge": "Parliamentary procedures, terminology",
    "embedding_model": "text-embedding-3-large"
}

# Training Data
training_data = {
    "kenyan_hansard": "10K manually annotated statements",
    "international_parliamentary": "2M+ statements (UK, Canada, Australia)",
    "political_datasets": "500K+ labeled political statements"
}
```

#### Quality Targets
- **Stance Detection**: 95%+ accuracy (vs 70% baseline)
- **Quality Assessment**: 90%+ accuracy (vs 65% baseline)
- **Context Understanding**: 95%+ accuracy with RAG enhancement
- **Processing Speed**: 100 statements/minute
- **Human Review**: Only 15% of statements require human input

#### Cost Structure
```python
monthly_costs = {
    "infrastructure": {
        "aws_compute": 300,
        "model_hosting": 450,
        "vector_database": 70,
        "storage_networking": 80
    },
    "ai_services": {
        "claude_api": 150,
        "embedding_api": 50,
        "fine_tuning_amortized": 100
    },
    "human_annotation": {
        "expert_annotators": 800,  # 2 part-time at $20/hour
        "quality_assurance": 200
    },
    "total_monthly": 2200,  # $2,200/month
    "per_statement_cost": 0.002  # $0.002 per statement
}
```

#### Implementation Timeline
- **Month 1**: Infrastructure setup, data collection, annotation
- **Month 2**: Model fine-tuning, RAG system development
- **Month 3**: Ensemble integration, HITL workflow
- **Month 4**: Production deployment, monitoring

### Cost vs Quality Trade-off Analysis

| Approach | Monthly Cost | Stance Accuracy | Quality Accuracy | Development Time |
|----------|-------------|-----------------|------------------|------------------|
| **GCP Batch (ADR 8)** | $150-250 | 70-75% | 65-70% | 2 months |
| **GCP Optimized** | $70-100 | 75-80% | 70-75% | 3-4 months |
| **Premium RAG+Ensemble** | $2,200 | 95%+ | 90%+ | 4 months |
| **Hybrid Approach** | $500-800 | 85-90% | 80-85% | 3 months |

### Recommended Decision Framework

**Choose GCP Batch (ADR 8) if**:
- Budget constraint is critical (£200/month)
- 70-75% accuracy is acceptable for MVP
- Quick launch is priority (3 months)

**Choose Premium RAG+Ensemble if**:
- Quality is paramount over cost
- Academic/research partnerships possible
- Long-term accuracy more important than initial budget
- Willing to invest $2,200/month for 95%+ accuracy

**Choose Hybrid Approach if**:
- Need balance between cost and quality
- Can afford $500-800/month
- Want 85-90% accuracy
- Plan to scale up quality over time

### Migration Path

If starting with GCP batch approach, migration to higher quality can be planned:

**Phase 1**: GCP Batch → Build user base and validate approach
**Phase 2**: Add RAG system → Improve accuracy to 80-85%
**Phase 3**: Add ensemble models → Reach 85-90% accuracy
**Phase 4**: Add HITL workflow → Achieve 95%+ accuracy

This staged approach allows proving the concept with budget constraints while building toward premium quality.

---

## FINAL ARCHITECTURE RECOMMENDATION (UPDATED)

### Technology Stack

```
┌─────────────────────────────────────────────────┐
│           FRONTEND (User-Facing)                │
├─────────────────────────────────────────────────┤
│ Next.js (React + TypeScript)                    │
│ - Static Site Generation (SSG)                  │
│ - Mobile-first design (Tailwind CSS)            │
│ - Hosted on Cloudflare Pages (FREE)            │
│ - Global CDN (FREE)                             │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│         DATA PROCESSING (Backend)               │
├─────────────────────────────────────────────────┤
│                                                  │
│  PDF Processing (Go Cloud Functions)            │
│  ├─ Scrape Hansard website                      │
│  ├─ Download PDFs                               │
│  ├─ Extract text (6-10x faster than Python)     │
│  └─ Store in database                           │
│                                                  │
│  AI/ML Processing (Python Cloud Functions)      │
│  ├─ MP attribution (spaCy NER)                  │
│  ├─ Metrics calculation                         │
│  ├─ Cartoon generation (Vertex AI)              │
│  └─ Infographic generation                      │
│                                                  │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│              DATA STORAGE                       │
├─────────────────────────────────────────────────┤
│                                                  │
│  Database: Supabase PostgreSQL (FREE tier)      │
│  ├─ MPs, metrics, statements                    │
│  ├─ 500MB limit (sufficient for our needs)      │
│  └─ Auto-backups included                       │
│                                                  │
│  File Storage: GCP Cloud Storage                │
│  ├─ Hot: Current year PDFs, images              │
│  ├─ Cold: Historical PDFs (Coldline)            │
│  └─ Tiered lifecycle management                 │
│                                                  │
│  AI: Vertex AI (Gemini + Imagen)                │
│  ├─ Batch processing (weekly)                   │
│  ├─ Optimized prompts                           │
│  └─ Consider open-source alternatives later     │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Cost Breakdown (Monthly) - UPDATED WITH GENAI SEMANTIC ANALYSIS

**GCP Services**:
- Cloud Functions (Go + Python): $20-40
  - Mostly free tier (2M invocations/month)
- Cloud Storage: $10-20
  - Standard: $10-15
  - Coldline: $5-10
- **Vertex AI (MAJOR COST DRIVER)**: $120-200
  - **Semantic Analysis**: $100-150/month (Phase 1: Batch processing)
    - ~20 Hansard docs/week × $6/doc = $120/month
  - Cartoons: $10-20/month (weekly generation)
  - Infographics: $10-20/month (weekly generation)
  - Optimize prompts aggressively
- **GCP Subtotal**: $150-260/month

**Third-Party Services**:
- Cloudflare Pages: $0 (FREE)
- Cloudflare CDN: $0 (FREE, up to 100GB/month)
- Supabase Database: $0-25
  - Start with free tier
  - Upgrade if needed ($25/month)
- Domain: ~$1/month (~$12/year)
- Email (SendGrid): $0 (free tier)
- **Third-Party Subtotal**: $1-26/month

**TOTAL ESTIMATED COST BY PHASE**:

**Phase 1 (Months 1-3) - MVP with Batch GenAI Analysis**:
- **$151-286/month**
- ⚠️ EXCEEDS £200/month budget by ~£50-80
- Accept higher costs initially to get system working
- MUST optimize in Phase 2

**Phase 2 (Months 4-6) - Optimized with Hierarchical Filtering**:
- **$90-180/month** (60-70% cost reduction)
- Within budget
- Rule-based pre-filtering reduces API calls
- Smart tiered analysis

**Phase 3 (Months 7+) - Fine-tuned Custom Model**:
- **$70-140/month** (optimal cost)
- Well within budget
- Custom model handles bulk processing
- Gemini only for edge cases

**CRITICAL NOTE**: GenAI semantic analysis is the #1 cost driver. Phase 1 will exceed budget, but this is necessary to build and test the system. Aggressive optimization in Phase 2 is mandatory to get within budget.

### Performance Characteristics

**PDF Processing**:
- Go: 1-2 seconds per 100-page PDF
- Can process 1000+ PDFs in a few hours
- Historical data: Process slowly over weeks (no rush)

**Website Performance**:
- Static pages: <1 second load time
- Cloudflare CDN: <500ms globally
- Mobile-optimized images: 2 quality levels

**Update Frequency**:
- Weekly batch processing
- Low compute costs (pay per execution)
- Predictable monthly costs

### Development Approach

**Phase 1: MVP (Months 1-3)**
1. Build Go PDF processor
2. Set up Supabase database
3. Create Python AI/ML pipeline
4. Generate static site with Next.js
5. Deploy to Cloudflare Pages

**Phase 2: Optimization (Months 4-6)**
1. Optimize costs (evaluate open-source AI)
2. Improve performance (caching, compression)
3. Add analytics
4. Scale up as traffic grows

**Phase 3: Growth (Months 7-12)**
1. Add senators data
2. Enhance features based on feedback
3. Implement monetization
4. Scale infrastructure as needed

---

## Consequences

### Positive

1. **Cost Efficiency**:
   - 60-80% lower than Python-only approach
   - Within budget with room for growth
   - Pay-per-use serverless = no idle costs

2. **Performance**:
   - Fast PDF processing (Go)
   - Global CDN for users (Cloudflare)
   - Mobile-optimized delivery

3. **Scalability**:
   - Serverless auto-scales
   - Static frontend handles traffic spikes
   - Can grow without major architectural changes

4. **Maintainability**:
   - Modular functions (easy to update)
   - Managed services (less operational overhead)
   - Good documentation for both Go and Python

5. **Flexibility**:
   - Can swap components as needed
   - Not locked into expensive vendors
   - Open-source friendly

### Negative

1. **Complexity**:
   - Two languages (Go + Python) vs. one
   - Need to learn Go (if not familiar)
   - More moving parts than monolith

2. **Development Time**:
   - Initially slower than pure Python
   - Need to set up inter-service communication
   - More testing complexity

3. **Debugging**:
   - Distributed system = harder to debug
   - Need good logging/monitoring
   - State management across functions

### Risks & Mitigations

**Risk**: Go learning curve
- **Mitigation**: Go is simpler than Python; excellent docs; focus on PDF processing only

**Risk**: Serverless cold starts
- **Mitigation**: Use Cloud Scheduler to keep functions warm; cold starts acceptable for weekly processing

**Risk**: Cost overruns
- **Mitigation**: Set up GCP billing alerts; monitor usage weekly; optimize aggressively

**Risk**: Vendor lock-in
- **Mitigation**: Use portable tech (PostgreSQL, standard libraries); can migrate if needed

---

## Alternative Architectures Considered

### Ultra-Budget Option: Pure Static + GitHub Actions

**Stack**:
- Hugo (static site generator)
- SQLite database
- GitHub Actions for processing (FREE)
- Cloudflare Pages for hosting (FREE)
- Local Python scripts for AI/ML

**Cost**: ~$10-30/month (AI API costs only)

**Pros**:
- Extremely cost-effective
- Simple architecture
- No cloud vendor bills

**Cons**:
- Limited AI/ML capabilities
- Slower processing (GitHub Actions limits)
- Less scalable
- More manual work

**Verdict**: Good fallback if budget becomes constrained

### High-Performance Option: Rust + PostgreSQL

**Stack**:
- Rust for all data processing
- PostgreSQL on managed service
- Next.js frontend
- Dedicated VM or container

**Cost**: ~$100-200/month

**Pros**:
- Maximum performance
- Lowest compute costs per operation
- Professional-grade architecture

**Cons**:
- Highest development time
- Steeper learning curve
- Over-engineered for initial needs

**Verdict**: Overkill for MVP; consider for v2 if scaling becomes priority

---

## Monitoring & Cost Control

### Cost Alerts
- Set GCP budget alerts at £50, £100, £150, £200
- Weekly cost reviews
- Dashboard for spending trends

### Performance Monitoring
- Cloudflare Analytics (FREE)
- GCP Cloud Logging (included)
- Custom metrics for processing times

### Optimization Opportunities
1. Move to open-source AI models (save $30-50/month)
2. Increase cold storage usage (save $20-30/month)
3. Optimize image compression (save bandwidth)
4. Implement aggressive caching

---

## Approval & Next Steps

### For Client Approval
- [ ] Review architecture decisions
- [ ] Confirm budget allocation
- [ ] Approve technology stack
- [ ] Authorize proceeding to implementation

### If Approved, Next Actions
1. Set up GCP project and billing
2. Create GitHub repository
3. Initialize Next.js project
4. Set up Supabase account
5. Write first Go Cloud Function (PDF scraper)
6. Build proof-of-concept

### Alternative Paths
- **If budget concerns**: Switch to Ultra-Budget Option
- **If Go too complex**: Stick with Python, optimize heavily
- **If time constrained**: Use ready-made solutions (Docparser, etc.)

---

**Decision Authority**: Client
**Stakeholders**: Development team (client), end users
**Review Date**: After MVP launch (Month 4)
**Status**: Awaiting approval

---

## Appendix: Quick Reference

### Language Comparison for PDF Processing
| Language | Speed    | Cost/1000 PDFs | Learning Curve | AI/ML Support |
|----------|----------|----------------|----------------|---------------|
| Python   | Baseline | $100-150       | Easy           | Excellent     |
| Go       | 6-10x    | $15-25         | Moderate       | Limited       |
| Rust     | 10-20x   | $8-15          | Hard           | Limited       |
| Java     | 3-5x     | $30-50         | Moderate       | Good          |
| Node.js  | 0.8x     | $120-180       | Easy           | Limited       |

### Platform Comparison
| Platform     | Cost (Est.) | AI/ML | Free Tier | Complexity |
|--------------|-------------|-------|-----------|------------|
| GCP          | $150-400    | ★★★★★ | Good      | Moderate   |
| AWS          | $150-350    | ★★★★☆ | Good      | Moderate   |
| Azure        | $150-400    | ★★★★☆ | Good      | Moderate   |
| Hybrid       | $100-300    | ★★★★★ | Excellent | High       |
| DigitalOcean | $50-150     | ★☆☆☆☆ | Limited   | Low        |

### Recommended Stack Summary
- **Frontend**: Next.js + Cloudflare Pages
- **PDF Processing**: Go (Cloud Functions)
- **AI/ML**: Python (Cloud Functions) + Vertex AI
- **Database**: Supabase PostgreSQL (free tier)
- **Storage**: GCP Cloud Storage (Tiered)
- **Hosting**: Cloudflare (FREE)
- **Cost**: $61-166/month

---

**Document Version**: 1.0  
**Last Updated**: January 6, 2026  
**Maintainer**: Development Team
