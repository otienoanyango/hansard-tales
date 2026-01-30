# Phase 1: Core Analysis Pipeline - Implementation Tasks

## Overview

This document breaks down Phase 1 implementation into actionable tasks. Each task includes acceptance criteria, property-based tests, and dependencies.

**Timeline**: 8 weeks
**Test Coverage Target**: ≥90%
**Dependencies**: Phase 0 must be complete

---

## Tasks

### Week 0: Technical Debt from Phase 0

- [-] 0. Address Phase 0 Technical Debt
  - [x] 0.1 Improve Test Coverage
    - [x] 0.1.1 Increase Qdrant adapter coverage from 37.93% to ≥80%
    - [x] 0.1.2 Increase Votes scraper coverage from 76.85% to ≥85%
    - [x] 0.1.3 Increase Base scraper coverage from 79.25% to ≥85%
    - [x] 0.1.4 Add tests for uncovered error handling paths
  - [x] 0.2 Type Annotations
    - [x] 0.2.1 Add type annotations to example scripts
    - [x] 0.2.2 Add type annotations to utility functions
    - [x] 0.2.3 Fix Alembic migration type issues
    - [x] 0.2.4 Enable mypy in pre-commit hooks
  - [ ] 0.3 Scraper Enhancements
    - [ ] 0.3.1 Implement date range filtering (start_date, end_date parameters)
    - [ ] 0.3.2 Add support for multiple parliament terms
    - [ ] 0.3.3 Implement parallel page fetching with connection pooling
    - [ ] 0.3.4 Add progress reporting for long-running scrapes

- [x] 0.4 MP Scraper Implementation
  - [x] 0.4.1 Create MPScraper class
    - [x] 0.4.1.1 Implement CSS selector for MP table (table.cols-7 tr.mp)
    - [x] 0.4.1.2 Extract MP data: name, county, constituency, party, status
    - [x] 0.4.1.3 Handle honorifics (HON., DR., ENG., AMB., etc.)
    - [x] 0.4.1.4 Implement pagination support (35 pages total)
    - [x] 0.4.1.5 Add parliament term parameter support
    - [x] 0.4.1.6 Implement duplicate detection by name+constituency
    - [x] 0.4.1.7 Store MPs in database with proper relationships
  - [x] 0.4.2 Write MP scraper tests
    - [x] 0.4.2.1 Test MP data extraction from sample HTML (tests/sample_html.md)
    - [x] 0.4.2.2 Test honorific parsing (HON., DR., ENG., AMB.)
    - [x] 0.4.2.3 Test pagination detection (35 pages)
    - [x] 0.4.2.4 Test empty field handling (missing county/constituency)
    - [x] 0.4.2.5 Test status field (Elected vs Nominated)
    - [x] 0.4.2.6 Test duplicate detection
    - [x] 0.4.2.7 Test database storage
  - [x] 0.4.3 Create MP scraper fixtures
    - [x] 0.4.3.1 Create tests/fixtures/sample_mps.html from tests/sample_html.md
    - [x] 0.4.3.2 Add realistic test data with various honorifics
    - [x] 0.4.3.3 Add edge cases (missing fields, special characters)

- [x] 0.5 Historical Data Processing Scripts
  - [x] 0.5.1 Create `scripts/download_historical_data.py`
    - [x] 0.5.1.1 Implement parliament term iteration (2013-2024)
    - [x] 0.5.1.2 Implement date range support
    - [x] 0.5.1.3 Add progress tracking with tqdm
    - [x] 0.5.1.4 Add resume capability (skip already downloaded)
    - [x] 0.5.1.5 Add summary statistics reporting
    - [x] 0.5.1.6 Add error logging and recovery
    - [x] 0.5.1.7 Support all document types (Hansard, Votes, MPs)
  - [x] 0.5.2 Create `scripts/process_historical_data.py`
    - [x] 0.5.2.1 Implement batch PDF processing
    - [x] 0.5.2.2 Add parallel processing with worker pool
    - [x] 0.5.2.3 Add progress tracking
    - [x] 0.5.2.4 Add error recovery and retry logic
    - [x] 0.5.2.5 Add validation and quality checks
    - [x] 0.5.2.6 Generate processing report
  - [x] 0.5.3 Create `scripts/validate_historical_data.py`
    - [x] 0.5.3.1 Verify all PDFs are readable
    - [x] 0.5.3.2 Check database consistency
    - [x] 0.5.3.3 Validate vector DB entries
    - [x] 0.5.3.4 Generate validation report
  - [x] 0.5.4 Write tests for historical data scripts
    - [x] 0.5.4.1 Test download script with mock data
    - [x] 0.5.4.2 Test process script with sample PDFs
    - [x] 0.5.4.3 Test validation script
    - [x] 0.5.4.4 Test error recovery
  - [x] 0.5.5 Generate data and populate database locally

