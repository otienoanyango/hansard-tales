# Phase 1: Core Analysis Pipeline - Implementation Tasks

## Overview

This document breaks down Phase 1 implementation into actionable tasks. Each task includes acceptance criteria, property-based tests, and dependencies.

**Timeline**: 8 weeks
**Test Coverage Target**: ≥90%
**Dependencies**: Phase 0 must be complete

---

## Tasks

### Week 0: Technical Debt from Phase 0

- [ ] 0. Address Phase 0 Technical Debt
  - [ ] 0.1 Improve Test Coverage
    - [ ] 0.1.1 Increase Qdrant adapter coverage from 37.93% to ≥80%
    - [ ] 0.1.2 Increase Votes scraper coverage from 76.85% to ≥85%
    - [ ] 0.1.3 Increase Base scraper coverage from 79.25% to ≥85%
    - [ ] 0.1.4 Add tests for uncovered error handling paths
  - [ ] 0.2 Type Annotations
    - [ ] 0.2.1 Add type annotations to example scripts
    - [ ] 0.2.2 Add type annotations to utility functions
    - [ ] 0.2.3 Fix Alembic migration type issues
    - [ ] 0.2.4 Enable mypy in pre-commit hooks
  - [ ] 0.3 Scraper Enhancements
    - [ ] 0.3.1 Implement date range filtering (start_date, end_date parameters)
    - [ ] 0.3.2 Add support for multiple parliament terms
    - [ ] 0.3.3 Implement parallel page fetching with connection pooling
    - [ ] 0.3.4 Add progress reporting for long-running scrapes

- [ ] 0.4 Historical Data Processing Scripts
  - [ ] 0.4.1 Create `scripts/download_historical_data.py`
    - [ ] 0.4.1.1 Implement parliament term iteration (2013-2024)
    - [ ] 0.4.1.2 Implement date range support
    - [ ] 0.4.1.3 Add progress tracking with tqdm
    - [ ] 0.4.1.4 Add resume capability (skip already downloaded)
    - [ ] 0.4.1.5 Add summary statistics reporting
    - [ ] 0.4.1.6 Add error logging and recovery
  - [ ] 0.4.2 Create `scripts/process_historical_data.py`
    - [ ] 0.4.2.1 Implement batch PDF processing
    - [ ] 0.4.2.2 Add parallel processing with worker pool
    - [ ] 0.4.2.3 Add progress tracking
    - [ ] 0.4.2.4 Add error recovery and retry logic
    - [ ] 0.4.2.5 Add validation and quality checks
    - [ ] 0.4.2.6 Generate processing report
  - [ ] 0.4.3 Create `scripts/validate_historical_data.py`
    - [ ] 0.4.3.1 Verify all PDFs are readable
    - [ ] 0.4.3.2 Check database consistency
    - [ ] 0.4.3.3 Validate vector DB entries
    - [ ] 0.4.3.4 Generate validation report
  - [ ] 0.4.4 Write tests for historical data scripts
    - [ ] 0.4.4.1 Test download script with mock data
    - [ ] 0.4.4.2 Test process script with sample PDFs
    - [ ] 0.4.4.3 Test validation script
    - [ ] 0.4.4.4 Test error recovery

### Week 1-2: Core NLP Components

- [ ] 1. MP Identification System
  - [ ] 1.1 Implement MPIdentifier class
    - [ ] 1.1.1 Create MPMatch dataclass
    - [ ] 1.1.2 Implement regex patterns for name formats
    - [ ] 1.1.3 Implement spaCy NER integration
    - [ ] 1.1.4 Implement database caching
    - [ ] 1.1.5 Implement fuzzy matching with fuzzywuzzy
    - [ ] 1.1.6 Implement batch identification
  - [ ] 1.2 Write unit tests
    - [ ] 1.2.1 Test exact name matching
    - [ ] 1.2.2 Test fuzzy name matching
    - [ ] 1.2.3 Test constituency/party boosting
    - [ ] 1.2.4 Test batch processing
    - [ ] 1.2.5 Test cache performance
  - [ ] 1.3 Write property-based tests
    - [ ] 1.3.1 Property 1.1: MP identification accuracy ≥95%
    - [ ] 1.3.2 Property 1.2: Name variation handling

