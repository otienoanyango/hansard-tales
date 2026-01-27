# Phase 4: Trackers and Reports - Design

## Introduction

This document provides detailed component designs for Phase 4 of the Hansard Tales system. Phase 4 adds tracker documents (Statements, Motions, Bills trackers), Legislative Proposals, Auditor General Reports, and Order Papers for both chambers, completing the document type coverage.

**Design Principles**:
- **Reuse Processing Infrastructure**: Leverage Phase 0-3 components for scraping and processing
- **Structured Data Extraction**: Focus on tabular data extraction from tracker documents
- **Financial Accountability**: Enable comprehensive audit tracking and parliamentary oversight
- **Legislative Efficiency**: Track agenda execution and legislative progress
- **Cost Management**: Stay within $60/month budget through efficient processing
- **Performance**: Maintain acceptable processing times despite increased document volume

**Phase 4 Goals**:
- Process all tracker documents (Statements, Motions, Bills trackers)
- Process Legislative Proposals with bill conversion tracking
- Process and analyze Auditor General Reports
- Parse Order Papers and track agenda execution
- Enable comprehensive accountability tracking
- Complete document type coverage (22 types total)

## System Architecture

### Phase 4 Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              Existing Processing Infrastructure                  │
│  (Reused from Phase 0-3)                                        │
│                                                                  │
│  PDF Processor → Text Extractor → Entity Recognizer            │
│  → Embedding Generator → LLM Analyzer → Citation Verifier      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Tracker Document Processors                     │
│                                                                  │
│  Statements Tracker → Motions Tracker → Bills Tracker          │
│  → Legislative Proposals → Order Papers                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Auditor General Report Analyzer                     │
│                                                                  │
│  Finding Extractor → Entity Identifier → Severity Classifier   │
│  → Financial Amount Extractor → Recommendation Tracker         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Enhanced Correlation Engine                         │
│                                                                  │
│  Tracker-Document Linker → AG Report-Debate Linker             │
│  → Order Paper-Proceeding Linker → Proposal-Bill Linker        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Accountability Analytics                            │
│                                                                  │
│  Constituency Representation → Financial Oversight              │
│  → Legislative Efficiency → Agenda Execution                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Enhanced Site Generation                            │
│                                                                  │
│  Tracker Pages → AG Report Pages → Order Paper Pages           │
│  → Accountability Dashboards → Enhanced Profiles                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Design 1: Database Schema Extensions for Trackers

### Component Design

**Purpose**: Extend database schema to support tracker documents and audit reports

**Technology**: SQLAlchemy + Alembic migrations

**Builds On**: Phase 0-3 database schema

### Schema Changes

**1. Statements Tracker Table**:
```python
class StatementRequestORM(Base):
    """Statement requests from Statements Tracker"""
    __tablename__ = "statement_requests"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    chamber = Column(SQLEnum(ChamberEnum), nullable=False)
    requester_id = Column(PGUUID(as_uuid=True), nullable=False)  # MP or Senator
    requester_type = Column(String(20), nullable=False)  # 'mp' or 'senator'
    
    # Request details
    topic = Column(Text, nullable=False)
    request_date = Column(Date, nullable=False)
    session_id = Column(String(50))
    
    # Fulfillment tracking
    fulfilled = Column(Boolean, default=False)
    fulfillment_date = Column(Date)
    hansard_statement_id = Column(PGUUID(as_uuid=True), ForeignKey('statements.id'))
    
    # Categorization
    topics = Column(JSON, default=[])
    is_constituency_specific = Column(Boolean, default=False)
    constituency = Column(String(100))
    
    # Source tracking
    source_url = Column(String(500), nullable=False)
    source_hash = Column(String(64), nullable=False)
    source_page = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Relationships
    hansard_statement = relationship("StatementORM", backref="statement_request")
    
    # Indexes
    __table_args__ = (
        Index('idx_statement_requests_chamber', 'chamber'),
        Index('idx_statement_requests_requester', 'requester_id'),
        Index('idx_statement_requests_date', 'request_date'),
        Index('idx_statement_requests_fulfilled', 'fulfilled'),
    )
```

**2. Motions Tracker Table**:
```python
class MotionTrackerORM(Base):
    """Motions from Motions Tracker"""
    __tablename__ = "motion_tracker"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    chamber = Column(SQLEnum(ChamberEnum), nullable=False)
    
    # Motion details
    motion_number = Column(String(50), nullable=False)
    mover_id = Column(PGUUID(as_uuid=True), nullable=False)
    mover_type = Column(String(20), nullable=False)
    motion_text = Column(Text, nullable=False)
    motion_date = Column(Date, nullable=False)
    
    # Status tracking
    status = Column(String(50), nullable=False)  # pending, passed, failed, withdrawn
    last_action_date = Column(Date)
    
    # Correlation
    vote_id = Column(PGUUID(as_uuid=True), ForeignKey('votes.id'))
    related_hansard_ids = Column(JSON, default=[])  # List of statement IDs
    
    # Categorization
    motion_type = Column(String(50))  # procedural, substantive, urgent
    topics = Column(JSON, default=[])
    
    # Source tracking
    source_url = Column(String(500), nullable=False)
    source_hash = Column(String(64), nullable=False)
    source_page = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Relationships
    vote = relationship("VoteORM", backref="motion")
    
    # Indexes
    __table_args__ = (
        Index('idx_motion_tracker_chamber', 'chamber'),
        Index('idx_motion_tracker_mover', 'mover_id'),
        Index('idx_motion_tracker_status', 'status'),
        Index('idx_motion_tracker_date', 'motion_date'),
        UniqueConstraint('motion_number', 'chamber', name='uq_motion_number_chamber'),
    )
```

**3. Bills Tracker Table**:
```python
class BillTrackerEntryORM(Base):
    """Bill status entries from Bills Tracker"""
    __tablename__ = "bill_tracker_entries"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bill_id = Column(PGUUID(as_uuid=True), ForeignKey('bills.id'), nullable=False)
    chamber = Column(SQLEnum(ChamberEnum), nullable=False)
    
    # Status snapshot
    status = Column(String(100), nullable=False)
    stage = Column(String(100))
    last_action_date = Column(Date, nullable=False)
    tracker_date = Column(Date, nullable=False)  # Date of tracker document
    
    # Progress tracking
    days_at_stage = Column(Integer)
    is_stalled = Column(Boolean, default=False)  # No progress >30 days
    
    # Source tracking
    source_url = Column(String(500), nullable=False)
    source_hash = Column(String(64), nullable=False)
    source_page = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    
    # Relationships
    bill = relationship("BillORM", backref="tracker_entries")
    
    # Indexes
    __table_args__ = (
        Index('idx_bill_tracker_bill_id', 'bill_id'),
        Index('idx_bill_tracker_chamber', 'chamber'),
        Index('idx_bill_tracker_date', 'tracker_date'),
        Index('idx_bill_tracker_stalled', 'is_stalled'),
    )
```


**4. Legislative Proposals Table**:
```python
class LegislativeProposalORM(Base):
    """Legislative proposals"""
    __tablename__ = "legislative_proposals"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    chamber = Column(SQLEnum(ChamberEnum), nullable=False)
    
    # Proposal details
    proposal_number = Column(String(50))
    title = Column(String(500), nullable=False)
    proposer_id = Column(PGUUID(as_uuid=True), nullable=False)
    proposer_type = Column(String(20), nullable=False)
    submission_date = Column(Date, nullable=False)
    
    # Content
    proposal_text = Column(Text, nullable=False)
    rationale = Column(Text)
    
    # Status tracking
    status = Column(String(50), nullable=False)  # submitted, under_review, adopted, rejected
    review_committee = Column(String(200))
    
    # Bill conversion tracking
    resulted_in_bill = Column(Boolean, default=False)
    bill_id = Column(PGUUID(as_uuid=True), ForeignKey('bills.id'))
    conversion_date = Column(Date)
    
    # Categorization
    topics = Column(JSON, default=[])
    
    # Source tracking
    source_url = Column(String(500), nullable=False)
    source_hash = Column(String(64), nullable=False)
    vector_doc_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Relationships
    bill = relationship("BillORM", backref="originating_proposal")
    
    # Indexes
    __table_args__ = (
        Index('idx_proposals_chamber', 'chamber'),
        Index('idx_proposals_proposer', 'proposer_id'),
        Index('idx_proposals_status', 'status'),
        Index('idx_proposals_resulted_in_bill', 'resulted_in_bill'),
    )
```

