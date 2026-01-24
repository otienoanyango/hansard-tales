# Phase 2: Extended Documents - Implementation Tasks

## Overview

Phase 2 extends Hansard Tales to process Bills, Questions, and Petitions. This builds on Phase 0 (Foundation) and Phase 1 (Core Analysis).

**Current Status**: Phase 0 and Phase 1 complete. Phase 2 not started.

**Timeline**: 4 weeks | **Test Coverage**: ≥90% | **Budget**: ≤$30/month

## Task Status Legend
- `[ ]` Not started | `[~]` Queued | `[-]` In progress | `[x]` Completed | `[ ]*` Optional

---

## Week 1: Bill Processing Infrastructure

### Task 1: Database Schema for Bills, Questions, Petitions

**Acceptance Criteria**:
- Bills, bill_versions, questions, petitions tables created
- Foreign keys and indexes configured
- Migration script tested

**Files**:
- `hansard_tales/database/migrations/add_phase2_tables.py`
- `tests/test_phase2_schema.py`

- [ ] 1.1 Create migration script
  - [ ] 1.1.1 Add bills table (bill_number, title, sponsor_id, introduction_date, ministry, bill_type, status)
  - [ ] 1.1.2 Add bill_versions table (bill_id, version_number, version_stage, text, changes_summary)
  - [ ] 1.1.3 Add questions table (question_number, asker_id, respondent, question_text, answer_text, question_date, question_type, ministry)
  - [ ] 1.1.4 Add petitions table (petition_number, title, petitioner, sponsor_id, submission_date, petition_text, prayer, status)
  - [ ] 1.1.5 Add indexes for performance
  - [ ] 1.1.6 Add foreign key constraints

- [ ] 1.2 Write migration tests
  - [ ] 1.2.1 Test schema creation
  - [ ] 1.2.2 Test foreign key constraints
  - [ ] 1.2.3 Test rollback functionality

---

### Task 2: Bill Scraper and Downloader

**Acceptance Criteria**:
- Discovers all bills from parliament website
- Downloads bill PDFs with version tracking
- Prevents duplicate downloads
- Metadata accuracy ≥95%

**Files**:
- `hansard_tales/scrapers/bill_scraper.py`
- `tests/test_bill_scraper.py`

- [ ] 2.1 Implement BillScraper class
  - [ ] 2.1.1 Create BillMetadata dataclass
  - [ ] 2.1.2 Implement discover_bills method
  - [ ] 2.1.3 Implement version detection
  - [ ] 2.1.4 Implement download_bill method
  - [ ] 2.1.5 Implement duplicate prevention

- [ ] 2.2 Write unit tests
  - [ ] 2.2.1 Test bill discovery
  - [ ] 2.2.2 Test metadata extraction
  - [ ] 2.2.3 Test version detection
  - [ ] 2.2.4 Test download functionality

- [ ] 2.3 Write property-based tests
  - [ ] 2.3.1 **Property 2.1**: All bills discovered
    - **Validates**: Requirements 1.1
    - **Strategy**: Compare with manual count from website
  - [ ] 2.3.2 **Property 2.2**: No duplicate downloads
    - **Validates**: Requirements 1.1
    - **Strategy**: Verify unique filenames and checksums

---

### Task 3: Bill Text Extraction and Structure Parsing

**Acceptance Criteria**:
- Text extraction accuracy ≥95%
- Preserves document structure (parts, sections, subsections)
- Extracts explanatory memorandum
- Handles amendments

**Files**:
- `hansard_tales/processors/bill_text_extractor.py`
- `tests/test_bill_text_extractor.py`

- [ ] 3.1 Implement BillTextExtractor class
  - [ ] 3.1.1 Create BillSection and BillStructure dataclasses
  - [ ] 3.1.2 Implement text extraction
  - [ ] 3.1.3 Implement metadata extraction
  - [ ] 3.1.4 Implement structure parsing (parts, sections, subsections)
  - [ ] 3.1.5 Implement explanatory memo extraction
  - [ ] 3.1.6 Implement schedule parsing

- [ ] 3.2 Write unit tests
  - [ ] 3.2.1 Test text extraction
  - [ ] 3.2.2 Test metadata extraction
  - [ ] 3.2.3 Test structure parsing
  - [ ] 3.2.4 Test edge cases

