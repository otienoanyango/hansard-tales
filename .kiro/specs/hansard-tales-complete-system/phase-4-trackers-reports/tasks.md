# Phase 4: Trackers and Reports - Implementation Tasks

## Overview

This document breaks down Phase 4 implementation into actionable tasks. Phase 4 adds tracker documents, Legislative Proposals, Auditor General Reports, and Order Papers, completing the document type coverage.

**Timeline**: 4 weeks | **Test Coverage Target**: ≥90% | **Budget**: ≤$60/month

## Task Status Legend
- `[ ]` Not started | `[~]` Queued | `[-]` In progress | `[x]` Completed | `[ ]*` Optional

---

## Week 1: Database Schema and Tracker Scrapers

### Task 1: Database Schema Extensions

**Acceptance Criteria**:
- All 8 new tables created
- Foreign keys and indexes configured
- Migration tested (upgrade and downgrade)
- Source traceability verified

**Files**:
- `hansard_tales/database/migrations/004_add_trackers_and_reports.py`
- `hansard_tales/database/models.py`
- `tests/test_phase4_schema.py`

- [ ] 1.1 Create Alembic migration
  - [ ] 1.1.1 Add statement_requests table
  - [ ] 1.1.2 Add motion_tracker table
  - [ ] 1.1.3 Add bill_tracker_entries table
  - [ ] 1.1.4 Add legislative_proposals table
  - [ ] 1.1.5 Add auditor_general_reports table
  - [ ] 1.1.6 Add audit_findings table
  - [ ] 1.1.7 Add order_papers table
  - [ ] 1.1.8 Add agenda_items table
  - [ ] 1.1.9 Add all indexes
  - [ ] 1.1.10 Add foreign key constraints

- [ ] 1.2 Update ORM models
  - [ ] 1.2.1 Create StatementRequestORM model
  - [ ] 1.2.2 Create MotionTrackerORM model
  - [ ] 1.2.3 Create BillTrackerEntryORM model
  - [ ] 1.2.4 Create LegislativeProposalORM model
  - [ ] 1.2.5 Create AuditorGeneralReportORM model
  - [ ] 1.2.6 Create AuditFindingORM model
  - [ ] 1.2.7 Create OrderPaperORM model
  - [ ] 1.2.8 Create AgendaItemORM model
  - [ ] 1.2.9 Update relationships

- [ ] 1.3 Write migration tests
  - [ ] 1.3.1 Test schema creation
  - [ ] 1.3.2 Test foreign key constraints
  - [ ] 1.3.3 Test rollback functionality

- [ ] 1.4 Write property-based tests
  - [ ] 1.4.1 **Property 1.1**: Tracker data completeness
    - **Validates**: Requirements 1.2.1, 2.2.1, 3.2.1
    - **Strategy**: Manual count vs extracted count for 10 documents
  - [ ] 1.4.2 **Property 1.2**: Source traceability
    - **Validates**: Requirements 13.1.1
    - **Strategy**: Verify source references for all entries

---

### Task 2: Tracker Document Scrapers

**Acceptance Criteria**:
- All tracker types discoverable
- Both chambers supported
- Duplicate prevention works
- Metadata extraction accurate

**Files**:
- `hansard_tales/scrapers/tracker_scraper.py`
- `hansard_tales/scrapers/statements_tracker_scraper.py`
- `hansard_tales/scrapers/motions_tracker_scraper.py`
- `hansard_tales/scrapers/bills_tracker_scraper.py`
- `hansard_tales/scrapers/legislative_proposals_scraper.py`
- `hansard_tales/scrapers/ag_report_scraper.py`
- `hansard_tales/scrapers/order_paper_scraper.py`
- `tests/test_tracker_scrapers.py`

- [ ] 2.1 Implement base TrackerScraper
  - [ ] 2.1.1 Create TrackerScraper extending BaseScraper
  - [ ] 2.1.2 Implement _get_chamber_base_url method
  - [ ] 2.1.3 Add chamber parameter support

