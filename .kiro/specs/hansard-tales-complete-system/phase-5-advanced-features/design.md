# Phase 5: Advanced Features - Design

## Introduction

This document provides detailed component designs for Phase 5 of the Hansard Tales system. Phase 5 adds advanced content features, performance optimizations, optional API layer, and enhanced user experience, completing the full product.

**Design Principles**:
- **Content Quality**: Prioritize accuracy and verifiability over volume
- **Performance**: Optimize for production scale and user experience
- **Accessibility**: Ensure platform is usable by all citizens
- **Extensibility**: Design for future enhancements
- **Cost Efficiency**: Maintain $60/month budget
- **User-Centric**: Focus on features that provide maximum value

**Phase 5 Goals**:
- Automate weekly parliament summaries
- Generate engaging historical content
- Enable advanced party position analysis
- Provide comprehensive search functionality
- Offer optional REST API for developers
- Enable data export for researchers
- Optimize performance for production
- Polish user experience

## System Architecture

### Phase 5 Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              Complete Processing Infrastructure                  │
│  (All Phase 0-4 components operational)                         │
│                                                                  │
│  22 Document Types → Processing → Analysis → Storage           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Content Generation Engine                       │
│                                                                  │
│  Weekly Summary Generator → Historical Content Generator        │
│  → Party Position Analyzer → Trend Analyzer                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Advanced Search System                          │
│                                                                  │
│  Full-Text Search (Lunr.js) → Semantic Search (Vector DB)      │
│  → Filtered Search → Search Index Generator                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  REST API Layer (Optional)                       │
│                                                                  │
│  FastAPI → Endpoints → Authentication → Rate Limiting           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Data Export System                              │
│                                                                  │
│  CSV Exporter → JSON Exporter → Excel Exporter → PDF Exporter  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Performance Optimization Layer                  │
│                                                                  │
│  Connection Pooling → Query Caching → Parallel Processing      │
│  → Incremental Updates → Asset Optimization                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Design 1: Weekly Parliament Summary Generator

### Component Design

**Purpose**: Automatically generate engaging weekly summaries of parliamentary activities

**Technology**: LLM (Claude 3.5 Haiku) + aggregation queries + citation verification

**Builds On**: Phase 1 LLM analyzer, Phase 4 accountability analytics

### Implementation

