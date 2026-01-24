# Phase 0: Foundation - Implementation Tasks

## Overview

This document breaks down the Phase 0 design into specific, testable implementation tasks. Each task includes acceptance criteria and property-based tests to verify correctness.

**Total Duration**: 2 weeks (14 days)
**Test Coverage Target**: ≥90%
**Property Tests**: 32 properties across all components

## Task Status Legend

- `[ ]` Not started
- `[-]` In progress
- `[x]` Completed

## Week 1: Core Infrastructure

### Task 1: Configuration Management

**Duration**: 2 days
**Dependencies**: None
**Validates**: Requirements 6.1-6.6

#### Subtasks

- [ ] 1.1 Implement Pydantic configuration models
  - Create `Config`, `DatabaseConfig`, `VectorDBConfig`, `EmbeddingConfig`, `ScraperConfig`, `LoggingConfig`, `MonitoringConfig`
  - Add validation for all fields
  - Support environment variable overrides
  - **Files**: `hansard_tales/config.py`

- [ ] 1.2 Create configuration files
  - Create `config/development.yaml`
  - Create `config/staging.yaml`
  - Create `config/production.yaml`
  - Create `.env.example`
  - **Files**: `config/*.yaml`, `.env.example`

- [ ] 1.3 Write unit tests for configuration
  - Test configuration loading from YAML
  - Test environment variable overrides
  - Test validation errors
  - Test connection string generation
  - **Files**: `tests/unit/test_config.py`

- [ ] 1.4 Write property tests for configuration (PBT)
  - **Property 1.1**: All required fields must be present and valid
  - **Property 1.2**: Environment variables must override file configuration
  - **Test Strategy**: Generate random configs, verify validation
  - **Files**: `tests/property/test_config_properties.py`

**Acceptance Criteria**:
- ✓ Configuration loads from YAML files
- ✓ Environment variables override file config
- ✓ Invalid configuration raises ValidationError
- ✓ All property tests pass
- ✓ Test coverage ≥90%

---

### Task 2: Data Models

**Duration**: 2 days
**Dependencies**: Task 1
**Validates**: Requirements 3.1-3.6, 15.1-15.5

#### Subtasks

- [ ] 2.1 Implement base models
  - Create `Chamber`, `DocumentType` enums
  - Create `SourceReference` (frozen/immutable)
  - Create `Document` base model
  - **Files**: `hansard_tales/models/base.py`

- [ ] 2.2 Implement document-specific models
  - Create `Statement`, `Bill`, `BillVersion`, `Vote`, `MPVote`, `Question`, `Petition`
  - Add all required fields with validation
  - Add source tracking to all models
  - **Files**: `hansard_tales/models/documents.py`

- [ ] 2.3 Write unit tests for models
  - Test model creation and validation
  - Test JSON serialization/deserialization
  - Test field constraints (min/max length, ranges)
  - Test enum values
  - **Files**: `tests/unit/test_models.py`

- [ ] 2.4 Write property tests for models (PBT)
  - **Property 2.1**: SourceReference fields must be immutable
  - **Property 2.2**: All generated UUIDs must be unique
  - **Property 2.3**: Models must serialize to/from JSON without data loss
  - **Test Strategy**: Generate random models, test invariants
  - **Files**: `tests/property/test_model_properties.py`

**Acceptance Criteria**:
- ✓ All models defined with proper validation
- ✓ SourceReference is immutable (frozen)
- ✓ JSON serialization is lossless
- ✓ All property tests pass
- ✓ Test coverage ≥90%

---

### Task 3: Database Schema (SQLAlchemy)

**Duration**: 2 days
**Dependencies**: Task 2
**Validates**: Requirements 1.1-1.8

#### Subtasks

- [ ] 3.1 Implement SQLAlchemy ORM models
  - Create `DocumentORM`, `MPORM`, `StatementORM`, `BillORM`, `BillVersionORM`
  - Create `VoteORM`, `MPVoteORM`, `QuestionORM`, `PetitionORM`
  - Add foreign key constraints
  - Add indexes on frequently queried columns
  - **Files**: `hansard_tales/database/models.py`

