# Document Flow and Correlation Architecture

## Overview

This document illustrates how all 22 document types (11 per chamber) flow through the Hansard Tales system and how they correlate with each other to provide comprehensive parliamentary accountability.

## Document Type Matrix

### National Assembly Documents

| Document Type | Update Frequency | Primary Entities | Correlates With | Phase |
|--------------|------------------|------------------|-----------------|-------|
| **Hansard** | Daily (sitting days) | Statements, MPs | Bills, Votes, Questions | 1 |
| **Votes & Proceedings** | Per vote | Votes, MPs, Bills | Hansard, Bills | 1 |
| **Bills** | Per lifecycle stage | Bills, Sponsors | Hansard, Votes, Questions, Petitions | 2 |
| **Questions** | Daily (sitting days) | Questions, MPs, Ministers | Hansard, Bills | 2 |
| **Petitions** | Weekly | Petitions, Petitioners, MPs | Bills, Hansard | 2 |
| **Statements Tracker** | Weekly | Constituency statements, MPs | Hansard | 4 |
| **Motions Tracker** | Weekly | Motions, MPs | Hansard, Votes | 4 |
| **Bills Tracker** | Weekly | Bill status | Bills, Hansard | 4 |
| **Order Papers** | Daily (sitting days) | Agenda items | Hansard, Bills, Questions | 4 |
| **Legislative Proposals** | Per proposal | Proposals, Sponsors | Bills | 4 |
| **Auditor General Reports** | Quarterly/Annually | Audit findings, Entities | Questions, Hansard | 4 |

### Senate Documents

Same 11 document types as National Assembly, with Senate-specific data.

## Data Flow Architecture

### Stage 1: Collection

```
parliament.go.ke
    │
    ├─→ Hansard PDFs ────────────┐
    ├─→ Votes PDFs ──────────────┤
    ├─→ Bills PDFs ──────────────┤
    ├─→ Questions PDFs ──────────┤
    ├─→ Petitions PDFs ──────────┼─→ Download Queue
    ├─→ Statements Tracker PDFs ─┤
    ├─→ Motions Tracker PDFs ────┤
    ├─→ Bills Tracker PDFs ──────┤
    ├─→ Order Papers PDFs ───────┤
    ├─→ Legislative Proposals ───┤
    └─→ AG Reports PDFs ─────────┘
```

### Stage 2: Processing

```
Download Queue
    │
    ├─→ PDF Parser ──────────────┐
    │   ├─ Text extraction       │
    │   ├─ Table extraction      │
    │   ├─ Metadata extraction   │
    │   └─ Page/line tracking    │
    │                             │
    ├─→ Entity Extractor ────────┤
    │   ├─ MP identification     │
    │   ├─ Bill identification   │
    │   ├─ Date extraction       │
    │   └─ Session identification│
    │                             │
    └─→ Embedding Generator ─────┤
        ├─ Document embeddings   │
        └─ Chunk embeddings      │
                                  │
                                  ▼
                        Processed Documents
```

### Stage 3: Storage

```
Processed Documents
    │
    ├─→ PostgreSQL ──────────────┐
    │   ├─ Structured metadata   │
    │   ├─ Entity relationships  │
    │   ├─ Analysis results      │
    │   └─ Source references     │
    │                             │
    └─→ Qdrant ─────────────────┤
        ├─ Full document text    │
        ├─ Embeddings            │
        ├─ Semantic metadata     │
        └─ Cross-references      │
                                  │
                                  ▼
                          Queryable Data Store
```

### Stage 4: Analysis

```
Queryable Data Store
    │
    ├─→ Context Retriever (RAG) ─┐
    │   ├─ Semantic search       │
    │   ├─ Multi-session context │
    │   └─ Cross-doc correlation │
    │                             │
    ├─→ Statement Classifier ────┤
    │   ├─ Filler detection      │
    │   └─ Substantive marking   │
    │                             │
    ├─→ Sentiment Analyzer ──────┤
    │   ├─ LLM analysis          │
    │   ├─ Citation generation   │
    │   └─ Confidence scoring    │
    │                             │
    ├─→ Citation Verifier ───────┤
    │   ├─ Quote matching        │
    │   ├─ Source verification   │
    │   └─ Audit logging         │
    │                             │
    ├─→ Quality Scorer ──────────┤
    │   ├─ Length analysis       │
    │   ├─ Specificity scoring   │
    │   └─ Evidence detection    │
    │                             │
    └─→ Topic Classifier ────────┤
        ├─ Keyword matching      │
        └─ Multi-label assignment│
                                  │
                                  ▼
                          Analyzed Data
```

