# Phase 2: Extended Documents - Requirements

## Introduction

Phase 2 extends the Hansard Tales system to process Bills, Questions, and Petitions from the National Assembly. This phase builds on Phase 1's analysis pipeline to enable comprehensive tracking of legislative activity and cross-document correlation.

**Phase Goals**:
- Process Bills with version tracking and lifecycle management
- Process Questions with answer pairing and ministry categorization
- Process Petitions with status tracking and sponsor linking
- Enable cross-document correlation (bills ↔ statements ↔ votes)
- Enhance MP profiles with Q&A and bill sponsorship activity
- Generate bill tracking and legislative activity pages

**Timeline**: 4 weeks (Weeks 7-10)
**Budget**: ~$30/month (increased LLM usage for bill analysis)

## Document Types

### Bills (National Assembly)
- **Source**: Parliament website bills section
- **Format**: PDF documents with multiple versions
- **Frequency**: Ongoing (new bills introduced regularly)
- **Volume**: ~50-100 bills per parliamentary session

### Questions (National Assembly)
- **Source**: Parliament website questions section
- **Format**: PDF documents (daily questions lists)
- **Frequency**: Daily when parliament in session
- **Volume**: ~20-50 questions per sitting day

### Petitions (National Assembly)
- **Source**: Parliament website petitions section
- **Format**: PDF documents
- **Frequency**: Weekly/monthly
- **Volume**: ~10-30 petitions per month

---

## Requirements

### 1. Bill Processing

#### 1.1 Bill Scraping and Download
**Priority**: High  
**Description**: Scrape and download all bills from National Assembly website

**Acceptance Criteria**:
- Discovers all available bills automatically
- Downloads bill PDFs with version tracking
- Handles multiple bill versions (First Reading, Second Reading, Committee, etc.)
- Detects new bills and updates
- Stores bill metadata (number, title, sponsor, date)
- Prevents duplicate downloads

**Testing**: Verify all bills from sample session downloaded

---

#### 1.2 Bill Text Extraction
**Priority**: High  
**Description**: Extract structured text from bill PDFs

**Acceptance Criteria**:
- Extracts bill title, number, and sponsor
- Extracts bill sections and clauses
- Preserves document structure (parts, sections, subsections)
- Handles amendments and tracked changes
- Extracts explanatory memorandum
- Text extraction accuracy ≥95%

**Testing**: Compare extracted text with source PDFs for 20 bills

---

#### 1.3 Bill Version Tracking
**Priority**: High  
**Description**: Track bill versions through legislative process

**Acceptance Criteria**:
- Identifies bill version (First Reading, Second Reading, Committee, etc.)
- Links versions of same bill
- Tracks changes between versions
- Stores version history
- Detects amendments and modifications

**Testing**: Verify version tracking for 10 bills with multiple versions

---

#### 1.4 Bill Metadata Extraction
**Priority**: High  
**Description**: Extract and structure bill metadata

**Acceptance Criteria**:
- Extracts bill number (e.g., "Bill No. 15 of 2024")
- Extracts bill title
- Identifies sponsor MP
- Extracts introduction date
- Identifies ministry/department
- Extracts bill type (Public, Private, Money Bill, etc.)
- Metadata accuracy ≥95%

**Testing**: Verify metadata for 50 bills

---

#### 1.5 Bill Summarization
**Priority**: Medium  
**Description**: Generate AI summaries of bills

**Acceptance Criteria**:
- Generates 2-3 paragraph summary
- Extracts key provisions (3-5 items)
- Identifies affected laws
- Summarizes objectives
- All summaries include citations
- Summary accuracy verified manually

**Testing**: Manual review of 20 bill summaries

---

#### 1.6 Bill-Statement Correlation
**Priority**: High  
**Description**: Link bills to Hansard statements that discuss them

**Acceptance Criteria**:
- Detects bill mentions in statements (≥90% recall)
- Links statements to correct bills
- Handles contextual references ("the Bill")
- Tracks debate history for each bill
- Identifies MPs who spoke about bill
- Correlation accuracy ≥85%

**Testing**: Verify correlations for 30 bills with known debates

---

#### 1.7 Bill-Vote Correlation
**Priority**: High  
**Description**: Link bills to voting records

**Acceptance Criteria**:
- Links votes to bills automatically
- Tracks voting history for each bill
- Identifies bill stage for each vote
- Correlates vote outcomes with bill progress
- Correlation accuracy ≥95%

**Testing**: Verify vote-bill links for 20 bills

---

### 2. Question Processing

#### 2.1 Question Scraping and Download
**Priority**: High  
**Description**: Scrape and download parliamentary questions

**Acceptance Criteria**:
- Discovers all available questions automatically
- Downloads question PDFs by date
- Handles oral and written questions
- Stores question metadata
- Prevents duplicate downloads
- Processes daily question lists

**Testing**: Verify all questions from sample week downloaded

---

#### 2.2 Question-Answer Pairing
**Priority**: High  
**Description**: Extract and pair questions with answers