- [ ] 2. Statement Segmentation
  - [ ] 2.1 Implement StatementSegmenter class
    - [ ] 2.1.1 Create Statement dataclass
    - [ ] 2.1.2 Implement boundary detection patterns
    - [ ] 2.1.3 Implement segmentation algorithm
    - [ ] 2.1.4 Implement text cleaning
    - [ ] 2.1.5 Integrate MP identification
  - [ ] 2.2 Write unit tests
    - [ ] 2.2.1 Test boundary detection
    - [ ] 2.2.2 Test segmentation accuracy
    - [ ] 2.2.3 Test text cleaning
    - [ ] 2.2.4 Test edge cases (short statements, headers)
  - [ ] 2.3 Write property-based tests
    - [ ] 2.3.1 Property 2.1: Segmentation accuracy ≥98%
    - [ ] 2.3.2 Property 2.2: No statement loss

- [ ] 3. Statement Classification (Filler Detection)
  - [ ] 3.1 Implement FillerDetector class
    - [ ] 3.1.1 Create StatementType enum
    - [ ] 3.1.2 Define filler patterns for each type
    - [ ] 3.1.3 Implement pattern matching
    - [ ] 3.1.4 Implement length-based classification
    - [ ] 3.1.5 Implement is_substantive helper
  - [ ] 3.2 Write unit tests
    - [ ] 3.2.1 Test procedural detection
    - [ ] 3.2.2 Test interruption detection
    - [ ] 3.2.3 Test administrative detection
    - [ ] 3.2.4 Test short acknowledgment detection
    - [ ] 3.2.5 Test substantive classification
  - [ ] 3.3 Write property-based tests
    - [ ] 3.3.1 Property 3.1: Filler detection precision ≥90%
    - [ ] 3.3.2 Property 3.2: No false negatives on substantive


### Week 3-4: LLM Integration

- [ ] 4. Context Retrieval (RAG)
  - [ ] 4.1 Implement ContextRetriever class
    - [ ] 4.1.1 Create RetrievedContext dataclass
    - [ ] 4.1.2 Initialize sentence-transformers embedder
    - [ ] 4.1.3 Implement historical statement retrieval
    - [ ] 4.1.4 Implement related bills retrieval
    - [ ] 4.1.5 Implement related votes retrieval
    - [ ] 4.1.6 Implement session context retrieval
  - [ ] 4.2 Write unit tests
    - [ ] 4.2.1 Test embedding generation
    - [ ] 4.2.2 Test historical retrieval
    - [ ] 4.2.3 Test bill retrieval
    - [ ] 4.2.4 Test vote retrieval
    - [ ] 4.2.5 Test result deduplication
  - [ ] 4.3 Write property-based tests
    - [ ] 4.3.1 Property 4.1: Context relevance
    - [ ] 4.3.2 Property 4.2: Context diversity

- [ ] 5. LLM Analysis
  - [ ] 5.1 Implement LLMAnalyzer class
    - [ ] 5.1.1 Create StatementAnalysis Pydantic model
    - [ ] 5.1.2 Initialize Anthropic client
    - [ ] 5.1.3 Implement system prompt
    - [ ] 5.1.4 Implement prompt building with context
    - [ ] 5.1.5 Implement API call with error handling
    - [ ] 5.1.6 Implement response parsing
    - [ ] 5.1.7 Implement batch analysis
  - [ ] 5.2 Write unit tests
    - [ ] 5.2.1 Test prompt building
    - [ ] 5.2.2 Test response parsing
    - [ ] 5.2.3 Test error handling
    - [ ] 5.2.4 Test batch processing
    - [ ] 5.2.5 Mock API calls for testing
  - [ ] 5.3 Write property-based tests
    - [ ] 5.3.1 Property 5.1: Sentiment accuracy ≥80%
    - [ ] 5.3.2 Property 5.2: Quality score consistency

