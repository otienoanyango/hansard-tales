# Hansard Tales MVP - Design Document (Simplified Architecture)

## 1. Design Philosophy

### 1.1 Core Principles
- **Simplicity First**: Single language, minimal dependencies, easy to understand
- **Cost Optimization**: Target £10-30/month, use free tiers aggressively
- **Solo Maintainable**: One person can build, deploy, and maintain
- **No Vendor Lock-in**: Can run anywhere, not tied to specific cloud provider
- **Ship Fast**: Focus on core value, defer complexity

### 1.2 Anti-Patterns to Avoid
- ❌ Multiple programming languages (Go + Python + Node.js)
- ❌ Complex microservices architecture
- ❌ Expensive AI for everything
- ❌ Over-engineered for scale
- ❌ Premature optimization

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  GitHub Repository                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Weekly Processing (GitHub Actions Cron)          │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │  1. Scrape Hansard PDFs                     │ │ │
│  │  │  2. Extract text (pdfplumber)               │ │ │
│  │  │  3. Identify MPs (regex + spaCy)            │ │ │
│  │  │  4. Extract bill references                 │ │ │
│  │  │  5. Update SQLite database                  │ │ │
│  │  │  6. Generate search index JSON              │ │ │
│  │  │  7. Generate static HTML (Hugo/Jinja2)      │ │ │
│  │  │  8. Commit & push changes                   │ │ │
│  │  └─────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Data Storage (Git-versioned)                     │ │
│  │  - data/hansard.db (SQLite)                       │ │
│  │  - data/pdfs/ (downloaded Hansard PDFs)           │ │
│  │  - output/ (generated static site)                │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓
                   (Git push triggers)
                          ↓
┌─────────────────────────────────────────────────────────┐
│              Cloudflare Pages (Free Tier)               │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Static Website                                   │ │
│  │  - /index.html (homepage with search)             │ │
│  │  - /mp/john-doe.html (349 MP pages)               │ │
│  │  - /party/odm.html (party pages)                  │ │
│  │  - /data/mp-search-index.json                     │ │
│  │  - /js/search.js (Fuse.js client-side search)    │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Features:                                              │
│  ✓ Global CDN (free)                                   │
│  ✓ Auto HTTPS (free)                                   │
│  ✓ DDoS protection (free)                              │
│  ✓ Unlimited bandwidth (free tier: 500 builds/month)  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    End Users                            │
│  📱 Mobile Users (Primary) | 💻 Desktop Users          │
│  - Fast static pages                                    │
│  - Client-side search (no backend)                      │
│  - Works on slow 3G networks                            │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
Weekly Batch Process:
┌──────────────┐
│ 1. Scrape    │ → Download new Hansard PDFs from parliament.go.ke
└──────────────┘
       ↓
┌──────────────┐
│ 2. Extract   │ → pdfplumber extracts text from PDFs
└──────────────┘
       ↓
┌──────────────┐
│ 3. Parse     │ → Regex + spaCy identifies MPs, statements, bills
└──────────────┘
       ↓
┌──────────────┐
│ 4. Store     │ → Update SQLite database (versioned in Git)
└──────────────┘
       ↓
┌──────────────┐
│ 5. Generate  │ → Hugo/Jinja2 creates static HTML pages
└──────────────┘
       ↓
