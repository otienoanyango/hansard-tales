# Hansard Tales

**Parliamentary Data Analysis System for Kenya's National Assembly and Senate**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](htmlcov/index.html)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Contributing](#contributing)
- [Documentation](#documentation)
- [License](#license)

---

## Overview

Hansard Tales is a comprehensive system for collecting, processing, and analyzing Kenyan parliamentary data. It provides automated tools for scraping parliament.go.ke, processing parliamentary documents (Hansard records, bills, votes, questions, petitions), and performing semantic search and analysis.

### Key Capabilities

- **Automated Data Collection**: Scrapes National Assembly and Senate documents with duplicate detection
- **Intelligent Processing**: Extracts text, metadata, and entities from PDF documents
- **Semantic Search**: Vector-based document retrieval using sentence embeddings
- **Source Tracking**: Immutable source references for anti-hallucination (every piece of data links back to original PDFs)
- **Performance Analysis**: Track MP contributions, voting patterns, and legislative activity
- **Production-Ready**: Comprehensive monitoring, logging, and error handling

---

## Features

### Data Collection
- ✅ **Automated Scrapers** for parliament.go.ke (Hansard, Votes & Proceedings)
- ✅ **Pagination Support** - Fetches all available documents across multiple pages
- ✅ **Duplicate Detection** - SHA256 hash-based deduplication
- ✅ **Rate Limiting** - Configurable delays to avoid server issues
- ✅ **Standardized Filenames** - Consistent naming for downloaded documents
- ✅ **Metadata Extraction** - Automatic extraction of dates, sessions, and document types

### Document Processing
- ✅ **PDF Text Extraction** - Multi-column layout support
- ✅ **Page & Line Tracking** - Precise source location for every piece of text
- ✅ **Entity Recognition** - MP names, bills, questions, petitions
- ✅ **Batch Processing** - Parallel processing with error recovery

### Semantic Search
- ✅ **Vector Embeddings** - sentence-transformers (all-MiniLM-L6-v2)
- ✅ **Dual Database Support** - ChromaDB (dev) / Qdrant (prod)
- ✅ **Metadata Filtering** - Filter by chamber, date, MP, document type
- ✅ **RAG-Ready** - Context retrieval for LLM applications

### Data Storage
- ✅ **Relational Database** - PostgreSQL (prod) / SQLite (dev)
- ✅ **Vector Database** - Qdrant (prod) / ChromaDB (dev)
- ✅ **Schema Migrations** - Alembic for version control
- ✅ **Type Safety** - Pydantic models with validation

### Monitoring & Observability
- ✅ **Structured Logging** - JSON logs with request IDs
- ✅ **Metrics** - Prometheus metrics for processing, errors, queue depth
- ✅ **Dashboards** - Grafana dashboards for system health
- ✅ **Error Tracking** - Sentry integration (optional)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Configuration Layer                          │
│  config.yaml → Environment Variables → Validated Config Object  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Models Layer                           │
│  Pydantic Models: Document, Statement, Bill, Vote, Question...  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │  SQLAlchemy ORM  │         │  Vector DB       │             │
│  │  (PostgreSQL/    │         │  (Qdrant/        │             │
│  │   SQLite)        │         │   ChromaDB)      │             │
│  └──────────────────┘         └──────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Collection Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Hansard     │  │  Votes       │  │  Bills       │  ...    │
│  │  Scraper     │  │  Scraper     │  │  Scraper     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Processing Layer                              │
│  PDF Parser → Entity Extractor → Embedding Generator            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Observability Layer                           │
│  Structured Logging + Metrics + Error Tracking                  │
└─────────────────────────────────────────────────────────────────┘
```

### Project Structure

```
hansard-tales/
├── hansard_tales/          # Main package
│   ├── config/            # Configuration management
│   ├── models/            # Pydantic data models
│   ├── database/          # SQLAlchemy ORM models
│   ├── scrapers/          # Web scrapers (Hansard, Votes, Bills)
│   ├── processors/        # PDF and document processors
│   ├── vector_db/         # Vector database adapters
│   ├── monitoring/        # Metrics and logging
│   └── utils/             # Utility functions
├── tests/                 # Test suite
│   ├── unit/             # Unit tests (90%+ coverage)
│   ├── integration/      # Integration tests
│   └── property/         # Property-based tests (Hypothesis)
├── config/                # Configuration files
│   ├── environments/     # Environment-specific configs
│   ├── grafana/          # Grafana dashboards
│   └── prometheus.yml    # Prometheus configuration
├── data/                  # Data storage (gitignored)
│   ├── pdfs/             # Downloaded PDFs
│   ├── vector_db/        # Vector database storage
│   └── logs/             # Application logs
├── docs/                  # Documentation
│   ├── ARCHITECTURE.md   # System architecture
│   ├── MONITORING.md     # Monitoring setup
│   └── SENTRY_SETUP.md   # Sentry configuration
├── alembic/              # Database migrations
├── scripts/              # Utility scripts
└── examples/             # Usage examples
```

---

## Installation

### Prerequisites

- **Python 3.12+** (3.10+ supported)
- **Virtual environment** (venv or conda)
- **Docker & Docker Compose** (for development services)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/hansard-tales.git
cd hansard-tales

# Run automated setup (creates venv, installs dependencies)
bash setup.sh

# Or manual setup:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Dependencies

Core dependencies include:
- **pydantic** (2.5+) - Data validation and settings
- **sqlalchemy** (2.0+) - ORM for relational database
- **alembic** (1.13+) - Database migrations
- **chromadb** (0.4+) / **qdrant-client** (1.7+) - Vector databases
- **sentence-transformers** (2.2+) - Embedding generation
- **PyMuPDF** / **pdfplumber** - PDF processing
- **requests** / **beautifulsoup4** - Web scraping
- **prometheus-client** - Metrics
- **sentry-sdk** - Error tracking (optional)

See [requirements.txt](requirements.txt) for complete list.

---

## Quick Start

### 1. Start Development Services

```bash
# Start PostgreSQL, Qdrant, Prometheus, Grafana
make docker-up

# Wait for services to be ready (10 seconds)
# Run database migrations
make migrate
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# For development, defaults work out of the box
```

### 3. Run Your First Scrape

```python
from hansard_tales.scrapers import HansardScraper
from hansard_tales.config import Config
from hansard_tales.models import Chamber

# Load configuration
config = Config()

# Create scraper
scraper = HansardScraper(config.scraper)

# Scrape Hansard documents
documents = scraper.scrape(
    chamber=Chamber.NATIONAL_ASSEMBLY,
    skip_existing=True  # Skip already downloaded files
)

print(f"Downloaded {len(documents)} documents")
```

### 4. Process PDFs

```python
from hansard_tales.processors import PDFProcessor
from pathlib import Path

# Create processor
processor = PDFProcessor()

# Process a PDF
result = processor.process(Path("data/pdfs/hansard_20251104_P.pdf"))

print(f"Extracted {len(result.statements)} statements")
print(f"Processing time: {result.processing_time:.2f}s")
```

### 5. Semantic Search

```python
from hansard_tales.vector_db import create_vector_db
from hansard_tales.vector_db.embeddings import EmbeddingGenerator

# Create vector DB and embedding generator
vector_db = create_vector_db(config.vector_db)
embedder = EmbeddingGenerator(config.embedding)

# Search for similar documents
query = "What is the government's position on healthcare funding?"
query_embedding = embedder.generate(query)

results = vector_db.search(
    collection="statements",
    query_vector=query_embedding,
    limit=10,
    filter={"chamber": "national_assembly"}
)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Text: {result.text[:200]}...")
    print(f"Source: {result.payload['source_url']}")
    print()
```

---

## Usage Examples

### Example 1: Scrape All Hansard Documents

```python
from hansard_tales.scrapers import HansardScraper
from hansard_tales.config import Config
from hansard_tales.models import Chamber
from datetime import date

config = Config()
scraper = HansardScraper(config.scraper)

# Scrape all documents from 13th Parliament (2022-present)
documents = scraper.scrape(
    chamber=Chamber.NATIONAL_ASSEMBLY,
    skip_existing=True
)

# Save to disk
for doc in documents:
    output_path = scraper.save_document(doc, config.scraper.download_dir)
    print(f"Saved: {output_path}")
```

### Example 2: Batch Process PDFs

```python
from hansard_tales.processors import PDFProcessor
from hansard_tales.utils.batch import BatchProcessor
from pathlib import Path

# Get all PDFs
pdf_dir = Path("data/pdfs")
pdf_files = list(pdf_dir.glob("hansard_*.pdf"))

# Create batch processor
processor = PDFProcessor()
batch = BatchProcessor(max_workers=4)

# Process in parallel
results = batch.process_batch(
    items=pdf_files,
    process_func=processor.process,
    continue_on_error=True
)

# Print summary
successful = [r for r in results if r.status == "success"]
failed = [r for r in results if r.status == "error"]

print(f"Processed: {len(successful)}/{len(pdf_files)}")
print(f"Failed: {len(failed)}")
```

### Example 3: Store Documents in Database

```python
from hansard_tales.database import get_session
from hansard_tales.database.models import DocumentORM
from hansard_tales.processors.storage_service import StorageService
from datetime import datetime

# Create storage service
storage = StorageService(config)

# Store processed document
with get_session() as session:
    doc = DocumentORM(
        type="hansard",
        chamber="national_assembly",
        title="Hansard Report - Tuesday, 4th November 2025 (P)",
        date=datetime(2025, 11, 4).date(),
        parliament_term=13,
        source_url="https://parliament.go.ke/...",
        source_hash="abc123...",
        download_date=datetime.utcnow(),
        vector_doc_id="doc_123",
        metadata={"period": "P"}
    )

    session.add(doc)
    session.commit()

    print(f"Stored document: {doc.id}")
```

### Example 4: Query Database

```python
from hansard_tales.database import get_session
from hansard_tales.database.models import DocumentORM, StatementORM
from sqlalchemy import and_

with get_session() as session:
    # Get all Hansard documents from November 2025
    documents = session.query(DocumentORM).filter(
        and_(
            DocumentORM.type == "hansard",
            DocumentORM.date >= "2025-11-01",
            DocumentORM.date < "2025-12-01"
        )
    ).all()

    print(f"Found {len(documents)} documents")

    # Get statements by specific MP
    statements = session.query(StatementORM).filter(
        StatementORM.mp_id == "mp_uuid_here"
    ).limit(10).all()

    for stmt in statements:
        print(f"Statement: {stmt.text[:100]}...")
```

---

## Configuration

### Configuration Files

The system uses YAML configuration files with environment-specific overrides:

```yaml
# config/environments/development.yaml
environment: development

database:
  engine: sqlite
  database: data/hansard_dev

vector_db:
  engine: chromadb
  persist_directory: data/vector_db_dev

scraper:
  base_url: https://parliament.go.ke
  download_dir: data/pdfs
  max_retries: 3
  retry_delay: 1.0
  timeout: 30

logging:
  level: DEBUG
  format: text
  output: stdout

monitoring:
  prometheus_enabled: false
  sentry_enabled: false
```

### Environment Variables

Override configuration using environment variables with `__` delimiter:

```bash
# Database configuration
export DB__ENGINE=postgresql
export DB__HOST=localhost
export DB__PORT=5432
export DB__PASSWORD=secret

# Vector DB configuration
export VECTOR_DB__ENGINE=qdrant
export VECTOR_DB__HOST=localhost

# Monitoring
export SENTRY__DSN=https://your-sentry-dsn
export SENTRY__ENABLED=true
```

### Configuration Options

| Section | Option | Default | Description |
|---------|--------|---------|-------------|
| **database** | engine | sqlite | Database engine (sqlite/postgresql) |
| | host | localhost | Database host |
| | port | 5432 | Database port |
| | database | hansard_tales | Database name |
| **vector_db** | engine | chromadb | Vector DB (chromadb/qdrant) |
| | host | localhost | Vector DB host |
| | port | 6333 | Vector DB port |
| **scraper** | base_url | parliament.go.ke | Parliament website URL |
| | max_retries | 3 | Max retry attempts |
| | retry_delay | 1.0 | Delay between retries (seconds) |
| | timeout | 30 | Request timeout (seconds) |
| **logging** | level | INFO | Log level (DEBUG/INFO/WARNING/ERROR) |
| | format | json | Log format (json/text) |
| | output | both | Log output (stdout/file/both) |
| **monitoring** | prometheus_enabled | true | Enable Prometheus metrics |
| | sentry_enabled | false | Enable Sentry error tracking |

---

## Development Setup

### 1. Install Development Dependencies

```bash
# Install with development extras
pip install -e .[dev]

# Or install from requirements-dev.txt
pip install -r requirements-dev.txt
```

### 2. Start Development Services

```bash
# Start all services (PostgreSQL, Qdrant, Prometheus, Grafana)
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down

# Stop and remove volumes (clean slate)
make docker-clean
```

### 3. Run Database Migrations

```bash
# Run all pending migrations
make migrate

# Create a new migration
make migrate-create
# Enter migration name when prompted
```

### 4. Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### 5. Development Workflow

```bash
# Format code
make format

# Run linters
make lint

# Run tests
make test

# Run tests with coverage
make coverage

# Clean generated files
make clean
```

### Available Make Commands

```bash
make help              # Show all available commands

# Setup
make install           # Install dependencies
make dev-setup         # Setup development environment
make setup             # Run full setup (venv + install)

# Testing
make test              # Run all tests
make test-unit         # Run unit tests only
make test-property     # Run property-based tests only
make test-integration  # Run integration tests only
make coverage          # Run tests with coverage report

# Code Quality
make lint              # Run linters (ruff, mypy)
make format            # Format code with ruff

# Database
make migrate           # Run database migrations
make migrate-create    # Create new migration

# Docker
make docker-up         # Start Docker services
make docker-down       # Stop Docker services
make docker-logs       # View Docker logs
make docker-clean      # Stop and remove Docker volumes

# Cleanup
make clean             # Remove generated files
```

---

## Testing

### Test Structure

```
tests/
├── unit/              # Unit tests (fast, isolated)
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_scrapers.py
│   └── test_processors.py
├── integration/       # Integration tests (slower, multiple components)
│   ├── test_scraper_integration.py
│   └── test_storage_integration.py
└── property/          # Property-based tests (Hypothesis)
    ├── test_model_properties.py
    └── test_scraper_properties.py
```

### Running Tests

```bash
# Run all tests (recommended for CI/CD)
./scripts/run_all_tests.sh

# Or run manually with proper isolation:
# 1. Run main test suite (excluding Sentry isolated tests)
pytest -m "not sentry_isolated" --cov=hansard_tales --cov-report=xml --cov-report=term

# 2. Run Sentry isolated tests separately
pytest -m "sentry_isolated" --cov=hansard_tales --cov-append --cov-report=xml --cov-report=term

# Run all tests together (may have test isolation issues in CI)
pytest

# Run specific test categories
pytest tests/unit/              # Unit tests only
pytest tests/property/          # Property-based tests only
pytest tests/integration/       # Integration tests only

# Run specific test file
pytest tests/unit/test_scrapers.py

# Run specific test
pytest tests/unit/test_scrapers.py::TestHansardScraper::test_scrape_success

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=hansard_tales --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

**Note**: Sentry configuration tests are marked with `@pytest.mark.sentry_isolated` and should be run separately from the main test suite to avoid logging capture issues in CI/CD environments. The `run_all_tests.sh` script handles this automatically.

### Test Coverage

- **Target**: ≥90% code coverage
- **Current**: 90%+ across all modules
- **Coverage Report**: Generated in `htmlcov/` directory

### Writing Tests

Follow the testing guidelines in [testing-guidelines.md](.kiro/rules/testing-guidelines.md):

1. **Unit Tests**: Test individual functions in isolation
2. **Property-Based Tests**: Test universal invariants with Hypothesis
3. **Integration Tests**: Test multiple components working together
4. **Fixtures**: Use pytest fixtures for test data
5. **Mocking**: Mock external dependencies (network, filesystem)

Example:

```python
import pytest
from hypothesis import given, strategies as st
from hansard_tales.scrapers import HansardScraper

class TestHansardScraper:
    """Test suite for Hansard scraper."""

    def test_scrape_success(self, mock_requests):
        """Test successful scraping."""
        # Arrange
        scraper = HansardScraper(config)

        # Act
        documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY)

        # Assert
        assert len(documents) > 0
        assert all(doc.hash for doc in documents)

    @given(st.text())
    def test_filename_generation_never_crashes(self, url):
        """Filename generation should never crash."""
        scraper = HansardScraper(config)
        filename = scraper._generate_filename(url)
        assert isinstance(filename, str)
```

---

## Monitoring

### Prometheus Metrics

Access Prometheus at http://localhost:9090

Available metrics:
- `hansard_documents_processed_total` - Total documents processed
- `hansard_processing_time_seconds` - Processing time histogram
- `hansard_errors_total` - Total errors by type
- `hansard_queue_depth` - Current queue depth

### Grafana Dashboards

Access Grafana at http://localhost:3000 (admin/admin)

Pre-configured dashboards:
- **System Overview** - High-level system health
- **Processing Metrics** - Document processing performance
- **Error Monitoring** - Error rates and types

See [docs/MONITORING.md](docs/MONITORING.md) for detailed setup.

### Sentry Error Tracking

Optional Sentry integration for error tracking:

```bash
# Enable Sentry
export SENTRY__ENABLED=true
export SENTRY__DSN=https://your-sentry-dsn

# Or in config/environments/production.yaml
monitoring:
  sentry_enabled: true
  sentry_dsn: ${SENTRY_DSN}
```

See [docs/SENTRY_SETUP.md](docs/SENTRY_SETUP.md) for configuration.

### Structured Logging

Logs are written in JSON format with request IDs for tracing:

```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "level": "INFO",
  "component": "hansard_scraper",
  "message": "Downloaded document",
  "context": {
    "request_id": "req_123",
    "url": "https://parliament.go.ke/...",
    "hash": "abc123..."
  }
}
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development workflow
- Code style guidelines
- Testing requirements
- Pull request process

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Write tests (maintain ≥90% coverage)
5. Run tests and linters: `make test && make lint`
6. Commit with clear message: `git commit -m "feat: add feature"`
7. Push and create pull request

---

## Documentation

### Available Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design decisions
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[MONITORING.md](docs/MONITORING.md)** - Monitoring and observability setup
- **[SENTRY_SETUP.md](docs/SENTRY_SETUP.md)** - Sentry error tracking configuration
- **[testing-guidelines.md](.kiro/rules/testing-guidelines.md)** - Testing best practices
- **[code-style.md](.kiro/rules/code-style.md)** - Code style guide

### API Documentation

API documentation is generated from docstrings. All public functions and classes include comprehensive docstrings with:
- Description
- Parameters
- Return values
- Exceptions
- Examples

---

## Project Status

**Phase 0: Foundation** - ✅ Complete

- ✅ Project setup and configuration
- ✅ Data models and database schema
- ✅ Vector database integration
- ✅ Web scrapers (Hansard, Votes & Proceedings)
- ✅ PDF processing pipeline
- ✅ Logging and error handling
- ✅ Testing infrastructure (90%+ coverage)
- ✅ CI/CD pipeline
- ✅ Development environment
- ✅ Monitoring setup

**Next Phases**:
- Phase 1: Advanced Processing (Entity extraction, classification)
- Phase 2: Analysis Tools (MP performance, voting patterns)
- Phase 3: API & Web Interface

---

## License

[License information to be added]

---

## Contact & Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/hansard-tales/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/hansard-tales/discussions)
- **Email**: [your-email@example.com]

---

## Acknowledgments

- Parliament of Kenya for providing public access to parliamentary documents
- Open source community for the excellent tools and libraries

---

**Built with ❤️ for transparency and accountability in Kenyan governance**