```python
from dataclasses import dataclass
from typing import List, Dict
from datetime import date, timedelta

@dataclass
class WeeklySummary:
    """Weekly parliament summary"""
    week_start: date
    week_end: date
    chamber: Chamber
    
    # Narrative summary
    summary_text: str  # 2-3 paragraphs
    
    # Key events
    bills_discussed: List[Dict]
    major_votes: List[Dict]
    important_statements: List[Dict]
    questions_answered: List[Dict]
    
    # Highlights
    controversial_debates: List[Dict]
    notable_quotes: List[Dict]
    most_active_members: List[Dict]
    
    # Statistics
    sitting_days: int
    total_statements: int
    bills_progressed: int
    votes_held: int
    
    # Citations
    source_documents: List[str]

class WeeklySummaryGenerator:
    """Generate weekly parliament summaries"""
    
    def __init__(self, db_session, llm_analyzer, citation_verifier):
        self.db = db_session
        self.llm = llm_analyzer
        self.citation_verifier = citation_verifier
    
    def generate_weekly_summary(
        self,
        week_start: date,
        chamber: Chamber
    ) -> WeeklySummary:
        """Generate summary for a week"""
        week_end = week_start + timedelta(days=6)
        
        # Aggregate week's activities
        activities = self._aggregate_weekly_activities(week_start, week_end, chamber)
        
        # Generate narrative summary using LLM
        summary_text = self._generate_narrative_summary(activities, chamber)
        
        # Verify all citations
        verified_summary = self.citation_verifier.verify_summary(summary_text, activities)
        
        # Identify highlights
        highlights = self._identify_highlights(activities)
        
        return WeeklySummary(
            week_start=week_start,
            week_end=week_end,
            chamber=chamber,
            summary_text=verified_summary,
            bills_discussed=activities['bills'],
            major_votes=activities['votes'],
            important_statements=activities['statements'],
            questions_answered=activities['questions'],
            controversial_debates=highlights['controversial'],
            notable_quotes=highlights['quotes'],
            most_active_members=highlights['active_members'],
            sitting_days=activities['sitting_days'],
            total_statements=activities['statement_count'],
            bills_progressed=activities['bills_progressed'],
            votes_held=activities['vote_count'],
            source_documents=activities['source_docs']
        )
    
    def _aggregate_weekly_activities(
        self,
        week_start: date,
        week_end: date,
        chamber: Chamber
    ) -> Dict:
        """Aggregate all activities for the week"""
        # Get all Hansard sessions
        sessions = self.db.query(DocumentORM).filter(
            DocumentORM.type == 'hansard',
            DocumentORM.chamber == chamber,
            DocumentORM.date >= week_start,
            DocumentORM.date <= week_end
        ).all()
        
        # Get all statements
        statements = []
        for session in sessions:
            session_statements = self.db.query(StatementORM).filter(
                StatementORM.document_id == session.id,
                StatementORM.classification == 'substantive'
            ).all()
            statements.extend(session_statements)
        
        # Get bills discussed
        bill_ids = set()
        for stmt in statements:
            bill_ids.update(stmt.related_bill_ids or [])
        
        bills = self.db.query(BillORM).filter(
            BillORM.id.in_(bill_ids)
        ).all()
        
        # Get votes
        votes = self.db.query(VoteORM).filter(
            VoteORM.chamber == chamber,
            VoteORM.vote_date >= week_start,
            VoteORM.vote_date <= week_end
        ).all()
        
        # Get questions
        questions = self.db.query(QuestionORM).filter(
            QuestionORM.chamber == chamber,
            QuestionORM.answer_date >= week_start,
            QuestionORM.answer_date <= week_end,
            QuestionORM.answer_text.isnot(None)
        ).all()
        
        # Count bills that progressed
        bills_progressed = 0
        for bill in bills:
            # Check if bill advanced stages this week
            tracker_entries = self.db.query(BillTrackerEntryORM).filter(
                BillTrackerEntryORM.bill_id == bill.id,
                BillTrackerEntryORM.tracker_date >= week_start,
                BillTrackerEntryORM.tracker_date <= week_end
            ).all()
            
            if len(tracker_entries) > 1:
                # Bill progressed if stage changed
                stages = [e.stage for e in tracker_entries]
                if len(set(stages)) > 1:
                    bills_progressed += 1
        
        return {
            'sitting_days': len(sessions),
            'statements': statements,
            'statement_count': len(statements),
            'bills': [self._format_bill(b) for b in bills[:10]],
            'bills_progressed': bills_progressed,
            'votes': [self._format_vote(v) for v in votes],
            'vote_count': len(votes),
            'questions': [self._format_question(q) for q in questions[:10]],
            'source_docs': [s.source_url for s in sessions]
        }
    
    def _generate_narrative_summary(
        self,
        activities: Dict,
        chamber: Chamber
    ) -> str:
        """Generate narrative summary using LLM"""
        prompt = f"""Generate a 2-3 paragraph summary of this week's parliamentary activities in the {chamber.value}.

Week's Activities:
- {activities['sitting_days']} sitting days
- {activities['statement_count']} substantive statements
- {activities['bills_progressed']} bills progressed
- {activities['vote_count']} votes held

Key Bills Discussed:
{self._format_bills_for_prompt(activities['bills'])}

Major Votes:
{self._format_votes_for_prompt(activities['votes'])}

Important Questions:
{self._format_questions_for_prompt(activities['questions'])}

Generate an engaging summary that:
1. Highlights the most significant events
2. Mentions key bills and their progress
3. Notes any controversial votes or debates
4. Includes specific quotes or statements (with citations)
5. Provides context for non-expert readers

Format: Plain text, 2-3 paragraphs, include [citation: document_id] for all claims.
"""
        
        response = self.llm.analyze(prompt)
        return response
    
    def _identify_highlights(self, activities: Dict) -> Dict:
        """Identify highlights from week's activities"""
        # Find controversial debates (high engagement, mixed sentiment)
        controversial = []
        for stmt in activities['statements']:
            if stmt.quality_score and stmt.quality_score > 80:
                # Check if related statements have mixed sentiment
                related = self._get_related_statements(stmt)
                sentiments = [s.sentiment for s in related if s.sentiment]
                
                if len(set(sentiments)) > 1:  # Mixed sentiments = controversial
                    controversial.append({
                        'statement_id': str(stmt.id),
                        'speaker': stmt.mp.name,
                        'text': stmt.text[:200],
                        'topic': stmt.topics[0] if stmt.topics else 'General'
                    })
        
        # Find notable quotes (high quality statements)
        notable_quotes = []
        high_quality = sorted(
            activities['statements'],
            key=lambda s: s.quality_score or 0,
            reverse=True
        )[:5]
        
        for stmt in high_quality:
            notable_quotes.append({
                'speaker': stmt.mp.name,
                'text': stmt.text[:300],
                'quality_score': stmt.quality_score,
                'statement_id': str(stmt.id)
            })
        
        # Find most active members
        member_activity = {}
        for stmt in activities['statements']:
            member_id = stmt.mp_id
            member_activity[member_id] = member_activity.get(member_id, 0) + 1
        
        most_active = sorted(
            member_activity.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        active_members = []
        for member_id, count in most_active:
            member = self._get_member(member_id)
            if member:
                active_members.append({
                    'name': member.name,
                    'statement_count': count,
                    'member_id': str(member_id)
                })
        
        return {
            'controversial': controversial[:5],
            'quotes': notable_quotes,
            'active_members': active_members
        }

class BicameralWeeklySummaryGenerator:
    """Generate bicameral weekly summaries"""
    
    def __init__(self, db_session, llm_analyzer):
        self.db = db_session
        self.llm = llm_analyzer
        self.na_generator = WeeklySummaryGenerator(db_session, llm_analyzer, None)
        self.senate_generator = WeeklySummaryGenerator(db_session, llm_analyzer, None)
    
    def generate_bicameral_summary(self, week_start: date) -> Dict:
        """Generate summary covering both chambers"""
        # Generate individual chamber summaries
        na_summary = self.na_generator.generate_weekly_summary(
            week_start,
            Chamber.NATIONAL_ASSEMBLY
        )
        
        senate_summary = self.senate_generator.generate_weekly_summary(
            week_start,
            Chamber.SENATE
        )
        
        # Identify cross-chamber activities
        cross_chamber = self._identify_cross_chamber_activities(
            week_start,
            week_start + timedelta(days=6)
        )
        
        # Generate bicameral narrative
        bicameral_narrative = self._generate_bicameral_narrative(
            na_summary,
            senate_summary,
            cross_chamber
        )
        
        return {
            'week_start': week_start,
            'week_end': week_start + timedelta(days=6),
            'national_assembly': na_summary,
            'senate': senate_summary,
            'cross_chamber_activities': cross_chamber,
            'bicameral_narrative': bicameral_narrative
        }
    
    def _identify_cross_chamber_activities(
        self,
        week_start: date,
        week_end: date
    ) -> Dict:
        """Identify activities involving both chambers"""
        # Find bills transmitted between chambers
        transmissions = self.db.query(CrossChamberBillORM).filter(
            CrossChamberBillORM.transmission_date >= week_start,
            CrossChamberBillORM.transmission_date <= week_end
        ).all()
        
        # Find joint committee activities
        # (Would need joint committee meeting tracking)
        
        return {
            'bills_transmitted': len(transmissions),
            'transmission_details': [
                {
                    'bill_id': str(t.bill_id),
                    'from': t.originating_chamber.value,
                    'to': t.receiving_chamber.value,
                    'date': t.transmission_date
                }
                for t in transmissions
            ]
        }
```

### Correctness Properties

**Property 1.1**: Summary accuracy
- **Validates**: Requirements 1.3.1
- **Property**: Summary accuracy must be ≥85%
- **Test Strategy**: Manual review of 20 summaries against source documents

**Property 1.2**: Citation completeness
- **Validates**: Requirements 1.1.6, 10.1.4
- **Property**: All claims must be cited
- **Test Strategy**: Verify all factual claims have citations

---

## Design 2: Historical Content Generator

### Component Design

**Purpose**: Generate "This Day in History" content for each calendar day

**Technology**: Database queries + LLM for narrative generation

**Builds On**: Phase 1 LLM analyzer

### Implementation

