# Phase 1: Core Analysis Pipeline - Design

## Introduction

This document provides detailed component designs for Phase 1 of the Hansard Tales system. It translates the requirements into concrete technical specifications for implementing AI-powered analysis of Hansard and Votes & Proceedings documents.

**Design Principles**:
- **Anti-Hallucination First**: Every LLM output must be verifiable with citations
- **Accuracy Over Speed**: Prioritize correctness, optimize performance later
- **Incremental Processing**: Support processing new documents without reprocessing old ones
- **Cost Consciousness**: Minimize LLM API calls through caching and smart batching
- **Testability**: Design for easy unit and property-based testing

## System Architecture

### Phase 1 Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hansard Processing Pipeline                   │
│                                                                  │
│  PDF → Text Extraction → MP Identification → Segmentation       │
│         → Filler Detection → Context Retrieval (RAG)            │
│         → LLM Analysis → Citation Verification → Storage        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Votes Processing Pipeline                     │
│                                                                  │
│  PDF → Table Extraction → Vote Parsing → MP Matching            │
│         → Bill Linking → Storage                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Correlation & Enrichment                      │
│                                                                  │
│  Bill-Statement Linking → MP Profile Generation                 │
│         → Session Summary Generation                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Static Site Generation                        │
│                                                                  │
│  Templates + Data → HTML Pages → Deploy to Cloudflare Pages     │
└─────────────────────────────────────────────────────────────────┘
```

## Design 1: MP Identification

### Component Design

**Purpose**: Extract MP names from Hansard text and match to database records

**Technology**: spaCy NER + fuzzy matching + rule-based patterns

### MP Name Patterns

Hansard uses several formats for MP names:
- `Hon. John Doe (Nairobi West, UDA)`
- `Dr. Jane Smith (Kisumu Central, ODM)`
- `The Speaker (Hon. Moses Wetangula)`
- `Mr. John Doe`
- `John Doe` (in subsequent mentions)

### Implementation

```python
from typing import Optional, List, Tuple
from dataclasses import dataclass
import re
from fuzzywuzzy import fuzz
import spacy

@dataclass
class MPMatch:
    """Result of MP identification"""
    mp_id: str
    name: str
    confidence: float
    constituency: Optional[str] = None
    party: Optional[str] = None

class MPIdentifier:
    """Identify MPs in Hansard text"""
    
    def __init__(self, db_session, nlp_model: str = "en_core_web_sm"):
        self.db = db_session
        self.nlp = spacy.load(nlp_model)
        self.mp_cache = self._load_mp_cache()
        
        # Compile regex patterns
        self.patterns = [
            # Hon. Name (Constituency, Party)
            re.compile(r'(?:Hon\.|Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\(([^,]+),\s*([^)]+)\)'),
            # Hon. Name
            re.compile(r'(?:Hon\.|Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'),
            # Name (Constituency)
            re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\(([^)]+)\)'),
        ]
    
    def _load_mp_cache(self) -> dict:
        """Load all MPs into memory for fast lookup"""
        mps = self.db.query(MPORM).filter(
            MPORM.chamber == 'national_assembly'
        ).all()
        
        cache = {}
        for mp in mps:
            # Index by full name
            cache[mp.name.lower()] = mp
            
            # Index by last name
            last_name = mp.name.split()[-1].lower()
            if last_name not in cache:
                cache[last_name] = []
            if isinstance(cache[last_name], list):
                cache[last_name].append(mp)
            else:
                cache[last_name] = [cache[last_name], mp]
        
        return cache
    
    def identify(self, text: str, context: Optional[dict] = None) -> Optional[MPMatch]:
        """Identify MP from text mention"""
        # Try regex patterns first
        for pattern in self.patterns:
            match = pattern.search(text)
            if match:
                name = match.group(1)
                constituency = match.group(2) if len(match.groups()) > 1 else None
                party = match.group(3) if len(match.groups()) > 2 else None
                
                mp = self._match_to_database(name, constituency, party)
                if mp:
                    return MPMatch(
                        mp_id=str(mp.id),
                        name=mp.name,
                        confidence=0.95,
                        constituency=mp.constituency,
                        party=mp.party
                    )
        
        # Try NER extraction
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                mp = self._match_to_database(ent.text)
                if mp:
                    return MPMatch(
                        mp_id=str(mp.id),
                        name=mp.name,
                        confidence=0.80,
                        constituency=mp.constituency,
                        party=mp.party
                    )
        
        return None
    
    def _match_to_database(
        self,
        name: str,
        constituency: Optional[str] = None,
        party: Optional[str] = None
    ) -> Optional[MPORM]:
        """Match extracted name to database record"""
        name_lower = name.lower()
        
        # Exact match
        if name_lower in self.mp_cache:
            mp = self.mp_cache[name_lower]
            if not isinstance(mp, list):
                return mp
        
        # Fuzzy match on full name
        best_match = None
        best_score = 0
        
        for cached_name, mp in self.mp_cache.items():
            if isinstance(mp, list):
                continue
            
            score = fuzz.ratio(name_lower, cached_name)
            
            # Boost score if constituency matches
            if constituency and mp.constituency:
                if constituency.lower() in mp.constituency.lower():
                    score += 20
            
            # Boost score if party matches
            if party and mp.party:
                if party.lower() in mp.party.lower():
                    score += 10
            
            if score > best_score and score >= 85:
                best_score = score
                best_match = mp
        
        return best_match
    
    def identify_batch(self, texts: List[str]) -> List[Optional[MPMatch]]:
        """Identify MPs in batch of texts"""
        return [self.identify(text) for text in texts]
```

### Correctness Properties

**Property 1.1**: MP identification accuracy
- **Validates**: Requirements 1.6
- **Property**: Identification accuracy must be ≥95% on test set
- **Test Strategy**: Manually annotate 100 Hansard excerpts, verify accuracy

**Property 1.2**: Name variation handling
- **Validates**: Requirements 1.3
- **Property**: Different name formats must resolve to same MP
- **Test Strategy**: Generate name variations, verify same MP returned


## Design 2: Statement Segmentation

### Component Design

**Purpose**: Split Hansard text into individual statements by MPs

**Technology**: Rule-based parsing + NLP sentence boundary detection

### Statement Boundaries

Hansard statements are bounded by:
- MP name mentions (start of new statement)
- Speaker interventions
- Section headers
- Page breaks

### Implementation

```python
from typing import List
from dataclasses import dataclass
import re

@dataclass
class Statement:
    """A single statement by an MP"""
    text: str
    mp_id: Optional[str]
    start_pos: int
    end_pos: int
    page_number: Optional[int] = None
    
