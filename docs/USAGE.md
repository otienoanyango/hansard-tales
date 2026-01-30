# Usage Guide

**Version**: 1.0 (Phase 1)
**Last Updated**: January 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Basic Usage](#basic-usage)
3. [Phase 1 Components](#phase-1-components)
4. [Common Workflows](#common-workflows)
5. [Command-Line Tools](#command-line-tools)
6. [Python API](#python-api)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

---

## Overview

Hansard Tales provides tools for:
- **Data Collection**: Scraping parliamentary documents
- **Document Processing**: Extracting text and metadata from PDFs
- **NLP Analysis**: MP identification, statement segmentation, sentiment analysis
- **LLM Analysis**: Quality scoring, topic classification, citation verification
- **Static Site Generation**: Creating browsable HTML site

---

## Basic Usage

### 1. Scrape Documents

```python
from hansard_tales.scrapers import HansardScraper
from hansard_tales.config import get_config
from hansard_tales.models import Chamber

config = get_config()
scraper = HansardScraper(config.scraper)

# Scrape all Hansard documents
documents = scraper.scrape(
    chamber=Chamber.NATIONAL_ASSEMBLY,
    skip_existing=True
)

print(f"Downloaded {len(documents)} documents")
```

### 2. Process PDFs

```python
from hansard_tales.processors import PDFProcessor
from pathlib import Path

processor = PDFProcessor()

# Process single PDF
result = processor.process(Path("data/pdfs/hansard_20251104_P.pdf"))
print(f"Extracted {len(result.statements)} statements")
```

### 3. Run Analysis Pipeline

```python
from hansard_tales.pipeline import ProcessingPipeline

pipeline = ProcessingPipeline(config)

# Process Hansard document through full pipeline
result = pipeline.process_hansard("data/pdfs/hansard_20251104_P.pdf")

print(f"Statements: {result.statements_count}")
print(f"Substantive: {result.substantive_count}")
print(f"Quality avg: {result.avg_quality_score:.1f}")
```

### 4. Generate Static Site

```python
from hansard_tales.site.generator import StaticSiteGenerator

generator = StaticSiteGenerator(config)
generator.generate_all()

print("Site generated in site_output/")
```

---

## Phase 1 Components

### MP Identification

Identify MPs in Hansard text:

```python
from hansard_tales.analysis import MPIdentifier

identifier = MPIdentifier(db_session)

# Identify MP from text
match = identifier.identify("Hon. John Doe (Nairobi West, UDA)")

if match:
    print(f"MP: {match.name}")
    print(f"Confidence: {match.confidence:.2f}")
    print(f"Constituency: {match.constituency}")
```

### Statement Segmentation

Segment Hansard into individual statements:

```python
from hansard_tales.analysis import StatementSegmenter

segmenter = StatementSegmenter(mp_identifier)

# Segment text
statements = segmenter.segment(hansard_text, session_id="123")

for stmt in statements:
    print(f"MP: {stmt.mp_id}")
    print(f"Text: {stmt.text[:100]}...")
    print()
```

### Filler Detection

Classify statements as substantive or filler:

```python
from hansard_tales.analysis import FillerDetector

detector = FillerDetector()

# Classify statement
stmt_type, confidence = detector.classify(statement)

if detector.is_substantive(statement):
    print("Substantive statement")
else:
    print(f"Filler: {stmt_type.value}")
```

### Context Retrieval (RAG)

Retrieve relevant context for LLM analysis:

```python
from hansard_tales.analysis import ContextRetriever

retriever = ContextRetriever(vector_db, config.embedding)

# Retrieve context
context = retriever.retrieve(statement, top_k=5)

print(f"Historical: {len(context.historical_statements)}")
print(f"Bills: {len(context.related_bills)}")
print(f"Votes: {len(context.related_votes)}")
```

### LLM Analysis

Analyze statements with Claude:

```python
from hansard_tales.analysis import LLMAnalyzer

analyzer = LLMAnalyzer(config.llm)

# Analyze statement
analysis = analyzer.analyze(statement, context)

print(f"Sentiment: {analysis.sentiment}")
print(f"Quality: {analysis.quality_score}/100")
print(f"Topics: {', '.join(analysis.primary_topic)}")
print(f"Key points: {analysis.key_points}")
```

### Citation Verification

Verify LLM citations:

```python
from hansard_tales.analysis import CitationVerifier

verifier = CitationVerifier()

# Verify citations
for citation in analysis.citations:
    is_valid = verifier.verify(citation, statement.text)
    print(f"Citation: {citation[:50]}...")
    print(f"Valid: {is_valid}")
```

### Vote Processing

Extract votes from Votes & Proceedings PDFs:

```python
from hansard_tales.processors import VoteProcessor

processor = VoteProcessor()

# Process votes PDF
vote_record = processor.process(Path("data/pdfs/votes_20251104.pdf"))

print(f"Bill: {vote_record.bill_id}")
print(f"Ayes: {vote_record.ayes_count}")
print(f"Noes: {vote_record.noes_count}")
print(f"Abstentions: {vote_record.abstentions_count}")
```

### Bill-Statement Linking

Link statements to bills:

```python
from hansard_tales.analysis import BillStatementLinker

linker = BillStatementLinker(vector_db)

# Find bill mentions
mentions = linker.find_bill_mentions(statement)

for mention in mentions:
    print(f"Bill: {mention.bill_number}")
    print(f"Context: {mention.context}")
    print(f"Confidence: {mention.confidence:.2f}")
```

### MP Profile Generation

Generate MP profiles:

```python
from hansard_tales.analysis import MPProfileGenerator

generator = MPProfileGenerator(db_session, llm_analyzer)

# Generate profile
profile = generator.generate_profile(mp_id="uuid-here")

print(f"MP: {profile.name}")
print(f"Total statements: {profile.total_statements}")
print(f"Avg quality: {profile.avg_quality_score:.1f}")
print(f"Top topics: {', '.join(profile.top_topics[:3])}")
print(f"Summary: {profile.summary}")
```

### Session Summary Generation

Generate session summaries:

```python
from hansard_tales.analysis import SessionSummaryGenerator

generator = SessionSummaryGenerator(db_session, llm_analyzer)

# Generate summary
summary = generator.generate_summary(session_id="123")

print(f"Date: {summary.date}")
print(f"Bills discussed: {len(summary.bills_discussed)}")
print(f"Key topics: {', '.join(summary.key_topics)}")
print(f"Summary: {summary.summary}")
```

---

## Common Workflows

### Workflow 1: Download and Process Historical Data

```bash
# 1. Download historical data
python scripts/download_historical_data.py --year 2025 --max-documents 50

# 2. Process downloaded PDFs
python scripts/process_historical_data.py --workers 4

# 3. Validate data integrity
python scripts/validate_historical_data.py

# 4. Generate static site
python -c "from hansard_tales.site.generator import StaticSiteGenerator; from hansard_tales.config import get_config; StaticSiteGenerator(get_config()).generate_all()"
```

### Workflow 2: Process Single Document

```python
from hansard_tales.pipeline import ProcessingPipeline
from hansard_tales.config import get_config
from pathlib import Path

config = get_config()
pipeline = ProcessingPipeline(config)

# Process single Hansard document
pdf_path = Path("data/pdfs/hansard_20251104_P.pdf")
result = pipeline.process_hansard(pdf_path)

# Check results
print(f"Status: {result.status}")
print(f"Statements: {result.statements_count}")
print(f"Processing time: {result.processing_time:.2f}s")

# Access processed data
for statement in result.statements:
    if statement.classification == "substantive":
        print(f"MP: {statement.mp_name}")
        print(f"Quality: {statement.quality_score}/100")
        print(f"Text: {statement.text[:100]}...")
        print()
```

### Workflow 3: Batch Processing

```python
from hansard_tales.utils.batch import BatchProcessor
from hansard_tales.processors import PDFProcessor
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

### Workflow 4: Search and Analysis

```python
from hansard_tales.vector_db import create_vector_db
from hansard_tales.vector_db.embeddings import EmbeddingGenerator
from hansard_tales.database import get_session
from hansard_tales.database.models import StatementORM

config = get_config()

# Create vector DB and embedder
vector_db = create_vector_db(config.vector_db)
embedder = EmbeddingGenerator(config.embedding)

# Search for statements
query = "What is the government's position on healthcare funding?"
query_embedding = embedder.generate(query)

results = vector_db.search(
    collection="statements",
    query_vector=query_embedding,
    limit=10,
    filter={"classification": "substantive"}
)

# Get full statement details from database
with get_session() as session:
    for result in results:
        stmt = session.query(StatementORM).filter_by(
            vector_doc_id=result.id
        ).first()

        if stmt:
            print(f"Score: {result.score:.3f}")
            print(f"MP: {stmt.mp.name}")
            print(f"Date: {stmt.document.date}")
            print(f"Text: {stmt.text[:200]}...")
            print()
```

---

## Command-Line Tools

### Download Historical Data

```bash
# Download all documents from 2025
python scripts/download_historical_data.py --year 2025

# Download specific date range
python scripts/download_historical_data.py \
    --start-date 2025-01-01 \
    --end-date 2025-12-31

# Download with limits
python scripts/download_historical_data.py \
    --year 2025 \
    --max-documents 100 \
    --workers 4
```

### Process Historical Data

```bash
# Process all PDFs
python scripts/process_historical_data.py

# Process with specific workers
python scripts/process_historical_data.py --workers 8

# Process specific year
python scripts/process_historical_data.py --year 2025
```

### Validate Data

```bash
# Validate all data
python scripts/validate_historical_data.py

# Validate specific year
python scripts/validate_historical_data.py --year 2025

# Generate detailed report
python scripts/validate_historical_data.py --report validation_report.json
```

### Validate Configuration

```bash
# Validate current configuration
python scripts/validate_config.py

# Validate specific environment
python scripts/validate_config.py --environment production

# Strict mode (warnings as errors)
python scripts/validate_config.py --strict
```

---

## Python API

### Configuration

```python
from hansard_tales.config import get_config, reload_config

# Get configuration
config = get_config()

# Access settings
print(config.database.connection_string)
print(config.llm.model)
print(config.embedding.model_name)

# Reload configuration (after changes)
config = reload_config()
```

### Database Operations

```python
from hansard_tales.database import get_session
from hansard_tales.database.models import DocumentORM, StatementORM, MPORM

# Query documents
with get_session() as session:
    # Get all Hansard documents
    documents = session.query(DocumentORM).filter_by(
        type="hansard"
    ).all()

    # Get statements by MP
    mp = session.query(MPORM).filter_by(name="John Doe").first()
    statements = session.query(StatementORM).filter_by(
        mp_id=mp.id
    ).limit(10).all()

    # Get substantive statements
    substantive = session.query(StatementORM).filter_by(
        classification="substantive"
    ).filter(
        StatementORM.quality_score >= 70
    ).all()
```

### Vector Database Operations

```python
from hansard_tales.vector_db import create_vector_db
from hansard_tales.vector_db.embeddings import EmbeddingGenerator

# Create vector DB
vector_db = create_vector_db(config.vector_db)

# Create embedder
embedder = EmbeddingGenerator(config.embedding)

# Add documents
texts = ["Statement 1", "Statement 2"]
embeddings = embedder.generate_batch(texts)
metadata = [{"mp_id": "123"}, {"mp_id": "456"}]

vector_db.add(
    collection="statements",
    vectors=embeddings,
    metadata=metadata
)

# Search
query_embedding = embedder.generate("healthcare funding")
results = vector_db.search(
    collection="statements",
    query_vector=query_embedding,
    limit=10
)
```

---

## Best Practices

### 1. Configuration Management

- Use environment-specific configs (dev/staging/prod)
- Store sensitive data in environment variables
- Validate configuration before running
- Use example configs as templates

### 2. Error Handling

- Always use try-except for external operations
- Log errors with context
- Use retry logic for transient failures
- Fail gracefully with meaningful messages

### 3. Performance Optimization

- Use batch processing for multiple documents
- Enable caching for repeated operations
- Use connection pooling for databases
- Process in parallel when possible

### 4. Cost Management

- Monitor LLM API usage
- Enable response caching
- Set monthly budget limits
- Use cheaper models for testing

### 5. Data Quality

- Validate input data before processing
- Check for duplicates
- Verify citations
- Monitor quality scores

### 6. Testing

- Test with sample data first
- Use small batches for initial runs
- Validate results manually
- Monitor processing metrics

---

## Examples

See `examples/` directory for complete examples:

- `prometheus_example.py` - Metrics collection
- `sentry_example.py` - Error tracking
- `test_dateparser_formats.py` - Date parsing

---

## Additional Resources

- [Setup Guide](SETUP.md) - Installation and setup
- [Configuration Guide](CONFIGURATION.md) - Configuration reference
- [API Documentation](API.md) - Complete API reference
- [Architecture](ARCHITECTURE.md) - System architecture
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

---

**Last Updated**: January 2025
**Version**: 1.0 (Phase 1)