- [ ] 2.2 Implement Statements Tracker scraper
  - [ ] 2.2.1 Create StatementsTrackerScraper
  - [ ] 2.2.2 Implement discover_trackers method
  - [ ] 2.2.3 Implement _extract_tracker_metadata method

- [ ] 2.3 Implement Motions Tracker scraper
  - [ ] 2.3.1 Create MotionsTrackerScraper
  - [ ] 2.3.2 Implement discover_trackers method

- [ ] 2.4 Implement Bills Tracker scraper
  - [ ] 2.4.1 Create BillsTrackerScraper
  - [ ] 2.4.2 Implement discover_trackers method

- [ ] 2.5 Implement Legislative Proposals scraper
  - [ ] 2.5.1 Create LegislativeProposalsScraper
  - [ ] 2.5.2 Implement discover_proposals method

- [ ] 2.6 Implement AG Report scraper
  - [ ] 2.6.1 Create AuditorGeneralReportScraper
  - [ ] 2.6.2 Implement discover_reports method
  - [ ] 2.6.3 Support year filtering

- [ ] 2.7 Implement Order Paper scraper
  - [ ] 2.7.1 Create OrderPaperScraper
  - [ ] 2.7.2 Implement discover_order_papers method

- [ ] 2.8 Write unit tests
  - [ ] 2.8.1 Test URL generation for all types
  - [ ] 2.8.2 Test document discovery (mocked)
  - [ ] 2.8.3 Test metadata extraction
  - [ ] 2.8.4 Test duplicate prevention

- [ ] 2.9 Write property-based tests
  - [ ] 2.9.1 **Property 2.1**: Tracker discovery completeness
    - **Validates**: Requirements 1.1.1, 2.1.1, 3.1.1
    - **Strategy**: Compare with manual count for sample period
  - [ ] 2.9.2 **Property 2.2**: Chamber tagging
    - **Validates**: Requirements 1.1.1, 2.1.1, 3.1.1
    - **Strategy**: Verify chamber field for all documents


---

## Week 2: Tracker Processors and AG Report Analyzer

### Task 3: Tracker Document Processors

**Acceptance Criteria**:
- All tracker entries extracted
- Table extraction works reliably
- Member identification accurate
- Data parsing accuracy ≥95%

**Files**:
- `hansard_tales/processors/statements_tracker_processor.py`
- `hansard_tales/processors/motions_tracker_processor.py`
- `hansard_tales/processors/bills_tracker_processor.py`
- `hansard_tales/processors/legislative_proposal_processor.py`
- `tests/test_tracker_processors.py`

- [ ] 3.1 Implement StatementsTrackerProcessor
  - [ ] 3.1.1 Create StatementRequest dataclass
  - [ ] 3.1.2 Implement process_tracker method
  - [ ] 3.1.3 Implement _parse_statement_row method
  - [ ] 3.1.4 Integrate ParliamentarianIdentifier
  - [ ] 3.1.5 Extract fulfillment status

- [ ] 3.2 Implement MotionsTrackerProcessor
  - [ ] 3.2.1 Create MotionEntry dataclass
  - [ ] 3.2.2 Implement process_tracker method
  - [ ] 3.2.3 Implement _parse_motion_row method
  - [ ] 3.2.4 Extract motion status

- [ ] 3.3 Implement BillsTrackerProcessor
  - [ ] 3.3.1 Create BillTrackerEntry dataclass
  - [ ] 3.3.2 Implement process_tracker method
  - [ ] 3.3.3 Implement _parse_bill_row method
  - [ ] 3.3.4 Calculate days_at_stage
  - [ ] 3.3.5 Identify stalled bills

- [ ] 3.4 Implement LegislativeProposalProcessor
  - [ ] 3.4.1 Create LegislativeProposal dataclass
  - [ ] 3.4.2 Implement process_proposal method
  - [ ] 3.4.3 Implement _extract_metadata method
  - [ ] 3.4.4 Integrate ParliamentarianIdentifier

