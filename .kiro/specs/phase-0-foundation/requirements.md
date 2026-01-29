# Phase 0: Foundation - Requirements

## Introduction

This document specifies requirements for Phase 0 of the Hansard Tales system: establishing the foundational infrastructure, data models, and development environment. This phase sets up the core architecture that all subsequent phases will build upon.

**Scope**: Infrastructure setup, database schema, basic scrapers, CI/CD pipeline

**Duration**: 2 weeks

**Dependencies**: None (clean slate)

## Glossary

- **Chamber**: Either National Assembly or Senate
- **Document**: Any parliamentary document (Hansard, Bill, Vote, etc.)
- **Vector Database**: Database storing document embeddings for semantic search
- **Embedding**: Numerical representation of text for semantic similarity
- **RAG**: Retrieval-Augmented Generation (context retrieval for LLM)
- **ORM**: Object-Relational Mapping (SQLAlchemy)
- **Migration**: Database schema version change

## Requirements

### Requirement 1: Database Schema Foundation

**User Story:** As a developer, I want a well-designed database schema, so that I can store all parliamentary data efficiently.

#### Acceptance Criteria

1. THE System SHALL use PostgreSQL for production and SQLite for development
2. THE System SHALL define tables for: documents, statements, mps, senators, sessions, chambers, parliament_terms, downloaded_files
3. THE System SHALL use SQLAlchemy ORM for all database operations
4. THE System SHALL use Alembic for schema migrations
5. WHEN a migration is applied, THE System SHALL preserve all existing data
6. THE System SHALL enforce foreign key constraints
7. THE System SHALL create indexes on frequently queried columns
8. THE System SHALL support both National Assembly and Senate data in the same schema
9. THE System SHALL maintain a downloaded_files table to track all downloaded PDFs by source_hash
10. THE downloaded_files table SHALL store: source_url, source_hash, standardized_filename, download_date, file_size, document_type
11. WHEN checking for duplicates, THE System SHALL query downloaded_files table by source_hash
12. THE System SHALL prevent redownloading files that already exist in downloaded_files table

### Requirement 2: Vector Database Setup

**User Story:** As a developer, I want a vector database for semantic search, so that I can retrieve relevant context for analysis.

#### Acceptance Criteria

1. THE System SHALL use Qdrant for production and ChromaDB for development
2. THE System SHALL store document embeddings with metadata
3. THE System SHALL support filtering by: document_type, chamber, date_range, mp_id, bill_id
4. THE System SHALL use sentence-transformers (all-MiniLM-L6-v2) for embedding generation
5. THE System SHALL persist vector data to disk
6. WHEN a document is stored in PostgreSQL, THE System SHALL store corresponding embedding in vector DB
7. THE System SHALL support semantic search with configurable result limits

### Requirement 3: Document Data Models

**User Story:** As a developer, I want unified data models for all document types, so that I can process them consistently.

#### Acceptance Criteria

1. THE System SHALL define a base Document model with common fields
2. THE System SHALL define specialized models for: Hansard, Bill, Vote, Question, Petition, Statement, Motion, OrderPaper, LegislativeProposal, AuditorReport
3. EACH document model SHALL include: id, type, chamber, title, date, session_id, source_url, source_hash
4. EACH document model SHALL include vector_doc_id for linking to vector DB
5. THE System SHALL use dataclasses or Pydantic models for type safety
6. THE System SHALL support JSON serialization for all models

### Requirement 4: Basic Web Scrapers

**User Story:** As a system operator, I want automated scrapers for parliament.go.ke, so that I can collect documents without manual intervention.

#### Acceptance Criteria