```python
from dataclasses import dataclass
from typing import List
from datetime import date

@dataclass
class HistoricalEvent:
    """Historical parliamentary event"""
    date: date
    year: int
    event_type: str  # bill_passed, major_debate, significant_vote
    title: str
    description: str
    participants: List[str]
    source_document_id: str

class HistoricalContentGenerator:
    """Generate historical content"""
    
    def __init__(self, db_session, llm_analyzer):
        self.db = db_session
        self.llm = llm_analyzer
    
    def generate_this_day_in_history(
        self,
        target_date: date
    ) -> Dict:
        """Generate content for this day in history"""
        # Get events from previous years on same day
        events = self._find_historical_events(target_date.month, target_date.day)
        
        if not events:
            return {'has_events': False}
        
        # Generate narrative
        narrative = self._generate_historical_narrative(events, target_date)
        
        # Calculate year-over-year comparison
        comparison = self._generate_year_comparison(target_date)
        
        return {
            'has_events': True,
            'date': target_date,
            'events': events,
            'narrative': narrative,
            'year_comparison': comparison
        }
    
    def _find_historical_events(self, month: int, day: int) -> List[HistoricalEvent]:
        """Find events from previous years on same date"""
        events = []
        
        # Find bills passed on this date
        bills_passed = self.db.query(VoteORM).filter(
            extract('month', VoteORM.vote_date) == month,
            extract('day', VoteORM.vote_date) == day,
            VoteORM.result == 'passed'
        ).join(BillORM).all()
        
        for vote in bills_passed:
            events.append(HistoricalEvent(
                date=vote.vote_date,
                year=vote.vote_date.year,
                event_type='bill_passed',
                title=f"{vote.bill.title} passed",
                description=f"Bill {vote.bill.bill_number} passed with {vote.ayes} ayes",
                participants=[vote.bill.sponsor.name] if vote.bill.sponsor else [],
                source_document_id=str(vote.id)
            ))
        
        # Find major debates (high quality statements)
        major_statements = self.db.query(StatementORM).filter(
            extract('month', StatementORM.created_at) == month,
            extract('day', StatementORM.created_at) == day,
            StatementORM.quality_score >= 80
        ).all()
        
        for stmt in major_statements[:5]:
            events.append(HistoricalEvent(
                date=stmt.created_at.date(),
                year=stmt.created_at.year,
                event_type='major_debate',
                title=f"Debate on {stmt.topics[0] if stmt.topics else 'parliamentary matter'}",
                description=stmt.text[:200],
                participants=[stmt.mp.name],
                source_document_id=str(stmt.id)
            ))
        
        # Sort by year (most recent first)
        events.sort(key=lambda e: e.year, reverse=True)
        
        return events
    
    def _generate_historical_narrative(
        self,
        events: List[HistoricalEvent],
        target_date: date
    ) -> str:
        """Generate narrative for historical events"""
        prompt = f"""Generate a brief historical narrative for {target_date.strftime('%B %d')} in Kenyan parliamentary history.

Historical Events:
{self._format_events_for_prompt(events)}

Generate a 2-paragraph narrative that:
1. Highlights the most significant events
2. Provides historical context
3. Notes any patterns or recurring themes
4. Is engaging for general readers

Include [citation: event_id] for all specific claims.
"""
        
        response = self.llm.analyze(prompt)
        return response
    
    def _generate_year_comparison(self, target_date: date) -> Dict:
        """Compare current year to previous years"""
        current_year = target_date.year
        
        # Get activity for current year (up to target date)
        current_activity = self._get_year_activity(current_year, target_date)
        
        # Get activity for previous year (same period)
        previous_year = current_year - 1
        previous_activity = self._get_year_activity(previous_year, target_date)
        
        return {
            'current_year': current_year,
            'current_bills': current_activity['bills'],
            'current_votes': current_activity['votes'],
            'current_statements': current_activity['statements'],
            'previous_year': previous_year,
            'previous_bills': previous_activity['bills'],
            'previous_votes': previous_activity['votes'],
            'previous_statements': previous_activity['statements'],
            'change_bills': current_activity['bills'] - previous_activity['bills'],
            'change_votes': current_activity['votes'] - previous_activity['votes'],
            'change_statements': current_activity['statements'] - previous_activity['statements']
        }
```

### Correctness Properties

**Property 2.1**: Historical accuracy
- **Validates**: Requirements 2.3.1
- **Property**: Historical events must be 100% accurate (no fabrication)
- **Test Strategy**: Verify all events against source documents

**Property 2.2**: Date verification
- **Validates**: Requirements 2.3.2
- **Property**: All dates must be verified
- **Test Strategy**: Check all event dates against source documents



---

## Design 3: Advanced Party Position Analyzer

### Component Design

**Purpose**: Track and analyze party positions across all votes and bills

**Technology**: Pandas for aggregation + custom algorithms

**Builds On**: Phase 3 cross-chamber analyzer

### Implementation

```python
from dataclasses import dataclass
from typing import List, Dict
import pandas as pd

@dataclass
class PartyPosition:
    """Party position on a bill or motion"""
    party: str
    bill_id: str
    position: str  # support, oppose, mixed, abstain
    vote_breakdown: Dict[str, int]  # {'ayes': 10, 'noes': 2, 'abstain': 1}
    discipline_rate: float  # Percentage voting with party line
    defectors: List[str]  # Member IDs who voted against party

class AdvancedPartyAnalyzer:
    """Advanced party position analysis"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def analyze_party_position(
        self,
        party: str,
        bill_id: str
    ) -> PartyPosition:
        """Analyze party position on a bill"""
        # Get all votes on this bill
        votes = self.db.query(VoteORM).filter(
            VoteORM.bill_id == bill_id
        ).all()
        
        if not votes:
            return None
        
        # Get party members' votes
        party_votes = []
        for vote in votes:
            member_votes = self.db.query(MPVoteORM).filter(
                MPVoteORM.vote_id == vote.id
            ).join(MPORM).filter(
                MPORM.party == party
            ).all()
            party_votes.extend(member_votes)
        
        # Aggregate vote breakdown
        vote_breakdown = {
            'ayes': len([v for v in party_votes if v.direction == 'aye']),
            'noes': len([v for v in party_votes if v.direction == 'no']),
            'abstain': len([v for v in party_votes if v.direction == 'abstain'])
        }
        
        # Determine party position
        total_votes = sum(vote_breakdown.values())
        if total_votes == 0:
            position = 'abstain'
        elif vote_breakdown['ayes'] > vote_breakdown['noes']:
            position = 'support'
        elif vote_breakdown['noes'] > vote_breakdown['ayes']:
            position = 'oppose'
        else:
            position = 'mixed'
        
        # Calculate discipline rate
        majority_direction = max(vote_breakdown, key=vote_breakdown.get)
        discipline_rate = (vote_breakdown[majority_direction] / total_votes) * 100 if total_votes > 0 else 0
        
        # Identify defectors
        defectors = []
        for v in party_votes:
            if v.direction != majority_direction:
                defectors.append(str(v.mp_id))
        
        return PartyPosition(
            party=party,
            bill_id=bill_id,
            position=position,
            vote_breakdown=vote_breakdown,
            discipline_rate=discipline_rate,
            defectors=defectors
        )
    
    def analyze_coalition_patterns(self) -> Dict:
        """Analyze coalition voting patterns"""
        # Get all votes
        votes = self.db.query(VoteORM).all()
        
        # Track which parties vote together
        party_alignment = {}
        
        for vote in votes:
            # Get party positions
            parties = self.db.query(MPORM.party).distinct().all()
            
            party_positions = {}
            for (party,) in parties:
                position = self.analyze_party_position(party, str(vote.bill_id))
                if position:
                    party_positions[party] = position.position
            
            # Track alignment
            for party1 in party_positions:
                for party2 in party_positions:
                    if party1 < party2:  # Avoid duplicates
                        key = f"{party1}_{party2}"
                        if key not in party_alignment:
                            party_alignment[key] = {'aligned': 0, 'total': 0}
                        
                        party_alignment[key]['total'] += 1
                        if party_positions[party1] == party_positions[party2]:
                            party_alignment[key]['aligned'] += 1
        
        # Calculate alignment rates
        alignment_rates = {}
        for key, counts in party_alignment.items():
            rate = (counts['aligned'] / counts['total']) * 100 if counts['total'] > 0 else 0
            alignment_rates[key] = rate
        
        return alignment_rates
    
    def identify_bipartisan_bills(self) -> List[Dict]:
        """Identify bills with bipartisan support"""
        bills = self.db.query(BillORM).all()
        
        bipartisan_bills = []
        
        for bill in bills:
            # Get party positions
            parties = self.db.query(MPORM.party).distinct().all()
            
            support_count = 0
            for (party,) in parties:
                position = self.analyze_party_position(party, str(bill.id))
                if position and position.position == 'support':
                    support_count += 1
            
            # Bipartisan if >50% of parties support
            if support_count > len(parties) / 2:
                bipartisan_bills.append({
                    'bill_id': str(bill.id),
                    'title': bill.title,
                    'support_count': support_count,
                    'total_parties': len(parties)
                })
        
        return bipartisan_bills
    
    def track_position_evolution(
        self,
        party: str,
        bill_id: str
    ) -> List[Dict]:
        """Track how party position evolved over time"""
        # Get all votes on bill chronologically
        votes = self.db.query(VoteORM).filter(
            VoteORM.bill_id == bill_id
        ).order_by(VoteORM.vote_date).all()
        
        evolution = []
        
        for vote in votes:
            position = self.analyze_party_position(party, bill_id)
            
            evolution.append({
                'date': vote.vote_date,
                'stage': vote.vote_type,
                'position': position.position if position else 'unknown',
                'discipline_rate': position.discipline_rate if position else 0
            })
        
        return evolution
```