- [ ] 3.2 Setup Alembic migrations
  - Initialize Alembic
  - Create initial migration
  - Configure migration environment
  - **Files**: `alembic/`, `alembic.ini`, `alembic/env.py`

- [ ] 3.3 Create database initialization script
  - Create script to initialize database
  - Create script to seed test data
  - **Files**: `hansard_tales/database/init_db.py`

- [ ] 3.4 Write unit tests for database
  - Test table creation
  - Test foreign key constraints
  - Test unique constraints
  - Test CRUD operations
  - **Files**: `tests/unit/test_database.py`

- [ ] 3.5 Write property tests for database (PBT)
  - **Property 3.1**: Foreign key references must point to existing records
  - **Property 3.2**: source_hash and bill_number must be unique
  - **Property 3.3**: Migrations must be reversible
  - **Test Strategy**: Generate random data, test constraints
  - **Files**: `tests/property/test_database_properties.py`

**Acceptance Criteria**:
- ✓ All tables created with proper schema
- ✓ Foreign key constraints enforced
- ✓ Indexes created on key columns
- ✓ Migrations work (upgrade/downgrade)
- ✓ All property tests pass
- ✓ Test coverage ≥90%

---

### Task 4: Vector Database Integration

**Duration**: 2 days
**Dependencies**: Task 2
**Validates**: Requirements 2.1-2.7

#### Subtasks

- [ ] 4.1 Implement vector DB interface
  - Create `VectorDB` abstract base class
  - Define interface methods (create_collection, insert, search, delete, get)
  - **Files**: `hansard_tales/vector_db/interface.py`

- [ ] 4.2 Implement ChromaDB adapter
  - Create `ChromaDBAdapter` implementing `VectorDB`
  - Implement all interface methods
  - Add persistence support
  - **Files**: `hansard_tales/vector_db/chromadb_adapter.py`

- [ ] 4.3 Implement Qdrant adapter
  - Create `QdrantAdapter` implementing `VectorDB`
  - Implement all interface methods
  - Add metadata filtering support
  - **Files**: `hansard_tales/vector_db/qdrant_adapter.py`

- [ ] 4.4 Implement embedding generator
  - Create `EmbeddingGenerator` using sentence-transformers
  - Support batch generation
  - Add similarity computation
  - **Files**: `hansard_tales/embedding/generator.py`

- [ ] 4.5 Create vector DB factory
  - Create factory function to instantiate correct adapter
  - **Files**: `hansard_tales/vector_db/__init__.py`

- [ ] 4.6 Write unit tests for vector DB
  - Test collection creation
  - Test vector insertion
  - Test semantic search
  - Test metadata filtering
  - Test embedding generation
  - **Files**: `tests/unit/test_vector_db.py`, `tests/unit/test_embedding.py`

- [ ] 4.7 Write property tests for vector DB (PBT)
  - **Property 4.1**: Same text must always generate same embedding
  - **Property 4.2**: Vectors must persist across restarts
  - **Property 4.3**: Search with filters must only return matching results
  - **Test Strategy**: Generate random texts, test invariants
  - **Files**: `tests/property/test_vector_properties.py`

**Acceptance Criteria**:
- ✓ Both ChromaDB and Qdrant adapters work
- ✓ Embeddings are consistent
- ✓ Semantic search returns relevant results
- ✓ Metadata filtering works correctly
- ✓ All property tests pass
- ✓ Test coverage ≥90%

---

## Week 2: Collection and Processing

### Task 5: Web Scrapers

**Duration**: 2 days
**Dependencies**: Task 1, Task 2
**Validates**: Requirements 4.1-4.8

#### Subtasks

- [ ] 5.1 Implement base scraper
  - Create `BaseScraper` abstract class
  - Implement retry logic with exponential backoff
  - Implement document download with hash computation
  - Add duplicate detection
  - **Files**: `hansard_tales/scrapers/base.py`

- [ ] 5.2 Implement Hansard scraper
  - Create `HansardScraper` extending `BaseScraper`
  - Implement URL discovery for National Assembly
  - Implement URL discovery for Senate
  - Extract metadata from filenames
  - **Files**: `hansard_tales/scrapers/hansard.py`