┌──────────────┐
│ 6. Deploy    │ → Git push → Cloudflare Pages auto-deploys
└──────────────┘
```

## 3. Technology Stack

### 3.1 Core Technologies

| Component | Technology | Cost | Rationale |
|-----------|-----------|------|-----------|
| **Language** | Python 3.11+ | Free | Single language, great libraries, easy to maintain |
| **PDF Processing** | pdfplumber | Free | Pure Python, good accuracy, no external dependencies |
| **NLP** | spaCy | Free | Fast, accurate NER, works offline |
| **Database** | SQLite | Free | Serverless, versioned in Git, perfect for read-heavy workloads |
| **Static Site** | Jinja2 | Free | Python-native, simple templates, easy to maintain |
| **CSS Framework** | Tailwind CSS (CDN) | Free | No build step, utility-first, mobile-first responsive |
| **Search** | Fuse.js | Free | Client-side fuzzy search, no backend needed |
| **Hosting** | Cloudflare Pages | Free | Unlimited bandwidth, global CDN, auto HTTPS |
| **CI/CD** | GitHub Actions | Free | 2,000 minutes/month free for public repos |
| **Version Control** | Git/GitHub | Free | Code + data + backup in one place |

### 3.2 Optional Technologies (Phase 2)

| Component | Technology | Cost | When to Add |
|-----------|-----------|------|-------------|
| **Cartoons** | Imagen API | £10-20/month | If budget allows and user demand exists |
| **Analytics** | Cloudflare Analytics | Free | Built-in with Cloudflare Pages |
| **Monitoring** | GitHub Actions logs | Free | Sufficient for MVP |

## 4. Data Model

### 4.1 SQLite Schema

```sql
-- Parliamentary terms/sessions (e.g., 13th Parliament 2022-2027)
CREATE TABLE parliamentary_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_number INTEGER NOT NULL,  -- e.g., 13
    start_date DATE NOT NULL,
    end_date DATE,  -- NULL if current term
    is_current BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MPs can serve across multiple terms
CREATE TABLE mps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    constituency TEXT NOT NULL,
    party TEXT,
    photo_url TEXT,
    first_elected_year INTEGER,  -- When they first became MP
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track which MPs served in which parliamentary terms
CREATE TABLE mp_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mp_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,
    constituency TEXT NOT NULL,  -- Can change between terms
    party TEXT,  -- Can change between terms
    elected_date DATE,
    left_date DATE,  -- NULL if still serving
    is_current BOOLEAN DEFAULT 0,
    FOREIGN KEY (mp_id) REFERENCES mps(id),
    FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id),
    UNIQUE(mp_id, term_id)
);

-- Hansard sessions (daily parliamentary sittings)
CREATE TABLE hansard_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL,
    date DATE NOT NULL,
    title TEXT,
    pdf_url TEXT NOT NULL,
    pdf_path TEXT,  -- Local path to downloaded PDF
    processed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id)
);

-- Statements made by MPs in sessions
CREATE TABLE statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mp_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    page_number INTEGER,
    bill_reference TEXT,  -- Store for future use (e.g., "Bill No. 123")
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mp_id) REFERENCES mps(id),
    FOREIGN KEY (session_id) REFERENCES hansard_sessions(id)
);

-- Indexes for performance
CREATE INDEX idx_statements_mp ON statements(mp_id);
CREATE INDEX idx_statements_session ON statements(session_id);
CREATE INDEX idx_statements_bill ON statements(bill_reference);
CREATE INDEX idx_hansard_date ON hansard_sessions(date);
CREATE INDEX idx_hansard_term ON hansard_sessions(term_id);
CREATE INDEX idx_mp_terms_current ON mp_terms(is_current);
CREATE INDEX idx_mp_terms_mp ON mp_terms(mp_id);

-- View for current MPs (13th Parliament)
CREATE VIEW current_mps AS
SELECT 
    m.id,
    m.name,
    mt.constituency,
    mt.party,
    m.photo_url,
    m.first_elected_year,
    mt.elected_date as current_term_start,
    pt.term_number
FROM mps m
JOIN mp_terms mt ON m.id = mt.mp_id
JOIN parliamentary_terms pt ON mt.term_id = pt.id
WHERE mt.is_current = 1;

-- View for MP performance in current term
CREATE VIEW mp_current_term_performance AS
SELECT 
    m.id,
    m.name,
    mt.constituency,
    mt.party,
    pt.term_number,
    COUNT(DISTINCT s.id) as statement_count,
    COUNT(DISTINCT s.session_id) as sessions_attended,
    COUNT(DISTINCT s.bill_reference) as bills_mentioned,
    MAX(hs.date) as last_active_date,
    MIN(hs.date) as first_active_date