- [ ] 3.3 Write property-based tests
  - [ ] 3.3.1 **Property 3.1**: Text extraction accuracy ≥95%
    - **Validates**: Requirements 1.2
    - **Strategy**: Compare with source for 20 bills
  - [ ] 3.3.2 **Property 3.2**: Structure preservation
    - **Validates**: Requirements 1.2
    - **Strategy**: Verify all sections/subsections extracted

---

### Task 4: Bill Version Tracking

**Acceptance Criteria**:
- Tracks bill versions chronologically
- Links versions of same bill
- Generates diffs between versions
- Stores version history

**Files**:
- `hansard_tales/processors/bill_version_tracker.py`
- `tests/test_bill_version_tracker.py`

- [ ] 4.1 Implement BillVersionTracker class
  - [ ] 4.1.1 Create BillChange dataclass
  - [ ] 4.1.2 Implement add_version method
  - [ ] 4.1.3 Implement generate_diff method
  - [ ] 4.1.4 Implement section identification
  - [ ] 4.1.5 Implement changes summarization

- [ ] 4.2 Write unit tests
  - [ ] 4.2.1 Test version addition
  - [ ] 4.2.2 Test diff generation
  - [ ] 4.2.3 Test changes summarization

- [ ] 4.3 Write property-based tests
  - [ ] 4.3.1 **Property 4.1**: Version tracking completeness
    - **Validates**: Requirements 1.3
    - **Strategy**: Verify all versions tracked for 10 bills

---

## Week 2: Bill Analysis and Question Processing

### Task 5: Bill Summarization with LLM

**Acceptance Criteria**:
- Generates 2-3 paragraph summaries
- Extracts 3-5 key provisions
- Identifies affected laws
- All summaries include verified citations

**Files**:
- `hansard_tales/analysis/bill_summarizer.py`
- `tests/test_bill_summarizer.py`

- [ ] 5.1 Implement BillSummarizer class
  - [ ] 5.1.1 Create BillSummary Pydantic model
  - [ ] 5.1.2 Implement summarize_bill method
  - [ ] 5.1.3 Implement prompt building
  - [ ] 5.1.4 Implement response parsing
  - [ ] 5.1.5 Integrate citation verification

- [ ] 5.2 Write unit tests
  - [ ] 5.2.1 Test prompt building
  - [ ] 5.2.2 Test response parsing
  - [ ] 5.2.3 Test citation verification
  - [ ] 5.2.4 Mock LLM calls

- [ ] 5.3 Write property-based tests
  - [ ] 5.3.1 **Property 5.1**: Summary accuracy
    - **Validates**: Requirements 1.5
    - **Strategy**: Manual review of 20 summaries
  - [ ] 5.3.2 **Property 5.2**: Citation verification
    - **Validates**: Requirements 1.5
    - **Strategy**: Verify all citations traceable

---

### Task 6: Question Scraper and Downloader

**Acceptance Criteria**:
- Discovers all questions by date
- Downloads question PDFs
- Handles oral and written questions
- Prevents duplicate downloads

**Files**:
- `hansard_tales/scrapers/question_scraper.py`
- `tests/test_question_scraper.py`

- [ ] 6.1 Implement QuestionScraper class
  - [ ] 6.1.1 Create QuestionMetadata dataclass
  - [ ] 6.1.2 Implement discover_questions method
  - [ ] 6.1.3 Implement download_questions method
  - [ ] 6.1.4 Implement date range filtering

- [ ] 6.2 Write unit tests
  - [ ] 6.2.1 Test question discovery
  - [ ] 6.2.2 Test download functionality
  - [ ] 6.2.3 Test date filtering
  - [ ] 6.2.4 Test duplicate prevention

- [ ] 6.3 Write property-based tests
  - [ ] 6.3.1 **Property 6.1**: Question discovery completeness
    - **Validates**: Requirements 2.1
    - **Strategy**: Verify all questions from sample week

---

### Task 7: Question-Answer Pairing

**Acceptance Criteria**:
- Pairs questions with answers accurately
- Identifies unanswered questions
- Handles supplementary questions
- Pairing accuracy ≥95%

**Files**:
- `hansard_tales/processors/question_processor.py`
- `tests/test_question_processor.py`

- [ ] 7.1 Implement QuestionAnswerPairer class
  - [ ] 7.1.1 Implement pair_qa method
  - [ ] 7.1.2 Implement extract_questions method
  - [ ] 7.1.3 Implement metadata extraction
  - [ ] 7.1.4 Implement MP resolution