class StatementSegmenter:
    """Segment Hansard text into statements"""
    
    def __init__(self, mp_identifier: MPIdentifier):
        self.mp_identifier = mp_identifier
        
        # Patterns for statement boundaries
        self.boundary_patterns = [
            # MP name with title
            re.compile(r'\n(?:Hon\.|Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+[A-Z]'),
            # Speaker interventions
            re.compile(r'\n(?:The Speaker|The Chairperson|The Deputy Speaker):'),
            # Section headers
            re.compile(r'\n[A-Z\s]{10,}\n'),
        ]
    
    def segment(self, text: str, session_id: str) -> List[Statement]:
        """Segment text into statements"""
        statements = []
        current_pos = 0
        
        # Find all boundary positions
        boundaries = self._find_boundaries(text)
        boundaries.append(len(text))  # Add end of text
        
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            
            segment_text = text[start:end].strip()
            if not segment_text or len(segment_text) < 20:
                continue
            
            # Identify MP for this segment
            mp_match = self.mp_identifier.identify(segment_text[:200])
            
            statement = Statement(
                text=segment_text,
                mp_id=mp_match.mp_id if mp_match else None,
                start_pos=start,
                end_pos=end
            )
            statements.append(statement)
        
        return statements
    
    def _find_boundaries(self, text: str) -> List[int]:
        """Find all statement boundary positions"""
        boundaries = [0]  # Start of text
        
        for pattern in self.boundary_patterns:
            for match in pattern.finditer(text):
                pos = match.start()
                if pos not in boundaries:
                    boundaries.append(pos)
        
        return sorted(boundaries)
    
    def clean_statement(self, text: str) -> str:
        """Clean statement text"""
        # Remove page numbers
        text = re.sub(r'\n\d+\n', '\n', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove header/footer artifacts
        text = re.sub(r'NATIONAL ASSEMBLY.*?\n', '', text)
        
        return text.strip()
```

### Correctness Properties

**Property 2.1**: Segmentation accuracy
- **Validates**: Requirements 1.7
- **Property**: Segmentation accuracy must be ≥98% on test set
- **Test Strategy**: Manually annotate 50 Hansard pages, verify boundaries

**Property 2.2**: No statement loss
- **Validates**: Requirements 1.7
- **Property**: All text must be assigned to some statement
- **Test Strategy**: Sum statement lengths equals input length (minus headers)


## Design 3: Statement Classification (Filler Detection)

### Component Design

**Purpose**: Classify statements as substantive or filler content

**Technology**: Rule-based classifier + ML classifier (optional)

### Filler Categories

1. **Procedural**: "I beg to move", "I second", "Question put and agreed to"
2. **Interruptions**: "(Applause)", "(Laughter)", "(Interruptions)"
3. **Administrative**: "The House rose at...", "Prayers"
4. **Short acknowledgments**: "Thank you", "I agree", "Yes"

### Implementation

```python
from enum import Enum
from typing import Tuple

class StatementType(Enum):
    SUBSTANTIVE = "substantive"
    PROCEDURAL = "procedural"
    INTERRUPTION = "interruption"
    ADMINISTRATIVE = "administrative"
    SHORT_ACK = "short_acknowledgment"

class FillerDetector:
    """Detect filler/non-substantive statements"""
    
    def __init__(self):
        self.filler_patterns = {
            StatementType.PROCEDURAL: [
                r'^I beg to move',
                r'^I second',
                r'^Question put and agreed to',
                r'^Motion made and Question proposed',
                r'^I beg to lay',
            ],
            StatementType.INTERRUPTION: [
                r'^\(Applause\)',
                r'^\(Laughter\)',
                r'^\(Interruptions\)',
                r'^\(Loud consultations\)',
            ],
            StatementType.ADMINISTRATIVE: [
                r'^The House rose at',
                r'^Prayers$',
                r'^ADJOURNMENT',
                r'^COMMUNICATION FROM THE CHAIR',
            ],
            StatementType.SHORT_ACK: [
                r'^Thank you\.?$',
                r'^I agree\.?$',
                r'^Yes\.?$',
                r'^No\.?$',
            ]
        }
        
        # Compile patterns
        self.compiled_patterns = {
            stmt_type: [re.compile(p, re.IGNORECASE) for p in patterns]
            for stmt_type, patterns in self.filler_patterns.items()
        }
    
    def classify(self, statement: Statement) -> Tuple[StatementType, float]:
        """Classify statement as substantive or filler"""
        text = statement.text.strip()
        
        # Check length first
        if len(text) < 10:
            return StatementType.SHORT_ACK, 1.0
        
        # Check patterns
        for stmt_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    return stmt_type, 0.95
        
        # Default to substantive
        return StatementType.SUBSTANTIVE, 0.90
    
    def is_substantive(self, statement: Statement) -> bool:
        """Check if statement is substantive"""
        stmt_type, confidence = self.classify(statement)
        return stmt_type == StatementType.SUBSTANTIVE
```

### Correctness Properties

**Property 3.1**: Filler detection precision
- **Validates**: Requirements 1.8
- **Property**: Filler detection precision must be ≥90%
- **Test Strategy**: Manually label 200 statements, verify precision

**Property 3.2**: No false negatives on substantive content
- **Validates**: Requirements 1.8
- **Property**: Substantive statements must not be classified as filler
- **Test Strategy**: Verify no substantive statements in filler set


## Design 4: Context Retrieval (RAG)

### Component Design

**Purpose**: Retrieve relevant context for LLM analysis using vector search

**Technology**: ChromaDB/Qdrant + sentence-transformers embeddings

### Context Types

1. **Historical statements**: Previous statements by same MP
2. **Related bills**: Bills mentioned in statement
3. **Related votes**: Votes on related topics
4. **Session context**: Other statements from same session

### Implementation

```python
from typing import List, Dict
from sentence_transformers import SentenceTransformer

@dataclass
class RetrievedContext:
    """Context retrieved for a statement"""
    historical_statements: List[Dict]
    related_bills: List[Dict]
    related_votes: List[Dict]
    session_context: List[Dict]

class ContextRetriever:
    """Retrieve relevant context using RAG"""
    
    def __init__(self, vector_db, embedding_model: str = "all-MiniLM-L6-v2"):
        self.vector_db = vector_db
        self.embedder = SentenceTransformer(embedding_model)
    
    def retrieve(
        self,
        statement: Statement,
        top_k: int = 5
    ) -> RetrievedContext:
        """Retrieve relevant context for statement"""
        # Generate embedding for statement
        query_embedding = self.embedder.encode(statement.text)
        
        # Retrieve historical statements by same MP
        historical = []
        if statement.mp_id:
            historical = self.vector_db.query(
                query_embeddings=[query_embedding],
                where={"mp_id": statement.mp_id},
                n_results=top_k
            )
        
        # Retrieve related bills
        related_bills = self._retrieve_related_bills(
            query_embedding,
            top_k=3
        )
        
        # Retrieve related votes
        related_votes = self._retrieve_related_votes(
            query_embedding,
            top_k=3
        )
        
        # Retrieve session context
        session_context = self._retrieve_session_context(
            statement,
            top_k=5
        )
        
        return RetrievedContext(
            historical_statements=historical,
            related_bills=related_bills,
            related_votes=related_votes,
            session_context=session_context
        )
    
    def _retrieve_related_bills(
        self,
        query_embedding,
        top_k: int
    ) -> List[Dict]:
        """Retrieve bills related to statement"""
        return self.vector_db.query(
            query_embeddings=[query_embedding],
            where={"document_type": "bill"},
            n_results=top_k
        )
    
    def _retrieve_related_votes(
        self,
        query_embedding,
        top_k: int
    ) -> List[Dict]:
        """Retrieve votes related to statement"""
        return self.vector_db.query(
            query_embeddings=[query_embedding],
            where={"document_type": "vote"},
            n_results=top_k
        )
    
    def _retrieve_session_context(
        self,
        statement: Statement,
        top_k: int
    ) -> List[Dict]:
        """Retrieve other statements from same session"""
        # Query by session_id and proximity
        return []  # Implement based on session tracking
```

### Correctness Properties

**Property 4.1**: Context relevance
- **Validates**: Requirements 1.9
- **Property**: Retrieved context must be semantically relevant
- **Test Strategy**: Manual evaluation of top-5 results for 50 queries

**Property 4.2**: Context diversity
- **Validates**: Requirements 1.9
- **Property**: Retrieved context should cover different aspects
- **Test Strategy**: Verify no duplicate or near-duplicate results


## Design 5: LLM Analysis (Sentiment, Quality, Topics)

### Component Design

**Purpose**: Analyze statements using Claude 3.5 Haiku for sentiment, quality, and topics

**Technology**: Anthropic Claude API with structured outputs

### Analysis Schema

```python
from pydantic import BaseModel, Field
from typing import List, Literal

class StatementAnalysis(BaseModel):
    """LLM analysis of a statement"""
    
    # Sentiment analysis
    sentiment: Literal["positive", "negative", "neutral", "mixed"]
    sentiment_confidence: float = Field(ge=0.0, le=1.0)
    sentiment_explanation: str
    
    # Quality scoring
    quality_score: int = Field(ge=0, le=100)
    quality_factors: Dict[str, int]  # clarity, depth, evidence, etc.
    
    # Topic classification
    primary_topic: str
    secondary_topics: List[str]
    topic_confidence: float = Field(ge=0.0, le=1.0)
    
    # Key points
    key_points: List[str] = Field(max_items=5)
    
    # Citations (for verification)
    citations: List[str]  # Direct quotes from statement
```

### Implementation

```python
import anthropic
from typing import Optional

class LLMAnalyzer:
    """Analyze statements using Claude"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        
        # System prompt for analysis
        self.system_prompt = """You are analyzing Kenyan parliamentary statements.
        
Your task:
1. Determine sentiment (positive/negative/neutral/mixed)
2. Score quality (0-100) based on clarity, depth, evidence
3. Identify primary and secondary topics
4. Extract key points (max 5)
5. Provide direct quotes as citations

CRITICAL: Only use information from the statement itself.
Do not make assumptions or add external knowledge.
All citations must be exact quotes from the statement."""
    
    def analyze(
        self,
        statement: Statement,
        context: Optional[RetrievedContext] = None
    ) -> StatementAnalysis:
        """Analyze statement with LLM"""
        # Build prompt with context
        prompt = self._build_prompt(statement, context)
        
        # Call Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse structured response
        analysis = self._parse_response(response.content[0].text)
        
        return analysis
    
    def _build_prompt(
        self,
        statement: Statement,
        context: Optional[RetrievedContext]
    ) -> str:
        """Build analysis prompt"""
        prompt = f"""Analyze this parliamentary statement:

STATEMENT:
{statement.text}

"""
        
        if context and context.historical_statements:
            prompt += "\nHISTORICAL CONTEXT (previous statements by this MP):\n"
            for hist in context.historical_statements[:3]:
                prompt += f"- {hist['text'][:200]}...\n"
        
        prompt += """
Provide analysis in JSON format:
{
  "sentiment": "positive|negative|neutral|mixed",
  "sentiment_confidence": 0.0-1.0,
  "sentiment_explanation": "brief explanation",
  "quality_score": 0-100,
  "quality_factors": {"clarity": 0-100, "depth": 0-100, "evidence": 0-100},
  "primary_topic": "main topic",
  "secondary_topics": ["topic1", "topic2"],
  "topic_confidence": 0.0-1.0,
  "key_points": ["point1", "point2", ...],
  "citations": ["exact quote 1", "exact quote 2", ...]
}"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> StatementAnalysis:
        """Parse LLM response into structured format"""
        import json
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in response")
        
        data = json.loads(json_match.group(0))
        return StatementAnalysis(**data)
    
    def analyze_batch(
        self,
        statements: List[Statement],
        batch_size: int = 10
    ) -> List[StatementAnalysis]:
        """Analyze statements in batches"""
        results = []
        
        for i in range(0, len(statements), batch_size):
            batch = statements[i:i + batch_size]
            
            # Process batch (could parallelize here)
            for statement in batch:
                analysis = self.analyze(statement)
                results.append(analysis)
        
        return results
```

### Cost Management

**Estimated costs** (Claude 3.5 Haiku):
- Input: $0.80 per million tokens
- Output: $4.00 per million tokens
- Average statement: ~500 tokens input, ~200 tokens output
- Cost per statement: ~$0.001
- 1000 statements: ~$1.00

**Optimization strategies**:
1. Cache analysis results
2. Batch similar statements
3. Skip filler statements
4. Use smaller context windows

### Correctness Properties

**Property 5.1**: Sentiment accuracy
- **Validates**: Requirements 1.10
- **Property**: Sentiment classification accuracy ≥80% on test set
- **Test Strategy**: Manual labeling of 100 statements, compare results

**Property 5.2**: Quality score consistency
- **Validates**: Requirements 1.11
- **Property**: Similar statements should have similar quality scores
- **Test Strategy**: Generate paraphrases, verify score variance < 10


## Design 6: Citation Generation and Verification

### Component Design

**Purpose**: Generate verifiable citations and prevent hallucinations

**Technology**: Exact string matching + fuzzy matching for verification

### Citation Format

```python
@dataclass
class Citation:
    """A verifiable citation"""
    quote: str  # Exact quote from source
    source_id: str  # Statement/document ID
    source_type: str  # "statement", "bill", "vote"
    page_number: Optional[int]
    verification_status: Literal["verified", "unverified", "failed"]
    similarity_score: float  # For fuzzy matches

class CitationVerifier:
    """Verify LLM-generated citations"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def verify_citation(
        self,
        citation: str,
        source_id: str,
        threshold: float = 0.95
    ) -> Citation:
        """Verify citation against source"""
        # Fetch source text
        source = self._fetch_source(source_id)
        if not source:
            return Citation(
                quote=citation,
                source_id=source_id,
                source_type="unknown",
                verification_status="failed",
                similarity_score=0.0
            )
        
        # Exact match
        if citation in source.text:
            return Citation(
                quote=citation,
                source_id=source_id,
                source_type=source.type,
                page_number=source.page_number,
                verification_status="verified",
                similarity_score=1.0
            )
        
        # Fuzzy match
        similarity = self._fuzzy_match(citation, source.text)
        if similarity >= threshold:
            # Find best matching substring
            best_match = self._find_best_match(citation, source.text)
            return Citation(
                quote=best_match,
                source_id=source_id,
                source_type=source.type,
                page_number=source.page_number,
                verification_status="verified",
                similarity_score=similarity
            )
        
        return Citation(
            quote=citation,
            source_id=source_id,
            source_type=source.type,
            verification_status="unverified",
            similarity_score=similarity
        )
    
    def _fuzzy_match(self, citation: str, source_text: str) -> float:
        """Calculate fuzzy match score"""
        from fuzzywuzzy import fuzz
        return fuzz.partial_ratio(citation, source_text) / 100.0
    
    def _find_best_match(self, citation: str, source_text: str) -> str:
        """Find best matching substring in source"""
        from difflib import SequenceMatcher
        
        matcher = SequenceMatcher(None, citation, source_text)
        match = matcher.find_longest_match(0, len(citation), 0, len(source_text))
        
        return source_text[match.b:match.b + match.size]
    
    def verify_batch(
        self,
        citations: List[Tuple[str, str]]
    ) -> List[Citation]:
        """Verify multiple citations"""
        return [
            self.verify_citation(quote, source_id)
            for quote, source_id in citations
        ]
```

### Anti-Hallucination Measures

1. **Mandatory citations**: All LLM outputs must include citations
2. **Verification required**: Citations verified before storage
3. **Confidence thresholds**: Low-confidence results flagged for review
4. **Audit trail**: All LLM inputs/outputs logged
5. **Human review**: Unverified citations require manual review

### Correctness Properties

**Property 6.1**: Citation verification accuracy
- **Validates**: Requirements 1.12
- **Property**: 100% of citations must be verified or flagged
- **Test Strategy**: Verify all citations in test set are checked

**Property 6.2**: No false verifications
- **Validates**: Requirements 1.12
- **Property**: Verified citations must exist in source
- **Test Strategy**: Sample verified citations, manually check source


## Design 7: Vote Processing

### Component Design

**Purpose**: Extract and process voting records from Votes & Proceedings PDFs

**Technology**: pdfplumber for table extraction + rule-based parsing

### Vote Record Format

```python
@dataclass
class VoteRecord:
    """A single vote record"""
    vote_id: str
    session_id: str
    date: date
    motion_text: str
    vote_type: Literal["division", "voice"]
    result: Literal["passed", "failed"]
    ayes: int
    noes: int
    abstentions: int
    mp_votes: List[MPVote]

@dataclass
class MPVote:
    """Individual MP vote"""
    mp_id: str
    vote: Literal["aye", "no", "abstain", "absent"]

class VoteProcessor:
    """Process Votes & Proceedings documents"""
    
    def __init__(self, db_session, mp_identifier: MPIdentifier):
        self.db = db_session
        self.mp_identifier = mp_identifier
    
    def process_pdf(self, pdf_path: Path) -> List[VoteRecord]:
        """Extract votes from PDF"""
        import pdfplumber
        
        votes = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extract tables
                tables = page.extract_tables()
                
                for table in tables:
                    if self._is_vote_table(table):
                        vote = self._parse_vote_table(table)
                        if vote:
                            votes.append(vote)
        
        return votes
    
    def _is_vote_table(self, table: List[List[str]]) -> bool:
        """Check if table contains vote data"""
        if not table or len(table) < 2:
            return False
        
        # Check for vote-related headers
        header = ' '.join(table[0]).lower()
        return any(keyword in header for keyword in ['ayes', 'noes', 'vote', 'division'])
    
    def _parse_vote_table(self, table: List[List[str]]) -> Optional[VoteRecord]:
        """Parse vote table into structured data"""
        # Extract motion text (usually above table)
        motion_text = ""
        
        # Parse MP votes
        mp_votes = []
        for row in table[1:]:  # Skip header
            if len(row) < 2:
                continue
            
            mp_name = row[0]
            vote_value = row[1].lower()
            
            # Match MP
            mp_match = self.mp_identifier.identify(mp_name)
            if not mp_match:
                continue
            
            # Parse vote
            if 'aye' in vote_value or 'yes' in vote_value:
                vote = "aye"
            elif 'no' in vote_value or 'nay' in vote_value:
                vote = "no"
            elif 'abstain' in vote_value:
                vote = "abstain"
            else:
                vote = "absent"
            
            mp_votes.append(MPVote(
                mp_id=mp_match.mp_id,
                vote=vote
            ))
        
        # Calculate totals
        ayes = sum(1 for v in mp_votes if v.vote == "aye")
        noes = sum(1 for v in mp_votes if v.vote == "no")
        abstentions = sum(1 for v in mp_votes if v.vote == "abstain")
        
        return VoteRecord(
            vote_id=str(uuid.uuid4()),
            session_id="",  # Set from context
            date=date.today(),  # Extract from PDF
            motion_text=motion_text,
            vote_type="division",
            result="passed" if ayes > noes else "failed",
            ayes=ayes,
            noes=noes,
            abstentions=abstentions,
            mp_votes=mp_votes
        )
```

### Correctness Properties

**Property 7.1**: Vote extraction completeness
- **Validates**: Requirements 1.14
- **Property**: All votes in PDF must be extracted
- **Test Strategy**: Manual count vs extracted count for 10 PDFs

**Property 7.2**: MP vote accuracy
- **Validates**: Requirements 1.14
- **Property**: MP votes must match source document
- **Test Strategy**: Sample 50 MP votes, verify against PDF


## Design 8: Bill-Statement Correlation

### Component Design

**Purpose**: Link statements to bills they discuss

**Technology**: NER for bill mentions + vector similarity + rule-based matching

### Bill Mention Patterns

Bills are mentioned as:
- "The Finance Bill, 2024"
- "Bill No. 15 of 2024"
- "the Bill" (contextual reference)

### Implementation

```python
@dataclass
class BillMention:
    """A mention of a bill in a statement"""
    bill_id: str
    bill_title: str
    mention_text: str
    confidence: float
    context: str  # Surrounding text

class BillStatementLinker:
    """Link statements to bills"""
    
    def __init__(self, db_session, vector_db):
        self.db = db_session
        self.vector_db = vector_db
        
        # Bill mention patterns
        self.patterns = [
            re.compile(r'(?:The\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Bill,?\s+(\d{4})'),
            re.compile(r'Bill\s+No\.\s+(\d+)\s+of\s+(\d{4})'),
            re.compile(r'the\s+Bill', re.IGNORECASE),
        ]
    
    def find_bill_mentions(self, statement: Statement) -> List[BillMention]:
        """Find all bill mentions in statement"""
        mentions = []
        
        # Pattern-based extraction
        for pattern in self.patterns:
            for match in pattern.finditer(statement.text):
                mention_text = match.group(0)
                
                # Try to resolve to specific bill
                bill = self._resolve_bill(mention_text, statement)
                if bill:
                    mentions.append(BillMention(
                        bill_id=str(bill.id),
                        bill_title=bill.title,
                        mention_text=mention_text,
                        confidence=0.90,
                        context=self._extract_context(statement.text, match.start())
                    ))
        
        return mentions
    
    def _resolve_bill(self, mention_text: str, statement: Statement) -> Optional[BillORM]:
        """Resolve bill mention to database record"""
        # Try exact title match
        bills = self.db.query(BillORM).filter(
            BillORM.title.ilike(f"%{mention_text}%")
        ).all()
        
        if len(bills) == 1:
            return bills[0]
        
        # Try vector similarity
        if len(bills) > 1:
            # Use statement context to disambiguate
            query_embedding = self.vector_db.embed(statement.text)
            
            best_bill = None
            best_score = 0
            
            for bill in bills:
                bill_embedding = self.vector_db.embed(bill.title + " " + bill.summary)
                score = cosine_similarity(query_embedding, bill_embedding)
                
                if score > best_score:
                    best_score = score
                    best_bill = bill
            
            if best_score > 0.7:
                return best_bill
        
        return None
    
    def _extract_context(self, text: str, position: int, window: int = 100) -> str:
        """Extract context around mention"""
        start = max(0, position - window)
        end = min(len(text), position + window)
        return text[start:end]
```

### Correctness Properties

**Property 8.1**: Bill mention detection recall
- **Validates**: Requirements 1.15
- **Property**: ≥90% of bill mentions must be detected
- **Test Strategy**: Manually annotate 50 statements, measure recall

**Property 8.2**: Bill resolution accuracy
- **Validates**: Requirements 1.15
- **Property**: Resolved bills must be correct
- **Test Strategy**: Verify 100 resolved bills against manual annotation


## Design 9: MP Profile Generation

### Component Design

**Purpose**: Generate comprehensive MP profiles from aggregated data

**Technology**: SQL aggregation + LLM summarization

### MP Profile Schema

```python
@dataclass
class MPProfile:
    """Comprehensive MP profile"""
    mp_id: str
    name: str
    constituency: str
    party: str
    
    # Activity metrics
    total_statements: int
    substantive_statements: int
    avg_quality_score: float
    
    # Participation
    sessions_attended: int
    votes_cast: int
    votes_aye: int
    votes_no: int
    votes_abstain: int
    
    # Topics
    top_topics: List[Tuple[str, int]]  # (topic, count)
    
    # Bills
    bills_sponsored: List[str]
    bills_discussed: List[str]
    
    # Sentiment
    avg_sentiment: str
    sentiment_distribution: Dict[str, int]
    
    # Generated summary
    summary: str
    key_positions: List[str]

class MPProfileGenerator:
    """Generate MP profiles"""
    
    def __init__(self, db_session, llm_analyzer: LLMAnalyzer):
        self.db = db_session
        self.llm = llm_analyzer
    
    def generate_profile(self, mp_id: str) -> MPProfile:
        """Generate comprehensive MP profile"""
        # Fetch MP data
        mp = self.db.query(MPORM).filter(MPORM.id == mp_id).first()
        if not mp:
            raise ValueError(f"MP not found: {mp_id}")
        
        # Aggregate statistics
        stats = self._aggregate_statistics(mp_id)
        
        # Generate summary
        summary = self._generate_summary(mp, stats)
        
        return MPProfile(
            mp_id=str(mp.id),
            name=mp.name,
            constituency=mp.constituency,
            party=mp.party,
            **stats,
            summary=summary
        )
    
    def _aggregate_statistics(self, mp_id: str) -> Dict:
        """Aggregate MP statistics from database"""
        from sqlalchemy import func
        
        # Statement counts
        total_statements = self.db.query(func.count(StatementORM.id)).filter(
            StatementORM.mp_id == mp_id
        ).scalar()
        
        substantive_statements = self.db.query(func.count(StatementORM.id)).filter(
            StatementORM.mp_id == mp_id,
            StatementORM.statement_type == 'substantive'
        ).scalar()
        
        # Quality score
        avg_quality = self.db.query(func.avg(StatementORM.quality_score)).filter(
            StatementORM.mp_id == mp_id
        ).scalar() or 0.0
        
        # Vote counts
        votes = self.db.query(MPVoteORM).filter(
            MPVoteORM.mp_id == mp_id
        ).all()
        
        votes_aye = sum(1 for v in votes if v.vote == 'aye')
        votes_no = sum(1 for v in votes if v.vote == 'no')
        votes_abstain = sum(1 for v in votes if v.vote == 'abstain')
        
        # Top topics
        top_topics = self.db.query(
            StatementORM.primary_topic,
            func.count(StatementORM.id)
        ).filter(
            StatementORM.mp_id == mp_id
        ).group_by(
            StatementORM.primary_topic
        ).order_by(
            func.count(StatementORM.id).desc()
        ).limit(5).all()
        
        return {
            'total_statements': total_statements,
            'substantive_statements': substantive_statements,
            'avg_quality_score': float(avg_quality),
            'votes_cast': len(votes),
            'votes_aye': votes_aye,
            'votes_no': votes_no,
            'votes_abstain': votes_abstain,
            'top_topics': top_topics,
        }
    
    def _generate_summary(self, mp: MPORM, stats: Dict) -> str:
        """Generate LLM summary of MP"""
        prompt = f"""Generate a brief profile summary for this MP:

Name: {mp.name}
Constituency: {mp.constituency}
Party: {mp.party}

Statistics:
- Total statements: {stats['total_statements']}
- Substantive statements: {stats['substantive_statements']}
- Average quality score: {stats['avg_quality_score']:.1f}/100
- Votes cast: {stats['votes_cast']}
- Top topics: {', '.join(t[0] for t in stats['top_topics'][:3])}

Write a 2-3 sentence summary highlighting their key focus areas and participation level."""
        
        response = self.llm.client.messages.create(
            model=self.llm.model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
```

### Correctness Properties

**Property 9.1**: Profile completeness
- **Validates**: Requirements 1.16
- **Property**: All profile fields must be populated
- **Test Strategy**: Verify no null fields for 50 profiles

**Property 9.2**: Statistics accuracy
- **Validates**: Requirements 1.16
- **Property**: Aggregated statistics must match raw data
- **Test Strategy**: Manually verify statistics for 10 MPs


## Design 10: Session Summary Generation

### Component Design

**Purpose**: Generate summaries of parliamentary sessions

**Technology**: LLM summarization with structured output

### Session Summary Schema

```python
@dataclass
class SessionSummary:
    """Summary of a parliamentary session"""
    session_id: str
    date: date
    session_type: str  # "morning", "afternoon", "evening"
    
    # Overview
    title: str
    summary: str  # 2-3 paragraphs
    
    # Key events
    key_debates: List[str]
    bills_discussed: List[str]
    votes_held: List[str]
    
    # Participation
    total_mps_present: int
    total_statements: int
    
    # Topics
    main_topics: List[str]

class SessionSummaryGenerator:
    """Generate session summaries"""
    
    def __init__(self, db_session, llm_analyzer: LLMAnalyzer):
        self.db = db_session
        self.llm = llm_analyzer
    
    def generate_summary(self, session_id: str) -> SessionSummary:
        """Generate session summary"""
        # Fetch session data
        session = self.db.query(SessionORM).filter(
            SessionORM.id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Fetch statements
        statements = self.db.query(StatementORM).filter(
            StatementORM.session_id == session_id,
            StatementORM.statement_type == 'substantive'
        ).all()
        
        # Generate summary with LLM
        summary_text = self._generate_llm_summary(session, statements)
        
        # Extract structured data
        return self._parse_summary(session, statements, summary_text)
    
    def _generate_llm_summary(
        self,
        session: SessionORM,
        statements: List[StatementORM]
    ) -> str:
        """Generate summary using LLM"""
        # Build context from statements
        context = "\n\n".join([
            f"MP: {s.mp.name}\nTopic: {s.primary_topic}\nKey points: {', '.join(s.key_points[:3])}"
            for s in statements[:20]  # Limit to top 20 statements
        ])
        
        prompt = f"""Summarize this parliamentary session:

Date: {session.date}
Type: {session.session_type}

Key statements:
{context}

Provide:
1. A title for the session (5-10 words)
2. A 2-3 paragraph summary of main discussions
3. List of key debates (3-5 items)
4. Main topics discussed (3-5 topics)

Format as JSON:
{{
  "title": "...",
  "summary": "...",
  "key_debates": ["...", "..."],
  "main_topics": ["...", "..."]
}}"""
        
        response = self.llm.client.messages.create(
            model=self.llm.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def _parse_summary(
        self,
        session: SessionORM,
        statements: List[StatementORM],
        summary_text: str
    ) -> SessionSummary:
        """Parse LLM output into structured summary"""
        import json
        
        data = json.loads(summary_text)
        
        # Get bills and votes
        bills = self.db.query(BillORM).join(
            BillStatementLinkORM
        ).filter(
            BillStatementLinkORM.statement_id.in_([s.id for s in statements])
        ).distinct().all()
        
        votes = self.db.query(VoteRecordORM).filter(
            VoteRecordORM.session_id == session.id
        ).all()
        
        return SessionSummary(
            session_id=str(session.id),
            date=session.date,
            session_type=session.session_type,
            title=data['title'],
            summary=data['summary'],
            key_debates=data['key_debates'],
            bills_discussed=[b.title for b in bills],
            votes_held=[v.motion_text for v in votes],
            total_mps_present=len(set(s.mp_id for s in statements)),
            total_statements=len(statements),
            main_topics=data['main_topics']
        )
```

### Correctness Properties

**Property 10.1**: Summary accuracy
- **Validates**: Requirements 1.17
- **Property**: Summary must reflect actual session content
- **Test Strategy**: Manual review of 20 summaries against source

**Property 10.2**: Key event extraction
- **Validates**: Requirements 1.17
- **Property**: All major debates/votes must be mentioned
- **Test Strategy**: Verify completeness for 10 sessions


## Design 11: Static Site Generation

### Component Design

**Purpose**: Generate static HTML site from processed data

**Technology**: Jinja2 templates + Python static site generator

### Site Structure

```
output/
├── index.html                    # Homepage with recent sessions
├── mps/
│   ├── index.html               # MP directory
│   └── [mp-slug].html           # Individual MP pages
├── sessions/
│   ├── index.html               # Session list
│   └── [date]-[type].html       # Session pages
├── bills/
│   ├── index.html               # Bill tracker
│   └── [bill-slug].html         # Bill pages
├── parties/
│   ├── index.html               # Party list
│   └── [party-slug].html        # Party pages
├── search/
│   └── index.html               # Search interface
└── static/
    ├── css/
    ├── js/
    └── images/
```

### Implementation

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import List

class StaticSiteGenerator:
    """Generate static HTML site"""
    
    def __init__(self, db_session, template_dir: Path, output_dir: Path):
        self.db = db_session
        self.output_dir = output_dir
        
        # Setup Jinja2
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
        
        # Register filters
        self.env.filters['slugify'] = self._slugify
        self.env.filters['format_date'] = self._format_date
    
    def generate_site(self):
        """Generate complete static site"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate pages
        self._generate_homepage()
        self._generate_mp_pages()
        self._generate_session_pages()
        self._generate_bill_pages()
        self._generate_party_pages()
        self._generate_search_page()
        
        # Copy static assets
        self._copy_static_assets()
    
    def _generate_homepage(self):
        """Generate homepage"""
        # Fetch recent sessions
        recent_sessions = self.db.query(SessionORM).order_by(
            SessionORM.date.desc()
        ).limit(10).all()
        
        # Fetch statistics
        stats = {
            'total_mps': self.db.query(MPORM).count(),
            'total_sessions': self.db.query(SessionORM).count(),
            'total_statements': self.db.query(StatementORM).count(),
            'total_bills': self.db.query(BillORM).count(),
        }
        
        # Render template
        template = self.env.get_template('homepage.html')
        html = template.render(
            recent_sessions=recent_sessions,
            stats=stats
        )
        
        # Write file
        (self.output_dir / 'index.html').write_text(html)
    
    def _generate_mp_pages(self):
        """Generate MP pages"""
        mps = self.db.query(MPORM).all()
        
        # MP directory
        template = self.env.get_template('mp_list.html')
        html = template.render(mps=mps)
        mp_dir = self.output_dir / 'mps'
        mp_dir.mkdir(exist_ok=True)
        (mp_dir / 'index.html').write_text(html)
        
        # Individual MP pages
        template = self.env.get_template('mp_profile.html')
        for mp in mps:
            # Fetch MP data
            profile = self._get_mp_profile(mp.id)
            
            html = template.render(mp=mp, profile=profile)
            filename = f"{self._slugify(mp.name)}.html"
            (mp_dir / filename).write_text(html)
    
    def _generate_session_pages(self):
        """Generate session pages"""
        sessions = self.db.query(SessionORM).all()
        
        # Session list
        template = self.env.get_template('session_list.html')
        html = template.render(sessions=sessions)
        session_dir = self.output_dir / 'sessions'
        session_dir.mkdir(exist_ok=True)
        (session_dir / 'index.html').write_text(html)
        
        # Individual session pages
        template = self.env.get_template('session_detail.html')
        for session in sessions:
            summary = self._get_session_summary(session.id)
            statements = self.db.query(StatementORM).filter(
                StatementORM.session_id == session.id
            ).all()
            
            html = template.render(
                session=session,
                summary=summary,
                statements=statements
            )
            filename = f"{session.date}-{session.session_type}.html"
            (session_dir / filename).write_text(html)
    
    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug"""
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text.strip('-')
    
    def _format_date(self, date_obj) -> str:
        """Format date for display"""
        return date_obj.strftime('%B %d, %Y')
```

### Correctness Properties

**Property 11.1**: Page generation completeness
- **Validates**: Requirements 1.18
- **Property**: All entities must have generated pages
- **Test Strategy**: Count database records vs generated files

**Property 11.2**: Link validity
- **Validates**: Requirements 1.18
- **Property**: All internal links must be valid
- **Test Strategy**: Crawl site, verify no 404s


## Design 12: Pipeline Orchestration

### Component Design

**Purpose**: Orchestrate the complete processing pipeline

**Technology**: Python orchestrator with dependency management

### Pipeline Stages

```python
from enum import Enum
from dataclasses import dataclass
from typing import Callable, List

class PipelineStage(Enum):
    """Pipeline processing stages"""
    DOWNLOAD = "download"
    TEXT_EXTRACTION = "text_extraction"
    MP_IDENTIFICATION = "mp_identification"
    SEGMENTATION = "segmentation"
    CLASSIFICATION = "classification"
    CONTEXT_RETRIEVAL = "context_retrieval"
    LLM_ANALYSIS = "llm_analysis"
    CITATION_VERIFICATION = "citation_verification"
    VOTE_PROCESSING = "vote_processing"
    BILL_LINKING = "bill_linking"
    PROFILE_GENERATION = "profile_generation"
    SUMMARY_GENERATION = "summary_generation"
    SITE_GENERATION = "site_generation"

@dataclass
class PipelineResult:
    """Result of pipeline execution"""
    stage: PipelineStage
    success: bool
    duration: float
    items_processed: int
    errors: List[str]

class ProcessingPipeline:
    """Orchestrate document processing pipeline"""
    
    def __init__(self, config: dict):
        self.config = config
        self.db = self._init_database()
        self.vector_db = self._init_vector_db()
        
        # Initialize components
        self.mp_identifier = MPIdentifier(self.db)
        self.segmenter = StatementSegmenter(self.mp_identifier)
        self.filler_detector = FillerDetector()
        self.context_retriever = ContextRetriever(self.vector_db)
        self.llm_analyzer = LLMAnalyzer(config['anthropic_api_key'])
        self.citation_verifier = CitationVerifier(self.db)
        self.vote_processor = VoteProcessor(self.db, self.mp_identifier)
        self.bill_linker = BillStatementLinker(self.db, self.vector_db)
        self.profile_generator = MPProfileGenerator(self.db, self.llm_analyzer)
        self.summary_generator = SessionSummaryGenerator(self.db, self.llm_analyzer)
        self.site_generator = StaticSiteGenerator(
            self.db,
            Path(config['template_dir']),
            Path(config['output_dir'])
        )
    
    def process_hansard(self, pdf_path: Path) -> List[PipelineResult]:
        """Process a Hansard PDF through complete pipeline"""
        results = []
        
        try:
            # Stage 1: Text extraction
            result = self._run_stage(
                PipelineStage.TEXT_EXTRACTION,
                lambda: self._extract_text(pdf_path)
            )
            results.append(result)
            text = result.data
            
            # Stage 2: MP identification & segmentation
            result = self._run_stage(
                PipelineStage.SEGMENTATION,
                lambda: self.segmenter.segment(text, session_id="")
            )
            results.append(result)
            statements = result.data
            
            # Stage 3: Classification
            result = self._run_stage(
                PipelineStage.CLASSIFICATION,
                lambda: [
                    (stmt, self.filler_detector.classify(stmt))
                    for stmt in statements
                ]
            )
            results.append(result)
            classified = result.data
            
            # Filter substantive statements
            substantive = [
                stmt for stmt, (type_, _) in classified
                if type_ == StatementType.SUBSTANTIVE
            ]
            
            # Stage 4: Context retrieval
            result = self._run_stage(
                PipelineStage.CONTEXT_RETRIEVAL,
                lambda: [
                    (stmt, self.context_retriever.retrieve(stmt))
                    for stmt in substantive
                ]
            )
            results.append(result)
            with_context = result.data
            
            # Stage 5: LLM analysis
            result = self._run_stage(
                PipelineStage.LLM_ANALYSIS,
                lambda: [
                    (stmt, self.llm_analyzer.analyze(stmt, ctx))
                    for stmt, ctx in with_context
                ]
            )
            results.append(result)
            analyzed = result.data
            
            # Stage 6: Citation verification
            result = self._run_stage(
                PipelineStage.CITATION_VERIFICATION,
                lambda: self._verify_citations(analyzed)
            )
            results.append(result)
            
            # Stage 7: Bill linking
            result = self._run_stage(
                PipelineStage.BILL_LINKING,
                lambda: [
                    self.bill_linker.find_bill_mentions(stmt)
                    for stmt, _ in analyzed
                ]
            )
            results.append(result)
            
            # Store results
            self._store_results(analyzed)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results.append(PipelineResult(
                stage=PipelineStage.DOWNLOAD,
                success=False,
                duration=0,
                items_processed=0,
                errors=[str(e)]
            ))
        
        return results
    
    def _run_stage(
        self,
        stage: PipelineStage,
        func: Callable
    ) -> PipelineResult:
        """Run a pipeline stage with timing and error handling"""
        import time
        
        start = time.time()
        try:
            data = func()
            duration = time.time() - start
            
            return PipelineResult(
                stage=stage,
                success=True,
                duration=duration,
                items_processed=len(data) if isinstance(data, list) else 1,
                errors=[],
                data=data
            )
        except Exception as e:
            duration = time.time() - start
            logger.error(f"Stage {stage} failed: {e}")
            
            return PipelineResult(
                stage=stage,
                success=False,
                duration=duration,
                items_processed=0,
                errors=[str(e)],
                data=None
            )
```

### Correctness Properties

**Property 12.1**: Pipeline completeness
- **Validates**: Requirements 1.13
- **Property**: All stages must execute for each document
- **Test Strategy**: Verify all stages run for 10 documents

**Property 12.2**: Error recovery
- **Validates**: Requirements 1.13
- **Property**: Pipeline failures must not corrupt database
- **Test Strategy**: Inject errors, verify database consistency


## Design 13: Cost Management

### Component Design

**Purpose**: Monitor and control LLM API costs

**Technology**: Usage tracking + rate limiting + caching

### Cost Tracking

```python
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict

@dataclass
class APIUsage:
    """Track API usage"""
    date: date
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    requests: int

class CostManager:
    """Manage and monitor API costs"""
    
    def __init__(self, db_session, monthly_budget: float = 20.0):
        self.db = db_session
        self.monthly_budget = monthly_budget
        
        # Cost per 1M tokens (Claude 3.5 Haiku)
        self.costs = {
            'input': 0.80,   # $0.80 per 1M tokens
            'output': 4.00,  # $4.00 per 1M tokens
        }
        
        # Cache for analysis results
        self.cache = {}
    
    def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ):
        """Track API usage"""
        cost = (
            (input_tokens / 1_000_000) * self.costs['input'] +
            (output_tokens / 1_000_000) * self.costs['output']
        )
        
        usage = APIUsage(
            date=date.today(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            requests=1
        )
        
        # Store in database
        self._store_usage(usage)
        
        # Check budget
        self._check_budget()
    
    def get_monthly_usage(self) -> Dict:
        """Get current month usage"""
        from sqlalchemy import func
        from datetime import datetime
        
        current_month = datetime.now().replace(day=1)
        
        result = self.db.query(
            func.sum(APIUsageORM.input_tokens),
            func.sum(APIUsageORM.output_tokens),
            func.sum(APIUsageORM.cost_usd),
            func.count(APIUsageORM.id)
        ).filter(
            APIUsageORM.date >= current_month
        ).first()
        
        return {
            'input_tokens': result[0] or 0,
            'output_tokens': result[1] or 0,
            'cost_usd': result[2] or 0.0,
            'requests': result[3] or 0,
            'budget_remaining': self.monthly_budget - (result[2] or 0.0)
        }
    
    def _check_budget(self):
        """Check if budget exceeded"""
        usage = self.get_monthly_usage()
        
        if usage['budget_remaining'] < 0:
            logger.warning(
                f"Monthly budget exceeded! "
                f"Used: ${usage['cost_usd']:.2f}, "
                f"Budget: ${self.monthly_budget:.2f}"
            )
            raise BudgetExceededError(
                f"Monthly budget of ${self.monthly_budget} exceeded"
            )
        
        if usage['budget_remaining'] < 2.0:
            logger.warning(
                f"Approaching budget limit! "
                f"Remaining: ${usage['budget_remaining']:.2f}"
            )
    
    def cache_analysis(self, statement_id: str, analysis: StatementAnalysis):
        """Cache analysis result"""
        self.cache[statement_id] = analysis
    
    def get_cached_analysis(self, statement_id: str) -> Optional[StatementAnalysis]:
        """Get cached analysis"""
        return self.cache.get(statement_id)
```

### Cost Optimization Strategies

1. **Caching**: Cache analysis results to avoid reprocessing
2. **Batching**: Process multiple statements in single API call
3. **Filtering**: Skip filler statements (saves ~30% of calls)
4. **Context pruning**: Limit context window size
5. **Model selection**: Use Haiku for simple tasks, Sonnet for complex

### Correctness Properties

**Property 13.1**: Cost tracking accuracy
- **Validates**: Requirements 1.19
- **Property**: Tracked costs must match actual API usage
- **Test Strategy**: Compare tracked costs with API billing

**Property 13.2**: Budget enforcement
- **Validates**: Requirements 1.19
- **Property**: Processing must stop when budget exceeded
- **Test Strategy**: Set low budget, verify processing stops


## Design 14: Monitoring and Observability

### Component Design

**Purpose**: Monitor pipeline health and performance

**Technology**: Prometheus metrics + structured logging

### Metrics

```python
from prometheus_client import Counter, Histogram, Gauge
import structlog

# Define metrics
statements_processed = Counter(
    'statements_processed_total',
    'Total statements processed',
    ['status', 'type']
)

processing_duration = Histogram(
    'processing_duration_seconds',
    'Time to process document',
    ['stage']
)

llm_api_calls = Counter(
    'llm_api_calls_total',
    'Total LLM API calls',
    ['model', 'status']
)

llm_tokens = Counter(
    'llm_tokens_total',
    'Total LLM tokens used',
    ['model', 'type']  # type: input/output
)

pipeline_errors = Counter(
    'pipeline_errors_total',
    'Total pipeline errors',
    ['stage', 'error_type']
)

active_processing = Gauge(
    'active_processing_jobs',
    'Number of active processing jobs'
)

class MonitoringService:
    """Monitor pipeline execution"""
    
    def __init__(self):
        self.logger = structlog.get_logger()
    
    def track_statement_processed(
        self,
        status: str,
        statement_type: str
    ):
        """Track statement processing"""
        statements_processed.labels(
            status=status,
            type=statement_type
        ).inc()
    
    def track_stage_duration(
        self,
        stage: str,
        duration: float
    ):
        """Track stage processing time"""
        processing_duration.labels(stage=stage).observe(duration)
    
    def track_llm_call(
        self,
        model: str,
        status: str,
        input_tokens: int,
        output_tokens: int
    ):
        """Track LLM API call"""
        llm_api_calls.labels(model=model, status=status).inc()
        llm_tokens.labels(model=model, type='input').inc(input_tokens)
        llm_tokens.labels(model=model, type='output').inc(output_tokens)
    
    def track_error(
        self,
        stage: str,
        error_type: str,
        error: Exception
    ):
        """Track pipeline error"""
        pipeline_errors.labels(
            stage=stage,
            error_type=error_type
        ).inc()
        
        self.logger.error(
            "pipeline_error",
            stage=stage,
            error_type=error_type,
            error=str(error)
        )
```

### Logging Configuration

```python
import structlog

def configure_logging():
    """Configure structured logging"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

### Correctness Properties

**Property 14.1**: Metrics accuracy
- **Validates**: Requirements 1.21
- **Property**: Metrics must reflect actual processing
- **Test Strategy**: Compare metrics with database counts

**Property 14.2**: Error logging completeness
- **Validates**: Requirements 1.21
- **Property**: All errors must be logged
- **Test Strategy**: Inject errors, verify logs


## Implementation Strategy

### Development Approach

**Incremental Implementation**:
1. Build components in dependency order
2. Test each component independently
3. Integrate components progressively
4. Validate end-to-end pipeline

**Testing Strategy**:
- Unit tests for each component (≥90% coverage)
- Property-based tests for correctness properties
- Integration tests for pipeline stages
- End-to-end tests with sample documents

### Component Dependencies

```
Phase 0 (Foundation)
    ↓
MP Identification → Statement Segmentation → Classification
    ↓                       ↓                      ↓
Context Retrieval ← Vector DB (Phase 0)
    ↓
LLM Analysis → Citation Verification
    ↓              ↓
Bill Linking   Vote Processing
    ↓              ↓
Profile Generation ← Session Summary Generation
    ↓
Static Site Generation
```

### Implementation Timeline

**Week 1-2**: Core NLP Components
- MP Identification
- Statement Segmentation
- Classification (Filler Detection)
- Unit tests + property tests

**Week 3-4**: LLM Integration
- Context Retrieval (RAG)
- LLM Analysis
- Citation Verification
- Cost Management
- Integration tests

**Week 5-6**: Document Processing
- Vote Processing
- Bill-Statement Linking
- Profile Generation
- Session Summary Generation

**Week 7-8**: Site Generation & Polish
- Static Site Generator
- Pipeline Orchestration
- Monitoring
- End-to-end tests
- Documentation

### File Structure

```
hansard_tales/
├── analysis/
│   ├── __init__.py
│   ├── mp_identifier.py          # Design 1
│   ├── segmenter.py               # Design 2
│   ├── classifier.py              # Design 3
│   ├── context_retriever.py      # Design 4
│   ├── llm_analyzer.py            # Design 5
│   ├── citation_verifier.py      # Design 6
│   └── bill_linker.py             # Design 8
├── processors/
│   ├── vote_processor.py          # Design 7
│   ├── profile_generator.py      # Design 9
│   └── summary_generator.py      # Design 10
├── pipeline/
│   ├── orchestrator.py            # Design 12
│   ├── cost_manager.py            # Design 13
│   └── monitoring.py              # Design 14
├── site/
│   └── generator.py               # Design 11
└── tests/
    ├── test_mp_identifier.py
    ├── test_segmenter.py
    ├── test_classifier.py
    ├── test_context_retriever.py
    ├── test_llm_analyzer.py
    ├── test_citation_verifier.py
    ├── test_vote_processor.py
    ├── test_bill_linker.py
    ├── test_profile_generator.py
    ├── test_summary_generator.py
    ├── test_site_generator.py
    ├── test_orchestrator.py
    ├── test_cost_manager.py
    └── test_monitoring.py
```

### Configuration

```yaml
# config/phase1.yaml
analysis:
  mp_identification:
    nlp_model: "en_core_web_sm"
    confidence_threshold: 0.85
  
  segmentation:
    min_statement_length: 20
  
  classification:
    filler_threshold: 0.90
  
  context_retrieval:
    embedding_model: "all-MiniLM-L6-v2"
    top_k: 5
  
  llm:
    model: "claude-3-5-haiku-20241022"
    max_tokens: 1024
    temperature: 0.0
  
  cost_management:
    monthly_budget: 20.0
    cache_enabled: true

pipeline:
  workers: 4
  batch_size: 10
  retry_attempts: 3

monitoring:
  prometheus_port: 9090
  log_level: "INFO"
```

### Risk Mitigation

**Risk 1**: LLM costs exceed budget
- **Mitigation**: Aggressive caching, budget enforcement, skip filler statements

**Risk 2**: MP identification accuracy < 95%
- **Mitigation**: Extensive test set, manual review, fuzzy matching fallback

**Risk 3**: Citation verification fails
- **Mitigation**: Multiple verification strategies, manual review queue

**Risk 4**: Processing too slow (>10 min per Hansard)
- **Mitigation**: Parallel processing, optimize LLM calls, profile bottlenecks

**Risk 5**: Vector DB performance issues
- **Mitigation**: Index optimization, query caching, batch operations

## Summary

This design document provides detailed specifications for implementing Phase 1 of the Hansard Tales system. Each component is designed with:

- Clear purpose and technology choices
- Concrete implementation code
- Correctness properties for testing
- Integration points with other components

The design prioritizes:
1. **Anti-hallucination**: Citation verification for all LLM outputs
2. **Cost control**: Budget management and caching
3. **Accuracy**: High thresholds for all NLP tasks
4. **Testability**: Property-based tests for all components
5. **Maintainability**: Clear separation of concerns

Next step: Create `tasks.md` with actionable implementation tasks.