FROM mps m
JOIN mp_terms mt ON m.id = mt.mp_id
JOIN parliamentary_terms pt ON mt.term_id = pt.id
LEFT JOIN hansard_sessions hs ON hs.term_id = pt.id
LEFT JOIN statements s ON s.mp_id = m.id AND s.session_id = hs.id
WHERE mt.is_current = 1
GROUP BY m.id;

-- View for MP historical performance (all terms)
CREATE VIEW mp_historical_performance AS
SELECT 
    m.id,
    m.name,
    pt.term_number,
    mt.constituency,
    mt.party,
    mt.elected_date,
    mt.left_date,
    COUNT(DISTINCT s.id) as statement_count,
    COUNT(DISTINCT s.session_id) as sessions_attended,
    COUNT(DISTINCT s.bill_reference) as bills_mentioned
FROM mps m
JOIN mp_terms mt ON m.id = mt.mp_id
JOIN parliamentary_terms pt ON mt.term_id = pt.id
LEFT JOIN hansard_sessions hs ON hs.term_id = pt.id
LEFT JOIN statements s ON s.mp_id = m.id AND s.session_id = hs.id
GROUP BY m.id, pt.term_number;
```

### 4.2 Search Index Format (JSON)

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
      "constituency": "Nairobi West",
      "party": "ODM",
      "slug": "john-doe",
      "current_term": {
        "statement_count": 45,
        "sessions_attended": 12,
        "term_number": 13
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
          "term_number": 13,
          "constituency": "Nairobi West",
          "party": "ODM",
          "statement_count": 45,
          "years": "2022-present"
        }
      ],
      "keywords": ["john", "doe", "nairobi", "west", "odm"]
    }
  ]
}
```

## 5. Core Components

### 5.0 Parliamentary Term Management

**Key Concepts**:
- **Parliamentary Term**: A 5-year period (e.g., 13th Parliament: 2022-2027)
- **MP Terms**: MPs can serve multiple parliamentary terms
- **Term-Specific Data**: Constituency and party can change between terms
- **Current vs Historical**: Track both current performance and historical record

**Example Scenarios**:

1. **MP serves multiple terms**:
   - John Doe: 12th Parliament (2017-2022) in Nairobi West, ODM
   - John Doe: 13th Parliament (2022-2027) in Nairobi West, ODM
   - Show performance for each term separately

2. **MP changes constituency**:
   - Jane Smith: 12th Parliament in Mombasa North, Jubilee
   - Jane Smith: 13th Parliament in Kilifi South, UDA
   - Track constituency change

3. **MP changes party**:
   - Bob Johnson: 13th Parliament started in ODM
   - Bob Johnson: Switched to UDA mid-term
   - Track party affiliation at time of statement

**Data Initialization**:
```python
# Initialize 13th Parliament (current)
def initialize_parliamentary_terms():
    conn = sqlite3.connect('data/hansard.db')
    cursor = conn.cursor()
    
    # Create 13th Parliament (current)
    cursor.execute("""
        INSERT INTO parliamentary_terms (term_number, start_date, end_date, is_current)
        VALUES (13, '2022-09-08', '2027-09-07', 1)
    """)
    
    # Optionally add historical terms
    cursor.execute("""
        INSERT INTO parliamentary_terms (term_number, start_date, end_date, is_current)
        VALUES (12, '2017-08-31', '2022-09-07', 0)
    """)
    
    conn.commit()
    conn.close()

# Link MP to current term
def add_mp_to_current_term(mp_id, constituency, party, elected_date):
    conn = sqlite3.connect('data/hansard.db')
    cursor = conn.cursor()
    
    # Get current term
    cursor.execute("SELECT id FROM parliamentary_terms WHERE is_current = 1")
    term_id = cursor.fetchone()[0]
    
    # Link MP to term
    cursor.execute("""
        INSERT INTO mp_terms (mp_id, term_id, constituency, party, elected_date, is_current)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (mp_id, term_id, constituency, party, elected_date))
    
    conn.commit()
    conn.close()
```

