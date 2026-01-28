# Phase 3: Senate Integration - Requirements

## Introduction

Phase 3 extends the Hansard Tales system to process all document types from the Senate chamber, effectively duplicating the National Assembly functionality for Kenya's upper house. This phase enables comprehensive bicameral parliamentary tracking, joint committee monitoring, and cross-chamber bill correlation.

**Phase Goals**:
- Process all Senate document types (Hansard, Votes, Bills, Questions, Petitions)
- Generate Senator profiles with full activity tracking
- Enable bicameral bill tracking (bills moving between chambers)
- Track joint committee activities
- Enable cross-chamber analysis and comparison
- Generate Senate-specific pages and dashboards

**Timeline**: 4 weeks (Weeks 11-14)
**Budget**: ~$50/month (doubled processing for both chambers)

## Document Types

### Senate Documents (All Types)
- **Hansard (Senate)**: Daily debates and proceedings
- **Votes & Proceedings (Senate)**: Voting records
- **Bills (Senate)**: Senate-originated bills and National Assembly bills under review
- **Questions (Senate)**: Senators' questions to government
- **Petitions (Senate)**: Public petitions to Senate
- **Statements Tracker (Senate)**: Constituency representation tracking
- **Motions Tracker (Senate)**: Motion status tracking
- **Bills Tracker (Senate)**: Bill progress tracking
- **Order Papers (Senate)**: Senate agenda
- **Legislative Proposals (Senate)**: Proposed legislation
- **Auditor General Reports (Senate)**: Financial audit reviews

**Source**: Parliament website Senate section
**Format**: PDF documents (similar structure to National Assembly)
**Frequency**: Daily when Senate in session
**Volume**: Similar to National Assembly (~60% of NA volume)

---

## Glossary

- **Senator**: Member of the Senate (upper house)
- **Bicameral**: Involving both chambers (National Assembly and Senate)
- **Joint Committee**: Committee with members from both chambers
- **Cross-Chamber Bill**: Bill that moves between National Assembly and Senate
- **County Representation**: Senate's role representing Kenya's 47 counties
- **Devolution**: Transfer of power to county governments (Senate oversight role)

---

## Requirements

### 1. Senate Data Infrastructure

#### 1.1 Database Schema Extension
**Priority**: High  
**Description**: Extend database schema to support Senate data

**Acceptance Criteria**:
- Adds `senators` table with same structure as `mps` table
- Extends `documents` table to support Senate chamber
- Extends `statements` table to support Senator attribution
- Extends `votes` table to support Senate votes
- Extends `bills` table to support bicameral tracking
- Adds `joint_committees` table
- Adds `cross_chamber_bills` table for bills moving between chambers
- All foreign key constraints properly configured
- Migration preserves existing National Assembly data

**Testing**: Verify schema migration on test database

---

#### 1.2 Senator Data Import
**Priority**: High  
**Description**: Import and maintain Senator roster

**Acceptance Criteria**:
- Imports all current Senators (67 total: 47 elected + 16 nominated + 4 ex-officio)
- Stores Senator metadata: name, party, county, category (elected/nominated/ex-officio)
- Handles Senator term tracking
- Supports historical Senator data
- Links Senators to counties
- Data accuracy ≥99%

**Testing**: Verify all 67 Senators imported correctly

---

#### 1.3 Chamber Differentiation
**Priority**: High  
**Description**: Ensure clear separation between chambers

**Acceptance Criteria**:
- All documents tagged with chamber (national_assembly or senate)
- All statements attributed to correct chamber
- All votes tracked by chamber
- All bills tracked by originating chamber
- Chamber filter available in all queries
- No cross-chamber data contamination

**Testing**: Verify chamber separation in 100 random records

---

### 2. Senate Document Scrapers

#### 2.1 Senate Hansard Scraper
**Priority**: High  
**Description**: Scrape and download Senate Hansard documents

**Acceptance Criteria**:
- Discovers all available Senate Hansard documents
- Downloads Senate Hansard PDFs
- Extracts metadata (date, session, title)
- Handles Senate-specific URL patterns
- Prevents duplicate downloads
- Processes daily Senate sittings
- Scraper accuracy ≥98%

