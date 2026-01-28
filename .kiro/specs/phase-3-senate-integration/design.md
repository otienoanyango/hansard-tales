# Phase 3: Senate Integration - Design

## Introduction

This document provides detailed component designs for Phase 3 of the Hansard Tales system. It extends all Phase 1 and Phase 2 functionality to the Senate chamber, enabling comprehensive bicameral parliamentary tracking.

**Design Principles**:
- **Reuse Everything**: Leverage all Phase 1 and Phase 2 components with chamber parameter
- **Chamber Isolation**: Ensure complete separation between National Assembly and Senate data
- **Bicameral Tracking**: Enable sophisticated cross-chamber bill tracking and analysis
- **Cost Management**: Stay within $50/month budget through efficient caching and batching
- **Performance**: Maintain acceptable processing times despite doubled volume

**Phase 3 Goals**:
- Process all Senate document types (Hansard, Votes, Bills, Questions, Petitions)
- Generate comprehensive Senator profiles
- Enable bicameral bill tracking (bills moving between chambers)
- Track joint committee activities
- Enable cross-chamber analysis and comparison
- Generate Senate-specific pages and dashboards

## System Architecture

### Phase 3 Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  Chamber-Agnostic Processing Core                │
│  (Reused from Phase 1 & 2 with chamber parameter)               │
│                                                                  │
│  MP/Senator Identifier → Statement Segmenter → Filler Detector  │
│  → Context Retriever → LLM Analyzer → Citation Verifier         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Senate Document Scrapers                        │
│                                                                  │
│  Senate Hansard → Senate Votes → Senate Bills                   │
│  → Senate Questions → Senate Petitions                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Bicameral Tracking Engine                       │
│                                                                  │
│  Cross-Chamber Bill Tracker → Joint Committee Tracker           │
│  → Bill Version Comparator → Vote Correlator                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Cross-Chamber Analysis                          │
│                                                                  │
│  Chamber Comparison → Party Position Analysis                   │
│  → Legislative Efficiency Metrics                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Enhanced Site Generation                        │
│                                                                  │
│  Senator Profiles → Senate Pages → Bicameral Bill Pages         │
│  → County Representation Pages → Joint Committee Pages          │
└─────────────────────────────────────────────────────────────────┘
```


## Design 1: Database Schema Extensions for Senate

### Component Design

**Purpose**: Extend Phase 0 database schema to support Senate data and bicameral tracking

**Technology**: SQLAlchemy + Alembic migrations

**Builds On**: Phase 0 database schema

### Schema Changes

**1. Senators Table** (extends MPs table pattern):
```python
class SenatorORM(Base):
    """Senators table (similar to MPs but with Senate-specific fields)"""
    __tablename__ = "senators"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    party = Column(String(100))
    county = Column(String(100), nullable=False)  # Senate represents counties
    category = Column(SQLEnum(SenatorCategory), nullable=False)  # elected, nominated, ex-officio
    parliament_term = Column(Integer, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_senators_county', 'county'),
        Index('idx_senators_term', 'parliament_term'),
        Index('idx_senators_name', 'name'),
    )

class SenatorCategory(enum.Enum):
    """Senator category"""
    ELECTED = "elected"  # 47 elected (one per county)
    NOMINATED = "nominated"  # 16 nominated
    EX_OFFICIO = "ex_officio"  # 4 ex-officio (Speaker + Deputy Speakers)
```

**2. Cross-Chamber Bills Table**:
```python
class CrossChamberBillORM(Base):
    """Track bills moving between chambers"""
    __tablename__ = "cross_chamber_bills"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bill_id = Column(PGUUID(as_uuid=True), ForeignKey('bills.id'), nullable=False)
    originating_chamber = Column(SQLEnum(ChamberEnum), nullable=False)
    receiving_chamber = Column(SQLEnum(ChamberEnum), nullable=False)
    transmission_date = Column(Date, nullable=False)
    status_in_receiving_chamber = Column(String(50), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Relationships
    bill = relationship("BillORM", backref="cross_chamber_tracking")
    
    # Indexes
    __table_args__ = (
        Index('idx_cross_chamber_bill_id', 'bill_id'),
        Index('idx_cross_chamber_chambers', 'originating_chamber', 'receiving_chamber'),
    )
```

**3. Joint Committees Table**:
```python
class JointCommitteeORM(Base):
    """Joint committees with members from both chambers"""
    __tablename__ = "joint_committees"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    mandate = Column(Text)
    
    # Members (JSON arrays of MP/Senator IDs)
    mp_members = Column(JSON, default=[])
    senator_members = Column(JSON, default=[])
    
    # Chairperson
    chairperson_id = Column(PGUUID(as_uuid=True))
    chairperson_chamber = Column(SQLEnum(ChamberEnum))
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_joint_committees_name', 'name'),
    )
