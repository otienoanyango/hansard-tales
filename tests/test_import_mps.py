#!/usr/bin/env python3
"""
Tests for MP Import Script

Tests the import functionality for MP data into the database
"""

import json
import pytest
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

from hansard_tales.database.import_mps import MPImporter


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary test database"""
    db_path = tmp_path / 'test.db'
    
    # Create database schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE parliamentary_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_number INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            is_current BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE mps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            constituency TEXT,
            party TEXT,
            photo_url TEXT,
            first_elected_year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE mp_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mp_id INTEGER NOT NULL,
            term_id INTEGER NOT NULL,
            constituency TEXT,
            party TEXT,
            elected_date DATE,
            left_date DATE,
            is_current BOOLEAN DEFAULT 0,
            FOREIGN KEY (mp_id) REFERENCES mps(id),
            FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id),
            UNIQUE(mp_id, term_id)
        )
    """)
    
    # Insert test parliamentary terms
    cursor.execute("""
        INSERT INTO parliamentary_terms (term_number, start_date, end_date, is_current)
        VALUES (13, '2022-09-08', '2027-09-07', 1)
    """)
    
    cursor.execute("""
        INSERT INTO parliamentary_terms (term_number, start_date, end_date, is_current)
        VALUES (12, '2017-08-31', '2022-09-07', 0)
    """)
    
    conn.commit()
    conn.close()
    
    return str(db_path)


@pytest.fixture
def sample_mp_data():
    """Sample MP data for testing"""
    return [
        {
            'name': 'JOHN DOE',
            'county': 'NAIROBI',
            'constituency': 'WESTLANDS',
            'party': 'ODM',
            'status': 'Elected',
            'photo_url': 'http://example.com/john.jpg',
            'term_start_year': 2022
        },
        {
            'name': 'JANE SMITH',
            'county': None,
            'constituency': None,
            'party': 'UDA',
            'status': 'Nominated',
            'photo_url': 'http://example.com/jane.jpg',
            'term_start_year': 2022
        }
    ]


@pytest.fixture
def sample_json_file(tmp_path, sample_mp_data):
    """Create a temporary JSON file with sample data"""
    json_path = tmp_path / 'mps.json'
    with open(json_path, 'w') as f:
        json.dump(sample_mp_data, f)
    return str(json_path)