**5. Auditor General Reports Table**:
```python
class AuditorGeneralReportORM(Base):
    """Auditor General reports"""
    __tablename__ = "auditor_general_reports"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Report details
    title = Column(String(500), nullable=False)
    report_type = Column(String(100))  # quarterly, annual, special
    reporting_period_start = Column(Date, nullable=False)
    reporting_period_end = Column(Date, nullable=False)
    publication_date = Column(Date, nullable=False)
    
    # Source tracking
    source_url = Column(String(500), nullable=False)
    source_hash = Column(String(64), nullable=False, unique=True)
    vector_doc_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Relationships
    findings = relationship("AuditFindingORM", backref="report")
    
    # Indexes
    __table_args__ = (
        Index('idx_ag_reports_period', 'reporting_period_start', 'reporting_period_end'),
        Index('idx_ag_reports_publication', 'publication_date'),
    )

class AuditFindingORM(Base):
    """Individual audit findings from AG reports"""
    __tablename__ = "audit_findings"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    report_id = Column(PGUUID(as_uuid=True), ForeignKey('auditor_general_reports.id'), nullable=False)
    
    # Finding details
    finding_number = Column(String(50))
    entity_name = Column(String(200), nullable=False)  # Ministry, department, county
    entity_type = Column(String(50))  # ministry, department, county, parastatal
    finding_text = Column(Text, nullable=False)
    recommendation = Column(Text)
    
    # Financial impact
    amount_involved = Column(Numeric(15, 2))  # Money involved in irregularity
    currency = Column(String(10), default='KES')
    
    # Categorization
    severity = Column(String(20))  # high, medium, low
    finding_type = Column(String(100))  # misappropriation, procurement_irregularity, etc.
    topics = Column(JSON, default=[])
    
    # Parliamentary response tracking
    discussed_in_parliament = Column(Boolean, default=False)
    related_statement_ids = Column(JSON, default=[])
    related_question_ids = Column(JSON, default=[])
    related_motion_ids = Column(JSON, default=[])
    
    # Implementation tracking
    recommendation_implemented = Column(Boolean)
    implementation_date = Column(Date)
    implementation_notes = Column(Text)
    
    # Source tracking
    source_page = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_findings_report', 'report_id'),
        Index('idx_findings_entity', 'entity_name'),
        Index('idx_findings_severity', 'severity'),
        Index('idx_findings_discussed', 'discussed_in_parliament'),
    )
```

**6. Order Papers Table**:
```python
class OrderPaperORM(Base):
    """Daily Order Papers (parliamentary agenda)"""
    __tablename__ = "order_papers"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    chamber = Column(SQLEnum(ChamberEnum), nullable=False)
    
    # Order Paper details
    sitting_date = Column(Date, nullable=False)
    session_id = Column(String(50))
    
    # Source tracking
    source_url = Column(String(500), nullable=False)
    source_hash = Column(String(64), nullable=False, unique=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Relationships
    agenda_items = relationship("AgendaItemORM", backref="order_paper")
    
    # Indexes
    __table_args__ = (
        Index('idx_order_papers_chamber', 'chamber'),
        Index('idx_order_papers_date', 'sitting_date'),
        UniqueConstraint('sitting_date', 'chamber', name='uq_order_paper_date_chamber'),
    )

class AgendaItemORM(Base):
    """Individual agenda items from Order Papers"""
    __tablename__ = "agenda_items"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    order_paper_id = Column(PGUUID(as_uuid=True), ForeignKey('order_papers.id'), nullable=False)
    
    # Item details
    item_number = Column(String(20), nullable=False)
    item_type = Column(String(50), nullable=False)  # bill, question, motion, report, etc.
    description = Column(Text, nullable=False)
    time_allocated = Column(Integer)  # Minutes
    
    # Correlation
    related_bill_id = Column(PGUUID(as_uuid=True), ForeignKey('bills.id'))
    related_question_id = Column(PGUUID(as_uuid=True), ForeignKey('questions.id'))
    related_motion_id = Column(PGUUID(as_uuid=True), ForeignKey('motion_tracker.id'))
    
    # Execution tracking
    executed = Column(Boolean, default=False)
    execution_date = Column(Date)
    time_spent = Column(Integer)  # Actual minutes spent
    deferred = Column(Boolean, default=False)
    deferred_reason = Column(Text)
    
    # Source tracking
    source_page = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Relationships
    bill = relationship("BillORM")
    question = relationship("QuestionORM")
    motion = relationship("MotionTrackerORM")
    
    # Indexes
    __table_args__ = (
        Index('idx_agenda_items_order_paper', 'order_paper_id'),
        Index('idx_agenda_items_type', 'item_type'),
        Index('idx_agenda_items_executed', 'executed'),
        Index('idx_agenda_items_deferred', 'deferred'),
    )
```

### Migration Strategy

```python
# alembic/versions/004_add_trackers_and_reports.py
def upgrade():
    # Create statement_requests table
    op.create_table(
        'statement_requests',
        # ... columns
    )
    
    # Create motion_tracker table
    op.create_table(
        'motion_tracker',
        # ... columns
    )
    
    # Create bill_tracker_entries table
    op.create_table(
        'bill_tracker_entries',
        # ... columns
    )
    
    # Create legislative_proposals table
    op.create_table(
        'legislative_proposals',
        # ... columns
    )
    
    # Create auditor_general_reports table
    op.create_table(
        'auditor_general_reports',
        # ... columns
    )
    
    # Create audit_findings table
    op.create_table(
        'audit_findings',
        # ... columns
    )
    
    # Create order_papers table
    op.create_table(
        'order_papers',
        # ... columns
    )
    
    # Create agenda_items table
    op.create_table(
        'agenda_items',
        # ... columns
    )
    
    # Add indexes
    # ... all indexes

def downgrade():
    op.drop_table('agenda_items')
    op.drop_table('order_papers')
    op.drop_table('audit_findings')
    op.drop_table('auditor_general_reports')
    op.drop_table('legislative_proposals')
    op.drop_table('bill_tracker_entries')
    op.drop_table('motion_tracker')
    op.drop_table('statement_requests')
```

### Correctness Properties

**Property 1.1**: Tracker data completeness
- **Validates**: Requirements 1.2.1, 2.2.1, 3.2.1
- **Property**: All tracker entries must be extracted from source documents
- **Test Strategy**: Manual count vs extracted count for 10 tracker documents

**Property 1.2**: Source traceability
- **Validates**: Requirements 13.1.1
- **Property**: All tracker entries must have valid source references
- **Test Strategy**: Verify source_url, source_hash, source_page for all entries



---

## Design 2: Tracker Document Scrapers

### Component Design

**Purpose**: Scrape tracker documents from parliament website for both chambers

**Technology**: BeautifulSoup + requests (reuse Phase 0 scraper infrastructure)

**Builds On**: Phase 0 BaseScraper, Phase 3 chamber-agnostic scrapers

### Implementation

```python
class TrackerScraper(BaseScraper):
    """Base scraper for tracker documents"""
    
    def __init__(self, config, chamber: Chamber):
        super().__init__(config)
        self.chamber = chamber
        self.base_url = self._get_chamber_base_url()
    
    def _get_chamber_base_url(self) -> str:
        """Get chamber-specific base URL"""
        if self.chamber == Chamber.NATIONAL_ASSEMBLY:
            return f"{self.config.scraper.base_url}/the-national-assembly"
        else:
            return f"{self.config.scraper.base_url}/the-senate"

class StatementsTrackerScraper(TrackerScraper):
    """Scrape Statements Tracker documents"""
    
    def discover_trackers(
        self,
        date_range: Optional[Tuple[date, date]] = None
    ) -> List[TrackerMetadata]:
        """Discover Statements Tracker documents"""
        url = f"{self.base_url}/house-business/statements"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find tracker PDF links
        tracker_links = soup.find_all('a', href=re.compile(r'/statements/.*\.pdf'))
        
        trackers = []
        for link in tracker_links:
            metadata = self._extract_tracker_metadata(link)
            if metadata and self._in_date_range(metadata.date, date_range):
                metadata.chamber = self.chamber
                trackers.append(metadata)
        
        return trackers
    
    def _extract_tracker_metadata(self, link) -> Optional[TrackerMetadata]:
        """Extract metadata from tracker link"""
        href = link.get('href')
        text = link.get_text(strip=True)
        
        # Extract date from filename or link text
        date_match = re.search(r'(\d{4}[-_]\d{2}[-_]\d{2})', href + text)
        if not date_match:
            return None
        
        tracker_date = self._parse_date(date_match.group(1))
        
        return TrackerMetadata(
            url=urljoin(self.base_url, href),
            date=tracker_date,
            chamber=self.chamber,
            document_type='statements_tracker'
        )

class MotionsTrackerScraper(TrackerScraper):
    """Scrape Motions Tracker documents"""
    
    def discover_trackers(
        self,
        date_range: Optional[Tuple[date, date]] = None
    ) -> List[TrackerMetadata]:
        """Discover Motions Tracker documents"""
        url = f"{self.base_url}/house-business/motions"
        
        # Similar to StatementsTrackerScraper
        # ...

class BillsTrackerScraper(TrackerScraper):
    """Scrape Bills Tracker documents"""
    
    def discover_trackers(
        self,
        date_range: Optional[Tuple[date, date]] = None
    ) -> List[TrackerMetadata]:
        """Discover Bills Tracker documents"""
        url = f"{self.base_url}/house-business/bills-tracker"
        
        # Similar to StatementsTrackerScraper
        # ...

class LegislativeProposalsScraper(TrackerScraper):
    """Scrape Legislative Proposals"""
    
    def discover_proposals(self) -> List[ProposalMetadata]:
        """Discover Legislative Proposals"""
        url = f"{self.base_url}/house-business/legislative-proposals"
        
        # Similar to other scrapers
        # ...

class AuditorGeneralReportScraper(BaseScraper):
    """Scrape Auditor General Reports (not chamber-specific)"""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_url = f"{config.scraper.base_url}/auditor-general-reports"
    
    def discover_reports(
        self,
        year: Optional[int] = None
    ) -> List[AGReportMetadata]:
        """Discover AG reports"""
        url = self.base_url
        
        response = self.session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find report links
        report_links = soup.find_all('a', href=re.compile(r'/reports/.*\.pdf'))
        
        reports = []
        for link in report_links:
            metadata = self._extract_report_metadata(link)
            if metadata and (year is None or metadata.year == year):
                reports.append(metadata)
        
        return reports

class OrderPaperScraper(TrackerScraper):
    """Scrape Order Papers (daily agenda)"""
    
    def discover_order_papers(
        self,
        date_range: Optional[Tuple[date, date]] = None
    ) -> List[OrderPaperMetadata]:
        """Discover Order Papers"""
        url = f"{self.base_url}/house-business/order-papers"
        
        # Similar to other scrapers
        # ...
```