### 5.1 Data Processing Pipeline (Python)

```python
# main.py - Single script that does everything
import pdfplumber
import spacy
import sqlite3
import re
from pathlib import Path
from datetime import datetime

# Load spaCy model for NER
nlp = spacy.load("en_core_web_sm")

def scrape_hansard_pdfs():
    """Scrape parliament.go.ke for new Hansard PDFs"""
    # Simple requests + BeautifulSoup scraping
    # Download PDFs to data/pdfs/
    pass

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pdfplumber"""
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text

def identify_speakers(text):
    """Use regex + spaCy to identify MPs and their statements"""
    # Pattern: "Hon. [Name]:" or "[Name] (MP):"
    pattern = r"Hon\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:"
    
    statements = []
    for match in re.finditer(pattern, text):
        mp_name = match.group(1)
        # Extract statement text (until next speaker)
        # Use spaCy for entity recognition and validation
        statements.append({
            'mp_name': mp_name,
            'text': extract_statement_text(text, match.end()),
            'bill_reference': extract_bill_reference(text)
        })
    
    return statements

def extract_bill_reference(text):
    """Extract bill references using regex"""
    # Pattern: "Bill No. 123" or "Bill 2024/123"
    pattern = r"Bill\s+(?:No\.\s*)?(\d+(?:/\d+)?)"
    match = re.search(pattern, text)
    return match.group(0) if match else None

def update_database(statements, session_id):
    """Update SQLite database with new statements"""
    conn = sqlite3.connect('data/hansard.db')
    cursor = conn.cursor()
    
    for stmt in statements:
        # Find or create MP
        mp_id = get_or_create_mp(cursor, stmt['mp_name'])
        
        # Insert statement
        cursor.execute("""
            INSERT INTO statements (mp_id, session_id, text, bill_reference)
            VALUES (?, ?, ?, ?)
        """, (mp_id, session_id, stmt['text'], stmt['bill_reference']))
    
    conn.commit()
    conn.close()

def generate_search_index():
    """Generate JSON search index for client-side search"""
    conn = sqlite3.connect('data/hansard.db')
    cursor = conn.cursor()
    
    # Get current parliamentary term
    cursor.execute("""
        SELECT term_number, start_date, end_date
        FROM parliamentary_terms
        WHERE is_current = 1
    """)
    current_term = cursor.fetchone()
    
    # Get current MPs with their performance
    cursor.execute("""
        SELECT id, name, constituency, party, 
               statement_count, sessions_attended, term_number
        FROM mp_current_term_performance
    """)
    
    mps = []
    for row in cursor.fetchall():
        mp_id = row[0]
        
        # Get historical performance for this MP
        cursor.execute("""
            SELECT term_number, constituency, party, 
                   statement_count, elected_date, left_date
            FROM mp_historical_performance
            WHERE id = ?
            ORDER BY term_number
        """, (mp_id,))
        
        historical = []
        for hist_row in cursor.fetchall():
            years = f"{hist_row[4][:4]}-"
            years += "present" if hist_row[5] is None else hist_row[5][:4]
            
            historical.append({
                'term_number': hist_row[0],
                'constituency': hist_row[1],
                'party': hist_row[2],
                'statement_count': hist_row[3],
                'years': years
            })
        
        mps.append({
            'id': row[0],
            'name': row[1],
            'constituency': row[2],
            'party': row[3],
            'slug': row[1].lower().replace(' ', '-'),
            'current_term': {
                'statement_count': row[4],
                'sessions_attended': row[5],
                'term_number': row[6]
            },
            'historical_terms': historical,
            'keywords': [
                row[1].lower(),  # name
                row[2].lower(),  # constituency
                row[3].lower() if row[3] else ''  # party
            ]
        })
    
    # Write to JSON
    import json
    with open('output/data/mp-search-index.json', 'w') as f:
        json.dump({
            'current_term': {
                'term_number': current_term[0],
                'start_date': current_term[1],
                'end_date': current_term[2]
            },
            'mps': mps
        }, f)
    
    conn.close()

def generate_static_site():
    """Generate static HTML pages using Jinja2 or Hugo"""
    # Option 1: Jinja2 (Python-native)
    from jinja2 import Environment, FileSystemLoader
    
    env = Environment(loader=FileSystemLoader('templates'))
    
    # Generate MP pages
    conn = sqlite3.connect('data/hansard.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM mp_performance")
    for mp in cursor.fetchall():
        template = env.get_template('mp_profile.html')
        html = template.render(mp=mp)
        
        # Write to output/mp/{slug}.html
        slug = mp[1].lower().replace(' ', '-')
        Path(f'output/mp/{slug}.html').write_text(html)
    
    conn.close()

def main():
    """Main processing pipeline - runs weekly"""
    print("Starting weekly Hansard processing...")
    
    # 1. Scrape new PDFs
    new_pdfs = scrape_hansard_pdfs()
    
    # 2. Process each PDF
    for pdf_path in new_pdfs:
        text = extract_text_from_pdf(pdf_path)
        statements = identify_speakers(text)
        session_id = create_session_record(pdf_path)
        update_database(statements, session_id)
    
    # 3. Generate search index
    generate_search_index()
    
    # 4. Generate static site
    generate_static_site()
    
    print("Processing complete!")

if __name__ == "__main__":
    main()
```