- [ ] 7.2 Write unit tests
  - [ ] 7.2.1 Test Q&A pairing
  - [ ] 7.2.2 Test metadata extraction
  - [ ] 7.2.3 Test unanswered detection
  - [ ] 7.2.4 Test supplementary handling

- [ ] 7.3 Write property-based tests
  - [ ] 7.3.1 **Property 7.1**: Pairing accuracy ≥95%
    - **Validates**: Requirements 2.2
    - **Strategy**: Verify pairing for 100 questions

---

### Task 8: Question Categorization

**Acceptance Criteria**:
- Assigns primary and secondary topics
- Identifies relevant ministry
- Categorization accuracy ≥80%

**Files**:
- `hansard_tales/analysis/question_categorizer.py`
- `tests/test_question_categorizer.py`

- [ ] 8.1 Implement QuestionCategorizer class
  - [ ] 8.1.1 Reuse LLM analyzer from Phase 1
  - [ ] 8.1.2 Implement categorization prompt
  - [ ] 8.1.3 Implement ministry identification
  - [ ] 8.1.4 Implement topic assignment

- [ ] 8.2 Write unit tests
  - [ ] 8.2.1 Test categorization
  - [ ] 8.2.2 Test ministry identification
  - [ ] 8.2.3 Mock LLM calls

- [ ] 8.3 Write property-based tests
  - [ ] 8.3.1 **Property 8.1**: Categorization accuracy ≥80%
    - **Validates**: Requirements 2.4
    - **Strategy**: Manual review of 50 categorizations

---

## Week 3: Petition Processing and Correlation

### Task 9: Petition Scraper and Processor

**Acceptance Criteria**:
- Discovers all petitions
- Extracts petition text and metadata
- Tracks petition status
- Metadata accuracy ≥95%

**Files**:
- `hansard_tales/scrapers/petition_scraper.py`
- `hansard_tales/processors/petition_processor.py`
- `tests/test_petition_scraper.py`
- `tests/test_petition_processor.py`

- [ ] 9.1 Implement PetitionScraper class
  - [ ] 9.1.1 Create PetitionMetadata dataclass
  - [ ] 9.1.2 Implement discover_petitions method
  - [ ] 9.1.3 Implement download_petitions method

- [ ] 9.2 Implement PetitionProcessor class
  - [ ] 9.2.1 Implement extract_petition method
  - [ ] 9.2.2 Implement metadata extraction
  - [ ] 9.2.3 Implement prayer extraction
  - [ ] 9.2.4 Implement status extraction

- [ ] 9.3 Write unit tests
  - [ ] 9.3.1 Test petition discovery
  - [ ] 9.3.2 Test text extraction
  - [ ] 9.3.3 Test metadata extraction
  - [ ] 9.3.4 Test status tracking

- [ ] 9.4 Write property-based tests
  - [ ] 9.4.1 **Property 9.1**: Petition discovery completeness
    - **Validates**: Requirements 3.1
    - **Strategy**: Verify all petitions from sample month

---

### Task 10: Bill-Statement Correlation

**Acceptance Criteria**:
- Detects bill mentions in statements (≥90% recall)
- Links statements to correct bills
- Correlation accuracy ≥85%

**Files**:
- `hansard_tales/correlation/bill_statement_linker.py`
- `tests/test_bill_statement_linker.py`

- [ ] 10.1 Implement BillStatementLinker class
  - [ ] 10.1.1 Add bill-specific patterns
  - [ ] 10.1.2 Implement debate history tracking
  - [ ] 10.1.3 Implement MP tracking for bills

- [ ] 10.2 Write unit tests
  - [ ] 10.2.1 Test bill mention detection
  - [ ] 10.2.2 Test correlation accuracy
  - [ ] 10.2.3 Test contextual references

- [ ] 10.3 Write property-based tests
  - [ ] 10.3.1 **Property 10.1**: Bill mention recall ≥90%
    - **Validates**: Requirements 1.6
    - **Strategy**: Verify correlations for 30 bills
  - [ ] 10.3.2 **Property 10.2**: Correlation accuracy ≥85%
    - **Validates**: Requirements 1.6
    - **Strategy**: Manual verification of 50 correlations

---

### Task 11: Bill-Vote Correlation

**Acceptance Criteria**:
- Links votes to bills automatically
- Tracks voting history for each bill
- Correlation accuracy ≥95%

