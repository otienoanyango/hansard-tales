# Phase 4: Trackers and Reports - Requirements

## Introduction

This document specifies requirements for Phase 4 of the Hansard Tales system. Phase 4 adds tracker documents (Statements, Motions, Bills trackers), Legislative Proposals, Auditor General Reports, and Order Papers for both chambers.

**Phase 4 Goals**:
- Process all tracker documents (Statements, Motions, Bills trackers)
- Process Legislative Proposals
- Process and analyze Auditor General Reports
- Parse Order Papers (parliamentary agenda)
- Track constituency representation
- Enable comprehensive accountability tracking
- Complete document type coverage

**Builds On**:
- Phase 0: Foundation infrastructure
- Phase 1: Core analysis pipeline
- Phase 2: Extended documents (Bills, Questions, Petitions)
- Phase 3: Senate integration and bicameral tracking

**Timeline**: 4 weeks (Weeks 15-18)
**Budget**: ≤$60/month
**Test Coverage**: ≥90%

---

## 1. Statements Tracker Processing

### 1.1 Document Collection

**1.1.1** The system SHALL scrape Statements Tracker documents from both chambers
- National Assembly: `parliament.go.ke/the-national-assembly/house-business/statements`
- Senate: `parliament.go.ke/the-senate/house-business/statements`

**1.1.2** The system SHALL download Statements Tracker PDFs with metadata extraction

**1.1.3** The system SHALL prevent duplicate downloads using content hashing

**1.1.4** The system SHALL extract metadata: date, chamber, session number

### 1.2 Data Extraction

**1.2.1** The system SHALL extract all statement requests from tracker documents

**1.2.2** The system SHALL extract: MP/Senator name, statement topic, request date, response status

**1.2.3** The system SHALL link statement requests to actual statements in Hansard

**1.2.4** The system SHALL track statement fulfillment (requested vs delivered)

**1.2.5** The system SHALL identify constituency-specific statement requests

### 1.3 Analysis

**1.3.1** The system SHALL categorize statement topics using LLM

**1.3.2** The system SHALL track statement request patterns by MP/Senator

**1.3.3** The system SHALL calculate statement fulfillment rate per MP/Senator

**1.3.4** The system SHALL identify most common statement topics

### 1.4 Accuracy Requirements

**1.4.1** Statement extraction accuracy SHALL be ≥95%

**1.4.2** Statement-Hansard linking accuracy SHALL be ≥85%

**1.4.3** Topic categorization accuracy SHALL be ≥80%

---

## 2. Motions Tracker Processing

### 2.1 Document Collection

**2.1.1** The system SHALL scrape Motions Tracker documents from both chambers

**2.1.2** The system SHALL download Motions Tracker PDFs with metadata extraction

**2.1.3** The system SHALL prevent duplicate downloads

### 2.2 Data Extraction

**2.2.1** The system SHALL extract all motions from tracker documents

**2.2.2** The system SHALL extract: motion number, mover name, motion text, status, date

**2.2.3** The system SHALL link motions to votes in Votes & Proceedings

**2.2.4** The system SHALL link motions to debates in Hansard

**2.2.5** The system SHALL track motion outcomes (passed, failed, withdrawn, pending)

### 2.3 Analysis

**2.3.1** The system SHALL categorize motion types (procedural, substantive, urgent)

**2.3.2** The system SHALL track motion success rate by MP/Senator

**2.3.3** The system SHALL identify most active motion movers

**2.3.4** The system SHALL analyze motion topics using LLM

### 2.4 Accuracy Requirements

**2.4.1** Motion extraction accuracy SHALL be ≥95%

**2.4.2** Motion-vote linking accuracy SHALL be ≥90%

**2.4.3** Motion-debate linking accuracy SHALL be ≥85%

---

## 3. Bills Tracker Processing

### 3.1 Document Collection

**3.1.1** The system SHALL scrape Bills Tracker documents from both chambers

**3.1.2** The system SHALL download Bills Tracker PDFs with metadata extraction

**3.1.3** The system SHALL prevent duplicate downloads

### 3.2 Data Extraction

**3.2.1** The system SHALL extract all bill status updates from tracker documents

**3.2.2** The system SHALL extract: bill number, title, sponsor, current stage, last action date

**3.2.3** The system SHALL link tracker entries to full bill documents

**3.2.4** The system SHALL track bill progress through legislative stages

**3.2.5** The system SHALL identify stalled bills (no progress >30 days)

### 3.3 Analysis

**3.3.1** The system SHALL calculate average time per legislative stage

**3.3.2** The system SHALL identify bottlenecks in legislative process

**3.3.3** The system SHALL track bill sponsor success rates

**3.3.4** The system SHALL generate bill progress reports

