# Design Document: Advanced Parliamentary Analysis

## Overview

This design extends the Hansard Tales system with advanced NLP capabilities for statement analysis, enhanced MP and party profiles, voting pattern tracking, and automated content generation. The system maintains its current Python/SQLite/static site architecture while adding modular analysis pipelines that can process statements for quality, sentiment, and topic classification.

### Key Design Principles

1. **Modularity**: Analysis components are independent and can be enabled/disabled via configuration
2. **Automation-First**: All processing runs automatically with minimal manual intervention
3. **Solo Developer Friendly**: Simple deployment, clear logging, automated monitoring
4. **Cost-Conscious**: Evaluate managed services against self-hosted alternatives
5. **Future-Proof**: Architecture supports adding Senate and additional data sources

### Research Summary

**NLP Libraries**: Based on research and requirements analysis, **LLMs (Claude 3.5 Haiku or GPT-4o-mini) with RAG** emerge as the optimal choice for this system:
- Superior context understanding for parliamentary debates
- Can analyze sentiment across multiple sessions
- Handles nuance, sarcasm, and indirect speech
- Cost-effective at scale (~$50-80/year for 20k statements)
- Zero configuration needed (no keyword maintenance)

**Traditional NLP (spaCy)** will be used for:
- Filler statement detection (rule-based patterns work well)
- Topic classification (keyword-based with TF-IDF)
- Fast, deterministic processing without API costs

**Vector Database**: ChromaDB selected for RAG architecture:
- Free, open-source, runs locally
- Python-native integration
- Persistent storage (~500MB for 50k documents)
- Semantic search with embeddings
- No API costs (uses local sentence-transformers)

