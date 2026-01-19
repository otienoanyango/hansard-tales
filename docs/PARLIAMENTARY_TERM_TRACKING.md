# Parliamentary Term Tracking

## Overview

Hansard Tales tracks MPs across multiple parliamentary terms, allowing users to view both current performance (13th Parliament: 2022-2027) and historical data from previous terms.

## Key Concepts

### Parliamentary Term
A 5-year period during which parliament operates. Kenya is currently in the **13th Parliament** (2022-2027).

**Historical Terms**:
- 12th Parliament: 2017-2022
- 11th Parliament: 2013-2017
- 10th Parliament: 2008-2013
- etc.

### MP Terms
MPs can serve in multiple parliamentary terms. Their data is tracked separately for each term because:
- **Constituency can change**: An MP might represent different constituencies in different terms
- **Party can change**: MPs can switch parties between or during terms
- **Performance varies**: Users want to compare performance across terms

## Database Design

### Core Tables

```sql
-- Parliamentary terms (e.g., 13th Parliament)
CREATE TABLE parliamentary_terms (
    id INTEGER PRIMARY KEY,
    term_number INTEGER,      -- 13
    start_date DATE,          -- 2022-09-08
    end_date DATE,            -- 2027-09-07 (NULL if ongoing)
    is_current BOOLEAN        -- TRUE for 13th Parliament
);

-- MPs (persistent across terms)
CREATE TABLE mps (
    id INTEGER PRIMARY KEY,
    name TEXT,
    first_elected_year INTEGER,  -- When they first became MP
    photo_url TEXT
);

-- Junction table: Which MPs served in which terms
CREATE TABLE mp_terms (
    id INTEGER PRIMARY KEY,
    mp_id INTEGER,
    term_id INTEGER,
    constituency TEXT,        -- Can change between terms
    party TEXT,              -- Can change between terms
    elected_date DATE,
    left_date DATE,          -- NULL if still serving
    is_current BOOLEAN       -- TRUE if serving in current term
);

-- Hansard sessions linked to specific term
CREATE TABLE hansard_sessions (
    id INTEGER PRIMARY KEY,
    term_id INTEGER,         -- Which parliament
    date DATE,
    pdf_url TEXT
);

-- Statements made by MPs
CREATE TABLE statements (
    id INTEGER PRIMARY KEY,
    mp_id INTEGER,
    session_id INTEGER,      -- Links to hansard_sessions → term
    text TEXT
);
```

### Relationships

```
Parliamentary Term (13th)
    ├── Hansard Sessions (all sessions in 13th Parliament)
    │   └── Statements (all statements in those sessions)
    └── MP Terms (all MPs who served in 13th Parliament)
        └── MPs (the actual MP records)
```

## Use Cases

### Use Case 1: Current MP Performance

**Scenario**: User wants to see how their MP is performing in the current parliament (13th).

**Query**:
```sql
SELECT 
    m.name,
    mt.constituency,
    mt.party,
    COUNT(s.id) as statement_count,
    COUNT(DISTINCT hs.id) as sessions_attended
FROM mps m
JOIN mp_terms mt ON m.id = mt.mp_id
JOIN parliamentary_terms pt ON mt.term_id = pt.id
LEFT JOIN hansard_sessions hs ON hs.term_id = pt.id
LEFT JOIN statements s ON s.mp_id = m.id AND s.session_id = hs.id
WHERE pt.is_current = 1
  AND m.name = 'John Doe'
GROUP BY m.id;
```

**Result**:
```
Name: John Doe
Constituency: Nairobi West
Party: ODM
Statements: 45
Sessions Attended: 12
Term: 13th Parliament (2022-2027)
```

### Use Case 2: Historical Performance

**Scenario**: User wants to see how an MP performed across multiple terms.