```

### Migration Strategy

```python
# alembic/versions/003_add_senate_support.py
def upgrade():
    # Create senators table
    op.create_table(
        'senators',
        sa.Column('id', PGUUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('party', sa.String(100)),
        sa.Column('county', sa.String(100), nullable=False),
        sa.Column('category', sa.Enum(SenatorCategory), nullable=False),
        sa.Column('parliament_term', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Create cross_chamber_bills table
    op.create_table(
        'cross_chamber_bills',
        # ... columns
    )
    
    # Create joint_committees table
    op.create_table(
        'joint_committees',
        # ... columns
    )
    
    # Add indexes
    op.create_index('idx_senators_county', 'senators', ['county'])
    # ... more indexes

def downgrade():
    op.drop_table('joint_committees')
    op.drop_table('cross_chamber_bills')
    op.drop_table('senators')
```

### Correctness Properties

**Property 1.1**: Chamber isolation
- **Validates**: Requirements 1.3.6
- **Property**: No data contamination between chambers
- **Test Strategy**: Query all documents, verify chamber field matches expected chamber

**Property 1.2**: Senator uniqueness
- **Validates**: Requirements 1.2.6
- **Property**: Each Senator appears once per term
- **Test Strategy**: Check for duplicate Senator records in same term



## Design 2: Chamber-Agnostic Component Refactoring

### Component Design

**Purpose**: Refactor Phase 1 and Phase 2 components to accept chamber parameter

**Technology**: Python refactoring + dependency injection

**Builds On**: All Phase 1 and Phase 2 components

### Refactoring Strategy

**Before (Phase 1 - National Assembly only)**:
```python
class MPIdentifier:
    def __init__(self, db_session):
        self.db = db_session
        self.mp_cache = self._load_mp_cache()
    
    def _load_mp_cache(self) -> dict:
        mps = self.db.query(MPORM).filter(
            MPORM.chamber == 'national_assembly'
        ).all()
        # ... build cache
```

**After (Phase 3 - Chamber-agnostic)**:
```python
class ParliamentarianIdentifier:
    """Identify MPs or Senators based on chamber"""
    
    def __init__(self, db_session, chamber: Chamber):
        self.db = db_session
        self.chamber = chamber
        self.cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        if self.chamber == Chamber.NATIONAL_ASSEMBLY:
            members = self.db.query(MPORM).all()
        else:  # Chamber.SENATE
            members = self.db.query(SenatorORM).all()
        
        # Build cache (same logic for both)
        cache = {}
        for member in members:
            cache[member.name.lower()] = member
        return cache
    
    def identify(self, text: str, context: Optional[dict] = None) -> Optional[MemberMatch]:
        """Identify MP or Senator from text mention"""
        # Same logic as before, works for both chambers
        # ...
```

### Component Refactoring Checklist

**Phase 1 Components to Refactor**:
- ✅ MPIdentifier → ParliamentarianIdentifier (chamber parameter)
- ✅ StatementSegmenter (already chamber-agnostic)
- ✅ FillerDetector (already chamber-agnostic)
- ✅ ContextRetriever (add chamber filter to queries)
- ✅ LLMAnalyzer (already chamber-agnostic)
- ✅ CitationVerifier (already chamber-agnostic)
- ✅ VoteProcessor (add chamber parameter)

**Phase 2 Components to Refactor**:
- ✅ BillScraper (add chamber parameter to URLs)
- ✅ BillTextExtractor (already chamber-agnostic)
- ✅ BillVersionTracker (already chamber-agnostic)
- ✅ BillSummarizer (already chamber-agnostic)
- ✅ QuestionScraper (add chamber parameter to URLs)
- ✅ QuestionAnswerPairer (already chamber-agnostic)
- ✅ PetitionScraper (add chamber parameter to URLs)
- ✅ PetitionProcessor (already chamber-agnostic)
- ✅ CorrelationEngine (add chamber filter to queries)

### Implementation Example

```python
class ChamberAwareProcessor:
    """Base class for chamber-aware processing"""
    
    def __init__(self, chamber: Chamber, config):
        self.chamber = chamber
        self.config = config
        
        # Initialize chamber-specific components
        self.member_identifier = ParliamentarianIdentifier(
            db_session=self.db,
            chamber=chamber
        )
        
        self.scraper = self._get_scraper()
    
    def _get_scraper(self):
        """Get chamber-specific scraper"""
        if self.chamber == Chamber.NATIONAL_ASSEMBLY:
            return NationalAssemblyScraper(self.config)
        else:
            return SenateScraper(self.config)
    
    def process_document(self, doc_path: Path):
        """Process document for specific chamber"""
        # Extract text
        text = self._extract_text(doc_path)
        
        # Segment statements
        statements = self.member_identifier.segment(text)
        
        # Process each statement
        for statement in statements:
            # Identify member (MP or Senator)
            member = self.member_identifier.identify(statement.text)
            
            # Store with chamber tag
            self._store_statement(statement, member, self.chamber)
```

### Correctness Properties

**Property 2.1**: Chamber parameter propagation
- **Validates**: Requirements 1.3.5
- **Property**: Chamber parameter must be passed to all sub-components
- **Test Strategy**: Trace chamber parameter through call stack, verify consistency

**Property 2.2**: No cross-chamber contamination
- **Validates**: Requirements 1.3.6
- **Property**: National Assembly processor must not access Senate data
- **Test Strategy**: Process NA document, verify no Senate queries executed



## Design 3: Senate Document Scrapers

### Component Design

**Purpose**: Scrape all Senate documents from parliament website

**Technology**: BeautifulSoup + requests (reuse Phase 0/2 scraper infrastructure)

**Builds On**: Phase 0 BaseScraper, Phase 2 document scrapers

### Senate URL Patterns

Senate documents follow similar patterns to National Assembly but with different base URLs:
- **Hansard**: `parliament.go.ke/the-senate/house-business/hansard`
- **Votes**: `parliament.go.ke/the-senate/house-business/votes-and-proceedings`
- **Bills**: `parliament.go.ke/the-senate/house-business/bills`
- **Questions**: `parliament.go.ke/the-senate/house-business/questions`
- **Petitions**: `parliament.go.ke/the-senate/house-business/petitions`

### Implementation

```python
class SenateScraper(BaseScraper):
    """Base scraper for Senate documents"""
    
    def __init__(self, config):
        super().__init__(config)
        self.chamber = Chamber.SENATE
        self.base_url = f"{config.scraper.base_url}/the-senate"
    
    def get_chamber_specific_url(self, document_type: str) -> str:
        """Get Senate-specific URL for document type"""
        return f"{self.base_url}/house-business/{document_type}"

class SenateHansardScraper(SenateScraper):
    """Scrape Senate Hansard documents"""
    
    def discover_hansard(self, date_range: Optional[Tuple[date, date]] = None) -> List[HansardMetadata]:
        """Discover Senate Hansard documents"""
        url = self.get_chamber_specific_url("hansard")
        
        # Reuse National Assembly scraper logic with Senate URL
        response = self.session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find Hansard links (same pattern as NA)
        hansard_links = soup.find_all('a', href=re.compile(r'/hansard/.*\.pdf'))
        
        hansards = []
        for link in hansard_links:
            metadata = self._extract_hansard_metadata(link)
            if metadata:
                metadata.chamber = Chamber.SENATE  # Tag as Senate
                hansards.append(metadata)
        
        return hansards

class SenateVotesScraper(SenateScraper):
    """Scrape Senate Votes & Proceedings"""
    
    def discover_votes(self, date_range: Optional[Tuple[date, date]] = None) -> List[VoteMetadata]:
        """Discover Senate voting records"""
        url = self.get_chamber_specific_url("votes-and-proceedings")
        
        # Reuse NA scraper logic with Senate URL
        # ... similar to SenateHansardScraper

class SenateBillsScraper(SenateScraper):
    """Scrape Senate bills"""
    
    def discover_bills(self) -> List[BillMetadata]:
        """Discover Senate bills"""
        url = self.get_chamber_specific_url("bills")
        
        # Senate bills include:
        # 1. Senate-originated bills
        # 2. National Assembly bills under Senate review
        
        bills = []
        
        # Scrape Senate bills page
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        bill_links = soup.find_all('a', href=re.compile(r'/bills/.*\.pdf'))
        
        for link in bill_links:
            metadata = self._extract_bill_metadata(link)
            if metadata:
                # Determine if Senate-originated or NA bill under review
                metadata.chamber = self._determine_bill_chamber(metadata)
                bills.append(metadata)
        
        return bills
    
    def _determine_bill_chamber(self, metadata: BillMetadata) -> Chamber:
        """Determine if bill originated in Senate or NA"""
        # Check bill text or metadata for originating chamber
        # Senate bills typically have "Senate Bill" in title
        if "Senate Bill" in metadata.title:
            return Chamber.SENATE
        
        # Check if bill is under review from NA
        if "under review" in metadata.title.lower():
            return Chamber.NATIONAL_ASSEMBLY  # Originated in NA
        
        # Default to Senate
        return Chamber.SENATE

class SenateQuestionsScraper(SenateScraper):
    """Scrape Senate questions"""
    
    def discover_questions(self, date_range: Optional[Tuple[date, date]] = None) -> List[QuestionMetadata]:
        """Discover Senate questions"""
        url = self.get_chamber_specific_url("questions")
        # Reuse NA scraper logic with Senate URL
        # ...

class SenatePetitionsScraper(SenateScraper):
    """Scrape Senate petitions"""
    
    def discover_petitions(self) -> List[PetitionMetadata]:
        """Discover Senate petitions"""
        url = self.get_chamber_specific_url("petitions")
        # Reuse NA scraper logic with Senate URL
        # ...
```

### Scraper Factory Pattern

```python
class ScraperFactory:
    """Factory for creating chamber-specific scrapers"""
    
    @staticmethod
    def create_hansard_scraper(chamber: Chamber, config) -> BaseScraper:
        """Create Hansard scraper for chamber"""
        if chamber == Chamber.NATIONAL_ASSEMBLY:
            return NationalAssemblyHansardScraper(config)
        else:
            return SenateHansardScraper(config)
    
    @staticmethod
    def create_votes_scraper(chamber: Chamber, config) -> BaseScraper:
        """Create Votes scraper for chamber"""
        if chamber == Chamber.NATIONAL_ASSEMBLY:
            return NationalAssemblyVotesScraper(config)
        else:
            return SenateVotesScraper(config)
    
    # ... similar for other document types
```

### Correctness Properties

**Property 3.1**: Senate URL correctness
- **Validates**: Requirements 2.1.4
- **Property**: All Senate URLs must point to Senate section
- **Test Strategy**: Verify all discovered URLs contain "/the-senate/"

**Property 3.2**: Chamber tagging
- **Validates**: Requirements 1.3.1
- **Property**: All Senate documents must be tagged with Senate chamber
- **Test Strategy**: Verify chamber field for all scraped documents



## Design 4: Bicameral Bill Tracking

### Component Design

**Purpose**: Track bills as they move between National Assembly and Senate

**Technology**: Custom tracking engine + database triggers

**Builds On**: Phase 2 bill tracking

### Bicameral Bill Lifecycle

```
National Assembly Bill:
1. Introduced in NA → First Reading (NA) → Second Reading (NA)
2. Committee Stage (NA) → Third Reading (NA) → Passed (NA)
3. Transmitted to Senate → First Reading (Senate) → Second Reading (Senate)
4. Committee Stage (Senate) → Third Reading (Senate) → Passed/Amended (Senate)
5. If amended: Return to NA for concurrence
6. Presidential Assent → Enacted

Senate Bill:
1. Introduced in Senate → ... → Passed (Senate)
2. Transmitted to NA → ... → Passed/Amended (NA)
3. If amended: Return to Senate for concurrence
4. Presidential Assent → Enacted
```

### Implementation

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class BillTransmissionStatus(Enum):
    """Status of bill in receiving chamber"""
    RECEIVED = "received"
    FIRST_READING = "first_reading"
    SECOND_READING = "second_reading"
    COMMITTEE = "committee"
    THIRD_READING = "third_reading"
    PASSED = "passed"
    AMENDED = "amended"
    REJECTED = "rejected"

@dataclass
class BillTransmission:
    """Record of bill transmission between chambers"""
    bill_id: str
    from_chamber: Chamber
    to_chamber: Chamber
    transmission_date: date
    status: BillTransmissionStatus
    amendments: Optional[List[str]] = None

class BicameralBillTracker:
    """Track bills across both chambers"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def track_transmission(
        self,
        bill_id: str,
        from_chamber: Chamber,
        to_chamber: Chamber,
        transmission_date: date
    ) -> BillTransmission:
        """Record bill transmission to other chamber"""
        # Create cross-chamber tracking record
        tracking = CrossChamberBillORM(
            bill_id=bill_id,
            originating_chamber=from_chamber,
            receiving_chamber=to_chamber,
            transmission_date=transmission_date,
            status_in_receiving_chamber=BillTransmissionStatus.RECEIVED.value
        )
        
        self.db.add(tracking)
        self.db.commit()
        
        return BillTransmission(
            bill_id=bill_id,
            from_chamber=from_chamber,
            to_chamber=to_chamber,
            transmission_date=transmission_date,
            status=BillTransmissionStatus.RECEIVED
        )
    
    def update_status(
        self,
        bill_id: str,
        receiving_chamber: Chamber,
        new_status: BillTransmissionStatus
    ):
        """Update bill status in receiving chamber"""
        tracking = self.db.query(CrossChamberBillORM).filter(
            CrossChamberBillORM.bill_id == bill_id,
            CrossChamberBillORM.receiving_chamber == receiving_chamber
        ).first()
        
        if tracking:
            tracking.status_in_receiving_chamber = new_status.value
            tracking.updated_at = datetime.utcnow()
            self.db.commit()
    
    def get_bill_timeline(self, bill_id: str) -> List[Dict]:
        """Get complete timeline of bill across both chambers"""
        bill = self.db.query(BillORM).filter(BillORM.id == bill_id).first()
        
        timeline = []
        
        # Add originating chamber events
        timeline.extend(self._get_chamber_events(bill, bill.chamber))
        
        # Add transmission events
        transmissions = self.db.query(CrossChamberBillORM).filter(
            CrossChamberBillORM.bill_id == bill_id
        ).all()
        
        for trans in transmissions:
            timeline.append({
                'date': trans.transmission_date,
                'event': 'Transmitted',
                'chamber': trans.receiving_chamber.value,
                'details': f"Transmitted from {trans.originating_chamber.value}"
            })
            
            # Add receiving chamber events
            timeline.extend(self._get_chamber_events(bill, trans.receiving_chamber))
        
        # Sort by date
        timeline.sort(key=lambda x: x['date'])
        
        return timeline
    
    def _get_chamber_events(self, bill: BillORM, chamber: Chamber) -> List[Dict]:
        """Get bill events in specific chamber"""
        events = []
        
        # Get votes in this chamber
        votes = self.db.query(VoteORM).filter(
            VoteORM.bill_id == bill.id,
            VoteORM.chamber == chamber
        ).all()
        
        for vote in votes:
            events.append({
                'date': vote.vote_date,
                'event': 'Vote',
                'chamber': chamber.value,
                'details': f"{vote.vote_type}: {vote.result}"
            })
        
        # Get statements in this chamber
        statements = self.db.query(StatementORM).filter(
            StatementORM.related_bill_ids.contains([str(bill.id)])
        ).join(MPORM).filter(
            MPORM.chamber == chamber
        ).all()
        
        for stmt in statements[:5]:  # Limit to 5 most recent
            events.append({
                'date': stmt.created_at.date(),
                'event': 'Debate',
                'chamber': chamber.value,
                'details': f"Discussed by {stmt.mp.name}"
            })
        
        return events
    
    def identify_bicameral_bills(self) -> List[str]:
        """Identify all bills that have moved between chambers"""
        transmissions = self.db.query(CrossChamberBillORM).all()
        return [str(t.bill_id) for t in transmissions]
    
    def compare_versions_across_chambers(
        self,
        bill_id: str
    ) -> Dict[str, any]:
        """Compare bill versions between chambers"""
        bill = self.db.query(BillORM).filter(BillORM.id == bill_id).first()
        
        # Get version from originating chamber
        originating_version = bill.versions[0]  # First version
        
        # Get version from receiving chamber (if exists)
        transmissions = self.db.query(CrossChamberBillORM).filter(
            CrossChamberBillORM.bill_id == bill_id
        ).all()
        
        if not transmissions:
            return {'has_cross_chamber_versions': False}
        
        # Get latest version (should be from receiving chamber)
        receiving_version = bill.versions[-1]  # Latest version
        
        # Generate diff
        from hansard_tales.processors.bill_version_tracker import BillVersionTracker
        tracker = BillVersionTracker(self.db)
        changes = tracker.generate_diff(
            originating_version.text,
            receiving_version.text
        )
        
        return {
            'has_cross_chamber_versions': True,
            'originating_chamber': bill.chamber.value,
            'originating_version': originating_version.version_number,
            'receiving_chamber': transmissions[0].receiving_chamber.value,
            'receiving_version': receiving_version.version_number,
            'changes': changes,
            'amendments_count': len(changes)
        }
```

### Correctness Properties

**Property 4.1**: Transmission tracking completeness
- **Validates**: Requirements 4.1.4
- **Property**: All bicameral bills must have transmission records
- **Test Strategy**: Query bills passed in both chambers, verify transmission records exist

**Property 4.2**: Timeline chronological order
- **Validates**: Requirements 4.2.6
- **Property**: Bill timeline events must be in chronological order
- **Test Strategy**: Generate timelines, verify dates are ascending



## Design 5: Senator Profile Generation

### Component Design

**Purpose**: Generate comprehensive Senator profiles with county representation tracking

**Technology**: Jinja2 templates + aggregation queries

**Builds On**: Phase 1 MP profile generation

### Senator Profile Data Model

```python
@dataclass
class SenatorProfile:
    """Complete Senator profile data"""
    # Basic info
    senator_id: str
    name: str
    party: str
    county: str
    category: SenatorCategory
    photo_url: Optional[str]
    contact_info: Dict[str, str]
    
    # Activity metrics
    total_statements: int
    substantive_statements: int
    average_quality_score: float
    
    # Topic distribution
    topics_discussed: List[Tuple[str, int]]  # (topic, count)
    
    # Voting record
    total_votes: int
    party_alignment_percentage: float
    votes_by_outcome: Dict[str, int]  # {'passed': 10, 'failed': 2}
    
    # Legislative activity
    bills_sponsored: List[Dict]
    bills_co_sponsored: List[Dict]
    questions_asked: List[Dict]
    petitions_sponsored: List[Dict]
    
    # Committee memberships
    committees: List[str]
    joint_committees: List[str]
    
    # County representation
    county_specific_statements: int
    county_specific_questions: int
    devolution_oversight_count: int
    
    # Recent activity
    recent_statements: List[Dict]
    recent_votes: List[Dict]

class SenatorProfileGenerator:
    """Generate Senator profiles"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def generate_profile(self, senator_id: str) -> SenatorProfile:
        """Generate complete profile for Senator"""
        senator = self.db.query(SenatorORM).filter(
            SenatorORM.id == senator_id
        ).first()
        
        if not senator:
            raise ValueError(f"Senator not found: {senator_id}")
        
        # Aggregate activity metrics
        statements = self._get_statements(senator_id)
        votes = self._get_votes(senator_id)
        bills = self._get_bills(senator_id)
        questions = self._get_questions(senator_id)
        petitions = self._get_petitions(senator_id)
        
        # Calculate metrics
        total_statements = len(statements)
        substantive_statements = len([s for s in statements if s.classification == 'substantive'])
        avg_quality = sum(s.quality_score or 0 for s in statements) / max(total_statements, 1)
        
        # Topic distribution
        topics = self._aggregate_topics(statements)
        
        # Voting record
        party_alignment = self._calculate_party_alignment(votes, senator.party)
        votes_by_outcome = self._aggregate_votes_by_outcome(votes)
        
        # County representation
        county_statements = self._count_county_specific(statements, senator.county)
        county_questions = self._count_county_specific_questions(questions, senator.county)
        devolution_count = self._count_devolution_oversight(statements)
        
        return SenatorProfile(
            senator_id=str(senator.id),
            name=senator.name,
            party=senator.party,
            county=senator.county,
            category=senator.category,
            photo_url=self._get_photo_url(senator),
            contact_info=self._get_contact_info(senator),
            total_statements=total_statements,
            substantive_statements=substantive_statements,
            average_quality_score=avg_quality,
            topics_discussed=topics,
            total_votes=len(votes),
            party_alignment_percentage=party_alignment,
            votes_by_outcome=votes_by_outcome,
            bills_sponsored=self._format_bills(bills['sponsored']),
            bills_co_sponsored=self._format_bills(bills['co_sponsored']),
            questions_asked=self._format_questions(questions),
            petitions_sponsored=self._format_petitions(petitions),
            committees=self._get_committees(senator_id),
            joint_committees=self._get_joint_committees(senator_id),
            county_specific_statements=county_statements,
            county_specific_questions=county_questions,
            devolution_oversight_count=devolution_count,
            recent_statements=self._format_recent_statements(statements[:10]),
            recent_votes=self._format_recent_votes(votes[:10])
        )
    
    def _count_county_specific(self, statements: List, county: str) -> int:
        """Count statements specifically about Senator's county"""
        count = 0
        county_lower = county.lower()
        
        for stmt in statements:
            if county_lower in stmt.text.lower():
                count += 1
        
        return count
    
    def _count_devolution_oversight(self, statements: List) -> int:
        """Count statements related to devolution oversight"""
        devolution_keywords = [
            'devolution', 'county government', 'county assembly',
            'county budget', 'county revenue', 'county services'
        ]
        
        count = 0
        for stmt in statements:
            text_lower = stmt.text.lower()
            if any(keyword in text_lower for keyword in devolution_keywords):
                count += 1
        
        return count
    
    def _get_joint_committees(self, senator_id: str) -> List[str]:
        """Get joint committees Senator is member of"""
        committees = self.db.query(JointCommitteeORM).filter(
            JointCommitteeORM.senator_members.contains([senator_id])
        ).all()
        
        return [c.name for c in committees]
    
    # ... other helper methods similar to MP profile generator
```

### County Representation Tracking

```python
class CountyRepresentationTracker:
    """Track how Senators represent their counties"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def generate_county_report(self, county: str) -> Dict:
        """Generate representation report for a county"""
        # Get Senator for county
        senator = self.db.query(SenatorORM).filter(
            SenatorORM.county == county
        ).first()
        
        if not senator:
            return {'error': f'No Senator found for {county}'}
        
        # Get all activity related to county
        statements = self._get_county_statements(senator.id, county)
        questions = self._get_county_questions(senator.id, county)
        petitions = self._get_county_petitions(county)
        
        return {
            'county': county,
            'senator': senator.name,
            'statements_count': len(statements),
            'questions_count': len(questions),
            'petitions_count': len(petitions),
            'top_issues': self._identify_top_issues(statements, questions),
            'recent_activity': self._format_recent_activity(statements, questions)
        }
    
    def _identify_top_issues(self, statements: List, questions: List) -> List[str]:
        """Identify top issues for county"""
        # Aggregate topics from statements and questions
        topics = {}
        
        for stmt in statements:
            for topic in stmt.topics:
                topics[topic] = topics.get(topic, 0) + 1
        
        for q in questions:
            for topic in q.topics:
                topics[topic] = topics.get(topic, 0) + 1
        
        # Sort by frequency
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        
        return [topic for topic, count in sorted_topics[:5]]
```

### Correctness Properties

**Property 5.1**: Profile completeness
- **Validates**: Requirements 6.1.7
- **Property**: All Senators must have complete profiles
- **Test Strategy**: Generate profiles for all Senators, verify all fields populated

**Property 5.2**: County attribution accuracy
- **Validates**: Requirements 6.2.5
- **Property**: County-specific metrics must be accurate
- **Test Strategy**: Manual review of 20 Senator profiles, verify county data



## Design 6: Cross-Chamber Analysis Engine

### Component Design

**Purpose**: Enable comparative analysis between National Assembly and Senate

**Technology**: Pandas for data aggregation + custom analysis algorithms

**Builds On**: Phase 1 and Phase 2 analysis components

### Implementation

```python
from dataclasses import dataclass
from typing import Dict, List
import pandas as pd

@dataclass
class ChamberComparison:
    """Comparison metrics between chambers"""
    metric_name: str
    national_assembly_value: float
    senate_value: float
    difference: float
    difference_percentage: float

class CrossChamberAnalyzer:
    """Analyze and compare chambers"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def generate_chamber_comparison(self) -> List[ChamberComparison]:
        """Generate comprehensive chamber comparison"""
        comparisons = []
        
        # Activity levels
        comparisons.append(self._compare_activity_levels())
        
        # Statement quality
        comparisons.append(self._compare_statement_quality())
        
        # Bill passage rates
        comparisons.append(self._compare_bill_passage_rates())
        
        # Voting patterns
        comparisons.append(self._compare_voting_patterns())
        
        # Topic distribution
        comparisons.extend(self._compare_topic_distribution())
        
        return comparisons
    
    def _compare_activity_levels(self) -> ChamberComparison:
        """Compare activity levels between chambers"""
        # Count statements per chamber
        na_statements = self.db.query(StatementORM).join(MPORM).filter(
            MPORM.chamber == Chamber.NATIONAL_ASSEMBLY
        ).count()
        
        senate_statements = self.db.query(StatementORM).join(SenatorORM).filter(
            SenatorORM.chamber == Chamber.SENATE
        ).count()
        
        difference = na_statements - senate_statements
        diff_pct = (difference / max(na_statements, 1)) * 100
        
        return ChamberComparison(
            metric_name="Total Statements",
            national_assembly_value=na_statements,
            senate_value=senate_statements,
            difference=difference,
            difference_percentage=diff_pct
        )
    
    def _compare_statement_quality(self) -> ChamberComparison:
        """Compare average statement quality"""
        # Get average quality score per chamber
        na_avg = self.db.query(
            func.avg(StatementORM.quality_score)
        ).join(MPORM).filter(
            MPORM.chamber == Chamber.NATIONAL_ASSEMBLY,
            StatementORM.quality_score.isnot(None)
        ).scalar() or 0
        
        senate_avg = self.db.query(
            func.avg(StatementORM.quality_score)
        ).join(SenatorORM).filter(
            SenatorORM.chamber == Chamber.SENATE,
            StatementORM.quality_score.isnot(None)
        ).scalar() or 0
        
        difference = na_avg - senate_avg
        diff_pct = (difference / max(na_avg, 1)) * 100
        
        return ChamberComparison(
            metric_name="Average Statement Quality",
            national_assembly_value=na_avg,
            senate_value=senate_avg,
            difference=difference,
            difference_percentage=diff_pct
        )
    
    def _compare_bill_passage_rates(self) -> ChamberComparison:
        """Compare bill passage rates"""
        # Count bills passed vs introduced per chamber
        na_introduced = self.db.query(BillORM).filter(
            BillORM.chamber == Chamber.NATIONAL_ASSEMBLY
        ).count()
        
        na_passed = self.db.query(BillORM).filter(
            BillORM.chamber == Chamber.NATIONAL_ASSEMBLY,
            BillORM.status.in_(['passed', 'enacted'])
        ).count()
        
        senate_introduced = self.db.query(BillORM).filter(
            BillORM.chamber == Chamber.SENATE
        ).count()
        
        senate_passed = self.db.query(BillORM).filter(
            BillORM.chamber == Chamber.SENATE,
            BillORM.status.in_(['passed', 'enacted'])
        ).count()
        
        na_rate = (na_passed / max(na_introduced, 1)) * 100
        senate_rate = (senate_passed / max(senate_introduced, 1)) * 100
        
        difference = na_rate - senate_rate
        diff_pct = (difference / max(na_rate, 1)) * 100
        
        return ChamberComparison(
            metric_name="Bill Passage Rate (%)",
            national_assembly_value=na_rate,
            senate_value=senate_rate,
            difference=difference,
            difference_percentage=diff_pct
        )
    
    def analyze_party_positions_across_chambers(self, party: str) -> Dict:
        """Analyze party positions in both chambers"""
        # Get party voting patterns in NA
        na_votes = self._get_party_votes(party, Chamber.NATIONAL_ASSEMBLY)
        
        # Get party voting patterns in Senate
        senate_votes = self._get_party_votes(party, Chamber.SENATE)
        
        # Compare alignment
        alignment = self._calculate_cross_chamber_alignment(na_votes, senate_votes)
        
        return {
            'party': party,
            'na_votes': len(na_votes),
            'senate_votes': len(senate_votes),
            'alignment_percentage': alignment,
            'divergent_bills': self._identify_divergent_bills(na_votes, senate_votes)
        }
    
    def _calculate_cross_chamber_alignment(
        self,
        na_votes: List,
        senate_votes: List
    ) -> float:
        """Calculate how often party votes same way in both chambers"""
        # Find bills voted on in both chambers
        na_bill_ids = {v.bill_id for v in na_votes}
        senate_bill_ids = {v.bill_id for v in senate_votes}
        common_bills = na_bill_ids & senate_bill_ids
        
        if not common_bills:
            return 0.0
        
        # Count agreements
        agreements = 0
        for bill_id in common_bills:
            na_vote = next(v for v in na_votes if v.bill_id == bill_id)
            senate_vote = next(v for v in senate_votes if v.bill_id == bill_id)
            
            # Check if party voted same way
            if na_vote.direction == senate_vote.direction:
                agreements += 1
        
        return (agreements / len(common_bills)) * 100
    
    def calculate_legislative_efficiency(self, chamber: Chamber) -> Dict:
        """Calculate legislative efficiency metrics for chamber"""
        # Get all bills for chamber
        bills = self.db.query(BillORM).filter(
            BillORM.chamber == chamber
        ).all()
        
        if not bills:
            return {'error': 'No bills found'}
        
        # Calculate average time to passage
        passage_times = []
        for bill in bills:
            if bill.status in ['passed', 'enacted']:
                # Calculate time from introduction to passage
                intro_date = bill.created_at.date()
                
                # Find passage vote
                passage_vote = self.db.query(VoteORM).filter(
                    VoteORM.bill_id == bill.id,
                    VoteORM.result == 'passed'
                ).order_by(VoteORM.vote_date.desc()).first()
                
                if passage_vote:
                    days = (passage_vote.vote_date - intro_date).days
                    passage_times.append(days)
        
        avg_passage_time = sum(passage_times) / len(passage_times) if passage_times else 0
        
        # Calculate amendment rate
        amended_bills = len([b for b in bills if len(b.versions) > 1])
        amendment_rate = (amended_bills / len(bills)) * 100
        
        # Calculate rejection rate
        rejected_bills = len([b for b in bills if b.status == 'rejected'])
        rejection_rate = (rejected_bills / len(bills)) * 100
        
        return {
            'chamber': chamber.value,
            'total_bills': len(bills),
            'average_passage_time_days': avg_passage_time,
            'amendment_rate_percentage': amendment_rate,
            'rejection_rate_percentage': rejection_rate
        }
```

### Correctness Properties

**Property 6.1**: Comparison accuracy
- **Validates**: Requirements 7.1.5
- **Property**: Chamber comparison metrics must be accurate
- **Test Strategy**: Manual calculation of metrics, compare with automated results

**Property 6.2**: Party alignment calculation
- **Validates**: Requirements 7.2.4
- **Property**: Party alignment percentage must be between 0-100
- **Test Strategy**: Verify all alignment percentages in valid range



## Design 7: Enhanced Static Site Generation

### Component Design

**Purpose**: Generate Senate-specific pages and bicameral bill pages

**Technology**: Jinja2 templates + static site generator (from Phase 1)

**Builds On**: Phase 1 site generator

### New Page Templates

**1. Senator Directory** (`templates/pages/senators_list.html`):
```html
{% extends "layouts/base.html" %}

{% block content %}
<div class="senators-directory">
    <h1>Senators of Kenya</h1>
    
    <!-- Filters -->
    <div class="filters">
        <select id="party-filter">
            <option value="">All Parties</option>
            {% for party in parties %}
            <option value="{{ party }}">{{ party }}</option>
            {% endfor %}
        </select>
        
        <select id="county-filter">
            <option value="">All Counties</option>
            {% for county in counties %}
            <option value="{{ county }}">{{ county }}</option>
            {% endfor %}
        </select>
        
        <select id="category-filter">
            <option value="">All Categories</option>
            <option value="elected">Elected</option>
            <option value="nominated">Nominated</option>
            <option value="ex_officio">Ex-Officio</option>
        </select>
    </div>
    
    <!-- Senator Grid -->
    <div class="senators-grid">
        {% for senator in senators %}
        <div class="senator-card" 
             data-party="{{ senator.party }}"
             data-county="{{ senator.county }}"
             data-category="{{ senator.category }}">
            <img src="{{ senator.photo_url }}" alt="{{ senator.name }}">
            <h3>{{ senator.name }}</h3>
            <p class="party">{{ senator.party }}</p>
            <p class="county">{{ senator.county }} County</p>
            <p class="category">{{ senator.category|title }}</p>
            <div class="stats">
                <span>{{ senator.total_statements }} statements</span>
                <span>Quality: {{ senator.average_quality_score|round(1) }}</span>
            </div>
            <a href="/senators/{{ senator.id }}.html">View Profile</a>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

**2. Senator Profile** (`templates/pages/senator_profile.html`):
```html
{% extends "layouts/base.html" %}

{% block content %}
<div class="senator-profile">
    <div class="profile-header">
        <img src="{{ senator.photo_url }}" alt="{{ senator.name }}">
        <div class="header-info">
            <h1>{{ senator.name }}</h1>
            <p class="party">{{ senator.party }}</p>
            <p class="county">{{ senator.county }} County</p>
            <p class="category">{{ senator.category|title }} Senator</p>
        </div>
    </div>
    
    <!-- Activity Overview -->
    <section class="activity-overview">
        <h2>Activity Overview</h2>
        <div class="metrics">
            <div class="metric">
                <span class="value">{{ senator.total_statements }}</span>
                <span class="label">Total Statements</span>
            </div>
            <div class="metric">
                <span class="value">{{ senator.substantive_statements }}</span>
                <span class="label">Substantive Statements</span>
            </div>
            <div class="metric">
                <span class="value">{{ senator.average_quality_score|round(1) }}</span>
                <span class="label">Avg Quality Score</span>
            </div>
            <div class="metric">
                <span class="value">{{ senator.total_votes }}</span>
                <span class="label">Votes Cast</span>
            </div>
        </div>
    </section>
    
    <!-- County Representation -->
    <section class="county-representation">
        <h2>County Representation</h2>
        <div class="county-metrics">
            <p>County-specific statements: {{ senator.county_specific_statements }}</p>
            <p>County-specific questions: {{ senator.county_specific_questions }}</p>
            <p>Devolution oversight activities: {{ senator.devolution_oversight_count }}</p>
        </div>
    </section>
    
    <!-- Legislative Activity -->
    <section class="legislative-activity">
        <h2>Legislative Activity</h2>
        
        <h3>Bills Sponsored ({{ senator.bills_sponsored|length }})</h3>
        <ul>
            {% for bill in senator.bills_sponsored %}
            <li>
                <a href="/bills/{{ bill.id }}.html">{{ bill.title }}</a>
                <span class="status">{{ bill.status }}</span>
            </li>
            {% endfor %}
        </ul>
        
        <h3>Questions Asked ({{ senator.questions_asked|length }})</h3>
        <ul>
            {% for question in senator.questions_asked[:10] %}
            <li>{{ question.question_text[:100] }}...</li>
            {% endfor %}
        </ul>
    </section>
    
    <!-- Committee Memberships -->
    <section class="committees">
        <h2>Committee Memberships</h2>
        <ul>
            {% for committee in senator.committees %}
            <li>{{ committee }}</li>
            {% endfor %}
        </ul>
        
        {% if senator.joint_committees %}
        <h3>Joint Committees</h3>
        <ul>
            {% for committee in senator.joint_committees %}
            <li>{{ committee }}</li>
            {% endfor %}
        </ul>
        {% endif %}
    </section>
    
    <!-- Recent Activity -->
    <section class="recent-activity">
        <h2>Recent Activity</h2>
        {% for statement in senator.recent_statements %}
        <div class="statement">
            <p class="date">{{ statement.date }}</p>
            <p class="text">{{ statement.text[:200] }}...</p>
            <a href="/sessions/{{ statement.session_id }}.html">View Full Statement</a>
        </div>
        {% endfor %}
    </section>
</div>
{% endblock %}
```

**3. Bicameral Bill Page** (`templates/pages/bicameral_bill.html`):
```html
{% extends "layouts/base.html" %}

{% block content %}
<div class="bicameral-bill">
    <h1>{{ bill.title }}</h1>
    <p class="bill-number">{{ bill.bill_number }}</p>
    
    <!-- Bicameral Status -->
    <section class="bicameral-status">
        <h2>Bicameral Progress</h2>
        <div class="chamber-status">
            <div class="chamber">
                <h3>{{ bill.originating_chamber|title }}</h3>
                <p class="status">{{ bill.status_in_originating }}</p>
                <p class="date">Passed: {{ bill.passage_date_originating }}</p>
            </div>
            <div class="transmission-arrow">→</div>
            <div class="chamber">
                <h3>{{ bill.receiving_chamber|title }}</h3>
                <p class="status">{{ bill.status_in_receiving }}</p>
                {% if bill.passage_date_receiving %}
                <p class="date">Passed: {{ bill.passage_date_receiving }}</p>
                {% endif %}
            </div>
        </div>
    </section>
    
    <!-- Timeline -->
    <section class="bill-timeline">
        <h2>Complete Timeline</h2>
        <div class="timeline">
            {% for event in bill.timeline %}
            <div class="timeline-event">
                <span class="date">{{ event.date }}</span>
                <span class="chamber">{{ event.chamber|title }}</span>
                <span class="event">{{ event.event }}</span>
                <p class="details">{{ event.details }}</p>
            </div>
            {% endfor %}
        </div>
    </section>
    
    <!-- Version Comparison -->
    {% if bill.has_amendments %}
    <section class="version-comparison">
        <h2>Amendments by {{ bill.receiving_chamber|title }}</h2>
        <p>{{ bill.amendments_count }} changes made</p>
        
        <div class="changes">
            {% for change in bill.changes %}
            <div class="change change-{{ change.type }}">
                <h4>{{ change.section }}</h4>
                {% if change.old_text %}
                <div class="old-text">
                    <strong>Original:</strong>
                    <p>{{ change.old_text }}</p>
                </div>
                {% endif %}
                {% if change.new_text %}
                <div class="new-text">
                    <strong>Amended:</strong>
                    <p>{{ change.new_text }}</p>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </section>
    {% endif %}
    
    <!-- Votes in Both Chambers -->
    <section class="votes">
        <h2>Voting Records</h2>
        
        <div class="chamber-votes">
            <div class="vote-record">
                <h3>{{ bill.originating_chamber|title }}</h3>
                <p>Ayes: {{ bill.vote_originating.ayes }}</p>
                <p>Noes: {{ bill.vote_originating.noes }}</p>
                <p>Result: {{ bill.vote_originating.result }}</p>
            </div>
            
            {% if bill.vote_receiving %}
            <div class="vote-record">
                <h3>{{ bill.receiving_chamber|title }}</h3>
                <p>Ayes: {{ bill.vote_receiving.ayes }}</p>
                <p>Noes: {{ bill.vote_receiving.noes }}</p>
                <p>Result: {{ bill.vote_receiving.result }}</p>
            </div>
            {% endif %}
        </div>
    </section>
    
    <!-- Debates in Both Chambers -->
    <section class="debates">
        <h2>Parliamentary Debates</h2>
        
        <h3>{{ bill.originating_chamber|title }} Debates</h3>
        {% for statement in bill.statements_originating %}
        <div class="statement">
            <p class="speaker">{{ statement.speaker_name }}</p>
            <p class="text">{{ statement.text[:200] }}...</p>
        </div>
        {% endfor %}
        
        <h3>{{ bill.receiving_chamber|title }} Debates</h3>
        {% for statement in bill.statements_receiving %}
        <div class="statement">
            <p class="speaker">{{ statement.speaker_name }}</p>
            <p class="text">{{ statement.text[:200] }}...</p>
        </div>
        {% endfor %}
    </section>
</div>
{% endblock %}
```

**4. County Representation Page** (`templates/pages/county.html`):
```html
{% extends "layouts/base.html" %}

{% block content %}
<div class="county-page">
    <h1>{{ county }} County</h1>
    
    <!-- Senator -->
    <section class="county-senator">
        <h2>Senator</h2>
        <div class="senator-card">
            <img src="{{ senator.photo_url }}" alt="{{ senator.name }}">
            <h3>{{ senator.name }}</h3>
            <p>{{ senator.party }}</p>
            <a href="/senators/{{ senator.id }}.html">View Profile</a>
        </div>
    </section>
    
    <!-- County Issues -->
    <section class="county-issues">
        <h2>Top Issues for {{ county }}</h2>
        <ul>
            {% for issue in top_issues %}
            <li>{{ issue }}</li>
            {% endfor %}
        </ul>
    </section>
    
    <!-- Recent Activity -->
    <section class="recent-activity">
        <h2>Recent Senate Activity for {{ county }}</h2>
        {% for activity in recent_activity %}
        <div class="activity">
            <p class="date">{{ activity.date }}</p>
            <p class="type">{{ activity.type }}</p>
            <p class="summary">{{ activity.summary }}</p>
        </div>
        {% endfor %}
    </section>
</div>
{% endblock %}
```

### Site Generator Implementation

```python
class EnhancedSiteGenerator:
    """Generate static site with Senate pages"""
    
    def __init__(self, db_session, template_dir: Path, output_dir: Path):
        self.db = db_session
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))
    
    def generate_all(self):
        """Generate complete site"""
        # Generate NA pages (from Phase 1)
        self.generate_mp_pages()
        self.generate_session_pages(Chamber.NATIONAL_ASSEMBLY)
        
        # Generate Senate pages (new)
        self.generate_senator_pages()
        self.generate_session_pages(Chamber.SENATE)
        
        # Generate bicameral pages (new)
        self.generate_bicameral_bill_pages()
        self.generate_county_pages()
        self.generate_joint_committee_pages()
        
        # Generate comparison pages (new)
        self.generate_chamber_comparison_page()
    
    def generate_senator_pages(self):
        """Generate all Senator profile pages"""
        senators = self.db.query(SenatorORM).all()
        
        for senator in senators:
            profile = SenatorProfileGenerator(self.db).generate_profile(str(senator.id))
            
            template = self.env.get_template('pages/senator_profile.html')
            html = template.render(senator=profile)
            
            output_path = self.output_dir / 'senators' / f'{senator.id}.html'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html)
    
    def generate_bicameral_bill_pages(self):
        """Generate pages for bicameral bills"""
        tracker = BicameralBillTracker(self.db)
        bicameral_bill_ids = tracker.identify_bicameral_bills()
        
        for bill_id in bicameral_bill_ids:
            bill_data = self._prepare_bicameral_bill_data(bill_id)
            
            template = self.env.get_template('pages/bicameral_bill.html')
            html = template.render(bill=bill_data)
            
            output_path = self.output_dir / 'bills' / f'{bill_id}.html'
            output_path.write_text(html)
    
    def generate_county_pages(self):
        """Generate pages for all 47 counties"""
        counties = self.db.query(SenatorORM.county).distinct().all()
        
        for (county,) in counties:
            county_data = CountyRepresentationTracker(self.db).generate_county_report(county)
            
            template = self.env.get_template('pages/county.html')
            html = template.render(**county_data)
            
            output_path = self.output_dir / 'counties' / f'{county.lower().replace(" ", "-")}.html'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html)