### Correctness Properties

**Property 2.1**: Tracker discovery completeness
- **Validates**: Requirements 1.1.1, 2.1.1, 3.1.1
- **Property**: All tracker documents must be discovered
- **Test Strategy**: Compare with manual count from website for sample period

**Property 2.2**: Chamber tagging
- **Validates**: Requirements 1.1.1, 2.1.1, 3.1.1
- **Property**: All tracker documents must be tagged with correct chamber
- **Test Strategy**: Verify chamber field for all scraped documents

---

## Design 3: Tracker Document Processors

### Component Design

**Purpose**: Extract structured data from tracker PDFs

**Technology**: PyPDF2 + tabula-py for table extraction

**Builds On**: Phase 0 PDF processor

### Implementation

```python
from dataclasses import dataclass
from typing import List, Optional
import tabula
import re

@dataclass
class StatementRequest:
    """Statement request from Statements Tracker"""
    requester_name: str
    requester_id: Optional[str]
    topic: str
    request_date: date
    fulfilled: bool
    fulfillment_date: Optional[date]
    hansard_reference: Optional[str]

class StatementsTrackerProcessor:
    """Process Statements Tracker documents"""
    
    def __init__(self, db_session, chamber: Chamber):
        self.db = db_session
        self.chamber = chamber
        self.member_identifier = ParliamentarianIdentifier(db_session, chamber)
    
    def process_tracker(self, pdf_path: Path) -> List[StatementRequest]:
        """Extract statement requests from tracker PDF"""
        # Extract tables from PDF
        tables = tabula.read_pdf(
            str(pdf_path),
            pages='all',
            multiple_tables=True,
            pandas_options={'header': 0}
        )
        
        requests = []
        for table in tables:
            # Process each row
            for _, row in table.iterrows():
                request = self._parse_statement_row(row)
                if request:
                    requests.append(request)
        
        return requests
    
    def _parse_statement_row(self, row) -> Optional[StatementRequest]:
        """Parse statement request from table row"""
        try:
            # Extract requester name
            requester_name = str(row.get('Member', row.get('Name', ''))).strip()
            if not requester_name:
                return None
            
            # Identify MP/Senator
            member = self.member_identifier.identify(requester_name)
            
            # Extract topic
            topic = str(row.get('Topic', row.get('Statement', ''))).strip()
            
            # Extract request date
            request_date_str = str(row.get('Date', row.get('Request Date', '')))
            request_date = self._parse_date(request_date_str)
            
            # Check fulfillment
            status = str(row.get('Status', '')).strip().lower()
            fulfilled = 'fulfilled' in status or 'delivered' in status
            
            # Extract fulfillment date if available
            fulfillment_date = None
            if fulfilled:
                fulfillment_date_str = str(row.get('Fulfillment Date', ''))
                fulfillment_date = self._parse_date(fulfillment_date_str)
            
            return StatementRequest(
                requester_name=requester_name,
                requester_id=str(member.id) if member else None,
                topic=topic,
                request_date=request_date,
                fulfilled=fulfilled,
                fulfillment_date=fulfillment_date,
                hansard_reference=None  # Will be linked later
            )
        except Exception as e:
            self.logger.warning(f"Failed to parse statement row: {e}")
            return None

@dataclass
class MotionEntry:
    """Motion entry from Motions Tracker"""
    motion_number: str
    mover_name: str
    mover_id: Optional[str]
    motion_text: str
    motion_date: date
    status: str
    last_action_date: Optional[date]

class MotionsTrackerProcessor:
    """Process Motions Tracker documents"""
    
    def __init__(self, db_session, chamber: Chamber):
        self.db = db_session
        self.chamber = chamber
        self.member_identifier = ParliamentarianIdentifier(db_session, chamber)
    
    def process_tracker(self, pdf_path: Path) -> List[MotionEntry]:
        """Extract motions from tracker PDF"""
        # Extract tables
        tables = tabula.read_pdf(
            str(pdf_path),
            pages='all',
            multiple_tables=True,
            pandas_options={'header': 0}
        )
        
        motions = []
        for table in tables:
            for _, row in table.iterrows():
                motion = self._parse_motion_row(row)
                if motion:
                    motions.append(motion)
        
        return motions
    
    def _parse_motion_row(self, row) -> Optional[MotionEntry]:
        """Parse motion from table row"""
        try:
            # Extract motion number
            motion_number = str(row.get('Motion No.', row.get('No.', ''))).strip()
            
            # Extract mover
            mover_name = str(row.get('Mover', row.get('Member', ''))).strip()
            member = self.member_identifier.identify(mover_name)
            
            # Extract motion text
            motion_text = str(row.get('Motion', row.get('Text', ''))).strip()
            
            # Extract date
            motion_date_str = str(row.get('Date', ''))
            motion_date = self._parse_date(motion_date_str)
            
            # Extract status
            status = str(row.get('Status', '')).strip().lower()
            
            # Extract last action date
            last_action_str = str(row.get('Last Action', ''))
            last_action_date = self._parse_date(last_action_str) if last_action_str else None
            
            return MotionEntry(
                motion_number=motion_number,
                mover_name=mover_name,
                mover_id=str(member.id) if member else None,
                motion_text=motion_text,
                motion_date=motion_date,
                status=status,
                last_action_date=last_action_date
            )
        except Exception as e:
            self.logger.warning(f"Failed to parse motion row: {e}")
            return None

@dataclass
class BillTrackerEntry:
    """Bill status entry from Bills Tracker"""
    bill_number: str
    bill_id: Optional[str]
    title: str
    sponsor_name: str
    stage: str
    status: str
    last_action_date: date
    days_at_stage: int

class BillsTrackerProcessor:
    """Process Bills Tracker documents"""
    
    def __init__(self, db_session, chamber: Chamber):
        self.db = db_session
        self.chamber = chamber
    
    def process_tracker(self, pdf_path: Path, tracker_date: date) -> List[BillTrackerEntry]:
        """Extract bill status from tracker PDF"""
        # Extract tables
        tables = tabula.read_pdf(
            str(pdf_path),
            pages='all',
            multiple_tables=True,
            pandas_options={'header': 0}
        )
        
        entries = []
        for table in tables:
            for _, row in table.iterrows():
                entry = self._parse_bill_row(row, tracker_date)
                if entry:
                    entries.append(entry)
        
        return entries
    
    def _parse_bill_row(self, row, tracker_date: date) -> Optional[BillTrackerEntry]:
        """Parse bill status from table row"""
        try:
            # Extract bill number
            bill_number = str(row.get('Bill No.', row.get('No.', ''))).strip()
            
            # Find bill in database
            bill = self.db.query(BillORM).filter(
                BillORM.bill_number == bill_number,
                BillORM.chamber == self.chamber
            ).first()
            
            # Extract title
            title = str(row.get('Title', '')).strip()
            
            # Extract sponsor
            sponsor_name = str(row.get('Sponsor', '')).strip()
            
            # Extract stage
            stage = str(row.get('Stage', row.get('Current Stage', ''))).strip()
            
            # Extract status
            status = str(row.get('Status', '')).strip()
            
            # Extract last action date
            last_action_str = str(row.get('Last Action', ''))
            last_action_date = self._parse_date(last_action_str)
            
            # Calculate days at stage
            days_at_stage = (tracker_date - last_action_date).days if last_action_date else 0
            
            return BillTrackerEntry(
                bill_number=bill_number,
                bill_id=str(bill.id) if bill else None,
                title=title,
                sponsor_name=sponsor_name,
                stage=stage,
                status=status,
                last_action_date=last_action_date,
                days_at_stage=days_at_stage
            )
        except Exception as e:
            self.logger.warning(f"Failed to parse bill row: {e}")
            return None
```

### Correctness Properties

**Property 3.1**: Table extraction completeness
- **Validates**: Requirements 1.2.1, 2.2.1, 3.2.1
- **Property**: All tables must be extracted from tracker PDFs
- **Test Strategy**: Manual count vs extracted count for 10 documents

**Property 3.2**: Data parsing accuracy
- **Validates**: Requirements 1.4.1, 2.4.1, 3.4.1
- **Property**: Extraction accuracy must be ≥95%
- **Test Strategy**: Manual verification of 100 extracted entries

---

## Design 4: Auditor General Report Analyzer

### Component Design

**Purpose**: Extract and analyze audit findings from AG reports

**Technology**: PyPDF2 + spaCy NER + LLM for categorization

**Builds On**: Phase 1 LLM analyzer, Phase 0 PDF processor

### Implementation