### 3.4 Accuracy Requirements

**3.4.1** Bill status extraction accuracy SHALL be ≥95%

**3.4.2** Bill-document linking accuracy SHALL be ≥95%

**3.4.3** Stage progression tracking accuracy SHALL be ≥90%

---

## 4. Legislative Proposals Processing

### 4.1 Document Collection

**4.1.1** The system SHALL scrape Legislative Proposals from both chambers

**4.1.2** The system SHALL download proposal PDFs with metadata extraction

**4.1.3** The system SHALL prevent duplicate downloads

### 4.2 Data Extraction

**4.2.1** The system SHALL extract proposal text and metadata

**4.2.2** The system SHALL extract: proposer name, proposal title, submission date, status

**4.2.3** The system SHALL link proposals to resulting bills (if any)

**4.2.4** The system SHALL track proposal outcomes (adopted, rejected, pending)

### 4.3 Analysis

**4.3.1** The system SHALL categorize proposal topics using LLM

**4.3.2** The system SHALL track proposal-to-bill conversion rate

**4.3.3** The system SHALL identify most active proposers

**4.3.4** The system SHALL analyze proposal success factors

### 4.4 Accuracy Requirements

**4.4.1** Proposal extraction accuracy SHALL be ≥95%

**4.4.2** Proposal-bill linking accuracy SHALL be ≥85%

**4.4.3** Topic categorization accuracy SHALL be ≥80%

---

## 5. Auditor General Reports Processing

### 5.1 Document Collection

**5.1.1** The system SHALL scrape Auditor General Reports from parliament website

**5.1.2** The system SHALL download AG report PDFs (typically 100-500 pages)

**5.1.3** The system SHALL prevent duplicate downloads

**5.1.4** The system SHALL handle quarterly and annual reports

### 5.2 Data Extraction

**5.2.1** The system SHALL extract report metadata: title, date, reporting period, entities audited

**5.2.2** The system SHALL extract audit findings and recommendations

**5.2.3** The system SHALL extract financial irregularities and amounts

**5.2.4** The system SHALL extract entity names (ministries, departments, counties)

**5.2.5** The system SHALL preserve table data (financial statements)

### 5.3 Analysis

**5.3.1** The system SHALL categorize findings by severity (high, medium, low)

**5.3.2** The system SHALL link findings to responsible entities

**5.3.3** The system SHALL track recurring issues across reports

**5.3.4** The system SHALL generate entity-specific audit summaries

**5.3.5** The system SHALL identify total financial irregularities per entity

### 5.4 Parliamentary Response Tracking

**5.4.1** The system SHALL link AG reports to parliamentary debates

**5.4.2** The system SHALL track which findings were discussed in parliament

**5.4.3** The system SHALL identify findings with no parliamentary response

**5.4.4** The system SHALL track implementation of recommendations

### 5.5 Accuracy Requirements

**5.5.1** Finding extraction accuracy SHALL be ≥90%

**5.5.2** Financial amount extraction accuracy SHALL be ≥95%

**5.5.3** Entity identification accuracy SHALL be ≥90%

**5.5.4** Severity categorization accuracy SHALL be ≥85%

---

## 6. Order Paper Processing

### 6.1 Document Collection

**6.1.1** The system SHALL scrape Order Papers from both chambers

**6.1.2** The system SHALL download Order Paper PDFs (daily agenda)

**6.1.3** The system SHALL prevent duplicate downloads

### 6.2 Data Extraction

**6.2.1** The system SHALL extract agenda items for each sitting day

**6.2.2** The system SHALL extract: item number, item type, description, time allocation

**6.2.3** The system SHALL extract scheduled bills for reading/debate

**6.2.4** The system SHALL extract scheduled questions

**6.2.5** The system SHALL extract scheduled motions

**6.2.6** The system SHALL extract committee reports scheduled for tabling

### 6.3 Agenda Tracking

**6.3.1** The system SHALL link Order Paper items to actual proceedings in Hansard

**6.3.2** The system SHALL track agenda item completion (scheduled vs executed)

**6.3.3** The system SHALL identify deferred agenda items

**6.3.4** The system SHALL calculate agenda completion rate

### 6.4 Analysis

**6.4.1** The system SHALL identify most frequently deferred items

**6.4.2** The system SHALL track time allocation vs actual time spent

**6.4.3** The system SHALL analyze agenda patterns (what gets prioritized)

### 6.5 Accuracy Requirements

**6.5.1** Agenda item extraction accuracy SHALL be ≥95%

**6.5.2** Item-proceeding linking accuracy SHALL be ≥85%

**6.5.3** Completion tracking accuracy SHALL be ≥90%

---

## 7. Cross-Document Correlation

