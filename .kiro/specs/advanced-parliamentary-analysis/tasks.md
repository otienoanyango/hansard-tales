# Implementation Plan: Advanced Parliamentary Analysis

## Overview

This implementation plan breaks down the advanced parliamentary analysis system into discrete, manageable tasks. The plan follows an incremental approach, building core analysis capabilities first, then enhancing pages, and finally adding content features. Each task builds on previous work, with checkpoints to ensure quality.

## Architecture Updates

**RAG (Retrieval-Augmented Generation)**: The system uses a dual-storage architecture:
- **SQLite**: Structured, queryable data (MP metadata, votes, analysis results)
- **ChromaDB**: Full document text with embeddings for semantic search
- **Context Retrieval**: Before analyzing any statement, the system retrieves relevant context from previous sessions, bill amendments, and related documents

**LLM-based Analysis**: Sentiment and quality analysis use LLMs (Claude 3.5 Haiku or GPT-4o-mini) instead of spaCy for:
- Superior context understanding across multiple sessions
- Nuanced sentiment detection (sarcasm, indirect speech)
- Zero configuration (no keyword maintenance)
- Cost: ~$50-80/year for 20k statements

**Anti-Hallucination Measures**: Critical for civic accountability:
- **Structured output**: LLM must provide citations for all claims
- **Citation verification**: All citations verified against source documents (≥90% similarity)
- **No content generation**: LLM only classifies/ranks, never generates statement text
- **Audit trail**: Every LLM decision logged with prompt, response, verification results
- **Source references**: Immutable links to official Hansard PDFs (URL, hash, page number)
- **Human review queue**: Low-confidence analyses flagged for review

**Traditional NLP (spaCy)**: Still used for:
- Filler statement detection (rule-based patterns work well)
- Topic classification (keyword-based with TF-IDF)
- Fast, deterministic processing without API costs

## Tasks

- [ ] 1. Database ORM and migration system setup
  - [ ] 1.1 Set up SQLAlchemy ORM with Alembic migrations
    - Install SQLAlchemy and Alembic
    - Configure Alembic for the project
    - Create base model classes
    - Set up migration environment
    - **Note**: Using ORM future-proofs database changes and prevents costly reprocessing
    - _Requirements: 18.10_
  
  - [ ] 1.2 Define SQLAlchemy models for all tables
    - Define Statement, MP, Session, Bill models (existing)
    - Define StatementClassification model
    - Define StatementSentiment model (with evidence_citations JSON field)
    - Define StatementQualityScore model
    - Define BillTopic and StatementTopic models
    - Define VoteRecord model
    - Define AttendanceRecord model
    - Define ConstituencyStatement model
    - Define ProblematicStatement model
    - Define WeeklySummary model
    - Define AnalysisAuditLog model (new)
    - Define HumanReviewQueue model (new)
    - Add source reference fields to Statement model (PDF URL, hash, page number)
    - Add vector_doc_id field to Statement and Bill models
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9_
  
  - [ ] 1.3 Create initial Alembic migration
    - Generate migration from models
    - Review and test migration
    - Document migration process
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9_
  
  - [ ] 1.4 Write property test for schema migration data preservation
    - **Property 47: Schema Migration Data Preservation**
    - **Validates: Requirements 18.10**
  
  - [ ] 1.5 Write unit tests for ORM models
    - Test model creation and relationships
    - Test data validation
    - Test migration execution
    - Test rollback
    - _Requirements: 18.10_
  
  - [ ] 1.6 Set up ChromaDB vector database
    - Install chromadb and sentence-transformers
    - Configure persistent storage directory
    - Create VectorStore class with add_document and search methods
    - Test embedding generation and semantic search
    - **Note**: Vector DB enables multi-session context retrieval
    - _Requirements: 25.1, 25.4, 25.5_
  
  - [ ] 1.7 Write property tests for vector database
    - **Property 56: Vector Storage Completeness**
    - **Validates: Requirements 25.4**
  
  - [ ] 1.8 Write unit tests for vector database
    - Test document storage with embeddings
    - Test semantic search
    - Test metadata filtering
    - Test persistence
    - _Requirements: 25.1, 25.4_