```python
from decimal import Decimal
from typing import List, Optional
import spacy

@dataclass
class AuditFinding:
    """Audit finding from AG report"""
    finding_number: str
    entity_name: str
    entity_type: str
    finding_text: str
    recommendation: str
    amount_involved: Optional[Decimal]
    severity: str
    finding_type: str

class AuditorGeneralReportAnalyzer:
    """Analyze Auditor General reports"""
    
    def __init__(self, db_session, llm_analyzer):
        self.db = db_session
        self.llm = llm_analyzer
        self.nlp = spacy.load('en_core_web_sm')
    
    def process_report(self, pdf_path: Path) -> List[AuditFinding]:
        """Extract findings from AG report"""
        # Extract text
        text = self._extract_text(pdf_path)
        
        # Segment into findings
        findings_text = self._segment_findings(text)
        
        # Process each finding
        findings = []
        for finding_text in findings_text:
            finding = self._process_finding(finding_text)
            if finding:
                findings.append(finding)
        
        return findings
    
    def _segment_findings(self, text: str) -> List[str]:
        """Segment report into individual findings"""
        # Look for finding markers
        # Common patterns: "Finding 1.1:", "Observation:", "Issue:", etc.
        finding_pattern = r'(?:Finding|Observation|Issue)\s+\d+(?:\.\d+)?:'
        
        # Split text by finding markers
        findings = re.split(finding_pattern, text)
        
        # Remove empty segments
        findings = [f.strip() for f in findings if f.strip()]
        
        return findings
    
    def _process_finding(self, finding_text: str) -> Optional[AuditFinding]:
        """Process individual finding"""
        try:
            # Extract entity name using NER
            entity = self._extract_entity(finding_text)
            
            # Extract financial amounts
            amount = self._extract_amount(finding_text)
            
            # Extract recommendation
            recommendation = self._extract_recommendation(finding_text)
            
            # Categorize using LLM
            categorization = self._categorize_finding(finding_text)
            
            return AuditFinding(
                finding_number=self._extract_finding_number(finding_text),
                entity_name=entity['name'],
                entity_type=entity['type'],
                finding_text=finding_text,
                recommendation=recommendation,
                amount_involved=amount,
                severity=categorization['severity'],
                finding_type=categorization['type']
            )
        except Exception as e:
            self.logger.warning(f"Failed to process finding: {e}")
            return None
    
    def _extract_entity(self, text: str) -> Dict[str, str]:
        """Extract entity name using NER"""
        doc = self.nlp(text)
        
        # Look for organization entities
        entities = [ent for ent in doc.ents if ent.label_ == 'ORG']
        
        if entities:
            entity_name = entities[0].text
            
            # Determine entity type
            entity_type = self._classify_entity_type(entity_name)
            
            return {'name': entity_name, 'type': entity_type}
        
        return {'name': 'Unknown', 'type': 'unknown'}
    
    def _classify_entity_type(self, entity_name: str) -> str:
        """Classify entity type"""
        name_lower = entity_name.lower()
        
        if 'ministry' in name_lower:
            return 'ministry'
        elif 'county' in name_lower:
            return 'county'
        elif 'department' in name_lower:
            return 'department'
        elif 'authority' in name_lower or 'board' in name_lower:
            return 'parastatal'
        else:
            return 'other'
    
    def _extract_amount(self, text: str) -> Optional[Decimal]:
        """Extract financial amount from text"""
        # Look for currency patterns
        # Patterns: KES 1,000,000 | Ksh. 1,000,000 | 1,000,000/- | 1.5 million
        
        # Pattern 1: KES/Ksh with number
        pattern1 = r'(?:KES|Ksh\.?)\s*([\d,]+(?:\.\d+)?)'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            return Decimal(amount_str)
        
        # Pattern 2: Number with /- suffix
        pattern2 = r'([\d,]+(?:\.\d+)?)\s*/[-]'
        match = re.search(pattern2, text)
        if match:
            amount_str = match.group(1).replace(',', '')
            return Decimal(amount_str)
        
        # Pattern 3: Million/billion
        pattern3 = r'([\d.]+)\s*(million|billion)'
        match = re.search(pattern3, text, re.IGNORECASE)
        if match:
            number = Decimal(match.group(1))
            unit = match.group(2).lower()
            multiplier = Decimal('1000000') if unit == 'million' else Decimal('1000000000')
            return number * multiplier
        
        return None
    
    def _extract_recommendation(self, text: str) -> str:
        """Extract recommendation from finding text"""
        # Look for recommendation section
        rec_pattern = r'(?:Recommendation|We recommend|It is recommended):\s*(.+?)(?:\n\n|$)'
        match = re.search(rec_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _categorize_finding(self, finding_text: str) -> Dict[str, str]:
        """Categorize finding using LLM"""
        prompt = f"""Categorize this audit finding:

Finding: {finding_text[:1000]}

Provide:
1. Severity (high/medium/low)
2. Type (misappropriation/procurement_irregularity/poor_record_keeping/non_compliance/other)

Respond in JSON format:
{{
    "severity": "high|medium|low",
    "type": "category",
    "reasoning": "brief explanation"
}}"""
        
        response = self.llm.analyze(prompt)
        return self._parse_categorization_response(response)

@dataclass
class MotionEntry:
    """Motion from Motions Tracker"""
    motion_number: str
    mover_name: str
    mover_id: Optional[str]
    motion_text: str
    motion_date: date
    status: str

class MotionsTrackerProcessor:
    """Process Motions Tracker documents"""
    
    def __init__(self, db_session, chamber: Chamber):
        self.db = db_session
        self.chamber = chamber
        self.member_identifier = ParliamentarianIdentifier(db_session, chamber)
    
    def process_tracker(self, pdf_path: Path) -> List[MotionEntry]:
        """Extract motions from tracker PDF"""
        # Similar to StatementsTrackerProcessor
        # Extract tables and parse rows
        # ...

@dataclass
class LegislativeProposal:
    """Legislative proposal"""
    proposal_number: str
    title: str
    proposer_name: str
    proposer_id: Optional[str]
    submission_date: date
    proposal_text: str
    status: str

class LegislativeProposalProcessor:
    """Process Legislative Proposals"""
    
    def __init__(self, db_session, chamber: Chamber):
        self.db = db_session
        self.chamber = chamber
        self.member_identifier = ParliamentarianIdentifier(db_session, chamber)
    
    def process_proposal(self, pdf_path: Path) -> LegislativeProposal:
        """Extract proposal from PDF"""
        # Extract text
        text = self._extract_text(pdf_path)
        
        # Extract metadata
        metadata = self._extract_metadata(text)
        
        # Identify proposer
        proposer = self.member_identifier.identify(metadata['proposer_name'])
        
        return LegislativeProposal(
            proposal_number=metadata['number'],
            title=metadata['title'],
            proposer_name=metadata['proposer_name'],
            proposer_id=str(proposer.id) if proposer else None,
            submission_date=metadata['date'],
            proposal_text=text,
            status=metadata['status']
        )
```

### Correctness Properties

**Property 4.1**: Extraction completeness
- **Validates**: Requirements 1.2.1, 2.2.1, 5.2.2
- **Property**: All entries must be extracted from tracker documents
- **Test Strategy**: Manual count vs extracted count for 10 documents

**Property 4.2**: Financial amount accuracy
- **Validates**: Requirements 5.5.2
- **Property**: Financial amounts must be ≥95% accurate
- **Test Strategy**: Manual verification of 50 extracted amounts



---

## Design 5: Order Paper Parser

### Component Design

**Purpose**: Parse Order Papers (daily parliamentary agenda) and track execution

**Technology**: PyPDF2 + tabula-py + pattern matching

**Builds On**: Phase 0 PDF processor

### Implementation

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class AgendaItemType(Enum):
    """Types of agenda items"""
    BILL_READING = "bill_reading"
    QUESTION_TIME = "question_time"
    MOTION = "motion"
    COMMITTEE_REPORT = "committee_report"
    STATEMENT = "statement"
    PETITION = "petition"
    OTHER = "other"

@dataclass
class AgendaItem:
    """Agenda item from Order Paper"""
    item_number: str
    item_type: AgendaItemType
    description: str
    time_allocated: Optional[int]  # Minutes
    related_bill_number: Optional[str]
    related_question_number: Optional[str]
    related_motion_number: Optional[str]