### Week 1-2: Core NLP Components

- [-] 1. MP Identification System
  - [x] 1.1 Implement MPIdentifier class
    - [x] 1.1.1 Create MPMatch dataclass
    - [x] 1.1.2 Implement regex patterns for name formats
    - [x] 1.1.3 Implement spaCy NER integration
    - [x] 1.1.4 Implement database caching
    - [x] 1.1.5 Implement fuzzy matching with fuzzywuzzy
    - [x] 1.1.6 Implement batch identification
  - [x] 1.2 Write unit tests
    - [x] 1.2.1 Test exact name matching
    - [x] 1.2.2 Test fuzzy name matching
    - [x] 1.2.3 Test constituency/party boosting
    - [x] 1.2.4 Test batch processing
    - [x] 1.2.5 Test cache performance
  - [x] 1.3 Write property-based tests
    - [x] 1.3.1 Property 1.1: MP identification accuracy ≥95%
    - [x] 1.3.2 Property 1.2: Name variation handling

- [x] 2. Statement Segmentation
  - [x] 2.1 Implement StatementSegmenter class
    - [x] 2.1.1 Create Statement dataclass
    - [x] 2.1.2 Implement boundary detection patterns
    - [x] 2.1.3 Implement segmentation algorithm
    - [x] 2.1.4 Implement text cleaning
    - [x] 2.1.5 Integrate MP identification
  - [x] 2.2 Write unit tests
    - [x] 2.2.1 Test boundary detection
    - [x] 2.2.2 Test segmentation accuracy
    - [x] 2.2.3 Test text cleaning
    - [x] 2.2.4 Test edge cases (short statements, headers)
  - [x] 2.3 Write property-based tests
    - [x] 2.3.1 Property 2.1: Segmentation accuracy ≥98%
    - [x] 2.3.2 Property 2.2: No statement loss

- [x] 3. Statement Classification (Filler Detection)
  - [x] 3.1 Implement FillerDetector class
    - [x] 3.1.1 Create StatementType enum
    - [x] 3.1.2 Define filler patterns for each type
    - [x] 3.1.3 Implement pattern matching
    - [x] 3.1.4 Implement length-based classification
    - [x] 3.1.5 Implement is_substantive helper
  - [x] 3.2 Write unit tests
    - [x] 3.2.1 Test procedural detection
    - [x] 3.2.2 Test interruption detection
    - [x] 3.2.3 Test administrative detection
    - [x] 3.2.4 Test short acknowledgment detection
    - [x] 3.2.5 Test substantive classification
  - [x] 3.3 Write property-based tests
    - [x] 3.3.1 Property 3.1: Filler detection precision ≥90%
    - [x] 3.3.2 Property 3.2: No false negatives on substantive


### Week 3-4: LLM Integration

- [x] 4. Context Retrieval (RAG)
  - [x] 4.1 Implement ContextRetriever class
    - [x] 4.1.1 Create RetrievedContext dataclass
    - [x] 4.1.2 Initialize sentence-transformers embedder
    - [x] 4.1.3 Implement historical statement retrieval
    - [x] 4.1.4 Implement related bills retrieval
    - [x] 4.1.5 Implement related votes retrieval
    - [x] 4.1.6 Implement session context retrieval
  - [x] 4.2 Write unit tests
    - [x] 4.2.1 Test embedding generation
    - [x] 4.2.2 Test historical retrieval
    - [x] 4.2.3 Test bill retrieval
    - [x] 4.2.4 Test vote retrieval
    - [x] 4.2.5 Test result deduplication
  - [x] 4.3 Write property-based tests
    - [x] 4.3.1 Property 4.1: Context relevance
    - [x] 4.3.2 Property 4.2: Context diversity