**Testing**: Verify all Senate Hansard from sample week downloaded

---

#### 2.2 Senate Votes Scraper
**Priority**: High  
**Description**: Scrape and download Senate Votes & Proceedings

**Acceptance Criteria**:
- Discovers all Senate voting records
- Downloads Senate Votes PDFs
- Extracts vote metadata
- Handles Senate-specific vote formats
- Links votes to bills
- Scraper accuracy ≥98%

**Testing**: Verify all Senate votes from sample month downloaded

---

#### 2.3 Senate Bills Scraper
**Priority**: High  
**Description**: Scrape and download Senate bills

**Acceptance Criteria**:
- Discovers all Senate-originated bills
- Downloads Senate bill PDFs
- Tracks bills received from National Assembly
- Handles bill version tracking
- Identifies bicameral bills
- Scraper accuracy ≥98%

**Testing**: Verify all Senate bills from sample session downloaded

---

#### 2.4 Senate Questions Scraper
**Priority**: High  
**Description**: Scrape and download Senate questions

**Acceptance Criteria**:
- Discovers all Senate questions
- Downloads Senate question PDFs
- Handles oral and written questions
- Extracts question metadata
- Scraper accuracy ≥98%

**Testing**: Verify all Senate questions from sample week downloaded

---

#### 2.5 Senate Petitions Scraper
**Priority**: High  
**Description**: Scrape and download Senate petitions

**Acceptance Criteria**:
- Discovers all Senate petitions
- Downloads Senate petition PDFs
- Extracts petition metadata
- Tracks petition sponsors
- Scraper accuracy ≥98%

**Testing**: Verify all Senate petitions from sample month downloaded

---

### 3. Senate Document Processing

#### 3.1 Senate Hansard Processing
**Priority**: High  
**Description**: Process Senate Hansard documents

**Acceptance Criteria**:
- Extracts text from Senate Hansard PDFs
- Segments text into Senator statements
- Identifies Senators correctly (≥95% accuracy)
- Preserves page and line numbers
- Handles Senate-specific formatting
- Processing time <10 minutes per document

**Testing**: Process 20 Senate Hansard documents

---

#### 3.2 Senate Statement Analysis
**Priority**: High  
**Description**: Analyze Senate statements with same pipeline as National Assembly

**Acceptance Criteria**:
- Classifies statements (filler vs substantive)
- Analyzes sentiment (support/oppose/neutral)
- Computes quality scores (0-100)
- Classifies topics
- Generates citations
- Verifies citations (100% verification rate)
- Analysis accuracy matches National Assembly (≥85%)

**Testing**: Analyze 100 Senate statements, compare with manual review

---

#### 3.3 Senate Vote Processing
**Priority**: High  
**Description**: Process Senate voting records

**Acceptance Criteria**:
- Extracts individual Senator votes
- Links votes to bills
- Tracks vote outcomes
- Handles Senate-specific vote types
- Processing accuracy ≥98%

**Testing**: Process 30 Senate votes

---

#### 3.4 Senate Bill Processing
**Priority**: High  
**Description**: Process Senate bills

**Acceptance Criteria**:
- Extracts bill text and metadata
- Tracks bill versions
- Identifies bill sponsors
- Generates bill summaries
- Links bills to statements and votes
- Processing accuracy ≥95%

**Testing**: Process 20 Senate bills

---

#### 3.5 Senate Question Processing
**Priority**: High  
**Description**: Process Senate questions

**Acceptance Criteria**:
- Extracts question-answer pairs
- Identifies asking Senator
- Identifies responding official
- Categorizes by topic and ministry
- Processing accuracy ≥95%

**Testing**: Process 50 Senate questions

---

#### 3.6 Senate Petition Processing
**Priority**: High  
**Description**: Process Senate petitions

**Acceptance Criteria**:
- Extracts petition text and metadata
- Identifies sponsor Senator
- Tracks petition status
- Categorizes by topic
- Processing accuracy ≥95%

**Testing**: Process 20 Senate petitions

---

### 4. Bicameral Bill Tracking