- [ ] 5.3 Implement Votes scraper
  - Create `VotesScraper` extending `BaseScraper`
  - Implement URL discovery for both chambers
  - Extract metadata from filenames
  - **Files**: `hansard_tales/scrapers/votes.py`

- [ ] 5.4 Create scraper factory
  - Create factory function to instantiate correct scraper
  - **Files**: `hansard_tales/scrapers/__init__.py`

- [ ] 5.5 Write unit tests for scrapers
  - Test URL discovery (mocked)
  - Test document download (mocked)
  - Test metadata extraction
  - Test retry logic
  - Test duplicate detection
  - **Files**: `tests/unit/test_scrapers.py`

- [ ] 5.6 Write property tests for scrapers (PBT)
  - **Property 5.1**: Same PDF content must always generate same hash
  - **Property 5.2**: Already-downloaded documents must be skipped
  - **Property 5.3**: Single document failure must not stop entire scrape
  - **Test Strategy**: Mock downloads, test error handling
  - **Files**: `tests/property/test_scraper_properties.py`

**Acceptance Criteria**:
- ✓ Scrapers discover document URLs
- ✓ Scrapers download PDFs with retry
- ✓ Duplicate detection works
- ✓ Error handling is resilient
- ✓ All property tests pass
- ✓ Test coverage ≥90%

---

### Task 6: PDF Processing Pipeline

**Duration**: 2 days
**Dependencies**: Task 2, Task 4
**Validates**: Requirements 5.1-5.7, 15.1-15.5

#### Subtasks

- [ ] 6.1 Implement PDF processor
  - Create `PDFProcessor` class
  - Implement text extraction with page/line tracking
  - Implement table extraction
  - Implement metadata extraction
  - Compute SHA256 hash
  - **Files**: `hansard_tales/processors/pdf_processor.py`

- [ ] 6.2 Implement specialized processors
  - Create `HansardProcessor` extending `PDFProcessor`
  - Create `VotesProcessor` extending `PDFProcessor`
  - **Files**: `hansard_tales/processors/hansard_processor.py`, `hansard_tales/processors/votes_processor.py`

- [ ] 6.3 Implement document storage service
  - Create `DocumentStorageService`
  - Implement dual storage (SQL + vector DB)
  - Implement duplicate detection
  - Generate and store embeddings
  - **Files**: `hansard_tales/storage/document_storage.py`

- [ ] 6.4 Write unit tests for PDF processing
  - Test text extraction
  - Test table extraction
  - Test metadata extraction
  - Test hash computation
  - Test storage service
  - **Files**: `tests/unit/test_pdf_processor.py`, `tests/unit/test_document_storage.py`

- [ ] 6.5 Write property tests for PDF processing (PBT)
  - **Property 6.1**: All text in PDF must be extracted
  - **Property 6.2**: Page and line numbers must be accurate
  - **Property 6.3**: Same PDF must always generate same hash
  - **Test Strategy**: Create test PDFs, verify extraction
  - **Files**: `tests/property/test_pdf_properties.py`

**Acceptance Criteria**:
- ✓ Text extraction preserves page/line numbers
- ✓ Tables are extracted correctly
- ✓ Documents stored in both SQL and vector DB
- ✓ Source tracking is immutable
- ✓ All property tests pass
- ✓ Test coverage ≥90%

---

### Task 7: Logging Infrastructure

**Duration**: 1 day
**Dependencies**: Task 1
**Validates**: Requirements 7.1-7.6

#### Subtasks

- [ ] 7.1 Implement structured logging
  - Configure structlog with JSON formatting
  - Create `Logger` wrapper class
  - Add request ID tracking with context vars
  - **Files**: `hansard_tales/logging/logger.py`

- [ ] 7.2 Setup log rotation
  - Configure file logging with rotation
  - Setup daily rotation with 30-day retention
  - **Files**: `hansard_tales/logging/rotation.py`

- [ ] 7.3 Write unit tests for logging
  - Test log formatting
  - Test log levels
  - Test request ID propagation
  - Test file rotation
  - **Files**: `tests/unit/test_logging.py`

- [ ] 7.4 Write property tests for logging (PBT)
  - **Property 7.1**: All log entries must include required fields
  - **Property 7.2**: Request ID must be included in all logs within same operation
  - **Test Strategy**: Generate logs, verify structure
  - **Files**: `tests/property/test_logging_properties.py`