- [ ] 3.5 Write unit tests
  - [ ] 3.5.1 Test table extraction
  - [ ] 3.5.2 Test row parsing
  - [ ] 3.5.3 Test member identification
  - [ ] 3.5.4 Test status extraction
  - [ ] 3.5.5 Test date parsing

- [ ] 3.6 Write property-based tests
  - [ ] 3.6.1 **Property 3.1**: Table extraction completeness
    - **Validates**: Requirements 1.2.1, 2.2.1, 3.2.1
    - **Strategy**: Manual count vs extracted count for 10 documents
  - [ ] 3.6.2 **Property 3.2**: Data parsing accuracy
    - **Validates**: Requirements 1.4.1, 2.4.1, 3.4.1
    - **Strategy**: Manual verification of 100 entries

---

### Task 4: Auditor General Report Analyzer

**Acceptance Criteria**:
- All findings extracted
- Entity identification accurate
- Financial amounts extracted correctly
- Severity categorization accurate

**Files**:
- `hansard_tales/analyzers/ag_report_analyzer.py`
- `tests/test_ag_report_analyzer.py`

- [ ] 4.1 Implement AuditFinding dataclass
  - [ ] 4.1.1 Add all finding fields
  - [ ] 4.1.2 Add financial amount field (Decimal)
  - [ ] 4.1.3 Add severity and type fields

- [ ] 4.2 Implement AuditorGeneralReportAnalyzer
  - [ ] 4.2.1 Implement process_report method
  - [ ] 4.2.2 Implement _segment_findings method
  - [ ] 4.2.3 Implement _process_finding method
  - [ ] 4.2.4 Implement _extract_entity method (spaCy NER)
  - [ ] 4.2.5 Implement _extract_amount method
  - [ ] 4.2.6 Implement _extract_recommendation method
  - [ ] 4.2.7 Implement _categorize_finding method (LLM)
  - [ ] 4.2.8 Implement _classify_entity_type method

- [ ] 4.3 Write unit tests
  - [ ] 4.3.1 Test finding segmentation
  - [ ] 4.3.2 Test entity extraction
  - [ ] 4.3.3 Test amount extraction
  - [ ] 4.3.4 Test recommendation extraction
  - [ ] 4.3.5 Test categorization (mocked LLM)

- [ ] 4.4 Write property-based tests
  - [ ] 4.4.1 **Property 4.1**: Extraction completeness
    - **Validates**: Requirements 5.2.2
    - **Strategy**: Manual count vs extracted count for 5 reports
  - [ ] 4.4.2 **Property 4.2**: Financial amount accuracy
    - **Validates**: Requirements 5.5.2
    - **Strategy**: Manual verification of 50 amounts

---

### Task 5: Order Paper Parser

**Acceptance Criteria**:
- All agenda items extracted
- Item type classification accurate
- Time allocation extracted
- Related document references extracted

**Files**:
- `hansard_tales/parsers/order_paper_parser.py`
- `hansard_tales/trackers/agenda_execution_tracker.py`
- `tests/test_order_paper_parser.py`

- [ ] 5.1 Implement AgendaItem dataclass
  - [ ] 5.1.1 Add item fields
  - [ ] 5.1.2 Add AgendaItemType enum
  - [ ] 5.1.3 Add related document reference fields

- [ ] 5.2 Implement OrderPaperParser
  - [ ] 5.2.1 Implement parse_order_paper method
  - [ ] 5.2.2 Implement _extract_agenda_items method
  - [ ] 5.2.3 Implement _classify_item_type method
  - [ ] 5.2.4 Implement _extract_time_allocation method
  - [ ] 5.2.5 Implement _extract_related_references method

- [ ] 5.3 Implement AgendaExecutionTracker
  - [ ] 5.3.1 Implement link_agenda_to_proceedings method
  - [ ] 5.3.2 Implement _check_item_execution method
  - [ ] 5.3.3 Implement calculate_completion_rate method

- [ ] 5.4 Write unit tests
  - [ ] 5.4.1 Test agenda item extraction
  - [ ] 5.4.2 Test item type classification
  - [ ] 5.4.3 Test time allocation extraction
  - [ ] 5.4.4 Test reference extraction
  - [ ] 5.4.5 Test execution tracking