### Correctness Properties

**Property 3.1**: Party position accuracy
- **Validates**: Requirements 3.4.1
- **Property**: Party position accuracy must be ≥90%
- **Test Strategy**: Manual verification of 50 party positions

**Property 3.2**: Voting pattern accuracy
- **Validates**: Requirements 3.4.2
- **Property**: Voting pattern analysis must be ≥95% accurate
- **Test Strategy**: Verify vote counts and alignments for 30 votes

---

## Design 4: Advanced Search System

### Component Design

**Purpose**: Provide comprehensive search across all documents

**Technology**: Lunr.js (client-side) + Vector DB (semantic search)

**Builds On**: Phase 0 vector DB

### Implementation

```python
from dataclasses import dataclass
from typing import List, Optional
import json

@dataclass
class SearchResult:
    """Search result"""
    document_id: str
    document_type: str
    title: str
    excerpt: str
    date: date
    chamber: str
    relevance_score: float
    url: str

class SearchIndexGenerator:
    """Generate search index for Lunr.js"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def generate_search_index(self) -> Dict:
        """Generate complete search index"""
        documents = []
        
        # Index all document types
        documents.extend(self._index_hansard())
        documents.extend(self._index_bills())
        documents.extend(self._index_votes())
        documents.extend(self._index_questions())
        documents.extend(self._index_petitions())
        documents.extend(self._index_trackers())
        documents.extend(self._index_ag_reports())
        
        # Create Lunr.js compatible index
        index_data = {
            'documents': documents,
            'fields': ['title', 'content', 'chamber', 'date', 'type'],
            'ref': 'id'
        }
        
        return index_data
    
    def _index_hansard(self) -> List[Dict]:
        """Index Hansard documents"""
        sessions = self.db.query(DocumentORM).filter(
            DocumentORM.type == 'hansard'
        ).all()
        
        indexed = []
        for session in sessions:
            # Get all statements
            statements = self.db.query(StatementORM).filter(
                StatementORM.document_id == session.id,
                StatementORM.classification == 'substantive'
            ).all()
            
            # Combine statement text
            content = ' '.join([s.text for s in statements[:50]])  # Limit for index size
            
            indexed.append({
                'id': str(session.id),
                'type': 'hansard',
                'title': f"Hansard - {session.date}",
                'content': content[:5000],  # Limit content length
                'date': session.date.isoformat(),
                'chamber': session.chamber.value,
                'url': f"/sessions/{session.id}.html"
            })
        
        return indexed
    
    def _index_bills(self) -> List[Dict]:
        """Index bills"""
        bills = self.db.query(BillORM).all()
        
        indexed = []
        for bill in bills:
            # Get bill text from latest version
            content = bill.versions[-1].text if bill.versions else ""
            
            indexed.append({
                'id': str(bill.id),
                'type': 'bill',
                'title': bill.title,
                'content': content[:5000],
                'date': bill.introduction_date.isoformat() if bill.introduction_date else "",
                'chamber': bill.chamber.value,
                'url': f"/bills/{bill.id}.html"
            })
        
        return indexed
    
    # Similar methods for other document types...

class SemanticSearchEngine:
    """Semantic search using vector DB"""
    
    def __init__(self, vector_db, embedding_generator):
        self.vector_db = vector_db
        self.embedder = embedding_generator
    
    def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 20
    ) -> List[SearchResult]:
        """Perform semantic search"""
        # Generate query embedding
        query_embedding = self.embedder.generate(query)
        
        # Search vector DB
        results = self.vector_db.search(
            collection_name='all_documents',
            query_vector=query_embedding,
            limit=limit,
            filter=filters
        )
        
        # Format results
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                document_id=result['id'],
                document_type=result['metadata']['type'],
                title=result['metadata']['title'],
                excerpt=result['text'][:300],
                date=result['metadata']['date'],
                chamber=result['metadata']['chamber'],
                relevance_score=result['score'],
                url=result['metadata']['url']
            ))
        
        return search_results

class HybridSearchEngine:
    """Combine full-text and semantic search"""
    
    def __init__(self, semantic_engine: SemanticSearchEngine):
        self.semantic = semantic_engine
    
    def search(
        self,
        query: str,
        search_type: str = 'hybrid',
        filters: Optional[Dict] = None,
        limit: int = 20
    ) -> List[SearchResult]:
        """Perform hybrid search"""
        if search_type == 'semantic':
            return self.semantic.search(query, filters, limit)
        
        elif search_type == 'fulltext':
            # Full-text search handled by Lunr.js on client side
            return []
        
        else:  # hybrid
            # Combine both approaches
            semantic_results = self.semantic.search(query, filters, limit)
            
            # Full-text results would come from client-side Lunr.js
            # Here we just return semantic results
            return semantic_results
```

### Correctness Properties

**Property 4.1**: Search completeness
- **Validates**: Requirements 4.1.1
- **Property**: Search must cover all document types
- **Test Strategy**: Verify search index includes all documents

**Property 4.2**: Search performance
- **Validates**: Requirements 4.3.1
- **Property**: Search queries must complete in <500ms
- **Test Strategy**: Benchmark 100 search queries



---

## Design 5: REST API Layer (Optional)

### Component Design

**Purpose**: Provide programmatic access to parliamentary data

**Technology**: FastAPI + Pydantic + SQLAlchemy

**Builds On**: Phase 0 data models

### Implementation

