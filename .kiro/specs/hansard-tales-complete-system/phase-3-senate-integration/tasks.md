# Phase 3: Senate Integration - Implementation Tasks

## Overview

This document breaks down Phase 3 implementation into actionable tasks. Phase 3 extends all Phase 1 and Phase 2 functionality to the Senate chamber, enabling comprehensive bicameral parliamentary tracking.

**Timeline**: 4 weeks | **Test Coverage Target**: ≥90% | **Budget**: ≤$50/month

## Task Status Legend
- `[ ]` Not started | `[~]` Queued | `[-]` In progress | `[x]` Completed | `[ ]*` Optional

---

## Week 1: Database Schema and Component Refactoring

### Task 1: Database Schema Extensions

**Acceptance Criteria**:
- Senators, cross_chamber_bills, joint_committees tables created
- All foreign keys and indexes configured
- Migration tested (upgrade and downgrade)
- Chamber isolation verified

**Files**:
- `hansard_tales/database/migrations/003_add_senate_support.py`
- `hansard_tales/database/models.py`
- `tests/test_senate_schema.py`

- [ ] 1.1 Create Alembic migration
  - [ ] 1.1.1 Add senators table with all fields
  - [ ] 1.1.2 Add cross_chamber_bills table
  - [ ] 1.1.3 Add joint_committees table
  - [ ] 1.1.4 Add indexes for performance
  - [ ] 1.1.5 Add foreign key constraints

- [ ] 1.2 Update ORM models
  - [ ] 1.2.1 Create SenatorORM model
  - [ ] 1.2.2 Create CrossChamberBillORM model
  - [ ] 1.2.3 Create JointCommitteeORM model
  - [ ] 1.2.4 Add SenatorCategory enum
  - [ ] 1.2.5 Update relationships

- [ ] 1.3 Write migration tests
  - [ ] 1.3.1 Test schema creation
  - [ ] 1.3.2 Test foreign key constraints
  - [ ] 1.3.3 Test rollback functionality
  - [ ] 1.3.4 Test data migration (if needed)

- [ ] 1.4 Write property-based tests
  - [ ] 1.4.1 **Property 1.1**: Chamber isolation
    - **Validates**: Requirements 1.3.6
    - **Strategy**: Query all documents, verify chamber field matches
  - [ ] 1.4.2 **Property 1.2**: Senator uniqueness
    - **Validates**: Requirements 1.2.6
    - **Strategy**: Check for duplicate Senator records in same term


---

### Task 2: Chamber-Agnostic Component Refactoring

**Acceptance Criteria**:
- All Phase 1 and Phase 2 components accept chamber parameter
- No cross-chamber data contamination
- Chamber parameter propagates correctly
- All existing tests pass with chamber parameter

**Files**:
- `hansard_tales/analysis/parliamentarian_identifier.py` (renamed from mp_identifier.py)
- `hansard_tales/analysis/context_retriever.py`
- `hansard_tales/processors/vote_processor.py`
- `hansard_tales/scrapers/bill_scraper.py`
- `hansard_tales/correlation/correlation_engine.py`
- `tests/test_chamber_agnostic_components.py`

- [ ] 2.1 Refactor Phase 1 components
  - [ ] 2.1.1 Rename MPIdentifier → ParliamentarianIdentifier
  - [ ] 2.1.2 Add chamber parameter to __init__
  - [ ] 2.1.3 Update _load_cache to query MPs or Senators based on chamber
  - [ ] 2.1.4 Update ContextRetriever to filter by chamber
  - [ ] 2.1.5 Update VoteProcessor to accept chamber parameter

- [ ] 2.2 Refactor Phase 2 components
  - [ ] 2.2.1 Update BillScraper to accept chamber parameter
  - [ ] 2.2.2 Update QuestionScraper to accept chamber parameter
  - [ ] 2.2.3 Update PetitionScraper to accept chamber parameter
  - [ ] 2.2.4 Update CorrelationEngine to filter by chamber