- [ ] 5.5 Write property-based tests
  - [ ] 5.5.1 **Property 5.1**: Agenda extraction completeness
    - **Validates**: Requirements 6.2.1
    - **Strategy**: Manual count vs extracted count for 10 Order Papers
  - [ ] 5.5.2 **Property 5.2**: Execution tracking accuracy
    - **Validates**: Requirements 6.5.3
    - **Strategy**: Manual verification of 50 agenda items

---

## Week 3: Correlation and Analytics

### Task 6: Enhanced Correlation Engine

**Acceptance Criteria**:
- Statement requests linked to Hansard
- Motions linked to votes
- AG findings linked to debates
- Proposals linked to bills
- Correlation accuracy ≥85%

**Files**:
- `hansard_tales/correlation/enhanced_correlation_engine.py`
- `tests/test_enhanced_correlation.py`

- [ ] 6.1 Implement EnhancedCorrelationEngine
  - [ ] 6.1.1 Extend Phase 2 CorrelationEngine
  - [ ] 6.1.2 Implement link_statement_requests_to_hansard method
  - [ ] 6.1.3 Implement _find_matching_statement method
  - [ ] 6.1.4 Implement link_motions_to_votes method
  - [ ] 6.1.5 Implement _is_matching_vote method
  - [ ] 6.1.6 Implement link_ag_findings_to_debates method
  - [ ] 6.1.7 Implement _find_statements_about_entity method
  - [ ] 6.1.8 Implement _find_questions_about_entity method
  - [ ] 6.1.9 Implement link_proposals_to_bills method

- [ ] 6.2 Write unit tests
  - [ ] 6.2.1 Test statement request linking
  - [ ] 6.2.2 Test motion-vote linking
  - [ ] 6.2.3 Test AG finding-debate linking
  - [ ] 6.2.4 Test proposal-bill linking
  - [ ] 6.2.5 Test vector similarity matching

- [ ] 6.3 Write property-based tests
  - [ ] 6.3.1 **Property 6.1**: Correlation completeness
    - **Validates**: Requirements 7.1.1, 7.1.2, 7.1.3
    - **Strategy**: Verify correlation attempts for all entries
  - [ ] 6.3.2 **Property 6.2**: AG report-debate linking
    - **Validates**: Requirements 7.2.1
    - **Strategy**: Manual review of 30 findings

---

### Task 7: Accountability Analytics

**Acceptance Criteria**:
- Constituency representation scores calculated
- Financial oversight metrics generated
- Legislative efficiency metrics calculated
- All scores in valid range (0-100)

**Files**:
- `hansard_tales/analytics/accountability_analyzer.py`
- `tests/test_accountability_analytics.py`

- [ ] 7.1 Implement ConstituencyRepresentationScore dataclass
  - [ ] 7.1.1 Add activity count fields
  - [ ] 7.1.2 Add score fields

- [ ] 7.2 Implement AccountabilityAnalyzer
  - [ ] 7.2.1 Implement calculate_constituency_representation method
  - [ ] 7.2.2 Calculate statement score
  - [ ] 7.2.3 Calculate question score
  - [ ] 7.2.4 Calculate petition score
  - [ ] 7.2.5 Calculate overall representation score

- [ ] 7.3 Implement financial oversight analytics
  - [ ] 7.3.1 Implement generate_financial_oversight_report method
  - [ ] 7.3.2 Calculate total irregularities
  - [ ] 7.3.3 Group by entity
  - [ ] 7.3.4 Calculate parliamentary response rate
  - [ ] 7.3.5 Implement _calculate_oversight_activity method

- [ ] 7.4 Implement legislative efficiency analytics
  - [ ] 7.4.1 Implement generate_legislative_efficiency_report method
  - [ ] 7.4.2 Calculate average stage times
  - [ ] 7.4.3 Identify stalled bills
  - [ ] 7.4.4 Calculate agenda completion rates