class OrderPaperParser:
    """Parse Order Papers"""
    
    def __init__(self, db_session, chamber: Chamber):
        self.db = db_session
        self.chamber = chamber
    
    def parse_order_paper(self, pdf_path: Path, sitting_date: date) -> List[AgendaItem]:
        """Parse agenda items from Order Paper"""
        # Extract text
        text = self._extract_text(pdf_path)
        
        # Extract agenda items
        items = self._extract_agenda_items(text)
        
        return items
    
    def _extract_agenda_items(self, text: str) -> List[AgendaItem]:
        """Extract agenda items from text"""
        items = []
        
        # Split by item numbers (1., 2., 3., etc.)
        item_pattern = r'(\d+)\.\s+(.+?)(?=\n\d+\.|$)'
        matches = re.finditer(item_pattern, text, re.DOTALL)
        
        for match in matches:
            item_number = match.group(1)
            item_text = match.group(2).strip()
            
            # Classify item type
            item_type = self._classify_item_type(item_text)
            
            # Extract time allocation
            time_allocated = self._extract_time_allocation(item_text)
            
            # Extract related document numbers
            related_refs = self._extract_related_references(item_text, item_type)
            
            items.append(AgendaItem(
                item_number=item_number,
                item_type=item_type,
                description=item_text,
                time_allocated=time_allocated,
                related_bill_number=related_refs.get('bill'),
                related_question_number=related_refs.get('question'),
                related_motion_number=related_refs.get('motion')
            ))
        
        return items
    
    def _classify_item_type(self, text: str) -> AgendaItemType:
        """Classify agenda item type"""
        text_lower = text.lower()
        
        if 'bill' in text_lower and any(stage in text_lower for stage in ['first reading', 'second reading', 'third reading']):
            return AgendaItemType.BILL_READING
        elif 'question' in text_lower or 'questions by members' in text_lower:
            return AgendaItemType.QUESTION_TIME
        elif 'motion' in text_lower:
            return AgendaItemType.MOTION
        elif 'committee report' in text_lower or 'report of' in text_lower:
            return AgendaItemType.COMMITTEE_REPORT
        elif 'statement' in text_lower:
            return AgendaItemType.STATEMENT
        elif 'petition' in text_lower:
            return AgendaItemType.PETITION
        else:
            return AgendaItemType.OTHER
    
    def _extract_time_allocation(self, text: str) -> Optional[int]:
        """Extract time allocation in minutes"""
        # Look for time patterns: "30 minutes", "1 hour", "2 hours 30 minutes"
        
        # Pattern 1: X minutes
        pattern1 = r'(\d+)\s*minutes?'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Pattern 2: X hour(s)
        pattern2 = r'(\d+)\s*hours?'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return int(match.group(1)) * 60
        
        # Pattern 3: X hours Y minutes
        pattern3 = r'(\d+)\s*hours?\s+(\d+)\s*minutes?'
        match = re.search(pattern3, text, re.IGNORECASE)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            return hours * 60 + minutes
        
        return None
    
    def _extract_related_references(self, text: str, item_type: AgendaItemType) -> Dict[str, str]:
        """Extract related document references"""
        refs = {}
        
        if item_type == AgendaItemType.BILL_READING:
            # Extract bill number
            bill_pattern = r'Bill\s+No\.\s*(\d+(?:/\d+)?)'
            match = re.search(bill_pattern, text, re.IGNORECASE)
            if match:
                refs['bill'] = match.group(1)
        
        elif item_type == AgendaItemType.MOTION:
            # Extract motion number
            motion_pattern = r'Motion\s+No\.\s*(\d+)'
            match = re.search(motion_pattern, text, re.IGNORECASE)
            if match:
                refs['motion'] = match.group(1)
        
        elif item_type == AgendaItemType.QUESTION_TIME:
            # Extract question numbers (may be range)
            question_pattern = r'Questions?\s+No\.\s*(\d+(?:\s*-\s*\d+)?)'
            match = re.search(question_pattern, text, re.IGNORECASE)
            if match:
                refs['question'] = match.group(1)
        
        return refs