- [ ] 2.3 Create factory pattern
  - [ ] 2.3.1 Create ChamberAwareProcessor base class
  - [ ] 2.3.2 Create ScraperFactory for chamber-specific scrapers
  - [ ] 2.3.3 Create ProcessorFactory for chamber-specific processors

- [ ] 2.4 Write unit tests
  - [ ] 2.4.1 Test ParliamentarianIdentifier with both chambers
  - [ ] 2.4.2 Test chamber parameter propagation
  - [ ] 2.4.3 Test factory pattern

- [ ] 2.5 Write property-based tests
  - [ ] 2.5.1 **Property 2.1**: Chamber parameter propagation
    - **Validates**: Requirements 1.3.5
    - **Strategy**: Trace chamber parameter through call stack
  - [ ] 2.5.2 **Property 2.2**: No cross-chamber contamination
    - **Validates**: Requirements 1.3.6
    - **Strategy**: Process NA document, verify no Senate queries

---

### Task 3: Senate Document Scrapers

**Acceptance Criteria**:
- All Senate document types discoverable
- Senate URLs correctly formed
- All documents tagged with Senate chamber
- Duplicate prevention works

**Files**:
- `hansard_tales/scrapers/senate_scraper.py`
- `hansard_tales/scrapers/senate_hansard_scraper.py`
- `hansard_tales/scrapers/senate_votes_scraper.py`
- `hansard_tales/scrapers/senate_bills_scraper.py`
- `hansard_tales/scrapers/senate_questions_scraper.py`
- `hansard_tales/scrapers/senate_petitions_scraper.py`
- `tests/test_senate_scrapers.py`

- [ ] 3.1 Implement base Senate scraper
  - [ ] 3.1.1 Create SenateScraper extending BaseScraper
  - [ ] 3.1.2 Implement get_chamber_specific_url method
  - [ ] 3.1.3 Set chamber = Chamber.SENATE

- [ ] 3.2 Implement Senate Hansard scraper
  - [ ] 3.2.1 Create SenateHansardScraper
  - [ ] 3.2.2 Implement discover_hansard method
  - [ ] 3.2.3 Reuse NA scraper logic with Senate URL
  - [ ] 3.2.4 Tag all documents with Senate chamber

- [ ] 3.3 Implement Senate Votes scraper
  - [ ] 3.3.1 Create SenateVotesScraper
  - [ ] 3.3.2 Implement discover_votes method
  - [ ] 3.3.3 Reuse NA scraper logic with Senate URL

- [ ] 3.4 Implement Senate Bills scraper
  - [ ] 3.4.1 Create SenateBillsScraper
  - [ ] 3.4.2 Implement discover_bills method
  - [ ] 3.4.3 Implement _determine_bill_chamber method
  - [ ] 3.4.4 Handle Senate-originated and NA bills under review

- [ ] 3.5 Implement Senate Questions scraper
  - [ ] 3.5.1 Create SenateQuestionsScraper
  - [ ] 3.5.2 Implement discover_questions method
  - [ ] 3.5.3 Reuse NA scraper logic with Senate URL

- [ ] 3.6 Implement Senate Petitions scraper
  - [ ] 3.6.1 Create SenatePetitionsScraper
  - [ ] 3.6.2 Implement discover_petitions method
  - [ ] 3.6.3 Reuse NA scraper logic with Senate URL

- [ ] 3.7 Write unit tests
  - [ ] 3.7.1 Test URL generation for all document types
  - [ ] 3.7.2 Test document discovery (mocked)
  - [ ] 3.7.3 Test chamber tagging
  - [ ] 3.7.4 Test duplicate prevention

- [ ] 3.8 Write property-based tests
  - [ ] 3.8.1 **Property 3.1**: Senate URL correctness
    - **Validates**: Requirements 2.1.4
    - **Strategy**: Verify all URLs contain "/the-senate/"
  - [ ] 3.8.2 **Property 3.2**: Chamber tagging
    - **Validates**: Requirements 1.3.1
    - **Strategy**: Verify chamber field for all scraped documents


---

## Week 2: Bicameral Tracking and Senator Profiles

### Task 4: Bicameral Bill Tracking Engine