```

### Correctness Properties

**Property 7.1**: Page generation completeness
- **Validates**: Requirements 8.1-8.6
- **Property**: All Senators, bills, and counties must have pages
- **Test Strategy**: Count generated pages, compare with database records

**Property 7.2**: Link integrity
- **Validates**: Requirements 8.1.5
- **Property**: All internal links must point to existing pages
- **Test Strategy**: Crawl generated site, verify all links resolve



## Design 8: Performance Optimization for Doubled Volume

### Component Design

**Purpose**: Maintain acceptable performance with doubled data volume

**Technology**: Caching + batch processing + parallel execution

**Builds On**: Phase 1 and Phase 2 processing pipelines

### Optimization Strategies

**1. Aggressive Caching**:
```python
from functools import lru_cache
from cachetools import TTLCache
import hashlib

class CachedLLMAnalyzer:
    """LLM analyzer with aggressive caching"""
    
    def __init__(self, llm_analyzer: LLMAnalyzer):
        self.llm = llm_analyzer
        # Cache for 7 days
        self.cache = TTLCache(maxsize=10000, ttl=604800)
    
    def analyze(self, statement: Statement, context: Optional[RetrievedContext] = None) -> StatementAnalysis:
        """Analyze with caching"""
        # Generate cache key from statement text
        cache_key = self._generate_cache_key(statement.text)
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Call LLM
        analysis = self.llm.analyze(statement, context)
        
        # Store in cache
        self.cache[cache_key] = analysis
        
        return analysis
    
    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.sha256(text.encode()).hexdigest()