```python
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

app = FastAPI(
    title="Hansard Tales API",
    description="Parliamentary accountability data API",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Response models
class MPResponse(BaseModel):
    """MP response model"""
    id: str
    name: str
    party: str
    constituency: str
    total_statements: int
    average_quality_score: float
    
    class Config:
        from_attributes = True

class BillResponse(BaseModel):
    """Bill response model"""
    id: str
    bill_number: str
    title: str
    chamber: str
    status: str
    sponsor_name: str
    
    class Config:
        from_attributes = True

class StatementResponse(BaseModel):
    """Statement response model"""
    id: str
    mp_name: str
    text: str
    date: date
    quality_score: Optional[float]
    sentiment: Optional[str]
    topics: List[str]
    
    class Config:
        from_attributes = True

# Endpoints
@app.get("/api/v1/mps", response_model=List[MPResponse])
async def list_mps(
    party: Optional[str] = None,
    constituency: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List MPs with optional filtering"""
    query = db.query(MPORM)
    
    if party:
        query = query.filter(MPORM.party == party)
    
    if constituency:
        query = query.filter(MPORM.constituency == constituency)
    
    mps = query.offset(offset).limit(limit).all()
    
    return [MPResponse.from_orm(mp) for mp in mps]

@app.get("/api/v1/mps/{mp_id}", response_model=MPResponse)
async def get_mp(mp_id: str, db: Session = Depends(get_db)):
    """Get MP by ID"""
    mp = db.query(MPORM).filter(MPORM.id == mp_id).first()
    
    if not mp:
        raise HTTPException(status_code=404, detail="MP not found")
    
    return MPResponse.from_orm(mp)

@app.get("/api/v1/bills", response_model=List[BillResponse])
async def list_bills(
    chamber: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List bills with optional filtering"""
    query = db.query(BillORM)
    
    if chamber:
        query = query.filter(BillORM.chamber == chamber)
    
    if status:
        query = query.filter(BillORM.status == status)
    
    bills = query.offset(offset).limit(limit).all()
    
    return [BillResponse.from_orm(bill) for bill in bills]

@app.get("/api/v1/statements", response_model=List[StatementResponse])
async def list_statements(
    mp_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_quality: Optional[float] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List statements with optional filtering"""
    query = db.query(StatementORM)
    
    if mp_id:
        query = query.filter(StatementORM.mp_id == mp_id)
    
    if date_from:
        query = query.filter(StatementORM.created_at >= date_from)
    
    if date_to:
        query = query.filter(StatementORM.created_at <= date_to)
    
    if min_quality:
        query = query.filter(StatementORM.quality_score >= min_quality)
    
    statements = query.offset(offset).limit(limit).all()
    
    return [StatementResponse.from_orm(stmt) for stmt in statements]

@app.get("/api/v1/search")
async def search(
    q: str,
    type: Optional[str] = None,
    chamber: Optional[str] = None,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """Semantic search across all documents"""
    search_engine = SemanticSearchEngine(vector_db, embedder)
    
    filters = {}
    if type:
        filters['type'] = type
    if chamber:
        filters['chamber'] = chamber
    
    results = search_engine.search(q, filters, limit)
    
    return {'results': results, 'count': len(results)}

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/rate-limited-endpoint")
@limiter.limit("100/minute")
async def rate_limited_endpoint(request: Request):
    """Example rate-limited endpoint"""
    return {"message": "This endpoint is rate limited"}
```

### Correctness Properties

**Property 5.1**: API response accuracy
- **Validates**: Requirements 5.1.2
- **Property**: API responses must match database data
- **Test Strategy**: Compare API responses with direct database queries

**Property 5.2**: API performance
- **Validates**: Requirements 5.3.1
- **Property**: API responses must complete in <200ms (p95)
- **Test Strategy**: Benchmark 1000 API requests

---

## Design 6: Data Export System

### Component Design

**Purpose**: Enable data export in multiple formats

**Technology**: Pandas + openpyxl + reportlab

**Builds On**: Phase 0 data models

### Implementation

```python
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import csv
import json

class DataExporter:
    """Export data in multiple formats"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def export_voting_records(
        self,
        member_id: str,
        format: str = 'csv',
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> bytes:
        """Export voting records for MP/Senator"""
        # Get votes
        votes = self.db.query(MPVoteORM).filter(
            MPVoteORM.mp_id == member_id
        ).join(VoteORM)
        
        if date_from:
            votes = votes.filter(VoteORM.vote_date >= date_from)
        
        if date_to:
            votes = votes.filter(VoteORM.vote_date <= date_to)
        
        votes = votes.all()
        
        # Convert to DataFrame
        data = []
        for vote in votes:
            data.append({
                'Date': vote.vote.vote_date,
                'Bill': vote.vote.bill.title if vote.vote.bill else 'N/A',
                'Vote': vote.direction,
                'Result': vote.vote.result,
                'Chamber': vote.vote.chamber.value
            })
        
        df = pd.DataFrame(data)
        
        # Export in requested format
        if format == 'csv':
            return df.to_csv(index=False).encode('utf-8')
        elif format == 'json':
            return df.to_json(orient='records').encode('utf-8')
        elif format == 'excel':
            return self._df_to_excel(df)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_bill_tracking(
        self,
        bill_id: str,
        format: str = 'csv'
    ) -> bytes:
        """Export bill tracking data"""
        # Get bill
        bill = self.db.query(BillORM).filter(BillORM.id == bill_id).first()
        
        if not bill:
            raise ValueError(f"Bill not found: {bill_id}")
        
        # Get tracker entries
        entries = self.db.query(BillTrackerEntryORM).filter(
            BillTrackerEntryORM.bill_id == bill_id
        ).order_by(BillTrackerEntryORM.tracker_date).all()
        
        # Convert to DataFrame
        data = []
        for entry in entries:
            data.append({
                'Date': entry.tracker_date,
                'Stage': entry.stage,
                'Status': entry.status,
                'Days at Stage': entry.days_at_stage,
                'Stalled': entry.is_stalled
            })
        
        df = pd.DataFrame(data)
        
        # Export
        if format == 'csv':
            return df.to_csv(index=False).encode('utf-8')
        elif format == 'json':
            return df.to_json(orient='records').encode('utf-8')
        elif format == 'excel':
            return self._df_to_excel(df)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_financial_oversight(
        self,
        format: str = 'csv',
        year: Optional[int] = None
    ) -> bytes:
        """Export financial oversight data"""
        # Get audit findings
        query = self.db.query(AuditFindingORM).join(AuditorGeneralReportORM)
        
        if year:
            query = query.filter(
                extract('year', AuditorGeneralReportORM.publication_date) == year
            )
        
        findings = query.all()
        
        # Convert to DataFrame
        data = []
        for finding in findings:
            data.append({
                'Entity': finding.entity_name,
                'Entity Type': finding.entity_type,
                'Finding': finding.finding_text[:200],
                'Amount': float(finding.amount_involved) if finding.amount_involved else 0,
                'Severity': finding.severity,
                'Type': finding.finding_type,
                'Discussed in Parliament': finding.discussed_in_parliament,
                'Report Date': finding.report.publication_date
            })
        
        df = pd.DataFrame(data)
        
        # Export
        if format == 'csv':
            return df.to_csv(index=False).encode('utf-8')
        elif format == 'json':
            return df.to_json(orient='records').encode('utf-8')
        elif format == 'excel':
            return self._df_to_excel(df)
        elif format == 'pdf':
            return self._generate_pdf_report(df, "Financial Oversight Report")
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _df_to_excel(self, df: pd.DataFrame) -> bytes:
        """Convert DataFrame to Excel bytes"""
        from io import BytesIO
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        
        return output.getvalue()
    
    def _generate_pdf_report(self, df: pd.DataFrame, title: str) -> bytes:
        """Generate PDF report from DataFrame"""
        from io import BytesIO
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=landscape(letter))
        
        elements = []
        
        # Add title
        styles = getSampleStyleSheet()
        elements.append(Paragraph(title, styles['Title']))
        
        # Add table
        data = [df.columns.tolist()] + df.values.tolist()
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        return output.getvalue()
```