**Acceptance Criteria**:
- Tracks bill transmissions between chambers
- Generates complete bill timelines
- Compares versions across chambers
- Identifies all bicameral bills

**Files**:
- `hansard_tales/tracking/bicameral_bill_tracker.py`
- `tests/test_bicameral_tracking.py`

- [ ] 4.1 Implement BicameralBillTracker class
  - [ ] 4.1.1 Create BillTransmission dataclass
  - [ ] 4.1.2 Create BillTransmissionStatus enum
  - [ ] 4.1.3 Implement track_transmission method
  - [ ] 4.1.4 Implement update_status method
  - [ ] 4.1.5 Implement get_bill_timeline method
  - [ ] 4.1.6 Implement identify_bicameral_bills method
  - [ ] 4.1.7 Implement compare_versions_across_chambers method

- [ ] 4.2 Implement timeline generation
  - [ ] 4.2.1 Implement _get_chamber_events method
  - [ ] 4.2.2 Aggregate events from both chambers
  - [ ] 4.2.3 Sort events chronologically
  - [ ] 4.2.4 Format timeline for display

- [ ] 4.3 Write unit tests
  - [ ] 4.3.1 Test transmission tracking
  - [ ] 4.3.2 Test status updates
  - [ ] 4.3.3 Test timeline generation
  - [ ] 4.3.4 Test version comparison
  - [ ] 4.3.5 Test bicameral bill identification

- [ ] 4.4 Write property-based tests
  - [ ] 4.4.1 **Property 4.1**: Transmission tracking completeness
    - **Validates**: Requirements 4.1.4
    - **Strategy**: Query bills passed in both chambers, verify transmission records
  - [ ] 4.4.2 **Property 4.2**: Timeline chronological order
    - **Validates**: Requirements 4.2.6
    - **Strategy**: Generate timelines, verify dates are ascending

---

### Task 5: Senator Profile Generation

**Acceptance Criteria**:
- All Senator profile fields populated
- County representation metrics accurate
- Devolution oversight tracking works
- Joint committee memberships tracked

**Files**:
- `hansard_tales/profiles/senator_profile_generator.py`
- `hansard_tales/profiles/county_representation_tracker.py`
- `tests/test_senator_profiles.py`

- [ ] 5.1 Implement SenatorProfile dataclass
  - [ ] 5.1.1 Add all basic info fields
  - [ ] 5.1.2 Add activity metrics fields
  - [ ] 5.1.3 Add county representation fields
  - [ ] 5.1.4 Add committee membership fields

- [ ] 5.2 Implement SenatorProfileGenerator class
  - [ ] 5.2.1 Implement generate_profile method
  - [ ] 5.2.2 Implement _get_statements method
  - [ ] 5.2.3 Implement _get_votes method
  - [ ] 5.2.4 Implement _get_bills method
  - [ ] 5.2.5 Implement _get_questions method
  - [ ] 5.2.6 Implement _get_petitions method
  - [ ] 5.2.7 Implement _count_county_specific method
  - [ ] 5.2.8 Implement _count_devolution_oversight method
  - [ ] 5.2.9 Implement _get_joint_committees method

- [ ] 5.3 Implement CountyRepresentationTracker class
  - [ ] 5.3.1 Implement generate_county_report method
  - [ ] 5.3.2 Implement _get_county_statements method
  - [ ] 5.3.3 Implement _get_county_questions method
  - [ ] 5.3.4 Implement _get_county_petitions method
  - [ ] 5.3.5 Implement _identify_top_issues method

- [ ] 5.4 Write unit tests
  - [ ] 5.4.1 Test profile generation
  - [ ] 5.4.2 Test county metrics calculation
  - [ ] 5.4.3 Test devolution oversight counting
  - [ ] 5.4.4 Test joint committee tracking
  - [ ] 5.4.5 Test county report generation