### Stage 5: Correlation

```
Analyzed Data
    │
    ├─→ Bill Correlator ─────────┐
    │   ├─ Bill ↔ Statements     │
    │   ├─ Bill ↔ Votes          │
    │   ├─ Bill ↔ Questions      │
    │   └─ Bill ↔ Petitions      │
    │                             │
    ├─→ MP Correlator ───────────┤
    │   ├─ MP ↔ Statements       │
    │   ├─ MP ↔ Votes            │
    │   ├─ MP ↔ Questions        │
    │   ├─ MP ↔ Petitions        │
    │   └─ MP ↔ Constituency     │
    │                             │
    └─→ Party Correlator ────────┤
        ├─ Party ↔ Statements    │
        ├─ Party ↔ Votes         │
        └─ Party ↔ Positions     │
                                  │
                                  ▼
                          Correlated Data
```

### Stage 6: Generation

```
Correlated Data
    │
    ├─→ MP Profile Generator ────┐
    ├─→ Senator Profile Generator┤
    ├─→ Party Page Generator ────┤
    ├─→ Bill Page Generator ─────┤
    ├─→ Session Page Generator ──┼─→ Static Site
    ├─→ Weekly Summary Generator ┤
    ├─→ Historical Page Generator┤
    └─→ Search Index Generator ──┘
```

## Cross-Document Correlation Examples

### Example 1: Bill Lifecycle Tracking

```
Bill: "The Finance Bill 2024"
    │
    ├─→ Legislative Proposal (Jan 2024)
    │   └─ Sponsor: MP John Doe
    │
    ├─→ Bill Tracker (Feb 2024)
    │   └─ Status: First Reading
    │
    ├─→ Hansard Statements (Mar 2024)
    │   ├─ MP Jane Smith: "I support this bill because..."
    │   ├─ MP John Doe: "This bill will help..."
    │   └─ MP Alice Brown: "I oppose this bill due to..."
    │
    ├─→ Questions (Mar 2024)
    │   ├─ MP Bob Wilson: "What is the impact on small businesses?"
    │   └─ Minister: "The impact will be minimal because..."
    │
    ├─→ Petitions (Apr 2024)
    │   └─ "Petition against Finance Bill 2024" (5000 signatures)
    │
    ├─→ Votes & Proceedings (May 2024)
    │   ├─ Second Reading: 180 Ayes, 120 Noes
    │   └─ Third Reading: 185 Ayes, 115 Noes
    │
    └─→ Bill Tracker (Jun 2024)
        └─ Status: Passed, awaiting Presidential assent
```

**System Capabilities**:
- Track bill from proposal to law
- Show all MPs who spoke about the bill
- Show all votes on the bill
- Show related questions and petitions
- Analyze sentiment trends over time
- Identify party positions

### Example 2: MP Activity Tracking

```
MP: "John Doe (Nairobi West)"
    │
    ├─→ Hansard Statements
    │   ├─ 150 substantive statements (2024)
    │   ├─ Topics: Healthcare (40), Education (35), Finance (30), ...
    │   ├─ Quality scores: Avg 72/100
    │   └─ Sentiment: 60% support, 30% oppose, 10% neutral
    │
    ├─→ Votes & Proceedings
    │   ├─ 200 votes cast (2024)
    │   ├─ Party alignment: 85%
    │   └─ Key divergences: Finance Bill, Healthcare Bill
    │
    ├─→ Questions
    │   ├─ 25 questions asked (2024)
    │   ├─ Topics: Healthcare (10), Education (8), Infrastructure (7)
    │   └─ Response rate: 80%
    │
    ├─→ Petitions
    │   ├─ 5 petitions sponsored (2024)
    │   └─ Topics: Healthcare (2), Education (2), Infrastructure (1)
    │
    ├─→ Statements Tracker
    │   ├─ 12 constituency statements (2024)
    │   └─ Issues: Water shortage, road repairs, school funding
    │
    └─→ Motions Tracker
        ├─ 3 motions sponsored (2024)
        └─ Topics: Healthcare funding, education reform
```

**System Capabilities**:
- Comprehensive MP performance tracking
- Topic-based activity analysis
- Constituency representation metrics
- Party alignment analysis
- Quality and sentiment trends

### Example 3: Party Position Analysis