- [ ] 6. Citation Verification
  - [ ] 6.1 Implement CitationVerifier class
    - [ ] 6.1.1 Create Citation dataclass
    - [ ] 6.1.2 Implement source fetching
    - [ ] 6.1.3 Implement exact match verification
    - [ ] 6.1.4 Implement fuzzy match verification
    - [ ] 6.1.5 Implement best match finding
    - [ ] 6.1.6 Implement batch verification
  - [ ] 6.2 Write unit tests
    - [ ] 6.2.1 Test exact matching
    - [ ] 6.2.2 Test fuzzy matching
    - [ ] 6.2.3 Test threshold handling
    - [ ] 6.2.4 Test batch verification
    - [ ] 6.2.5 Test error cases
  - [ ] 6.3 Write property-based tests
    - [ ] 6.3.1 Property 6.1: Citation verification accuracy
    - [ ] 6.3.2 Property 6.2: No false verifications

- [ ] 7. Cost Management
  - [ ] 7.1 Implement CostManager class
    - [ ] 7.1.1 Create APIUsage dataclass
    - [ ] 7.1.2 Implement usage tracking
    - [ ] 7.1.3 Implement cost calculation
    - [ ] 7.1.4 Implement budget checking
    - [ ] 7.1.5 Implement caching
    - [ ] 7.1.6 Implement monthly usage reports
  - [ ] 7.2 Write unit tests
    - [ ] 7.2.1 Test usage tracking
    - [ ] 7.2.2 Test cost calculation
    - [ ] 7.2.3 Test budget enforcement
    - [ ] 7.2.4 Test caching
    - [ ] 7.2.5 Test usage reports
  - [ ] 7.3 Write property-based tests
    - [ ] 7.3.1 Property 13.1: Cost tracking accuracy
    - [ ] 7.3.2 Property 13.2: Budget enforcement


### Week 5-6: Document Processing

- [ ] 8. Vote Processing
  - [ ] 8.1 Implement VoteProcessor class
    - [ ] 8.1.1 Create VoteRecord and MPVote dataclasses
    - [ ] 8.1.2 Implement PDF table extraction
    - [ ] 8.1.3 Implement vote table detection
    - [ ] 8.1.4 Implement vote parsing
    - [ ] 8.1.5 Implement MP matching
    - [ ] 8.1.6 Implement vote totals calculation
  - [ ] 8.2 Write unit tests
    - [ ] 8.2.1 Test table detection
    - [ ] 8.2.2 Test vote parsing
    - [ ] 8.2.3 Test MP matching
    - [ ] 8.2.4 Test totals calculation
    - [ ] 8.2.5 Test edge cases
  - [ ] 8.3 Write property-based tests
    - [ ] 8.3.1 Property 7.1: Vote extraction completeness
    - [ ] 8.3.2 Property 7.2: MP vote accuracy

- [ ] 9. Bill-Statement Linking
  - [ ] 9.1 Implement BillStatementLinker class
    - [ ] 9.1.1 Create BillMention dataclass
    - [ ] 9.1.2 Implement bill mention patterns
    - [ ] 9.1.3 Implement pattern-based extraction
    - [ ] 9.1.4 Implement bill resolution
    - [ ] 9.1.5 Implement vector similarity disambiguation
    - [ ] 9.1.6 Implement context extraction
  - [ ] 9.2 Write unit tests
    - [ ] 9.2.1 Test pattern matching
    - [ ] 9.2.2 Test bill resolution
    - [ ] 9.2.3 Test disambiguation
    - [ ] 9.2.4 Test context extraction
    - [ ] 9.2.5 Test edge cases
  - [ ] 9.3 Write property-based tests
    - [ ] 9.3.1 Property 8.1: Bill mention detection recall ≥90%
    - [ ] 9.3.2 Property 8.2: Bill resolution accuracy

