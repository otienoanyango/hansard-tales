"""
Tests for static site generator.
"""
import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
from hansard_tales.site_generator import (
    generate_static_site,
    get_logo_filename,
    create_url_for
)


@pytest.fixture
def test_db():
    """Create test database with sample data."""
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
            elected_date DATE,
            left_date DATE,
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
            text TEXT NOT NULL,
            page_number INTEGER,
            bill_reference TEXT
        )
    ''')
    
    # Insert test data
    cursor.execute(
        "INSERT INTO parliamentary_terms (term_number, start_date, end_date, is_current) VALUES (13, '2022-09-08', '2027-09-07', 1)"
    )
    term_id = cursor.lastrowid
    
    # Insert test MPs
    test_mps = [
        ('Alice Wanjiru', 'Nairobi West', 'UDA', 'http://example.com/alice.jpg'),
        ('Bob Kamau', 'Mombasa North', 'ODM', None),
        ('Carol Achieng', 'Kisumu Central', 'ODM', 'http://example.com/carol.jpg'),
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
            "INSERT INTO mp_terms (mp_id, term_id, constituency, party, elected_date, is_current) VALUES (?, ?, ?, ?, ?, 1)",
            (mp_id, term_id, constituency, party, '2022-09-08')
        )
    
    # Insert test session and statements
    cursor.execute(
        "INSERT INTO hansard_sessions (term_id, date, pdf_url) VALUES (?, ?, ?)",
        (term_id, '2024-01-15', 'http://example.com/test.pdf')
    )
    session_id = cursor.lastrowid
    
    # Add statements
    cursor.execute(
        "INSERT INTO statements (mp_id, session_id, text, page_number) VALUES (?, ?, ?, ?)",
        (mp_ids[0], session_id, 'Statement 1', 5)
    )
    cursor.execute(
        "INSERT INTO statements (mp_id, session_id, text, page_number, bill_reference) VALUES (?, ?, ?, ?, ?)",
        (mp_ids[1], session_id, 'Statement 2', 10, 'Bill No. 123')
    )
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    import os
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


class TestURLFor:
    """Test url_for function."""
    
    def test_static_endpoint_no_base_path(self):
        """Test static file URL generation without base path."""
        url_for = create_url_for('')
        url = url_for('static', filename='css/main.css')
        assert url == '/static/css/main.css'
    
    def test_static_endpoint_with_base_path(self):
        """Test static file URL generation with base path."""
        url_for = create_url_for('/hansard-tales')
        url = url_for('static', filename='css/main.css')
        assert url == '/hansard-tales/static/css/main.css'
    
    def test_index_endpoint_no_base_path(self):
        """Test index URL generation without base path."""
        url_for = create_url_for('')
        url = url_for('index')
        assert url == '/index.html'
    
    def test_index_endpoint_with_base_path(self):
        """Test index URL generation with base path."""
        url_for = create_url_for('/hansard-tales')
        url = url_for('index')
        assert url == '/hansard-tales/index.html'
    
    def test_mps_list_endpoint_with_base_path(self):
        """Test MPs listing URL generation with base path."""
        url_for = create_url_for('/hansard-tales')
        url = url_for('mps_list')
        assert url == '/hansard-tales/mps/index.html'
    
    def test_mp_profile_endpoint_with_base_path(self):
        """Test MP profile URL generation with base path."""
        url_for = create_url_for('/hansard-tales')
        url = url_for('mp_profile', mp_id=123)
        assert url == '/hansard-tales/mp/123/index.html'
    
    def test_parties_endpoint_with_base_path(self):
        """Test parties listing URL generation with base path."""
        url_for = create_url_for('/hansard-tales')
        url = url_for('parties')
        assert url == '/hansard-tales/parties/index.html'
    
    def test_party_detail_endpoint_with_base_path(self):
        """Test party detail URL generation with base path."""
        url_for = create_url_for('/hansard-tales')
        url = url_for('party_detail', party_slug='uda')
        assert url == '/hansard-tales/party/uda/index.html'
    
    def test_base_path_trailing_slash_removed(self):
        """Test that trailing slash is removed from base path."""
        url_for = create_url_for('/hansard-tales/')
        url = url_for('index')
        assert url == '/hansard-tales/index.html'


class TestLogoFilename:
    """Test get_logo_filename function."""
    
    def test_simple_party_name(self):
        """Test simple party name."""
        filename = get_logo_filename('UDA')
        assert filename == 'UDA.svg'
    
    def test_party_with_spaces(self):
        """Test party name with spaces."""
        filename = get_logo_filename('DAP K')
        assert filename == 'DAP-K.svg'
    
    def test_ford_k_special_case(self):
        """Test FORD-K special case."""
        filename = get_logo_filename('FORD - K')
        assert filename == 'FORD-K.svg'
        
        filename = get_logo_filename('FORD-K')
        assert filename == 'FORD-K.svg'
    
    def test_independent_special_case(self):
        """Test IND special case."""
        filename = get_logo_filename('IND')
        assert filename == 'IND.svg'
        
        filename = get_logo_filename('IND.')
        assert filename == 'IND.svg'


class TestSiteGeneration:
    """Test static site generation."""
    
    def test_generate_site_creates_output_dir(self, test_db, temp_output_dir):
        """Test that site generation creates output directory."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        assert temp_output_dir.exists()
    
    def test_generate_site_creates_index(self, test_db, temp_output_dir):
        """Test that site generation creates index.html."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        assert (temp_output_dir / 'index.html').exists()
    
    def test_generate_site_creates_mps_listing(self, test_db, temp_output_dir):
        """Test that site generation creates MPs listing."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        assert (temp_output_dir / 'mps' / 'index.html').exists()
    
    def test_generate_site_creates_mp_profiles(self, test_db, temp_output_dir):
        """Test that site generation creates MP profile pages."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        # Should have 3 MP profiles
        mp_dirs = list((temp_output_dir / 'mp').glob('*'))
        assert len(mp_dirs) == 3
    
    def test_generate_site_creates_parties_listing(self, test_db, temp_output_dir):
        """Test that site generation creates parties listing."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        assert (temp_output_dir / 'parties' / 'index.html').exists()
    
    def test_generate_site_creates_party_pages(self, test_db, temp_output_dir):
        """Test that site generation creates party detail pages."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        # Should have 2 party pages (UDA, ODM)
        party_dirs = list((temp_output_dir / 'party').glob('*'))
        assert len(party_dirs) == 2
    
    def test_generate_site_creates_placeholder_pages(self, test_db, temp_output_dir):
        """Test that site generation creates placeholder pages."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        assert (temp_output_dir / 'about.html').exists()
        assert (temp_output_dir / 'disclaimer.html').exists()
        assert (temp_output_dir / 'privacy.html').exists()
    
    def test_generate_site_copies_static_files(self, test_db, temp_output_dir):
        """Test that site generation copies static files."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        assert (temp_output_dir / 'static').exists()
    
    def test_generate_site_creates_nojekyll(self, test_db, temp_output_dir):
        """Test that site generation creates .nojekyll file."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        assert (temp_output_dir / '.nojekyll').exists()
    
    def test_generate_site_with_nonexistent_db(self, temp_output_dir):
        """Test that site generation fails with nonexistent database."""
        with pytest.raises(SystemExit):
            generate_static_site(db_path='/nonexistent/db.db', output_dir=temp_output_dir, base_path='')
    
    def test_generate_site_with_base_path(self, test_db, temp_output_dir):
        """Test that site generation uses base path in URLs."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='/hansard-tales')
        
        # Check that index.html contains base path in URLs
        index_content = (temp_output_dir / 'index.html').read_text()
        assert '/hansard-tales/static/' in index_content or '/hansard-tales/' in index_content


class TestMPProfileContent:
    """Test MP profile page content."""
    
    def test_mp_profile_contains_name(self, test_db, temp_output_dir):
        """Test that MP profile contains MP name."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        
        # Find first MP profile
        mp_dirs = list((temp_output_dir / 'mp').glob('*'))
        profile_path = mp_dirs[0] / 'index.html'
        content = profile_path.read_text()
        
        # Should contain one of the MP names
        assert any(name in content for name in ['Alice Wanjiru', 'Bob Kamau', 'Carol Achieng'])
    
    def test_mp_profile_contains_constituency(self, test_db, temp_output_dir):
        """Test that MP profile contains constituency."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        
        mp_dirs = list((temp_output_dir / 'mp').glob('*'))
        profile_path = mp_dirs[0] / 'index.html'
        content = profile_path.read_text()
        
        # Should contain one of the constituencies
        assert any(const in content for const in ['Nairobi West', 'Mombasa North', 'Kisumu Central'])


class TestPartiesContent:
    """Test parties page content."""
    
    def test_parties_listing_contains_party_names(self, test_db, temp_output_dir):
        """Test that parties listing contains party names."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        
        content = (temp_output_dir / 'parties' / 'index.html').read_text()
        assert 'UDA' in content
        assert 'ODM' in content
    
    def test_party_page_contains_party_name(self, test_db, temp_output_dir):
        """Test that party page contains party name."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        
        # Find first party page
        party_dirs = list((temp_output_dir / 'party').glob('*'))
        party_path = party_dirs[0] / 'index.html'
        content = party_path.read_text()
        
        # Should contain one of the party names
        assert 'UDA' in content or 'ODM' in content


class TestFileStructure:
    """Test generated file structure."""
    
    def test_output_has_correct_structure(self, test_db, temp_output_dir):
        """Test that output directory has correct structure."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        
        # Check main directories exist
        assert (temp_output_dir / 'static').exists()
        assert (temp_output_dir / 'mps').exists()
        assert (temp_output_dir / 'mp').exists()
        assert (temp_output_dir / 'parties').exists()
        assert (temp_output_dir / 'party').exists()
    
    def test_mp_profiles_have_index_html(self, test_db, temp_output_dir):
        """Test that MP profile directories have index.html."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        
        mp_dirs = list((temp_output_dir / 'mp').glob('*'))
        for mp_dir in mp_dirs:
            assert (mp_dir / 'index.html').exists()
    
    def test_party_pages_have_index_html(self, test_db, temp_output_dir):
        """Test that party directories have index.html."""
        generate_static_site(db_path=test_db, output_dir=temp_output_dir, base_path='')
        
        party_dirs = list((temp_output_dir / 'party').glob('*'))
        for party_dir in party_dirs:
            assert (party_dir / 'index.html').exists()