- [ ] 5.5 Write property-based tests
  - [ ] 5.5.1 **Property 5.1**: Profile completeness
    - **Validates**: Requirements 6.1.7
    - **Strategy**: Generate profiles for all Senators, verify all fields
  - [ ] 5.5.2 **Property 5.2**: County attribution accuracy
    - **Validates**: Requirements 6.2.5
    - **Strategy**: Manual review of 20 Senator profiles

---

### Task 6: Cross-Chamber Analysis Engine

**Acceptance Criteria**:
- Chamber comparison metrics accurate
- Party position analysis works across chambers
- Legislative efficiency metrics calculated
- Cross-chamber alignment calculated

**Files**:
- `hansard_tales/analysis/cross_chamber_analyzer.py`
- `tests/test_cross_chamber_analysis.py`

- [ ] 6.1 Implement ChamberComparison dataclass
  - [ ] 6.1.1 Add metric_name field
  - [ ] 6.1.2 Add chamber value fields
  - [ ] 6.1.3 Add difference fields

- [ ] 6.2 Implement CrossChamberAnalyzer class
  - [ ] 6.2.1 Implement generate_chamber_comparison method
  - [ ] 6.2.2 Implement _compare_activity_levels method
  - [ ] 6.2.3 Implement _compare_statement_quality method
  - [ ] 6.2.4 Implement _compare_bill_passage_rates method
  - [ ] 6.2.5 Implement _compare_voting_patterns method
  - [ ] 6.2.6 Implement _compare_topic_distribution method

- [ ] 6.3 Implement party analysis
  - [ ] 6.3.1 Implement analyze_party_positions_across_chambers method
  - [ ] 6.3.2 Implement _get_party_votes method
  - [ ] 6.3.3 Implement _calculate_cross_chamber_alignment method
  - [ ] 6.3.4 Implement _identify_divergent_bills method

- [ ] 6.4 Implement efficiency metrics
  - [ ] 6.4.1 Implement calculate_legislative_efficiency method
  - [ ] 6.4.2 Calculate average passage time
  - [ ] 6.4.3 Calculate amendment rate
  - [ ] 6.4.4 Calculate rejection rate

- [ ] 6.5 Write unit tests
  - [ ] 6.5.1 Test chamber comparison generation
  - [ ] 6.5.2 Test party position analysis
  - [ ] 6.5.3 Test alignment calculation
  - [ ] 6.5.4 Test efficiency metrics

- [ ] 6.6 Write property-based tests
  - [ ] 6.6.1 **Property 6.1**: Comparison accuracy
    - **Validates**: Requirements 7.1.5
    - **Strategy**: Manual calculation, compare with automated results
  - [ ] 6.6.2 **Property 6.2**: Party alignment calculation
    - **Validates**: Requirements 7.2.4
    - **Strategy**: Verify alignment percentages in 0-100 range


---

## Week 3: Site Generation and Performance Optimization

### Task 7: Enhanced Static Site Generation

**Acceptance Criteria**:
- All Senator pages generated
- Bicameral bill pages generated
- County representation pages generated
- Joint committee pages generated
- All internal links valid

**Files**:
- `hansard_tales/site/enhanced_site_generator.py`
- `templates/pages/senators_list.html`
- `templates/pages/senator_profile.html`
- `templates/pages/bicameral_bill.html`
- `templates/pages/county.html`
- `templates/pages/joint_committee.html`
- `templates/pages/chamber_comparison.html`
- `tests/test_enhanced_site_generation.py`

- [ ] 7.1 Create Jinja2 templates
  - [ ] 7.1.1 Create senators_list.html template
  - [ ] 7.1.2 Create senator_profile.html template
  - [ ] 7.1.3 Create bicameral_bill.html template
  - [ ] 7.1.4 Create county.html template
  - [ ] 7.1.5 Create joint_committee.html template
  - [ ] 7.1.6 Create chamber_comparison.html template

- [ ] 7.2 Implement EnhancedSiteGenerator class
  - [ ] 7.2.1 Extend Phase 1 StaticSiteGenerator
  - [ ] 7.2.2 Implement generate_senator_pages method
  - [ ] 7.2.3 Implement generate_bicameral_bill_pages method
  - [ ] 7.2.4 Implement generate_county_pages method
  - [ ] 7.2.5 Implement generate_joint_committee_pages method
  - [ ] 7.2.6 Implement generate_chamber_comparison_page method
  - [ ] 7.2.7 Implement _prepare_bicameral_bill_data method