1. THE System SHALL implement a scraper for National Assembly Hansard
2. THE System SHALL implement a scraper for National Assembly Votes & Proceedings
3. EACH scraper SHALL extract PDF links ONLY from specific HTML tables on parliament.go.ke pages
4. EACH scraper SHALL identify the correct table by HTML structure (class, id, or table headers)
5. WHEN no documents are found on the first page, THE System SHALL raise an error indicating potential HTML/CSS changes
6. EACH scraper SHALL download PDFs to either local storage (for testing and adhoc runs) or to cloud storage (S3)
7. EACH scraper SHALL use the dateparser library to parse British format dates from PDF link titles
8. EACH scraper SHALL assume all dates are in UTC+3 timezone (Kenya timezone)
9. EACH scraper SHALL extract metadata (date, session, title) from PDF filename or content
10. EACH scraper SHALL compute SHA256 hash of downloaded PDF
11. WHEN checking for duplicates, THE System SHALL first query the downloaded_files table by source URL
12. WHEN a file exists in the downloaded_files table, THE System SHALL verify the file exists in storage
13. WHEN a file exists in both the table and storage, THE System SHALL skip downloading
14. WHEN a file exists in the table but not in storage, THE System SHALL download and update the table
15. WHEN a file does not exist in the table, THE System SHALL download and insert a new record
16. WHEN a scraper fails during document processing, THE System SHALL log the error and continue with remaining documents
17. THE System SHALL support date range filtering for scrapers
18. EACH scraper SHALL validate that extracted links are PDF files before downloading
19. THE System SHALL support pagination to fetch all available documents across multiple pages
20. THE System SHALL use parliament term parameter in URLs for proper document filtering
21. THE System SHALL add rate limiting delays between page requests to avoid server issues
22. THE System SHALL generate standardized filenames for downloaded documents based on extracted metadata
23. HANSARD documents SHALL be renamed to format: hansard_YYYYMMDD_<P|A|E>.pdf where P=Morning, A=Afternoon, E=Evening
24. VOTES documents SHALL be renamed to format: votes_YYYYMMDDTHHMMSSZ.pdf in ISO 8601 datetime format with UTC timezone
25. WHEN filename parsing fails, THE System SHALL fallback to original filename

#### Implementation Notes

**Scraping Workflow Order:**
1. Fetch page 0 table links using CSS Selectors, extract link title and href
2. Parse dates from link titles using dateparser library (UTC+3 timezone)
3. Determine what the storage path would be for each file
4. Check the downloads tracking table by original URL to find if file has been downloaded
5. For files existing in the tracking table, verify if they exist in storage
6. If files don't exist in storage, download them and update table if necessary
7. If files exist in storage, skip them
8. For files that don't exist in the tracking table, download and insert new records

**Rationale for URL-based checking:**
Using hash-based comparison requires downloading files first to compute hashes. Since the goal is to eliminate re-downloading existing files, checking the database by URL first, then verifying file existence in storage, achieves this goal without unnecessary downloads.

**Hansard Scraper Specifics:**
- URL Format: `https://parliament.go.ke/the-national-assembly/house-business/hansard?field_parliament_value=2022&page=0`
- CSS Selector: `table.cols-2 td.views-field-field-pdf a[href$=".pdf"]`
- Pagination: Automatically detects total pages from `nav.pager` element
- Parliament Term: Default 2022 (13th Parliament)
- Rate Limiting: Uses `retry_delay` config between page requests
- Date Parsing: Uses dateparser library with UTC+3 timezone for British format dates
- Filename Format: `hansard_YYYYMMDD_<P|A|E>.pdf`
- Verified: Successfully fetches 452 PDFs from 19 pages

**Votes Scraper Specifics:**
- URL Format: `https://parliament.go.ke/the-national-assembly/house-business/votes-proceedings?field_parliament_value=2022&page=0`
- CSS Selector: `table.cols-2 td.views-field-field-pdf a[href$=".pdf"]`
- Pagination: Same as Hansard scraper
- Date Parsing: Uses dateparser library with UTC+3 timezone for British format dates
- Filename Format: `votes_YYYYMMDDTHHMMSSZ.pdf`
- Time Parsing: Extracts time from title (e.g., "at 2.30pm") and converts to 24-hour format

### Requirement 5: PDF Processing Pipeline

**User Story:** As a developer, I want a PDF processing pipeline, so that I can extract text and metadata from parliamentary documents.

#### Acceptance Criteria

1. THE System SHALL extract text from PDF documents
2. THE System SHALL preserve page numbers and line numbers for source tracking
3. THE System SHALL handle multi-column layouts (common in Hansard)
4. THE System SHALL extract tables from structured documents (Votes, Trackers)
5. WHEN PDF parsing fails, THE System SHALL log the error with document identifier
6. THE System SHALL support batch processing of multiple PDFs
7. THE System SHALL generate embeddings for extracted text

### Requirement 6: Configuration Management

**User Story:** As a system administrator, I want centralized configuration, so that I can adjust system behavior without code changes.

#### Acceptance Criteria

1. THE System SHALL use YAML files for configuration
2. THE System SHALL support environment variable overrides
3. THE System SHALL validate configuration on startup
4. THE System SHALL provide default values for all configuration options
5. THE System SHALL support separate configurations for: development, staging, production
6. WHEN configuration is invalid, THE System SHALL log errors and exit gracefully

### Requirement 7: Logging Infrastructure

**User Story:** As a system operator, I want structured logging, so that I can diagnose issues quickly.

#### Acceptance Criteria

1. THE System SHALL use structured logging (JSON format)
2. EACH log entry SHALL include: timestamp, level, component, message, context
3. THE System SHALL support log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
4. THE System SHALL write logs to: stdout (for containers) and files (for local dev)
5. THE System SHALL rotate log files daily
6. THE System SHALL include request IDs for tracing operations across components