class AgendaExecutionTracker:
    """Track agenda item execution"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def link_agenda_to_proceedings(
        self,
        order_paper_id: str,
        hansard_id: str
    ):
        """Link Order Paper items to actual proceedings"""
        # Get agenda items
        agenda_items = self.db.query(AgendaItemORM).filter(
            AgendaItemORM.order_paper_id == order_paper_id
        ).all()
        
        # Get Hansard statements
        statements = self.db.query(StatementORM).filter(
            StatementORM.document_id == hansard_id
        ).all()
        
        # Match agenda items to proceedings
        for item in agenda_items:
            executed = self._check_item_execution(item, statements)
            
            if executed:
                item.executed = True
                item.execution_date = statements[0].created_at.date()
            else:
                item.deferred = True
        
        self.db.commit()
    
    def _check_item_execution(
        self,
        item: AgendaItemORM,
        statements: List[StatementORM]
    ) -> bool:
        """Check if agenda item was executed"""
        # Check by related document
        if item.related_bill_id:
            # Check if bill was discussed
            for stmt in statements:
                if item.related_bill_id in stmt.related_bill_ids:
                    return True
        
        # Check by description similarity
        item_desc_lower = item.description.lower()
        for stmt in statements:
            if self._text_similarity(item_desc_lower, stmt.text.lower()) > 0.7:
                return True
        
        return False
    
    def calculate_completion_rate(self, order_paper_id: str) -> float:
        """Calculate agenda completion rate"""
        items = self.db.query(AgendaItemORM).filter(
            AgendaItemORM.order_paper_id == order_paper_id
        ).all()
        
        if not items:
            return 0.0
        
        executed_count = len([i for i in items if i.executed])
        return (executed_count / len(items)) * 100
```

### Correctness Properties

**Property 5.1**: Agenda extraction completeness
- **Validates**: Requirements 6.2.1
- **Property**: All agenda items must be extracted
- **Test Strategy**: Manual count vs extracted count for 10 Order Papers

**Property 5.2**: Execution tracking accuracy
- **Validates**: Requirements 6.5.3
- **Property**: Execution tracking must be ≥90% accurate
- **Test Strategy**: Manual verification of 50 agenda items

---

## Design 6: Enhanced Correlation Engine

### Component Design

**Purpose**: Link tracker documents to primary documents and enable cross-document analysis

**Technology**: Vector similarity + pattern matching + database queries

**Builds On**: Phase 2 correlation engine

### Implementation

```python
class EnhancedCorrelationEngine:
    """Enhanced correlation with tracker documents"""
    
    def __init__(self, db_session, vector_db, embedding_generator):
        self.db = db_session
        self.vector_db = vector_db
        self.embedder = embedding_generator
    
    def link_statement_requests_to_hansard(self):
        """Link statement requests to actual statements in Hansard"""
        # Get unfulfilled statement requests
        requests = self.db.query(StatementRequestORM).filter(
            StatementRequestORM.fulfilled == False
        ).all()
        
        for request in requests:
            # Search for matching statement
            matching_statement = self._find_matching_statement(request)
            
            if matching_statement:
                request.fulfilled = True
                request.fulfillment_date = matching_statement.created_at.date()
                request.hansard_statement_id = matching_statement.id
        
        self.db.commit()
    
    def _find_matching_statement(
        self,
        request: StatementRequestORM
    ) -> Optional[StatementORM]:
        """Find Hansard statement matching request"""
        # Get requester's statements after request date
        statements = self.db.query(StatementORM).filter(
            StatementORM.mp_id == request.requester_id,
            StatementORM.created_at >= request.request_date
        ).all()
        
        if not statements:
            return None
        
        # Use vector similarity to find best match
        request_embedding = self.embedder.generate(request.topic)
        
        best_match = None
        best_similarity = 0.0
        
        for stmt in statements:
            stmt_embedding = self.embedder.generate(stmt.text[:500])
            similarity = self._cosine_similarity(request_embedding, stmt_embedding)
            
            if similarity > best_similarity and similarity > 0.7:
                best_similarity = similarity
                best_match = stmt
        
        return best_match
    
    def link_motions_to_votes(self):
        """Link motions to votes"""
        # Get motions without votes
        motions = self.db.query(MotionTrackerORM).filter(
            MotionTrackerORM.vote_id == None
        ).all()
        
        for motion in motions:
            # Find vote on same date
            vote = self.db.query(VoteORM).filter(
                VoteORM.chamber == motion.chamber,
                VoteORM.vote_date == motion.motion_date
            ).first()
            
            if vote:
                # Verify it's the right vote using text similarity
                if self._is_matching_vote(motion, vote):
                    motion.vote_id = vote.id
        
        self.db.commit()
    
    def link_ag_findings_to_debates(self):
        """Link AG report findings to parliamentary debates"""
        # Get all findings
        findings = self.db.query(AuditFindingORM).all()
        
        for finding in findings:
            # Search for statements mentioning entity
            statements = self._find_statements_about_entity(finding.entity_name)
            
            if statements:
                finding.discussed_in_parliament = True
                finding.related_statement_ids = [str(s.id) for s in statements]
            
            # Search for questions about entity
            questions = self._find_questions_about_entity(finding.entity_name)
            
            if questions:
                finding.related_question_ids = [str(q.id) for q in questions]
        
        self.db.commit()
    
    def link_proposals_to_bills(self):
        """Link Legislative Proposals to resulting bills"""
        # Get proposals without bills
        proposals = self.db.query(LegislativeProposalORM).filter(
            LegislativeProposalORM.resulted_in_bill == False
        ).all()
        
        for proposal in proposals:
            # Search for bills with similar title
            bills = self.db.query(BillORM).filter(
                BillORM.chamber == proposal.chamber
            ).all()
            
            # Use text similarity to find match
            best_match = None
            best_similarity = 0.0
            
            for bill in bills:
                similarity = self._text_similarity(
                    proposal.title.lower(),
                    bill.title.lower()
                )
                
                if similarity > best_similarity and similarity > 0.8:
                    best_similarity = similarity
                    best_match = bill
            
            if best_match:
                proposal.resulted_in_bill = True
                proposal.bill_id = best_match.id
                proposal.conversion_date = best_match.introduction_date
        
        self.db.commit()
    
    def _find_statements_about_entity(self, entity_name: str) -> List[StatementORM]:
        """Find statements mentioning entity"""
        # Use vector search for semantic matching
        entity_embedding = self.embedder.generate(entity_name)
        
        # Search vector DB
        results = self.vector_db.search(
            collection_name='statements',
            query_vector=entity_embedding,
            limit=20,
            score_threshold=0.7
        )
        
        # Get statement IDs
        statement_ids = [r['id'] for r in results]
        
        # Fetch from database
        statements = self.db.query(StatementORM).filter(
            StatementORM.id.in_(statement_ids)
        ).all()
        
        return statements
```

### Correctness Properties

**Property 6.1**: Correlation accuracy
- **Validates**: Requirements 7.1.1, 7.1.2, 7.1.3, 7.1.4
- **Property**: Tracker-to-document correlations must be ≥85% accurate
- **Test Strategy**: Manual verification of 100 correlations

**Property 6.2**: AG report-debate linking
- **Validates**: Requirements 7.2.1
- **Property**: AG report findings must be linked to relevant debates
- **Test Strategy**: Manual review of 30 findings, verify parliamentary response

---

## Design 7: Accountability Analytics

### Component Design

**Purpose**: Generate accountability metrics and insights

**Technology**: Pandas for aggregation + custom analytics

**Builds On**: Phase 3 cross-chamber analyzer

### Implementation

```python
from dataclasses import dataclass
from typing import Dict, List
import pandas as pd

@dataclass
class ConstituencyRepresentationScore:
    """Constituency representation metrics"""
    constituency: str
    mp_name: str
    
    # Activity counts
    total_statements: int
    constituency_statements: int
    questions_asked: int
    constituency_questions: int
    petitions_sponsored: int
    
    # Representation score (0-100)
    representation_score: float
    
    # Breakdown
    statement_score: float
    question_score: float
    petition_score: float

class AccountabilityAnalyzer:
    """Generate accountability metrics"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def calculate_constituency_representation(
        self,
        constituency: str
    ) -> ConstituencyRepresentationScore:
        """Calculate representation score for constituency"""
        # Get MP for constituency
        mp = self.db.query(MPORM).filter(
            MPORM.constituency == constituency
        ).first()
        
        if not mp:
            raise ValueError(f"No MP found for {constituency}")
        
        # Get activity counts
        total_statements = self.db.query(StatementORM).filter(
            StatementORM.mp_id == mp.id
        ).count()
        
        constituency_statements = self.db.query(StatementORM).filter(
            StatementORM.mp_id == mp.id
        ).join(StatementRequestORM).filter(
            StatementRequestORM.is_constituency_specific == True
        ).count()
        
        questions_asked = self.db.query(QuestionORM).filter(
            QuestionORM.asker_id == mp.id
        ).count()
        
        # Count constituency-specific questions
        constituency_questions = 0
        questions = self.db.query(QuestionORM).filter(
            QuestionORM.asker_id == mp.id
        ).all()
        
        for q in questions:
            if constituency.lower() in q.question_text.lower():
                constituency_questions += 1
        
        petitions_sponsored = self.db.query(PetitionORM).filter(
            PetitionORM.sponsor_id == mp.id
        ).count()
        
        # Calculate scores
        statement_score = (constituency_statements / max(total_statements, 1)) * 100
        question_score = (constituency_questions / max(questions_asked, 1)) * 100
        petition_score = min(petitions_sponsored * 10, 100)  # 10 points per petition, max 100
        
        # Overall score (weighted average)
        representation_score = (
            statement_score * 0.4 +
            question_score * 0.4 +
            petition_score * 0.2
        )
        
        return ConstituencyRepresentationScore(
            constituency=constituency,
            mp_name=mp.name,
            total_statements=total_statements,
            constituency_statements=constituency_statements,
            questions_asked=questions_asked,
            constituency_questions=constituency_questions,
            petitions_sponsored=petitions_sponsored,
            representation_score=representation_score,
            statement_score=statement_score,
            question_score=question_score,
            petition_score=petition_score
        )
    
    def generate_financial_oversight_report(self) -> Dict:
        """Generate financial oversight report"""
        # Get all AG report findings
        findings = self.db.query(AuditFindingORM).all()
        
        # Calculate total irregularities
        total_amount = sum(
            f.amount_involved for f in findings
            if f.amount_involved is not None
        )
        
        # Group by entity
        entity_totals = {}
        for finding in findings:
            entity = finding.entity_name
            amount = finding.amount_involved or Decimal(0)
            entity_totals[entity] = entity_totals.get(entity, Decimal(0)) + amount
        
        # Sort by amount
        top_entities = sorted(
            entity_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]
        
        # Calculate parliamentary response rate
        discussed_count = len([f for f in findings if f.discussed_in_parliament])
        response_rate = (discussed_count / len(findings)) * 100 if findings else 0
        
        # Identify MPs/Senators active in oversight
        oversight_activity = self._calculate_oversight_activity()
        
        return {
            'total_findings': len(findings),
            'total_amount_involved': float(total_amount),
            'top_entities': [(e, float(a)) for e, a in top_entities],
            'parliamentary_response_rate': response_rate,
            'oversight_leaders': oversight_activity[:10]
        }
    
    def _calculate_oversight_activity(self) -> List[Dict]:
        """Calculate oversight activity by MP/Senator"""
        # Get all findings with parliamentary response
        findings = self.db.query(AuditFindingORM).filter(
            AuditFindingORM.discussed_in_parliament == True
        ).all()
        
        # Count activity by member
        member_activity = {}
        
        for finding in findings:
            # Count statements
            for stmt_id in finding.related_statement_ids:
                stmt = self.db.query(StatementORM).filter(
                    StatementORM.id == stmt_id
                ).first()
                
                if stmt:
                    member_id = stmt.mp_id
                    member_activity[member_id] = member_activity.get(member_id, 0) + 1
            
            # Count questions
            for q_id in finding.related_question_ids:
                q = self.db.query(QuestionORM).filter(
                    QuestionORM.id == q_id
                ).first()
                
                if q:
                    member_id = q.asker_id
                    member_activity[member_id] = member_activity.get(member_id, 0) + 1
        
        # Sort by activity
        sorted_activity = sorted(
            member_activity.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get member details
        result = []
        for member_id, count in sorted_activity:
            member = self._get_member(member_id)
            if member:
                result.append({
                    'member_id': member_id,
                    'name': member.name,
                    'chamber': member.chamber.value,
                    'oversight_activities': count
                })
        
        return result
    
    def generate_legislative_efficiency_report(self, chamber: Chamber) -> Dict:
        """Generate legislative efficiency report"""
        # Get bill tracker entries
        entries = self.db.query(BillTrackerEntryORM).filter(
            BillTrackerEntryORM.chamber == chamber
        ).all()
        
        if not entries:
            return {'error': 'No tracker data'}
        
        # Calculate average time per stage
        stage_times = {}
        for entry in entries:
            stage = entry.stage
            days = entry.days_at_stage
            
            if stage not in stage_times:
                stage_times[stage] = []
            stage_times[stage].append(days)
        
        avg_stage_times = {
            stage: sum(times) / len(times)
            for stage, times in stage_times.items()
        }
        
        # Identify stalled bills
        stalled_bills = self.db.query(BillTrackerEntryORM).filter(
            BillTrackerEntryORM.chamber == chamber,
            BillTrackerEntryORM.is_stalled == True
        ).count()
        
        # Calculate agenda completion rate
        order_papers = self.db.query(OrderPaperORM).filter(
            OrderPaperORM.chamber == chamber
        ).all()
        
        completion_rates = []
        for op in order_papers:
            rate = AgendaExecutionTracker(self.db).calculate_completion_rate(str(op.id))
            completion_rates.append(rate)
        
        avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0
        
        return {
            'chamber': chamber.value,
            'average_stage_times': avg_stage_times,
            'stalled_bills_count': stalled_bills,
            'average_agenda_completion_rate': avg_completion_rate
        }
```

### Correctness Properties

**Property 7.1**: Correlation completeness
- **Validates**: Requirements 7.1.1, 7.1.2, 7.1.3
- **Property**: All tracker entries must be correlated where possible
- **Test Strategy**: Verify correlation attempts for all entries

**Property 7.2**: Representation score validity
- **Validates**: Requirements 8.3.4
- **Property**: Representation scores must be between 0-100
- **Test Strategy**: Verify all scores in valid range



---

## Design 8: Enhanced Site Generation for Trackers

### Component Design

**Purpose**: Generate pages for tracker documents and accountability dashboards

**Technology**: Jinja2 templates + static site generator

**Builds On**: Phase 3 enhanced site generator

### New Page Templates

**1. Statements Tracker Page** (`templates/pages/statements_tracker.html`):
```html
{% extends "layouts/base.html" %}

{% block content %}
<div class="statements-tracker">
    <h1>Statements Tracker - {{ chamber|title }}</h1>
    
    <!-- Summary Stats -->
    <div class="summary-stats">
        <div class="stat">
            <span class="value">{{ total_requests }}</span>
            <span class="label">Total Requests</span>
        </div>
        <div class="stat">
            <span class="value">{{ fulfilled_count }}</span>
            <span class="label">Fulfilled</span>
        </div>
        <div class="stat">
            <span class="value">{{ fulfillment_rate|round(1) }}%</span>
            <span class="label">Fulfillment Rate</span>
        </div>
    </div>
    
    <!-- Requests Table -->
    <table class="requests-table">
        <thead>
            <tr>
                <th>Date</th>
                <th>Member</th>
                <th>Topic</th>
                <th>Status</th>
                <th>Fulfillment Date</th>
            </tr>
        </thead>
        <tbody>
            {% for request in requests %}
            <tr class="{{ 'fulfilled' if request.fulfilled else 'pending' }}">
                <td>{{ request.request_date }}</td>
                <td><a href="/mps/{{ request.requester_id }}.html">{{ request.requester_name }}</a></td>
                <td>{{ request.topic }}</td>
                <td>{{ 'Fulfilled' if request.fulfilled else 'Pending' }}</td>
                <td>
                    {% if request.fulfilled %}
                        {{ request.fulfillment_date }}
                        <a href="/statements/{{ request.hansard_statement_id }}.html">View Statement</a>
                    {% else %}
                        -
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

**2. Auditor General Report Page** (`templates/pages/ag_report.html`):
```html
{% extends "layouts/base.html" %}

{% block content %}
<div class="ag-report">
    <h1>{{ report.title }}</h1>
    <p class="period">Reporting Period: {{ report.reporting_period_start }} to {{ report.reporting_period_end }}</p>
    <p class="publication">Published: {{ report.publication_date }}</p>
    
    <!-- Summary Stats -->
    <div class="summary-stats">
        <div class="stat">
            <span class="value">{{ findings|length }}</span>
            <span class="label">Total Findings</span>
        </div>
        <div class="stat">
            <span class="value">KES {{ total_amount|format_currency }}</span>
            <span class="label">Total Amount Involved</span>
        </div>
        <div class="stat">
            <span class="value">{{ discussed_count }}</span>
            <span class="label">Discussed in Parliament</span>
        </div>
        <div class="stat">
            <span class="value">{{ response_rate|round(1) }}%</span>
            <span class="label">Parliamentary Response Rate</span>
        </div>
    </div>
    
    <!-- Findings by Severity -->
    <section class="findings-by-severity">
        <h2>Findings by Severity</h2>
        
        {% for severity in ['high', 'medium', 'low'] %}
        <div class="severity-section">
            <h3>{{ severity|title }} Severity ({{ findings_by_severity[severity]|length }})</h3>
            
            {% for finding in findings_by_severity[severity] %}
            <div class="finding finding-{{ severity }}">
                <h4>{{ finding.entity_name }}</h4>
                <p class="finding-text">{{ finding.finding_text[:300] }}...</p>
                
                {% if finding.amount_involved %}
                <p class="amount">Amount: KES {{ finding.amount_involved|format_currency }}</p>
                {% endif %}
                
                <p class="recommendation"><strong>Recommendation:</strong> {{ finding.recommendation }}</p>
                
                {% if finding.discussed_in_parliament %}
                <div class="parliamentary-response">
                    <h5>Parliamentary Response:</h5>
                    <ul>
                        {% for stmt_id in finding.related_statement_ids %}
                        <li><a href="/statements/{{ stmt_id }}.html">View Statement</a></li>
                        {% endfor %}
                        {% for q_id in finding.related_question_ids %}
                        <li><a href="/questions/{{ q_id }}.html">View Question</a></li>
                        {% endfor %}
                    </ul>
                </div>
                {% else %}
                <p class="no-response">⚠️ No parliamentary response yet</p>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </section>
    
    <!-- Findings by Entity -->
    <section class="findings-by-entity">
        <h2>Top Entities by Irregularities</h2>
        <table>
            <thead>
                <tr>
                    <th>Entity</th>
                    <th>Findings</th>
                    <th>Total Amount</th>
                    <th>Parliamentary Response</th>
                </tr>
            </thead>
            <tbody>
                {% for entity in top_entities %}
                <tr>
                    <td><a href="/entities/{{ entity.id }}.html">{{ entity.name }}</a></td>
                    <td>{{ entity.findings_count }}</td>
                    <td>KES {{ entity.total_amount|format_currency }}</td>
                    <td>{{ entity.response_rate|round(1) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </section>
</div>
{% endblock %}
```

**3. Financial Oversight Dashboard** (`templates/pages/financial_oversight.html`):
```html
{% extends "layouts/base.html" %}

{% block content %}
<div class="financial-oversight-dashboard">
    <h1>Financial Oversight Dashboard</h1>
    
    <!-- Overview Stats -->
    <div class="overview-stats">
        <div class="stat">
            <span class="value">{{ total_reports }}</span>
            <span class="label">AG Reports</span>
        </div>
        <div class="stat">
            <span class="value">{{ total_findings }}</span>
            <span class="label">Total Findings</span>
        </div>
        <div class="stat">
            <span class="value">KES {{ total_irregularities|format_currency }}</span>
            <span class="label">Total Irregularities</span>
        </div>
        <div class="stat">
            <span class="value">{{ response_rate|round(1) }}%</span>
            <span class="label">Parliamentary Response Rate</span>
        </div>
    </div>
    
    <!-- Oversight Leaders -->
    <section class="oversight-leaders">
        <h2>Most Active in Financial Oversight</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Member</th>
                    <th>Chamber</th>
                    <th>Activities</th>
                </tr>
            </thead>
            <tbody>
                {% for leader in oversight_leaders %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td><a href="/members/{{ leader.member_id }}.html">{{ leader.name }}</a></td>
                    <td>{{ leader.chamber|title }}</td>
                    <td>{{ leader.oversight_activities }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </section>
    
    <!-- Entities with Most Irregularities -->
    <section class="top-entities">
        <h2>Entities with Most Irregularities</h2>
        <table>
            <thead>
                <tr>
                    <th>Entity</th>
                    <th>Type</th>
                    <th>Findings</th>
                    <th>Amount</th>
                    <th>Response Rate</th>
                </tr>
            </thead>
            <tbody>
                {% for entity in top_entities %}
                <tr>
                    <td><a href="/entities/{{ entity.id }}.html">{{ entity.name }}</a></td>
                    <td>{{ entity.type|title }}</td>
                    <td>{{ entity.findings_count }}</td>
                    <td>KES {{ entity.amount|format_currency }}</td>
                    <td>{{ entity.response_rate|round(1) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </section>
    
    <!-- Recent Reports -->
    <section class="recent-reports">
        <h2>Recent Auditor General Reports</h2>
        {% for report in recent_reports %}
        <div class="report-card">
            <h3><a href="/ag-reports/{{ report.id }}.html">{{ report.title }}</a></h3>
            <p class="period">{{ report.reporting_period_start }} to {{ report.reporting_period_end }}</p>
            <p class="findings">{{ report.findings_count }} findings</p>
            <p class="amount">KES {{ report.total_amount|format_currency }}</p>
        </div>
        {% endfor %}
    </section>
</div>
{% endblock %}
```

**4. Legislative Efficiency Dashboard** (`templates/pages/legislative_efficiency.html`):
```html
{% extends "layouts/base.html" %}

{% block content %}
<div class="legislative-efficiency-dashboard">
    <h1>Legislative Efficiency Dashboard</h1>
    
    <!-- Chamber Comparison -->
    <div class="chamber-comparison">
        <div class="chamber-stats">
            <h2>National Assembly</h2>
            <p>Avg passage time: {{ na_efficiency.average_passage_time_days }} days</p>
            <p>Amendment rate: {{ na_efficiency.amendment_rate_percentage|round(1) }}%</p>
            <p>Agenda completion: {{ na_efficiency.agenda_completion_rate|round(1) }}%</p>
        </div>
        
        <div class="chamber-stats">
            <h2>Senate</h2>
            <p>Avg passage time: {{ senate_efficiency.average_passage_time_days }} days</p>
            <p>Amendment rate: {{ senate_efficiency.amendment_rate_percentage|round(1) }}%</p>
            <p>Agenda completion: {{ senate_efficiency.agenda_completion_rate|round(1) }}%</p>
        </div>
    </div>
    
    <!-- Stalled Bills -->
    <section class="stalled-bills">
        <h2>Stalled Bills (>30 days at current stage)</h2>
        <table>
            <thead>
                <tr>
                    <th>Bill</th>
                    <th>Chamber</th>
                    <th>Stage</th>
                    <th>Days at Stage</th>
                    <th>Last Action</th>
                </tr>
            </thead>
            <tbody>
                {% for bill in stalled_bills %}
                <tr>
                    <td><a href="/bills/{{ bill.id }}.html">{{ bill.title }}</a></td>
                    <td>{{ bill.chamber|title }}</td>
                    <td>{{ bill.stage }}</td>
                    <td>{{ bill.days_at_stage }}</td>
                    <td>{{ bill.last_action_date }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </section>
    
    <!-- Most Efficient Sponsors -->
    <section class="efficient-sponsors">
        <h2>Most Efficient Bill Sponsors</h2>
        <p>Members whose bills progress fastest through legislative stages</p>
        <table>
            <thead>
                <tr>
                    <th>Member</th>
                    <th>Bills Sponsored</th>
                    <th>Avg Passage Time</th>
                    <th>Success Rate</th>
                </tr>
            </thead>
            <tbody>
                {% for sponsor in efficient_sponsors %}
                <tr>
                    <td><a href="/members/{{ sponsor.id }}.html">{{ sponsor.name }}</a></td>
                    <td>{{ sponsor.bills_count }}</td>
                    <td>{{ sponsor.avg_passage_days }} days</td>
                    <td>{{ sponsor.success_rate|round(1) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </section>
</div>
{% endblock %}
```

### Site Generator Implementation

```python
class Phase4SiteGenerator:
    """Generate site with tracker and report pages"""
    
    def __init__(self, db_session, template_dir: Path, output_dir: Path):
        self.db = db_session
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))
    
    def generate_all(self):
        """Generate complete site with Phase 4 pages"""
        # Generate tracker pages
        self.generate_statements_tracker_pages()
        self.generate_motions_tracker_pages()
        self.generate_bills_tracker_pages()
        
        # Generate proposal pages
        self.generate_legislative_proposal_pages()
        
        # Generate AG report pages
        self.generate_ag_report_pages()
        
        # Generate Order Paper pages
        self.generate_order_paper_pages()
        
        # Generate accountability dashboards
        self.generate_financial_oversight_dashboard()
        self.generate_legislative_efficiency_dashboard()
        self.generate_constituency_representation_pages()
    
    def generate_ag_report_pages(self):
        """Generate AG report pages"""
        reports = self.db.query(AuditorGeneralReportORM).all()
        
        for report in reports:
            # Get findings
            findings = self.db.query(AuditFindingORM).filter(
                AuditFindingORM.report_id == report.id
            ).all()
            
            # Group by severity
            findings_by_severity = {
                'high': [f for f in findings if f.severity == 'high'],
                'medium': [f for f in findings if f.severity == 'medium'],
                'low': [f for f in findings if f.severity == 'low']
            }
            
            # Calculate stats
            total_amount = sum(
                f.amount_involved for f in findings
                if f.amount_involved is not None
            )
            
            discussed_count = len([f for f in findings if f.discussed_in_parliament])
            response_rate = (discussed_count / len(findings)) * 100 if findings else 0
            
            # Get top entities
            entity_stats = self._calculate_entity_stats(findings)
            
            # Render template
            template = self.env.get_template('pages/ag_report.html')
            html = template.render(
                report=report,
                findings=findings,
                findings_by_severity=findings_by_severity,
                total_amount=total_amount,
                discussed_count=discussed_count,
                response_rate=response_rate,
                top_entities=entity_stats[:10]
            )
            
            # Write file
            output_path = self.output_dir / 'ag-reports' / f'{report.id}.html'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html)
    
    def generate_financial_oversight_dashboard(self):
        """Generate financial oversight dashboard"""
        analyzer = AccountabilityAnalyzer(self.db)
        report = analyzer.generate_financial_oversight_report()
        
        template = self.env.get_template('pages/financial_oversight.html')
        html = template.render(**report)
        
        output_path = self.output_dir / 'dashboards' / 'financial-oversight.html'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)
    
    def generate_constituency_representation_pages(self):
        """Generate constituency representation pages"""
        # Get all constituencies
        constituencies = self.db.query(MPORM.constituency).distinct().all()
        
        analyzer = AccountabilityAnalyzer(self.db)
        
        for (constituency,) in constituencies:
            score = analyzer.calculate_constituency_representation(constituency)
            
            template = self.env.get_template('pages/constituency_representation.html')
            html = template.render(score=score)
            
            output_path = self.output_dir / 'constituencies' / f'{constituency.lower().replace(" ", "-")}.html'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html)
```

### Correctness Properties

**Property 8.1**: Page generation completeness
- **Validates**: Requirements 9.1.1-9.5.3
- **Property**: All tracker documents and reports must have pages
- **Test Strategy**: Count generated pages, compare with database records

**Property 8.2**: Dashboard accuracy
- **Validates**: Requirements 9.5.1-9.5.3
- **Property**: Dashboard metrics must match database calculations
- **Test Strategy**: Manual verification of dashboard data

---

## Design 9: Cost Management for Increased Volume

### Component Design

**Purpose**: Manage costs with increased document volume and LLM usage

**Technology**: Caching + batch processing + selective LLM usage

**Builds On**: Phase 1 cost manager

### Implementation

```python
class Phase4CostManager:
    """Manage costs for Phase 4"""
    
    def __init__(self, config):
        self.config = config
        self.monthly_budget = Decimal('60.00')
        self.cache = {}
    
    def should_use_llm(self, document_type: str, text: str) -> bool:
        """Decide if LLM analysis is needed"""
        # Check cache first
        cache_key = self._generate_cache_key(text)
        if cache_key in self.cache:
            return False  # Use cached result
        
        # Selective LLM usage
        if document_type in ['statements_tracker', 'motions_tracker', 'bills_tracker']:
            # Trackers are mostly structured data, minimal LLM needed
            return False
        
        if document_type == 'auditor_general_report':
            # Only use LLM for categorization, not extraction
            return True
        
        if document_type == 'order_paper':
            # Order Papers are structured, no LLM needed
            return False
        
        if document_type == 'legislative_proposal':
            # Use LLM for topic categorization
            return True
        
        return False
    
    def estimate_monthly_cost(self) -> Dict[str, Decimal]:
        """Estimate monthly costs"""
        # Estimate document volumes
        hansard_docs = 40  # 20 per chamber per month
        votes_docs = 20  # 10 per chamber per month
        bills = 10  # 5 per chamber per month
        questions = 8  # 4 per chamber per month
        petitions = 4  # 2 per chamber per month
        trackers = 12  # 6 types × 2 chambers per month
        ag_reports = 1  # Quarterly
        order_papers = 40  # 20 per chamber per month
        proposals = 2  # 1 per chamber per month
        
        # LLM usage estimates
        llm_costs = {
            'hansard': Decimal('15.00'),  # From Phase 1
            'votes': Decimal('0.00'),  # No LLM
            'bills': Decimal('5.00'),  # From Phase 2
            'questions': Decimal('3.00'),  # From Phase 2
            'petitions': Decimal('2.00'),  # From Phase 2
            'trackers': Decimal('0.00'),  # Structured data, no LLM
            'ag_reports': Decimal('10.00'),  # Finding categorization
            'order_papers': Decimal('0.00'),  # Structured data, no LLM
            'proposals': Decimal('2.00'),  # Topic categorization
        }
        
        total_llm = sum(llm_costs.values())
        
        # Infrastructure costs
        infrastructure = Decimal('10.00')  # Lambda + misc
        
        # Total
        total = total_llm + infrastructure
        
        return {
            'llm_costs': llm_costs,
            'total_llm': total_llm,
            'infrastructure': infrastructure,
            'total': total,
            'budget': self.monthly_budget,
            'remaining': self.monthly_budget - total
        }
```

### Correctness Properties

**Property 9.1**: Budget compliance
- **Validates**: Requirements 11.1.1
- **Property**: Monthly costs must not exceed $60
- **Test Strategy**: Track actual costs for one month, verify ≤$60

**Property 9.2**: Cache effectiveness
- **Validates**: Requirements 11.2.2
- **Property**: Cache hit rate must be ≥50%
- **Test Strategy**: Monitor cache hits vs misses over one week

---

## Summary

### Design Components

| Design | Component | Technology | Builds On |
|--------|-----------|------------|-----------|
| 1 | Database Schema Extensions | SQLAlchemy + Alembic | Phase 0-3 schema |
| 2 | Tracker Document Scrapers | BeautifulSoup + requests | Phase 0 scrapers |
| 3 | Tracker Document Processors | PyPDF2 + tabula-py | Phase 0 PDF processor |
| 4 | AG Report Analyzer | spaCy NER + LLM | Phase 1 LLM analyzer |
| 5 | Order Paper Parser | PyPDF2 + pattern matching | Phase 0 PDF processor |
| 6 | Enhanced Correlation Engine | Vector similarity + DB queries | Phase 2 correlation |
| 7 | Accountability Analytics | Pandas + custom analytics | Phase 3 analyzer |
| 8 | Enhanced Site Generation | Jinja2 templates | Phase 3 site generator |
| 9 | Cost Management | Caching + selective LLM | Phase 1 cost manager |

### Property-Based Tests

**18 Properties** to validate:
- Database schema: 2 properties
- Tracker scrapers: 2 properties
- Tracker processors: 2 properties
- AG report analyzer: 2 properties
- Order Paper parser: 2 properties
- Correlation engine: 2 properties
- Accountability analytics: 2 properties
- Site generation: 2 properties
- Cost management: 2 properties

### Key Features

**New Document Types** (6 per chamber = 12 total):
1. Statements Tracker
2. Motions Tracker
3. Bills Tracker
4. Legislative Proposals
5. Auditor General Reports (not chamber-specific)
6. Order Papers

**New Analytics**:
- Constituency representation scoring
- Financial oversight tracking
- Legislative efficiency metrics
- Agenda execution tracking

**New Pages**:
- Tracker directory and detail pages
- AG report pages with finding details
- Financial oversight dashboard
- Legislative efficiency dashboard
- Constituency representation pages

### Performance Targets

- Tracker processing: <5 min per document
- AG report processing: <30 min per document
- Order Paper processing: <3 min per document
- Full site generation: <45 min
- Database queries: <100ms

### Cost Targets

- Total monthly cost: ≤$60
- LLM costs: ≤$40/month
- Infrastructure: ≤$20/month
- Cache hit rate: ≥50%

### Completion Criteria

Phase 4 design is complete when:
- ✓ All 9 component designs documented
- ✓ All 18 properties defined
- ✓ All data models specified
- ✓ All algorithms described
- ✓ All templates designed
- ✓ Performance targets defined
- ✓ Cost estimates validated
- ✓ Ready for task breakdown