```

**2. Batch Processing**:
```python
class BatchProcessor:
    """Process documents in optimized batches"""
    
    def __init__(self, chamber: Chamber, batch_size: int = 50):
        self.chamber = chamber
        self.batch_size = batch_size
    
    def process_documents(self, document_ids: List[str]):
        """Process documents in batches"""
        # Group by document type for efficient processing
        grouped = self._group_by_type(document_ids)
        
        for doc_type, ids in grouped.items():
            # Process in batches
            for i in range(0, len(ids), self.batch_size):
                batch = ids[i:i + self.batch_size]
                self._process_batch(doc_type, batch)
    
    def _process_batch(self, doc_type: str, batch: List[str]):
        """Process a batch of documents"""
        if doc_type == 'hansard':
            self._process_hansard_batch(batch)
        elif doc_type == 'votes':
            self._process_votes_batch(batch)
        # ... other types
    
    def _process_hansard_batch(self, batch: List[str]):
        """Process Hansard batch with optimizations"""
        # Load all documents at once
        documents = self.db.query(DocumentORM).filter(
            DocumentORM.id.in_(batch)
        ).all()
        
        # Extract all statements
        all_statements = []
        for doc in documents:
            statements = self.segmenter.segment(doc.text)
            all_statements.extend(statements)
        
        # Batch LLM calls (10 at a time)
        for i in range(0, len(all_statements), 10):
            stmt_batch = all_statements[i:i + 10]
            analyses = self.llm.analyze_batch(stmt_batch)
            
            # Store results
            for stmt, analysis in zip(stmt_batch, analyses):
                self._store_statement(stmt, analysis)