- [ ] 7.3 Implement page generation methods
  - [ ] 7.3.1 Generate Senator directory page
  - [ ] 7.3.2 Generate individual Senator profile pages
  - [ ] 7.3.3 Generate bicameral bill pages with timeline
  - [ ] 7.3.4 Generate county representation pages
  - [ ] 7.3.5 Generate joint committee pages
  - [ ] 7.3.6 Generate chamber comparison dashboard

- [ ] 7.4 Write unit tests
  - [ ] 7.4.1 Test Senator page generation
  - [ ] 7.4.2 Test bicameral bill page generation
  - [ ] 7.4.3 Test county page generation
  - [ ] 7.4.4 Test template rendering
  - [ ] 7.4.5 Test link generation

- [ ] 7.5 Write property-based tests
  - [ ] 7.5.1 **Property 7.1**: Page generation completeness
    - **Validates**: Requirements 8.1-8.6
    - **Strategy**: Count generated pages, compare with database records
  - [ ] 7.5.2 **Property 7.2**: Link integrity
    - **Validates**: Requirements 8.1.5
    - **Strategy**: Crawl generated site, verify all links resolve

---

### Task 8: Performance Optimization

**Acceptance Criteria**:
- Hansard processing <10 min per document
- Full site generation <30 min
- Database queries <100ms
- Memory usage <8GB
- Cache hit rate ≥40%

**Files**:
- `hansard_tales/optimization/cached_llm_analyzer.py`
- `hansard_tales/optimization/batch_processor.py`
- `hansard_tales/optimization/parallel_processor.py`
- `hansard_tales/optimization/optimized_queries.py`
- `hansard_tales/optimization/incremental_processor.py`
- `tests/test_performance_optimization.py`

- [ ] 8.1 Implement aggressive caching
  - [ ] 8.1.1 Create CachedLLMAnalyzer class
  - [ ] 8.1.2 Implement TTL cache (7 days)
  - [ ] 8.1.3 Implement _generate_cache_key method
  - [ ] 8.1.4 Integrate with existing LLMAnalyzer

- [ ] 8.2 Implement batch processing
  - [ ] 8.2.1 Create BatchProcessor class
  - [ ] 8.2.2 Implement process_documents method
  - [ ] 8.2.3 Implement _group_by_type method
  - [ ] 8.2.4 Implement _process_batch method
  - [ ] 8.2.5 Implement _process_hansard_batch method
  - [ ] 8.2.6 Implement _process_votes_batch method

- [ ] 8.3 Implement parallel processing
  - [ ] 8.3.1 Create ParallelProcessor class
  - [ ] 8.3.2 Implement process_chambers_parallel method
  - [ ] 8.3.3 Implement process_chamber method
  - [ ] 8.3.4 Use ThreadPoolExecutor for parallelization

- [ ] 8.4 Implement database query optimization
  - [ ] 8.4.1 Create OptimizedQueries class
  - [ ] 8.4.2 Implement get_statements_with_members method (eager loading)
  - [ ] 8.4.3 Implement get_bills_with_related_data method (eager loading)
  - [ ] 8.4.4 Add database indexes for frequently queried columns

- [ ] 8.5 Implement incremental processing
  - [ ] 8.5.1 Create IncrementalProcessor class
  - [ ] 8.5.2 Implement get_documents_to_process method
  - [ ] 8.5.3 Implement mark_processed method
  - [ ] 8.5.4 Add last_processed_at field to DocumentORM

- [ ] 8.6 Write unit tests
  - [ ] 8.6.1 Test cache functionality
  - [ ] 8.6.2 Test batch processing
  - [ ] 8.6.3 Test parallel processing
  - [ ] 8.6.4 Test query optimization
  - [ ] 8.6.5 Test incremental processing

