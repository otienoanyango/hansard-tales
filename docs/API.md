# Hansard Tales API Documentation

## Overview

This document provides comprehensive API documentation for the Hansard Tales system. The system is designed as a library with modular components that can be used independently or together.

## Table of Contents

1. [Configuration](#configuration)
2. [Data Models](#data-models)
3. [Database Operations](#database-operations)
4. [Vector Database](#vector-database)
5. [Web Scrapers](#web-scrapers)
6. [PDF Processing](#pdf-processing)
7. [Monitoring & Metrics](#monitoring--metrics)
8. [Error Handling](#error-handling)

---

## Configuration

### Settings Module

```python
from hansard_tales.config.settings import Settings

# Load configuration
settings = Settings()

# Access configuration
db_url = settings.database_url
vector_db_path = settings.vector_db_path
```

#### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `database_url` | str | `sqlite:///data/hansard.db` | Database connection string |
| `vector_db_path` | str | `data/vector_db` | Vector database storage path |
| `vector_db_engine` | str | `chromadb` | Vector DB engine (chromadb/qdrant) |
| `embedding_model` | str | `all-MiniLM-L6-v2` | Sentence transformer model |
| `log_level` | str | `INFO` | Logging level |
| `prometheus_port` | int | `9090` | Prometheus metrics port |
| `sentry_dsn` | str | `None` | Sentry DSN for error tracking |

---

## Data Models

### Pydantic Models

All data models are defined using Pydantic for validation and serialization.

#### Document

```python
from hansard_tales.models import Document, Chamber, DocumentType
from datetime import date

doc = Document(
    type=DocumentType.HANSARD,
    chamber=Chamber.NATIONAL_ASSEMBLY,
    title="Hansard Report - Tuesday, 4th November 2025",
    date=date(2025, 11, 4),
    parliament_term=13,
    source_url="https://parliament.go.ke/...",
    source_hash="abc123...",
    vector_doc_id="doc_001"
)
```

#### Statement

```python
from hansard_tales.models import Statement
from uuid import uuid4

statement = Statement(
    document_id=uuid4(),
    mp_id=uuid4(),
    text="The honorable member raises an important point...",
    source_url="https://parliament.go.ke/...",
    source_hash="def456...",
    vector_doc_id="stmt_001"
)
```

#### Bill

```python
from hansard_tales.models import Bill, BillStatus

bill = Bill(
    bill_number="Bill No. 42 of 2025",
    title="The Climate Change Amendment Bill, 2025",
    chamber=Chamber.NATIONAL_ASSEMBLY,
    status=BillStatus.SECOND_READING,
    sponsor_id=uuid4(),
    topics=["environment", "climate"]
)
```

### ORM Models

SQLAlchemy ORM models for database operations.

```python
from hansard_tales.database.models import DocumentORM, StatementORM, BillORM
from hansard_tales.database.base import get_session

# Create session
session = get_session()

# Query documents
documents = session.query(DocumentORM).filter(
    DocumentORM.chamber == "national_assembly",
    DocumentORM.date >= date(2025, 1, 1)
).all()

# Insert statement
statement_orm = StatementORM(
    document_id=doc.id,
    mp_id=mp.id,
    text="Statement text...",
    source_url="https://...",
    source_hash="hash...",
    vector_doc_id="vec_001"
)
session.add(statement_orm)
session.commit()
```

---

## Database Operations

### Session Management

```python
from hansard_tales.database.base import get_session, init_db

# Initialize database (create tables)
init_db()

# Get session
with get_session() as session:
    # Perform operations
    documents = session.query(DocumentORM).all()
```

### Migrations

```python
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new table"

# Rollback migration
alembic downgrade -1
```

---

## Vector Database

### Initialization

```python
from hansard_tales.vector_db import create_vector_db, EmbeddingGenerator
from hansard_tales.config.settings import Settings

settings = Settings()

# Create vector DB
vector_db = create_vector_db(
    engine=settings.vector_db_engine,
    path=settings.vector_db_path
)

# Create embedding generator
embedder = EmbeddingGenerator(model_name=settings.embedding_model)
```

### Operations

#### Insert Document

```python
# Generate embedding
text = "Parliamentary statement text..."
embedding = embedder.generate(text)

# Insert into vector DB
vector_db.insert(
    collection="statements",
    id="stmt_001",
    vector=embedding,
    payload={
        "document_id": str(doc.id),
        "mp_id": str(mp.id),
        "chamber": "national_assembly",
        "date": "2025-11-04"
    },
    text=text
)
```

#### Search

```python
# Search for similar documents
query = "climate change legislation"
query_embedding = embedder.generate(query)

results = vector_db.search(
    collection="statements",
    query_vector=query_embedding,
    limit=10,
    filter={"chamber": "national_assembly"}
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Text: {result.text}")
    print(f"Metadata: {result.payload}")
```

---

## Web Scrapers

### Hansard Scraper

```python
from hansard_tales.scrapers import create_scraper, Chamber
from hansard_tales.config.settings import Settings
from datetime import date

settings = Settings()

# Create scraper
scraper = create_scraper("hansard", settings)

# Scrape documents
documents = scraper.scrape(
    chamber=Chamber.NATIONAL_ASSEMBLY,
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31),
    skip_existing=True
)

# Save documents
for doc in documents:
    output_path = scraper.save_document(
        doc,
        output_dir=settings.pdf_download_dir
    )
    print(f"Saved: {output_path}")
```

### Votes Scraper

```python
# Create votes scraper
scraper = create_scraper("votes", settings)

# Scrape votes
documents = scraper.scrape(
    chamber=Chamber.NATIONAL_ASSEMBLY,
    parliament_term=2022
)
```

### Custom Scraper

```python
from hansard_tales.scrapers.base import BaseScraper

class CustomScraper(BaseScraper):
    def get_document_urls(self, chamber, start_date=None, end_date=None):
        # Implement URL extraction
        return ["https://..."]

    def extract_metadata(self, url, content):
        # Implement metadata extraction
        return {"document_type": "custom"}
```

---

## PDF Processing

### PDF Processor

```python
from hansard_tales.processors import PDFProcessor
from pathlib import Path

processor = PDFProcessor()

# Extract text from PDF
pdf_path = Path("data/pdfs/hansard_20251104_P.pdf")
text = processor.extract_text(pdf_path)

# Extract with page numbers
pages = processor.extract_pages(pdf_path)
for page_num, page_text in enumerate(pages, 1):
    print(f"Page {page_num}: {page_text[:100]}...")
```

### Storage Service

```python
from hansard_tales.processors import StorageService

storage = StorageService(base_path="data/pdfs")

# Save document
file_path = storage.save(
    content=pdf_bytes,
    filename="hansard_20251104_P.pdf",
    document_type="hansard"
)

# Check if exists
exists = storage.exists("hansard_20251104_P.pdf")

# Get file path
path = storage.get_path("hansard_20251104_P.pdf")
```

---

## Monitoring & Metrics

### Prometheus Metrics

```python
from hansard_tales.monitoring.metrics import (
    documents_processed,
    processing_time,
    error_counter
)

# Increment counter
documents_processed.labels(document_type="hansard").inc()

# Record timing
with processing_time.labels(operation="scraping").time():
    # Perform operation
    scraper.scrape(...)

# Record error
error_counter.labels(error_type="network_error").inc()
```

### Health Checks

```python
from hansard_tales.monitoring.health import HealthCheck

health = HealthCheck()

# Check database
db_status = health.check_database()

# Check vector DB
vector_status = health.check_vector_db()

# Get overall status
status = health.get_status()
print(status)  # {"status": "healthy", "checks": {...}}
```

### Sentry Integration

```python
from hansard_tales.monitoring.sentry_config import init_sentry

# Initialize Sentry
init_sentry(dsn="https://...", environment="production")

# Errors are automatically captured
try:
    risky_operation()
except Exception as e:
    # Automatically sent to Sentry
    raise
```

---

## Error Handling

### Custom Exceptions

```python
from hansard_tales.utils.errors import (
    DataCollectionError,
    ProcessingError,
    StorageError
)

# Raise custom exception
raise DataCollectionError(
    "Failed to scrape documents",
    context={"url": "https://...", "status_code": 404}
)
```

### Retry Logic

```python
from hansard_tales.utils.retry import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=1.0)
def unstable_operation():
    # Operation that might fail
    response = requests.get("https://...")
    response.raise_for_status()
    return response.json()
```

### Batch Processing

```python
from hansard_tales.utils.batch import BatchProcessor

processor = BatchProcessor(
    batch_size=10,
    max_workers=4,
    continue_on_error=True
)

def process_item(item):
    # Process single item
    return result

results = processor.process(items, process_item)

# Check results
print(f"Successful: {results.successful}")
print(f"Failed: {results.failed}")
print(f"Errors: {results.errors}")
```

---

## Usage Examples

### Complete Workflow

```python
from hansard_tales.config.settings import Settings
from hansard_tales.scrapers import create_scraper
from hansard_tales.processors import PDFProcessor, StorageService
from hansard_tales.vector_db import create_vector_db, EmbeddingGenerator
from hansard_tales.database.base import get_session
from hansard_tales.database.models import DocumentORM
from hansard_tales.models import Chamber
from datetime import date, datetime

# 1. Initialize
settings = Settings()
scraper = create_scraper("hansard", settings)
processor = PDFProcessor()
storage = StorageService()
vector_db = create_vector_db(settings.vector_db_engine, settings.vector_db_path)
embedder = EmbeddingGenerator(settings.embedding_model)

# 2. Scrape documents
documents = scraper.scrape(
    chamber=Chamber.NATIONAL_ASSEMBLY,
    start_date=date(2025, 11, 1),
    end_date=date(2025, 11, 30)
)

# 3. Process and store
with get_session() as session:
    for doc in documents:
        # Save PDF
        file_path = storage.save(doc.content, doc.filename, "hansard")

        # Extract text
        text = processor.extract_text(file_path)

        # Generate embedding
        embedding = embedder.generate(text)

        # Store in vector DB
        vector_id = f"doc_{doc.hash[:8]}"
        vector_db.insert(
            collection="documents",
            id=vector_id,
            vector=embedding,
            payload=doc.metadata,
            text=text
        )

        # Store in database
        doc_orm = DocumentORM(
            type="hansard",
            chamber="national_assembly",
            title=doc.metadata.get("title", ""),
            date=date.fromisoformat(doc.metadata["date"]),
            parliament_term=13,
            source_url=doc.url,
            source_hash=doc.hash,
            download_date=datetime.utcnow(),
            vector_doc_id=vector_id,
            metadata=doc.metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(doc_orm)

    session.commit()

print(f"Processed {len(documents)} documents")
```

---

## Testing

### Unit Tests

```python
import pytest
from hansard_tales.scrapers import create_scraper

def test_scraper_creation():
    scraper = create_scraper("hansard", settings)
    assert scraper is not None

def test_document_extraction():
    scraper = create_scraper("hansard", settings)
    urls = scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY)
    assert len(urls) > 0
```

### Property-Based Tests

```python
from hypothesis import given, strategies as st
from hansard_tales.models import Document

@given(st.text(min_size=1, max_size=500))
def test_document_title_validation(title):
    """Document titles should always be valid."""
    doc = Document(
        type="hansard",
        chamber="national_assembly",
        title=title,
        date=date.today(),
        parliament_term=13,
        source_url="https://...",
        source_hash="hash",
        vector_doc_id="vec_001"
    )
    assert doc.title == title
```

---

## Performance Considerations

### Batch Operations

- Use `BatchProcessor` for parallel processing
- Configure `max_workers` based on CPU cores
- Enable `continue_on_error` for resilience

### Database Optimization

- Use indexes on frequently queried columns
- Batch inserts with `session.bulk_insert_mappings()`
- Use connection pooling for concurrent access

### Vector Search

- Limit search results to reasonable numbers (10-100)
- Use metadata filters to narrow search space
- Cache embeddings for frequently queried texts

---

## Security

### API Keys

Store sensitive configuration in environment variables:

```bash
export SENTRY_DSN="https://..."
export DATABASE_PASSWORD="..."
```

### Input Validation

All inputs are validated using Pydantic models:

```python
from pydantic import ValidationError

try:
    doc = Document(**data)
except ValidationError as e:
    print(f"Validation error: {e}")
```

---

## Support

For issues, questions, or contributions:

- GitHub Issues: https://github.com/yourusername/hansard-tales/issues
- Documentation: https://github.com/yourusername/hansard-tales/docs
- Contributing: See CONTRIBUTING.md

---

## Version History

- **v0.1.0** (2025-01-01): Initial release with core functionality
  - Web scrapers for Hansard and Votes
  - PDF processing pipeline
  - Vector database integration
  - Monitoring and metrics
