# Phase 1: Core Analysis Pipeline - Requirements

## Introduction

This document specifies requirements for Phase 1 of the Hansard Tales system: implementing the core analysis pipeline for Hansard and Votes & Proceedings documents from the National Assembly. This phase builds on Phase 0's foundation to add AI-powered analysis with anti-hallucination measures.

**Scope**: Statement classification, sentiment analysis, quality scoring, topic classification, citation verification, basic MP profiles

**Duration**: 4 weeks

**Dependencies**: Phase 0 (Foundation) complete

**Document Types**: Hansard, Votes & Proceedings (National Assembly only)

## Glossary

- **Statement**: A single utterance by an MP in Hansard
- **Filler Statement**: Low-value statement (e.g., "I support", "Thank you Mr. Speaker")
- **Substantive Statement**: High-value statement with policy content
- **RAG**: Retrieval-Augmented Generation (context retrieval for LLM)
- **Citation**: Reference to source document with page/line numbers
- **Quality Score**: 0-100 score indicating statement value
- **Sentiment**: Support, oppose, or neutral stance on a topic

## Requirements

### Requirement 1: MP Identification and Extraction

**User Story:** As a system, I want to identify MPs in Hansard text, so that I can attribute statements correctly.

#### Acceptance Criteria

1. THE System SHALL extract MP names from Hansard text
2. THE System SHALL match extracted names to MP database records
3. THE System SHALL handle name variations (e.g., "Hon. John Doe" vs "John Doe")
4. THE System SHALL handle titles (Hon., Dr., Prof., etc.)
5. WHEN an MP name is ambiguous, THE System SHALL use context (constituency, party) to disambiguate
6. THE System SHALL achieve ≥95% accuracy on MP identification
7. THE System SHALL log unmatched MP names for manual review

### Requirement 2: Statement Segmentation

**User Story:** As a system, I want to segment Hansard text into individual statements, so that I can analyze each statement separately.

#### Acceptance Criteria

1. THE System SHALL split Hansard text into individual statements by MP
2. EACH statement SHALL include: mp_id, text, timestamp (if available), page_number, line_number
3. THE System SHALL preserve statement boundaries accurately
4. THE System SHALL handle multi-paragraph statements
5. THE System SHALL handle interruptions and interjections
6. THE System SHALL achieve ≥98% accuracy on statement segmentation

### Requirement 3: Statement Classification (Filler Detection)

**User Story:** As an analyst, I want to identify filler statements, so that I can focus on substantive content.

#### Acceptance Criteria

1. THE System SHALL classify each statement as "filler" or "substantive"
2. THE System SHALL use rule-based heuristics for classification
3. Filler indicators SHALL include: length < 20 words, common phrases ("I support", "Thank you"), procedural statements
4. THE System SHALL achieve ≥90% precision on filler detection
5. THE System SHALL achieve ≥85% recall on filler detection
6. THE System SHALL store classification result with each statement

### Requirement 4: Context Retrieval (RAG)

**User Story:** As a system, I want to retrieve relevant context for statement analysis, so that the LLM has necessary background information.

#### Acceptance Criteria

1. THE System SHALL retrieve relevant context from vector DB for each statement
2. Context SHALL include: related bills, previous statements by same MP, related questions, session context
3. THE System SHALL limit context to fit within LLM context window (200K tokens for Claude)
4. THE System SHALL rank context by relevance score
5. THE System SHALL retrieve top 10 most relevant documents
6. THE System SHALL include source references for all retrieved context

### Requirement 5: Sentiment Analysis

**User Story:** As an analyst, I want to know MP sentiment on topics, so that I can track positions over time.

#### Acceptance Criteria

1. THE System SHALL analyze sentiment for each substantive statement
2. Sentiment SHALL be one of: "support", "oppose", "neutral"
3. THE System SHALL use Claude 3.5 Haiku for sentiment analysis
4. THE System SHALL provide confidence score (0-100) for sentiment
5. THE System SHALL identify the topic being discussed
6. WHEN confidence < 70%, THE System SHALL mark sentiment as "uncertain"
7. THE System SHALL generate citations for sentiment determination