- [ ] 7.5 Write unit tests
  - [ ] 7.5.1 Test representation score calculation
  - [ ] 7.5.2 Test financial oversight report
  - [ ] 7.5.3 Test legislative efficiency report
  - [ ] 7.5.4 Test oversight activity calculation

- [ ] 7.6 Write property-based tests
  - [ ] 7.6.1 **Property 7.1**: Correlation completeness
    - **Validates**: Requirements 7.1.1-7.1.4
    - **Strategy**: Verify correlation attempts
  - [ ] 7.6.2 **Property 7.2**: Representation score validity
    - **Validates**: Requirements 8.3.4
    - **Strategy**: Verify all scores in 0-100 range


---

## Week 4: Site Generation, Integration, and Documentation

### Task 8: Enhanced Site Generation

**Acceptance Criteria**:
- All tracker pages generated
- AG report pages generated
- Accountability dashboards generated
- All internal links valid

**Files**:
- `hansard_tales/site/phase4_site_generator.py`
- `templates/pages/statements_tracker.html`
- `templates/pages/motions_tracker.html`
- `templates/pages/bills_tracker.html`
- `templates/pages/ag_report.html`
- `templates/pages/ag_reports_list.html`
- `templates/pages/order_paper.html`
- `templates/pages/financial_oversight.html`
- `templates/pages/legislative_efficiency.html`
- `templates/pages/constituency_representation.html`
- `tests/test_phase4_site_generation.py`

- [ ] 8.1 Create Jinja2 templates
  - [ ] 8.1.1 Create statements_tracker.html
  - [ ] 8.1.2 Create motions_tracker.html
  - [ ] 8.1.3 Create bills_tracker.html
  - [ ] 8.1.4 Create ag_report.html
  - [ ] 8.1.5 Create ag_reports_list.html
  - [ ] 8.1.6 Create order_paper.html
  - [ ] 8.1.7 Create financial_oversight.html
  - [ ] 8.1.8 Create legislative_efficiency.html
  - [ ] 8.1.9 Create constituency_representation.html

- [ ] 8.2 Implement Phase4SiteGenerator
  - [ ] 8.2.1 Extend Phase 3 EnhancedSiteGenerator
  - [ ] 8.2.2 Implement generate_statements_tracker_pages method
  - [ ] 8.2.3 Implement generate_motions_tracker_pages method
  - [ ] 8.2.4 Implement generate_bills_tracker_pages method
  - [ ] 8.2.5 Implement generate_legislative_proposal_pages method
  - [ ] 8.2.6 Implement generate_ag_report_pages method
  - [ ] 8.2.7 Implement generate_order_paper_pages method
  - [ ] 8.2.8 Implement generate_financial_oversight_dashboard method
  - [ ] 8.2.9 Implement generate_legislative_efficiency_dashboard method
  - [ ] 8.2.10 Implement generate_constituency_representation_pages method

- [ ] 8.3 Implement helper methods
  - [ ] 8.3.1 Implement _calculate_entity_stats method
  - [ ] 8.3.2 Implement _format_currency filter
  - [ ] 8.3.3 Implement _prepare_dashboard_data methods

- [ ] 8.4 Write unit tests
  - [ ] 8.4.1 Test tracker page generation
  - [ ] 8.4.2 Test AG report page generation
  - [ ] 8.4.3 Test dashboard generation
  - [ ] 8.4.4 Test template rendering
  - [ ] 8.4.5 Test link generation

- [ ] 8.5 Write property-based tests
  - [ ] 8.5.1 **Property 8.1**: Page generation completeness
    - **Validates**: Requirements 9.1.1-9.5.3
    - **Strategy**: Count generated pages vs database records
  - [ ] 8.5.2 **Property 8.2**: Dashboard accuracy
    - **Validates**: Requirements 9.5.1-9.5.3
    - **Strategy**: Manual verification of dashboard data

---

### Task 9: Enhanced MP/Senator Profiles

**Acceptance Criteria**:
- Tracker activity added to profiles
- Oversight activity tracked
- Constituency representation scores included
- All profile fields populated