**Acceptance Criteria**:
- Extracts question text
- Extracts answer text
- Pairs questions with answers
- Identifies unanswered questions
- Handles supplementary questions
- Pairing accuracy ≥95%

**Testing**: Verify pairing for 100 questions

---

#### 2.3 Question Metadata Extraction
**Priority**: High  
**Description**: Extract structured metadata from questions

**Acceptance Criteria**:
- Extracts question number
- Identifies asking MP
- Identifies responding minister/official
- Extracts question date
- Extracts answer date (if answered)
- Identifies question type (oral/written)
- Identifies ministry/department
- Metadata accuracy ≥95%

**Testing**: Verify metadata for 100 questions

---

#### 2.4 Question Categorization
**Priority**: Medium  
**Description**: Categorize questions by topic and ministry

**Acceptance Criteria**:
- Assigns primary topic to each question
- Assigns secondary topics (up to 3)
- Identifies relevant ministry
- Groups related questions
- Categorization accuracy ≥80%

**Testing**: Manual review of 50 question categorizations

---

#### 2.5 Question-Statement Linking
**Priority**: Medium  
**Description**: Link questions to related Hansard statements

**Acceptance Criteria**:
- Links oral questions to Hansard debate
- Identifies follow-up discussions
- Tracks question references in statements
- Linking accuracy ≥85%

**Testing**: Verify links for 30 oral questions

---

### 3. Petition Processing

#### 3.1 Petition Scraping and Download
**Priority**: High  
**Description**: Scrape and download public petitions

**Acceptance Criteria**:
- Discovers all available petitions automatically
- Downloads petition PDFs
- Stores petition metadata
- Prevents duplicate downloads
- Tracks petition updates

**Testing**: Verify all petitions from sample month downloaded

---

#### 3.2 Petition Text Extraction
**Priority**: High  
**Description**: Extract structured text from petitions

**Acceptance Criteria**:
- Extracts petition title
- Extracts petitioner name/organization
- Extracts petition text
- Extracts prayer (what is being requested)
- Identifies sponsor MP
- Text extraction accuracy ≥95%

**Testing**: Compare extracted text with source for 20 petitions

---

#### 3.3 Petition Metadata Extraction
**Priority**: High  
**Description**: Extract structured metadata from petitions

**Acceptance Criteria**:
- Extracts petition number
- Extracts submission date
- Identifies sponsor MP
- Identifies assigned committee
- Extracts petition status
- Metadata accuracy ≥95%

**Testing**: Verify metadata for 50 petitions

---

#### 3.4 Petition Categorization
**Priority**: Medium  
**Description**: Categorize petitions by topic

**Acceptance Criteria**:
- Assigns primary topic to each petition
- Assigns secondary topics (up to 3)
- Groups related petitions
- Categorization accuracy ≥80%

**Testing**: Manual review of 30 petition categorizations

---

#### 3.5 Petition Status Tracking
**Priority**: Medium  
**Description**: Track petition progress through system

**Acceptance Criteria**:
- Tracks petition status (submitted, committee review, response pending, etc.)
- Identifies assigned committee
- Tracks committee actions
- Identifies responses/outcomes
- Updates status automatically

**Testing**: Verify status tracking for 20 petitions

---

### 4. Cross-Document Correlation

#### 4.1 Bill Lifecycle Tracking
**Priority**: High  
**Description**: Track complete bill lifecycle across documents

**Acceptance Criteria**:
- Links bill versions chronologically
- Links bill to related statements
- Links bill to related votes
- Links bill to related questions
- Generates timeline visualization
- Tracks bill status (introduced, committee, passed, etc.)

**Testing**: Verify complete lifecycle for 10 bills

---

#### 4.2 MP Legislative Activity Tracking
**Priority**: High  
**Description**: Track MP activity across all document types

**Acceptance Criteria**:
- Tracks bills sponsored by MP
- Tracks questions asked by MP
- Tracks petitions sponsored by MP
- Tracks statements about bills
- Tracks votes on bills
- Generates activity summary

**Testing**: Verify activity tracking for 20 MPs

---

#### 4.3 Topic-Based Correlation
**Priority**: Medium  
**Description**: Correlate documents by topic

**Acceptance Criteria**:
- Groups bills by topic
- Groups questions by topic
- Groups petitions by topic
- Links related documents across types
- Generates topic pages

**Testing**: Verify topic grouping for 5 major topics

---

### 5. Enhanced MP Profiles

#### 5.1 Bill Sponsorship Tracking
**Priority**: High  
**Description**: Add bill sponsorship to MP profiles

**Acceptance Criteria**:
- Lists all bills sponsored by MP
- Shows bill status for each
- Calculates success rate
- Identifies co-sponsors
- Tracks bill topics

**Testing**: Verify bill data for 30 MP profiles

---

#### 5.2 Question Activity Tracking
**Priority**: High  
**Description**: Add question activity to MP profiles

**Acceptance Criteria**:
- Lists all questions asked by MP
- Shows answer status
- Categorizes questions by topic
- Calculates question frequency
- Identifies most questioned ministries

**Testing**: Verify question data for 30 MP profiles