### 7.1 Tracker Integration

**7.1.1** The system SHALL correlate Statements Tracker with Hansard statements

**7.1.2** The system SHALL correlate Motions Tracker with votes and debates

**7.1.3** The system SHALL correlate Bills Tracker with bill documents and votes

**7.1.4** The system SHALL correlate Order Papers with actual proceedings

### 7.2 Audit Report Integration

**7.2.1** The system SHALL link AG report findings to parliamentary debates

**7.2.2** The system SHALL link AG reports to relevant questions

**7.2.3** The system SHALL link AG reports to oversight motions

**7.2.4** The system SHALL track parliamentary follow-up on audit findings

### 7.3 Proposal Integration

**7.3.1** The system SHALL link Legislative Proposals to resulting bills

**7.3.2** The system SHALL link proposals to parliamentary debates

**7.3.3** The system SHALL track proposal adoption timeline

---

## 8. Enhanced MP/Senator Profiles

### 8.1 Tracker Activity

**8.1.1** The system SHALL add statement request tracking to profiles

**8.1.2** The system SHALL add motion activity to profiles

**8.1.3** The system SHALL add legislative proposal activity to profiles

**8.1.4** The system SHALL calculate fulfillment rates for each activity type

### 8.2 Oversight Activity

**8.2.1** The system SHALL track MP/Senator engagement with AG reports

**8.2.2** The system SHALL identify MPs/Senators active in financial oversight

**8.2.3** The system SHALL track follow-up on audit findings

### 8.3 Constituency Representation

**8.3.1** The system SHALL track constituency-specific statements

**8.3.2** The system SHALL track constituency-specific questions

**8.3.3** The system SHALL track constituency-specific petitions

**8.3.4** The system SHALL generate constituency representation scores

---

## 9. Site Generation

### 9.1 Tracker Pages

**9.1.1** The system SHALL generate Statements Tracker directory pages

**9.1.2** The system SHALL generate Motions Tracker directory pages

**9.1.3** The system SHALL generate Bills Tracker directory pages

**9.1.4** The system SHALL generate individual tracker item pages

### 9.2 Audit Report Pages

**9.2.1** The system SHALL generate AG Reports directory page

**9.2.2** The system SHALL generate individual AG report pages

**9.2.3** The system SHALL generate entity-specific audit pages

**9.2.4** The system SHALL generate finding-specific pages with parliamentary response

### 9.3 Order Paper Pages

**9.3.1** The system SHALL generate Order Paper archive pages

**9.3.2** The system SHALL generate daily agenda pages

**9.3.3** The system SHALL show agenda completion status

### 9.4 Legislative Proposal Pages

**9.4.1** The system SHALL generate proposals directory page

**9.4.2** The system SHALL generate individual proposal pages

**9.4.3** The system SHALL show proposal-to-bill conversion tracking

### 9.5 Accountability Dashboards

**9.5.1** The system SHALL generate financial oversight dashboard

**9.5.2** The system SHALL generate legislative efficiency dashboard

**9.5.3** The system SHALL generate constituency representation dashboard

---

## 10. Performance Requirements

### 10.1 Processing Performance

**10.1.1** Statements Tracker processing SHALL complete in <5 minutes per document

**10.1.2** Motions Tracker processing SHALL complete in <5 minutes per document

**10.1.3** Bills Tracker processing SHALL complete in <3 minutes per document

**10.1.4** Legislative Proposal processing SHALL complete in <10 minutes per document

**10.1.5** AG Report processing SHALL complete in <30 minutes per document

**10.1.6** Order Paper processing SHALL complete in <3 minutes per document

### 10.2 System Performance

**10.2.1** Full site generation SHALL complete in <45 minutes

**10.2.2** Database queries SHALL complete in <100ms

**10.2.3** Memory usage SHALL remain <10GB during processing

**10.2.4** Disk usage SHALL remain <50GB for all documents

---

## 11. Cost Requirements

### 11.1 Budget Constraints

**11.1.1** Total monthly cost SHALL NOT exceed $60

**11.1.2** LLM API costs SHALL NOT exceed $40/month

**11.1.3** Infrastructure costs SHALL NOT exceed $20/month

### 11.2 Cost Optimization

**11.2.1** The system SHALL cache LLM results for ≥30 days

**11.2.2** The system SHALL achieve ≥50% cache hit rate

**11.2.3** The system SHALL batch LLM calls for efficiency

**11.2.4** The system SHALL use incremental processing to avoid reprocessing

---

## 12. Testing Requirements

### 12.1 Test Coverage

**12.1.1** Overall test coverage SHALL be ≥90%

**12.1.2** New code test coverage SHALL be ≥90%

**12.1.3** Critical paths SHALL have 100% test coverage