```
Party: "Orange Democratic Movement (ODM)"
    │
    ├─→ Hansard Statements (all members)
    │   ├─ Healthcare: 70% support universal coverage
    │   ├─ Education: 85% support increased funding
    │   └─ Finance: 40% support tax increases
    │
    ├─→ Votes & Proceedings (all members)
    │   ├─ Healthcare Bill: 95% voted Yes
    │   ├─ Education Bill: 90% voted Yes
    │   └─ Finance Bill: 60% voted No
    │
    └─→ Questions (all members)
        ├─ Healthcare: 45 questions asked
        ├─ Education: 38 questions asked
        └─ Finance: 52 questions asked
```

**System Capabilities**:
- Aggregate party positions by topic
- Identify party unity/division
- Track party consistency (statements vs votes)
- Compare parties on key issues

## Document Type Relationships

### Primary Relationships

```
Bills ←──────────────────────────────────────┐
  ↑                                           │
  │                                           │
  ├─ Hansard Statements (MPs discuss bills)  │
  ├─ Votes (MPs vote on bills)               │
  ├─ Questions (MPs ask about bills)         │
  ├─ Petitions (Citizens petition on bills)  │
  ├─ Bills Tracker (Status updates)          │
  └─ Legislative Proposals (Bill origins)    │
                                              │
MPs/Senators ←───────────────────────────────┤
  ↑                                           │
  │                                           │
  ├─ Hansard Statements (MPs speak)          │
  ├─ Votes (MPs vote)                        │
  ├─ Questions (MPs ask/answer)              │
  ├─ Petitions (MPs sponsor)                 │
  ├─ Statements Tracker (Constituency work)  │
  ├─ Motions Tracker (MPs move motions)      │
  └─ Legislative Proposals (MPs propose)     │
                                              │
Sessions ←───────────────────────────────────┤
  ↑                                           │
  │                                           │
  ├─ Hansard (Session debates)               │
  ├─ Votes (Session votes)                   │
  ├─ Questions (Session Q&A)                 │
  └─ Order Papers (Session agenda)           │
                                              │
Topics ←─────────────────────────────────────┘
  ↑
  │
  ├─ Bills (Categorized by topic)
  ├─ Statements (Categorized by topic)
  ├─ Questions (Categorized by topic)
  ├─ Petitions (Categorized by topic)
  └─ AG Reports (Categorized by topic)
```

### Secondary Relationships

```
Auditor General Reports
  ↓
  └─→ Questions (MPs ask about audit findings)
      └─→ Hansard (MPs discuss audit findings)

Order Papers
  ↓
  └─→ Hansard (Agenda items discussed)
      └─→ Votes (Agenda items voted on)

Statements Tracker
  ↓
  └─→ Hansard (Constituency issues raised)
      └─→ Questions (Follow-up questions)

Motions Tracker
  ↓
  └─→ Hansard (Motions debated)
      └─→ Votes (Motions voted on)
```

## RAG Context Retrieval Strategy

### For Statement Analysis

When analyzing a statement about a bill:

1. **Retrieve Bill Context**:
   - Current bill text
   - All bill versions (amendments)
   - Bill sponsor and co-sponsors
   - Bill status and history

2. **Retrieve MP Context**:
   - MP's previous statements on this bill
   - MP's votes on this bill
   - MP's questions about this bill
   - MP's party position

3. **Retrieve Related Documents**:
   - Other MPs' statements on this bill
   - Petitions related to this bill
   - Questions related to this bill
   - Auditor reports (if relevant)

4. **Retrieve Temporal Context**:
   - Statements from same session
   - Statements from previous sessions on same bill
   - Recent amendments or votes

### For Bill Analysis

When analyzing a bill:

1. **Retrieve Bill History**:
   - All versions of the bill
   - All amendments
   - Sponsor's statements
   - Committee reports

2. **Retrieve Parliamentary Activity**:
   - All statements mentioning the bill
   - All votes on the bill
   - All questions about the bill
   - All petitions related to the bill

3. **Retrieve Similar Bills**:
   - Bills with similar topics
   - Bills from same sponsor
   - Bills from same committee

### For MP Analysis

When analyzing an MP:

1. **Retrieve MP Activity**:
   - All statements (filtered by substantive)
   - All votes
   - All questions asked/answered
   - All petitions sponsored
   - All motions sponsored
   - All constituency statements

2. **Retrieve Party Context**:
   - Party positions on topics
   - Party voting patterns
   - Other party members' activities

3. **Retrieve Constituency Context**:
   - Constituency-specific statements
   - Constituency-related questions
   - Constituency-related petitions

## Storage Optimization