**Cloud Hosting**: For static site hosting, S3 + CloudFront is the clear winner for cost and performance ([fueint.com](https://fueint.com/blog/ec2-vs-lambda-vs-ecs)). For processing workloads:
- Lambda: Cost-effective for intermittent processing (daily/weekly runs)
- EC2: More economical for continuous processing or high-volume workloads
- ECS/Fargate: Best for containerized workloads requiring orchestration

**CI/CD**: GitHub Actions with Terraform provides robust IaC and deployment automation ([bomberbot.com](https://www.bomberbot.com/terraform/how-to-deploy-aws-infrastructure-with-terraform-and-github-actions-a-multi-environment-ci-cd-guide)), supporting multi-environment deployments with OIDC authentication for secure AWS access.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Collection Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Hansard    │  │   Votes &    │  │  Statements  │      │
│  │   Scraper    │  │  Proceedings │  │   Tracker    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  Document Ingestion Layer                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Extract text, generate embeddings, store metadata   │   │
│  └──────┬───────────────────────────────────────┬───────┘   │
└─────────┼───────────────────────────────────────┼───────────┘
          │                                       │
          ▼                                       ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│   SQLite (Structured)    │    │  ChromaDB (Semantic)     │
│  • MP metadata           │    │  • Full statement text   │
│  • Vote records          │    │  • Bill text & versions  │
│  • Attendance            │    │  • Questions, petitions  │
│  • Statement metadata    │    │  • Embeddings for search │
│  • Analysis results      │    │  • Source references     │
└──────────┬───────────────┘    └──────────┬───────────────┘
           │                               │
           └───────────┬───────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Pipeline                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Statement  │  │  Context     │  │    LLM       │      │
│  │  Classifier  │  │  Retriever   │  │  Analyzer    │      │
│  │  (spaCy)     │  │  (RAG)       │  │  (Claude)    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│  ┌──────┴──────────────────┴──────────────────┴───────┐    │
│  │     Citation Verifier & Quality Scorer            │    │
│  └──────────────────────────┬──────────────────────────┘    │
└─────────────────────────────┼─────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Storage Layer                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         SQLite: Analysis Results + Audit Logs        │   │
│  │  • Sentiments with citations  • Quality scores       │   │
│  │  • Source references          • Audit trail          │   │
│  └──────────────────────────┬───────────────────────────┘   │
└─────────────────────────────┼─────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Static Site Generation                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  MP Pages    │  │ Party Pages  │  │   Content    │      │
│  │  + Citations │  │  + Citations │  │   Features   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Data Collection**: Scrapers run on schedule, download new documents
2. **Document Ingestion**: Extract text, generate embeddings, store in both databases
3. **Context Retrieval**: For each statement, retrieve relevant context via semantic search
4. **LLM Analysis**: Analyze with full context, return structured output with citations
5. **Citation Verification**: Verify all citations against source documents
6. **Storage**: Store verified results with audit trail
7. **Generation**: Static site builder queries database, generates HTML with source links
8. **Deployment**: Generated site deployed to hosting (S3 + CloudFront)

## Components and Interfaces

### 0. Vector Database & RAG System

**Purpose**: Store document embeddings and enable semantic search for multi-session context

**Interface**:
```python
class VectorStore:
    def __init__(self, persist_directory: Path):
        """Initialize ChromaDB with persistence"""
        
    def add_document(self, text: str, metadata: dict, doc_id: str):
        """
        Store document with embedding
        
        Args:
            text: Full document text
            metadata: Document metadata (type, date, mp_id, bill_id, etc.)
            doc_id: Unique document identifier
        """
        
    def search(self, query: str, filters: dict, limit: int = 10) -> List[Document]:
        """
        Semantic search for relevant documents
        
        Args:
            query: Search query (can be text or embedding)
            filters: Metadata filters (bill_id, mp_id, date_range, etc.)
            limit: Maximum number of results
            
        Returns:
            List of documents with similarity scores
        """
        
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Retrieve specific document by ID"""
```

**Implementation Approach**:
- Use ChromaDB for local vector storage
- Use sentence-transformers for embeddings (free, local)
- Store full text + metadata for each document
- Support filtering by document type, date, MP, bill, etc.

**Document Types Stored**:
```python
@dataclass
class StoredDocument:
    id: str
    text: str
    type: str  # 'statement', 'bill', 'vote', 'question', 'petition'
    metadata: dict  # {mp_id, bill_id, session_id, date, etc.}
    embedding: List[float]  # Generated by sentence-transformers
```

### 0.1 Context Retriever

**Purpose**: Retrieve relevant context for LLM analysis using RAG

**Interface**:
```python
class ContextRetriever:
    def __init__(self, vector_store: VectorStore, sqlite_db: Path):
        """Initialize with vector store and SQLite connection"""
        
    def retrieve_bill_context(self, bill_id: str, limit: int = 10) -> BillContext:
        """
        Retrieve full context for a bill across all sessions
        
        Returns:
            BillContext with bill text, amendments, related statements, votes
        """
        
    def retrieve_mp_context(self, mp_id: str, bill_id: str, limit: int = 10) -> MPContext:
        """
        Retrieve MP's history with a specific bill
        
        Returns:
            MPContext with previous statements, votes, questions
        """
        
    def retrieve_related_documents(self, statement_id: str, limit: int = 20) -> RelatedDocs:
        """
        Find documents related to a statement
        
        Returns:
            RelatedDocs with votes, questions, petitions, bill versions
        """
```

**Context Structure**:
```python
@dataclass
class BillContext:
    bill_id: str
    bill_text: str
    amendments: List[Amendment]
    related_statements: List[Statement]
    votes: List[VoteRecord]
    questions: List[Question]
    
@dataclass
class MPContext:
    mp_id: str
    bill_id: str
    previous_statements: List[Statement]
    voting_record: List[VoteRecord]
    related_questions: List[Question]
```

### 1. Statement Classifier

**Purpose**: Distinguish substantive statements from filler/procedural text (rule-based with spaCy)

**Interface**:
```python
class StatementClassifier:
    def __init__(self, config: ClassifierConfig):
        """Initialize with filler patterns from config"""
        
    def classify(self, statement: Statement) -> Classification:
        """
        Classify statement as filler or substantive
        
        Returns:
            Classification with type (filler/substantive) and reason
        """
        
    def batch_classify(self, statements: List[Statement]) -> List[Classification]:
        """Classify multiple statements efficiently"""
```

**Implementation Approach**:
- Rule-based classification using configurable patterns
- Pattern categories: parliamentary etiquette, procedural language, acknowledgments
- Confidence scoring based on pattern matches
- Extensible pattern system via YAML configuration

**Configuration Example**:
```yaml
filler_patterns:
  etiquette:
    - "thank you.*speaker"
    - "hon.*members"
    - "point of order"
  procedural:
    - "i beg to move"
    - "i second"
    - "question put and agreed"
```

### 2. Sentiment Analyzer (LLM-based with RAG)

**Purpose**: Determine MP stance toward bills with full multi-session context

**Interface**:
```python
class SentimentAnalyzer:
    def __init__(self, llm_client: LLMClient, context_retriever: ContextRetriever):
        """Initialize with LLM client and context retriever"""
        
    def analyze(self, statement: Statement, bill: Bill) -> VerifiedSentiment:
        """
        Analyze statement sentiment with full context
        
        Returns:
            VerifiedSentiment with classification, confidence, and verified citations
        """
        
    def batch_analyze(self, statements: List[Statement]) -> List[VerifiedSentiment]:
        """Analyze multiple statements efficiently"""
```

**Implementation Approach**:
- Retrieve relevant context using RAG (previous statements, bill amendments, votes)
- Send context + statement to LLM with structured output requirements
- LLM returns sentiment + citations
- Verify citations before storing
- Flag low-confidence analyses for review

**LLM Prompt Structure**:
```python
prompt = f"""
Analyze this MP's sentiment toward Bill {bill_id}.

CRITICAL RULES:
1. You MUST cite exact text from provided documents
2. Do NOT paraphrase or infer information not stated
3. Return structured JSON with citations
4. If uncertain, return confidence: 0.0

Current Statement:
ID: {statement.id}
Text: "{statement.text}"
Date: {statement.date}

Bill Context:
{bill.text}
{bill.amendments}

MP's Previous Statements on this Bill:
{mp_context.previous_statements}

MP's Voting Record:
{mp_context.voting_record}

Return JSON:
{{
    "sentiment": "support|oppose|neutral",
    "confidence": 0.0-1.0,
    "evidence": [
        {{
            "quote": "exact text from statement",
            "source_id": "statement_id or document_id",
            "reasoning": "why this supports the classification"
        }}
    ],
    "related_documents": ["doc_id1", "doc_id2"]
}}
"""
```

**Sentiment Structure**:
```python
@dataclass
class VerifiedSentiment:
    sentiment: str  # 'support', 'oppose', 'neutral'
    confidence: float  # 0.0-1.0
    evidence: List[Citation]  # Verified citations
    flagged_for_review: bool
    audit_log_id: str  # Reference to audit log entry
```

### 2.1 Citation Verifier

**Purpose**: Verify LLM citations against source documents to prevent hallucination

**Interface**:
```python
class CitationVerifier:
    def __init__(self, vector_store: VectorStore, sqlite_db: Path):
        """Initialize with access to source documents"""
        
    def verify_citations(self, analysis: LLMAnalysis, statement: Statement, context: Context) -> VerifiedAnalysis:
        """
        Verify all citations in LLM output
        
        Returns:
            VerifiedAnalysis with only verified citations, or flagged for review
        """
        
    def quote_exists_in_source(self, quote: str, source_text: str, threshold: float = 0.9) -> bool:
        """
        Check if quote appears in source with fuzzy matching
        
        Args:
            quote: Quote to verify
            source_text: Source document text
            threshold: Similarity threshold (0.9 = 90% match)
        """
```

**Verification Process**:
1. For each citation in LLM output:
   - Retrieve source document by ID
   - Fuzzy match quote against source text (≥90% similarity)
   - If match found, keep citation
   - If no match, log warning and discard citation
2. If no verified citations remain:
   - Return confidence: 0.0
   - Flag for human review
   - Log to audit trail
3. Return analysis with only verified citations

### 3. Quality Scorer

**Purpose**: Distinguish substantive statements from filler/procedural text

**Interface**:
```python
class StatementClassifier:
    def __init__(self, config: ClassifierConfig):
        """Initialize with filler patterns from config"""
        
    def classify(self, statement: Statement) -> Classification:
        """
        Classify statement as filler or substantive
        
        Returns:
            Classification with type (filler/substantive) and reason
        """
        
    def batch_classify(self, statements: List[Statement]) -> List[Classification]:
        """Classify multiple statements efficiently"""
```

**Implementation Approach**:
- Rule-based classification using configurable patterns
- Pattern categories: parliamentary etiquette, procedural language, acknowledgments
- Confidence scoring based on pattern matches
- Extensible pattern system via YAML configuration

**Configuration Example**:
```yaml
filler_patterns:
  etiquette:
    - "thank you.*speaker"
    - "hon.*members"
    - "point of order"
  procedural:
    - "i beg to move"
    - "i second"
    - "question put and agreed"
```

### 2. Sentiment Analyzer

**Purpose**: Determine MP stance toward bills (support/oppose/neutral)

**Interface**:
```python
class SentimentAnalyzer:
    def __init__(self, model_path: str):
        """Initialize spaCy model for sentiment analysis"""
        
    def analyze(self, statement: Statement, bill: Optional[Bill]) -> Sentiment:
        """
        Analyze statement sentiment toward bill
        
        Returns:
            Sentiment with classification (support/oppose/neutral) and confidence
        """
        
    def batch_analyze(self, statements: List[Statement]) -> List[Sentiment]:
        """Analyze multiple statements efficiently"""
```

**Implementation Approach**:
- Use spaCy's pre-trained sentiment model as baseline
- Fine-tune on parliamentary language if needed
- Context-aware: consider bill references and parliamentary conventions
- Confidence thresholding for human review flagging

**Sentiment Indicators**:
- Support: "I support", "commend", "welcome", "agree with"
- Oppose: "I oppose", "reject", "disagree", "concerns about"
- Neutral: Questions, clarifications, procedural statements

### 3. Quality Scorer

**Purpose**: Assign quality scores to substantive statements

**Interface**:
```python
class QualityScorer:
    def __init__(self, config: ScorerConfig):
        """Initialize with scoring weights from config"""
        
    def score(self, statement: Statement) -> QualityScore:
        """
        Calculate quality score (0-100) for statement
        
        Returns:
            QualityScore with score and contributing factors
        """
        
    def batch_score(self, statements: List[Statement]) -> List[QualityScore]:
        """Score multiple statements efficiently"""
```

**Scoring Factors**:
1. **Length** (0-20 points): Substantive statements are typically 50-500 words
2. **Policy Specificity** (0-25 points): References to specific bills, policies, data
3. **Evidence Use** (0-25 points): Citations, statistics, examples
4. **Coherence** (0-15 points): Logical structure, clear argumentation
5. **Impact** (0-15 points): Addresses significant issues, proposes solutions

**Configuration**:
```yaml
quality_scoring:
  weights:
    length: 0.20
    specificity: 0.25
    evidence: 0.25
    coherence: 0.15
    impact: 0.15
  thresholds:
    highlight: 80
    review: 60
```

### 4. Topic Classifier

**Purpose**: Categorize bills and statements into policy topics

**Interface**:
```python
class TopicClassifier:
    def __init__(self, taxonomy: TopicTaxonomy):
        """Initialize with topic taxonomy"""
        
    def classify(self, text: str) -> List[TopicAssignment]:
        """
        Classify text into policy topics
        
        Returns:
            List of topics with confidence scores (primary + secondary)
        """
        
    def batch_classify(self, texts: List[str]) -> List[List[TopicAssignment]]:
        """Classify multiple texts efficiently"""
```

**Topic Taxonomy** (Configurable):
```yaml
topics:
  - id: healthcare
    name: Healthcare & Medical Services
    keywords: [health, medical, hospital, doctor, patient]
    
  - id: education
    name: Education & Training
    keywords: [education, school, university, teacher, student]
    
  - id: finance
    name: Finance & Economy
    keywords: [budget, tax, economy, finance, revenue]
    
  - id: infrastructure
    name: Infrastructure & Development
    keywords: [road, water, electricity, infrastructure, development]
    
  - id: agriculture
    name: Agriculture & Food Security
    keywords: [agriculture, farming, food, crop, livestock]
    
  - id: security
    name: Security & Defense
    keywords: [security, police, military, defense, crime]
```

**Implementation Approach**:
- Keyword-based classification with TF-IDF weighting
- Support for multi-label classification (primary + secondary topics)
- Extensible taxonomy via configuration
- Consider using spaCy's text categorization for more sophisticated classification

### 5. Problematic Statement Detector

**Purpose**: Identify statements showing impunity, ignorance, or sycophancy

**Interface**:
```python
class ProblematicStatementDetector:
    def __init__(self, config: DetectorConfig):
        """Initialize with problematic patterns from config"""
        
    def detect(self, statement: Statement) -> Optional[ProblematicFlag]:
        """
        Detect problematic content in statement
        
        Returns:
            ProblematicFlag with category and matched patterns, or None
        """
        
    def batch_detect(self, statements: List[Statement]) -> List[Optional[ProblematicFlag]]:
        """Detect problematic content in multiple statements"""
```

**Problematic Categories**:
```yaml
problematic_patterns:
  impunity:
    - "above the law"
    - "untouchable"
    - "no one can touch"
    
  ignorance:
    - "i don't know"
    - "not my concern"
    - "not important"
    
  sycophancy:
    - "your excellency.*great"
    - "wise leader"
    - "unmatched wisdom"
```

### 6. Votes & Proceedings Scraper

**Purpose**: Extract voting records from parliament.go.ke

**Interface**:
```python
class VotesProceedings Scraper:
    def __init__(self, base_url: str):
        """Initialize with parliament.go.ke base URL"""
        
    def scrape_votes(self, date_range: DateRange) -> List[VoteRecord]:
        """
        Scrape voting records for date range
        
        Returns:
            List of VoteRecord with bill, MP votes, and metadata
        """
        
    def parse_vote_document(self, pdf_path: Path) -> List[VoteRecord]:
        """Parse votes from downloaded PDF"""
```

**Vote Record Structure**:
```python
@dataclass
class VoteRecord:
    bill_id: str
    bill_title: str
    vote_date: date
    votes: List[MPVote]  # List of (mp_id, vote_direction)
    session_id: str
```

### 7. Statements Tracker Processor

**Purpose**: Extract constituency representation from Statements Tracker PDFs

**Interface**:
```python
class StatementsTrackerProcessor:
    def __init__(self, download_url: str):
        """Initialize with Statements Tracker PDF URL"""
        
    def download_latest(self) -> Path:
        """Download latest Statements Tracker PDF"""
        
    def parse_statements(self, pdf_path: Path) -> List[ConstituencyStatement]:
        """
        Parse constituency statements from PDF
        
        Returns:
            List of statements with MP, constituency, and content
        """
```

### 8. Weekly Content Generator

**Purpose**: Generate "This Week in Parliament" summaries

**Interface**:
```python
class WeeklyContentGenerator:
    def __init__(self, db_path: Path):
        """Initialize with database connection"""
        
    def generate_weekly_summary(self, week_start: date) -> WeeklySummary:
        """
        Generate summary for specified week
        
        Returns:
            WeeklySummary with bills, top statements, attendance
        """
        
    def archive_summary(self, summary: WeeklySummary) -> Path:
        """Save summary to archive with permanent URL"""
```

**Weekly Summary Structure**:
```python
@dataclass
class WeeklySummary:
    week_start: date
    week_end: date
    bills_passed: List[Bill]
    bills_debated: List[Bill]
    top_statements: List[Statement]  # By quality score
    attendance_stats: AttendanceStats
    notable_votes: List[VoteRecord]
```

### 9. Historical Content Generator

**Purpose**: Generate "This Day in Parliament History" pages

**Interface**:
```python
class HistoricalContentGenerator:
    def __init__(self, db_path: Path):
        """Initialize with database connection"""
        
    def generate_historical_page(self, target_date: date) -> HistoricalPage:
        """
        Generate historical page for date across all years
        
        Returns:
            HistoricalPage with discussions from same date in previous years
        """
```

### 10. Enhanced Static Site Generator

**Purpose**: Generate static HTML pages with new features

**Interface**:
```python
class EnhancedSiteGenerator:
    def __init__(self, db_path: Path, template_dir: Path, output_dir: Path):
        """Initialize with database and template paths"""
        
    def generate_mp_page(self, mp_id: str) -> Path:
        """Generate enhanced MP profile page"""
        
    def generate_party_page(self, party_id: str) -> Path:
        """Generate enhanced party page"""
        
    def generate_session_page(self, session_id: str) -> Path:
        """Generate session page with top quotes"""
        
    def generate_weekly_archive(self) -> Path:
        """Generate weekly summaries archive"""
        
    def generate_historical_pages(self) -> List[Path]:
        """Generate all historical date pages"""
        
    def generate_topic_index(self) -> Path:
        """Generate policy topic index page"""
```

## Data Models

### Dual Storage Architecture

**SQLite** stores structured, queryable data:
- MP metadata, votes, attendance
- Statement metadata (id, date, mp_id, session_id)
- Analysis results (sentiment, quality scores, classifications)
- Source references (PDF URLs, hashes, page numbers)
- Audit logs

**ChromaDB** stores full text with embeddings:
- Complete statement text
- Full bill text (all versions)
- Questions, petitions, tracker documents
- Semantic search via embeddings

### Database Schema Extensions

**statements** table (enhanced):
```sql
CREATE TABLE statements (
    id INTEGER PRIMARY KEY,
    mp_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    date DATE NOT NULL,
    
    -- Source references (immutable)
    source_pdf_url TEXT NOT NULL,
    source_pdf_hash TEXT NOT NULL,  -- SHA256
    page_number INTEGER,
    line_number INTEGER,
    
    -- Vector DB reference
    vector_doc_id TEXT NOT NULL,  -- ID in ChromaDB
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mp_id) REFERENCES mps(id),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

**statement_sentiments** table (enhanced with citations):
```sql
CREATE TABLE statement_sentiments (
    id INTEGER PRIMARY KEY,
    statement_id INTEGER NOT NULL,
    bill_id INTEGER,
    sentiment TEXT NOT NULL,  -- 'support', 'oppose', 'neutral'
    confidence REAL NOT NULL,
    flagged_for_review BOOLEAN DEFAULT 0,
    
    -- Evidence citations (JSON array)
    evidence_citations TEXT NOT NULL,  -- JSON: [{quote, source_id, reasoning}]
    
    -- LLM metadata
    llm_model TEXT NOT NULL,  -- e.g., 'claude-3.5-haiku'
    llm_prompt_hash TEXT NOT NULL,  -- SHA256 of prompt
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (statement_id) REFERENCES statements(id),
    FOREIGN KEY (bill_id) REFERENCES bills(id)
);
```

**analysis_audit_log** table (new):
```sql
CREATE TABLE analysis_audit_log (
    id INTEGER PRIMARY KEY,
    statement_id INTEGER NOT NULL,
    analysis_type TEXT NOT NULL,  -- 'sentiment', 'quality', 'classification'
    
    -- LLM details
    llm_model TEXT NOT NULL,
    llm_prompt_hash TEXT NOT NULL,
    llm_response TEXT NOT NULL,  -- Full JSON response
    
    -- Verification results
    citations_provided INTEGER NOT NULL,
    citations_verified INTEGER NOT NULL,
    verification_failures TEXT,  -- JSON array of failed citations
    
    -- Outcome
    confidence REAL NOT NULL,
    flagged_for_review BOOLEAN DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (statement_id) REFERENCES statements(id)
);
```

**human_review_queue** table (new):
```sql
CREATE TABLE human_review_queue (
    id INTEGER PRIMARY KEY,
    statement_id INTEGER NOT NULL,
    analysis_type TEXT NOT NULL,
    
    -- Analysis results
    analysis_data TEXT NOT NULL,  -- JSON
    
    -- Review flags
    flags TEXT NOT NULL,  -- JSON array: ['low_confidence', 'no_citations', etc.]
    
    -- Review status
    status TEXT DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'modified'
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (statement_id) REFERENCES statements(id)
);
```

**bills** table (enhanced):
```sql
CREATE TABLE bills (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    bill_number TEXT NOT NULL,
    status TEXT NOT NULL,
    
    -- Source references
    source_url TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    
    -- Vector DB references
    vector_doc_ids TEXT NOT NULL,  -- JSON array of version IDs in ChromaDB
    
    introduced_date DATE,
    passed_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**statement_quality_scores** table:
```sql
CREATE TABLE statement_quality_scores (
    id INTEGER PRIMARY KEY,
    statement_id INTEGER NOT NULL,
    overall_score REAL NOT NULL,  -- 0-100
    length_score REAL,
    specificity_score REAL,
    evidence_score REAL,
    coherence_score REAL,
    impact_score REAL,
    flagged_as_highlight BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (statement_id) REFERENCES statements(id)
);
```

**bill_topics** table:
```sql
CREATE TABLE bill_topics (
    id INTEGER PRIMARY KEY,
    bill_id INTEGER NOT NULL,
    topic_id TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT 0,
    confidence REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills(id)
);
```

**statement_topics** table:
```sql
CREATE TABLE statement_topics (
    id INTEGER PRIMARY KEY,
    statement_id INTEGER NOT NULL,
    topic_id TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (statement_id) REFERENCES statements(id)
);
```

**vote_records** table:
```sql
CREATE TABLE vote_records (
    id INTEGER PRIMARY KEY,
    bill_id INTEGER NOT NULL,
    mp_id INTEGER NOT NULL,
    vote_direction TEXT NOT NULL,  -- 'yes', 'no', 'abstain'
    vote_date DATE NOT NULL,
    session_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills(id),
    FOREIGN KEY (mp_id) REFERENCES mps(id),
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    UNIQUE(bill_id, mp_id, session_id)
);
```

**attendance_records** table:
```sql
CREATE TABLE attendance_records (
    id INTEGER PRIMARY KEY,
    mp_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    present BOOLEAN NOT NULL,
    session_date DATE NOT NULL,
    session_type TEXT,  -- 'plenary', 'committee', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mp_id) REFERENCES mps(id),
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    UNIQUE(mp_id, session_id)
);
```

**constituency_statements** table:
```sql
CREATE TABLE constituency_statements (
    id INTEGER PRIMARY KEY,
    mp_id INTEGER NOT NULL,
    constituency_id INTEGER NOT NULL,
    statement_id INTEGER,
    statement_text TEXT NOT NULL,
    statement_date DATE NOT NULL,
    source_document TEXT,  -- Reference to Statements Tracker PDF
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mp_id) REFERENCES mps(id),
    FOREIGN KEY (constituency_id) REFERENCES constituencies(id),
    FOREIGN KEY (statement_id) REFERENCES statements(id)
);
```

**problematic_statements** table:
```sql
CREATE TABLE problematic_statements (
    id INTEGER PRIMARY KEY,
    statement_id INTEGER NOT NULL,
    category TEXT NOT NULL,  -- 'impunity', 'ignorance', 'sycophancy'
    matched_patterns TEXT NOT NULL,  -- JSON array of matched patterns
    severity TEXT,  -- 'low', 'medium', 'high'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (statement_id) REFERENCES statements(id)
);
```

**weekly_summaries** table:
```sql
CREATE TABLE weekly_summaries (
    id INTEGER PRIMARY KEY,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    summary_data TEXT NOT NULL,  -- JSON with bills, statements, stats
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(week_start)
);
```

### Schema Migration Strategy

```python
class DatabaseMigrator:
    def __init__(self, db_path: Path):
        """Initialize with database path"""
        
    def get_current_version(self) -> int:
        """Get current schema version"""
        
    def apply_migrations(self, target_version: Optional[int] = None):
        """Apply migrations up to target version"""
        
    def rollback_migration(self, target_version: int):
        """Rollback to specific version"""
```

**Migration Files**:
- `migrations/001_add_classifications.sql`
- `migrations/002_add_sentiments.sql`
- `migrations/003_add_quality_scores.sql`
- etc.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I've identified several areas of redundancy:

**Redundancy Group 1: Statement Classification**
- Properties 1.1, 1.2, 1.3 all test statement classification
- Can be combined into one comprehensive property about classification correctness

**Redundancy Group 2: Data Persistence**
- Properties 1.6, 2.5, 3.6, 4.5 all test database storage
- These are implied by the system working correctly - if classification works and we can query results, storage worked
- Can be reduced to one property about data persistence round-trip

**Redundancy Group 3: Participation Metrics**
- Properties 1.4 and 5.1 are identical (exclude filler statements from metrics)
- Combine into single property

**Redundancy Group 4: Page Generation Structure**
- Properties 6.1, 7.1, 8.3 test that page sections exist
- These are examples of page structure, not properties
- Keep as integration test examples, not properties

**Redundancy Group 5: Sentiment Classification**
- Properties 2.2, 2.3, 2.4 test specific sentiment types
- Property 2.1 already covers all sentiment classification
- The specific types are edge cases handled by generators

**Redundancy Group 6: Schema Initialization**
- Properties 18.1-18.7 all test table creation
- Can be combined into one property about complete schema initialization

**Redundancy Group 7: Configuration Loading**
- Properties 20.1-20.5 all test configuration file loading
- Can be combined into one property about configuration system

After reflection, reducing from 100+ testable criteria to ~40 unique properties that provide comprehensive coverage without redundancy.

### Correctness Properties

**Property 1: Statement Classification Completeness**
*For any* statement processed by the system, the statement should be classified as exactly one of: filler or substantive, with a classification reason stored.
**Validates: Requirements 1.1, 1.2, 1.3, 1.6**

**Property 2: Filler Statement Exclusion from Metrics**
*For any* MP with a mix of filler and substantive statements, participation metrics should count only substantive statements.
**Validates: Requirements 1.4, 5.1**

**Property 3: Sentiment Classification Completeness**
*For any* statement related to a bill, the system should assign exactly one sentiment (support/oppose/neutral) with a confidence score between 0 and 1.
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

**Property 4: Low Confidence Flagging**
*For any* sentiment classification with confidence below the configured threshold, the statement should be flagged for review.
**Validates: Requirements 2.6**

**Property 5: Quality Score Range**
*For any* substantive statement, the quality score should be between 0 and 100 inclusive.
**Validates: Requirements 3.1, 3.6**

**Property 6: High Quality Flagging**
*For any* statement with quality score above 80, the statement should be flagged as a potential highlight.
**Validates: Requirements 3.4**

**Property 7: Topic Assignment Completeness**
*For any* bill processed by the system, at least one policy topic should be assigned.
**Validates: Requirements 4.1, 4.5**

**Property 8: Primary Topic Uniqueness**
*For any* bill with multiple topic assignments, exactly one topic should be marked as primary.
**Validates: Requirements 4.3**

**Property 9: Statement Grouping by Topic**
*For any* MP page generated, statements should be grouped such that all statements in a topic group share that topic classification.
**Validates: Requirements 4.4, 5.2**

**Property 10: Average Quality Score Accuracy**
*For any* MP with substantive statements, the displayed average quality score should equal the mean of all their substantive statement scores.
**Validates: Requirements 5.3**

**Property 11: Sentiment Distribution Completeness**
*For any* MP with bill-related statements, the sentiment distribution should sum to the total number of bill-related statements.
**Validates: Requirements 5.4**

**Property 12: Term Filtering**
*For any* participation metric calculation, only statements from the last two parliament terms should be included.
**Validates: Requirements 5.5**

**Property 13: Top Quotes Balance**
*For any* session with statements from multiple sides of a debate, top quotes should include at least one statement from each side if quality scores permit.
**Validates: Requirements 6.2**

**Property 14: Top Quotes Quality Threshold**
*For any* session, all top quotes should have quality scores of 80 or above, unless fewer than 10 statements meet this threshold.
**Validates: Requirements 6.3**

**Property 15: Top Quotes Field Completeness**
*For any* top quote displayed, the output should contain speaker name, statement text, context, and related bill (if applicable).
**Validates: Requirements 6.4**

**Property 16: Top Quotes Count Limit**
*For any* session day page, the number of top quotes should not exceed 10.
**Validates: Requirements 6.5**

**Property 17: Problematic Pattern Detection**
*For any* statement containing configured problematic patterns, the statement should be flagged with the appropriate category (impunity/ignorance/sycophancy).
**Validates: Requirements 7.2, 7.3, 7.4, 7.5**

**Property 18: Problematic Section Conditional Display**
*For any* MP with zero problematic statements, their page should not contain a problematic statements section.
**Validates: Requirements 7.7**

**Property 19: Constituency Statement Linking**
*For any* constituency statement extracted from Statements Tracker, the statement should be linked to both the MP and their constituency.
**Validates: Requirements 8.1, 8.2**

**Property 20: Constituency Statement Count Accuracy**
*For any* MP page, the displayed constituency statement count should equal the number of constituency statements linked to that MP.
**Validates: Requirements 8.4**

**Property 21: PDF Parsing Error Resilience**
*For any* Statements Tracker PDF that fails to parse, the system should log the error and continue processing without crashing.
**Validates: Requirements 8.6**

**Property 22: Attendance Percentage Accuracy**
*For any* MP, the attendance percentage should equal (sessions attended / sessions eligible) × 100.
**Validates: Requirements 9.2, 9.5**

**Property 23: Attendance Grouping by Session Type**
*For any* MP attendance display, attendance records should be grouped such that all records in a session type group share that session type.
**Validates: Requirements 9.3**

**Property 24: Vote Record Completeness**
*For any* vote extracted from Votes & Proceedings, the stored record should contain bill ID, vote direction, and date.
**Validates: Requirements 10.1, 10.2**

**Property 25: Vote Topic Grouping**
*For any* MP voting history display, votes should be grouped such that all votes in a topic group relate to bills with that topic.
**Validates: Requirements 10.3**

**Property 26: Party Alignment Calculation**
*For any* MP vote on a bill, if a party position exists for that bill, the vote should be marked as aligned or divergent based on matching the party position.
**Validates: Requirements 10.4, 10.5**

**Property 27: Weekly Summary Date Range**
*For any* weekly summary, all included bills and statements should have dates within the summary's week_start to week_end range.
**Validates: Requirements 11.2, 11.3, 11.4, 11.5**

**Property 28: Weekly Summary Archival**
*For any* generated weekly summary, a permanent URL should be created and the summary should be retrievable via that URL.
**Validates: Requirements 11.6**

**Property 29: Archive Chronological Ordering**
*For any* weekly archive display, summaries should be ordered by week_start date in descending order.
**Validates: Requirements 11.7**

**Property 30: Historical Date Matching**
*For any* historical date page for date D, all displayed discussions should be from date D in previous years.
**Validates: Requirements 12.1**

**Property 31: Historical Discussion Field Completeness**
*For any* historical discussion displayed, the output should contain year, topic, and key statements.
**Validates: Requirements 12.2**

**Property 32: Historical Page Generation Completeness**
*For any* date with parliamentary activity in the database, a historical date page should be generated.
**Validates: Requirements 12.5**

**Property 33: Party Statement Aggregation by Topic**
*For any* party page, statements should be aggregated such that all statements in a topic group are from party members and relate to that topic.
**Validates: Requirements 13.1**

**Property 34: Weighted Party Position**
*For any* party position calculation on a topic, statements with higher quality scores should have proportionally more influence on the calculated position.
**Validates: Requirements 13.2**

**Property 35: Party Sentiment Distribution**
*For any* party page topic section, the sentiment distribution should sum to the total number of party member statements on that topic.
**Validates: Requirements 13.3**

**Property 36: Data Source Error Isolation**
*For any* processing run with multiple data sources, if one data source fails, processing should continue for remaining data sources.
**Validates: Requirements 14.5**

**Property 37: Data Source Logging**
*For any* data source processing attempt, the system should log the source identifier, status (success/failure), and any errors.
**Validates: Requirements 14.6**

**Property 38: Automated Processing End-to-End**
*For any* scheduled processing run, the system should complete data collection, analysis, and site generation without manual intervention.
**Validates: Requirements 15.1, 15.2, 15.3**

**Property 39: Error Notification with Context**
*For any* error during automated processing, if notifications are configured, a notification should be sent containing error details and context.
**Validates: Requirements 15.4**

**Property 40: Processing Log Completeness**
*For any* processing run, logs should contain timestamps, component identifiers, and status for each major processing step.
**Validates: Requirements 15.6**

**Property 41: Optional Human Review Independence**
*For any* processing run with human review disabled, all analysis and generation should complete successfully.
**Validates: Requirements 15.7**

**Property 42: CI/CD Test-Gated Deployment**
*For any* code push to main branch, deployment should only occur if all tests pass.
**Validates: Requirements 16.3**

**Property 43: Infrastructure Change Automation**
*For any* infrastructure code change, the change should be applied through the CI/CD pipeline, not manually.
**Validates: Requirements 16.6**

**Property 44: Automatic Rollback on Health Check Failure**
*For any* deployment where health checks fail, the system should automatically rollback to the previous version.
**Validates: Requirements 16.7**

**Property 45: Structured Logging Format**
*For any* log entry, the entry should contain timestamp, log level, component, and message in a structured format (JSON).
**Validates: Requirements 17.3**

**Property 46: Metrics Exposure**
*For any* processing run, metrics for processing time, error rate, and data volume should be collected and exposed for monitoring.
**Validates: Requirements 17.4**

**Property 47: Schema Migration Data Preservation**
*For any* database schema migration, all data present before migration should remain accessible after migration.
**Validates: Requirements 18.8**

**Property 48: Configuration Validation**
*For any* system startup, configuration should be validated and any errors should be logged before processing begins.
**Validates: Requirements 20.7**

**Property 49: Invalid Configuration Fallback**
*For any* invalid configuration value, the system should log the error and use the default value for that configuration.
**Validates: Requirements 20.6**

**Property 50: Error Logging with Context**
*For any* error encountered during processing, the log entry should contain timestamp, error type, error message, and processing context.
**Validates: Requirements 21.1, 21.4**

**Property 51: Single Statement Failure Isolation**
*For any* batch of statements being processed, if one statement fails processing, the remaining statements should continue to be processed.
**Validates: Requirements 21.2**

**Property 52: Exponential Backoff Retry**
*For any* failed external data source request, the system should retry with exponentially increasing delays between attempts.
**Validates: Requirements 21.3**

**Property 53: Conditional Critical Error Notification**
*For any* critical error, if notifications are configured, a notification should be sent.
**Validates: Requirements 21.6**

**Property 54: Adaptive Streaming Processing**
*For any* processing run where memory usage exceeds configured thresholds, the system should switch to streaming processing mode.
**Validates: Requirements 22.6**

**Property 55: Context Retrieval Relevance**
*For any* statement analysis, retrieved context documents should have semantic similarity scores above the configured threshold.
**Validates: Requirements 25.2, 25.3**

**Property 56: Vector Storage Completeness**
*For any* document stored in SQLite, a corresponding document with embeddings should exist in the vector database.
**Validates: Requirements 25.4**

**Property 57: Citation Verification Requirement**
*For any* LLM analysis output, all citations must be verified against source documents before storing results.
**Validates: Requirements 26.2**

**Property 58: No Generated Content**
*For any* statement displayed on the website, the text must exactly match the text stored in the database from the original Hansard source.
**Validates: Requirements 26.3**

**Property 59: Source Reference Immutability**
*For any* statement, the source reference fields (PDF URL, hash, page number) must never be modified after initial storage.
**Validates: Requirements 26.4**

**Property 60: Low Confidence Review Flagging**
*For any* LLM analysis with confidence below the configured threshold, the analysis must be flagged for human review.
**Validates: Requirements 26.5**

**Property 61: Audit Log Completeness**
*For any* LLM analysis performed, an audit log entry must be created containing the prompt hash, model, response, and verification results.
**Validates: Requirements 26.6**

**Property 62: Citation Fuzzy Match Threshold**
*For any* citation verification, the quote must match the source text with at least 90% similarity.
**Validates: Requirements 26.8**

**Property 63: Failed Citation Rejection**
*For any* LLM analysis where citation verification fails for all citations, the analysis must be rejected and flagged for review.
**Validates: Requirements 26.9**

## Error Handling

### Error Categories

1. **Data Collection Errors**
   - Network failures when scraping parliament.go.ke
   - PDF download failures
   - PDF parsing errors

2. **Processing Errors**
   - Statement classification failures
   - Sentiment analysis errors
   - Quality scoring failures
   - Topic classification errors

3. **Storage Errors**
   - Database connection failures
   - Transaction failures
   - Schema migration errors

4. **Generation Errors**
   - Template rendering failures
   - File write errors
   - Deployment failures

### Error Handling Strategy

**Retry Logic**:
```python
def retry_with_backoff(func, max_retries=3, base_delay=1.0):
    """
    Retry function with exponential backoff
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each retry)
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s")
            time.sleep(delay)
```

**Error Isolation**:
- Process statements in batches with try-except around each statement
- Continue processing remaining statements if one fails
- Log failures with full context for debugging

**Graceful Degradation**:
- If sentiment analysis fails, mark sentiment as "unknown"
- If quality scoring fails, assign default score of 50
- If topic classification fails, assign "uncategorized" topic
- Generate pages with available data, mark missing sections clearly

**Notification Strategy**:
```yaml
notifications:
  enabled: true
  channels:
    - type: email
      recipients: [maintainer@example.com]
      on_error_types: [critical, data_loss]
    
    - type: slack
      webhook_url: ${SLACK_WEBHOOK}
      on_error_types: [critical]
```

## Testing Strategy

### Dual Testing Approach

The system requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests**: Verify specific examples, edge cases, and error conditions
- Test specific filler patterns match correctly
- Test edge cases like empty statements, missing data
- Test error handling for network failures, parsing errors
- Test integration between components

**Property-Based Tests**: Verify universal properties across all inputs
- Use Hypothesis library for Python property-based testing
- Generate random statements, bills, MPs, votes
- Verify properties hold for all generated inputs
- Minimum 100 iterations per property test

### Property-Based Testing Configuration

**Library**: Hypothesis (https://hypothesis.readthedocs.io/)

**Test Structure**:
```python
from hypothesis import given, strategies as st
import pytest

@given(st.text(min_size=10, max_size=1000))
def test_statement_classification_completeness(statement_text):
    """
    Feature: advanced-parliamentary-analysis
    Property 1: Statement Classification Completeness
    
    For any statement, classification should return exactly one type
    """
    statement = Statement(text=statement_text, mp_id=1, session_id=1)
    classifier = StatementClassifier(config)
    
    classification = classifier.classify(statement)
    
    assert classification.type in ['filler', 'substantive']
    assert classification.reason is not None
    assert len(classification.reason) > 0
```

**Test Tagging**:
Every property test must include a comment referencing the design property:
```python
"""
Feature: advanced-parliamentary-analysis
Property {number}: {property_text}
"""
```

**Minimum Iterations**:
Configure Hypothesis to run minimum 100 iterations:
```python
from hypothesis import settings

@settings(max_examples=100)
@given(...)
def test_property(...):
    ...
```

### Test Coverage Requirements

- Overall project: ≥90% coverage
- New modules: ≥90% coverage
- All properties must have corresponding property tests
- All error paths must have unit tests

### Integration Testing

**End-to-End Pipeline Tests**:
1. Download sample PDFs
2. Process through full pipeline
3. Verify database contains expected data
4. Generate static pages
5. Verify pages contain expected content

**Data Source Integration Tests**:
- Test Hansard scraping and processing
- Test Votes & Proceedings scraping
- Test Statements Tracker processing
- Verify error handling for unavailable sources

## Infrastructure and Deployment

### Infrastructure as Code (Terraform)

**Directory Structure**:
```
terraform/
├── modules/
│   ├── static-site/        # S3 + CloudFront
│   ├── processing/         # Lambda or EC2
│   ├── database/           # RDS or managed SQLite
│   └── monitoring/         # CloudWatch, alarms
├── environments/
│   ├── dev/
│   ├── staging/
│   └── production/
└── main.tf
```

**Static Site Module** (S3 + CloudFront):
```hcl
module "static_site" {
  source = "./modules/static-site"
  
  bucket_name = "hansard-tales-${var.environment}"
  domain_name = var.domain_name
  
  cloudfront_config = {
    price_class = "PriceClass_100"  # US, Canada, Europe
    min_ttl     = 0
    default_ttl = 86400  # 24 hours
    max_ttl     = 31536000  # 1 year
  }
}
```

**Processing Module** (Lambda for scheduled processing):
```hcl
module "processing" {
  source = "./modules/processing"
  
  function_name = "hansard-processor-${var.environment}"
  runtime       = "python3.12"
  timeout       = 900  # 15 minutes
  memory_size   = 2048  # 2GB
  
  schedule_expression = "cron(0 2 * * ? *)"  # Daily at 2 AM UTC
  
  environment_variables = {
    DB_PATH = "/tmp/hansard.db"
    CONFIG_PATH = "/opt/config.yaml"
  }
}
```

### CI/CD Pipeline (GitHub Actions)

**Workflow Structure**:
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests
        run: |
          pytest --cov=hansard_tales --cov-report=term --cov-report=xml
      
      - name: Check coverage
        run: |
          coverage report --fail-under=90
  
  terraform-plan:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1
      
      - name: Terraform Plan
        run: |
          cd terraform/environments/${{ github.event.pull_request.base.ref }}
          terraform init
          terraform plan
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1
      
      - name: Terraform Apply
        run: |
          cd terraform/environments/production
          terraform init
          terraform apply -auto-approve
      
      - name: Deploy Lambda
        run: |
          zip -r function.zip hansard_tales/
          aws lambda update-function-code \
            --function-name hansard-processor-production \
            --zip-file fileb://function.zip
      
      - name: Run health checks
        run: |
          python scripts/health_check.py --environment production
      
      - name: Rollback on failure
        if: failure()
        run: |
          python scripts/rollback.py --environment production
```

### Hosting Cost Analysis

**Option 1: S3 + CloudFront + Lambda (Recommended for MVP)**

*Assumptions*:
- 1000 page views/day
- 10GB static site
- Daily processing (15 min Lambda execution)
- 1GB database

*Monthly Costs*:
- S3 storage: $0.23 (10GB × $0.023/GB)
- CloudFront: $8.50 (100GB transfer × $0.085/GB)
- Lambda: $5.00 (30 executions × 15 min × 2GB)
- Total: ~$14/month

*Pros*:
- Very low cost for low traffic
- No server management
- Automatic scaling
- Pay only for usage

*Cons*:
- Lambda timeout limits (15 min max)
- Cold start latency
- More complex debugging

**Option 2: EC2 t3.micro + S3 + CloudFront**

*Assumptions*:
- t3.micro instance (2 vCPU, 1GB RAM)
- Same traffic as Option 1

*Monthly Costs*:
- EC2: $7.50 (t3.micro reserved)
- S3 + CloudFront: $8.73 (same as Option 1)
- Total: ~$16/month

*Pros*:
- No timeout limits
- Easier debugging
- More control over environment
- Can run long-running processes

*Cons*:
- Always-on cost (even with no traffic)
- Requires server management
- Manual scaling

**Option 3: Netlify/Vercel (Static Site) + AWS Lambda**

*Monthly Costs*:
- Netlify: $0 (free tier: 100GB bandwidth)
- Lambda: $5.00 (same as Option 1)
- Total: ~$5/month

*Pros*:
- Simplest deployment
- Excellent CDN
- Free SSL
- Git-based deployment

*Cons*:
- Vendor lock-in
- Limited control
- May need paid tier for higher traffic

**Recommendation**: Start with Option 1 (S3 + CloudFront + Lambda) for MVP. It offers the best balance of cost, scalability, and ease of management for a solo developer. Can migrate to EC2 if processing needs exceed Lambda limits.

### Monitoring and Observability

**CloudWatch Metrics**:
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def publish_metric(metric_name, value, unit='Count'):
    """Publish custom metric to CloudWatch"""
    cloudwatch.put_metric_data(
        Namespace='HansardTales',
        MetricData=[{
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }]
    )

# Usage
publish_metric('StatementsProcessed', 1500, 'Count')
publish_metric('ProcessingTime', 245.3, 'Seconds')
publish_metric('ErrorRate', 0.02, 'Percent')
```

**Structured Logging**:
```python
import json
import logging

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log(self, level, message, **context):
        """Log with structured context"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'context': context
        }
        self.logger.log(level, json.dumps(log_entry))

# Usage
logger = StructuredLogger('hansard_tales')
logger.log(logging.INFO, 'Processing statement', 
           statement_id=123, mp_id=45, classification='substantive')
```

**Health Checks**:
```python
def health_check():
    """Verify system health"""
    checks = {
        'database': check_database_connection(),
        'storage': check_s3_access(),
        'processing': check_last_processing_time(),
    }
    
    all_healthy = all(checks.values())
    
    return {
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat()
    }
```

### Deployment Rollback Strategy

**Automatic Rollback Triggers**:
1. Health check failures after deployment
2. Error rate spike (>5% in 5 minutes)
3. Processing time increase (>2x baseline)

**Rollback Implementation**:
```python
def rollback_deployment(environment):
    """Rollback to previous deployment"""
    # Get previous Lambda version
    lambda_client = boto3.client('lambda')
    versions = lambda_client.list_versions_by_function(
        FunctionName=f'hansard-processor-{environment}'
    )
    
    previous_version = versions['Versions'][-2]['Version']
    
    # Update alias to previous version
    lambda_client.update_alias(
        FunctionName=f'hansard-processor-{environment}',
        Name='live',
        FunctionVersion=previous_version
    )
    
    logger.info(f'Rolled back to version {previous_version}')
```

## Future Work Documentation

All future enhancements should be documented in `docs/future-work/` with the following structure:

### Senate Integration (docs/future-work/senate-integration.md)

**User Stories**:
- As a researcher, I want to analyze Senate debates alongside National Assembly debates
- As a citizen, I want to see how Senators represent my county

**Architecture Considerations**:
- Extend data source architecture to support Senate documents
- Add Senate-specific tables (senators, senate_sessions, senate_statements)
- Reuse analysis pipeline (classification, sentiment, quality scoring)
- Generate separate Senate pages with similar structure to National Assembly

**Cost Analysis**:
- Additional storage: ~2GB (similar to National Assembly)
- Processing time: +50% (fewer sessions than National Assembly)
- Infrastructure: No additional cost (same Lambda/EC2 handles both)

**Implementation Effort**: 2-3 weeks
- Week 1: Data model extensions, scraper adaptation
- Week 2: Page generation, testing
- Week 3: Integration, deployment

**Scalability Considerations**:
- Database size will double (manageable with SQLite up to ~10GB)
- Consider PostgreSQL if combined data exceeds 5GB
- Processing can remain parallel (separate Lambda invocations)

### Additional Data Sources (docs/future-work/additional-data-sources.md)

**Priority Order**:
1. Votes & Proceedings (High Priority - already in main spec)
2. Bills Tracker (High Priority - enables better bill analysis)
3. Petitions Tracker (Medium Priority - shows constituent engagement)
4. Questions Tracker (Medium Priority - shows MP oversight activity)
5. Committee Reports (Low Priority - complex parsing)

**Per Data Source**:
- User stories
- Data structure analysis
- Parsing complexity assessment
- Storage requirements
- Processing time estimates
- Integration approach
- Cost impact

### Architecture Decision Records (docs/future-work/adrs/)

**ADR Template**:
```markdown
# ADR-001: [Decision Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[What is the issue we're trying to solve?]

## Decision
[What is the change we're proposing?]

## Consequences
### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Cost 1]
- [Trade-off 1]

### Neutral
- [Consideration 1]

## Alternatives Considered
### Alternative 1
- Pros: ...
- Cons: ...
- Why rejected: ...

## Cost Analysis
- Development time: X weeks
- Infrastructure cost: $Y/month
- Maintenance overhead: Z hours/month
```

**Key ADRs to Create**:
1. ADR-001: SQLite vs PostgreSQL for production
2. ADR-002: Lambda vs EC2 for processing
3. ADR-003: spaCy vs NLTK for NLP
4. ADR-004: S3 + CloudFront vs Netlify for hosting
5. ADR-005: Monorepo vs separate repos for Senate integration

## Summary

This design provides a comprehensive architecture for enhancing the Hansard Tales system with advanced parliamentary analysis capabilities. Key design decisions:

1. **Modular NLP Pipeline**: Independent components for classification, sentiment, quality scoring, and topic assignment
2. **spaCy for NLP**: High-performance library with pre-trained models
3. **SQLite with Migration Support**: Maintains simplicity while supporting schema evolution
4. **Lambda + S3 + CloudFront**: Cost-effective, scalable hosting for solo developer
5. **GitHub Actions + Terraform**: Automated CI/CD with infrastructure as code
6. **Property-Based Testing**: Comprehensive correctness verification with Hypothesis
7. **Structured Logging + CloudWatch**: Observable system with actionable metrics
8. **Future-Proof Architecture**: Modular design supports Senate and additional data sources

The design prioritizes automation, cost-effectiveness, and maintainability for a solo developer while providing a solid foundation for future enhancements.