### Requirement 6: Citation Generation and Verification

**User Story:** As a system architect, I want verifiable citations for all analysis, so that I can prevent hallucination.

#### Acceptance Criteria

1. THE System SHALL generate citations for all LLM-based analysis
2. EACH citation SHALL include: source_url, source_hash, page_number, line_number, quote
3. THE System SHALL verify that quoted text exists in source document
4. WHEN verification fails, THE System SHALL reject the analysis result
5. THE System SHALL log all citation verification failures
6. THE System SHALL achieve 100% citation verification rate (no unverified claims)

### Requirement 7: Quality Scoring

**User Story:** As an analyst, I want quality scores for statements, so that I can prioritize high-value content.

#### Acceptance Criteria

1. THE System SHALL compute quality score (0-100) for each substantive statement
2. Quality factors SHALL include: length, specificity, evidence, policy content, originality
3. THE System SHALL use both rule-based and LLM-based scoring
4. THE System SHALL normalize scores to 0-100 range
5. THE System SHALL store quality score with each statement
6. THE System SHALL provide score breakdown (which factors contributed)

### Requirement 8: Topic Classification

**User Story:** As an analyst, I want statements categorized by topic, so that I can track discussions by subject area.

#### Acceptance Criteria

1. THE System SHALL classify each statement into one or more topics
2. Topics SHALL include: Healthcare, Education, Finance, Infrastructure, Agriculture, Security, Governance, etc.
3. THE System SHALL support multi-label classification (statement can have multiple topics)
4. THE System SHALL use keyword matching and LLM-based classification
5. THE System SHALL achieve ≥85% accuracy on topic classification
6. THE System SHALL allow custom topic definitions

### Requirement 9: Vote Processing

**User Story:** As a system, I want to process Votes & Proceedings documents, so that I can track how MPs voted.

#### Acceptance Criteria

1. THE System SHALL extract vote records from Votes & Proceedings PDFs
2. EACH vote record SHALL include: bill_id, vote_date, vote_type, result
3. THE System SHALL extract individual MP votes (aye, no, abstain, absent)
4. THE System SHALL match votes to bills in database
5. THE System SHALL handle different vote formats (division, voice, etc.)
6. THE System SHALL achieve ≥98% accuracy on vote extraction

### Requirement 10: Bill-Statement Correlation

**User Story:** As an analyst, I want to link statements to bills, so that I can see all discussion about a bill.

#### Acceptance Criteria

1. THE System SHALL identify bill references in statements
2. THE System SHALL link statements to bill records in database
3. THE System SHALL use both explicit references (bill numbers) and semantic similarity
4. THE System SHALL store bill-statement relationships
5. THE System SHALL compute relevance score for each relationship
6. THE System SHALL achieve ≥80% precision on bill-statement linking

### Requirement 11: MP Profile Generation

**User Story:** As a citizen, I want to see MP profiles with their activity, so that I can hold them accountable.

#### Acceptance Criteria

1. THE System SHALL generate profile page for each MP
2. Profile SHALL include: name, party, constituency, photo, contact info
3. Profile SHALL include: total statements, substantive statements, quality score average
4. Profile SHALL include: topics discussed (with counts)
5. Profile SHALL include: voting record (total votes, party alignment %)
6. Profile SHALL include: recent activity (last 10 statements)
7. Profile SHALL be generated as static HTML

### Requirement 12: Session Summary Generation

**User Story:** As a citizen, I want session summaries, so that I can quickly understand what happened.

#### Acceptance Criteria

1. THE System SHALL generate summary for each Hansard session
2. Summary SHALL include: date, bills discussed, key topics, notable statements
3. Summary SHALL include: vote results (if any)
4. Summary SHALL include: attendance statistics
5. Summary SHALL be generated as static HTML
6. Summary SHALL link to full Hansard document

### Requirement 13: Analysis Pipeline Orchestration

**User Story:** As a system operator, I want automated analysis pipeline, so that new documents are processed automatically.

#### Acceptance Criteria