**Files**:
- `hansard_tales/profiles/enhanced_profile_generator.py`
- `tests/test_enhanced_profiles.py`

- [ ] 9.1 Extend profile generators
  - [ ] 9.1.1 Add statement request tracking to MPProfileGenerator
  - [ ] 9.1.2 Add motion activity to profiles
  - [ ] 9.1.3 Add legislative proposal activity to profiles
  - [ ] 9.1.4 Add oversight activity tracking
  - [ ] 9.1.5 Add constituency representation score

- [ ] 9.2 Implement profile methods
  - [ ] 9.2.1 Implement _get_statement_requests method
  - [ ] 9.2.2 Implement _get_motions method
  - [ ] 9.2.3 Implement _get_proposals method
  - [ ] 9.2.4 Implement _calculate_oversight_activity method
  - [ ] 9.2.5 Implement _calculate_representation_score method

- [ ] 9.3 Write unit tests
  - [ ] 9.3.1 Test tracker data aggregation
  - [ ] 9.3.2 Test oversight activity calculation
  - [ ] 9.3.3 Test representation score calculation

- [ ] 9.4 Write property-based tests
  - [ ] 9.4.1 **Property 9.1**: Profile completeness
    - **Validates**: Requirements 8.1.1-8.3.4
    - **Strategy**: Verify all fields for 30 profiles

---

### Task 10: Cost Management and Optimization

**Acceptance Criteria**:
- Monthly costs ≤$60
- Cache hit rate ≥50%
- Selective LLM usage implemented
- Cost tracking accurate

**Files**:
- `hansard_tales/optimization/phase4_cost_manager.py`
- `tests/test_phase4_cost_management.py`

- [ ] 10.1 Implement Phase4CostManager
  - [ ] 10.1.1 Extend Phase 1 CostManager
  - [ ] 10.1.2 Implement should_use_llm method
  - [ ] 10.1.3 Implement estimate_monthly_cost method
  - [ ] 10.1.4 Add tracker-specific cost tracking

- [ ] 10.2 Implement selective LLM usage
  - [ ] 10.2.1 Skip LLM for structured trackers
  - [ ] 10.2.2 Use LLM only for AG report categorization
  - [ ] 10.2.3 Use LLM only for proposal categorization
  - [ ] 10.2.4 Implement aggressive caching

- [ ] 10.3 Write unit tests
  - [ ] 10.3.1 Test LLM usage decisions
  - [ ] 10.3.2 Test cost estimation
  - [ ] 10.3.3 Test cache effectiveness

- [ ] 10.4 Write property-based tests
  - [ ] 10.4.1 **Property 10.1**: Budget compliance
    - **Validates**: Requirements 11.1.1
    - **Strategy**: Track actual costs for one month
  - [ ] 10.4.2 **Property 10.2**: Cache effectiveness
    - **Validates**: Requirements 11.2.2
    - **Strategy**: Monitor cache hits vs misses

---

### Task 11: Integration and End-to-End Testing

**Acceptance Criteria**:
- Complete pipeline processes all document types
- All components integrate correctly
- Performance meets requirements
- Cost stays within budget

**Files**:
- `tests/test_phase4_integration.py`
- `tests/test_phase4_end_to_end.py`

- [ ] 11.1 Integration tests
  - [ ] 11.1.1 Test Statements Tracker processing pipeline
  - [ ] 11.1.2 Test Motions Tracker processing pipeline
  - [ ] 11.1.3 Test Bills Tracker processing pipeline
  - [ ] 11.1.4 Test Legislative Proposals processing pipeline
  - [ ] 11.1.5 Test AG Report processing pipeline
  - [ ] 11.1.6 Test Order Paper processing pipeline
  - [ ] 11.1.7 Test enhanced correlation engine
  - [ ] 11.1.8 Test accountability analytics
  - [ ] 11.1.9 Test enhanced profile generation
  - [ ] 11.1.10 Test site generation