- [ ] 2. Configuration management system
  - [ ] 2.1 Create configuration schema and loader
    - Define YAML schema for all configuration options
    - Implement ConfigLoader class with validation
    - Support environment variable overrides
    - Implement default value fallback
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 20.1, 20.2, 20.3, 20.4, 20.5_
  
  - [ ] 2.2 Create default configuration files
    - Create config/filler_patterns.yaml with etiquette and procedural patterns
    - Create config/topic_taxonomy.yaml with policy topics
    - Create config/quality_scoring.yaml with weights and thresholds
    - Create config/problematic_patterns.yaml with impunity/ignorance/sycophancy patterns
    - Create config/data_sources.yaml with parliament.go.ke URLs
    - _Requirements: 20.1, 20.2, 20.3, 20.5_
  
  - [ ] 2.3 Write property tests for configuration system
    - **Property 48: Configuration Validation**
    - **Property 49: Invalid Configuration Fallback**
    - **Validates: Requirements 20.6, 20.7**
  
  - [ ] 2.4 Write unit tests for configuration loading
    - Test YAML parsing
    - Test validation errors
    - Test default values
    - Test environment variable overrides
    - _Requirements: 20.6, 20.7_

- [ ] 3. Context retrieval system (RAG)
  - [ ] 3.1 Implement ContextRetriever class
    - Create retrieve_bill_context method (gets bill text, amendments, related statements, votes)
    - Create retrieve_mp_context method (gets MP's history with specific bill)
    - Create retrieve_related_documents method (finds related votes, questions, petitions)
    - Use vector database semantic search with metadata filtering
    - Return structured context objects (BillContext, MPContext, RelatedDocs)
    - _Requirements: 25.2, 25.3, 25.6_
  
  - [ ] 3.2 Write property tests for context retrieval
    - **Property 55: Context Retrieval Relevance**
    - **Validates: Requirements 25.2, 25.3**
  
  - [ ] 3.3 Write unit tests for context retriever
    - Test bill context retrieval
    - Test MP context retrieval
    - Test related documents retrieval
    - Test semantic search filtering
    - Test result limiting
    - _Requirements: 25.2, 25.3, 25.6_

- [ ] 4. Statement classifier implementation
  - [ ] 4.1 Implement StatementClassifier class
    - Load filler patterns from configuration
    - Implement pattern matching logic
    - Calculate confidence scores
    - Return Classification with type and reason
    - Support batch classification
    - _Requirements: 1.1, 1.2, 1.3, 1.6_
  
  - [ ] 4.2 Write property tests for statement classification
    - **Property 1: Statement Classification Completeness**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.6**
  
  - [ ] 4.3 Write unit tests for classifier
    - Test etiquette pattern matching
    - Test procedural pattern matching
    - Test substantive statement detection
    - Test confidence scoring
    - Test batch processing
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 5. Citation verifier implementation (anti-hallucination)
  - [ ] 5.1 Implement CitationVerifier class
    - Create verify_citations method that checks all LLM citations
    - Implement quote_exists_in_source with fuzzy matching (≥90% similarity)
    - Use difflib.SequenceMatcher for fuzzy string matching
    - Return VerifiedAnalysis with only verified citations
    - Flag for review if no citations verify
    - Log verification failures to audit trail
    - **Note**: Critical for preventing AI hallucination
    - _Requirements: 26.2, 26.8, 26.9_
  
  - [ ] 5.2 Write property tests for citation verification
    - **Property 57: Citation Verification Requirement**
    - **Property 62: Citation Fuzzy Match Threshold**
    - **Property 63: Failed Citation Rejection**
    - **Validates: Requirements 26.2, 26.8, 26.9**
  
  - [ ] 5.3 Write unit tests for citation verifier
    - Test exact quote matching
    - Test fuzzy quote matching at various thresholds
    - Test citation rejection
    - Test review flagging
    - Test audit logging
    - _Requirements: 26.2, 26.8, 26.9_

- [ ] 6. Sentiment analyzer implementation (LLM-based with RAG)
  - [ ] 6.1 Set up LLM client (Claude 3.5 Haiku or GPT-4o-mini)
    - Install anthropic or openai SDK
    - Configure API keys via environment variables
    - Create LLMClient wrapper class
    - Implement structured output parsing (JSON mode)
    - Add retry logic with exponential backoff
    - **Note**: LLM provides superior context understanding vs spaCy
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [ ] 6.2 Implement SentimentAnalyzer class with RAG
    - Retrieve context using ContextRetriever (bill history, MP history)
    - Build LLM prompt with context and structured output requirements
    - Require LLM to provide citations for all claims
    - Parse LLM JSON response
    - Verify citations using CitationVerifier
    - Store verified results with audit log
    - Flag low-confidence analyses for review
    - **Note**: Never allow LLM to generate statement text, only classify
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 26.1, 26.2, 26.3, 26.5, 26.6_
  
  - [ ] 6.3 Write property tests for sentiment analysis
    - **Property 3: Sentiment Classification Completeness**
    - **Property 4: Low Confidence Flagging**
    - **Property 58: No Generated Content**
    - **Property 60: Low Confidence Review Flagging**
    - **Property 61: Audit Log Completeness**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 26.3, 26.5, 26.6**
  
  - [ ] 6.4 Write unit tests for sentiment analyzer
    - Test context retrieval integration
    - Test LLM prompt construction
    - Test citation verification integration
    - Test confidence thresholding
    - Test review flagging
    - Test audit logging
    - Test error handling (API failures, invalid responses)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 26.2, 26.5, 26.6_

- [ ] 7. Quality scorer implementation
  - [ ] 7.1 Implement QualityScorer class
    - Load scoring weights from configuration
    - Implement length scoring (0-20 points)
    - Implement specificity scoring (0-25 points)
    - Implement evidence scoring (0-25 points)
    - Implement coherence scoring (0-15 points)
    - Implement impact scoring (0-15 points)
    - Calculate overall score (0-100)
    - Flag highlights above threshold
    - Support batch scoring
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6_
  
  - [ ] 7.2 Write property tests for quality scoring
    - **Property 5: Quality Score Range**
    - **Property 6: High Quality Flagging**
    - **Validates: Requirements 3.1, 3.4, 3.6**
  
  - [ ] 7.3 Write unit tests for quality scorer
    - Test each scoring factor
    - Test overall score calculation
    - Test highlight flagging
    - Test batch processing
    - _Requirements: 3.1, 3.4_

- [ ] 8. Checkpoint - Core analysis components complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Topic classifier implementation
  - [ ] 7.1 Implement TopicClassifier class
    - Load topic taxonomy from configuration
    - Implement keyword-based classification with TF-IDF
    - Support multi-label classification (primary + secondary)
    - Calculate confidence scores
    - Support batch classification
    - _Requirements: 4.1, 4.2, 4.3, 4.5_
  
  - [ ] 7.2 Write property tests for topic classification
    - **Property 7: Topic Assignment Completeness**
    - **Property 8: Primary Topic Uniqueness**
    - **Validates: Requirements 4.1, 4.3, 4.5**
  
  - [ ] 7.3 Write unit tests for topic classifier
    - Test single topic assignment
    - Test multi-topic assignment
    - Test primary/secondary designation
    - Test confidence scoring
    - _Requirements: 4.1, 4.3_

- [ ] 8. Problematic statement detector implementation
  - [ ] 8.1 Implement ProblematicStatementDetector class
    - Load problematic patterns from configuration
    - Implement pattern matching for impunity category
    - Implement pattern matching for ignorance category
    - Implement pattern matching for sycophancy category
    - Return ProblematicFlag with category and matched patterns
    - Support batch detection
    - _Requirements: 7.2, 7.3, 7.4, 7.5, 7.6_
  
  - [ ] 8.2 Write property tests for problematic detection
    - **Property 17: Problematic Pattern Detection**
    - **Validates: Requirements 7.2, 7.3, 7.4, 7.5**
  
  - [ ] 8.3 Write unit tests for problematic detector
    - Test impunity pattern detection
    - Test ignorance pattern detection
    - Test sycophancy pattern detection
    - Test batch processing
    - _Requirements: 7.2, 7.3, 7.4_

- [ ] 9. Processing pipeline integration
  - [ ] 9.1 Create unified processing pipeline
    - Implement ProcessingPipeline class that orchestrates all analyzers
    - Process statements through classification → sentiment → quality → topics → problematic detection
    - Store all results in database
    - Handle errors gracefully with logging
    - Support batch processing with progress tracking
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 7.2_
  
  - [ ] 9.2 Write property tests for pipeline
    - **Property 2: Filler Statement Exclusion from Metrics**
    - **Property 51: Single Statement Failure Isolation**
    - **Validates: Requirements 1.4, 5.1, 21.2**
  
  - [ ] 9.3 Write integration tests for pipeline
    - Test end-to-end processing of sample statements
    - Test error handling and continuation
    - Test database storage
    - Test batch processing
    - _Requirements: 1.1, 2.1, 3.1, 4.1_

- [ ] 10. Votes & Proceedings scraper
  - [ ] 10.1 Implement VotesProceedings Scraper class
    - Download Votes & Proceedings PDFs from parliament.go.ke
    - Parse PDF to extract vote records
    - Extract bill ID, MP votes, and metadata
    - Handle PDF format variations
    - Support date range filtering
    - _Requirements: 10.1, 10.2_
  
  - [ ] 10.2 Write property tests for vote scraping
    - **Property 24: Vote Record Completeness**
    - **Validates: Requirements 10.1, 10.2**
  
  - [ ] 10.3 Write unit tests for vote scraper
    - Test PDF download
    - Test PDF parsing
    - Test vote extraction
    - Test error handling for malformed PDFs
    - _Requirements: 10.1, 10.2_

- [ ] 11. Statements Tracker processor
  - [ ] 11.1 Implement StatementsTrackerProcessor class
    - Download Statements Tracker PDF from parliament.go.ke
    - Parse PDF to extract constituency statements
    - Link statements to MPs and constituencies
    - Handle PDF format changes gracefully
    - _Requirements: 8.1, 8.2, 8.5, 8.6_
  
  - [ ] 11.2 Write property tests for Statements Tracker processing
    - **Property 19: Constituency Statement Linking**
    - **Property 21: PDF Parsing Error Resilience**
    - **Validates: Requirements 8.1, 8.2, 8.6**
  
  - [ ] 11.3 Write unit tests for Statements Tracker processor
    - Test PDF download
    - Test PDF parsing
    - Test statement extraction
    - Test error handling
    - _Requirements: 8.1, 8.5, 8.6**

- [ ] 12. Checkpoint - Data collection components complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Enhanced MP page generation
  - [ ] 13.1 Implement enhanced MP profile page generator
    - Calculate participation metrics excluding filler statements
    - Group statements by policy topic
    - Calculate average quality score
    - Calculate sentiment distribution
    - Filter to last two parliament terms
    - Display constituency representation section
    - Display attendance statistics
    - Display voting patterns by topic
    - Display problematic statements section (conditional)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 7.7, 8.3, 8.4, 9.2, 9.3, 9.4, 9.5, 10.3, 10.4, 10.5_
  
  - [ ] 13.2 Write property tests for MP page generation
    - **Property 9: Statement Grouping by Topic**
    - **Property 10: Average Quality Score Accuracy**
    - **Property 11: Sentiment Distribution Completeness**
    - **Property 12: Term Filtering**
    - **Property 18: Problematic Section Conditional Display**
    - **Property 20: Constituency Statement Count Accuracy**
    - **Property 22: Attendance Percentage Accuracy**
    - **Property 23: Attendance Grouping by Session Type**
    - **Property 25: Vote Topic Grouping**
    - **Property 26: Party Alignment Calculation**
    - **Validates: Requirements 4.4, 5.2, 5.3, 5.4, 5.5, 7.7, 8.4, 9.2, 9.5, 10.3, 10.4, 10.5**
  
  - [ ] 13.3 Write unit tests for MP page generation
    - Test page structure
    - Test metric calculations
    - Test conditional sections
    - Test template rendering
    - _Requirements: 5.2, 5.3, 5.4, 7.7, 8.4_

- [ ] 14. Session day page generation with top quotes
  - [ ] 14.1 Implement session day page generator
    - Select top quotes with quality scores above 80
    - Include statements from both sides of debates
    - Limit to 10 quotes per session
    - Display speaker name, text, context, and related bill
    - Handle sessions with no high-quality statements
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [ ] 14.2 Write property tests for session page generation
    - **Property 13: Top Quotes Balance**
    - **Property 14: Top Quotes Quality Threshold**
    - **Property 15: Top Quotes Field Completeness**
    - **Property 16: Top Quotes Count Limit**
    - **Validates: Requirements 6.2, 6.3, 6.4, 6.5**
  
  - [ ] 14.3 Write unit tests for session page generation
    - Test quote selection
    - Test balance between sides
    - Test quality filtering
    - Test count limiting
    - Test empty session handling
    - _Requirements: 6.2, 6.3, 6.5, 6.6_

- [ ] 15. Enhanced party page generation
  - [ ] 15.1 Implement enhanced party page generator
    - Aggregate member statements by policy topic
    - Calculate weighted party position using quality scores
    - Display sentiment distribution per topic
    - Show most active members per topic
    - Calculate voting alignment percentage
    - Handle insufficient data gracefully
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_
  
  - [ ] 15.2 Write property tests for party page generation
    - **Property 33: Party Statement Aggregation by Topic**
    - **Property 34: Weighted Party Position**
    - **Property 35: Party Sentiment Distribution**
    - **Validates: Requirements 13.1, 13.2, 13.3**
  
  - [ ] 15.3 Write unit tests for party page generation
    - Test statement aggregation
    - Test weighted position calculation
    - Test sentiment distribution
    - Test member ranking
    - Test alignment calculation
    - Test insufficient data handling
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

- [ ] 16. Weekly content generator
  - [ ] 16.1 Implement WeeklyContentGenerator class
    - Filter bills passed during week
    - Filter bills debated during week
    - Select top statements by quality score
    - Calculate attendance statistics for week
    - Generate WeeklySummary with all data
    - Archive summary with permanent URL
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_
  
  - [ ] 16.2 Implement weekly archive page generator
    - Display summaries in reverse chronological order
    - Generate archive index page
    - _Requirements: 11.7_
  
  - [ ] 16.3 Write property tests for weekly content generation
    - **Property 27: Weekly Summary Date Range**
    - **Property 28: Weekly Summary Archival**
    - **Property 29: Archive Chronological Ordering**
    - **Validates: Requirements 11.2, 11.3, 11.4, 11.5, 11.6, 11.7**
  
  - [ ] 16.4 Write unit tests for weekly content generator
    - Test date range filtering
    - Test bill selection
    - Test statement selection
    - Test attendance calculation
    - Test archival
    - Test ordering
    - _Requirements: 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

- [ ] 17. Historical content generator
  - [ ] 17.1 Implement HistoricalContentGenerator class
    - Match current date across all years in database
    - Extract year, topic, and key statements
    - Generate links to full session records
    - Prioritize high-quality statements
    - Handle dates with no historical records
    - Generate historical date pages for all dates with activity
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_
  
  - [ ] 17.2 Write property tests for historical content generation
    - **Property 30: Historical Date Matching**
    - **Property 31: Historical Discussion Field Completeness**
    - **Property 32: Historical Page Generation Completeness**
    - **Validates: Requirements 12.1, 12.2, 12.5**
  
  - [ ] 17.3 Write unit tests for historical content generator
    - Test date matching
    - Test field extraction
    - Test link generation
    - Test quality prioritization
    - Test empty date handling
    - Test page generation
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [ ] 18. Checkpoint - Page generation complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 19. Error handling and logging infrastructure
  - [ ] 19.1 Implement structured logging system
    - Create StructuredLogger class with JSON output
    - Include timestamp, level, component, message, and context
    - Support different log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Create separate log files for different processing stages
    - _Requirements: 17.3, 21.1, 21.4, 21.5_
  
  - [ ] 19.2 Implement retry logic with exponential backoff
    - Create retry_with_backoff decorator
    - Support configurable max retries and base delay
    - Log retry attempts
    - _Requirements: 21.3_
  
  - [ ] 19.3 Implement error notification system
    - Support email and Slack notifications
    - Configure notification triggers (critical errors, data loss)
    - Include actionable error details in notifications
    - _Requirements: 15.4, 21.6_
  
  - [ ] 19.4 Write property tests for error handling
    - **Property 50: Error Logging with Context**
    - **Property 52: Exponential Backoff Retry**
    - **Property 53: Conditional Critical Error Notification**
    - **Validates: Requirements 21.1, 21.3, 21.4, 21.6**
  
  - [ ] 19.5 Write unit tests for error handling
    - Test structured logging format
    - Test retry logic
    - Test notification triggers
    - Test error isolation
    - _Requirements: 17.3, 21.1, 21.3, 21.4, 21.6_

- [ ] 20. Monitoring and metrics
  - [ ] 20.1 Implement metrics collection
    - Create MetricsCollector class
    - Collect processing time metrics
    - Collect error rate metrics
    - Collect data volume metrics
    - Expose metrics for CloudWatch
    - _Requirements: 17.4_
  
  - [ ] 20.2 Implement health check system
    - Check database connection
    - Check S3 access
    - Check last processing time
    - Return health status with details
    - _Requirements: 16.7_
  
  - [ ] 20.3 Write property tests for monitoring
    - **Property 46: Metrics Exposure**
    - **Validates: Requirements 17.4**
  
  - [ ] 20.4 Write unit tests for monitoring
    - Test metrics collection
    - Test metrics exposure
    - Test health checks
    - _Requirements: 17.4, 16.7_

- [ ] 21. Automation and scheduling
  - [ ] 21.1 Implement automated processing orchestrator
    - Create main processing script that runs full pipeline
    - Download new documents from parliament.go.ke
    - Process statements through analysis pipeline
    - Generate static pages
    - Deploy to hosting
    - Log all steps with structured logging
    - _Requirements: 15.1, 15.2, 15.3, 15.6_
  
  - [ ] 21.2 Create command-line tools for manual processing
    - CLI for processing specific date ranges
    - CLI for reprocessing statements
    - CLI for regenerating pages
    - CLI for running migrations
    - _Requirements: 15.5_
  
  - [ ] 21.3 Write property tests for automation
    - **Property 38: Automated Processing End-to-End**
    - **Property 39: Error Notification with Context**
    - **Property 40: Processing Log Completeness**
    - **Property 41: Optional Human Review Independence**
    - **Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.6, 15.7**
  
  - [ ] 21.4 Write integration tests for automation
    - Test full pipeline execution
    - Test error handling
    - Test logging
    - Test CLI tools
    - _Requirements: 15.1, 15.2, 15.3, 15.5_

- [ ] 22. Infrastructure as Code (Terraform)
  - [ ] 22.1 Create Terraform modules
    - Create static-site module (S3 + CloudFront)
    - Create processing module (Lambda)
    - Create monitoring module (CloudWatch)
    - Create main.tf with module composition
    - _Requirements: 16.1_
  
  - [ ] 22.2 Create environment configurations
    - Create dev environment configuration
    - Create staging environment configuration
    - Create production environment configuration
    - _Requirements: 16.4, 16.5_
  
  - [ ] 22.3 Write unit tests for Terraform
    - Test module configurations
    - Test environment configurations
    - Validate Terraform syntax
    - _Requirements: 16.1, 16.4_

- [ ] 23. CI/CD pipeline (GitHub Actions)
  - [ ] 23.1 Create test workflow
    - Run pytest with coverage
    - Enforce 90% coverage threshold
    - Run on pull requests and pushes to main
    - _Requirements: 16.2, 23.1_
  
  - [ ] 23.2 Create Terraform plan workflow
    - Run terraform plan on pull requests
    - Comment plan output on PR
    - _Requirements: 16.2_
  
  - [ ] 23.3 Create deployment workflow
    - Run terraform apply on main branch
    - Deploy Lambda function
    - Run health checks
    - Rollback on failure
    - _Requirements: 16.3, 16.6, 16.7_
  
  - [ ] 23.4 Write property tests for CI/CD
    - **Property 42: CI/CD Test-Gated Deployment**
    - **Property 43: Infrastructure Change Automation**
    - **Property 44: Automatic Rollback on Health Check Failure**
    - **Validates: Requirements 16.3, 16.6, 16.7**
  
  - [ ] 23.5 Write integration tests for CI/CD
    - Test workflow execution
    - Test deployment process
    - Test rollback process
    - _Requirements: 16.3, 16.6, 16.7_

- [ ] 24. Checkpoint - Infrastructure and automation complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 25. Data source integration architecture
  - [ ] 25.1 Create modular data source architecture
    - Define DataSource interface
    - Implement HansardDataSource
    - Implement VotesDataSource
    - Implement StatementsTrackerDataSource
    - Support error isolation between sources
    - Log data source status and errors
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_
  
  - [ ] 25.2 Write property tests for data source architecture
    - **Property 36: Data Source Error Isolation**
    - **Property 37: Data Source Logging**
    - **Validates: Requirements 14.5, 14.6**
  
  - [ ] 25.3 Write unit tests for data source architecture
    - Test interface implementation
    - Test error isolation
    - Test logging
    - Test National Assembly and Senate support
    - _Requirements: 14.1, 14.4, 14.5, 14.6_

- [ ] 26. Performance optimization
  - [ ] 26.1 Implement batch database operations
    - Use executemany for bulk inserts
    - Use transactions for related operations
    - Add database indexes for common queries
    - _Requirements: 22.1, 22.3_
  
  - [ ] 26.2 Implement parallel page generation
    - Use ThreadPoolExecutor for page generation
    - Generate pages in parallel where possible
    - _Requirements: 22.2_
  
  - [ ] 26.3 Implement adaptive streaming processing
    - Monitor memory usage during processing
    - Switch to streaming mode if memory exceeds threshold
    - _Requirements: 22.6_
  
  - [ ] 26.4 Write property tests for performance
    - **Property 54: Adaptive Streaming Processing**
    - **Validates: Requirements 22.6**
  
  - [ ] 26.5 Write unit tests for performance optimizations
    - Test batch operations
    - Test parallel processing
    - Test streaming mode
    - _Requirements: 22.1, 22.2, 22.6_

- [ ] 27. Frontend/Backend architecture decision and API layer
  - [ ] 27.1 Evaluate frontend architecture options
    - Document static site generation (current approach) pros/cons
    - Document server-side rendering (React/Next.js) pros/cons
    - Consider user experience and navigation improvements
    - Consider API layer for third-party access (journalists/researchers)
    - Analyze learning opportunities (frontend, NLP, LLM, ML techniques)
    - Provide recommendation with trade-offs
    - **Note**: This is a critical architectural decision that affects UX, maintainability, and extensibility
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_
  
  - [ ] 27.2 Design API layer for backend services
    - Define REST API endpoints for parliamentary data
    - Design authentication/authorization for API access
    - Document API schema (OpenAPI/Swagger)
    - Consider rate limiting for public API
    - Design API versioning strategy
    - **Note**: API enables third-party integrations and separates concerns
    - _Requirements: 14.1, 14.2_
  
  - [ ] 27.3 Implement API layer (if recommended)
    - Create FastAPI or Flask application
    - Implement core API endpoints (MPs, statements, bills, votes)
    - Implement authentication middleware
    - Add API documentation (Swagger UI)
    - Add rate limiting
    - _Requirements: 14.1, 14.2_
  
  - [ ] 27.4 Write unit tests for API layer
    - Test endpoint responses
    - Test authentication
    - Test rate limiting
    - Test error handling
    - _Requirements: 23.2, 23.3_
  
  - [ ] 27.5 Update infrastructure for API deployment
    - Add API Gateway or ALB to Terraform
    - Configure Lambda or ECS for API hosting
    - Set up API monitoring
    - _Requirements: 16.1, 16.4_

- [ ] 28. Future work documentation
  - [ ] 28.1 Create Senate integration documentation
    - Write user stories for Senate integration
    - Document architecture considerations
    - Provide cost analysis
    - Estimate implementation effort
    - Document scalability considerations
    - _Requirements: 24.1, 24.3, 24.4, 24.5, 24.6_
  
  - [ ] 28.2 Create additional data sources documentation
    - Document each additional data source (Bills Tracker, Petitions, Questions, etc.)
    - Provide user stories for each
    - Analyze data structures and parsing complexity
    - Estimate storage and processing requirements
    - Document integration approach
    - Provide cost impact analysis
    - _Requirements: 24.2, 24.3, 24.5, 24.6_
  
  - [ ] 28.3 Create Architecture Decision Records (ADRs)
    - Write ADR-001: SQLite vs PostgreSQL for production
    - Write ADR-002: Lambda vs EC2 for processing
    - Write ADR-003: spaCy vs NLTK for NLP
    - Write ADR-004: S3 + CloudFront vs Netlify for hosting
    - Write ADR-005: Monorepo vs separate repos for Senate integration
    - Write ADR-006: Static site generation vs server-side rendering (React/Next.js)
    - Write ADR-007: API layer design and authentication strategy
    - _Requirements: 24.4_
  
  - [ ] 28.4 Create prioritized roadmap
    - Prioritize future enhancements
    - Estimate effort for each enhancement
    - Document dependencies between enhancements
    - _Requirements: 24.7_

- [ ] 29. Final checkpoint - Complete system integration
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 30. End-to-end integration testing
  - [ ] 30.1 Write end-to-end integration tests
    - Test complete pipeline from PDF download to page generation
    - Test error handling across components
    - Test data consistency across database tables
    - Test generated pages contain expected content
    - _Requirements: 23.3_

- [ ] 31. Documentation and deployment guide
  - [ ] 31.1 Create deployment documentation
    - Document AWS account setup
    - Document GitHub Actions secrets configuration
    - Document Terraform deployment process
    - Document monitoring setup
    - _Requirements: 16.1, 16.2_
  
  - [ ] 31.2 Create operational runbook
    - Document common operational tasks
    - Document troubleshooting procedures
    - Document rollback procedures
    - Document monitoring and alerting
    - _Requirements: 15.5, 16.7_

## Notes

- All tasks including tests are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases (≥90% coverage required)
- Integration tests validate component interactions
- The implementation follows an incremental approach: ORM setup → core analysis → page generation → automation → infrastructure → API layer
- SQLAlchemy/Alembic used for database ORM and migrations to future-proof schema changes
- Frontend/backend separation and API layer evaluation is a critical architectural decision
- Consider learning opportunities in frontend, NLP, LLM, and ML techniques throughout implementation
