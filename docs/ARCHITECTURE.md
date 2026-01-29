# Hansard Tales - System Architecture

**Version**: 1.0
**Last Updated**: January 2025
**Status**: Phase 0 Complete

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Component Architecture](#component-architecture)
4. [Data Flow Diagrams](#data-flow-diagrams)
5. [Database Architecture](#database-architecture)
6. [Vector Database Architecture](#vector-database-architecture)
7. [Technology Stack](#technology-stack)
8. [Design Patterns](#design-patterns)
9. [Scalability Considerations](#scalability-considerations)
10. [Security Architecture](#security-architecture)
11. [Monitoring and Observability](#monitoring-and-observability)
12. [Deployment Architecture](#deployment-architecture)
13. [API Design](#api-design)
14. [Anti-Hallucination Architecture](#anti-hallucination-architecture)
15. [Future Enhancements](#future-enhancements)

---

## 1. System Overview

### 1.1 Purpose

Hansard Tales is a comprehensive system for collecting, processing, and analyzing Kenyan parliamentary data. It provides automated tools for scraping parliament.go.ke, processing parliamentary documents (Hansard records, bills, votes, questions, petitions), and performing semantic search and analysis.

### 1.2 Key Capabilities

- **Automated Data Collection**: Scrapes National Assembly and Senate documents with duplicate detection
- **Intelligent Processing**: Extracts text, metadata, and entities from PDF documents
- **Semantic Search**: Vector-based document retrieval using sentence embeddings
- **Source Tracking**: Immutable source references for anti-hallucination
- **Performance Analysis**: Track MP contributions, voting patterns, and legislative activity
- **Production-Ready**: Comprehensive monitoring, logging, and error handling

### 1.3 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Configuration Layer                         │
│  config.yaml → Environment Variables → Validated Config Object  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Models Layer                          │
│  Pydantic Models: Document, Statement, Bill, Vote, Question...  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                              │
│  ┌──────────────────┐         ┌──────────────────┐              │
│  │  SQLAlchemy ORM  │         │  Vector DB       │              │
│  │  (PostgreSQL/    │         │  (Qdrant/        │              │
│  │   SQLite)        │         │   ChromaDB)      │              │
│  └──────────────────┘         └──────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Collection Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Hansard     │  │  Votes       │  │  Bills       │  ...      │
│  │  Scraper     │  │  Scraper     │  │  Scraper     │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Processing Layer                             │
│  PDF Parser → Entity Extractor → Embedding Generator            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Observability Layer                          │
│  Structured Logging + Metrics + Error Tracking                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Principles

### 2.1 Core Principles

1. **Simplicity First**: Start with SQLite and ChromaDB, migrate to PostgreSQL and Qdrant when needed
2. **Type Safety**: Use Pydantic models and type hints throughout
3. **Testability**: Design for easy unit and property-based testing (≥90% coverage)
4. **Extensibility**: Support all 22 document types from the start
5. **Anti-Hallucination**: Immutable source tracking at every layer
6. **Fail-Safe**: Graceful degradation and error isolation
7. **Observability**: Comprehensive logging, metrics, and monitoring

### 2.2 Design Philosophy


- **Stateless Components**: Each component can operate independently
- **Idempotent Operations**: Safe to retry without side effects
- **Portable**: Can run on any machine with minimal dependencies
- **Configuration-Driven**: Behavior controlled through configuration, not code
- **Batch-Oriented**: Process multiple items with error isolation

---

## 3. Component Architecture

### 3.1 Component Overview

The system is organized into distinct layers, each with specific responsibilities:

```
hansard-tales/
├── hansard_tales/          # Main package
│   ├── config/            # Configuration management
│   ├── models/            # Pydantic data models
│   ├── database/          # SQLAlchemy ORM models
│   ├── scrapers/          # Web scrapers
│   ├── processors/        # PDF and document processors
│   ├── vector_db/         # Vector database adapters
│   ├── monitoring/        # Metrics and logging
│   └── utils/             # Utility functions
├── tests/                 # Test suite
├── config/                # Configuration files
├── data/                  # Data storage
├── docs/                  # Documentation
├── alembic/              # Database migrations
└── scripts/              # Utility scripts
```

### 3.2 Configuration Layer

**Purpose**: Centralized configuration with validation and environment-specific overrides

**Technology**: Pydantic Settings + YAML

**Key Components**:
- `Config`: Main configuration class
- `DatabaseConfig`: Database connection settings
- `VectorDBConfig`: Vector database settings
- `ScraperConfig`: Web scraper settings
- `LoggingConfig`: Logging configuration
- `MonitoringConfig`: Monitoring settings

**Features**:
- Environment variable overrides with `__` delimiter
- Type validation using Pydantic
- Default values for all settings
- Separate configs for dev/staging/production

**Example**:
```python
from hansard_tales.config import get_config

config = get_config()
print(config.database.connection_string)
# sqlite:///hansard_tales.db (development)
# postgresql://user:pass@host:5432/db (production)
```


### 3.3 Data Models Layer

**Purpose**: Type-safe data models for all parliamentary documents with immutable source tracking

**Technology**: Pydantic v2 for validation

**Key Models**:
- `Document`: Base document model
- `Statement`: Parliamentary statement from Hansard
- `Bill`: Legislative bill with version tracking
- `Vote`: Parliamentary vote record
- `Question`: Parliamentary question and answer
- `Petition`: Public petition to parliament
- `SourceReference`: Immutable source tracking (frozen dataclass)

**Features**:
- Pydantic validation for all fields
- JSON serialization/deserialization
- Immutable source references (frozen=True)
- UUID-based identifiers
- Enum types for chambers, document types, statuses

**Example**:
```python
from hansard_tales.models import Document, DocumentType, Chamber, SourceReference
from datetime import date, datetime

doc = Document(
    type=DocumentType.HANSARD,
    chamber=Chamber.NATIONAL_ASSEMBLY,
    title="Hansard Report - Tuesday, 4th November 2025 (P)",
    date=date(2025, 11, 4),
    parliament_term=13,
    source=SourceReference(
        source_url="https://parliament.go.ke/...",
        source_hash="abc123...",
        download_date=datetime.utcnow()
    ),
    vector_doc_id="doc_123"
)
```

### 3.4 Storage Layer

**Purpose**: Dual storage for structured data (SQL) and semantic search (vector DB)

**Technology**: SQLAlchemy ORM + ChromaDB/Qdrant

**Components**:
- **Relational Database**: PostgreSQL (prod) / SQLite (dev)
  - Stores structured data with foreign key constraints
  - Alembic for schema migrations
  - Indexes on frequently queried columns

- **Vector Database**: Qdrant (prod) / ChromaDB (dev)
  - Stores document embeddings for semantic search
  - Metadata filtering support
  - Persistent storage to disk

**Key Features**:
- Automatic schema migrations with Alembic
- Foreign key integrity enforcement
- Duplicate detection via source_hash
- Vector-SQL synchronization


### 3.5 Collection Layer

**Purpose**: Automated collection of parliamentary documents from parliament.go.ke

**Technology**: requests + BeautifulSoup4 with CSS selectors

**Key Scrapers**:
- `HansardScraper`: National Assembly/Senate Hansard documents
- `VotesScraper`: Votes & Proceedings documents
- `BillsScraper`: Legislative bills (Phase 1)
- `QuestionsScraper`: Parliamentary questions (Phase 1)
- `PetitionsScraper`: Public petitions (Phase 1)

**Features**:
- Pagination support (fetches all pages automatically)
- CSS selector-based extraction for reliability
- SHA256 hash-based duplicate detection
- Rate limiting to avoid server issues
- Standardized filename generation
- Metadata extraction from filenames
- Retry logic with exponential backoff
- Error isolation (continue on single failure)

**Implementation Details**:
- **Hansard Scraper**:
  - CSS Selector: `table.cols-2 td.views-field-field-pdf a[href$=".pdf"]`
  - Filename Format: `hansard_YYYYMMDD_<P|A|E>.pdf`
  - Verified: 452 PDFs from 19 pages (13th Parliament)

- **Votes Scraper**:
  - CSS Selector: `table.cols-2 td.views-field-field-pdf a[href$=".pdf"]`
  - Filename Format: `votes_YYYYMMDDTHHMMSSZ.pdf`
  - Time extraction from title (e.g., "at 2.30pm")

### 3.6 Processing Layer

**Purpose**: Extract text, metadata, and entities from PDF documents

**Technology**: PyMuPDF (fitz) + pdfplumber

**Key Components**:
- `PDFProcessor`: Base PDF processing
- `HansardProcessor`: Hansard-specific processing
- `VotesProcessor`: Votes-specific processing
- `StorageService`: Document storage coordination

**Features**:
- Multi-column layout support
- Page and line number tracking
- Table extraction
- Metadata extraction
- Batch processing with parallelization
- Error recovery and logging

**Processing Pipeline**:
1. Extract text blocks with coordinates
2. Extract tables (for structured documents)
3. Extract PDF metadata
4. Generate embeddings
5. Store in SQL + Vector DB


### 3.7 Observability Layer

**Purpose**: Comprehensive logging, metrics, and error tracking

**Technology**: structlog + Prometheus + Sentry (optional)

**Components**:
- **Structured Logging**: JSON logs with request IDs
- **Metrics**: Prometheus metrics for monitoring
- **Error Tracking**: Sentry integration for production
- **Health Checks**: Endpoint for service health

**Key Metrics**:
- `documents_processed_total`: Total documents processed
- `document_processing_seconds`: Processing time histogram
- `errors_total`: Total errors by type
- `processing_queue_depth`: Current queue depth
- `vector_db_documents_total`: Vector DB size

---

## 4. Data Flow Diagrams

### 4.1 Document Collection Flow

```
┌─────────────┐
│   Scraper   │
│  (Hansard,  │
│   Votes)    │
└──────┬──────┘
       │
       │ 1. Fetch HTML pages with pagination
       │
       ▼
┌─────────────────┐
│  parliament.    │
│    go.ke        │
└──────┬──────────┘
       │
       │ 2. Extract PDF links (CSS selectors)
       │
       ▼
┌─────────────────┐
│  Download PDFs  │
│  (with retry)   │
└──────┬──────────┘
       │
       │ 3. Compute SHA256 hash
       │
       ▼
┌─────────────────┐
│  Check for      │
│  Duplicates     │
│  (source_hash)  │
└──────┬──────────┘
       │
       │ 4. Skip if exists, else continue
       │
       ▼
┌─────────────────┐
│  Save to Disk   │
│  (standardized  │
│   filename)     │
└──────┬──────────┘
       │
       │ 5. Record in downloaded_files table
       │
       ▼
┌─────────────────┐
│  Downloaded     │
│  Files Table    │
└─────────────────┘
```


### 4.2 Document Processing Flow

```
┌─────────────┐
│  PDF File   │
└──────┬──────┘
       │
       │ 1. Read PDF
       │
       ▼
┌─────────────────┐
│  PDF Processor  │
│  (PyMuPDF +     │
│   pdfplumber)   │
└──────┬──────────┘
       │
       │ 2. Extract text blocks (with page/line numbers)
       │ 3. Extract tables
       │ 4. Extract metadata
       │
       ▼
┌─────────────────┐
│  Extracted      │
│  Content        │
└──────┬──────────┘
       │
       │ 5. Generate embeddings
       │
       ▼
┌─────────────────┐
│  Embedding      │
│  Generator      │
│  (sentence-     │
│   transformers) │
└──────┬──────────┘
       │
       │ 6. Store in parallel
       │
       ├──────────────────┬──────────────────┐
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  SQL DB     │  │  Vector DB  │  │  Metrics    │
│  (metadata) │  │  (semantic) │  │  (tracking) │
└─────────────┘  └─────────────┘  └─────────────┘
```

### 4.3 Semantic Search Flow

```
┌─────────────┐
│  User Query │
│  "healthcare│
│   funding"  │
└──────┬──────┘
       │
       │ 1. Generate query embedding
       │
       ▼
┌─────────────────┐
│  Embedding      │
│  Generator      │
└──────┬──────────┘
       │
       │ 2. Vector similarity search
       │
       ▼
┌─────────────────┐
│  Vector DB      │
│  (Qdrant/       │
│   ChromaDB)     │
└──────┬──────────┘
       │
       │ 3. Return top-k similar documents
       │    with metadata filters
       │
       ▼
┌─────────────────┐
│  Search Results │
│  (with scores)  │
└──────┬──────────┘
       │
       │ 4. Enrich with SQL metadata
       │
       ▼
┌─────────────────┐
│  SQL DB         │
│  (full details) │
└──────┬──────────┘
       │
       │ 5. Return to user
       │
       ▼
┌─────────────────┐
│  Ranked Results │
│  + Source Links │
└─────────────────┘
```


---

## 5. Database Architecture

### 5.1 Relational Database Schema

**Engine**: PostgreSQL (production) / SQLite (development)

**Key Tables**:

#### documents
Stores all parliamentary documents with source tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| type | ENUM | Document type (hansard, bill, vote, etc.) |
| chamber | ENUM | national_assembly or senate |
| title | VARCHAR(500) | Document title |
| date | DATE | Document date |
| session_id | VARCHAR(100) | Session identifier |
| parliament_term | INTEGER | Parliament term (e.g., 13) |
| source_url | TEXT | Original document URL |
| source_hash | VARCHAR(64) | SHA256 hash (unique) |
| download_date | TIMESTAMP | When downloaded |
| vector_doc_id | VARCHAR(100) | Link to vector DB |
| metadata | JSON | Additional metadata |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

**Indexes**:
- `idx_documents_type_chamber_date` (type, chamber, date)
- `idx_documents_source_hash` (source_hash) - UNIQUE
- `idx_documents_date` (date)

#### downloaded_files
Tracks all downloaded files for duplicate prevention.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| source_url | TEXT | Original URL |
| source_hash | VARCHAR(64) | SHA256 hash (unique) |
| standardized_filename | VARCHAR(255) | Generated filename |
| original_filename | VARCHAR(500) | Original filename |
| file_size | INTEGER | File size in bytes |
| document_type | VARCHAR(50) | Document type |
| download_date | TIMESTAMP | When downloaded |
| file_path | TEXT | Local file path |
| chamber | VARCHAR(50) | Chamber |
| parliament_term | INTEGER | Parliament term |
| created_at | TIMESTAMP | Record creation time |

**Indexes**:
- `idx_downloaded_files_hash` (source_hash) - UNIQUE
- `idx_downloaded_files_type` (document_type)
- `idx_downloaded_files_date` (download_date)


#### statements
Stores individual parliamentary statements from Hansard.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| document_id | UUID | Foreign key to documents |
| mp_id | UUID | Foreign key to mps |
| text | TEXT | Statement text |
| timestamp | TIMESTAMP | When statement was made |
| source_url | TEXT | Original document URL |
| source_hash | VARCHAR(64) | Document hash |
| page_number | INTEGER | Page in PDF |
| line_number | INTEGER | Line on page |
| vector_doc_id | VARCHAR(100) | Link to vector DB |
| classification | VARCHAR(50) | filler or substantive |
| sentiment | VARCHAR(50) | support, oppose, neutral |
| quality_score | FLOAT | Quality score (0-100) |
| topics | JSON | List of topics |
| related_bill_ids | JSON | Related bill UUIDs |
| related_question_ids | JSON | Related question UUIDs |
| created_at | TIMESTAMP | Record creation time |

**Indexes**:
- `idx_statements_document_id` (document_id)
- `idx_statements_mp_id` (mp_id)
- `idx_statements_classification` (classification)

#### mps
Stores MPs and Senators.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(200) | Full name |
| chamber | ENUM | national_assembly or senate |
| party | VARCHAR(100) | Political party |
| constituency | VARCHAR(200) | Constituency/County |
| parliament_term | INTEGER | Parliament term |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

**Indexes**:
- `idx_mps_chamber_term` (chamber, parliament_term)
- `idx_mps_name` (name)

#### bills
Stores legislative bills with version tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| bill_number | VARCHAR(50) | Official bill number (unique) |
| title | VARCHAR(500) | Bill title |
| chamber | ENUM | Chamber |
| status | VARCHAR(50) | Bill status |
| current_version | INTEGER | Current version number |
| sponsor_id | UUID | Foreign key to mps |
| co_sponsor_ids | JSON | List of co-sponsor UUIDs |
| related_statement_ids | JSON | Related statements |
| related_vote_ids | JSON | Related votes |
| related_question_ids | JSON | Related questions |
| related_petition_ids | JSON | Related petitions |
| topics | JSON | List of topics |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

**Indexes**:
- `idx_bills_bill_number` (bill_number) - UNIQUE
- `idx_bills_status` (status)
- `idx_bills_chamber` (chamber)


### 5.2 Database Relationships

```
┌─────────────┐
│  documents  │
└──────┬──────┘
       │
       │ 1:N
       │
       ▼
┌─────────────┐       ┌─────────────┐
│ statements  │──────▶│     mps     │
└─────────────┘  N:1  └─────────────┘
                              │
                              │ 1:N
                              │
                              ▼
                       ┌─────────────┐
                       │    bills    │
                       └──────┬──────┘
                              │
                              │ 1:N
                              │
                              ▼
                       ┌─────────────┐
                       │    votes    │
                       └──────┬──────┘
                              │
                              │ 1:N
                              │
                              ▼
                       ┌─────────────┐
                       │  mp_votes   │
                       └─────────────┘
```

### 5.3 Migration Strategy

**Tool**: Alembic

**Process**:
1. Create migration: `alembic revision --autogenerate -m "description"`
2. Review generated migration
3. Apply migration: `alembic upgrade head`
4. Rollback if needed: `alembic downgrade -1`

**Key Features**:
- Automatic schema detection
- Reversible migrations
- Version control for schema
- Data preservation during migrations

---

## 6. Vector Database Architecture

### 6.1 Vector Database Selection

**Development**: ChromaDB (embedded, file-based)
**Production**: Qdrant (server-based, scalable)

**Rationale**:
- ChromaDB: Simple setup, no server required, perfect for development
- Qdrant: High performance, horizontal scaling, production-ready

### 6.2 Collection Schema

#### documents Collection
Stores full document embeddings.

**Dimension**: 384 (all-MiniLM-L6-v2)

**Payload Schema**:
```json
{
  "document_id": "uuid",
  "document_type": "hansard|bill|vote|...",
  "chamber": "national_assembly|senate",
  "date": "YYYY-MM-DD",
  "session_id": "string",
  "parliament_term": 13,
  "source_url": "https://...",
  "source_hash": "sha256..."
}
```


#### statements Collection
Stores individual statement embeddings.

**Dimension**: 384

**Payload Schema**:
```json
{
  "statement_id": "uuid",
  "document_id": "uuid",
  "mp_id": "uuid",
  "chamber": "national_assembly|senate",
  "date": "YYYY-MM-DD",
  "classification": "filler|substantive",
  "quality_score": 85.5,
  "topics": ["healthcare", "education"],
  "source_url": "https://...",
  "source_hash": "sha256...",
  "page_number": 5,
  "line_number": 120
}
```

#### bills Collection
Stores bill version embeddings.

**Dimension**: 384

**Payload Schema**:
```json
{
  "bill_id": "uuid",
  "bill_number": "Bill No. 123 of 2025",
  "version_number": 2,
  "chamber": "national_assembly|senate",
  "status": "second_reading",
  "sponsor_id": "uuid",
  "topics": ["taxation", "finance"],
  "source_url": "https://...",
  "source_hash": "sha256..."
}
```

### 6.3 Embedding Generation

**Model**: sentence-transformers/all-MiniLM-L6-v2

**Specifications**:
- Dimension: 384
- Max sequence length: 256 tokens
- Language: English
- Performance: ~14k sentences/sec on CPU

**Features**:
- Batch processing for efficiency
- Consistent embeddings (same text → same vector)
- Cosine similarity for search
- GPU support (optional)

### 6.4 Search Capabilities

**Supported Operations**:
1. **Semantic Search**: Find similar documents by meaning
2. **Metadata Filtering**: Filter by chamber, date, MP, document type
3. **Hybrid Search**: Combine semantic + metadata filters
4. **Batch Retrieval**: Retrieve multiple documents efficiently

**Example Query**:
```python
results = vector_db.search(
    collection="statements",
    query_vector=embedding,
    limit=10,
    filter={
        "chamber": "national_assembly",
        "date": {"$gte": "2025-01-01"},
        "classification": "substantive"
    }
)
```

---

## 7. Technology Stack

### 7.1 Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Language** | Python | 3.12+ | Primary language |
| **Data Validation** | Pydantic | 2.5+ | Type-safe models |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Migrations** | Alembic | 1.13+ | Schema versioning |
| **Vector DB (Dev)** | ChromaDB | 0.4+ | Embedded vector store |
| **Vector DB (Prod)** | Qdrant | 1.7+ | Production vector store |
| **Embeddings** | sentence-transformers | 2.2+ | Text embeddings |
| **PDF Processing** | PyMuPDF | 1.23+ | PDF text extraction |
| **PDF Tables** | pdfplumber | 0.10+ | Table extraction |
| **Web Scraping** | requests | 2.31+ | HTTP client |
| **HTML Parsing** | BeautifulSoup4 | 4.12+ | HTML parsing |
| **Logging** | structlog | 23.2+ | Structured logging |
| **Metrics** | prometheus-client | 0.19+ | Metrics export |
| **Error Tracking** | sentry-sdk | 1.39+ | Error monitoring |
| **Testing** | pytest | 7.4+ | Test framework |
| **Property Testing** | Hypothesis | 6.92+ | Property-based tests |
| **Coverage** | pytest-cov | 4.1+ | Code coverage |
| **Linting** | ruff | 0.1+ | Fast linter |
| **Type Checking** | mypy | 1.8+ | Static type checking |


### 7.2 Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Database (Prod)** | PostgreSQL 16 | Relational data |
| **Database (Dev)** | SQLite 3 | Local development |
| **Vector DB (Prod)** | Qdrant | Vector search |
| **Vector DB (Dev)** | ChromaDB | Local development |
| **Metrics** | Prometheus | Metrics collection |
| **Dashboards** | Grafana | Visualization |
| **Container Runtime** | Docker | Containerization |
| **Orchestration** | Docker Compose | Local services |
| **CI/CD** | GitHub Actions | Automation |
| **Version Control** | Git | Source control |

### 7.3 Development Tools

| Tool | Purpose |
|------|---------|
| **pre-commit** | Git hooks for quality checks |
| **ruff** | Fast Python linter and formatter |
| **mypy** | Static type checking |
| **pytest** | Test runner |
| **Hypothesis** | Property-based testing |
| **pytest-cov** | Coverage reporting |
| **Make** | Build automation |
| **Alembic** | Database migrations |

---

## 8. Design Patterns

### 8.1 Adapter Pattern

**Usage**: Vector database abstraction

**Purpose**: Support multiple vector DB backends (ChromaDB, Qdrant) with single interface

**Implementation**:
```python
class VectorDB(ABC):
    @abstractmethod
    def search(self, collection, query_vector, limit, filter):
        pass

class ChromaDBAdapter(VectorDB):
    def search(self, collection, query_vector, limit, filter):
        # ChromaDB-specific implementation
        pass

class QdrantAdapter(VectorDB):
    def search(self, collection, query_vector, limit, filter):
        # Qdrant-specific implementation
        pass

def create_vector_db(config) -> VectorDB:
    if config.engine == "chromadb":
        return ChromaDBAdapter(config.persist_directory)
    elif config.engine == "qdrant":
        return QdrantAdapter(config.host, config.port)
```

**Benefits**:
- Easy to switch between implementations
- Testable with mock adapters
- Extensible to new vector DBs


### 8.2 Factory Pattern

**Usage**: Scraper creation, vector DB creation

**Purpose**: Create objects without specifying exact class

**Implementation**:
```python
def create_scraper(document_type: str, config: ScraperConfig):
    scrapers = {
        "hansard": HansardScraper,
        "votes": VotesScraper,
        "bills": BillsScraper,
    }
    scraper_class = scrapers.get(document_type)
    if not scraper_class:
        raise ValueError(f"Unknown document type: {document_type}")
    return scraper_class(config)
```

**Benefits**:
- Centralized object creation
- Easy to add new types
- Configuration-driven

### 8.3 Strategy Pattern

**Usage**: PDF processing strategies

**Purpose**: Different processing strategies for different document types

**Implementation**:
```python
class PDFProcessor:
    def process(self, pdf_path: Path) -> ProcessedPDF:
        # Base processing
        pass

class HansardProcessor(PDFProcessor):
    def process(self, pdf_path: Path) -> ProcessedPDF:
        # Hansard-specific processing
        pass

class VotesProcessor(PDFProcessor):
    def process(self, pdf_path: Path) -> ProcessedPDF:
        # Votes-specific processing
        pass
```

**Benefits**:
- Specialized processing per document type
- Shared base functionality
- Easy to extend

### 8.4 Repository Pattern

**Usage**: Data access layer

**Purpose**: Abstract database operations

**Implementation**:
```python
class DocumentRepository:
    def __init__(self, session):
        self.session = session

    def get_by_id(self, doc_id: UUID) -> Optional[Document]:
        return self.session.query(DocumentORM).filter_by(id=doc_id).first()

    def get_by_hash(self, source_hash: str) -> Optional[Document]:
        return self.session.query(DocumentORM).filter_by(source_hash=source_hash).first()

    def save(self, document: Document) -> None:
        doc_orm = self._to_orm(document)
        self.session.add(doc_orm)
        self.session.commit()
```

**Benefits**:
- Testable with mock repositories
- Centralized data access logic
- Easy to change storage backend


### 8.5 Decorator Pattern

**Usage**: Metrics tracking, retry logic

**Purpose**: Add functionality without modifying original code

**Implementation**:
```python
@track_processing_time('hansard', 'national_assembly')
def process_hansard(pdf_path: Path) -> ProcessedPDF:
    # Processing logic
    pass

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
def download_document(url: str) -> bytes:
    # Download logic
    pass
```

**Benefits**:
- Separation of concerns
- Reusable functionality
- Clean code

### 8.6 Singleton Pattern

**Usage**: Configuration management

**Purpose**: Single global configuration instance

**Implementation**:
```python
_config: Config | None = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config
```

**Benefits**:
- Single source of truth
- Lazy initialization
- Memory efficient

---

## 9. Scalability Considerations

### 9.1 Horizontal Scaling

**Current State**: Single-node deployment

**Future Scaling**:
1. **Database**: PostgreSQL read replicas for query scaling
2. **Vector DB**: Qdrant cluster with sharding
3. **Processing**: Distributed task queue (Celery + Redis)
4. **API**: Load-balanced API servers

### 9.2 Vertical Scaling

**Resource Requirements**:
- **CPU**: 4+ cores for parallel processing
- **RAM**: 8GB+ for embedding generation
- **Storage**: 100GB+ for PDFs and databases
- **Network**: 100Mbps+ for scraping

### 9.3 Performance Optimizations

**Implemented**:
- Batch processing with parallelization
- Database indexes on frequently queried columns
- Vector DB persistence to disk
- Connection pooling for databases
- Caching for configuration

**Future Optimizations**:
- Redis caching for frequent queries
- CDN for static PDF storage
- Async I/O for scraping
- GPU acceleration for embeddings
- Query result caching


### 9.4 Data Volume Projections

**Current Scale** (13th Parliament, 2022-2027):
- Hansard documents: ~450/year × 5 years = 2,250 documents
- Votes & Proceedings: ~200/year × 5 years = 1,000 documents
- Bills: ~100/year × 5 years = 500 documents
- Total PDFs: ~4,000 documents
- Storage: ~20GB PDFs + 5GB databases

**10-Year Scale** (2 parliaments):
- Total PDFs: ~8,000 documents
- Storage: ~40GB PDFs + 10GB databases
- Vector DB: ~10M embeddings

**Scaling Triggers**:
- Database size > 50GB → Consider sharding
- Vector DB size > 100M vectors → Enable clustering
- Query latency > 1s → Add read replicas
- Processing queue > 1000 items → Add workers

---

## 10. Security Architecture

### 10.1 Data Security

**Implemented**:
- **SQL Injection Prevention**: Parameterized queries only
- **Input Validation**: Pydantic models validate all inputs
- **Hash Verification**: SHA256 for file integrity
- **Immutable Sources**: Frozen dataclasses prevent tampering

**Future Enhancements**:
- Encryption at rest for sensitive data
- TLS/SSL for all network connections
- API authentication (JWT tokens)
- Role-based access control (RBAC)

### 10.2 Application Security

**Implemented**:
- **Dependency Scanning**: Automated vulnerability checks
- **Code Linting**: Security-focused linting rules
- **Type Safety**: Static type checking with mypy
- **Error Handling**: No sensitive data in error messages

**Future Enhancements**:
- Rate limiting for API endpoints
- CORS configuration for web interface
- Content Security Policy (CSP)
- Regular security audits

### 10.3 Infrastructure Security

**Implemented**:
- **Container Isolation**: Docker containers for services
- **Network Segmentation**: Docker networks
- **Secret Management**: Environment variables for secrets
- **Minimal Permissions**: Least privilege principle

**Future Enhancements**:
- Secrets management (HashiCorp Vault)
- Network policies (Kubernetes)
- Container scanning
- Intrusion detection


---

## 11. Monitoring and Observability

### 11.1 Logging Architecture

**Technology**: structlog (structured logging)

**Log Format**: JSON

**Log Levels**:
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages for potential issues
- ERROR: Error messages for failures
- CRITICAL: Critical failures requiring immediate attention

**Log Structure**:
```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "level": "INFO",
  "component": "hansard_scraper",
  "message": "document_downloaded",
  "context": {
    "request_id": "req_123",
    "document_type": "hansard",
    "chamber": "national_assembly",
    "date": "2025-01-01",
    "file_size": 1024000,
    "duration_ms": 1500
  }
}
```

**Features**:
- Request ID tracking across operations
- Context binding for related logs
- Automatic log rotation (daily)
- Log retention (30 days)
- Multiple outputs (stdout, file)

### 11.2 Metrics Architecture

**Technology**: Prometheus

**Metrics Endpoint**: `http://localhost:9090/metrics`

**Key Metrics**:

| Metric | Type | Description |
|--------|------|-------------|
| `documents_processed_total` | Counter | Total documents processed by type/chamber/status |
| `document_processing_seconds` | Histogram | Processing time distribution |
| `errors_total` | Counter | Total errors by component/type |
| `processing_queue_depth` | Gauge | Current queue depth by document type |
| `vector_db_documents_total` | Gauge | Total documents in vector DB by collection |

**Metric Labels**:
- `document_type`: hansard, votes, bills, etc.
- `chamber`: national_assembly, senate
- `status`: success, error, skipped
- `component`: scraper, processor, storage
- `error_type`: Exception class name


### 11.3 Dashboards

**Technology**: Grafana

**Access**: `http://localhost:3000` (admin/admin)

**Pre-configured Dashboards**:

1. **System Overview**
   - Total documents processed
   - Processing success rate
   - Error rate trends
   - Queue depth
   - System health

2. **Processing Metrics**
   - Processing time percentiles (p50, p95, p99)
   - Throughput (documents/hour)
   - Processing by document type
   - Processing by chamber

3. **Error Monitoring**
   - Error count by type
   - Error rate trends
   - Failed documents list
   - Error distribution by component

### 11.4 Error Tracking

**Technology**: Sentry (optional)

**Features**:
- Automatic error capture
- Stack trace collection
- Error grouping and deduplication
- Release tracking
- Performance monitoring
- User context tracking

**Configuration**:
```python
# Enable in production
monitoring:
  sentry_enabled: true
  dsn: ${SENTRY_DSN}
```

### 11.5 Health Checks

**Endpoint**: `/health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "components": {
    "database": "healthy",
    "vector_db": "healthy",
    "disk_space": "healthy"
  },
  "metrics": {
    "documents_processed": 1234,
    "queue_depth": 5,
    "error_rate": 0.01
  }
}
```

---

## 12. Deployment Architecture

### 12.1 Development Environment

**Setup**: Docker Compose

**Services**:
- PostgreSQL (port 5432)
- Qdrant (ports 6333, 6334)
- Prometheus (port 9090)
- Grafana (port 3000)

**Start Command**:
```bash
docker-compose up -d
```

**Features**:
- Automatic service startup
- Health checks
- Volume persistence
- Network isolation


### 12.2 Production Deployment (Future)

**Platform Options**:
1. **AWS**: ECS/Fargate + RDS + S3
2. **GCP**: Cloud Run + Cloud SQL + Cloud Storage
3. **Azure**: Container Instances + Azure Database + Blob Storage
4. **Self-Hosted**: Kubernetes cluster

**Recommended Architecture** (AWS):
```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Cloud                            │
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │  Application │         │  Application │                 │
│  │  Load        │────────▶│  Servers     │                 │
│  │  Balancer    │         │  (ECS)       │                 │
│  └──────────────┘         └──────┬───────┘                 │
│                                   │                          │
│                    ┌──────────────┼──────────────┐          │
│                    │              │              │          │
│                    ▼              ▼              ▼          │
│           ┌──────────────┐ ┌──────────┐ ┌──────────┐      │
│           │  RDS         │ │  Qdrant  │ │  S3      │      │
│           │  PostgreSQL  │ │  Cluster │ │  (PDFs)  │      │
│           └──────────────┘ └──────────┘ └──────────┘      │
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │  CloudWatch  │         │  Secrets     │                 │
│  │  (Metrics)   │         │  Manager     │                 │
│  └──────────────┘         └──────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

**Components**:
- **Load Balancer**: Distribute traffic across application servers
- **ECS/Fargate**: Containerized application deployment
- **RDS PostgreSQL**: Managed database with automatic backups
- **Qdrant Cluster**: Distributed vector search
- **S3**: Object storage for PDFs
- **CloudWatch**: Metrics and logging
- **Secrets Manager**: Secure credential storage

### 12.3 CI/CD Pipeline

**Platform**: GitHub Actions

**Workflow**:
```
┌─────────────┐
│  Git Push   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Lint       │
│  (ruff,     │
│   mypy)     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Test       │
│  (pytest)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Coverage   │
│  (≥90%)     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Build      │
│  (Docker)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Deploy     │
│  (if main)  │
└─────────────┘
```

**Stages**:
1. **Lint**: Code quality checks (ruff, mypy)
2. **Test**: Run all tests (unit, integration, property)
3. **Coverage**: Verify ≥90% code coverage
4. **Build**: Build Docker images
5. **Deploy**: Deploy to production (main branch only)


---

## 13. API Design

### 13.1 Current State

**Phase 0**: No public API (internal library usage only)

**Usage Pattern**:
```python
from hansard_tales.scrapers import HansardScraper
from hansard_tales.processors import PDFProcessor
from hansard_tales.config import get_config

config = get_config()
scraper = HansardScraper(config.scraper)
processor = PDFProcessor()

# Scrape documents
documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY)

# Process PDFs
for doc in documents:
    result = processor.process(doc.path)
```

### 13.2 Future API Design (Phase 2)

**Technology**: FastAPI

**Base URL**: `https://api.hansardtales.ke/v1`

**Endpoints**:

#### Documents
```
GET    /documents                    # List documents
GET    /documents/{id}               # Get document
POST   /documents/search             # Semantic search
GET    /documents/{id}/download      # Download PDF
```

#### Statements
```
GET    /statements                   # List statements
GET    /statements/{id}              # Get statement
POST   /statements/search            # Semantic search
GET    /statements/by-mp/{mp_id}     # Statements by MP
```

#### MPs
```
GET    /mps                          # List MPs
GET    /mps/{id}                     # Get MP
GET    /mps/{id}/statements          # MP's statements
GET    /mps/{id}/votes               # MP's votes
GET    /mps/{id}/bills               # MP's bills
```

#### Bills
```
GET    /bills                        # List bills
GET    /bills/{id}                   # Get bill
GET    /bills/{id}/versions          # Bill versions
GET    /bills/{id}/votes             # Bill votes
```

#### Search
```
POST   /search/semantic              # Semantic search across all
POST   /search/advanced              # Advanced search with filters
```

**Authentication**: JWT tokens (future)

**Rate Limiting**: 100 requests/minute (future)

---

## 14. Anti-Hallucination Architecture

### 14.1 Immutable Source Tracking

**Principle**: Every piece of data must link back to its original source

**Implementation**:

1. **SourceReference Model** (Frozen Dataclass):
```python
@dataclass(frozen=True)
class SourceReference:
    source_url: str          # Original document URL
    source_hash: str         # SHA256 hash
    download_date: datetime  # When downloaded
    page_number: Optional[int]  # Page in PDF
    line_number: Optional[int]  # Line on page
```

2. **All Models Include Source**:
- Document → SourceReference
- Statement → SourceReference
- Bill → SourceReference (per version)
- Vote → SourceReference

3. **Database Constraints**:
- source_hash is UNIQUE
- source_url is NOT NULL
- Foreign keys enforce referential integrity


### 14.2 Verification Chain

**From Analysis → Original PDF**:

```
User Query
    │
    ▼
Statement in Database
    │
    ├─ statement.source.source_url → Original PDF URL
    ├─ statement.source.source_hash → Verify PDF integrity
    ├─ statement.source.page_number → Exact page
    └─ statement.source.line_number → Exact line
    │
    ▼
Original PDF (verifiable)
```

**Benefits**:
- Every claim can be verified
- Detect data corruption (hash mismatch)
- Trace back to original source
- Prevent hallucination in LLM applications

### 14.3 Hash-Based Integrity

**Process**:
1. Download PDF
2. Compute SHA256 hash
3. Store hash in database
4. On retrieval, verify hash matches

**Verification**:
```python
def verify_document_integrity(pdf_path: Path, expected_hash: str) -> bool:
    """Verify PDF hasn't been tampered with."""
    actual_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    return actual_hash == expected_hash
```

### 14.4 Duplicate Prevention

**Mechanism**: Check source_hash before downloading

**Benefits**:
- Avoid redownloading same document
- Prevent duplicate processing
- Save storage space
- Maintain data consistency

**Implementation**:
```python
def is_duplicate(source_hash: str) -> bool:
    """Check if document already exists."""
    existing = session.query(DownloadedFileORM).filter(
        DownloadedFileORM.source_hash == source_hash
    ).first()
    return existing is not None
```

---

## 15. Future Enhancements

### 15.1 Phase 1: Advanced Processing

**Planned Features**:
- MP name extraction and identification
- Statement classification (filler vs substantive)
- Sentiment analysis
- Topic extraction
- Bill-statement linking
- Question-answer matching

**Technology Additions**:
- spaCy for NER
- Transformers for classification
- Topic modeling (LDA/BERTopic)


### 15.2 Phase 2: Analysis Tools

**Planned Features**:
- MP performance dashboards
- Voting pattern analysis
- Bill progress tracking
- Constituency representation metrics
- Party alignment analysis
- Legislative productivity metrics

**Technology Additions**:
- Pandas for data analysis
- Plotly for visualizations
- Jupyter notebooks for exploration

### 15.3 Phase 3: API & Web Interface

**Planned Features**:
- RESTful API (FastAPI)
- Web interface (React/Vue)
- Public data access
- API documentation (OpenAPI)
- Rate limiting
- Authentication

**Technology Additions**:
- FastAPI for API
- React/Vue for frontend
- Redis for caching
- Nginx for reverse proxy

### 15.4 Phase 4: Advanced Features

**Planned Features**:
- Real-time scraping (webhooks)
- Automated report generation
- Email notifications
- Mobile app
- Data exports (CSV, JSON, Excel)
- Historical trend analysis

**Technology Additions**:
- Celery for task queue
- Redis for message broker
- React Native for mobile
- Pandas for exports

---

## Appendix A: Architectural Decision Records (ADRs)

### ADR-001: Use Pydantic for Data Models

**Status**: Accepted

**Context**: Need type-safe data models with validation

**Decision**: Use Pydantic v2 for all data models

**Rationale**:
- Built-in validation
- JSON serialization
- Type hints support
- Excellent documentation
- Active community

**Consequences**:
- Positive: Type safety, validation, serialization
- Negative: Learning curve for team

### ADR-002: Dual Database Strategy

**Status**: Accepted

**Context**: Need both structured data storage and semantic search

**Decision**: Use PostgreSQL + Qdrant (SQLite + ChromaDB for dev)

**Rationale**:
- PostgreSQL: Mature, reliable, ACID compliant
- Qdrant: High-performance vector search
- ChromaDB: Simple development setup
- SQLite: Zero-config development

**Consequences**:
- Positive: Best tool for each job
- Negative: Complexity of managing two databases


### ADR-003: CSS Selectors for Web Scraping

**Status**: Accepted

**Context**: Need reliable way to extract PDF links from parliament.go.ke

**Decision**: Use CSS selectors with BeautifulSoup

**Rationale**:
- More maintainable than XPath
- Easier to read and write
- Less brittle than regex
- Well-supported by BeautifulSoup

**Consequences**:
- Positive: Clean, maintainable code
- Negative: Breaks if HTML structure changes (mitigated by fail-fast)

### ADR-004: Immutable Source References

**Status**: Accepted

**Context**: Need to prevent hallucination in LLM applications

**Decision**: Use frozen dataclasses for SourceReference

**Rationale**:
- Prevents accidental modification
- Ensures data integrity
- Supports verification chain
- Pythonic approach

**Consequences**:
- Positive: Data integrity, verifiability
- Negative: Cannot update source references (by design)

### ADR-005: Property-Based Testing

**Status**: Accepted

**Context**: Need comprehensive test coverage

**Decision**: Use Hypothesis for property-based testing

**Rationale**:
- Finds edge cases automatically
- Complements unit tests
- Industry best practice
- Excellent Python support

**Consequences**:
- Positive: Better test coverage, fewer bugs
- Negative: Longer test execution time

---

## Appendix B: Technology Alternatives Considered

### Database Alternatives

| Technology | Pros | Cons | Decision |
|-----------|------|------|----------|
| **PostgreSQL** | Mature, ACID, JSON support | Requires server | ✅ Chosen (prod) |
| **SQLite** | Zero-config, embedded | Single-writer | ✅ Chosen (dev) |
| **MongoDB** | Flexible schema | No ACID | ❌ Rejected |
| **MySQL** | Popular, mature | Less JSON support | ❌ Rejected |

### Vector Database Alternatives

| Technology | Pros | Cons | Decision |
|-----------|------|------|----------|
| **Qdrant** | Fast, scalable, Rust | Requires server | ✅ Chosen (prod) |
| **ChromaDB** | Simple, embedded | Limited scale | ✅ Chosen (dev) |
| **Pinecone** | Managed, scalable | Vendor lock-in | ❌ Rejected |
| **Weaviate** | Feature-rich | Complex setup | ❌ Rejected |
| **Milvus** | Scalable | Heavy resource use | ❌ Rejected |


### Embedding Model Alternatives

| Model | Dimension | Speed | Quality | Decision |
|-------|-----------|-------|---------|----------|
| **all-MiniLM-L6-v2** | 384 | Fast | Good | ✅ Chosen |
| **all-mpnet-base-v2** | 768 | Medium | Better | ❌ Too slow |
| **text-embedding-ada-002** | 1536 | API | Best | ❌ Cost/API |
| **instructor-large** | 768 | Slow | Better | ❌ Too slow |

### Web Scraping Alternatives

| Technology | Pros | Cons | Decision |
|-----------|------|------|----------|
| **requests + BeautifulSoup** | Simple, fast | No JS | ✅ Chosen |
| **Scrapy** | Feature-rich | Overkill | ❌ Too complex |
| **Selenium** | JS support | Slow, heavy | ❌ Not needed |
| **Playwright** | Modern, fast | Complex | ❌ Not needed |

---

## Appendix C: Performance Benchmarks

### Scraping Performance

| Operation | Time | Throughput |
|-----------|------|------------|
| Fetch single page | 1-2s | - |
| Extract PDF links | <100ms | - |
| Download single PDF | 2-5s | - |
| Full Hansard scrape (452 PDFs) | ~30min | 15 PDFs/min |

### Processing Performance

| Operation | Time | Throughput |
|-----------|------|------------|
| Extract text (10-page PDF) | 1-2s | - |
| Generate embedding | 50-100ms | 10-20/sec |
| Store in SQL | 10-20ms | - |
| Store in vector DB | 20-50ms | - |
| Full processing pipeline | 2-3s/PDF | 20-30 PDFs/min |

### Search Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Vector search (top-10) | 10-50ms | ChromaDB |
| Vector search (top-10) | 5-20ms | Qdrant |
| SQL query (simple) | 1-5ms | With indexes |
| SQL query (complex join) | 10-50ms | With indexes |

---

## Appendix D: Glossary

| Term | Definition |
|------|------------|
| **Chamber** | Either National Assembly or Senate |
| **Document** | Any parliamentary document (Hansard, Bill, Vote, etc.) |
| **Embedding** | Numerical representation of text for semantic similarity |
| **Hansard** | Official record of parliamentary debates |
| **MP** | Member of Parliament (National Assembly or Senate) |
| **ORM** | Object-Relational Mapping (SQLAlchemy) |
| **Parliament Term** | 5-year period (e.g., 13th Parliament: 2022-2027) |
| **RAG** | Retrieval-Augmented Generation (context retrieval for LLM) |
| **Source Hash** | SHA256 hash of original PDF for integrity verification |
| **Vector Database** | Database storing document embeddings for semantic search |

---

## Appendix E: References

### Documentation
- [README.md](../README.md) - Project overview and setup
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development guidelines
- [MONITORING.md](MONITORING.md) - Monitoring setup
- [SENTRY_SETUP.md](SENTRY_SETUP.md) - Error tracking setup

### External Resources
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [sentence-transformers Documentation](https://www.sbert.net/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

---

**Document Version**: 1.0
**Last Updated**: January 2025
**Maintained By**: Hansard Tales Development Team
**Status**: Phase 0 Complete