- [ ] 11.2 End-to-end tests
  - [ ] 11.2.1 Process complete Statements Tracker
  - [ ] 11.2.2 Process complete Motions Tracker
  - [ ] 11.2.3 Process complete Bills Tracker
  - [ ] 11.2.4 Process complete AG Report
  - [ ] 11.2.5 Process complete Order Paper
  - [ ] 11.2.6 Generate all correlations
  - [ ] 11.2.7 Generate all analytics
  - [ ] 11.2.8 Generate complete site

- [ ] 11.3 Performance testing
  - [ ] 11.3.1 Benchmark Statements Tracker processing (<5 min)
  - [ ] 11.3.2 Benchmark Motions Tracker processing (<5 min)
  - [ ] 11.3.3 Benchmark Bills Tracker processing (<3 min)
  - [ ] 11.3.4 Benchmark AG Report processing (<30 min)
  - [ ] 11.3.5 Benchmark Order Paper processing (<3 min)
  - [ ] 11.3.6 Benchmark full site generation (<45 min)
  - [ ] 11.3.7 Measure memory usage (<10GB)

- [ ] 11.4 Cost monitoring
  - [ ] 11.4.1 Track LLM costs for all document types
  - [ ] 11.4.2 Verify budget compliance (≤$60/month)
  - [ ] 11.4.3 Verify cache effectiveness (≥50% hit rate)
  - [ ] 11.4.4 Generate cost breakdown report

---

### Task 12: Monitoring and Observability

**Acceptance Criteria**:
- Document type-specific metrics tracked
- Correlation metrics tracked
- Cost metrics tracked
- Quality metrics tracked

**Files**:
- `hansard_tales/monitoring/phase4_metrics.py`
- `config/grafana/dashboards/phase4_overview.json`
- `tests/test_phase4_monitoring.py`

- [ ] 12.1 Implement Phase 4 metrics
  - [ ] 12.1.1 Add tracker processing metrics
  - [ ] 12.1.2 Add AG report processing metrics
  - [ ] 12.1.3 Add correlation metrics
  - [ ] 12.1.4 Add cost metrics per document type

- [ ] 12.2 Create Grafana dashboard
  - [ ] 12.2.1 Create Phase 4 overview dashboard
  - [ ] 12.2.2 Add tracker processing panels
  - [ ] 12.2.3 Add AG report analysis panels
  - [ ] 12.2.4 Add correlation panels
  - [ ] 12.2.5 Add cost tracking panels

- [ ] 12.3 Write unit tests
  - [ ] 12.3.1 Test metric recording
  - [ ] 12.3.2 Test dashboard configuration

- [ ] 12.4 Write property-based tests
  - [ ] 12.4.1 **Property 12.1**: Metrics accuracy
    - **Validates**: Requirements 14.1.1-14.2.4
    - **Strategy**: Compare metrics with database counts

---

### Task 13: Configuration and Documentation

**Acceptance Criteria**:
- Configuration file documented
- README with setup instructions
- API documentation generated
- Example usage provided

**Files**:
- `config/phase4.yaml`
- `docs/phase4/README.md`
- `docs/phase4/TRACKERS.md`
- `docs/phase4/AG_REPORTS.md`
- `docs/phase4/ACCOUNTABILITY.md`
- `docs/phase4/EXAMPLES.md`

- [ ] 13.1 Configuration
  - [ ] 13.1.1 Create phase4.yaml config file
  - [ ] 13.1.2 Document all configuration options
  - [ ] 13.1.3 Add tracker-specific configuration
  - [ ] 13.1.4 Add AG report configuration
  - [ ] 13.1.5 Create example configurations

- [ ] 13.2 Documentation
  - [ ] 13.2.1 Write setup instructions
  - [ ] 13.2.2 Write tracker processing guide
  - [ ] 13.2.3 Write AG report analysis guide
  - [ ] 13.2.4 Write accountability analytics guide
  - [ ] 13.2.5 Create example scripts
  - [ ] 13.2.6 Document troubleshooting

- [ ] 13.3 Code documentation
  - [ ] 13.3.1 Add docstrings to all new classes
  - [ ] 13.3.2 Add docstrings to all new functions
  - [ ] 13.3.3 Generate API documentation
  - [ ] 13.3.4 Add inline comments for complex logic