class TestMPImporter:
    """Test suite for MPImporter"""
    
    def test_initialization(self, temp_db):
        """Test importer initialization"""
        importer = MPImporter(db_path=temp_db)
        assert importer.db_path == temp_db
        assert importer.conn is None
        assert importer.cursor is None
    
    def test_connect(self, temp_db):
        """Test database connection"""
        importer = MPImporter(db_path=temp_db)
        importer.connect()
        
        assert importer.conn is not None
        assert importer.cursor is not None
        
        importer.close()
    
    def test_get_term_by_year(self, temp_db):
        """Test getting term by year"""
        importer = MPImporter(db_path=temp_db)
        importer.connect()
        
        # Test 2022 (13th Parliament)
        term_id = importer.get_term_by_year(2022)
        assert term_id == 1
        
        # Test 2017 (12th Parliament)
        term_id = importer.get_term_by_year(2017)
        assert term_id == 2
        
        # Test non-existent year
        term_id = importer.get_term_by_year(2000)
        assert term_id is None
        
        importer.close()
    
    def test_get_or_create_mp_new(self, temp_db):
        """Test creating a new MP"""
        importer = MPImporter(db_path=temp_db)
        importer.connect()
        
        mp_data = {
            'name': 'JOHN DOE',
            'constituency': 'WESTLANDS',
            'party': 'ODM',
            'photo_url': 'http://example.com/john.jpg'
        }
        
        mp_id = importer.get_or_create_mp(mp_data)
        
        assert mp_id is not None
        assert mp_id > 0
        
        # Verify MP was created
        importer.cursor.execute("SELECT * FROM mps WHERE id = ?", (mp_id,))
        mp = importer.cursor.fetchone()
        
        assert mp is not None
        assert mp[1] == 'JOHN DOE'  # name
        assert mp[2] == 'WESTLANDS'  # constituency
        assert mp[3] == 'ODM'  # party
        
        importer.close()
    
    def test_get_or_create_mp_existing(self, temp_db):
        """Test getting an existing MP"""
        importer = MPImporter(db_path=temp_db)
        importer.connect()
        
        mp_data = {
            'name': 'JOHN DOE',
            'constituency': 'WESTLANDS',
            'party': 'ODM',
            'photo_url': 'http://example.com/john.jpg'
        }
        
        # Create MP first time
        mp_id1 = importer.get_or_create_mp(mp_data)
        
        # Try to create again
        mp_id2 = importer.get_or_create_mp(mp_data)
        
        # Should return same ID
        assert mp_id1 == mp_id2
        
        # Verify only one MP exists
        importer.cursor.execute("SELECT COUNT(*) FROM mps WHERE name = ?", ('JOHN DOE',))
        count = importer.cursor.fetchone()[0]
        assert count == 1
        
        importer.close()
    
    def test_link_mp_to_term(self, temp_db):
        """Test linking MP to parliamentary term"""
        importer = MPImporter(db_path=temp_db)
        importer.connect()
        
        # Create MP
        mp_data = {
            'name': 'JOHN DOE',
            'constituency': 'WESTLANDS',
            'party': 'ODM',
            'photo_url': 'http://example.com/john.jpg'
        }
        mp_id = importer.get_or_create_mp(mp_data)
        
        # Link to term
        result = importer.link_mp_to_term(mp_id, 1, mp_data, is_current=True)
        
        assert result is True
        
        # Verify link was created
        importer.cursor.execute("""
            SELECT * FROM mp_terms WHERE mp_id = ? AND term_id = ?
        """, (mp_id, 1))
        link = importer.cursor.fetchone()
        
        assert link is not None
        assert link[3] == 'WESTLANDS'  # constituency
        assert link[4] == 'ODM'  # party
        assert link[7] == 1  # is_current
        
        importer.close()
    
    def test_link_mp_to_term_duplicate(self, temp_db):
        """Test linking MP to term twice (should not create duplicate)"""
        importer = MPImporter(db_path=temp_db)
        importer.connect()
        
        # Create MP
        mp_data = {
            'name': 'JOHN DOE',
            'constituency': 'WESTLANDS',
            'party': 'ODM'
        }
        mp_id = importer.get_or_create_mp(mp_data)
        
        # Link to term first time
        result1 = importer.link_mp_to_term(mp_id, 1, mp_data)
        assert result1 is True
        
        # Try to link again
        result2 = importer.link_mp_to_term(mp_id, 1, mp_data)
        assert result2 is False
        
        # Verify only one link exists
        importer.cursor.execute("""
            SELECT COUNT(*) FROM mp_terms WHERE mp_id = ? AND term_id = ?
        """, (mp_id, 1))
        count = importer.cursor.fetchone()[0]
        assert count == 1
        
        importer.close()
    
    def test_import_from_json(self, temp_db, sample_json_file):
        """Test importing MPs from JSON file"""
        importer = MPImporter(db_path=temp_db)
        importer.connect()
        
        stats = importer.import_from_json(
            json_path=sample_json_file,
            is_current=True
        )
        
        assert stats['total'] == 2
        assert stats['new_mps'] == 2
        assert stats['new_links'] == 2
        assert stats['errors'] == 0
        
        # Verify MPs were created
        importer.cursor.execute("SELECT COUNT(*) FROM mps")
        mp_count = importer.cursor.fetchone()[0]
        assert mp_count == 2
        
        # Verify links were created
        importer.cursor.execute("SELECT COUNT(*) FROM mp_terms")
        link_count = importer.cursor.fetchone()[0]
        assert link_count == 2
        
        importer.close()
    
    def test_import_from_json_with_term_id(self, temp_db, sample_json_file):
        """Test importing with explicit term ID"""
        importer = MPImporter(db_path=temp_db)
        importer.connect()
        
        stats = importer.import_from_json(
            json_path=sample_json_file,
            term_id=1,
            is_current=True
        )
        
        assert stats['total'] == 2
        assert stats['new_mps'] == 2
        
        # Verify all linked to term 1
        importer.cursor.execute("SELECT COUNT(*) FROM mp_terms WHERE term_id = 1")
        count = importer.cursor.fetchone()[0]
        assert count == 2
        
        importer.close()
    
    def test_import_from_json_idempotent(self, temp_db, sample_json_file):
        """Test that importing twice doesn't create duplicates"""
        importer = MPImporter(db_path=temp_db)
        importer.connect()
        
        # Import first time
        stats1 = importer.import_from_json(sample_json_file)
        assert stats1['new_mps'] == 2
        assert stats1['new_links'] == 2
        
        # Import second time
        stats2 = importer.import_from_json(sample_json_file)
        assert stats2['new_mps'] == 0
        assert stats2['existing_mps'] == 2
        assert stats2['existing_links'] == 2
        
        # Verify no duplicates
        importer.cursor.execute("SELECT COUNT(*) FROM mps")
        mp_count = importer.cursor.fetchone()[0]
        assert mp_count == 2
        
        importer.cursor.execute("SELECT COUNT(*) FROM mp_terms")
        link_count = importer.cursor.fetchone()[0]
        assert link_count == 2
        
        importer.close()
    
    def test_verify_import(self, temp_db, sample_json_file):
        """Test import verification"""
        importer = MPImporter(db_path=temp_db)
        importer.connect()
        
        # Import data
        importer.import_from_json(sample_json_file, term_id=1)
        
        # Verify
        stats = importer.verify_import(term_id=1)
        
        assert stats['total_mps'] == 2
        assert stats['elected'] == 1  # JOHN DOE
        assert stats['nominated'] == 1  # JANE SMITH
        assert 'ODM' in stats['top_parties']
        assert 'UDA' in stats['top_parties']
        
        importer.close()
    
    def test_import_invalid_file(self, temp_db):
        """Test importing from non-existent file"""
        importer = MPImporter(db_path=temp_db)
        importer.connect()
        
        with pytest.raises(FileNotFoundError):
            importer.import_from_json('nonexistent.json')
        
        importer.close()
    
    def test_import_no_term(self, temp_db, tmp_path):
        """Test importing without term information"""
        importer = MPImporter(db_path=temp_db)
        importer.connect()
        
        # Create JSON without term_start_year
        data = [{'name': 'TEST MP', 'party': 'TEST'}]
        json_path = tmp_path / 'test.json'
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        with pytest.raises(ValueError):
            importer.import_from_json(str(json_path))
        
        importer.close()



