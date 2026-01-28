# Phase 3: Senate Integration - Implementation Tasks

## Overview

Phase 3 extends all Phase 1 and Phase 2 functionality to the Senate chamber, enabling comprehensive bicameral parliamentary tracking.

**Timeline**: 4 weeks | **Test Coverage**: ≥90% | **Budget**: ≤$50/month
**Dependencies**: Phase 0, 1, and 2 must be complete

---

## Tasks

### Week 1: Database Schema and Component Refactoring

- [ ] 1. Database Schema Extensions
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
    - [ ] 1.3.4 Test data migration
  - [ ] 1.4 Write property-based tests
    - [ ] 1.4.1 Property 1.1: Chamber isolation
    - [ ] 1.4.2 Property 1.2: Senator uniqueness

- [ ] 2. Chamber-Agnostic Component Refactoring
  - [ ] 2.1 Refactor Phase 1 components
    - [ ] 2.1.1 Rename MPIdentifier → ParliamentarianIdentifier
    - [ ] 2.1.2 Add chamber parameter to __init__
    - [ ] 2.1.3 Update _load_cache to query MPs or Senators
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
    - [ ] 2.5.1 Property 2.1: Chamber parameter propagation

### Week 2: Senate Document Scrapers

- [ ] 3. Senate Hansard Scraper
  - [ ] 3.1 Implement SenateHansardScraper
    - [ ] 3.1.1 Extend BaseScraper with Senate URLs
    - [ ] 3.1.2 Implement discover_hansards method
    - [ ] 3.1.3 Implement download_hansard method
    - [ ] 3.1.4 Handle Senate-specific metadata
  - [ ] 3.2 Write unit tests
    - [ ] 3.2.1 Test Senate URL discovery
    - [ ] 3.2.2 Test metadata extraction
    - [ ] 3.2.3 Test download functionality
  - [ ] 3.3 Write property-based tests
    - [ ] 3.3.1 Property 3.1: All Senate Hansards discovered

- [ ] 4. Senate Votes Scraper
  - [ ] 4.1 Implement SenateVotesScraper
    - [ ] 4.1.1 Extend BaseScraper with Senate URLs
    - [ ] 4.1.2 Implement discover_votes method
    - [ ] 4.1.3 Implement download_votes method
  - [ ] 4.2 Write unit tests
    - [ ] 4.2.1 Test Senate votes discovery
    - [ ] 4.2.2 Test download functionality
  - [ ] 4.3 Write property-based tests
    - [ ] 4.3.1 Property 4.1: All Senate votes discovered

- [ ] 5. Senate Bills, Questions, Petitions Scrapers
  - [ ] 5.1 Implement Senate scrapers
    - [ ] 5.1.1 Implement SenateBillScraper
    - [ ] 5.1.2 Implement SenateQuestionScraper
    - [ ] 5.1.3 Implement SenatePetitionScraper
  - [ ] 5.2 Write unit tests
    - [ ] 5.2.1 Test bill scraper
    - [ ] 5.2.2 Test question scraper
    - [ ] 5.2.3 Test petition scraper
  - [ ] 5.3 Write property-based tests
    - [ ] 5.3.1 Property 5.1: Document discovery completeness

### Week 3: Bicameral Features

- [ ] 6. Cross-Chamber Bill Tracking
  - [ ] 6.1 Implement CrossChamberBillTracker
    - [ ] 6.1.1 Implement bill matching algorithm
    - [ ] 6.1.2 Implement cross-chamber timeline
    - [ ] 6.1.3 Implement amendment tracking
    - [ ] 6.1.4 Implement mediation tracking
  - [ ] 6.2 Write unit tests
    - [ ] 6.2.1 Test bill matching
    - [ ] 6.2.2 Test timeline generation
    - [ ] 6.2.3 Test amendment tracking
  - [ ] 6.3 Write property-based tests
    - [ ] 6.3.1 Property 6.1: Bill matching accuracy ≥90%

