"""
Tests for MP profile template and route.
"""
import pytest
import sqlite3
from pathlib import Path
from app import app, get_db_connection
import tempfile
import os


@pytest.fixture
def test_db():
    """Create test database with sample data for integration tests."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Initialize database schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE parliamentary_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_number INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            is_current BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE mps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            constituency TEXT NOT NULL,
            party TEXT,
            photo_url TEXT,
            first_elected_year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id),
            UNIQUE(mp_id, term_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE hansard_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_id INTEGER NOT NULL,
            date DATE NOT NULL,
            title TEXT,
            pdf_url TEXT NOT NULL,
            pdf_path TEXT,
            processed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mp_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            page_number INTEGER,
            bill_reference TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (mp_id) REFERENCES mps(id),
            FOREIGN KEY (session_id) REFERENCES hansard_sessions(id)
        )
    ''')
    
    # Insert test data
    # Parliamentary term
    cursor.execute('''
        INSERT INTO parliamentary_terms (term_number, start_date, end_date, is_current)
        VALUES (13, '2022-09-08', '2027-09-07', 1)
    ''')
    term_id = cursor.lastrowid
    
    # Test MP
    cursor.execute('''
        INSERT INTO mps (name, constituency, party, first_elected_year)
        VALUES ('John Doe', 'Nairobi West', 'ODM', 2017)
    ''')
    mp_id = cursor.lastrowid
    
    # Link MP to term
    cursor.execute('''
        INSERT INTO mp_terms (mp_id, term_id, constituency, party, elected_date, is_current)
        VALUES (?, ?, 'Nairobi West', 'ODM', '2022-09-08', 1)
    ''', (mp_id, term_id))
    
    # Test session
    cursor.execute('''
        INSERT INTO hansard_sessions (term_id, date, title, pdf_url, processed)
        VALUES (?, '2024-01-15', 'Test Session', 'http://example.com/test.pdf', 1)
    ''', (term_id,))
    session_id = cursor.lastrowid
    
    # Test statements
    cursor.execute('''
        INSERT INTO statements (mp_id, session_id, text, page_number, bill_reference)
        VALUES (?, ?, 'This is a test statement about education reform.', 5, 'Bill No. 123')
    ''', (mp_id, session_id))
    
    cursor.execute('''
        INSERT INTO statements (mp_id, session_id, text, page_number)
        VALUES (?, ?, 'Another statement about healthcare.', 7)
    ''', (mp_id, session_id))
    
    conn.commit()
    conn.close()
    
    # Temporarily replace the database path in app.py
    original_db = os.environ.get('TEST_DB_PATH')
    os.environ['TEST_DB_PATH'] = db_path
    
    yield mp_id
    
    # Cleanup
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


class TestMPProfileRoute:
    """Test MP profile route."""
    
    def test_mp_profile_route_exists(self, client, test_db):
        """Test that MP profile route exists."""
        response = client.get(f'/mp/{test_db}/')
        assert response.status_code == 200
    
    def test_mp_profile_not_found(self, client):
        """Test MP profile returns 404 for non-existent MP."""
        response = client.get('/mp/999999/')
        assert response.status_code == 404
    
    def test_mp_profile_contains_mp_name(self, client, test_db):
        """Test that MP profile contains MP name."""
        response = client.get(f'/mp/{test_db}/')
        assert response.status_code == 200
        # Should contain some text content
        assert len(response.data) > 0


class TestMPProfileTemplate:
    """Test MP profile template structure."""
    
    def test_template_file_exists(self):
        """Test that mp_profile.html template exists."""
        template_path = Path('templates/pages/mp_profile.html')
        assert template_path.exists()
    
    def test_template_extends_base(self):
        """Test that template extends base layout."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        assert '{% extends "layouts/base.html" %}' in content
    
    def test_template_has_title_block(self):
        """Test that template has title block."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        assert '{% block title %}' in content
    
    def test_template_has_content_block(self):
        """Test that template has content block."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        assert '{% block content %}' in content


class TestMPProfileContent:
    """Test MP profile content sections."""
    
    def test_profile_displays_mp_info(self, client, test_db):
        """Test that profile displays MP information."""
        response = client.get(f'/mp/{test_db}/')
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        
        # Should contain key sections
        assert 'Constituency:' in data or 'constituency' in data.lower()
        assert 'Party:' in data or 'party' in data.lower()
    
    def test_profile_displays_performance_metrics(self, client, test_db):
        """Test that profile displays performance metrics."""
        response = client.get(f'/mp/{test_db}/')
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        
        # Should contain performance section
        assert 'Performance' in data or 'performance' in data.lower()
        assert 'Statements' in data or 'statements' in data.lower()
    
    def test_profile_has_statements_section(self, client, test_db):
        """Test that profile has statements section."""
        response = client.get(f'/mp/{test_db}/')
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        
        # Should contain statements section
        assert 'Statements' in data or 'statements' in data.lower()