class TestCLI:
    """Test suite for CLI argument parsing and main() function."""
    
    @patch('pathlib.Path.exists')
    @patch('hansard_tales.database.import_mps.MPImporter')
    @patch('builtins.open', new_callable=lambda: Mock(return_value=Mock(__enter__=Mock(return_value=Mock()), __exit__=Mock())))
    @patch('json.load')
    @patch('sys.argv', ['hansard-import-mps', '--file', 'test_mps.json', '--current'])
    def test_main_with_arguments(self, mock_json_load, mock_open, mock_importer_class, mock_exists):
        """Test main() with custom arguments."""
        from hansard_tales.database.import_mps import main
        
        # Mock file exists
        mock_exists.return_value = True
        
        # Mock JSON data
        mock_json_load.return_value = [
            {'name': 'Test MP', 'term_start_year': 2022}
        ]
        
        # Mock importer instance
        mock_importer = Mock()
        mock_importer.import_from_json.return_value = {
            'total': 10,
            'new_mps': 5,
            'existing_mps': 5,
            'new_links': 10,
            'existing_links': 0,
            'errors': 0
        }
        mock_importer.get_term_by_year.return_value = 1
        mock_importer.verify_import.return_value = {
            'total_mps': 10,
            'elected': 8,
            'nominated': 2,
            'top_parties': {'Party A': 5, 'Party B': 3}
        }
        mock_importer_class.return_value = mock_importer
        
        # Run main - returns 0 on success
        result = main()
        
        # Should return 0 (success)
        assert result == 0
        
        # Verify import_from_json was called
        mock_importer.import_from_json.assert_called_once()
    
    @patch('pathlib.Path.exists')
    @patch('hansard_tales.database.import_mps.MPImporter')
    @patch('pathlib.Path.open', create=True)
    @patch('json.load')
    @patch('sys.argv', ['hansard-import-mps', '--file', 'test_mps.json', '--term-id', '1'])
    def test_main_with_term_id(self, mock_json_load, mock_path_open, mock_importer_class, mock_exists):
        """Test main() with explicit term ID."""
        from hansard_tales.database.import_mps import main
        
        # Mock file exists
        mock_exists.return_value = True
        
        # Mock JSON data
        mock_json_load.return_value = [
            {'name': 'Test MP', 'term_start_year': 2022}
        ]
        
        # Mock importer instance
        mock_importer = Mock()
        mock_importer.import_from_json.return_value = {
            'total': 10,
            'new_mps': 10,
            'existing_mps': 0,
            'new_links': 10,
            'existing_links': 0,
            'errors': 0
        }
        mock_importer.verify_import.return_value = {
            'total_mps': 10,
            'elected': 8,
            'nominated': 2,
            'top_parties': {'Party A': 5, 'Party B': 3}
        }
        mock_importer_class.return_value = mock_importer
        
        # Run main - returns 0 on success
        result = main()
        
        # Should return 0 (success)
        assert result == 0
        
        # Verify import was successful
        mock_importer.import_from_json.assert_called_once()