**Query**:
```sql
SELECT 
    pt.term_number,
    CONCAT(pt.start_date, ' - ', COALESCE(pt.end_date, 'present')) as years,
    mt.constituency,
    mt.party,
    COUNT(s.id) as statement_count
FROM mps m
JOIN mp_terms mt ON m.id = mt.mp_id
JOIN parliamentary_terms pt ON mt.term_id = pt.id
LEFT JOIN hansard_sessions hs ON hs.term_id = pt.id
LEFT JOIN statements s ON s.mp_id = m.id AND s.session_id = hs.id
WHERE m.name = 'John Doe'
GROUP BY pt.term_number
ORDER BY pt.term_number DESC;
```

**Result**:
```
13th Parliament (2022-present)
  Constituency: Nairobi West
  Party: ODM
  Statements: 45

12th Parliament (2017-2022)
  Constituency: Nairobi West
  Party: ODM
  Statements: 120

11th Parliament (2013-2017)
  Constituency: Nairobi East  ← Changed constituency
  Party: TNA                  ← Changed party
  Statements: 89
```

### Use Case 3: MP Changed Constituency

**Scenario**: MP moved to a different constituency between terms.

**Example**: Jane Smith
- 12th Parliament: Mombasa North, Jubilee
- 13th Parliament: Kilifi South, UDA

**Data**:
```sql
-- MP record (persistent)
INSERT INTO mps (name, first_elected_year) 
VALUES ('Jane Smith', 2017);

-- 12th Parliament term
INSERT INTO mp_terms (mp_id, term_id, constituency, party, elected_date)
VALUES (2, 12, 'Mombasa North', 'Jubilee', '2017-08-31');

-- 13th Parliament term (different constituency and party)
INSERT INTO mp_terms (mp_id, term_id, constituency, party, elected_date, is_current)
VALUES (2, 13, 'Kilifi South', 'UDA', '2022-09-08', 1);
```

### Use Case 4: Filter Statements by Term

**Scenario**: User wants to see only statements from a specific parliamentary term.

**UI**:
```html
<select id="term-filter">
    <option value="13">13th Parliament (2022-present)</option>
    <option value="12">12th Parliament (2017-2022)</option>
    <option value="11">11th Parliament (2013-2017)</option>
</select>
```

**Query**:
```sql
SELECT 
    s.text,
    hs.date,
    pt.term_number
FROM statements s
JOIN hansard_sessions hs ON s.session_id = hs.id
JOIN parliamentary_terms pt ON hs.term_id = pt.id
WHERE s.mp_id = ?
  AND pt.term_number = ?  -- User's selected term
ORDER BY hs.date DESC;
```

## UI/UX Considerations

### MP Profile Page

**Current Term Section** (Prominent):
```
┌─────────────────────────────────────────┐
│ John Doe                                │
│ Nairobi West • ODM                      │
│ 13th Parliament (2022-2027)             │
│                                         │
│ Current Term Performance:               │
│ ├─ 45 Statements                        │
│ ├─ 12 Sessions Attended                 │
│ └─ 3 Bills Mentioned                    │
└─────────────────────────────────────────┘
```

**Historical Terms Section** (Collapsible):
```
┌─────────────────────────────────────────┐
│ Historical Performance ▼                │
│                                         │
│ 12th Parliament (2017-2022)             │
│ Nairobi West • ODM                      │
│ ├─ 120 Statements                       │
│ └─ 35 Sessions Attended                 │
│                                         │
│ 11th Parliament (2013-2017)             │
│ Nairobi East • TNA  ← Changed           │
│ ├─ 89 Statements                        │
│ └─ 28 Sessions Attended                 │
└─────────────────────────────────────────┘
```

**Statement List with Term Filter**:
```
┌─────────────────────────────────────────┐
│ Recent Statements                       │
│                                         │
│ Filter by term: [13th Parliament ▼]    │
│                                         │
│ 2024-01-15 (13th Parliament)            │
│ "I rise to support this bill..."        │
│ [View in Hansard]                       │
│                                         │
│ 2023-12-10 (13th Parliament)            │
│ "The people of Nairobi West..."         │
│ [View in Hansard]                       │
└─────────────────────────────────────────┘
```

## Search Index Format