```

**3. Parallel Processing**:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

class ParallelProcessor:
    """Process documents in parallel"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    def process_chambers_parallel(self):
        """Process both chambers in parallel"""
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both chambers
            na_future = executor.submit(
                self.process_chamber,
                Chamber.NATIONAL_ASSEMBLY
            )
            senate_future = executor.submit(
                self.process_chamber,
                Chamber.SENATE
            )
            
            # Wait for both to complete
            na_result = na_future.result()
            senate_result = senate_future.result()
        
        return {
            'national_assembly': na_result,
            'senate': senate_result
        }
    
    def process_chamber(self, chamber: Chamber):
        """Process all documents for a chamber"""
        # Get unprocessed documents
        documents = self._get_unprocessed_documents(chamber)
        
        # Process in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.process_document, doc): doc
                for doc in documents
            }
            
            results = []
            for future in as_completed(futures):
                doc = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to process {doc.id}: {e}")
        
        return results
```

**4. Database Query Optimization**:
```python
class OptimizedQueries:
    """Optimized database queries"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_statements_with_members(self, chamber: Chamber) -> List:
        """Get statements with member info in single query"""
        # Use eager loading to avoid N+1 queries
        if chamber == Chamber.NATIONAL_ASSEMBLY:
            return self.db.query(StatementORM).join(MPORM).options(
                joinedload(StatementORM.mp)
            ).filter(
                MPORM.chamber == chamber
            ).all()
        else:
            return self.db.query(StatementORM).join(SenatorORM).options(
                joinedload(StatementORM.senator)
            ).filter(
                SenatorORM.chamber == chamber
            ).all()
    
    def get_bills_with_related_data(self, chamber: Chamber) -> List:
        """Get bills with all related data in single query"""
        return self.db.query(BillORM).options(
            joinedload(BillORM.versions),
            joinedload(BillORM.votes),
            joinedload(BillORM.sponsor)
        ).filter(
            BillORM.chamber == chamber
        ).all()
```