### 12.2 Property-Based Testing

**12.2.1** The system SHALL implement property tests for all tracker processors

**12.2.2** The system SHALL implement property tests for AG report analysis

**12.2.3** The system SHALL implement property tests for Order Paper parsing

**12.2.4** The system SHALL implement property tests for cross-document correlation

### 12.3 Integration Testing

**12.3.1** The system SHALL test complete tracker processing pipeline

**12.3.2** The system SHALL test AG report processing pipeline

**12.3.3** The system SHALL test Order Paper processing pipeline

**12.3.4** The system SHALL test cross-document correlation

---

## 13. Data Quality Requirements

### 13.1 Extraction Quality

**13.1.1** All tracker data extraction SHALL preserve source references

**13.1.2** All financial amounts SHALL be extracted with ≥95% accuracy

**13.1.3** All entity names SHALL be normalized consistently

**13.1.4** All dates SHALL be extracted in ISO format

### 13.2 Correlation Quality

**13.2.1** Tracker-to-document correlations SHALL be ≥85% accurate

**13.2.2** AG report-to-debate correlations SHALL be ≥80% accurate

**13.2.3** Order Paper-to-proceeding correlations SHALL be ≥90% accurate

### 13.3 Anti-Hallucination

**13.3.1** All LLM-generated categorizations SHALL include confidence scores

**13.3.2** All findings SHALL be traceable to source documents

**13.3.3** All financial amounts SHALL be verified against source

**13.3.4** All entity attributions SHALL be verified

---

## 14. Monitoring Requirements

### 14.1 Processing Metrics

**14.1.1** The system SHALL track documents processed per document type

**14.1.2** The system SHALL track processing time per document type

**14.1.3** The system SHALL track error rate per document type

**14.1.4** The system SHALL track LLM API usage per document type

### 14.2 Quality Metrics

**14.2.1** The system SHALL track extraction accuracy per document type

**14.2.2** The system SHALL track correlation accuracy

**14.2.3** The system SHALL track cache hit rates

**14.2.4** The system SHALL track cost per document type

### 14.3 Alerting

**14.3.1** The system SHALL alert on processing failures

**14.3.2** The system SHALL alert on budget threshold exceeded (>90%)

**14.3.3** The system SHALL alert on accuracy degradation

---

## 15. Documentation Requirements

### 15.1 User Documentation

**15.1.1** The system SHALL document all new document types

**15.1.2** The system SHALL provide examples for each tracker type

**15.1.3** The system SHALL document AG report analysis methodology

**15.1.4** The system SHALL document correlation algorithms

### 15.2 API Documentation

**15.2.1** The system SHALL document all new data models

**15.2.2** The system SHALL document all new processors

**15.2.3** The system SHALL document all new correlation methods

### 15.3 Operational Documentation

**15.3.1** The system SHALL document processing schedules

**15.3.2** The system SHALL document troubleshooting procedures

**15.3.3** The system SHALL document cost optimization strategies

---

## Summary

### Requirements by Category

| Category | Count | Priority |
|----------|-------|----------|
| Statements Tracker | 14 | P0 |
| Motions Tracker | 14 | P0 |
| Bills Tracker | 14 | P0 |
| Legislative Proposals | 12 | P1 |
| Auditor General Reports | 19 | P1 |
| Order Papers | 15 | P1 |
| Cross-Document Correlation | 10 | P0 |
| Enhanced Profiles | 11 | P0 |
| Site Generation | 14 | P0 |
| Performance | 10 | P0 |
| Cost | 8 | P0 |
| Testing | 12 | P0 |
| Data Quality | 13 | P0 |
| Monitoring | 11 | P1 |
| Documentation | 9 | P1 |

**Total Requirements**: 176

### Key Metrics

- **Extraction Accuracy**: ≥95% for all document types
- **Correlation Accuracy**: ≥85% for all correlation types
- **Processing Time**: <30 min per AG report, <5 min for trackers
- **Budget**: ≤$60/month
- **Test Coverage**: ≥90%

### Document Types Added

Phase 4 adds 6 new document types per chamber (12 total):
1. Statements Tracker
2. Motions Tracker
3. Bills Tracker
4. Legislative Proposals
5. Auditor General Reports
6. Order Papers

**Total System Coverage**: 22 document types (11 per chamber)

### Success Criteria

Phase 4 is successful when:
- ✓ All 6 document types processed for both chambers
- ✓ All tracker-to-document correlations working
- ✓ AG report analysis operational
- ✓ Order Paper tracking functional
- ✓ Enhanced profiles include all tracker data
- ✓ All accuracy requirements met
- ✓ Budget compliance verified
- ✓ Test coverage ≥90%
- ✓ Documentation complete