```json
{
  "current_term": {
    "term_number": 13,
    "start_date": "2022-09-08",
    "end_date": "2027-09-07"
  },
  "mps": [
    {
      "id": 1,
      "name": "John Doe",
      "slug": "john-doe",
      "current_term": {
        "term_number": 13,
        "constituency": "Nairobi West",
        "party": "ODM",
        "statement_count": 45,
        "sessions_attended": 12
      },
      "historical_terms": [
        {
          "term_number": 12,
          "constituency": "Nairobi West",
          "party": "ODM",
          "statement_count": 120,
          "years": "2017-2022"
        },
        {
          "term_number": 11,
          "constituency": "Nairobi East",
          "party": "TNA",
          "statement_count": 89,
          "years": "2013-2017"
        }
      ]
    }
  ]
}
```

## Implementation Notes

### MVP Scope

**Include**:
- ✅ Track current term (13th Parliament: 2022-2027)
- ✅ Database schema supports multiple terms
- ✅ Display current term performance prominently
- ✅ Store historical data if available

**Defer to Phase 2**:
- ❌ Processing historical Hansard PDFs (focus on 2024-2025 first)
- ❌ Complex cross-term comparisons
- ❌ Term-by-term trend analysis

### Data Migration Path

**Phase 1 (MVP)**:
```sql
-- Initialize 13th Parliament
INSERT INTO parliamentary_terms (term_number, start_date, end_date, is_current)
VALUES (13, '2022-09-08', '2027-09-07', 1);

-- Add all 349 current MPs to 13th Parliament
INSERT INTO mp_terms (mp_id, term_id, constituency, party, elected_date, is_current)
SELECT id, 13, constituency, party, '2022-09-08', 1
FROM mps;
```

**Phase 2 (Historical Data)**:
```sql
-- Add 12th Parliament
INSERT INTO parliamentary_terms (term_number, start_date, end_date, is_current)
VALUES (12, '2017-08-31', '2022-09-07', 0);

-- Link MPs who served in 12th Parliament
-- (Manual data entry or scraping historical records)
```

## Benefits

### For Users
1. **Context**: Understand which parliament they're viewing
2. **Comparison**: See how MP performed in previous terms
3. **Accountability**: Track long-term patterns, not just recent activity
4. **Transparency**: See if MP changed constituency or party

### For Platform
1. **Scalability**: Easy to add new parliamentary terms
2. **Flexibility**: Handle MPs who serve multiple terms
3. **Accuracy**: Track term-specific data (constituency, party changes)
4. **Future-proof**: Ready for 14th Parliament in 2027

## Example Queries

### Get all MPs in current term
```sql
SELECT m.name, mt.constituency, mt.party
FROM mps m
JOIN mp_terms mt ON m.id = mt.mp_id
WHERE mt.is_current = 1;
```

### Get MP's performance across all terms
```sql
SELECT 
    pt.term_number,
    mt.constituency,
    mt.party,
    COUNT(s.id) as statements
FROM mps m
JOIN mp_terms mt ON m.id = mt.mp_id
JOIN parliamentary_terms pt ON mt.term_id = pt.id
LEFT JOIN hansard_sessions hs ON hs.term_id = pt.id
LEFT JOIN statements s ON s.mp_id = m.id AND s.session_id = hs.id
WHERE m.name = 'John Doe'
GROUP BY pt.term_number;
```

### Get all statements from a specific term
```sql
SELECT s.text, hs.date, m.name
FROM statements s
JOIN hansard_sessions hs ON s.session_id = hs.id
JOIN parliamentary_terms pt ON hs.term_id = pt.id
JOIN mps m ON s.mp_id = m.id
WHERE pt.term_number = 13
ORDER BY hs.date DESC;
```

## Conclusion

Parliamentary term tracking is essential for:
- Providing proper context to users
- Handling MPs who serve multiple terms
- Tracking constituency and party changes
- Enabling historical analysis

The database design supports this with minimal complexity while remaining flexible for future enhancements.