- [ ] 13.4 User guides
  - [ ] 13.4.1 Create tracker documents guide
  - [ ] 13.4.2 Create AG reports guide
  - [ ] 13.4.3 Create accountability dashboards guide
  - [ ] 13.4.4 Create constituency representation guide

---

## Summary

**Total Tasks**: 13 major tasks
**Total Subtasks**: ~180 subtasks
**Timeline**: 4 weeks
**Test Coverage Target**: ≥90%
**Budget**: ≤$60/month

**Key Milestones**:
- Week 1: Database schema and tracker scrapers complete
- Week 2: Tracker processors and AG report analyzer complete
- Week 3: Correlation engine and accountability analytics complete
- Week 4: Site generation, integration testing, and documentation complete

**Dependencies**:
- Phase 0 (Foundation) must be complete ✓
- Phase 1 (Core Analysis) must be complete ✓
- Phase 2 (Extended Documents) must be complete ✓
- Phase 3 (Senate Integration) must be complete ✓
- Tasks 1-2 must complete before Task 3
- Tasks 3-5 must complete before Task 6
- Tasks 6-7 must complete before Task 8
- Tasks 8-9 must complete before Task 11
- Task 10 can run in parallel with Tasks 6-9
- Tasks 11-12 must complete before Task 13

**Performance Targets**:
- Statements Tracker: <5 min per document
- Motions Tracker: <5 min per document
- Bills Tracker: <3 min per document
- Legislative Proposals: <10 min per document
- AG Reports: <30 min per document
- Order Papers: <3 min per document
- Full site generation: <45 min
- Database queries: <100ms
- Memory usage: <10GB

**Cost Management**:
- Monthly budget: $60
- LLM costs: ~$40/month (with selective usage and caching)
- Infrastructure: ~$20/month
- Cache hit rate target: ≥50%
- Selective LLM usage for trackers (structured data)
- Full LLM usage only for AG report categorization

**Test Coverage**:
- Unit tests: ≥90% coverage
- Integration tests: All major workflows
- Property tests: 18 properties validated
- End-to-end tests: Complete pipeline

**Property-Based Tests Summary**:
- Database schema: 2 properties
- Tracker scrapers: 2 properties
- Tracker processors: 2 properties
- AG report analyzer: 2 properties
- Order Paper parser: 2 properties
- Correlation engine: 2 properties
- Accountability analytics: 2 properties
- Site generation: 2 properties
- Cost management: 2 properties
- **Total**: 18 properties

**New Document Types** (6 per chamber + 1 shared = 13 total):
1. Statements Tracker (NA)
2. Statements Tracker (Senate)
3. Motions Tracker (NA)
4. Motions Tracker (Senate)
5. Bills Tracker (NA)
6. Bills Tracker (Senate)
7. Legislative Proposals (NA)
8. Legislative Proposals (Senate)
9. Order Papers (NA)
10. Order Papers (Senate)
11. Auditor General Reports (shared)

**Total System Coverage**: 22 document types

**New Analytics**:
- Constituency representation scoring
- Financial oversight tracking
- Legislative efficiency metrics
- Agenda execution tracking
- Proposal-to-bill conversion tracking

**New Pages**:
- Tracker directory and detail pages (6 types)
- AG report pages with finding details
- Financial oversight dashboard
- Legislative efficiency dashboard
- Constituency representation pages

**Completion Criteria**:
Phase 4 is complete when:
- ✓ All 13 tasks completed
- ✓ All 18 property tests passing
- ✓ Test coverage ≥90%
- ✓ Performance targets met
- ✓ Budget compliance verified (≤$60/month)
- ✓ All 22 document types processed
- ✓ Documentation complete
- ✓ Ready to proceed to Phase 5

**Next Steps**:
1. Review and approve this task list
2. Begin implementation with Task 1 (Database Schema)
3. Execute tasks in order, completing all subtasks
4. Run tests after each task
5. Update task status as work progresses
6. Monitor performance and costs throughout
7. Generate progress reports weekly

