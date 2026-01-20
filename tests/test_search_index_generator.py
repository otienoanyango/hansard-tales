"""
Tests for search index generator module.
"""
import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from hansard_tales.search_index_generator import (
    generate_keywords,
    generate_search_index,
    get_db_connection
)


@pytest.fixture
def test_db():
    """Create a temporary test database with sample data."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE parliamentary_terms (
            id INTEGER PRIMARY KEY,
            term_number INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            is_current BOOLEAN DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE mps (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            constituency TEXT NOT NULL,
            party TEXT,
            photo_url TEXT,
            first_elected_year INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE mp_terms (
            id INTEGER PRIMARY KEY,
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
    """)
    
    cursor.execute("""
        CREATE TABLE hansard_sessions (
            id INTEGER PRIMARY KEY,
            term_id INTEGER NOT NULL,
            date DATE NOT NULL,
            title TEXT,
            pdf_url TEXT NOT NULL,
            FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE statements (
            id INTEGER PRIMARY KEY,
            mp_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            page_number INTEGER,
            bill_reference TEXT,
            FOREIGN KEY (mp_id) REFERENCES mps(id),
            FOREIGN KEY (session_id) REFERENCES hansard_sessions(id)
        )
    """)
    
    # Insert test data
    # Parliamentary terms
    cursor.execute("""
        INSERT INTO parliamentary_terms (id, term_number, start_date, end_date, is_current)
        VALUES (1, 12, '2017-08-31', '2022-09-07', 0)
    """)
    cursor.execute("""
        INSERT INTO parliamentary_terms (id, term_number, start_date, end_date, is_current)
        VALUES (2, 13, '2022-09-08', '2027-09-07', 1)
    """)
    
    # MPs
    cursor.execute("""
        INSERT INTO mps (id, name, constituency, party, photo_url, first_elected_year)
        VALUES (1, 'JOHN DOE', 'NAIROBI CENTRAL', 'UDA', 'http://example.com/photo1.jpg', 2017)
    """)
    cursor.execute("""
        INSERT INTO mps (id, name, constituency, party, photo_url, first_elected_year)
        VALUES (2, 'JANE SMITH', 'MOMBASA NORTH', 'ODM', 'http://example.com/photo2.jpg', 2022)
    """)
    cursor.execute("""
        INSERT INTO mps (id, name, constituency, party, photo_url, first_elected_year)
        VALUES (3, 'PETER JONES', 'KISUMU EAST', 'ANC', 'http://example.com/photo3.jpg', 2022)
    """)
    
    # MP terms
    # John Doe - served in both terms
    cursor.execute("""
        INSERT INTO mp_terms (mp_id, term_id, constituency, party, elected_date, is_current)
        VALUES (1, 1, 'NAIROBI CENTRAL', 'JP', '2017-08-31', 0)
    """)
    cursor.execute("""
        INSERT INTO mp_terms (mp_id, term_id, constituency, party, elected_date, is_current)
        VALUES (1, 2, 'NAIROBI CENTRAL', 'UDA', '2022-09-08', 1)
    """)
    
    # Jane Smith - only current term
    cursor.execute("""
        INSERT INTO mp_terms (mp_id, term_id, constituency, party, elected_date, is_current)
        VALUES (2, 2, 'MOMBASA NORTH', 'ODM', '2022-09-08', 1)
    """)
    
    # Peter Jones - only current term
    cursor.execute("""
        INSERT INTO mp_terms (mp_id, term_id, constituency, party, elected_date, is_current)
        VALUES (3, 2, 'KISUMU EAST', 'ANC', '2022-09-08', 1)
    """)
    
    # Hansard sessions
    cursor.execute("""
        INSERT INTO hansard_sessions (id, term_id, date, title, pdf_url)
        VALUES (1, 2, '2024-01-15', 'Session 1', 'http://example.com/hansard1.pdf')
    """)
    cursor.execute("""
        INSERT INTO hansard_sessions (id, term_id, date, title, pdf_url)
        VALUES (2, 2, '2024-01-16', 'Session 2', 'http://example.com/hansard2.pdf')
    """)
    
    # Statements
    # John Doe - 3 statements, 2 sessions, 1 bill
    cursor.execute("""
        INSERT INTO statements (mp_id, session_id, text, page_number, bill_reference)
        VALUES (1, 1, 'Statement 1', 5, 'Bill No. 123')
    """)
    cursor.execute("""
        INSERT INTO statements (mp_id, session_id, text, page_number)
        VALUES (1, 1, 'Statement 2', 6)
    """)
    cursor.execute("""
        INSERT INTO statements (mp_id, session_id, text, page_number)
        VALUES (1, 2, 'Statement 3', 10)
    """)
    
    # Jane Smith - 1 statement, 1 session, 0 bills
    cursor.execute("""
        INSERT INTO statements (mp_id, session_id, text, page_number)
        VALUES (2, 1, 'Statement 4', 7)
    """)
    
    # Peter Jones - 0 statements
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink()