### Correctness Properties

**Property 6.1**: Export completeness
- **Validates**: Requirements 6.2.1-6.2.5
- **Property**: Exports must include all requested data
- **Test Strategy**: Verify exported data matches database queries

**Property 6.2**: Export performance
- **Validates**: Requirements 6.3.1
- **Property**: Exports must complete in <30 seconds
- **Test Strategy**: Benchmark exports for various data sizes

---

## Design 7: Performance Optimization Suite

### Component Design

**Purpose**: Optimize system performance for production scale

**Technology**: Connection pooling + caching + parallel processing

**Builds On**: Phase 3 performance optimizations

### Implementation

```python
from sqlalchemy.pool import QueuePool
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import redis

class DatabaseOptimizer:
    """Database performance optimizations"""
    
    def __init__(self, config):
        self.config = config
        self.engine = self._create_optimized_engine()
        self.cache = redis.Redis(host='localhost', port=6379, db=0)
    
    def _create_optimized_engine(self):
        """Create database engine with connection pooling"""
        from sqlalchemy import create_engine
        
        engine = create_engine(
            self.config.database.url,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        return engine
    
    @lru_cache(maxsize=1000)
    def get_cached_query_result(self, query_key: str):
        """Cache query results"""
        # Check Redis cache
        cached = self.cache.get(query_key)
        if cached:
            return json.loads(cached)
        
        return None
    
    def set_cached_query_result(self, query_key: str, result, ttl: int = 3600):
        """Store query result in cache"""
        self.cache.setex(
            query_key,
            ttl,
            json.dumps(result, default=str)
        )

class ParallelSiteGenerator:
    """Generate site pages in parallel"""
    
    def __init__(self, db_session, template_dir: Path, output_dir: Path):
        self.db = db_session
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.max_workers = 8
    
    def generate_all_parallel(self):
        """Generate all pages in parallel"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all page generation tasks
            futures = []
            
            # MP pages
            mps = self.db.query(MPORM).all()
            for mp in mps:
                future = executor.submit(self._generate_mp_page, mp)
                futures.append(future)
            
            # Senator pages
            senators = self.db.query(SenatorORM).all()
            for senator in senators:
                future = executor.submit(self._generate_senator_page, senator)
                futures.append(future)
            
            # Bill pages
            bills = self.db.query(BillORM).all()
            for bill in bills:
                future = executor.submit(self._generate_bill_page, bill)
                futures.append(future)
            
            # Wait for all to complete
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Page generation failed: {e}")
    
    def _generate_mp_page(self, mp: MPORM):
        """Generate single MP page"""
        # Generate profile
        profile = MPProfileGenerator(self.db).generate_profile(str(mp.id))
        
        # Render template
        template = self.env.get_template('pages/mp_profile.html')
        html = template.render(mp=profile)
        
        # Write file
        output_path = self.output_dir / 'mps' / f'{mp.id}.html'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)

class IncrementalProcessor:
    """Process only new/changed documents"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_documents_needing_processing(self) -> List[str]:
        """Get documents that need processing"""
        # Find documents without analysis
        unprocessed = self.db.query(DocumentORM.id).filter(
            ~DocumentORM.statements.any()
        ).all()
        
        # Find documents updated since last processing
        updated = self.db.query(DocumentORM.id).filter(
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

class AssetOptimizer:
    """Optimize static assets"""
    
    def __init__(self, asset_dir: Path):
        self.asset_dir = asset_dir
    
    def optimize_all(self):
        """Optimize all assets"""
        self.minify_css()
        self.minify_js()
        self.optimize_images()
    
    def minify_css(self):
        """Minify CSS files"""
        import csscompressor
        
        css_files = self.asset_dir.glob('**/*.css')
        
        for css_file in css_files:
            if '.min.' in css_file.name:
                continue  # Skip already minified
            
            content = css_file.read_text()
            minified = csscompressor.compress(content)
            
            # Write minified version
            min_file = css_file.with_suffix('.min.css')
            min_file.write_text(minified)
    
    def minify_js(self):
        """Minify JavaScript files"""
        import jsmin
        
        js_files = self.asset_dir.glob('**/*.js')
        
        for js_file in js_files:
            if '.min.' in js_file.name:
                continue
            
            content = js_file.read_text()
            minified = jsmin.jsmin(content)
            
            min_file = js_file.with_suffix('.min.js')
            min_file.write_text(minified)
    
    def optimize_images(self):
        """Optimize images"""
        from PIL import Image
        
        image_files = list(self.asset_dir.glob('**/*.png')) + \
                     list(self.asset_dir.glob('**/*.jpg'))
        
        for img_file in image_files:
            img = Image.open(img_file)
            
            # Resize if too large
            max_size = (1200, 1200)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized
            img.save(img_file, optimize=True, quality=85)
```

### Correctness Properties

**Property 7.1**: Optimization correctness
- **Validates**: Requirements 7.1.1-7.3.4
- **Property**: Optimizations must not change functionality
- **Test Strategy**: Compare outputs before/after optimization

**Property 7.2**: Performance improvement
- **Validates**: Requirements 7.4.1-7.4.4
- **Property**: Optimizations must improve performance by ≥30%
- **Test Strategy**: Benchmark before/after optimization



---

## Design 8: User Experience Enhancements

### Component Design

**Purpose**: Polish user interface and improve accessibility

**Technology**: HTML/CSS/JavaScript + Chart.js + Leaflet.js

**Builds On**: Phase 1-4 site generation

### Implementation

**1. Interactive Voting Charts** (`static/js/voting-charts.js`):
```javascript
class VotingChartGenerator {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.chart = null;
    }
    
    renderVotingRecord(votingData) {
        const ctx = this.container.getContext('2d');
        
        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: votingData.map(v => v.date),
                datasets: [{
                    label: 'Ayes',
                    data: votingData.map(v => v.ayes),
                    backgroundColor: 'rgba(75, 192, 192, 0.6)'
                }, {
                    label: 'Noes',
                    data: votingData.map(v => v.noes),
                    backgroundColor: 'rgba(255, 99, 132, 0.6)'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    renderPartyDiscipline(partyData) {
        const ctx = this.container.getContext('2d');
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: partyData.map(p => p.date),
                datasets: [{
                    label: 'Party Discipline Rate',
                    data: partyData.map(p => p.discipline_rate),
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
}
```