### 5.2 GitHub Actions Workflow

```yaml
# .github/workflows/weekly-update.yml
name: Weekly Hansard Update

on:
  schedule:
    # Every Sunday at 2 AM EAT (23:00 UTC Saturday)
    - cron: '0 23 * * 6'
  workflow_dispatch:  # Allow manual trigger

jobs:
  process-hansard:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Full history for Git versioning
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          python -m spacy download en_core_web_sm
      
      - name: Run processing pipeline
        run: python scripts/main.py
      
      - name: Commit and push changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data/ output/
          git diff --quiet && git diff --staged --quiet || \
            (git commit -m "Weekly update: $(date +'%Y-%m-%d')" && git push)
      
      - name: Notify on failure
        if: failure()
        run: echo "Processing failed! Check logs."
```

### 5.3 Static Site Templates (Jinja2)

**Design System:**
- **CSS Framework**: Tailwind CSS via CDN (no build step required)
- **Color Palette**: Kenyan flag-inspired colors
  - Warm white (#FAF9F6) as base background
  - Kenya green (subtle shades 50-900) for primary accents
  - Kenya red (subtle shades 50-900) for secondary accents
  - Black borders (2px) for clear visual definition
- **Typography**: Helvetica Neue as primary font with system font fallback
  - Font stack: "Helvetica Neue" → San Francisco → Segoe UI → Roboto → Arial
  - Zero font downloads (uses pre-installed fonts)
  - Excellent readability across all devices
- **Responsive Design**: Mobile-first with Tailwind breakpoints
- **Accessibility**: WCAG AA compliant, semantic HTML, ARIA labels

**Template Structure:**
- `templates/layouts/base.html` - Base layout with navigation, header, footer
- `templates/pages/` - Page-specific templates
- `templates/components/` - Reusable UI components
- `static/css/main.css` - Minimal custom CSS (smooth scroll, print, focus)
- `static/js/main.js` - Mobile navigation toggle

**Development & Deployment:**
- Flask development server (app.py) with hot-reload for local testing
- Docker environment (Dockerfile, docker-compose.yml) for containerized development
- Static site generator (scripts/generate_static_site.py) for GitHub Pages
- GitHub Actions workflow for auto-deployment on push

```html
<!-- templates/mp_profile.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ mp.name }} - Hansard Tales</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <header>
        <h1>Hansard Tales</h1>
        <nav>
            <a href="/">Home</a>
            <a href="/search">Search MPs</a>
            <a href="/terms">Parliamentary Terms</a>
        </nav>
    </header>
    
    <main>
        <div class="mp-profile">
            <img src="{{ mp.photo_url }}" alt="{{ mp.name }}">
            <h2>{{ mp.name }}</h2>
            <p><strong>Constituency:</strong> {{ mp.constituency }}</p>
            <p><strong>Party:</strong> {{ mp.party }}</p>
            <p><strong>Current Term:</strong> {{ mp.current_term_number }}th Parliament ({{ mp.current_term_years }})</p>
            
            <!-- Current Term Performance -->
            <h3>Current Term Performance ({{ mp.current_term_number }}th Parliament)</h3>
            <div class="stats">
                <div class="stat">
                    <span class="number">{{ mp.current_statement_count }}</span>
                    <span class="label">Statements</span>
                </div>
                <div class="stat">
                    <span class="number">{{ mp.current_sessions_attended }}</span>
                    <span class="label">Sessions Attended</span>
                </div>
                <div class="stat">
                    <span class="number">{{ mp.current_bills_mentioned }}</span>
                    <span class="label">Bills Mentioned</span>
                </div>
            </div>
            
            <!-- Historical Performance (if MP served in previous terms) -->
            {% if mp.historical_terms|length > 1 %}
            <h3>Historical Performance</h3>
            <div class="historical-terms">
                {% for term in mp.historical_terms %}
                <div class="term-card">
                    <h4>{{ term.term_number }}th Parliament ({{ term.years }})</h4>
                    <p><strong>Constituency:</strong> {{ term.constituency }}</p>
                    <p><strong>Party:</strong> {{ term.party }}</p>
                    <div class="term-stats">
                        <span>{{ term.statement_count }} statements</span>
                        <span>{{ term.sessions_attended }} sessions</span>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <!-- Recent Statements (Current Term) -->
            <h3>Recent Statements ({{ mp.current_term_number }}th Parliament)</h3>
            <div class="term-filter">
                <label>Filter by term:</label>
                <select id="term-filter">
                    <option value="current" selected>Current ({{ mp.current_term_number }}th)</option>
                    {% for term in mp.historical_terms %}
                    <option value="{{ term.term_number }}">{{ term.term_number }}th Parliament</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="statements" id="statements-list">
                {% for statement in mp.statements %}
                <div class="statement" data-term="{{ statement.term_number }}">
                    <p class="date">{{ statement.date }} ({{ statement.term_number }}th Parliament)</p>
                    <p class="text">{{ statement.text }}</p>
                    <a href="{{ statement.hansard_url }}" target="_blank">
                        View in Hansard (Page {{ statement.page_number }})
                    </a>
                </div>
                {% endfor %}
            </div>
        </div>
    </main>
    
    <footer>
        <p>Data sourced from Parliament of Kenya Hansard records</p>
        <p>Current: {{ current_term.term_number }}th Parliament ({{ current_term.start_date }} - {{ current_term.end_date }})</p>
    </footer>
    
    <script>
        // Simple term filtering
        document.getElementById('term-filter').addEventListener('change', function(e) {
            const selectedTerm = e.target.value;
            const statements = document.querySelectorAll('.statement');
            
            statements.forEach(stmt => {
                if (selectedTerm === 'current') {
                    stmt.style.display = stmt.dataset.term === '{{ mp.current_term_number }}' ? 'block' : 'none';
                } else {
                    stmt.style.display = stmt.dataset.term === selectedTerm ? 'block' : 'none';
                }
            });
        });
    </script>
</body>
</html>
```

### 5.4 Client-Side Search (JavaScript)

```javascript
// js/search.js
// Load Fuse.js for fuzzy search
import Fuse from 'https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.mjs';

// Load MP data
let mpsData = [];
fetch('/data/mp-search-index.json')
    .then(response => response.json())
    .then(data => {
        mpsData = data.mps;
        initializeSearch();
    });

function initializeSearch() {
    const fuse = new Fuse(mpsData, {
        keys: ['name', 'constituency', 'party'],
        threshold: 0.3,  // Fuzzy matching tolerance
        includeScore: true
    });
    
    const searchInput = document.getElementById('mp-search');
    const resultsDiv = document.getElementById('search-results');
    
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value;
        
        if (query.length < 2) {
            resultsDiv.innerHTML = '';
            return;
        }
        
        const results = fuse.search(query);
        displayResults(results);
    });
}

function displayResults(results) {
    const resultsDiv = document.getElementById('search-results');
    
    if (results.length === 0) {
        resultsDiv.innerHTML = '<p>No MPs found</p>';
        return;
    }
    
    const html = results.slice(0, 10).map(result => {
        const mp = result.item;
        return `
            <div class="search-result">
                <a href="/mp/${mp.slug}.html">
                    <h3>${mp.name}</h3>
                    <p>${mp.constituency} • ${mp.party}</p>
                    <p class="stats">${mp.statement_count} statements</p>
                </a>
            </div>
        `;
    }).join('');
    
    resultsDiv.innerHTML = html;
}
```

## 6. Deployment Strategy

### 6.1 Cloudflare Pages Setup

```bash
# One-time setup (via Cloudflare dashboard)
1. Connect GitHub repository
2. Set build command: (none - pre-built by GitHub Actions)
3. Set output directory: output/
4. Enable automatic deployments on push to main
```

### 6.2 Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/hansard-tales.git
cd hansard-tales

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run processing locally
python scripts/main.py

# Serve static site locally
cd output
python -m http.server 8000
# Visit http://localhost:8000
```

## 7. Cost Breakdown

### 7.1 Monthly Costs (MVP)

| Service | Cost | Notes |
|---------|------|-------|
| GitHub Actions | £0 | 2,000 minutes/month free (public repo) |
| Cloudflare Pages | £0 | 500 builds/month, unlimited bandwidth |
| SQLite | £0 | No database server needed |
| Domain (.ke) | £1/month | ~£12/year |
| **Optional**: Imagen API | £10-20/month | Only if generating cartoons |
| **Total** | **£1-21/month** | **90-95% cost reduction** |

### 7.2 Cost Comparison

| Architecture | Monthly Cost | Complexity | Maintainability |
|--------------|--------------|------------|-----------------|
| **Original (GCP + Multi-language)** | £150-286 | Very High | Difficult |
| **Simplified (Python + Static)** | £1-21 | Low | Easy |
| **Savings** | **£129-265** | **90% reduction** | **Much better** |

## 8. Performance Characteristics

### 8.1 Processing Performance

- **PDF Processing**: ~30 seconds per 100-page PDF (pdfplumber)
- **Weekly Batch**: ~20 minutes for 35 PDFs (acceptable for weekly job)
- **Static Site Generation**: ~10 seconds for 349 pages (Hugo) or ~30 seconds (Jinja2)
- **Total Weekly Runtime**: ~25 minutes (well within GitHub Actions free tier)

### 8.2 Website Performance

- **Page Load Time**: <1 second (static HTML, CDN)
- **Search Response**: <100ms (client-side, no network)
- **Mobile Performance**: Excellent (simple HTML/CSS, minimal JS)
- **Bandwidth**: Unlimited (Cloudflare Pages free tier)

## 9. Scalability Considerations

### 9.1 Current Limits

- **MPs**: 349 (fixed, no scaling needed)
- **Hansard PDFs**: ~35 per week = ~1,800 per year (manageable)
- **SQLite**: Can handle millions of rows (sufficient for decades)
- **Static Site**: Can serve millions of users (CDN)

### 9.2 When to Scale

**Don't scale until you have:**
- 10,000+ daily active users
- Real-time update requirements
- User-generated content
- Complex interactive features

**Then consider:**
- Moving to PostgreSQL (if SQLite becomes limiting)
- Adding caching layer (Redis)
- Implementing API for third-party integrations
- But keep the simple architecture as long as possible!

## 10. Security Considerations

### 10.1 Attack Surface

- **Static Site**: Minimal attack surface (no backend, no database queries)
- **No User Input**: No forms, no authentication = no injection attacks
- **HTTPS**: Automatic via Cloudflare
- **DDoS Protection**: Built-in with Cloudflare

### 10.2 Data Security

- **Source Attribution**: Every statement links to official Hansard PDF
- **Version Control**: Git history provides audit trail
- **Backup**: Git = automatic backup (GitHub + local clones)
- **No PII**: Only public MP data, no user data collected

## 11. Monitoring & Maintenance

### 11.1 Monitoring

- **GitHub Actions**: Email notifications on workflow failures
- **Cloudflare Analytics**: Built-in traffic analytics (free)
- **Git History**: Track all data changes
- **Manual Spot Checks**: Weekly review of new data

### 11.2 Maintenance Tasks

**Weekly** (automated):
- Process new Hansard PDFs
- Update MP profiles
- Regenerate static site

**Monthly** (manual):
- Review processing accuracy
- Check for new MPs or changes
- Update MP photos if needed

**Quarterly** (manual):
- Review and optimize processing scripts
- Update dependencies
- Backup SQLite database (Git already does this)

## 12. Migration Path (Future)

### 12.1 When to Consider Migration

**Signals that you've outgrown this architecture:**
- Need real-time updates (not weekly batches)
- User accounts and authentication required
- Complex interactive features needed
- API for third-party integrations demanded
- Processing takes >1 hour per week

### 12.2 Migration Options

**Option 1: Add Backend API (Keep Static Frontend)**
- Deploy FastAPI on Cloud Run (free tier)
- Keep SQLite or migrate to PostgreSQL
- Static site calls API for dynamic data
- Cost: +£0-10/month

**Option 2: Move to Full Cloud (If Necessary)**
- Migrate to GCP/AWS only when truly needed
- Keep Python-only stack
- Use managed services (Cloud Run, Cloud SQL)
- Cost: +£50-100/month

**Option 3: Hybrid (Recommended)**
- Keep static site for MP profiles
- Add API for new features only
- Gradual migration as needed
- Cost: +£10-30/month

## 13. Development Roadmap

### 13.1 Phase 1: MVP (Weeks 1-4)

**Week 1: Setup**
- Set up GitHub repository
- Create SQLite schema
- Build PDF scraper
- Test with 5 sample PDFs

**Week 2: Processing**
- Implement text extraction
- Build MP identification
- Create database update logic
- Test with 20 PDFs

**Week 3: Site Generation**
- Create HTML templates
- Generate MP profile pages
- Build search functionality
- Test locally

**Week 4: Deployment**
- Set up GitHub Actions
- Configure Cloudflare Pages
- Process all historical data
- Launch!

### 13.2 Phase 2: Enhancements (Months 2-3)

- Add bill-centric pages
- Implement simple stance detection
- Add party comparison pages
- Improve search with filters

### 13.3 Phase 3: Growth (Months 4-6)

- Add cartoons (if budget allows)
- Implement basic infographics
- Add social sharing features
- Consider API for partners

## 14. Success Metrics

### 14.1 Technical Metrics

- ✅ Processing completes in <30 minutes
- ✅ Zero failed deployments
- ✅ Page load time <2 seconds
- ✅ Search response time <100ms
- ✅ Monthly costs <£30

### 14.2 Business Metrics

- 🎯 1,000+ unique visitors/month
- 🎯 2+ pages per session
- 🎯 60%+ mobile traffic
- 🎯 5+ media mentions
- 🎯 Organic growth through word-of-mouth

## 15. Conclusion

This simplified architecture achieves:

✅ **90% cost reduction** (£1-21/month vs £150-286/month)  
✅ **90% complexity reduction** (single language, no cloud services)  
✅ **Solo maintainable** (one person can handle everything)  
✅ **Fast to ship** (4 weeks to MVP vs 12 weeks)  
✅ **No vendor lock-in** (runs anywhere)  
✅ **Easy to debug** (single script, single log)  
✅ **Scalable when needed** (can migrate later)  

**The key insight**: You're processing 35 PDFs per week, not 35,000. Optimize for simplicity, not scale.