- [ ] 8.7 Write property-based tests
  - [ ] 8.7.1 **Property 8.1**: Processing completeness
    - **Validates**: Requirements 9.1.7
    - **Strategy**: Count processed documents, verify matches total
  - [ ] 8.7.2 **Property 8.2**: Cache correctness
    - **Validates**: Requirements 9.3.2
    - **Strategy**: Process same document with/without cache, verify identical

- [ ] 8.8 Performance benchmarking
  - [ ] 8.8.1 Benchmark Hansard processing time
  - [ ] 8.8.2 Benchmark site generation time
  - [ ] 8.8.3 Benchmark database query performance
  - [ ] 8.8.4 Measure memory usage
  - [ ] 8.8.5 Measure cache hit rate


---

## Week 4: Integration, Testing, and Documentation

### Task 9: Senate Data Import and Processing

**Acceptance Criteria**:
- All 67 Senators imported
- Senator metadata accurate
- County assignments correct
- Category assignments correct

**Files**:
- `hansard_tales/database/import_senators.py`
- `data/senators_13th_parliament.json`
- `tests/test_senator_import.py`

- [ ] 9.1 Create Senator data file
  - [ ] 9.1.1 Collect Senator data from parliament website
  - [ ] 9.1.2 Create senators_13th_parliament.json
  - [ ] 9.1.3 Include all 47 elected Senators
  - [ ] 9.1.4 Include 16 nominated Senators
  - [ ] 9.1.5 Include 4 ex-officio Senators

- [ ] 9.2 Implement import_senators.py script
  - [ ] 9.2.1 Load Senator data from JSON
  - [ ] 9.2.2 Validate Senator data
  - [ ] 9.2.3 Insert Senators into database
  - [ ] 9.2.4 Handle duplicates
  - [ ] 9.2.5 Log import results

- [ ] 9.3 Write unit tests
  - [ ] 9.3.1 Test Senator data validation
  - [ ] 9.3.2 Test import functionality
  - [ ] 9.3.3 Test duplicate handling
  - [ ] 9.3.4 Test county assignments

- [ ] 9.4 Write property-based tests
  - [ ] 9.4.1 **Property 9.1**: Senator count accuracy
    - **Validates**: Requirements 1.2.1
    - **Strategy**: Verify 67 Senators imported (47 elected + 16 nominated + 4 ex-officio)
  - [ ] 9.4.2 **Property 9.2**: County coverage
    - **Validates**: Requirements 1.2.2
    - **Strategy**: Verify all 47 counties have elected Senators

---

### Task 10: Pipeline Orchestration for Both Chambers

**Acceptance Criteria**:
- Both chambers process in parallel
- Error isolation between chambers
- Progress tracking for both chambers
- Cost tracking for both chambers

**Files**:
- `hansard_tales/pipeline/bicameral_orchestrator.py`
- `tests/test_bicameral_orchestration.py`

- [ ] 10.1 Implement BicameralOrchestrator class
  - [ ] 10.1.1 Extend Phase 1 ProcessingPipeline
  - [ ] 10.1.2 Implement process_both_chambers method
  - [ ] 10.1.3 Implement parallel chamber processing
  - [ ] 10.1.4 Implement error isolation
  - [ ] 10.1.5 Implement progress tracking
  - [ ] 10.1.6 Implement cost tracking

- [ ] 10.2 Implement chamber-specific pipelines
  - [ ] 10.2.1 Create NA processing pipeline
  - [ ] 10.2.2 Create Senate processing pipeline
  - [ ] 10.2.3 Implement pipeline coordination

- [ ] 10.3 Write unit tests
  - [ ] 10.3.1 Test parallel processing
  - [ ] 10.3.2 Test error isolation
  - [ ] 10.3.3 Test progress tracking
  - [ ] 10.3.4 Test cost tracking

- [ ] 10.4 Write property-based tests
  - [ ] 10.4.1 **Property 10.1**: Pipeline completeness
    - **Validates**: Requirements 1.3.7
    - **Strategy**: Verify all stages run for both chambers
  - [ ] 10.4.2 **Property 10.2**: Error isolation
    - **Validates**: Requirements 1.3.7
    - **Strategy**: Inject error in one chamber, verify other continues