def test_get_db_connection(test_db):
    """Test database connection."""
    conn = get_db_connection(test_db)
    assert conn is not None
    
    # Test row factory
    cursor = conn.cursor()
    cursor.execute("SELECT 1 as test")
    row = cursor.fetchone()
    assert row['test'] == 1
    
    conn.close()


def test_generate_keywords_basic():
    """Test keyword generation with basic MP data."""
    mp_data = {
        'name': 'JOHN DOE',
        'constituency': 'NAIROBI CENTRAL',
        'party': 'UDA'
    }
    
    keywords = generate_keywords(mp_data)
    
    assert 'JOHN' in keywords
    assert 'DOE' in keywords
    assert 'NAIROBI' in keywords
    assert 'CENTRAL' in keywords
    assert 'NAIROBI CENTRAL' in keywords
    assert 'UDA' in keywords


def test_generate_keywords_with_county():
    """Test keyword generation with county data."""
    mp_data = {
        'name': 'JANE SMITH',
        'constituency': 'MOMBASA NORTH',
        'party': 'ODM',
        'county': 'MOMBASA'
    }
    
    keywords = generate_keywords(mp_data)
    
    assert 'JANE' in keywords
    assert 'SMITH' in keywords
    assert 'MOMBASA' in keywords
    assert 'NORTH' in keywords
    assert 'ODM' in keywords


def test_generate_keywords_no_duplicates():
    """Test that keywords don't contain duplicates."""
    mp_data = {
        'name': 'PETER JONES',
        'constituency': 'KISUMU EAST',
        'party': 'ANC',
        'county': 'KISUMU'
    }
    
    keywords = generate_keywords(mp_data)
    
    # KISUMU appears in both constituency and county
    assert keywords.count('KISUMU') == 1


def test_generate_keywords_empty_data():
    """Test keyword generation with empty data."""
    mp_data = {}
    keywords = generate_keywords(mp_data)
    assert keywords == []


def test_generate_keywords_none_values():
    """Test keyword generation with None values."""
    mp_data = {
        'name': 'JOHN DOE',
        'constituency': None,
        'party': None
    }
    
    keywords = generate_keywords(mp_data)
    
    assert 'JOHN' in keywords
    assert 'DOE' in keywords
    assert len(keywords) == 2


def test_generate_search_index_basic(test_db, tmp_path):
    """Test basic search index generation."""
    output_dir = tmp_path / 'output'
    
    generate_search_index(db_path=test_db, output_dir=output_dir)
    
    # Check output file exists
    index_file = output_dir / 'data' / 'mp-search-index.json'
    assert index_file.exists()
    
    # Load and verify JSON
    with open(index_file, 'r', encoding='utf-8') as f:
        search_index = json.load(f)
    
    assert len(search_index) == 3  # 3 current MPs


def test_generate_search_index_mp_data(test_db, tmp_path):
    """Test search index contains correct MP data."""
    output_dir = tmp_path / 'output'
    
    generate_search_index(db_path=test_db, output_dir=output_dir)
    
    # Load JSON
    index_file = output_dir / 'data' / 'mp-search-index.json'
    with open(index_file, 'r', encoding='utf-8') as f:
        search_index = json.load(f)
    
    # Find John Doe
    john_doe = next(mp for mp in search_index if mp['name'] == 'JOHN DOE')
    
    assert john_doe['id'] == 1
    assert john_doe['constituency'] == 'NAIROBI CENTRAL'
    assert john_doe['party'] == 'UDA'
    assert john_doe['photo_url'] == 'http://example.com/photo1.jpg'