- [ ] 10. MP Profile Generation
  - [ ] 10.1 Implement MPProfileGenerator class
    - [ ] 10.1.1 Create MPProfile dataclass
    - [ ] 10.1.2 Implement statistics aggregation
    - [ ] 10.1.3 Implement topic aggregation
    - [ ] 10.1.4 Implement bill aggregation
    - [ ] 10.1.5 Implement LLM summary generation
    - [ ] 10.1.6 Implement batch profile generation
  - [ ] 10.2 Write unit tests
    - [ ] 10.2.1 Test statistics aggregation
    - [ ] 10.2.2 Test topic aggregation
    - [ ] 10.2.3 Test summary generation
    - [ ] 10.2.4 Test batch processing
    - [ ] 10.2.5 Test edge cases
  - [ ] 10.3 Write property-based tests
    - [ ] 10.3.1 Property 9.1: Profile completeness
    - [ ] 10.3.2 Property 9.2: Statistics accuracy

- [ ] 11. Session Summary Generation
  - [ ] 11.1 Implement SessionSummaryGenerator class
    - [ ] 11.1.1 Create SessionSummary dataclass
    - [ ] 11.1.2 Implement statement aggregation
    - [ ] 11.1.3 Implement LLM summary generation
    - [ ] 11.1.4 Implement structured parsing
    - [ ] 11.1.5 Implement bill/vote linking
    - [ ] 11.1.6 Implement batch generation
  - [ ] 11.2 Write unit tests
    - [ ] 11.2.1 Test statement aggregation
    - [ ] 11.2.2 Test summary generation
    - [ ] 11.2.3 Test structured parsing
    - [ ] 11.2.4 Test batch processing
    - [ ] 11.2.5 Test edge cases
  - [ ] 11.3 Write property-based tests
    - [ ] 11.3.1 Property 10.1: Summary accuracy
    - [ ] 11.3.2 Property 10.2: Key event extraction


### Week 7-8: Site Generation & Polish

- [ ] 12. Static Site Generation
  - [ ] 12.1 Implement StaticSiteGenerator class
    - [ ] 12.1.1 Setup Jinja2 environment
    - [ ] 12.1.2 Implement homepage generation
    - [ ] 12.1.3 Implement MP pages generation
    - [ ] 12.1.4 Implement session pages generation
    - [ ] 12.1.5 Implement bill pages generation
    - [ ] 12.1.6 Implement party pages generation
    - [ ] 12.1.7 Implement search page generation
    - [ ] 12.1.8 Implement static asset copying
  - [ ] 12.2 Create Jinja2 templates
    - [ ] 12.2.1 Create base layout template
    - [ ] 12.2.2 Create homepage template
    - [ ] 12.2.3 Create MP list template
    - [ ] 12.2.4 Create MP profile template
    - [ ] 12.2.5 Create session list template
    - [ ] 12.2.6 Create session detail template
    - [ ] 12.2.7 Create bill templates
    - [ ] 12.2.8 Create party templates
    - [ ] 12.2.9 Create search template
  - [ ] 12.3 Write unit tests
    - [ ] 12.3.1 Test homepage generation
    - [ ] 12.3.2 Test MP page generation
    - [ ] 12.3.3 Test session page generation
    - [ ] 12.3.4 Test template rendering
    - [ ] 12.3.5 Test link generation
  - [ ] 12.4 Write property-based tests
    - [ ] 12.4.1 Property 11.1: Page generation completeness
    - [ ] 12.4.2 Property 11.2: Link validity