---

### Task 11: Integration and End-to-End Testing

**Acceptance Criteria**:
- Complete pipeline processes both chambers
- All components integrate correctly
- Performance meets requirements
- Cost stays within budget

**Files**:
- `tests/test_phase3_integration.py`
- `tests/test_phase3_end_to_end.py`

- [ ] 11.1 Integration tests
  - [ ] 11.1.1 Test Senate document scraping
  - [ ] 11.1.2 Test Senate document processing
  - [ ] 11.1.3 Test bicameral bill tracking
  - [ ] 11.1.4 Test Senator profile generation
  - [ ] 11.1.5 Test cross-chamber analysis
  - [ ] 11.1.6 Test enhanced site generation

- [ ] 11.2 End-to-end tests
  - [ ] 11.2.1 Process complete Senate Hansard
  - [ ] 11.2.2 Process complete Senate Votes
  - [ ] 11.2.3 Process Senate Bills
  - [ ] 11.2.4 Process Senate Questions
  - [ ] 11.2.5 Process Senate Petitions
  - [ ] 11.2.6 Generate all Senator profiles
  - [ ] 11.2.7 Generate bicameral bill pages
  - [ ] 11.2.8 Generate complete site

- [ ] 11.3 Performance testing
  - [ ] 11.3.1 Benchmark Senate Hansard processing (<10 min)
  - [ ] 11.3.2 Benchmark Senate Votes processing (<2 min)
  - [ ] 11.3.3 Benchmark Senate Bill processing (<5 min)
  - [ ] 11.3.4 Benchmark bicameral tracking (<10 min)
  - [ ] 11.3.5 Benchmark site generation (<30 min)
  - [ ] 11.3.6 Measure memory usage (<8GB)

- [ ] 11.4 Cost monitoring
  - [ ] 11.4.1 Track LLM costs for both chambers
  - [ ] 11.4.2 Verify budget compliance (≤$50/month)
  - [ ] 11.4.3 Verify caching effectiveness (≥40% reduction)
  - [ ] 11.4.4 Generate cost report

---

### Task 12: Monitoring and Observability

**Acceptance Criteria**:
- Chamber-specific metrics tracked
- Bicameral metrics tracked
- Performance metrics tracked
- Cost metrics tracked

**Files**:
- `hansard_tales/monitoring/bicameral_metrics.py`
- `config/grafana/dashboards/bicameral_overview.json`
- `tests/test_bicameral_monitoring.py`

- [ ] 12.1 Implement bicameral metrics
  - [ ] 12.1.1 Add chamber-specific counters
  - [ ] 12.1.2 Add bicameral bill tracking metrics
  - [ ] 12.1.3 Add cross-chamber analysis metrics
  - [ ] 12.1.4 Add performance metrics

- [ ] 12.2 Create Grafana dashboard
  - [ ] 12.2.1 Create bicameral overview dashboard
  - [ ] 12.2.2 Add chamber comparison panels
  - [ ] 12.2.3 Add bicameral bill tracking panels
  - [ ] 12.2.4 Add performance panels

- [ ] 12.3 Write unit tests
  - [ ] 12.3.1 Test metric recording
  - [ ] 12.3.2 Test dashboard configuration

- [ ] 12.4 Write property-based tests
  - [ ] 12.4.1 **Property 12.1**: Metrics accuracy
    - **Validates**: Requirements 10.1.5
    - **Strategy**: Compare metrics with database counts


---

### Task 13: Configuration and Documentation

**Acceptance Criteria**:
- Configuration file documented
- README with setup instructions
- API documentation generated
- Example usage provided

**Files**:
- `config/phase3.yaml`
- `docs/phase3/README.md`
- `docs/phase3/API.md`
- `docs/phase3/EXAMPLES.md`
- `docs/phase3/BICAMERAL_TRACKING.md`