**Files**:
- `hansard_tales/correlation/bill_vote_linker.py`
- `tests/test_bill_vote_linker.py`

- [ ] 11.1 Implement BillVoteLinker class
  - [ ] 11.1.1 Implement vote-bill matching
  - [ ] 11.1.2 Implement stage identification
  - [ ] 11.1.3 Implement voting history tracking

- [ ] 11.2 Write unit tests
  - [ ] 11.2.1 Test vote-bill matching
  - [ ] 11.2.2 Test stage identification
  - [ ] 11.2.3 Test history tracking

- [ ] 11.3 Write property-based tests
  - [ ] 11.3.1 **Property 11.1**: Correlation accuracy ≥95%
    - **Validates**: Requirements 1.7
    - **Strategy**: Verify vote-bill links for 20 bills

---

### Task 12: Question-Statement Linking

**Acceptance Criteria**:
- Links oral questions to Hansard debate
- Identifies follow-up discussions
- Linking accuracy ≥85%

**Files**:
- `hansard_tales/correlation/question_statement_linker.py`
- `tests/test_question_statement_linker.py`

- [ ] 12.1 Implement QuestionStatementLinker class
  - [ ] 12.1.1 Implement question mention detection
  - [ ] 12.1.2 Implement debate linking
  - [ ] 12.1.3 Implement follow-up tracking

- [ ] 12.2 Write unit tests
  - [ ] 12.2.1 Test question detection
  - [ ] 12.2.2 Test debate linking
  - [ ] 12.2.3 Test follow-up tracking

- [ ] 12.3 Write property-based tests
  - [ ] 12.3.1 **Property 12.1**: Linking accuracy ≥85%
    - **Validates**: Requirements 2.5
    - **Strategy**: Verify links for 30 oral questions

---

### Task 13: Bill Lifecycle Tracker

**Acceptance Criteria**:
- Links bill versions chronologically
- Links bill to related documents
- Generates timeline visualization
- Tracks bill status

**Files**:
- `hansard_tales/correlation/bill_lifecycle_tracker.py`
- `tests/test_bill_lifecycle_tracker.py`

- [ ] 13.1 Implement BillLifecycleTracker class
  - [ ] 13.1.1 Implement version linking
  - [ ] 13.1.2 Implement document correlation
  - [ ] 13.1.3 Implement timeline generation
  - [ ] 13.1.4 Implement status tracking

- [ ] 13.2 Write unit tests
  - [ ] 13.2.1 Test version linking
  - [ ] 13.2.2 Test document correlation
  - [ ] 13.2.3 Test timeline generation

- [ ] 13.3 Write property-based tests
  - [ ] 13.3.1 **Property 13.1**: Lifecycle completeness
    - **Validates**: Requirements 4.1
    - **Strategy**: Verify complete lifecycle for 10 bills

---

### Task 14: MP Legislative Activity Tracker

**Acceptance Criteria**:
- Tracks bills sponsored by MP
- Tracks questions asked by MP
- Tracks petitions sponsored by MP
- Generates activity summary

**Files**:
- `hansard_tales/correlation/mp_activity_tracker.py`
- `tests/test_mp_activity_tracker.py`

- [ ] 14.1 Implement MPActivityTracker class
  - [ ] 14.1.1 Implement bill sponsorship tracking
  - [ ] 14.1.2 Implement question tracking
  - [ ] 14.1.3 Implement petition tracking
  - [ ] 14.1.4 Implement activity aggregation

- [ ] 14.2 Write unit tests
  - [ ] 14.2.1 Test bill tracking
  - [ ] 14.2.2 Test question tracking
  - [ ] 14.2.3 Test petition tracking
  - [ ] 14.2.4 Test aggregation

- [ ] 14.3 Write property-based tests
  - [ ] 14.3.1 **Property 14.1**: Activity tracking completeness
    - **Validates**: Requirements 4.2
    - **Strategy**: Verify activity for 20 MPs

---

## Week 4: Site Generation and Integration

### Task 15: Enhanced MP Profile Generator

**Acceptance Criteria**:
- Adds bill sponsorship data
- Adds question activity data
- Adds petition sponsorship data
- Calculates success rates

**Files**:
- `hansard_tales/site/enhanced_mp_profile_generator.py`
- `tests/test_enhanced_mp_profile_generator.py`