**Acceptance Criteria**:
- ✓ Structured logging works (JSON format)
- ✓ Request IDs propagate correctly
- ✓ Log rotation works
- ✓ All property tests pass
- ✓ Test coverage ≥90%

---

### Task 8: Error Handling

**Duration**: 1 day
**Dependencies**: Task 7
**Validates**: Requirements 8.1-8.5

#### Subtasks

- [ ] 8.1 Implement exception hierarchy
  - Create `HansardTalesError` base exception
  - Create `DataCollectionError`, `ProcessingError`, `StorageError`, `ConfigurationError`, `ValidationError`
  - **Files**: `hansard_tales/exceptions.py`

- [ ] 8.2 Implement retry logic
  - Create retry decorators using tenacity
  - Configure exponential backoff
  - **Files**: `hansard_tales/utils/retry.py`

- [ ] 8.3 Implement error context capture
  - Create `ErrorContext` dataclass
  - Implement context capture function
  - Implement error logging function
  - **Files**: `hansard_tales/errors/context.py`

- [ ] 8.4 Implement batch processor
  - Create `BatchProcessor` with error isolation
  - Support continue-on-error mode
  - **Files**: `hansard_tales/utils/batch.py`

- [ ] 8.5 Write unit tests for error handling
  - Test exception hierarchy
  - Test retry logic
  - Test error context capture
  - Test batch processing with errors
  - **Files**: `tests/unit/test_errors.py`

- [ ] 8.6 Write property tests for error handling (PBT)
  - **Property 8.1**: Failed operations must retry exactly max_retries times
  - **Property 8.2**: Single item failure must not stop batch processing
  - **Property 8.3**: All errors must be logged with full context
  - **Test Strategy**: Mock failures, verify behavior
  - **Files**: `tests/property/test_error_properties.py`

**Acceptance Criteria**:
- ✓ Custom exceptions defined
- ✓ Retry logic works with exponential backoff
- ✓ Error context is captured completely
- ✓ Batch processing isolates errors
- ✓ All property tests pass
- ✓ Test coverage ≥90%

---

### Task 9: Testing Infrastructure

**Duration**: 1 day
**Dependencies**: All previous tasks
**Validates**: Requirements 9.1-9.7

#### Subtasks

- [ ] 9.1 Setup pytest configuration
  - Create `pytest.ini` with coverage settings
  - Configure test markers (unit, integration, property, slow)
  - Set coverage threshold to 90%
  - **Files**: `pytest.ini`

- [ ] 9.2 Create test fixtures
  - Create `conftest.py` with common fixtures
  - Add fixtures: temp_dir, test_config, db_session, vector_db, sample_pdf, sample_document
  - **Files**: `tests/conftest.py`

- [ ] 9.3 Create sample test data
  - Create sample PDFs for testing
  - Create sample configurations
  - **Files**: `tests/fixtures/`

- [ ] 9.4 Write integration tests
  - Test scrape → process → store workflow
  - Test end-to-end document processing
  - **Files**: `tests/integration/test_end_to_end.py`

- [ ] 9.5 Write property tests for testing infrastructure (PBT)
  - **Property 9.1**: Tests must not affect each other
  - **Property 9.2**: Code coverage must be ≥90%
  - **Test Strategy**: Run tests in random order
  - **Files**: `tests/property/test_testing_properties.py`

**Acceptance Criteria**:
- ✓ pytest configured correctly
- ✓ All fixtures work
- ✓ Integration tests pass
- ✓ Coverage ≥90%
- ✓ All property tests pass

---

### Task 10: CI/CD Pipeline

**Duration**: 1 day
**Dependencies**: Task 9
**Validates**: Requirements 10.1-10.7

#### Subtasks

- [ ] 10.1 Create GitHub Actions workflow
  - Create `.github/workflows/ci.yml`
  - Add lint job (ruff, mypy)
  - Add test job (pytest with coverage)
  - Add build job
  - Add deploy job (placeholder)
  - **Files**: `.github/workflows/ci.yml`

