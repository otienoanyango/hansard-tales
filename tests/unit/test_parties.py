"""
Tests for party pages templates and routes.
"""
import pytest
import sqlite3
from pathlib import Path
from app import app
import tempfile
import os


@pytest.fixture
def test_db():
    """Create test database with sample party data."""
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
    cursor.execute("INSERT INTO parliamentary_terms (term_number, start_date, is_current) VALUES (13, '2022-09-08', 1)")
    term_id = cursor.lastrowid
    
    # Insert test MPs with different parties
    cursor.execute("INSERT INTO mps (name, constituency, party) VALUES ('John Doe', 'Nairobi West', 'UDA')")
    mp1_id = cursor.lastrowid
    cursor.execute("INSERT INTO mp_terms (mp_id, term_id, constituency, party, is_current) VALUES (?, ?, 'Nairobi West', 'UDA', 1)", (mp1_id, term_id))
    
    cursor.execute("INSERT INTO mps (name, constituency, party) VALUES ('Jane Smith', 'Mombasa North', 'ODM')")
    mp2_id = cursor.lastrowid
    cursor.execute("INSERT INTO mp_terms (mp_id, term_id, constituency, party, is_current) VALUES (?, ?, 'Mombasa North', 'ODM', 1)", (mp2_id, term_id))
    
    cursor.execute("INSERT INTO mps (name, constituency, party) VALUES ('Bob Johnson', 'Kisumu Central', 'ODM')")
    mp3_id = cursor.lastrowid
    cursor.execute("INSERT INTO mp_terms (mp_id, term_id, constituency, party, is_current) VALUES (?, ?, 'Kisumu Central', 'ODM', 1)", (mp3_id, term_id))
    
    # Insert test session and statements
    cursor.execute("INSERT INTO hansard_sessions (term_id, date, pdf_url) VALUES (?, '2024-01-15', 'http://example.com/test.pdf')", (term_id,))
    session_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO statements (mp_id, session_id, text) VALUES (?, ?, 'Test statement 1')", (mp1_id, session_id))
    cursor.execute("INSERT INTO statements (mp_id, session_id, text) VALUES (?, ?, 'Test statement 2')", (mp2_id, session_id))
    cursor.execute("INSERT INTO statements (mp_id, session_id, text) VALUES (?, ?, 'Test statement 3')", (mp2_id, session_id))
    
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


class TestPartiesListingTemplate:
    """Test parties listing template structure."""
    
    def test_template_file_exists(self):
        """Test that parties.html template exists."""
        template_path = Path('templates/pages/parties.html')
        assert template_path.exists()
    
    def test_template_extends_base(self):
        """Test that template extends base layout."""
        template_path = Path('templates/pages/parties.html')
        content = template_path.read_text()
        assert '{% extends "layouts/base.html" %}' in content
    
    def test_template_has_title_block(self):
        """Test that template has title block."""
        template_path = Path('templates/pages/parties.html')
        content = template_path.read_text()
        assert '{% block title %}' in content
    
    def test_template_has_content_block(self):
        """Test that template has content block."""
        template_path = Path('templates/pages/parties.html')
        content = template_path.read_text()
        assert '{% block content %}' in content


class TestPartiesListingRoute:
    """Test parties listing route."""
    
    def test_parties_route_exists(self, client, test_db):
        """Test that parties route exists."""
        response = client.get('/parties/')
        assert response.status_code == 200
    
    def test_parties_returns_html(self, client, test_db):
        """Test that parties route returns HTML."""
        response = client.get('/parties/')
        assert response.content_type == 'text/html; charset=utf-8'
    
    def test_parties_has_content(self, client, test_db):
        """Test that parties page has content."""
        response = client.get('/parties/')
        assert len(response.data) > 0


class TestPartiesListingContent:
    """Test parties listing page content."""
    
    def test_shows_page_title(self, client, test_db):
        """Test that page shows title."""
        response = client.get('/parties/')
        data = response.data.decode('utf-8')
        assert 'Political Parties' in data or 'Parties' in data
    
    def test_shows_party_cards(self, client, test_db):
        """Test that page shows party cards."""
        response = client.get('/parties/')
        data = response.data.decode('utf-8')
        # Should show both UDA and ODM parties
        assert 'UDA' in data
        assert 'ODM' in data
    
    def test_shows_mp_counts(self, client, test_db):
        """Test that page shows MP counts for parties."""
        response = client.get('/parties/')
        data = response.data.decode('utf-8')
        assert 'Total MPs' in data or 'MP' in data


class TestPartyDetailTemplate:
    """Test individual party template structure."""
    
    def test_template_file_exists(self):
        """Test that party.html template exists."""
        template_path = Path('templates/pages/party.html')
        assert template_path.exists()
    
    def test_template_extends_base(self):
        """Test that template extends base layout."""
        template_path = Path('templates/pages/party.html')
        content = template_path.read_text()
        assert '{% extends "layouts/base.html" %}' in content
    
    def test_template_has_title_block(self):
        """Test that template has title block."""
        template_path = Path('templates/pages/party.html')
        content = template_path.read_text()
        assert '{% block title %}' in content
    
    def test_template_has_content_block(self):
        """Test that template has content block."""
        template_path = Path('templates/pages/party.html')
        content = template_path.read_text()
        assert '{% block content %}' in content