- [ ] 15.1 Extend MPProfileGenerator from Phase 1
  - [ ] 15.1.1 Add bill sponsorship tracking
  - [ ] 15.1.2 Add question activity tracking
  - [ ] 15.1.3 Add petition sponsorship tracking
  - [ ] 15.1.4 Calculate success rates

- [ ] 15.2 Write unit tests
  - [ ] 15.2.1 Test bill data aggregation
  - [ ] 15.2.2 Test question data aggregation
  - [ ] 15.2.3 Test petition data aggregation
  - [ ] 15.2.4 Test success rate calculation

- [ ] 15.3 Write property-based tests
  - [ ] 15.3.1 **Property 15.1**: Profile completeness
    - **Validates**: Requirements 5.1, 5.2, 5.3
    - **Strategy**: Verify all fields for 30 MP profiles

---

### Task 16: Bill Tracking Pages

**Acceptance Criteria**:
- Generates bill directory page
- Generates individual bill pages
- Generates version comparison pages
- Includes timeline visualization

**Files**:
- `hansard_tales/site/bill_page_generator.py`
- `templates/pages/bill_list.html`
- `templates/pages/bill_detail.html`
- `templates/pages/bill_version_compare.html`
- `tests/test_bill_page_generator.py`

- [ ] 16.1 Implement BillPageGenerator class
  - [ ] 16.1.1 Implement bill directory generation
  - [ ] 16.1.2 Implement individual bill pages
  - [ ] 16.1.3 Implement version comparison pages
  - [ ] 16.1.4 Implement timeline visualization

- [ ] 16.2 Create Jinja2 templates
  - [ ] 16.2.1 Create bill list template
  - [ ] 16.2.2 Create bill detail template
  - [ ] 16.2.3 Create version comparison template

- [ ] 16.3 Write unit tests
  - [ ] 16.3.1 Test directory generation
  - [ ] 16.3.2 Test detail page generation
  - [ ] 16.3.3 Test version comparison

- [ ] 16.4 Write property-based tests
  - [ ] 16.4.1 **Property 16.1**: Page generation completeness
    - **Validates**: Requirements 6.1
    - **Strategy**: Verify pages for all bills

---

### Task 17: Question and Petition Pages

**Acceptance Criteria**:
- Generates question directory page
- Generates individual question pages
- Generates petition directory page
- Generates individual petition pages

**Files**:
- `hansard_tales/site/question_page_generator.py`
- `hansard_tales/site/petition_page_generator.py`
- `templates/pages/question_list.html`
- `templates/pages/question_detail.html`
- `templates/pages/petition_list.html`
- `templates/pages/petition_detail.html`
- `tests/test_question_page_generator.py`
- `tests/test_petition_page_generator.py`

- [ ] 17.1 Implement QuestionPageGenerator class
  - [ ] 17.1.1 Implement question directory
  - [ ] 17.1.2 Implement individual question pages
  - [ ] 17.1.3 Implement ministry-specific pages
  - [ ] 17.1.4 Implement unanswered questions page

- [ ] 17.2 Implement PetitionPageGenerator class
  - [ ] 17.2.1 Implement petition directory
  - [ ] 17.2.2 Implement individual petition pages
  - [ ] 17.2.3 Implement status-based pages

- [ ] 17.3 Create Jinja2 templates
  - [ ] 17.3.1 Create question templates
  - [ ] 17.3.2 Create petition templates

- [ ] 17.4 Write unit tests
  - [ ] 17.4.1 Test question page generation
  - [ ] 17.4.2 Test petition page generation

- [ ] 17.5 Write property-based tests
  - [ ] 17.5.1 **Property 17.1**: Page generation completeness
    - **Validates**: Requirements 6.2, 6.3
    - **Strategy**: Verify pages for all questions and petitions

---

### Task 18: Legislative Activity Dashboard

**Acceptance Criteria**:
- Shows recent bills, questions, petitions
- Shows active debates and upcoming votes
- Updates automatically

**Files**:
- `hansard_tales/site/dashboard_generator.py`
- `templates/pages/dashboard.html`
- `tests/test_dashboard_generator.py`

- [ ] 18.1 Implement DashboardGenerator class
  - [ ] 18.1.1 Implement recent activity aggregation
  - [ ] 18.1.2 Implement active debates tracking
  - [ ] 18.1.3 Implement upcoming votes tracking
  - [ ] 18.1.4 Implement dashboard generation