- [ ] 7. Joint Committee Tracking
  - [ ] 7.1 Implement JointCommitteeTracker
    - [ ] 7.1.1 Implement committee identification
    - [ ] 7.1.2 Implement membership tracking
    - [ ] 7.1.3 Implement activity tracking
  - [ ] 7.2 Write unit tests
    - [ ] 7.2.1 Test committee identification
    - [ ] 7.2.2 Test membership tracking
  - [ ] 7.3 Write property-based tests
    - [ ] 7.3.1 Property 7.1: Committee tracking completeness

- [ ] 8. Bicameral Comparison Engine
  - [ ] 8.1 Implement BicameralComparisonEngine
    - [ ] 8.1.1 Implement chamber comparison metrics
    - [ ] 8.1.2 Implement topic comparison
    - [ ] 8.1.3 Implement activity comparison
  - [ ] 8.2 Write unit tests
    - [ ] 8.2.1 Test comparison metrics
    - [ ] 8.2.2 Test topic comparison
  - [ ] 8.3 Write property-based tests
    - [ ] 8.3.1 Property 8.1: Comparison accuracy

### Week 4: Site Generation and Integration

- [ ] 9. Senator Profile Pages
  - [ ] 9.1 Implement SenatorProfileGenerator
    - [ ] 9.1.1 Extend MP profile generator
    - [ ] 9.1.2 Add Senate-specific fields
    - [ ] 9.1.3 Add county representation
  - [ ] 9.2 Create templates
    - [ ] 9.2.1 Create senator list template
    - [ ] 9.2.2 Create senator profile template
  - [ ] 9.3 Write unit tests
    - [ ] 9.3.1 Test profile generation
    - [ ] 9.3.2 Test template rendering
  - [ ] 9.4 Write property-based tests
    - [ ] 9.4.1 Property 9.1: Profile completeness

- [ ] 10. Bicameral Pages
  - [ ] 10.1 Implement BicameralPageGenerator
    - [ ] 10.1.1 Implement cross-chamber bill pages
    - [ ] 10.1.2 Implement joint committee pages
    - [ ] 10.1.3 Implement comparison pages
  - [ ] 10.2 Create templates
    - [ ] 10.2.1 Create bicameral bill template
    - [ ] 10.2.2 Create joint committee template
    - [ ] 10.2.3 Create comparison template
  - [ ] 10.3 Write unit tests
    - [ ] 10.3.1 Test page generation
    - [ ] 10.3.2 Test template rendering
  - [ ] 10.4 Write property-based tests
    - [ ] 10.4.1 Property 10.1: Page generation completeness

- [ ] 11. Integration and End-to-End Testing
  - [ ] 11.1 Integration tests
    - [ ] 11.1.1 Test Senate document processing
    - [ ] 11.1.2 Test cross-chamber correlation
    - [ ] 11.1.3 Test bicameral features
  - [ ] 11.2 End-to-end tests
    - [ ] 11.2.1 Process complete Senate dataset
    - [ ] 11.2.2 Generate all correlations
    - [ ] 11.2.3 Generate complete site
  - [ ] 11.3 Performance testing
    - [ ] 11.3.1 Benchmark Senate processing
    - [ ] 11.3.2 Benchmark bicameral features
  - [ ] 11.4 Cost monitoring
    - [ ] 11.4.1 Track LLM costs
    - [ ] 11.4.2 Verify budget compliance

- [ ] 12. Configuration and Documentation
  - [ ] 12.1 Configuration
    - [ ] 12.1.1 Create phase3.yaml config file
    - [ ] 12.1.2 Document configuration options
  - [ ] 12.2 Documentation
    - [ ] 12.2.1 Write setup instructions
    - [ ] 12.2.2 Write usage guide
    - [ ] 12.2.3 Document bicameral features
  - [ ] 12.3 Code documentation
    - [ ] 12.3.1 Add docstrings to all classes
    - [ ] 12.3.2 Add docstrings to all functions

---

## Summary

**Total Tasks**: 12 major tasks
**Timeline**: 4 weeks
**Test Coverage Target**: ≥90%
**Budget**: ≤$50/month

**Dependencies**:
- Phase 0, 1, and 2 must be complete
- Tasks 1-2 must complete before Tasks 3-5
- Tasks 3-5 must complete before Tasks 6-8
- Tasks 6-8 must complete before Tasks 9-10
- Tasks 11-12 are final integration and documentation