#### 4.1 Cross-Chamber Bill Identification
**Priority**: High  
**Description**: Identify bills that move between chambers

**Acceptance Criteria**:
- Detects when National Assembly bill sent to Senate
- Detects when Senate bill sent to National Assembly
- Links same bill across chambers
- Tracks bill status in each chamber
- Identification accuracy ≥95%

**Testing**: Verify tracking for 20 bicameral bills

---

#### 4.2 Bicameral Bill Timeline
**Priority**: High  
**Description**: Generate complete timeline for bicameral bills

**Acceptance Criteria**:
- Shows bill introduction in originating chamber
- Shows passage in originating chamber
- Shows transmission to other chamber
- Shows committee review in second chamber
- Shows passage/rejection in second chamber
- Shows presidential assent (if applicable)
- Timeline accuracy ≥98%

**Testing**: Verify timelines for 15 bicameral bills

---

#### 4.3 Bill Version Comparison Across Chambers
**Priority**: Medium  
**Description**: Compare bill versions between chambers

**Acceptance Criteria**:
- Identifies amendments made by second chamber
- Highlights differences between versions
- Tracks reconciliation process
- Shows final agreed version
- Comparison accuracy ≥90%

**Testing**: Compare versions for 10 amended bills

---

#### 4.4 Bicameral Vote Correlation
**Priority**: Medium  
**Description**: Correlate votes on same bill across chambers

**Acceptance Criteria**:
- Links votes on same bill in both chambers
- Compares voting patterns
- Identifies party alignment across chambers
- Shows vote outcome differences
- Correlation accuracy ≥95%

**Testing**: Verify correlation for 20 bills voted in both chambers

---

### 5. Joint Committee Tracking

#### 5.1 Joint Committee Identification
**Priority**: Medium  
**Description**: Identify and track joint committees

**Acceptance Criteria**:
- Identifies all joint committees
- Tracks committee membership (MPs and Senators)
- Stores committee mandates
- Tracks committee meetings
- Identification accuracy ≥98%

**Testing**: Verify all joint committees identified

---

#### 5.2 Joint Committee Activity Tracking
**Priority**: Medium  
**Description**: Track joint committee activities

**Acceptance Criteria**:
- Tracks bills referred to joint committees
- Tracks committee reports
- Links committee activities to bills
- Tracks committee recommendations
- Activity tracking accuracy ≥90%

**Testing**: Verify tracking for 10 joint committee activities

---

### 6. Senator Profiles

#### 6.1 Senator Profile Generation
**Priority**: High  
**Description**: Generate comprehensive Senator profiles

**Acceptance Criteria**:
- Profile includes: name, party, county, category, photo, contact
- Profile includes: total statements, substantive statements, quality score
- Profile includes: topics discussed (with counts)
- Profile includes: voting record (total votes, party alignment %)
- Profile includes: bills sponsored
- Profile includes: questions asked
- Profile includes: petitions sponsored
- Profile includes: committee memberships
- Profile includes: recent activity
- Profiles generated as static HTML

**Testing**: Verify profiles for all 67 Senators

---

#### 6.2 County Representation Tracking
**Priority**: High  
**Description**: Track how Senators represent their counties

**Acceptance Criteria**:
- Links Senators to counties
- Tracks county-specific statements
- Tracks county-specific questions
- Tracks county-specific petitions
- Generates county representation scores
- Tracking accuracy ≥90%

**Testing**: Verify county tracking for 20 Senators

---

#### 6.3 Devolution Oversight Tracking
**Priority**: Medium  
**Description**: Track Senate's devolution oversight role

**Acceptance Criteria**:
- Identifies devolution-related statements
- Tracks county government oversight activities
- Links to Auditor General reports on counties
- Categorizes devolution topics
- Tracking accuracy ≥85%

**Testing**: Verify devolution tracking for 30 statements

---

### 7. Cross-Chamber Analysis

#### 7.1 Chamber Comparison Dashboard
**Priority**: Medium  
**Description**: Generate dashboard comparing chambers

**Acceptance Criteria**:
- Shows activity levels (statements, votes, bills) by chamber
- Shows topic distribution by chamber
- Shows party representation by chamber
- Shows bill passage rates by chamber
- Updates automatically
- Dashboard accuracy ≥95%