class TestPartyDetailRoute:
    """Test individual party route."""
    
    def test_party_route_exists(self, client, test_db):
        """Test that party detail route exists."""
        response = client.get('/party/odm/')
        assert response.status_code == 200
    
    def test_party_not_found(self, client, test_db):
        """Test that non-existent party returns 404."""
        response = client.get('/party/nonexistent/')
        assert response.status_code == 404
    
    def test_party_returns_html(self, client, test_db):
        """Test that party route returns HTML."""
        response = client.get('/party/odm/')
        assert response.content_type == 'text/html; charset=utf-8'


class TestPartyDetailContent:
    """Test individual party page content."""
    
    def test_shows_party_name(self, client, test_db):
        """Test that page shows party name."""
        response = client.get('/party/odm/')
        data = response.data.decode('utf-8')
        assert 'ODM' in data
    
    def test_shows_party_stats(self, client, test_db):
        """Test that page shows party statistics."""
        response = client.get('/party/odm/')
        data = response.data.decode('utf-8')
        assert 'Total MPs' in data or 'MPs' in data
        assert 'Statements' in data or 'statements' in data.lower()
    
    def test_shows_mp_list(self, client, test_db):
        """Test that page shows list of MPs."""
        response = client.get('/party/odm/')
        data = response.data.decode('utf-8')
        # Should show ODM MPs
        assert 'Jane Smith' in data
        assert 'Bob Johnson' in data
    
    def test_has_back_link(self, client, test_db):
        """Test that page has back link to parties listing."""
        response = client.get('/party/odm/')
        data = response.data.decode('utf-8')
        assert '/parties/' in data
        assert 'Back' in data or 'back' in data.lower()


class TestPartiesResponsive:
    """Test parties pages responsive design."""
    
    def test_listing_uses_responsive_classes(self):
        """Test that listing template uses responsive classes."""
        template_path = Path('templates/pages/parties.html')
        content = template_path.read_text()
        assert 'md:' in content
        assert 'lg:' in content or 'md:grid-cols' in content
    
    def test_detail_uses_responsive_classes(self):
        """Test that detail template uses responsive classes."""
        template_path = Path('templates/pages/party.html')
        content = template_path.read_text()
        assert 'md:' in content
    
    def test_uses_grid_layout(self):
        """Test that templates use grid layout."""
        template_path = Path('templates/pages/parties.html')
        content = template_path.read_text()
        assert 'grid' in content


class TestPartiesAccessibility:
    """Test parties pages accessibility."""
    
    def test_listing_uses_semantic_html(self):
        """Test that listing uses semantic HTML."""
        template_path = Path('templates/pages/parties.html')
        content = template_path.read_text()
        assert '<section' in content
        assert '<h1' in content
        assert '<h2' in content
    
    def test_detail_uses_semantic_html(self):
        """Test that detail uses semantic HTML."""
        template_path = Path('templates/pages/party.html')
        content = template_path.read_text()
        assert '<section' in content
        assert '<h1' in content
    
    def test_links_are_descriptive(self):
        """Test that links have descriptive text."""
        template_path = Path('templates/pages/parties.html')
        content = template_path.read_text()
        assert 'click here' not in content.lower()


class TestPartiesStyling:
    """Test parties pages styling."""
    
    def test_listing_uses_tailwind(self):
        """Test that listing uses Tailwind CSS."""
        template_path = Path('templates/pages/parties.html')
        content = template_path.read_text()
        assert 'bg-' in content
        assert 'text-' in content
        assert 'border-' in content
    
    def test_detail_uses_tailwind(self):
        """Test that detail uses Tailwind CSS."""
        template_path = Path('templates/pages/party.html')
        content = template_path.read_text()
        assert 'bg-' in content
        assert 'text-' in content
    
    def test_uses_kenya_colors(self):
        """Test that templates use Kenya colors."""
        template_path = Path('templates/pages/parties.html')
        content = template_path.read_text()
        assert 'kenya-red' in content or 'kenya-green' in content
    
    def test_uses_borders(self):
        """Test that templates use borders."""
        template_path = Path('templates/pages/parties.html')
        content = template_path.read_text()
        assert 'border-' in content


class TestPartyDetailSorting:
    """Test party detail page sorting functionality."""
    
    def test_has_sort_dropdown(self):
        """Test that detail page has sort dropdown."""
        template_path = Path('templates/pages/party.html')
        content = template_path.read_text()
        assert 'sort-select' in content
        assert '<select' in content
    
    def test_has_sort_options(self):
        """Test that sort dropdown has options."""
        template_path = Path('templates/pages/party.html')
        content = template_path.read_text()
        assert 'name' in content.lower()
        assert 'constituency' in content.lower()
        assert 'statements' in content.lower()
    
    def test_has_sorting_javascript(self):
        """Test that page has JavaScript for sorting."""
        template_path = Path('templates/pages/party.html')
        content = template_path.read_text()
        assert '{% block extra_js %}' in content
        assert 'addEventListener' in content


class TestPartiesLinks:
    """Test parties pages links."""
    
    def test_listing_links_to_party_pages(self):
        """Test that listing links to individual party pages."""
        template_path = Path('templates/pages/parties.html')
        content = template_path.read_text()
        assert '/party/' in content
    
    def test_detail_links_to_mp_profiles(self):
        """Test that detail page links to MP profiles."""
        template_path = Path('templates/pages/party.html')
        content = template_path.read_text()
        assert '/mp/' in content
    
    def test_detail_has_back_link(self):
        """Test that detail page has back link."""
        template_path = Path('templates/pages/party.html')
        content = template_path.read_text()
        assert '/parties/' in content