1. THE System SHALL process documents in order: scrape → parse → segment → classify → analyze → store
2. THE System SHALL support batch processing of multiple documents
3. THE System SHALL support incremental processing (only new documents)
4. THE System SHALL track processing status for each document
5. THE System SHALL retry failed processing steps (max 3 retries)
6. THE System SHALL log all processing steps with timing information
7. THE System SHALL support parallel processing (configurable workers)

### Requirement 14: Static Site Generation

**User Story:** As a citizen, I want a website to browse parliamentary data, so that I can access information easily.

#### Acceptance Criteria

1. THE System SHALL generate static HTML site from processed data
2. Site SHALL include: homepage, MP list, MP profiles, session list, session pages
3. Site SHALL include: search functionality (client-side)
4. Site SHALL include: navigation menu, breadcrumbs, footer
5. Site SHALL be responsive (mobile-friendly)
6. Site SHALL use semantic HTML and accessibility best practices
7. Site SHALL be deployable to Cloudflare Pages

### Requirement 15: Performance and Scalability

**User Story:** As a system operator, I want efficient processing, so that I can handle large volumes of data.

#### Acceptance Criteria

1. THE System SHALL process one Hansard document (100 pages) in < 10 minutes
2. THE System SHALL process one Votes document (10 pages) in < 2 minutes
3. THE System SHALL support processing 100+ documents in batch
4. THE System SHALL use < 4GB RAM during processing
5. THE System SHALL cache embeddings to avoid recomputation
6. THE System SHALL use connection pooling for database access

### Requirement 16: Cost Management

**User Story:** As a system operator, I want to minimize costs, so that the system is sustainable.

#### Acceptance Criteria

1. THE System SHALL track LLM API usage (tokens, cost)
2. THE System SHALL implement rate limiting for LLM calls
3. THE System SHALL cache LLM responses to avoid duplicate calls
4. THE System SHALL estimate cost before processing batch
5. THE System SHALL alert when monthly cost exceeds threshold
6. THE System SHALL target < $20/month for LLM costs

### Requirement 17: Data Quality Assurance

**User Story:** As a system architect, I want data quality checks, so that I can ensure accuracy.

#### Acceptance Criteria

1. THE System SHALL validate all extracted data before storage
2. THE System SHALL check for duplicate statements (by hash)
3. THE System SHALL verify MP IDs exist in database
4. THE System SHALL verify bill IDs exist in database
5. THE System SHALL check for missing required fields
6. THE System SHALL log all validation failures
7. THE System SHALL generate data quality report after each batch

### Requirement 18: Monitoring and Observability

**User Story:** As a system operator, I want detailed monitoring, so that I can track system health.

#### Acceptance Criteria

1. THE System SHALL track metrics: statements_processed, analysis_time, llm_calls, llm_cost
2. THE System SHALL track error rates by component
3. THE System SHALL track data quality metrics (accuracy, completeness)
4. THE System SHALL expose metrics in Prometheus format
5. THE System SHALL provide Grafana dashboard for Phase 1 metrics
6. THE System SHALL alert on critical errors

### Requirement 19: Testing and Validation

**User Story:** As a developer, I want comprehensive tests, so that I can ensure correctness.

#### Acceptance Criteria

1. THE System SHALL maintain ≥90% code coverage for Phase 1 code
2. THE System SHALL include unit tests for all components
3. THE System SHALL include integration tests for full pipeline
4. THE System SHALL include property-based tests for key invariants
5. THE System SHALL include end-to-end tests with sample data
6. THE System SHALL validate against manually annotated test set (≥100 statements)

### Requirement 20: Documentation

**User Story:** As a developer, I want clear documentation, so that I can understand and maintain the system.

#### Acceptance Criteria

1. THE System SHALL document all analysis algorithms
2. THE System SHALL document LLM prompts and expected outputs
3. THE System SHALL document data quality thresholds
4. THE System SHALL document API endpoints (if any)
5. THE System SHALL include examples of analysis outputs
6. THE System SHALL update ARCHITECTURE.md with Phase 1 components