**5. Incremental Processing**:
```python
class IncrementalProcessor:
    """Process only new/updated documents"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_documents_to_process(self, chamber: Chamber) -> List[str]:
        """Get only unprocessed or updated documents"""
        # Find documents without analysis
        unprocessed = self.db.query(DocumentORM.id).filter(
            DocumentORM.chamber == chamber,
            ~DocumentORM.statements.any()  # No statements yet
        ).all()
        
        # Find documents updated since last processing
        updated = self.db.query(DocumentORM.id).filter(
            DocumentORM.chamber == chamber,
            DocumentORM.updated_at > DocumentORM.last_processed_at
        ).all()
        
        return [str(doc_id) for (doc_id,) in unprocessed + updated]
    
    def mark_processed(self, document_id: str):
        """Mark document as processed"""
        doc = self.db.query(DocumentORM).filter(
            DocumentORM.id == document_id
        ).first()
        
        if doc:
            doc.last_processed_at = datetime.utcnow()
            self.db.commit()
```

### Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Hansard processing | <10 min per document | Batch LLM calls, parallel processing |
| Vote processing | <2 min per document | Efficient table extraction |
| Bill processing | <5 min per bill | Cache summaries, incremental updates |
| Full site generation | <30 min | Parallel page generation, template caching |
| Database queries | <100ms per query | Indexes, eager loading, query optimization |
| Memory usage | <8GB | Streaming processing, garbage collection |

### Correctness Properties

**Property 8.1**: Processing completeness
- **Validates**: Requirements 9.1.7
- **Property**: All documents must be processed despite optimizations
- **Test Strategy**: Count processed documents, verify matches total

**Property 8.2**: Cache correctness
- **Validates**: Requirements 9.3.2
- **Property**: Cached results must match non-cached results
- **Test Strategy**: Process same document with/without cache, verify identical results