- [ ] 13.1 Configuration
  - [ ] 13.1.1 Create phase3.yaml config file
  - [ ] 13.1.2 Document all configuration options
  - [ ] 13.1.3 Add Senate-specific configuration
  - [ ] 13.1.4 Add bicameral tracking configuration
  - [ ] 13.1.5 Create example configurations

- [ ] 13.2 Documentation
  - [ ] 13.2.1 Write setup instructions
  - [ ] 13.2.2 Write usage guide
  - [ ] 13.2.3 Document bicameral tracking
  - [ ] 13.2.4 Document Senator profiles
  - [ ] 13.2.5 Document cross-chamber analysis
  - [ ] 13.2.6 Create example scripts
  - [ ] 13.2.7 Document troubleshooting

- [ ] 13.3 Code documentation
  - [ ] 13.3.1 Add docstrings to all new classes
  - [ ] 13.3.2 Add docstrings to all new functions
  - [ ] 13.3.3 Generate API documentation
  - [ ] 13.3.4 Add inline comments for complex logic

- [ ] 13.4 User guides
  - [ ] 13.4.1 Create bicameral tracking guide
  - [ ] 13.4.2 Create Senator profile guide
  - [ ] 13.4.3 Create cross-chamber analysis guide
  - [ ] 13.4.4 Create county representation guide

---

## Summary

**Total Tasks**: 13 major tasks
**Total Subtasks**: ~200 subtasks
**Timeline**: 4 weeks
**Test Coverage Target**: ≥90%
**Budget**: ≤$50/month

**Key Milestones**:
- Week 1: Database schema and component refactoring complete
- Week 2: Bicameral tracking and Senator profiles complete
- Week 3: Site generation and performance optimization complete
- Week 4: Integration testing and documentation complete

**Dependencies**:
- Phase 0 (Foundation) must be complete ✓
- Phase 1 (Core Analysis) must be complete ✓
- Phase 2 (Extended Documents) must be complete ✓
- Tasks 1-2 must complete before Task 3
- Tasks 3-4 must complete before Task 5
- Tasks 5-6 must complete before Task 7
- Task 8 can run in parallel with Tasks 5-7
- Tasks 7-8 must complete before Task 10
- Tasks 9-10 must complete before Task 11
- Tasks 11-12 must complete before Task 13

**Performance Targets**:
- Hansard processing: <10 min per document
- Vote processing: <2 min per document
- Bill processing: <5 min per bill
- Bicameral tracking: <10 min for full dataset
- Full site generation: <30 min
- Database queries: <100ms per query
- Memory usage: <8GB
- Cache hit rate: ≥40%

**Cost Management**:
- Monthly budget: $50
- LLM costs: ~$30/month (with caching)
- Hosting costs: $0 (Cloudflare Pages)
- Database costs: $0 (self-hosted PostgreSQL)
- Vector DB costs: $0 (self-hosted Qdrant)
- Monitoring costs: $0 (self-hosted Prometheus/Grafana)

**Test Coverage**:
- Unit tests: ≥90% coverage
- Integration tests: All major workflows
- Property tests: 24 properties validated
- End-to-end tests: Complete pipeline

**Property-Based Tests Summary**:
- Schema: 2 properties
- Component refactoring: 2 properties
- Senate scrapers: 2 properties
- Bicameral tracking: 2 properties
- Senator profiles: 2 properties
- Cross-chamber analysis: 2 properties
- Site generation: 2 properties
- Performance optimization: 2 properties
- Senator import: 2 properties
- Pipeline orchestration: 2 properties
- Monitoring: 1 property
- **Total**: 21 properties

**Completion Criteria**:
Phase 3 is complete when:
- ✓ All 13 tasks completed
- ✓ All 21 property tests passing
- ✓ Test coverage ≥90%
- ✓ Performance targets met
- ✓ Budget compliance verified
- ✓ Documentation complete
- ✓ Ready to proceed to Phase 4

**Next Steps**:
1. Review and approve this task list
2. Begin implementation with Task 1 (Database Schema)
3. Execute tasks in order, completing all subtasks
4. Run tests after each task
5. Update task status as work progresses
6. Monitor performance and costs throughout
7. Generate progress reports weekly