### PostgreSQL Schema

```sql
-- Core entities
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    chamber VARCHAR(20) NOT NULL,
    title TEXT NOT NULL,
    date DATE NOT NULL,
    session_id UUID,
    source_url TEXT NOT NULL,
    source_hash VARCHAR(64) NOT NULL,
    vector_doc_id VARCHAR(100) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE statements (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    mp_id UUID REFERENCES mps(id),
    text TEXT NOT NULL,
    page_number INT,
    line_number INT,
    vector_doc_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE bills (
    id UUID PRIMARY KEY,
    bill_number VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    chamber VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL,
    sponsor_id UUID REFERENCES mps(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE votes (
    id UUID PRIMARY KEY,
    bill_id UUID REFERENCES bills(id),
    mp_id UUID REFERENCES mps(id),
    direction VARCHAR(20) NOT NULL,
    vote_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Correlation tables
CREATE TABLE bill_statements (
    bill_id UUID REFERENCES bills(id),
    statement_id UUID REFERENCES statements(id),
    relevance_score FLOAT,
    PRIMARY KEY (bill_id, statement_id)
);

CREATE TABLE bill_questions (
    bill_id UUID REFERENCES bills(id),
    question_id UUID REFERENCES questions(id),
    relevance_score FLOAT,
    PRIMARY KEY (bill_id, question_id)
);

CREATE TABLE bill_petitions (
    bill_id UUID REFERENCES bills(id),
    petition_id UUID REFERENCES petitions(id),
    relevance_score FLOAT,
    PRIMARY KEY (bill_id, petition_id)
);
```

### Qdrant Collections

```python
# Collection: documents
{
    "name": "documents",
    "vectors": {
        "size": 384,  # all-MiniLM-L6-v2
        "distance": "Cosine"
    },
    "payload_schema": {
        "document_id": "keyword",
        "document_type": "keyword",
        "chamber": "keyword",
        "date": "datetime",
        "mp_id": "keyword",
        "bill_id": "keyword",
        "session_id": "keyword",
        "topics": "keyword[]"
    }
}

# Collection: statements
{
    "name": "statements",
    "vectors": {
        "size": 384,
        "distance": "Cosine"
    },
    "payload_schema": {
        "statement_id": "keyword",
        "document_id": "keyword",
        "mp_id": "keyword",
        "chamber": "keyword",
        "date": "datetime",
        "bill_ids": "keyword[]",
        "topics": "keyword[]",
        "classification": "keyword",
        "quality_score": "float"
    }
}
```

## Query Patterns

### Pattern 1: Find all activity on a bill

```python
# PostgreSQL
bill_statements = db.query(Statement).join(
    bill_statements_table
).filter(
    bill_statements_table.c.bill_id == bill_id
).all()

bill_votes = db.query(Vote).filter(
    Vote.bill_id == bill_id
).all()

bill_questions = db.query(Question).join(
    bill_questions_table
).filter(
    bill_questions_table.c.bill_id == bill_id
).all()

# Qdrant (semantic search)
related_docs = qdrant.search(
    collection_name="documents",
    query_vector=bill_embedding,
    query_filter={
        "must": [
            {"key": "bill_id", "match": {"value": bill_id}}
        ]
    },
    limit=100
)
```

### Pattern 2: Find MP activity by topic

```python
# PostgreSQL
mp_statements = db.query(Statement).join(
    statement_topics_table
).filter(
    Statement.mp_id == mp_id,
    statement_topics_table.c.topic_id == topic_id
).all()

# Qdrant (semantic search)
topic_statements = qdrant.search(
    collection_name="statements",
    query_vector=topic_embedding,
    query_filter={
        "must": [
            {"key": "mp_id", "match": {"value": mp_id}},
            {"key": "topics", "match": {"any": [topic_id]}}
        ]
    },
    limit=100
)
```

### Pattern 3: Find similar bills

```python
# Qdrant (semantic search)
similar_bills = qdrant.search(
    collection_name="documents",
    query_vector=bill_embedding,
    query_filter={
        "must": [
            {"key": "document_type", "match": {"value": "bill"}},
            {"key": "chamber", "match": {"value": chamber}}
        ]
    },
    limit=10
)
```

## Next Steps

1. Review MASTER_ARCHITECTURE.md for complete system design
2. Review phase-specific requirements for detailed specifications
3. Implement phases sequentially (0 → 1 → 2 → 3 → 4 → 5)
4. Test cross-document correlation at each phase
5. Monitor storage and performance as data grows