def test_generate_search_index_current_term_data(test_db, tmp_path):
    """Test search index contains current term performance data."""
    output_dir = tmp_path / 'output'
    
    generate_search_index(db_path=test_db, output_dir=output_dir)
    
    # Load JSON
    index_file = output_dir / 'data' / 'mp-search-index.json'
    with open(index_file, 'r', encoding='utf-8') as f:
        search_index = json.load(f)
    
    # Find John Doe
    john_doe = next(mp for mp in search_index if mp['name'] == 'JOHN DOE')
    
    assert john_doe['current_term']['term_number'] == 13
    assert john_doe['current_term']['statement_count'] == 3
    assert john_doe['current_term']['sessions_attended'] == 2
    assert john_doe['current_term']['bills_mentioned'] == 1
    
    # Find Jane Smith
    jane_smith = next(mp for mp in search_index if mp['name'] == 'JANE SMITH')
    
    assert jane_smith['current_term']['statement_count'] == 1
    assert jane_smith['current_term']['sessions_attended'] == 1
    assert jane_smith['current_term']['bills_mentioned'] == 0
    
    # Find Peter Jones (no statements)
    peter_jones = next(mp for mp in search_index if mp['name'] == 'PETER JONES')
    
    assert peter_jones['current_term']['statement_count'] == 0
    assert peter_jones['current_term']['sessions_attended'] == 0
    assert peter_jones['current_term']['bills_mentioned'] == 0


def test_generate_search_index_historical_terms(test_db, tmp_path):
    """Test search index contains historical terms data."""
    output_dir = tmp_path / 'output'
    
    generate_search_index(db_path=test_db, output_dir=output_dir)
    
    # Load JSON
    index_file = output_dir / 'data' / 'mp-search-index.json'
    with open(index_file, 'r', encoding='utf-8') as f:
        search_index = json.load(f)
    
    # Find John Doe (served in 2 terms)
    john_doe = next(mp for mp in search_index if mp['name'] == 'JOHN DOE')
    
    assert len(john_doe['historical_terms']) == 2
    
    # Check current term (13)
    current_term = next(t for t in john_doe['historical_terms'] if t['term_number'] == 13)
    assert current_term['constituency'] == 'NAIROBI CENTRAL'
    assert current_term['party'] == 'UDA'
    assert current_term['elected_date'] == '2022-09-08'
    
    # Check previous term (12)
    previous_term = next(t for t in john_doe['historical_terms'] if t['term_number'] == 12)
    assert previous_term['constituency'] == 'NAIROBI CENTRAL'
    assert previous_term['party'] == 'JP'
    assert previous_term['elected_date'] == '2017-08-31'
    
    # Find Jane Smith (only current term)
    jane_smith = next(mp for mp in search_index if mp['name'] == 'JANE SMITH')
    
    assert len(jane_smith['historical_terms']) == 1
    assert jane_smith['historical_terms'][0]['term_number'] == 13


def test_generate_search_index_keywords(test_db, tmp_path):
    """Test search index contains keywords."""
    output_dir = tmp_path / 'output'
    
    generate_search_index(db_path=test_db, output_dir=output_dir)
    
    # Load JSON
    index_file = output_dir / 'data' / 'mp-search-index.json'
    with open(index_file, 'r', encoding='utf-8') as f:
        search_index = json.load(f)
    
    # Check all MPs have keywords
    for mp in search_index:
        assert 'keywords' in mp
        assert isinstance(mp['keywords'], list)
        assert len(mp['keywords']) > 0


def test_generate_search_index_sorted_by_name(test_db, tmp_path):
    """Test search index is sorted by MP name."""
    output_dir = tmp_path / 'output'
    
    generate_search_index(db_path=test_db, output_dir=output_dir)
    
    # Load JSON
    index_file = output_dir / 'data' / 'mp-search-index.json'
    with open(index_file, 'r', encoding='utf-8') as f:
        search_index = json.load(f)
    
    # Check order
    names = [mp['name'] for mp in search_index]
    assert names == sorted(names)


def test_generate_search_index_json_format(test_db, tmp_path):
    """Test search index JSON is properly formatted."""
    output_dir = tmp_path / 'output'
    
    generate_search_index(db_path=test_db, output_dir=output_dir)
    
    # Load JSON
    index_file = output_dir / 'data' / 'mp-search-index.json'
    with open(index_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check it's valid JSON
    json.loads(content)
    
    # Check it's indented (pretty-printed)
    assert '\n' in content
    assert '  ' in content


def test_generate_search_index_missing_database(tmp_path):
    """Test error handling when database doesn't exist."""
    output_dir = tmp_path / 'output'
    missing_db = tmp_path / 'missing.db'
    
    with pytest.raises(SystemExit):
        generate_search_index(db_path=missing_db, output_dir=output_dir)


def test_generate_search_index_creates_output_directory(test_db, tmp_path):
    """Test that output directory is created if it doesn't exist."""
    output_dir = tmp_path / 'new_output' / 'nested'
    
    assert not output_dir.exists()
    
    generate_search_index(db_path=test_db, output_dir=output_dir)
    
    assert output_dir.exists()
    assert (output_dir / 'data').exists()
    assert (output_dir / 'data' / 'mp-search-index.json').exists()