- [ ] 18.2 Create dashboard template
  - [ ] 18.2.1 Create dashboard layout
  - [ ] 18.2.2 Add activity widgets
  - [ ] 18.2.3 Add visualization components

- [ ] 18.3 Write unit tests
  - [ ] 18.3.1 Test activity aggregation
  - [ ] 18.3.2 Test dashboard generation

- [ ] 18.4 Write property-based tests
  - [ ] 18.4.1 **Property 18.1**: Dashboard accuracy
    - **Validates**: Requirements 6.4
    - **Strategy**: Verify dashboard data matches database

---

### Task 19: Integration and End-to-End Testing

**Acceptance Criteria**:
- Complete pipeline processes all document types
- All components integrate correctly
- Performance meets requirements
- Cost stays within budget

**Files**:
- `tests/test_phase2_integration.py`
- `tests/test_phase2_end_to_end.py`

- [ ] 19.1 Integration tests
  - [ ] 19.1.1 Test bill processing pipeline
  - [ ] 19.1.2 Test question processing pipeline
  - [ ] 19.1.3 Test petition processing pipeline
  - [ ] 19.1.4 Test correlation engine
  - [ ] 19.1.5 Test enhanced profile generation
  - [ ] 19.1.6 Test site generation

- [ ] 19.2 End-to-end tests
  - [ ] 19.2.1 Process complete bill set
  - [ ] 19.2.2 Process complete question set
  - [ ] 19.2.3 Process complete petition set
  - [ ] 19.2.4 Generate all correlations
  - [ ] 19.2.5 Generate complete site
  - [ ] 19.2.6 Verify site content

- [ ] 19.3 Performance testing
  - [ ] 19.3.1 Benchmark bill processing (<5 min per bill)
  - [ ] 19.3.2 Benchmark question processing (<2 min per list)
  - [ ] 19.3.3 Benchmark petition processing (<3 min per petition)
  - [ ] 19.3.4 Benchmark correlation (<10 min for full dataset)
  - [ ] 19.3.5 Benchmark site generation (<15 min)

- [ ] 19.4 Cost monitoring
  - [ ] 19.4.1 Track LLM costs
  - [ ] 19.4.2 Verify budget compliance (≤$30/month)
  - [ ] 19.4.3 Verify caching effectiveness (≥40% reduction)

---

### Task 20: Configuration and Documentation

**Acceptance Criteria**:
- Configuration file documented
- README with setup instructions
- API documentation generated
- Example usage provided

**Files**:
- `config/phase2.yaml`
- `docs/phase2/README.md`
- `docs/phase2/API.md`
- `docs/phase2/EXAMPLES.md`

- [ ] 20.1 Configuration
  - [ ] 20.1.1 Create phase2.yaml config file
  - [ ] 20.1.2 Document all configuration options
  - [ ] 20.1.3 Create example configurations

- [ ] 20.2 Documentation
  - [ ] 20.2.1 Write setup instructions
  - [ ] 20.2.2 Write usage guide
  - [ ] 20.2.3 Document API endpoints
  - [ ] 20.2.4 Create example scripts
  - [ ] 20.2.5 Document troubleshooting

- [ ] 20.3 Code documentation
  - [ ] 20.3.1 Add docstrings to all classes
  - [ ] 20.3.2 Add docstrings to all functions
  - [ ] 20.3.3 Generate API documentation

---

## Summary

**Total Tasks**: 20 major tasks
**Total Subtasks**: ~180 subtasks
**Timeline**: 4 weeks
**Test Coverage Target**: ≥90%
**Budget**: ≤$30/month

**Key Milestones**:
- Week 1: Bill processing infrastructure complete
- Week 2: Bill analysis and question processing complete
- Week 3: Petition processing and cross-document correlation complete
- Week 4: Enhanced profiles, site generation, and integration testing complete

**Dependencies**:
- Phase 0 (Foundation) must be complete ✓
- Phase 1 (Core Analysis) must be complete ✓
- Tasks 1-4 must complete before Task 10
- Tasks 5-9 must complete before Tasks 12-15
- Tasks 10-15 must complete before Task 16
- Tasks 16-18 depend on all previous tasks
- Tasks 19-20 are final integration and documentation

**Next Steps**:
1. Review and approve this task list
2. Begin implementation with Task 1 (Database Schema)
3. Execute tasks in order, completing all subtasks
4. Run tests after each task
5. Update task status as work progresses