### Requirement 8: Error Handling Strategy

**User Story:** As a developer, I want consistent error handling, so that failures are predictable and recoverable.

#### Acceptance Criteria

1. THE System SHALL define custom exception classes for: DataCollectionError, ProcessingError, StorageError
2. THE System SHALL retry failed operations with exponential backoff (max 3 retries)
3. WHEN a single document fails processing, THE System SHALL continue with remaining documents
4. THE System SHALL log all errors with full context (stack trace, input data, state)
5. THE System SHALL send notifications for critical errors (if configured)

### Requirement 9: Testing Infrastructure

**User Story:** As a developer, I want comprehensive testing infrastructure with realistic test data, so that I can verify correctness and catch real-world issues.

#### Acceptance Criteria

1. THE System SHALL use pytest for all tests
2. THE System SHALL use Hypothesis for property-based tests
3. THE System SHALL maintain ≥90% code coverage
4. THE System SHALL run tests on every commit (CI/CD)
5. THE System SHALL include: unit tests, integration tests, property tests
6. THE System SHALL prefer realistic test data over excessive mocking
7. THE System SHALL use real PDFs from parliament.go.ke for testing (stored in tests/data/pdfs/)
8. THE System SHALL use temporary SQLite databases instead of mocking database operations
9. THE System SHALL use temporary directories for file operations
10. THE System SHALL mock only external network calls and slow operations
11. THE System SHALL use fixtures for test data
12. THE System SHALL mock external dependencies only when necessary (network, slow operations)

### Requirement 10: CI/CD Pipeline

**User Story:** As a developer, I want automated testing and deployment, so that I can ship changes confidently.

#### Acceptance Criteria

1. THE System SHALL use GitHub Actions for CI/CD
2. WHEN code is pushed, THE System SHALL run all tests
3. WHEN tests pass on main branch, THE System SHALL deploy automatically
4. THE System SHALL enforce code coverage thresholds (≥90%)
5. THE System SHALL run linting (ruff, mypy) on every commit
6. THE System SHALL build and test in isolated environments
7. THE System SHALL cache dependencies for faster builds

### Requirement 11: Development Environment

**User Story:** As a developer, I want a simple development environment, so that I can start contributing quickly.

#### Acceptance Criteria

1. THE System SHALL provide a docker-compose.yml for local development
2. THE System SHALL include: PostgreSQL, Qdrant, Prometheus, Grafana in docker-compose
3. THE System SHALL provide a Makefile with common commands (test, lint, migrate, etc.)
4. THE System SHALL document setup steps in README.md
5. THE System SHALL use virtual environments (venv) for Python dependencies
6. THE System SHALL pin all dependency versions in requirements.txt

### Requirement 12: Monitoring Setup

**User Story:** As a system operator, I want basic monitoring, so that I can track system health.

#### Acceptance Criteria

1. THE System SHALL expose metrics in Prometheus format
2. THE System SHALL track: documents_processed, processing_time, error_rate, queue_depth
3. THE System SHALL provide Grafana dashboards for visualization
4. THE System SHALL support health check endpoints
5. THE System SHALL integrate with Sentry for error tracking (optional)

### Requirement 13: Documentation

**User Story:** As a developer, I want comprehensive documentation, so that I can understand the system architecture.

#### Acceptance Criteria

1. THE System SHALL include README.md with: overview, setup, usage
2. THE System SHALL include ARCHITECTURE.md with: system design, data flow, components
3. THE System SHALL include CONTRIBUTING.md with: development workflow, testing, code style
4. THE System SHALL include API documentation (if applicable)
5. THE System SHALL include inline code documentation (docstrings)
6. THE System SHALL include ADRs for all major architectural decisions

### Requirement 14: Data Source URLs

**User Story:** As a system operator, I want documented data source URLs, so that I can verify scraper targets.

#### Acceptance Criteria

1. THE System SHALL document all parliament.go.ke URLs in configuration
2. THE System SHALL support both National Assembly and Senate URLs
3. THE System SHALL handle URL changes gracefully (log warning, continue)
4. THE System SHALL validate URLs on startup

### Requirement 15: Source Tracking (Anti-Hallucination Foundation)

**User Story:** As a system architect, I want immutable source tracking, so that all data can be verified against original documents.

#### Acceptance Criteria

1. WHEN a document is downloaded, THE System SHALL store: source_url, source_hash (SHA256), download_date
2. WHEN text is extracted, THE System SHALL store: page_number, line_number (if applicable)
3. THE System SHALL NEVER modify source reference fields after initial storage
4. THE System SHALL support linking from any processed data back to original PDF
5. THE System SHALL verify PDF integrity using stored hash