- [x] 5. LLM Analysis
  - [x] 5.1 Implement LLMAnalyzer class
    - [x] 5.1.1 Create StatementAnalysis Pydantic model
    - [x] 5.1.2 Initialize Anthropic client
    - [x] 5.1.3 Implement system prompt
    - [x] 5.1.4 Implement prompt building with context
    - [x] 5.1.5 Implement API call with error handling
    - [x] 5.1.6 Implement response parsing
    - [x] 5.1.7 Implement batch analysis
  - [x] 5.2 Write unit tests
    - [x] 5.2.1 Test prompt building
    - [x] 5.2.2 Test response parsing
    - [x] 5.2.3 Test error handling
    - [x] 5.2.4 Test batch processing
    - [x] 5.2.5 Mock API calls for testing
  - [x] 5.3 Write property-based tests
    - [x] 5.3.1 Property 5.1: Sentiment accuracy ≥80%
    - [x] 5.3.2 Property 5.2: Quality score consistency

- [x] 6. Citation Verification
  - [x] 6.1 Implement CitationVerifier class
    - [x] 6.1.1 Create Citation dataclass
    - [x] 6.1.2 Implement source fetching
    - [x] 6.1.3 Implement exact match verification
    - [x] 6.1.4 Implement fuzzy match verification
    - [x] 6.1.5 Implement best match finding
    - [x] 6.1.6 Implement batch verification
  - [x] 6.2 Write unit tests
    - [x] 6.2.1 Test exact matching
    - [x] 6.2.2 Test fuzzy matching
    - [x] 6.2.3 Test threshold handling
    - [x] 6.2.4 Test batch verification
    - [x] 6.2.5 Test error cases
  - [x] 6.3 Write property-based tests
    - [x] 6.3.1 Property 6.1: Citation verification accuracy
    - [x] 6.3.2 Property 6.2: No false verifications

- [ ] 7. Cost Management
  - [x] 7.1 Implement CostManager class
    - [x] 7.1.1 Create APIUsage dataclass
    - [x] 7.1.2 Implement usage tracking
    - [x] 7.1.3 Implement cost calculation
    - [x] 7.1.4 Implement budget checking
    - [x] 7.1.5 Implement Prometheus metrics emission
    - [x] 7.1.6 Implement monthly usage reports
  - [x] 7.2 Write unit tests
    - [x] 7.2.1 Test usage tracking
    - [x] 7.2.2 Test cost calculation
    - [x] 7.2.3 Test budget enforcement
    - [x] 7.2.4 Test daily/monthly aggregation
    - [x] 7.2.5 Test usage reports
  - [x] 7.3 Write property-based tests
    - [x] 7.3.1 Property 13.1: Cost tracking accuracy
    - [x] 7.3.2 Property 13.2: Budget enforcement


### Week 5-6: Document Processing

- [x] 8. Vote Processing
  - [x] 8.1 Implement VoteProcessor class
    - [x] 8.1.1 Create VoteRecord and MPVote dataclasses
    - [x] 8.1.2 Implement PDF table extraction
    - [x] 8.1.3 Implement vote table detection
    - [x] 8.1.4 Implement vote parsing
    - [x] 8.1.5 Implement MP matching
    - [x] 8.1.6 Implement vote totals calculation
  - [x] 8.2 Write unit tests
    - [x] 8.2.1 Test table detection
    - [x] 8.2.2 Test vote parsing
    - [x] 8.2.3 Test MP matching
    - [x] 8.2.4 Test totals calculation
    - [x] 8.2.5 Test edge cases
  - [x] 8.3 Write property-based tests
    - [x] 8.3.1 Property 7.1: Vote extraction completeness
    - [x] 8.3.2 Property 7.2: MP vote accuracy

- [x] 9. Bill-Statement Linking
  - [x] 9.1 Implement BillStatementLinker class
    - [x] 9.1.1 Create BillMention dataclass
    - [x] 9.1.2 Implement bill mention patterns
    - [x] 9.1.3 Implement pattern-based extraction
    - [x] 9.1.4 Implement bill resolution
    - [x] 9.1.5 Implement vector similarity disambiguation
    - [x] 9.1.6 Implement context extraction
  - [x] 9.2 Write unit tests
    - [x] 9.2.1 Test pattern matching
    - [x] 9.2.2 Test bill resolution
    - [x] 9.2.3 Test disambiguation
    - [x] 9.2.4 Test context extraction
    - [x] 9.2.5 Test edge cases
  - [x] 9.3 Write property-based tests
    - [x] 9.3.1 Property 8.1: Bill mention detection recall ≥90%
    - [x] 9.3.2 Property 8.2: Bill resolution accuracy

