# Phase 2: Extended Documents - Startup Guide

## Current Status

**Phase 1 Completion**: ✅ 95% Complete
- 719/784 unit tests passing (91.7%)
- CostManager fully implemented with budget enforcement
- All core analysis modules operational
- Statement segmentation, NLP, citation verification working

**Commit Status**: Latest is test fixes and Phase 1 completion summary

---

## Phase 2 Overview

Phase 2 extends Hansard Tales to process Bills, Questions, and Petitions beyond core Hansard debates.

**Timeline**: 4 weeks
**Budget**: $30/month
**Test Coverage Target**: ≥90%
**Key Deliverables**:
- Bill processing pipeline (scraper, text extraction, versioning)
- Question processing (discovery, Q&A pairing, categorization)
- Petition processing (discovery, text extraction)
- Cross-document correlation (bills to statements/votes/questions)
- Enhanced MP profiles with legislative activity
- Legislative activity dashboard

---

## Week 1 Plan: Bill Processing Infrastructure

### Task Priority Order (Recommended)

1. **Task 1: Database Schema** (High Priority - Blocking)
   - Time: 2-3 hours
   - Impact: Required for all document storage
   - Files to create:
     - `alembic/versions/xx_add_bills_questions_petitions.py`
     - Migration tests

2. **Task 2: Bill Scraper** (High Priority)
   - Time: 4-5 hours
   - Impact: Core bill discovery
   - Files to create:
     - `hansard_tales/scrapers/bills.py`
     - `tests/unit/test_bill_scraper.py`

3. **Task 3: Bill Text Extraction** (High Priority)
   - Time: 5-6 hours
   - Impact: Extract structured data from bill PDFs
   - Files to create:
     - `hansard_tales/processors/bill_processor.py`
     - `tests/unit/test_bill_processor.py`

4. **Task 4: Bill Version Tracking** (Medium Priority)
   - Time: 3-4 hours
   - Impact: Track bill amendments and changes
   - Files to create:
     - `hansard_tales/analysis/bill_version_tracker.py`
     - `tests/unit/test_bill_version_tracker.py`

---

## Implementation Checklist

### Week 1: Bill Processing Infrastructure
- [ ] Task 1: Database Schema (Phase 1 models already exist - just add migration)
- [ ] Task 2: Bill Scraper (20 tests)
- [ ] Task 3: Bill Text Extraction (25 tests)
- [ ] Task 4: Bill Version Tracking (15 tests)
- **Target**: 60 tests passing, ≥90% coverage on new modules

### Week 2: Bill Analysis & Questions
- [ ] Task 5: Bill Summarization (20 tests)
- [ ] Task 6: Question Scraper (18 tests)
- [ ] Task 7: Q&A Pairing (20 tests)
- [ ] Task 8: Question Categorization (15 tests)

### Week 3: Petitions & Correlation
- [ ] Task 9: Petition Processing (18 tests)
- [ ] Task 10-14: Correlation engines (Bills-Statements, Bills-Votes, Questions-Statements, Bill Lifecycle, MP Activity)

### Week 4: Site Generation & Integration
- [ ] Task 15: Enhanced MP Profiles
- [ ] Task 16-17: Bill, Question, Petition pages
- [ ] Task 18: Legislative Dashboard
- [ ] Task 19: Integration & E2E tests
- [ ] Task 20: Documentation

---

## Key Database Models (Already Exist from Phase 1)

```python
# From hansard_tales/database/models.py:
- BillORM           # Bills table
- BillVersionORM    # Bill versions
- VoteORM           # Votes (linked to bills)
- QuestionORM       # Parliamentary questions
- PetitionORM       # Petitions
- StatementORM      # Hansard statements (from Phase 1)
- MPORM             # MPs (from Phase 1)
```

---

## Integration Points with Phase 1

1. **LLM Analyzer**: Use for bill summarization, question categorization
2. **Citation Verifier**: Verify bill citations in statements
3. **Bill Statement Linker**: Already enhanced in Phase 1
4. **Cost Manager**: Track API calls for Phase 2 tasks
5. **Vector DB**: Store bill embeddings for similarity search

---

## Development Strategy

### Database-First Approach
1. Start with migration scripts
2. Verify schema with migration tests
3. Implement scrapers to populate data
4. Build processors/analyzers on top

### Testing Strategy
- Unit tests for each scraper/processor (mock data)
- Integration tests with actual parliament.go.ke (limited calls)
- Property-based tests for data consistency
- Cost tracking for all LLM calls

### Cost Management
- Bill summarization: ~$0.01-0.05 per bill (Haiku)
- Question categorization: ~$0.005 per question
- Estimated Phase 2 usage: $20-30/month within budget

---

## First Steps

1. **Review database models** to understand existing schema
2. **Create migration script** for any missing tables
3. **Write migration tests** to verify schema integrity
4. **Start Task 2: Bill Scraper** with 2-3 unit tests
5. **Commit incrementally** after each sub-task

---

## Useful Commands

```bash
# Run Phase 1 tests to ensure no regression
pytest tests/unit/ -v --tb=short

# Run specific Phase 2 test file
pytest tests/unit/test_bill_scraper.py -v

# Run with coverage
pytest tests/unit/ --cov=hansard_tales.scrapers

# Check current test count
pytest --co -q | grep -c "test"

# Run a specific test
pytest tests/unit/test_bill_scraper.py::TestBillScraper::test_discover_bills -v
```

---

## Success Criteria for Week 1

✅ Database migration complete and tested
✅ Bill scraper discovers bills from parliament.go.ke (mock tests)
✅ Bill text extraction works on sample PDFs
✅ Bill version tracking identifies differences between versions
✅ 60+ tests passing with ≥90% coverage on new modules
✅ No regression in Phase 1 tests (719+ still passing)
✅ Cost tracking shows <$5 usage for Week 1

---

## Questions to Address

1. What's the parliament.go.ke URL structure for bills?
2. Do we need all parliament terms or just current (13)?
3. Should we cache bill PDFs or re-download each run?
4. How many bill versions exist to track?
5. Should bill processing use same CSV import or live scraping?

---

## Resources

- Phase 1 Status: See `PHASE_1_COMPLETION_STATUS.md`
- Test Fixes: See `TEST_FIXES_SUMMARY.md`
- Database Models: `hansard_tales/database/models.py`
- Existing Scrapers (reference): `hansard_tales/scrapers/base.py`
- Parliament.go.ke: https://parliament.go.ke/

---

**Ready to start Week 1?** Let's begin with Task 1 (Database Schema).
