"""
Tests for MPs listing page template and route.
"""
import pytest
import sqlite3
from pathlib import Path
from app import app
import tempfile
import os


@pytest.fixture
def test_db():
    """Create test database with sample MP data."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
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
            constituency TEXT NOT NULL,
            party TEXT,
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
            is_current BOOLEAN DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE hansard_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_id INTEGER NOT NULL,
            date DATE NOT NULL,
            pdf_url TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mp_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            text TEXT NOT NULL
        )
    ''')
    
    # Insert test data
    cursor.execute(
        "INSERT INTO parliamentary_terms (term_number, start_date, is_current) VALUES (13, '2022-09-08', 1)"
    )
    term_id = cursor.lastrowid
    
    # Insert test MPs with different parties
    test_mps = [
        ('Alice Wanjiru', 'Nairobi West', 'UDA', 'http://example.com/alice.jpg'),
        ('Bob Kamau', 'Mombasa North', 'ODM', None),
        ('Carol Achieng', 'Kisumu Central', 'ODM', 'http://example.com/carol.jpg'),
        ('David Mwangi', 'Nakuru East', 'UDA', None),
        ('Eve Njeri', 'Eldoret South', 'UDA', 'http://example.com/eve.jpg'),
    ]
    
    mp_ids = []
    for name, constituency, party, photo_url in test_mps:
        cursor.execute(
            "INSERT INTO mps (name, constituency, party, photo_url) VALUES (?, ?, ?, ?)",
            (name, constituency, party, photo_url)
        )
        mp_id = cursor.lastrowid
        mp_ids.append(mp_id)
        cursor.execute(
            "INSERT INTO mp_terms (mp_id, term_id, constituency, party, is_current) VALUES (?, ?, ?, ?, 1)",
            (mp_id, term_id, constituency, party)
        )
    
    # Insert test session and statements
    cursor.execute(
        "INSERT INTO hansard_sessions (term_id, date, pdf_url) VALUES (?, ?, ?)",
        (term_id, '2024-01-15', 'http://example.com/test.pdf')
    )
    session_id = cursor.lastrowid
    
    # Add varying statement counts
    cursor.execute(
        "INSERT INTO statements (mp_id, session_id, text) VALUES (?, ?, ?)",
        (mp_ids[0], session_id, 'Statement 1')
    )
    cursor.execute(
        "INSERT INTO statements (mp_id, session_id, text) VALUES (?, ?, ?)",
        (mp_ids[0], session_id, 'Statement 2')
    )
    cursor.execute(
        "INSERT INTO statements (mp_id, session_id, text) VALUES (?, ?, ?)",
        (mp_ids[1], session_id, 'Statement 3')
    )
    cursor.execute(
        "INSERT INTO statements (mp_id, session_id, text) VALUES (?, ?, ?)",
        (mp_ids[2], session_id, 'Statement 4')
    )
    cursor.execute(
        "INSERT INTO statements (mp_id, session_id, text) VALUES (?, ?, ?)",
        (mp_ids[2], session_id, 'Statement 5')
    )
    cursor.execute(
        "INSERT INTO statements (mp_id, session_id, text) VALUES (?, ?, ?)",
        (mp_ids[2], session_id, 'Statement 6')
    )
    
    conn.commit()
    conn.close()
    
    original_db = os.environ.get('TEST_DB_PATH')
    os.environ['TEST_DB_PATH'] = db_path
    
    yield
    
    if original_db:
        os.environ['TEST_DB_PATH'] = original_db
    else:
        os.environ.pop('TEST_DB_PATH', None)
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestMPsListingTemplate:
    """Test MPs listing template structure."""
    
    def test_template_file_exists(self):
        """Test that mps_list.html template exists."""
        template_path = Path('templates/pages/mps_list.html')
        assert template_path.exists()
    
    def test_template_extends_base(self):
        """Test that template extends base layout."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert '{% extends "layouts/base.html" %}' in content
    
    def test_template_has_title_block(self):
        """Test that template has title block."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert '{% block title %}' in content
    
    def test_template_has_content_block(self):
        """Test that template has content block."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert '{% block content %}' in content


class TestMPsListingRoute:
    """Test MPs listing route."""
    
    def test_mps_route_exists(self, client, test_db):
        """Test that MPs listing route exists."""
        response = client.get('/mps/')
        assert response.status_code == 200
    
    def test_mps_returns_html(self, client, test_db):
        """Test that MPs route returns HTML."""
        response = client.get('/mps/')
        assert response.content_type == 'text/html; charset=utf-8'
    
    def test_mps_has_content(self, client, test_db):
        """Test that MPs page has content."""
        response = client.get('/mps/')
        assert len(response.data) > 0


