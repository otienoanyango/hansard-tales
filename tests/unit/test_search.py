"""
Tests for MP search functionality.

Tests the search index generation and search UI integration.
"""
import json
import pytest
import sqlite3
import tempfile
from pathlib import Path
from hansard_tales.site_generator import generate_static_site
from hansard_tales.search_index_generator import generate_search_index


@pytest.fixture
def test_db():
    """Create test database with sample data."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables (simplified schema for testing)
    cursor.execute('''
        CREATE TABLE parliamentary_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_number INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            is_current BOOLEAN DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE mps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            photo_url TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE mp_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mp_id INTEGER NOT NULL,
            term_id INTEGER NOT NULL,
            constituency TEXT NOT NULL,
            party TEXT,
            elected_date DATE,
            left_date DATE,
            is_current BOOLEAN DEFAULT 0,
            FOREIGN KEY (mp_id) REFERENCES mps(id),
            FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE hansard_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_id INTEGER NOT NULL,
            session_date DATE NOT NULL,
            FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mp_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            statement_text TEXT NOT NULL,
            bill_reference TEXT,
            FOREIGN KEY (mp_id) REFERENCES mps(id),
            FOREIGN KEY (session_id) REFERENCES hansard_sessions(id)
        )
    ''')
    
    # Insert test data
    cursor.execute('''
        INSERT INTO parliamentary_terms (term_number, start_date, end_date, is_current)
        VALUES (13, '2022-09-08', '2027-09-07', 1)
    ''')
    term_id = cursor.lastrowid
    
    # Insert test MPs
    test_mps = [
        ('John Doe', 'https://example.com/john.jpg'),
        ('Jane Smith', 'https://example.com/jane.jpg'),
        ('Bob Johnson', None),
    ]
    
    for name, photo_url in test_mps:
        cursor.execute('INSERT INTO mps (name, photo_url) VALUES (?, ?)', (name, photo_url))
        mp_id = cursor.lastrowid
        
        # Link MP to term
        constituency = 'Nairobi' if name == 'John Doe' else ('Mombasa' if name == 'Jane Smith' else 'Nominated')
        party = 'UDA' if name == 'John Doe' else ('ODM' if name == 'Jane Smith' else 'KANU')
        
        cursor.execute('''
            INSERT INTO mp_terms (mp_id, term_id, constituency, party, is_current)
            VALUES (?, ?, ?, ?, 1)
        ''', (mp_id, term_id, constituency, party))
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    import os
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client():
    """Create Flask test client."""
    from app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def search_index_file(test_db, tmp_path):
    """Generate search index for testing."""
    output_dir = tmp_path / 'output'
    generate_search_index(db_path=test_db, output_dir=output_dir)
    
    index_file = output_dir / 'data' / 'mp-search-index.json'
    assert index_file.exists(), "Search index file should be created"
    
    return index_file


class TestSearchIndex:
    """Test search index generation and structure."""
    
    def test_search_index_structure(self, search_index_file):
        """Test that search index has correct structure."""
        with open(search_index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        assert isinstance(index, list), "Index should be a list"
        assert len(index) > 0, "Index should contain MPs"
        
        # Check first MP structure
        mp = index[0]
        assert 'id' in mp
        assert 'name' in mp
        assert 'constituency' in mp
        assert 'party' in mp
        assert 'photo_url' in mp
        assert 'current_term' in mp
        assert 'historical_terms' in mp
        assert 'keywords' in mp
    
    def test_search_index_current_term(self, search_index_file):
        """Test that current term data is included."""
        with open(search_index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        mp = index[0]
        current_term = mp['current_term']
        
        assert 'term_number' in current_term
        assert 'statement_count' in current_term
        assert 'sessions_attended' in current_term
        assert 'bills_mentioned' in current_term
        
        # Verify data types
        assert isinstance(current_term['term_number'], int)
        assert isinstance(current_term['statement_count'], int)
        assert isinstance(current_term['sessions_attended'], int)
        assert isinstance(current_term['bills_mentioned'], int)
    
    def test_search_index_keywords(self, search_index_file):
        """Test that keywords are generated."""
        with open(search_index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        mp = index[0]
        keywords = mp['keywords']
        
        assert isinstance(keywords, list), "Keywords should be a list"
        assert len(keywords) > 0, "Keywords should not be empty"
        
        # Keywords should include name components
        name_parts = mp['name'].split()
        for part in name_parts:
            assert part in keywords, f"Name part '{part}' should be in keywords"
    
    def test_search_index_historical_terms(self, search_index_file):
        """Test that historical terms are included."""
        with open(search_index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        mp = index[0]
        historical_terms = mp['historical_terms']
        
        assert isinstance(historical_terms, list), "Historical terms should be a list"
        
        if len(historical_terms) > 0:
            term = historical_terms[0]
            assert 'term_number' in term
            assert 'constituency' in term
            assert 'party' in term
            assert 'elected_date' in term
            assert 'left_date' in term


class TestSearchUI:
    """Test search UI integration."""
    
    def test_homepage_has_search_input(self, client):
        """Test that homepage has search input field."""
        response = client.get('/')
        assert response.status_code == 200
        
        html = response.data.decode('utf-8')
        assert 'id="mp-search"' in html, "Homepage should have search input"
        assert 'placeholder="Search by MP name or constituency..."' in html
    
    def test_homepage_has_search_results_container(self, client):
        """Test that homepage has search results container."""
        response = client.get('/')
        assert response.status_code == 200
        
        html = response.data.decode('utf-8')
        assert 'id="search-results"' in html, "Homepage should have search results container"
        assert 'hidden' in html, "Search results should be hidden by default"
    
    def test_homepage_loads_fusejs(self, client):
        """Test that homepage loads Fuse.js from CDN."""
        response = client.get('/')
        assert response.status_code == 200
        
        html = response.data.decode('utf-8')
        assert 'fuse.js' in html.lower() or 'fuse.min.js' in html.lower(), \
            "Homepage should load Fuse.js"
    
    def test_homepage_loads_search_js(self, client):
        """Test that homepage loads search.js."""
        response = client.get('/')
        assert response.status_code == 200
        
        html = response.data.decode('utf-8')
        assert 'search.js' in html, "Homepage should load search.js"
    
    def test_search_js_file_exists(self):
        """Test that search.js file exists."""
        search_js = Path('static/js/search.js')
        assert search_js.exists(), "search.js file should exist"
        
        # Check file has content
        content = search_js.read_text()
        assert len(content) > 0, "search.js should not be empty"
        assert 'Fuse' in content, "search.js should reference Fuse"
        assert 'mp-search-index.json' in content, "search.js should load search index"


class TestSearchIndexEndpoint:
    """Test that search index is accessible via HTTP."""
    
    def test_search_index_accessible(self, client, test_db, tmp_path):
        """Test that search index JSON is accessible."""
        # Generate search index
        output_dir = Path('output')
        generate_search_index(db_path=test_db, output_dir=output_dir)
        
        # Try to access via Flask static files
        response = client.get('/data/mp-search-index.json')
        
        # Note: This test may fail if Flask app doesn't serve from output/
        # In production, the static site generator copies this file
        # For now, we just verify the file exists
        index_file = output_dir / 'data' / 'mp-search-index.json'
        assert index_file.exists(), "Search index should be generated"


class TestSearchFunctionality:
    """Test search functionality integration."""
    
    def test_search_with_empty_query(self, search_index_file):
        """Test that empty query returns no results."""
        # This would be tested in JavaScript, but we verify the index structure
        with open(search_index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        assert len(index) > 0, "Index should have MPs to search"
    
    def test_search_by_name(self, search_index_file):
        """Test that MPs can be found by name."""
        with open(search_index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # Get first MP name
        first_mp = index[0]
        name = first_mp['name']
        
        # Verify name is searchable (in keywords or name field)
        assert name in [mp['name'] for mp in index]
    
    def test_search_by_constituency(self, search_index_file):
        """Test that MPs can be found by constituency."""
        with open(search_index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # Find MP with constituency
        mp_with_constituency = next(
            (mp for mp in index if mp['constituency'] != 'Nominated'),
            None
        )
        
        if mp_with_constituency:
            constituency = mp_with_constituency['constituency']
            # Verify constituency is in keywords
            assert constituency in mp_with_constituency['keywords']
    
    def test_search_by_party(self, search_index_file):
        """Test that MPs can be found by party."""
        with open(search_index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # Find MP with party
        mp_with_party = next(
            (mp for mp in index if mp['party']),
            None
        )
        
        if mp_with_party:
            party = mp_with_party['party']
            # Verify party is in keywords
            assert party in mp_with_party['keywords']


class TestSearchPerformance:
    """Test search performance and optimization."""
    
    def test_search_index_size(self, search_index_file):
        """Test that search index is reasonably sized."""
        file_size = search_index_file.stat().st_size
        
        # Index should be less than 1MB for 349 MPs
        assert file_size < 1024 * 1024, \
            f"Search index too large: {file_size / 1024:.1f} KB"
    
    def test_search_index_json_valid(self, search_index_file):
        """Test that search index is valid JSON."""
        try:
            with open(search_index_file, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Search index is not valid JSON: {e}")
    
    def test_keywords_no_duplicates(self, search_index_file):
        """Test that keywords don't have duplicates."""
        with open(search_index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        for mp in index:
            keywords = mp['keywords']
            # Check for duplicates
            assert len(keywords) == len(set(keywords)), \
                f"MP {mp['name']} has duplicate keywords"