- [ ] 13. Pipeline Orchestration
  - [ ] 13.1 Implement ProcessingPipeline class
    - [ ] 13.1.1 Create PipelineStage enum
    - [ ] 13.1.2 Create PipelineResult dataclass
    - [ ] 13.1.3 Initialize all components
    - [ ] 13.1.4 Implement Hansard processing pipeline
    - [ ] 13.1.5 Implement Votes processing pipeline
    - [ ] 13.1.6 Implement stage execution with timing
    - [ ] 13.1.7 Implement error handling
    - [ ] 13.1.8 Implement result storage
  - [ ] 13.2 Write unit tests
    - [ ] 13.2.1 Test stage execution
    - [ ] 13.2.2 Test error handling
    - [ ] 13.2.3 Test result storage
    - [ ] 13.2.4 Test pipeline completion
    - [ ] 13.2.5 Test parallel processing
  - [ ] 13.3 Write property-based tests
    - [ ] 13.3.1 Property 12.1: Pipeline completeness
    - [ ] 13.3.2 Property 12.2: Error recovery

- [ ] 14. Monitoring and Observability
  - [ ] 14.1 Implement MonitoringService class
    - [ ] 14.1.1 Define Prometheus metrics
    - [ ] 14.1.2 Configure structlog
    - [ ] 14.1.3 Implement statement tracking
    - [ ] 14.1.4 Implement stage duration tracking
    - [ ] 14.1.5 Implement LLM call tracking
    - [ ] 14.1.6 Implement error tracking
    - [ ] 14.1.7 Implement metrics endpoint
  - [ ] 14.2 Write unit tests
    - [ ] 14.2.1 Test metric recording
    - [ ] 14.2.2 Test log formatting
    - [ ] 14.2.3 Test error logging
    - [ ] 14.2.4 Test metrics endpoint
  - [ ] 14.3 Write property-based tests
    - [ ] 14.3.1 Property 14.1: Metrics accuracy
    - [ ] 14.3.2 Property 14.2: Error logging completeness

- [ ] 15. Integration and End-to-End Testing
  - [ ] 15.1 Integration tests
    - [ ] 15.1.1 Test MP identification → Segmentation
    - [ ] 15.1.2 Test Segmentation → Classification
    - [ ] 15.1.3 Test Classification → Context Retrieval
    - [ ] 15.1.4 Test Context Retrieval → LLM Analysis
    - [ ] 15.1.5 Test LLM Analysis → Citation Verification
    - [ ] 15.1.6 Test Vote Processing → Database Storage
    - [ ] 15.1.7 Test Bill Linking → Profile Generation
    - [ ] 15.1.8 Test Profile Generation → Site Generation
  - [ ] 15.2 End-to-end tests
    - [ ] 15.2.1 Process complete Hansard PDF
    - [ ] 15.2.2 Process complete Votes PDF
    - [ ] 15.2.3 Generate MP profiles
    - [ ] 15.2.4 Generate session summaries
    - [ ] 15.2.5 Generate static site
    - [ ] 15.2.6 Verify site content
    - [ ] 15.2.7 Measure performance
    - [ ] 15.2.8 Verify cost tracking
  - [ ] 15.3 Performance testing
    - [ ] 15.3.1 Benchmark Hansard processing time
    - [ ] 15.3.2 Benchmark LLM API calls
    - [ ] 15.3.3 Benchmark vector DB queries
    - [ ] 15.3.4 Benchmark site generation
    - [ ] 15.3.5 Optimize bottlenecks

- [ ] 16. Configuration and Documentation
  - [ ] 16.1 Configuration
    - [ ] 16.1.1 Create phase1.yaml config file
    - [ ] 16.1.2 Document all configuration options
    - [ ] 16.1.3 Create example configurations
    - [ ] 16.1.4 Add configuration validation
  - [ ] 16.2 Documentation
    - [ ] 16.2.1 Write setup instructions
    - [ ] 16.2.2 Write usage guide
    - [ ] 16.2.3 Document API endpoints
    - [ ] 16.2.4 Create example scripts
    - [ ] 16.2.5 Document troubleshooting
  - [ ] 16.3 Code documentation
    - [ ] 16.3.1 Add docstrings to all classes
    - [ ] 16.3.2 Add docstrings to all functions
    - [ ] 16.3.3 Generate API documentation
    - [ ] 16.3.4 Add inline comments for complex logic

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