- [x] 10. MP Profile Generation
  - [x] 10.1 Implement MPProfileGenerator class
    - [x] 10.1.1 Create MPProfile dataclass
    - [x] 10.1.2 Implement statistics aggregation
    - [x] 10.1.3 Implement topic aggregation
    - [x] 10.1.4 Implement bill aggregation
    - [x] 10.1.5 Implement LLM summary generation
    - [x] 10.1.6 Implement batch profile generation
  - [x] 10.2 Write unit tests
    - [x] 10.2.1 Test statistics aggregation
    - [x] 10.2.2 Test topic aggregation
    - [x] 10.2.3 Test summary generation
    - [x] 10.2.4 Test batch processing
    - [x] 10.2.5 Test edge cases
  - [x] 10.3 Write property-based tests
    - [x] 10.3.1 Property 9.1: Profile completeness
    - [x] 10.3.2 Property 9.2: Statistics accuracy

- [x] 11. Session Summary Generation
  - [x] 11.1 Implement SessionSummaryGenerator class
    - [x] 11.1.1 Create SessionSummary dataclass
    - [x] 11.1.2 Implement statement aggregation
    - [x] 11.1.3 Implement LLM summary generation
    - [x] 11.1.4 Implement structured parsing
    - [x] 11.1.5 Implement bill/vote linking
    - [x] 11.1.6 Implement batch generation
  - [x] 11.2 Write unit tests
    - [x] 11.2.1 Test statement aggregation
    - [x] 11.2.2 Test summary generation
    - [x] 11.2.3 Test structured parsing
    - [x] 11.2.4 Test batch processing
    - [x] 11.2.5 Test edge cases
  - [x] 11.3 Write property-based tests
    - [x] 11.3.1 Property 10.1: Summary accuracy
    - [x] 11.3.2 Property 10.2: Key event extraction


### Week 7-8: Site Generation & Polish

- [x] 12. Static Site Generation
  - [x] 12.1 Implement StaticSiteGenerator class
    - [x] 12.1.1 Setup Jinja2 environment
    - [x] 12.1.2 Implement homepage generation
    - [x] 12.1.3 Implement MP pages generation
    - [x] 12.1.4 Implement session pages generation
    - [x] 12.1.5 Implement bill pages generation
    - [x] 12.1.6 Implement party pages generation
    - [x] 12.1.7 Implement search page generation
    - [x] 12.1.8 Implement static asset copying
  - [x] 12.2 Create Jinja2 templates
    - [x] 12.2.1 Create base layout template
    - [x] 12.2.2 Create homepage template
    - [x] 12.2.3 Create MP list template
    - [x] 12.2.4 Create MP profile template
    - [x] 12.2.5 Create session list template
    - [x] 12.2.6 Create session detail template
    - [x] 12.2.7 Create bill templates
    - [x] 12.2.8 Create party templates
    - [x] 12.2.9 Create search template
  - [x] 12.3 Write unit tests
    - [x] 12.3.1 Test homepage generation
    - [x] 12.3.2 Test MP page generation
    - [x] 12.3.3 Test session page generation
    - [x] 12.3.4 Test template rendering
    - [x] 12.3.5 Test link generation
  - [x] 12.4 Write property-based tests
    - [x] 12.4.1 Property 11.1: Page generation completeness
    - [x] 12.4.2 Property 11.2: Link validity

- [x] 13. Pipeline Orchestration
  - [x] 13.1 Implement ProcessingPipeline class
    - [x] 13.1.1 Create PipelineStage enum
    - [x] 13.1.2 Create PipelineResult dataclass
    - [x] 13.1.3 Initialize all components
    - [x] 13.1.4 Implement Hansard processing pipeline
    - [x] 13.1.5 Implement Votes processing pipeline
    - [x] 13.1.6 Implement stage execution with timing
    - [x] 13.1.7 Implement error handling
    - [x] 13.1.8 Implement result storage
  - [x] 13.2 Write unit tests
    - [x] 13.2.1 Test stage execution
    - [x] 13.2.2 Test error handling
    - [x] 13.2.3 Test result storage
    - [x] 13.2.4 Test pipeline completion
    - [x] 13.2.5 Test parallel processing
  - [x] 13.3 Write property-based tests
    - [x] 13.3.1 Property 12.1: Pipeline completeness
    - [x] 13.3.2 Property 12.2: Error recovery