**2. Bill Timeline Visualization** (`static/js/bill-timeline.js`):
```javascript
class BillTimelineRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
    }
    
    render(timelineData) {
        const timeline = document.createElement('div');
        timeline.className = 'bill-timeline';
        
        timelineData.forEach((event, index) => {
            const eventElement = this.createEventElement(event, index);
            timeline.appendChild(eventElement);
        });
        
        this.container.appendChild(timeline);
    }
    
    createEventElement(event, index) {
        const element = document.createElement('div');
        element.className = 'timeline-event';
        element.dataset.chamber = event.chamber;
        
        element.innerHTML = `
            <div class="event-marker">${index + 1}</div>
            <div class="event-content">
                <div class="event-date">${event.date}</div>
                <div class="event-chamber">${event.chamber}</div>
                <div class="event-title">${event.event}</div>
                <div class="event-details">${event.details}</div>
            </div>
        `;
        
        return element;
    }
}
```

**3. Constituency Map** (`static/js/constituency-map.js`):
```javascript
class ConstituencyMapRenderer {
    constructor(containerId) {
        this.container = containerId;
        this.map = null;
    }
    
    initialize() {
        // Initialize Leaflet map
        this.map = L.map(this.container).setView([-1.286389, 36.817223], 6);
        
        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
    }
    
    renderConstituencies(constituencyData) {
        constituencyData.forEach(constituency => {
            // Add marker for each constituency
            const marker = L.marker([constituency.lat, constituency.lng])
                .addTo(this.map);
            
            // Add popup with representation score
            marker.bindPopup(`
                <strong>${constituency.name}</strong><br>
                MP: ${constituency.mp_name}<br>
                Representation Score: ${constituency.score.toFixed(1)}
            `);
            
            // Color code by score
            const color = this.getScoreColor(constituency.score);
            marker.setIcon(this.createColoredIcon(color));
        });
    }
    
    getScoreColor(score) {
        if (score >= 80) return 'green';
        if (score >= 60) return 'yellow';
        if (score >= 40) return 'orange';
        return 'red';
    }
}
```

**4. Accessibility Enhancements** (`templates/layouts/base.html`):
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Hansard Tales{% endblock %}</title>
    
    <!-- Skip to main content -->
    <a href="#main-content" class="skip-link">Skip to main content</a>
    
    <!-- Stylesheets -->
    <link rel="stylesheet" href="/static/css/main.min.css">
    
    <!-- ARIA landmarks -->
</head>
<body>
    <header role="banner">
        <nav role="navigation" aria-label="Main navigation">
            <!-- Navigation with keyboard support -->
            <ul>
                <li><a href="/" tabindex="0">Home</a></li>
                <li><a href="/mps" tabindex="0">MPs</a></li>
                <li><a href="/senators" tabindex="0">Senators</a></li>
                <li><a href="/bills" tabindex="0">Bills</a></li>
                <li><a href="/search" tabindex="0">Search</a></li>
            </ul>
        </nav>
        
        <!-- Search bar -->
        <div class="search-bar" role="search">
            <label for="site-search" class="sr-only">Search site</label>
            <input 
                type="search" 
                id="site-search" 
                placeholder="Search parliament..."
                aria-label="Search parliamentary documents"
            >
        </div>
    </header>
    
    <!-- Breadcrumbs -->
    <nav aria-label="Breadcrumb" class="breadcrumb">
        {% block breadcrumb %}{% endblock %}
    </nav>
    
    <main id="main-content" role="main">
        {% block content %}{% endblock %}
    </main>
    
    <footer role="contentinfo">
        <p>&copy; 2026 Hansard Tales</p>
    </footer>
    
    <!-- Back to top button -->
    <button 
        id="back-to-top" 
        aria-label="Back to top"
        onclick="window.scrollTo({top: 0, behavior: 'smooth'})"
    >
        ↑ Top
    </button>
    
    <script src="/static/js/main.min.js"></script>
</body>
</html>
```

**5. Responsive Design** (`static/css/responsive.css`):
```css
/* Mobile-first responsive design */

/* Base styles (mobile) */
.container {
    width: 100%;
    padding: 1rem;
}

.grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
}