- [ ] 10.2 Setup pre-commit hooks
  - Create `.pre-commit-config.yaml`
  - Add hooks: trailing-whitespace, ruff, mypy
  - **Files**: `.pre-commit-config.yaml`

- [ ] 10.3 Configure code coverage reporting
  - Setup codecov integration
  - Configure coverage thresholds
  - **Files**: `.codecov.yml`

- [ ] 10.4 Write property tests for CI/CD (PBT)
  - **Property 10.1**: All tests must run on every commit
  - **Property 10.2**: CI must fail if coverage < 90%
  - **Test Strategy**: Verify CI configuration
  - **Files**: `tests/property/test_ci_properties.py`

**Acceptance Criteria**:
- ✓ CI runs on every push
- ✓ Linting enforced
- ✓ Tests run on multiple Python versions
- ✓ Coverage threshold enforced
- ✓ All property tests pass

---

### Task 11: Development Environment

**Duration**: 1 day
**Dependencies**: Task 1
**Validates**: Requirements 11.1-11.6

#### Subtasks

- [ ] 11.1 Create Docker Compose configuration
  - Create `docker-compose.yml`
  - Add services: postgres, qdrant, prometheus, grafana
  - Configure volumes and health checks
  - **Files**: `docker-compose.yml`

- [ ] 11.2 Create Makefile
  - Add commands: install, dev-setup, test, lint, format, clean, migrate, run
  - Add Docker commands: docker-up, docker-down, docker-logs
  - **Files**: `Makefile`

- [ ] 11.3 Create requirements files
  - Create `requirements.txt` (production dependencies)
  - Create `requirements-dev.txt` (development dependencies)
  - Pin all versions
  - **Files**: `requirements.txt`, `requirements-dev.txt`

- [ ] 11.4 Create setup script
  - Create `scripts/setup.sh`
  - Check Python version
  - Create virtual environment
  - Install dependencies
  - Setup pre-commit hooks
  - Start Docker services
  - Run migrations
  - **Files**: `scripts/setup.sh`

- [ ] 11.5 Create pyproject.toml
  - Configure project metadata
  - Configure build system
  - Configure tool settings (ruff, mypy, pytest)
  - **Files**: `pyproject.toml`

- [ ] 11.6 Write property tests for development environment (PBT)
  - **Property 11.1**: Setup script must create identical environments
  - **Property 11.2**: All Docker services must be healthy after startup
  - **Test Strategy**: Run setup, verify services
  - **Files**: `tests/property/test_dev_env_properties.py`

**Acceptance Criteria**:
- ✓ Docker Compose starts all services
- ✓ Makefile commands work
- ✓ Setup script completes successfully
- ✓ All services are healthy
- ✓ All property tests pass

---

### Task 12: Monitoring Setup

**Duration**: 1 day
**Dependencies**: Task 1, Task 7
**Validates**: Requirements 12.1-12.5

#### Subtasks

- [ ] 12.1 Implement Prometheus metrics
  - Create metrics: documents_processed, processing_time, error_count, queue_depth, vector_db_size
  - Create decorators for tracking
  - Start metrics server
  - **Files**: `hansard_tales/monitoring/metrics.py`

- [ ] 12.2 Create Prometheus configuration
  - Create `config/prometheus.yml`
  - Configure scrape targets
  - **Files**: `config/prometheus.yml`

- [ ] 12.3 Create Grafana dashboards
  - Create dashboard JSON
  - Add panels: documents processed, processing time, error rate, queue depth
  - **Files**: `config/grafana/dashboards/system_overview.json`

- [ ] 12.4 Implement Sentry integration
  - Configure Sentry SDK
  - Add error capture
  - **Files**: `hansard_tales/monitoring/sentry.py`

- [ ] 12.5 Implement health check endpoint
  - Create FastAPI app with /health endpoint
  - Check database, vector DB, disk space
  - **Files**: `hansard_tales/monitoring/health.py`

- [ ] 12.6 Write unit tests for monitoring
  - Test metrics collection
  - Test health checks
  - **Files**: `tests/unit/test_monitoring.py`

- [ ] 12.7 Write property tests for monitoring (PBT)
  - **Property 12.1**: Metrics must accurately reflect system state
  - **Property 12.2**: Health check must detect service failures
  - **Test Strategy**: Process documents, verify metrics
  - **Files**: `tests/property/test_monitoring_properties.py`