- [x] 14. Monitoring and Observability
  - [x] 14.1 Implement MonitoringService class
    - [x] 14.1.1 Define Prometheus metrics
    - [x] 14.1.2 Configure structlog
    - [x] 14.1.3 Implement statement tracking
    - [x] 14.1.4 Implement stage duration tracking
    - [x] 14.1.5 Implement LLM call tracking
    - [x] 14.1.6 Implement error tracking
    - [x] 14.1.7 Implement metrics endpoint
  - [x] 14.2 Write unit tests
    - [x] 14.2.1 Test metric recording
    - [x] 14.2.2 Test log formatting
    - [x] 14.2.3 Test error logging
    - [x] 14.2.4 Test metrics endpoint
  - [x] 14.3 Write property-based tests
    - [x] 14.3.1 Property 14.1: Metrics accuracy
    - [x] 14.3.2 Property 14.2: Error logging completeness

- [x] 15. Integration and End-to-End Testing
  - [x] 15.1 Integration tests
    - [x] 15.1.1 Test MP identification → Segmentation
    - [x] 15.1.2 Test Segmentation → Classification
    - [x] 15.1.3 Test Classification → Context Retrieval
    - [x] 15.1.4 Test Context Retrieval → LLM Analysis
    - [x] 15.1.5 Test LLM Analysis → Citation Verification
    - [x] 15.1.6 Test Vote Processing → Database Storage
    - [x] 15.1.7 Test Bill Linking → Profile Generation
    - [x] 15.1.8 Test Profile Generation → Site Generation
  - [x] 15.2 End-to-end tests
    - [x] 15.2.1 Process complete Hansard PDF
    - [x] 15.2.2 Process complete Votes PDF
    - [x] 15.2.3 Generate MP profiles
    - [x] 15.2.4 Generate session summaries
    - [x] 15.2.5 Generate static site
    - [x] 15.2.6 Verify site content
    - [x] 15.2.7 Measure performance
    - [x] 15.2.8 Verify cost tracking
  - [x] 15.3 Performance testing
    - [x] 15.3.1 Benchmark Hansard processing time
    - [x] 15.3.2 Benchmark LLM API calls
    - [x] 15.3.3 Benchmark vector DB queries
    - [x] 15.3.4 Benchmark site generation
    - [x] 15.3.5 Optimize bottlenecks

- [ ] 16. Configuration and Documentation
  - [x] 16.1 Configuration
    - [x] 16.1.1 Create phase1.yaml config file
    - [x] 16.1.2 Document all configuration options
    - [x] 16.1.3 Create example configurations
    - [x] 16.1.4 Add configuration validation
  - [x] 16.2 Documentation
    - [x] 16.2.1 Write setup instructions
    - [x] 16.2.2 Write usage guide
    - [x] 16.2.3 Document API endpoints
    - [x] 16.2.4 Create example scripts
    - [x] 16.2.5 Document troubleshooting
  - [x] 16.3 Code documentation
    - [x] 16.3.1 Add docstrings to all classes
    - [x] 16.3.2 Add docstrings to all functions
    - [x] 16.3.3 Generate API documentation
    - [x] 16.3.4 Add inline comments for complex logic

---

## Summary

**Total Tasks**: 17 major tasks (including Phase 0 technical debt)
**Total Subtasks**: 210+ subtasks
**Timeline**: 9 weeks (1 week for technical debt + 8 weeks for core analysis)
**Test Coverage Target**: ≥90%

**Key Milestones**:
- Week 1: Phase 0 technical debt resolved, historical data scripts complete
- Week 3: Core NLP components complete
- Week 5: LLM integration complete
- Week 7: Document processing complete
- Week 9: Site generation and polish complete

**Dependencies**:
- Phase 0 must be complete before starting Phase 1
- Task 0 (technical debt) should be completed first for clean foundation
- Tasks 1-3 must complete before Task 4
- Tasks 4-7 must complete before Tasks 8-11
- Tasks 8-11 must complete before Task 12
- Task 13 requires all previous tasks
- Task 14 can run in parallel with other tasks
- Tasks 15-16 are final integration and documentation

**Phase 0 Technical Debt Items**:
- Increase test coverage for Qdrant adapter, Votes scraper, Base scraper
- Add comprehensive type annotations for mypy compliance
- Implement date range filtering in scrapers
- Add support for multiple parliament terms
- Create historical data processing scripts