/* Tablet */
@media (min-width: 768px) {
    .container {
        max-width: 720px;
        margin: 0 auto;
    }
    
    .grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Desktop */
@media (min-width: 1024px) {
    .container {
        max-width: 960px;
    }
    
    .grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

/* Large desktop */
@media (min-width: 1280px) {
    .container {
        max-width: 1200px;
    }
    
    .grid {
        grid-template-columns: repeat(4, 1fr);
    }
}

/* Touch-friendly buttons */
@media (hover: none) and (pointer: coarse) {
    button, a {
        min-height: 44px;
        min-width: 44px;
    }
}
```

### Correctness Properties

**Property 8.1**: Accessibility compliance
- **Validates**: Requirements 8.3.1
- **Property**: Site must meet WCAG 2.1 Level AA
- **Test Strategy**: Run automated accessibility audit (axe-core)

**Property 8.2**: Mobile responsiveness
- **Validates**: Requirements 8.4.1
- **Property**: Site must be fully functional on mobile
- **Test Strategy**: Test on multiple device sizes

---

## Design 9: Advanced Analytics and Insights

### Component Design

**Purpose**: Generate insights and predictions from parliamentary data

**Technology**: Pandas + scikit-learn (optional) + custom algorithms

**Builds On**: Phase 4 accountability analytics

### Implementation

```python
from dataclasses import dataclass
from typing import List, Dict
import pandas as pd
from collections import Counter

@dataclass
class TrendingTopic:
    """Trending topic in parliament"""
    topic: str
    mention_count: int
    growth_rate: float  # Percentage increase from previous period
    chambers: List[str]
    top_speakers: List[str]

class TrendAnalyzer:
    """Analyze trends in parliamentary data"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def identify_trending_topics(
        self,
        period_days: int = 7
    ) -> List[TrendingTopic]:
        """Identify trending topics"""
        from datetime import datetime, timedelta
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=period_days)
        previous_start = start_date - timedelta(days=period_days)
        
        # Get current period topics
        current_topics = self._get_period_topics(start_date, end_date)
        
        # Get previous period topics
        previous_topics = self._get_period_topics(previous_start, start_date)
        
        # Calculate growth rates
        trending = []
        for topic, current_count in current_topics.items():
            previous_count = previous_topics.get(topic, 0)
            
            if previous_count > 0:
                growth_rate = ((current_count - previous_count) / previous_count) * 100
            else:
                growth_rate = 100.0  # New topic
            
            # Only include topics with significant growth
            if growth_rate > 50 or current_count > 10:
                # Get chambers and speakers
                chambers, speakers = self._get_topic_details(topic, start_date, end_date)
                
                trending.append(TrendingTopic(
                    topic=topic,
                    mention_count=current_count,
                    growth_rate=growth_rate,
                    chambers=chambers,
                    top_speakers=speakers[:5]
                ))
        
        # Sort by growth rate
        trending.sort(key=lambda t: t.growth_rate, reverse=True)
        
        return trending[:10]
    
    def _get_period_topics(self, start_date: date, end_date: date) -> Dict[str, int]:
        """Get topic counts for period"""
        statements = self.db.query(StatementORM).filter(
            StatementORM.created_at >= start_date,
            StatementORM.created_at <= end_date,
            StatementORM.classification == 'substantive'
        ).all()
        
        # Count topics
        topic_counts = Counter()
        for stmt in statements:
            for topic in stmt.topics:
                topic_counts[topic] += 1
        
        return dict(topic_counts)
    
    def predict_bill_passage_likelihood(self, bill_id: str) -> Dict:
        """Predict likelihood of bill passage"""
        bill = self.db.query(BillORM).filter(BillORM.id == bill_id).first()
        
        if not bill:
            raise ValueError(f"Bill not found: {bill_id}")
        
        # Analyze historical patterns
        similar_bills = self._find_similar_bills(bill)
        
        # Calculate passage rate for similar bills
        passed_count = len([b for b in similar_bills if b.status in ['passed', 'enacted']])
        passage_rate = (passed_count / len(similar_bills)) * 100 if similar_bills else 50
        
        # Adjust based on current factors
        factors = self._analyze_passage_factors(bill)
        
        # Calculate final likelihood
        likelihood = passage_rate
        
        # Adjust for sponsor influence
        if factors['sponsor_success_rate'] > 70:
            likelihood += 10
        elif factors['sponsor_success_rate'] < 30:
            likelihood -= 10
        
        # Adjust for party support
        if factors['party_support'] > 80:
            likelihood += 15
        elif factors['party_support'] < 40:
            likelihood -= 15
        
        # Adjust for time at stage
        if factors['days_at_current_stage'] > 60:
            likelihood -= 20  # Stalled bills less likely to pass
        
        # Clamp to 0-100
        likelihood = max(0, min(100, likelihood))
        
        return {
            'bill_id': bill_id,
            'passage_likelihood': likelihood,
            'factors': factors,
            'similar_bills_analyzed': len(similar_bills)
        }
    
    def _find_similar_bills(self, bill: BillORM) -> List[BillORM]:
        """Find historically similar bills"""
        # Find bills with similar topics
        similar = self.db.query(BillORM).filter(
            BillORM.id != bill.id,
            BillORM.chamber == bill.chamber,
            BillORM.topics.overlap(bill.topics)  # PostgreSQL array overlap
        ).limit(50).all()
        
        return similar
    
    def _analyze_passage_factors(self, bill: BillORM) -> Dict:
        """Analyze factors affecting passage"""
        # Sponsor success rate
        sponsor_bills = self.db.query(BillORM).filter(
            BillORM.sponsor_id == bill.sponsor_id
        ).all()
        
        sponsor_passed = len([b for b in sponsor_bills if b.status in ['passed', 'enacted']])
        sponsor_success_rate = (sponsor_passed / len(sponsor_bills)) * 100 if sponsor_bills else 50
        
        # Party support (from voting records)
        party_support = self._calculate_party_support(bill)
        
        # Time at current stage
        latest_tracker = self.db.query(BillTrackerEntryORM).filter(
            BillTrackerEntryORM.bill_id == bill.id
        ).order_by(BillTrackerEntryORM.tracker_date.desc()).first()
        
        days_at_stage = latest_tracker.days_at_stage if latest_tracker else 0
        
        return {
            'sponsor_success_rate': sponsor_success_rate,
            'party_support': party_support,
            'days_at_current_stage': days_at_stage
        }
```

### Correctness Properties

**Property 9.1**: Visualization accuracy
- **Validates**: Requirements 8.2.1-8.2.4
- **Property**: Visualizations must accurately represent data
- **Test Strategy**: Verify chart data matches database queries

**Property 9.2**: Prediction validity
- **Validates**: Requirements 9.3.1
- **Property**: Predictions must be based on valid historical data
- **Test Strategy**: Verify prediction accuracy against actual outcomes

---

## Summary

### Design Components

| Design | Component | Technology | Builds On |
|--------|-----------|------------|-----------|
| 1 | Weekly Summary Generator | LLM + aggregation | Phase 1 LLM analyzer |
| 2 | Historical Content Generator | Database queries + LLM | Phase 1 LLM analyzer |
| 3 | Advanced Party Analyzer | Pandas + algorithms | Phase 3 analyzer |
| 4 | Advanced Search System | Lunr.js + Vector DB | Phase 0 vector DB |
| 5 | REST API Layer | FastAPI + Pydantic | Phase 0 models |
| 6 | Data Export System | Pandas + openpyxl | Phase 0 models |
| 7 | Performance Optimization | Connection pooling + caching | Phase 3 optimization |
| 8 | UX Enhancements | HTML/CSS/JS + Chart.js | Phase 1-4 site |
| 9 | Advanced Analytics | Pandas + ML (optional) | Phase 4 analytics |

### Property-Based Tests

**18 Properties** to validate:
- Weekly summaries: 2 properties
- Historical content: 2 properties
- Party analysis: 2 properties
- Search system: 2 properties
- REST API: 2 properties
- Data export: 2 properties
- Performance optimization: 2 properties
- UX enhancements: 2 properties
- Advanced analytics: 2 properties

### Key Features

**Content Generation**:
- Automated weekly summaries (both chambers + bicameral)
- Historical content for every calendar day
- Trend analysis and insights

**Search and Discovery**:
- Full-text search (Lunr.js)
- Semantic search (Vector DB)
- Filtered and boolean search
- Search index <10MB

**API and Export**:
- REST API with OpenAPI docs (optional)
- CSV, JSON, Excel, PDF exports
- Rate limiting and authentication

**Performance**:
- Connection pooling
- Query result caching
- Parallel page generation
- Asset minification
- Incremental processing

**User Experience**:
- Interactive charts and visualizations
- Constituency maps
- Responsive design
- WCAG 2.1 Level AA compliance
- Keyboard navigation

**Analytics**:
- Trending topics
- Party position tracking
- Bill passage prediction
- Comparative analysis

### Performance Targets

- Full system processing: <2 hours
- Site generation: <30 minutes
- Database queries: <50ms (p95)
- Search queries: <500ms
- API responses: <200ms (p95)
- Memory usage: <8GB

### Cost Targets

- Total monthly cost: ≤$60
- LLM costs: ≤$40/month
- Infrastructure: ≤$20/month
- Cache hit rate: ≥50%

### Completion Criteria

Phase 5 design is complete when:
- ✓ All 9 component designs documented
- ✓ All 18 properties defined
- ✓ All algorithms described
- ✓ All templates designed
- ✓ Performance targets defined
- ✓ Cost estimates validated
- ✓ Ready for task breakdown