class TestMPsListingContent:
    """Test MPs listing page content."""
    
    def test_shows_page_title(self, client, test_db):
        """Test that page shows title."""
        response = client.get('/mps/')
        data = response.data.decode('utf-8')
        assert 'Members of Parliament' in data or 'All MPs' in data
    
    def test_shows_mp_cards(self, client, test_db):
        """Test that page shows MP cards."""
        response = client.get('/mps/')
        data = response.data.decode('utf-8')
        # Should show test MPs
        assert 'Alice Wanjiru' in data
        assert 'Bob Kamau' in data
        assert 'Carol Achieng' in data
    
    def test_shows_mp_constituencies(self, client, test_db):
        """Test that page shows MP constituencies."""
        response = client.get('/mps/')
        data = response.data.decode('utf-8')
        assert 'Nairobi West' in data
        assert 'Mombasa North' in data
    
    def test_shows_mp_parties(self, client, test_db):
        """Test that page shows MP parties."""
        response = client.get('/mps/')
        data = response.data.decode('utf-8')
        assert 'UDA' in data
        assert 'ODM' in data
    
    def test_shows_total_count(self, client, test_db):
        """Test that page shows total MP count."""
        response = client.get('/mps/')
        data = response.data.decode('utf-8')
        assert '5' in data  # 5 test MPs


class TestMPsListingFilters:
    """Test MPs listing filters."""
    
    def test_has_party_filter(self):
        """Test that page has party filter dropdown."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert 'party-filter' in content
        assert '<select' in content
    
    def test_has_sort_options(self):
        """Test that page has sort dropdown."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert 'sort-select' in content
        assert 'name' in content.lower()
        assert 'constituency' in content.lower()
        assert 'statements' in content.lower()
    
    def test_party_filter_shows_all_option(self, client, test_db):
        """Test that party filter has 'All Parties' option."""
        response = client.get('/mps/')
        data = response.data.decode('utf-8')
        assert 'All Parties' in data
    
    def test_party_filter_shows_parties(self, client, test_db):
        """Test that party filter shows available parties."""
        response = client.get('/mps/')
        data = response.data.decode('utf-8')
        # Should show parties with counts
        assert 'UDA' in data
        assert 'ODM' in data


class TestMPsListingJavaScript:
    """Test MPs listing JavaScript functionality."""
    
    def test_has_filter_javascript(self):
        """Test that page has filtering JavaScript."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert '{% block extra_js %}' in content
        assert 'addEventListener' in content
        assert 'party-filter' in content
    
    def test_has_sort_javascript(self):
        """Test that page has sorting JavaScript."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert 'sort-select' in content
        assert 'sort' in content.lower()
    
    def test_has_data_attributes(self):
        """Test that MP cards have data attributes for filtering/sorting."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert 'data-party' in content
        assert 'data-name' in content
        assert 'data-constituency' in content
        assert 'data-statements' in content


class TestMPsListingResponsive:
    """Test MPs listing responsive design."""
    
    def test_uses_responsive_classes(self):
        """Test that template uses responsive classes."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert 'md:' in content
        assert 'lg:' in content or 'md:grid-cols' in content
    
    def test_uses_grid_layout(self):
        """Test that template uses grid layout."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert 'grid' in content


class TestMPsListingAccessibility:
    """Test MPs listing accessibility."""
    
    def test_uses_semantic_html(self):
        """Test that template uses semantic HTML."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert '<section' in content
        assert '<h1' in content
        assert '<h2' in content or '<h3' in content
    
    def test_has_labels_for_inputs(self):
        """Test that form controls have labels."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert '<label' in content
        assert 'for=' in content
    
    def test_links_are_descriptive(self):
        """Test that links have descriptive text."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert 'click here' not in content.lower()


class TestMPsListingStyling:
    """Test MPs listing styling."""
    
    def test_uses_tailwind(self):
        """Test that template uses Tailwind CSS."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert 'bg-' in content
        assert 'text-' in content
        assert 'border-' in content
    
    def test_uses_kenya_colors(self):
        """Test that template uses Kenya colors."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert 'kenya-red' in content or 'kenya-green' in content
    
    def test_uses_borders(self):
        """Test that template uses borders."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert 'border-' in content


class TestMPsListingLinks:
    """Test MPs listing links."""
    
    def test_links_to_mp_profiles(self):
        """Test that MP cards link to individual profiles."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert '/mp/' in content
    
    def test_mp_cards_are_clickable(self, client, test_db):
        """Test that MP cards are links."""
        response = client.get('/mps/')
        data = response.data.decode('utf-8')
        assert 'href="/mp/' in data


class TestMPsListingEmptyState:
    """Test MPs listing empty state."""
    
    def test_has_empty_state(self):
        """Test that template has empty state."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert 'No MPs Found' in content
    
    def test_has_no_results_message(self):
        """Test that template has no results message for filtering."""
        template_path = Path('templates/pages/mps_list.html')
        content = template_path.read_text()
        assert 'no-results' in content