**Acceptance Criteria**:
- ✓ Prometheus metrics exposed
- ✓ Grafana dashboards work
- ✓ Sentry captures errors
- ✓ Health check endpoint works
- ✓ All property tests pass
- ✓ Test coverage ≥90%

---

### Task 13: Documentation

**Duration**: 1 day
**Dependencies**: All previous tasks
**Validates**: Requirements 13.1-13.6

#### Subtasks

- [ ] 13.1 Create README.md
  - Add project overview
  - Add features list
  - Add quick start guide
  - Add links to documentation
  - **Files**: `README.md`

- [ ] 13.2 Create ARCHITECTURE.md
  - Document system design
  - Document data flow
  - Document component interactions
  - **Files**: `docs/ARCHITECTURE.md`

- [ ] 13.3 Create CONTRIBUTING.md
  - Document development workflow
  - Document testing guidelines
  - Document code style
  - **Files**: `docs/CONTRIBUTING.md`

- [ ] 13.4 Create ADRs
  - Create ADR template
  - Document all 8 architectural decisions from master architecture
  - **Files**: `docs/architecture/adrs/*.md`

- [ ] 13.5 Setup MkDocs
  - Create `mkdocs.yml`
  - Create documentation structure
  - Add API documentation with mkdocstrings
  - **Files**: `mkdocs.yml`, `docs/`

- [ ] 13.6 Write docstrings
  - Add docstrings to all public functions and classes
  - Follow Google docstring format
  - **Files**: All Python files

- [ ] 13.7 Write property tests for documentation (PBT)
  - **Property 13.1**: All public APIs must have documentation
  - **Property 13.2**: All major architectural decisions must have ADRs
  - **Test Strategy**: Check docstrings, verify ADRs exist
  - **Files**: `tests/property/test_documentation_properties.py`

**Acceptance Criteria**:
- ✓ README is comprehensive
- ✓ ARCHITECTURE.md is complete
- ✓ CONTRIBUTING.md is clear
- ✓ All 8 ADRs documented
- ✓ MkDocs site builds
- ✓ All public APIs have docstrings
- ✓ All property tests pass

---

## Summary

### Task Overview

| Task | Duration | Dependencies | Properties |
|------|----------|--------------|------------|
| 1. Configuration | 2 days | None | 2 |
| 2. Data Models | 2 days | 1 | 3 |
| 3. Database Schema | 2 days | 2 | 3 |
| 4. Vector DB | 2 days | 2 | 3 |
| 5. Web Scrapers | 2 days | 1, 2 | 3 |
| 6. PDF Processing | 2 days | 2, 4 | 3 |
| 7. Logging | 1 day | 1 | 2 |
| 8. Error Handling | 1 day | 7 | 3 |
| 9. Testing Infrastructure | 1 day | All | 2 |
| 10. CI/CD | 1 day | 9 | 2 |
| 11. Dev Environment | 1 day | 1 | 2 |
| 12. Monitoring | 1 day | 1, 7 | 2 |
| 13. Documentation | 1 day | All | 2 |

**Total**: 19 days of work compressed into 14 days through parallelization

### Property-Based Tests Summary

**32 Properties** to validate:
- Configuration: 2 properties
- Data Models: 3 properties
- Database: 3 properties
- Vector DB: 3 properties
- Scrapers: 3 properties
- PDF Processing: 3 properties
- Logging: 2 properties
- Error Handling: 3 properties
- Testing: 2 properties
- CI/CD: 2 properties
- Dev Environment: 2 properties
- Monitoring: 2 properties
- Documentation: 2 properties

### Test Coverage Target

- **Unit Tests**: ≥90% coverage
- **Integration Tests**: End-to-end workflows
- **Property Tests**: All 32 properties validated

### Completion Criteria

Phase 0 is complete when:
- ✓ All 13 tasks completed
- ✓ All 32 property tests passing
- ✓ Test coverage ≥90%
- ✓ CI/CD pipeline green
- ✓ Documentation complete
- ✓ Development environment working
- ✓ Ready to proceed to Phase 1