**Testing**: Verify dashboard metrics

---

#### 7.2 Party Position Analysis Across Chambers
**Priority**: Medium  
**Description**: Analyze party positions in both chambers

**Acceptance Criteria**:
- Tracks party voting patterns in each chamber
- Compares party positions across chambers
- Identifies party alignment/divergence
- Generates party position reports
- Analysis accuracy ≥85%

**Testing**: Verify analysis for 5 major parties

---

#### 7.3 Legislative Efficiency Metrics
**Priority**: Low  
**Description**: Calculate legislative efficiency metrics

**Acceptance Criteria**:
- Calculates bill passage time by chamber
- Calculates amendment rates by chamber
- Calculates rejection rates by chamber
- Compares efficiency across chambers
- Metrics accuracy ≥90%

**Testing**: Verify metrics for one parliamentary session

---

### 8. Site Generation Enhancements

#### 8.1 Senate Homepage
**Priority**: High  
**Description**: Generate Senate-specific homepage

**Acceptance Criteria**:
- Shows recent Senate activity
- Shows active Senate bills
- Shows recent Senate votes
- Shows Senator of the week/month
- Links to Senator directory
- Updates automatically

**Testing**: Verify homepage generation

---

#### 8.2 Senator Directory
**Priority**: High  
**Description**: Generate Senator directory page

**Acceptance Criteria**:
- Lists all Senators
- Supports filtering by: party, county, category
- Supports sorting by: name, activity, quality score
- Links to individual Senator profiles
- Includes search functionality

**Testing**: Verify directory with all Senators

---

#### 8.3 Senate Session Pages
**Priority**: High  
**Description**: Generate pages for Senate sessions

**Acceptance Criteria**:
- Session summary page
- Full Hansard text
- Vote results
- Bills discussed
- Attendance statistics
- Links to related documents

**Testing**: Verify pages for 20 Senate sessions

---

#### 8.4 Bicameral Bill Pages
**Priority**: High  
**Description**: Generate pages for bicameral bills

**Acceptance Criteria**:
- Shows bill status in both chambers
- Shows complete timeline
- Shows votes in both chambers
- Shows amendments by chamber
- Links to debates in both chambers
- Shows final outcome

**Testing**: Verify pages for 15 bicameral bills

---

#### 8.5 County Representation Pages
**Priority**: Medium  
**Description**: Generate pages showing county representation

**Acceptance Criteria**:
- Page for each county
- Shows county Senators
- Shows county-specific activity
- Shows devolution oversight
- Links to related documents

**Testing**: Verify pages for all 47 counties

---

#### 8.6 Joint Committee Pages
**Priority**: Medium  
**Description**: Generate pages for joint committees

**Acceptance Criteria**:
- Page for each joint committee
- Shows committee membership
- Shows committee activities
- Shows bills under review
- Shows committee reports

**Testing**: Verify pages for all joint committees

---

### 9. Performance and Scalability

#### 9.1 Processing Performance
**Priority**: High  
**Description**: Maintain acceptable processing times with doubled volume

**Acceptance Criteria**:
- Senate Hansard processing: <10 minutes per document
- Senate vote processing: <2 minutes per document
- Senate bill processing: <5 minutes per bill
- Senate question processing: <2 minutes per list
- Senate petition processing: <3 minutes per petition
- Full site generation: <30 minutes (both chambers)
- Parallel processing supported (4+ workers)

**Testing**: Benchmark processing times

---

#### 9.2 Resource Management
**Priority**: High  
**Description**: Manage increased resource usage

**Acceptance Criteria**:
- Memory usage <8GB during processing
- Disk usage <50GB for all data
- Database size <5GB
- Vector database size <3GB
- Efficient caching reduces redundant processing

**Testing**: Monitor resource usage during full processing

---

#### 9.3 Cost Management
**Priority**: High  
**Description**: Keep costs within budget despite doubled volume

**Acceptance Criteria**:
- Monthly LLM costs ≤$50
- Caching reduces LLM calls by ≥50%
- Batch processing optimizes API usage
- Cost tracking by chamber
- Budget alerts configured