---

#### 5.3 Petition Sponsorship Tracking
**Priority**: Medium  
**Description**: Add petition sponsorship to MP profiles

**Acceptance Criteria**:
- Lists all petitions sponsored by MP
- Shows petition status
- Categorizes petitions by topic
- Tracks petition outcomes

**Testing**: Verify petition data for 20 MP profiles

---

### 6. Site Generation Enhancements

#### 6.1 Bill Tracking Pages
**Priority**: High  
**Description**: Generate static pages for bill tracking

**Acceptance Criteria**:
- Bill directory page (all bills)
- Individual bill pages with full details
- Bill version comparison pages
- Bill timeline visualization
- Related statements/votes sections
- Search and filter functionality

**Testing**: Verify pages generated for all bills

---

#### 6.2 Question Pages
**Priority**: Medium  
**Description**: Generate static pages for questions

**Acceptance Criteria**:
- Question directory page
- Individual question pages
- Ministry-specific question pages
- Unanswered questions page
- Search functionality

**Testing**: Verify pages generated for all questions

---

#### 6.3 Petition Pages
**Priority**: Medium  
**Description**: Generate static pages for petitions

**Acceptance Criteria**:
- Petition directory page
- Individual petition pages
- Status-based petition pages
- Topic-based petition pages

**Testing**: Verify pages generated for all petitions

---

#### 6.4 Legislative Activity Dashboard
**Priority**: Medium  
**Description**: Generate dashboard showing legislative activity

**Acceptance Criteria**:
- Shows recent bills
- Shows recent questions
- Shows recent petitions
- Shows active debates
- Shows upcoming votes
- Updates automatically

**Testing**: Verify dashboard accuracy

---

### 7. Performance and Scalability

#### 7.1 Processing Performance
**Priority**: High  
**Description**: Maintain acceptable processing times

**Acceptance Criteria**:
- Bill processing: <5 minutes per bill
- Question processing: <2 minutes per question list
- Petition processing: <3 minutes per petition
- Correlation processing: <10 minutes for full dataset
- Site generation: <15 minutes for complete site

**Testing**: Benchmark processing times

---

#### 7.2 Cost Management
**Priority**: High  
**Description**: Keep LLM costs within budget

**Acceptance Criteria**:
- Monthly LLM costs ≤$30
- Bill summarization costs tracked
- Question categorization costs tracked
- Caching reduces costs by ≥40%
- Budget alerts configured

**Testing**: Monitor costs for one month

---

### 8. Data Quality and Validation

#### 8.1 Data Completeness
**Priority**: High  
**Description**: Ensure all documents processed

**Acceptance Criteria**:
- No missing bills from source
- No missing questions from source
- No missing petitions from source
- All correlations attempted
- Missing data flagged for review

**Testing**: Compare database counts with source

---

#### 8.2 Data Accuracy
**Priority**: High  
**Description**: Validate extracted data accuracy

**Acceptance Criteria**:
- Bill metadata accuracy ≥95%
- Question metadata accuracy ≥95%
- Petition metadata accuracy ≥95%
- Correlation accuracy ≥85%
- Manual spot-checks pass

**Testing**: Manual validation of 100 random records

---

### 9. Testing and Quality Assurance

#### 9.1 Unit Test Coverage
**Priority**: High  
**Description**: Maintain high test coverage

**Acceptance Criteria**:
- Overall test coverage ≥90%
- All new modules have tests
- All edge cases covered
- Property-based tests for key functions

**Testing**: Run coverage reports

---

#### 9.2 Integration Testing
**Priority**: High  
**Description**: Test component integration

**Acceptance Criteria**:
- Bill processing pipeline tested end-to-end
- Question processing pipeline tested end-to-end
- Petition processing pipeline tested end-to-end
- Correlation pipeline tested end-to-end
- Site generation tested with all document types

**Testing**: Run integration test suite

---

### 10. Documentation

#### 10.1 Technical Documentation
**Priority**: Medium  
**Description**: Document Phase 2 implementation

**Acceptance Criteria**:
- API documentation complete
- Data model documentation complete
- Processing pipeline documented
- Configuration options documented

**Testing**: Documentation review

---

#### 10.2 User Documentation
**Priority**: Medium  
**Description**: Document user-facing features

**Acceptance Criteria**:
- Bill tracking guide
- Question browsing guide
- Petition browsing guide
- Search functionality guide

**Testing**: User documentation review

---

## Summary

**Total Requirements**: 40 requirements across 10 categories

**Key Metrics**:
- Bill processing: <5 min per bill
- Question processing: <2 min per list
- Petition processing: <3 min per petition
- Metadata accuracy: ≥95%
- Correlation accuracy: ≥85%
- Test coverage: ≥90%
- Monthly cost: ≤$30

**Dependencies**:
- Phase 0 (Foundation) must be complete
- Phase 1 (Core Analysis) must be complete
- Vector database operational
- LLM API configured
- Static site generator working

**Next Steps**:
1. Review and approve requirements
2. Create design document
3. Create implementation tasks
4. Begin development