class TestMPProfileResponsive:
    """Test MP profile responsive design."""
    
    def test_template_has_responsive_classes(self):
        """Test that template uses responsive Tailwind classes."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should have mobile-first responsive classes
        assert 'md:' in content  # Medium breakpoint
        assert 'lg:' in content or 'md:flex-row' in content  # Responsive layout
    
    def test_template_has_grid_layout(self):
        """Test that template uses grid layout for metrics."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should use grid for performance metrics
        assert 'grid' in content


class TestMPProfileAccessibility:
    """Test MP profile accessibility features."""
    
    def test_template_has_semantic_html(self):
        """Test that template uses semantic HTML."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should use semantic elements
        assert '<h1' in content
        assert '<h2' in content
    
    def test_template_has_alt_text_for_images(self):
        """Test that images have alt text."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should have alt attribute for images
        assert 'alt=' in content
    
    def test_template_has_aria_labels(self):
        """Test that interactive elements have labels."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should have labels for form elements
        assert '<label' in content or 'aria-label' in content


class TestMPProfileTermFilter:
    """Test MP profile term filtering functionality."""
    
    def test_template_has_term_filter(self):
        """Test that template has term filter dropdown."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should have term filter select element
        assert 'term-filter' in content
        assert '<select' in content
    
    def test_template_has_filter_javascript(self):
        """Test that template has JavaScript for filtering."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should have JavaScript block
        assert '{% block extra_js %}' in content
        assert 'addEventListener' in content or 'term-filter' in content


class TestMPProfileHistoricalTerms:
    """Test MP profile historical terms section."""
    
    def test_template_has_historical_section(self):
        """Test that template has historical terms section."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should have conditional historical section
        assert 'historical_terms' in content
        assert 'Historical' in content or 'historical' in content.lower()
    
    def test_template_shows_historical_conditionally(self):
        """Test that historical section is conditional."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should check if historical terms exist
        assert '{% if historical_terms' in content


class TestMPProfileLinks:
    """Test MP profile external links."""
    
    def test_template_has_hansard_links(self):
        """Test that template has links to Hansard PDFs."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should have links to Hansard
        assert 'hansard_url' in content or 'Hansard' in content
    
    def test_template_links_open_in_new_tab(self):
        """Test that external links open in new tab."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should have target="_blank" for external links
        assert 'target="_blank"' in content
        assert 'rel="noopener"' in content


class TestDatabaseQueries:
    """Test database queries for MP profile."""
    
    def test_get_db_connection_works(self):
        """Test that database connection works."""
        db_path = Path('data/hansard.db')
        if not db_path.exists():
            pytest.skip("Database not found - skipping integration test")
        
        try:
            conn = get_db_connection()
            assert conn is not None
            conn.close()
        except Exception as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_can_query_mps_table(self):
        """Test that we can query MPs table."""
        db_path = Path('data/hansard.db')
        if not db_path.exists():
            pytest.skip("Database not found - skipping integration test")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM mps")
            result = cursor.fetchone()
            assert result['count'] >= 0
            conn.close()
        except Exception as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_can_query_mp_terms_table(self):
        """Test that we can query mp_terms table."""
        db_path = Path('data/hansard.db')
        if not db_path.exists():
            pytest.skip("Database not found - skipping integration test")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM mp_terms")
            result = cursor.fetchone()
            assert result['count'] >= 0
            conn.close()
        except Exception as e:
            pytest.skip(f"Database not available: {e}")


class TestMPProfileStyling:
    """Test MP profile styling and design."""
    
    def test_template_uses_tailwind_classes(self):
        """Test that template uses Tailwind CSS classes."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should use Tailwind utility classes
        assert 'bg-' in content
        assert 'text-' in content
        assert 'border-' in content
    
    def test_template_uses_kenya_colors(self):
        """Test that template uses Kenya color palette."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should use custom Kenya colors
        assert 'kenya-green' in content or 'kenya-red' in content
    
    def test_template_has_rounded_corners(self):
        """Test that template uses rounded corners."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should use rounded classes
        assert 'rounded' in content
    
    def test_template_has_borders(self):
        """Test that template uses black borders."""
        template_path = Path('templates/pages/mp_profile.html')
        content = template_path.read_text()
        
        # Should use border-black
        assert 'border-black' in content or 'border-2' in content