**Testing**: Monitor costs for one month

---

### 10. Data Quality and Validation

#### 10.1 Senate Data Completeness
**Priority**: High  
**Description**: Ensure all Senate documents processed

**Acceptance Criteria**:
- No missing Senate Hansard from source
- No missing Senate votes from source
- No missing Senate bills from source
- No missing Senate questions from source
- No missing Senate petitions from source
- Completeness ≥98%

**Testing**: Compare database counts with source

---

#### 10.2 Cross-Chamber Data Consistency
**Priority**: High  
**Description**: Ensure consistency across chambers

**Acceptance Criteria**:
- Bicameral bills correctly linked
- Joint committee data consistent
- Party data consistent across chambers
- No duplicate records across chambers
- Consistency checks pass ≥99%

**Testing**: Run consistency validation suite

---

#### 10.3 Senator Attribution Accuracy
**Priority**: High  
**Description**: Validate Senator identification accuracy

**Acceptance Criteria**:
- Senator identification accuracy ≥95%
- No MP-Senator confusion
- County attribution accuracy ≥98%
- Party attribution accuracy ≥98%

**Testing**: Manual validation of 100 random statements

---

### 11. Testing and Quality Assurance

#### 11.1 Unit Test Coverage
**Priority**: High  
**Description**: Maintain high test coverage for Phase 3 code

**Acceptance Criteria**:
- Overall test coverage ≥90%
- All Senate-specific modules have tests
- All bicameral tracking modules have tests
- Property-based tests for key functions

**Testing**: Run coverage reports

---

#### 11.2 Integration Testing
**Priority**: High  
**Description**: Test Senate integration with existing system

**Acceptance Criteria**:
- Senate processing pipeline tested end-to-end
- Bicameral tracking tested end-to-end
- Cross-chamber analysis tested
- Site generation tested with both chambers
- No regression in National Assembly functionality

**Testing**: Run integration test suite

---

#### 11.3 Comparative Testing
**Priority**: Medium  
**Description**: Compare Senate and National Assembly processing

**Acceptance Criteria**:
- Processing accuracy comparable across chambers
- Analysis quality comparable across chambers
- Performance comparable across chambers
- No systematic bias toward either chamber

**Testing**: Compare metrics for both chambers

---

### 12. Documentation

#### 12.1 Technical Documentation
**Priority**: Medium  
**Description**: Document Phase 3 implementation

**Acceptance Criteria**:
- Senate data model documented
- Bicameral tracking documented
- Cross-chamber analysis documented
- API updates documented

**Testing**: Documentation review

---

#### 12.2 User Documentation
**Priority**: Medium  
**Description**: Document user-facing Senate features

**Acceptance Criteria**:
- Senator profile guide
- Bicameral bill tracking guide
- County representation guide
- Cross-chamber comparison guide

**Testing**: User documentation review

---

## Summary

**Total Requirements**: 60 requirements across 12 categories

**Key Metrics**:
- Senate document processing: Same performance as National Assembly
- Senator identification accuracy: ≥95%
- Bicameral bill tracking accuracy: ≥95%
- Cross-chamber data consistency: ≥99%
- Test coverage: ≥90%
- Monthly cost: ≤$50

**Dependencies**:
- Phase 0 (Foundation) must be complete
- Phase 1 (Core Analysis) must be complete
- Phase 2 (Extended Documents) must be complete
- All National Assembly functionality operational
- Sufficient infrastructure capacity for doubled volume

**Key Challenges**:
- Doubled data volume requires efficient processing
- Bicameral bill tracking adds complexity
- County representation tracking is Senate-specific
- Cross-chamber analysis requires careful data modeling
- Cost management with doubled LLM usage

**Success Criteria**:
- All 67 Senators have complete profiles
- All Senate documents processed with same quality as National Assembly
- Bicameral bills tracked accurately across chambers
- Cross-chamber analysis provides valuable insights
- System performance remains acceptable with doubled volume
- Costs stay within $50/month budget

**Next Steps**:
1. Review and approve requirements
2. Create design document
3. Create implementation tasks
4. Begin development

