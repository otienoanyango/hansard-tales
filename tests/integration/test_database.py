"""
Tests for database initialization and schema.

This module verifies that the database schema is correctly created
with all required tables, indexes, and views.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the init_db module
from hansard_tales.database.init_db import (
    create_tables,
    create_indexes,
    create_views,
    verify_schema,
    initialize_database
)


@pytest.fixture
def db_connection(production_db):
    """Create a database connection for testing."""
    conn = sqlite3.connect(production_db)
    yield conn
    conn.close()


class TestDatabaseSchema:
    """Test suite for database schema creation."""
    
    def test_create_tables(self, db_connection):
        """Test that all required tables are created."""
        create_tables(db_connection)
        
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'parliamentary_terms',
            'mps',
            'mp_terms',
            'hansard_sessions',
            'statements'
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table {table} not created"
    
    def test_parliamentary_terms_table_structure(self, db_connection):
        """Test parliamentary_terms table has correct columns."""
        create_tables(db_connection)
        
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(parliamentary_terms)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        assert 'id' in columns
        assert 'term_number' in columns
        assert 'start_date' in columns
        assert 'end_date' in columns
        assert 'is_current' in columns
        assert 'created_at' in columns
    
    def test_mps_table_structure(self, db_connection):
        """Test mps table has correct columns."""
        create_tables(db_connection)
        
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(mps)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        assert 'id' in columns
        assert 'name' in columns
        assert 'constituency' in columns
        assert 'party' in columns
        assert 'photo_url' in columns
        assert 'first_elected_year' in columns
    
    def test_mp_terms_table_structure(self, db_connection):
        """Test mp_terms junction table has correct columns."""
        create_tables(db_connection)
        
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(mp_terms)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        assert 'id' in columns
        assert 'mp_id' in columns
        assert 'term_id' in columns
        assert 'constituency' in columns
        assert 'party' in columns
        assert 'elected_date' in columns
        assert 'left_date' in columns
        assert 'is_current' in columns
    
    def test_hansard_sessions_table_structure(self, db_connection):
        """Test hansard_sessions table has correct columns."""
        create_tables(db_connection)
        
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(hansard_sessions)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        assert 'id' in columns
        assert 'term_id' in columns
        assert 'date' in columns
        assert 'title' in columns
        assert 'pdf_url' in columns
        assert 'pdf_path' in columns
        assert 'processed' in columns
    
    def test_statements_table_structure(self, db_connection):
        """Test statements table has correct columns."""
        create_tables(db_connection)
        
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(statements)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        assert 'id' in columns
        assert 'mp_id' in columns
        assert 'session_id' in columns
        assert 'text' in columns
        assert 'page_number' in columns
        assert 'bill_reference' in columns
    
    def test_create_indexes(self, db_connection):
        """Test that all required indexes are created."""
        create_tables(db_connection)
        create_indexes(db_connection)
        
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        expected_indexes = [
            'idx_statements_mp',
            'idx_statements_session',
            'idx_statements_bill',
            'idx_hansard_date',
            'idx_hansard_term',
            'idx_mp_terms_current',
            'idx_mp_terms_mp',
            'idx_mp_terms_term',
        ]
        
        for index in expected_indexes:
            assert index in indexes, f"Index {index} not created"
    
    def test_create_views(self, db_connection):
        """Test that all required views are created."""
        create_tables(db_connection)
        create_views(db_connection)
        
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]
        
        expected_views = [
            'current_mps',
            'mp_current_term_performance',
            'mp_historical_performance'
        ]
        
        for view in expected_views:
            assert view in views, f"View {view} not created"
    
    def test_current_mps_view_structure(self, db_connection):
        """Test current_mps view can be queried."""
        create_tables(db_connection)
        create_views(db_connection)
        
        cursor = db_connection.cursor()
        # Should not raise an error
        cursor.execute("SELECT * FROM current_mps LIMIT 0")
        columns = [description[0] for description in cursor.description]
        
        expected_columns = [
            'id', 'name', 'constituency', 'party', 
            'photo_url', 'first_elected_year', 
            'current_term_start', 'term_number'
        ]
        
        for col in expected_columns:
            assert col in columns, f"Column {col} not in current_mps view"
    
    def test_verify_schema_success(self, db_connection):
        """Test schema verification passes with complete schema."""
        create_tables(db_connection)
        create_indexes(db_connection)
        create_views(db_connection)
        
        assert verify_schema(db_connection) is True
    
    def test_verify_schema_missing_tables(self):
        """Test schema verification fails with missing tables."""
        # Create a fresh empty database (not using production_db)
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            empty_db = f.name
        
        try:
            conn = sqlite3.connect(empty_db)
            # Don't create tables
            assert verify_schema(conn) is False
            conn.close()
        finally:
            Path(empty_db).unlink(missing_ok=True)
    
    def test_initialize_database(self, production_db):
        """Test full database initialization."""
        # production_db already initializes the database, so we just verify it works
        assert Path(production_db).exists()
        
        # Verify database is usable
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        assert len(tables) >= 5
    
    def test_foreign_key_constraints(self, db_connection):
        """Test that foreign key constraints are enforced."""
        create_tables(db_connection)
        
        # Enable foreign keys
        db_connection.execute("PRAGMA foreign_keys = ON")
        
        cursor = db_connection.cursor()
        
        # Try to insert mp_term without corresponding mp (should fail)
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO mp_terms (mp_id, term_id, constituency)
                VALUES (999, 1, 'Test Constituency')
            """)
    
    def test_unique_constraints(self, db_connection):
        """Test that unique constraints are enforced."""
        create_tables(db_connection)
        
        cursor = db_connection.cursor()
        
        # Insert a parliamentary term (use a different term number than production_db's term 13)
        cursor.execute("""
            INSERT INTO parliamentary_terms (term_number, start_date)
            VALUES (14, '2027-09-08')
        """)
        
        # Try to insert duplicate term_number (should fail)
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO parliamentary_terms (term_number, start_date)
                VALUES (14, '2027-09-08')
            """)


class TestDatabaseOperations:
    """Test suite for basic database operations."""
    
    def test_insert_parliamentary_term(self, db_connection):
        """Test inserting a parliamentary term."""
        create_tables(db_connection)
        
        cursor = db_connection.cursor()
        # Use a different term number than production_db's term 13
        cursor.execute("""
            INSERT INTO parliamentary_terms 
            (term_number, start_date, end_date, is_current)
            VALUES (14, '2027-09-08', '2032-09-07', 0)
        """)
        db_connection.commit()
        
        cursor.execute("SELECT * FROM parliamentary_terms WHERE term_number = 14")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 14  # term_number
        assert result[4] == 0   # is_current
    
    def test_insert_mp(self, db_connection):
        """Test inserting an MP."""
        create_tables(db_connection)
        
        cursor = db_connection.cursor()
        cursor.execute("""
            INSERT INTO mps (name, constituency, party, first_elected_year)
            VALUES ('John Doe', 'Nairobi West', 'ODM', 2022)
        """)
        db_connection.commit()
        
        cursor.execute("SELECT * FROM mps WHERE name = 'John Doe'")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 'John Doe'
        assert result[2] == 'Nairobi West'
    
    def test_link_mp_to_term(self, db_connection):
        """Test linking an MP to a parliamentary term."""
        create_tables(db_connection)
        
        cursor = db_connection.cursor()
        
        # Insert term (use a different term number than production_db's term 13)
        cursor.execute("""
            INSERT INTO parliamentary_terms 
            (term_number, start_date, is_current)
            VALUES (14, '2027-09-08', 0)
        """)
        term_id = cursor.lastrowid
        
        # Insert MP
        cursor.execute("""
            INSERT INTO mps (name, constituency, party)
            VALUES ('Jane Smith', 'Mombasa North', 'Jubilee')
        """)
        mp_id = cursor.lastrowid
        
        # Link MP to term
        cursor.execute("""
            INSERT INTO mp_terms 
            (mp_id, term_id, constituency, party, is_current)
            VALUES (?, ?, 'Mombasa North', 'Jubilee', 0)
        """, (mp_id, term_id))
        db_connection.commit()
        
        # Verify link
        cursor.execute("""
            SELECT * FROM mp_terms 
            WHERE mp_id = ? AND term_id = ?
        """, (mp_id, term_id))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == mp_id
        assert result[2] == term_id



class TestFilePathValidation:
    """Test suite for file path validation in database."""
    
    def test_hansard_sessions_file_paths_reference_existing_files(self, production_db):
        """
        Test that file paths in hansard_sessions reference existing files.
        
        Validates: Requirement 5.9 (file path validation)
        """
        import tempfile
        import shutil
        from hansard_tales.storage.filesystem import FilesystemStorage
        
        # Create temporary storage directory
        temp_dir = tempfile.mkdtemp()
        storage = FilesystemStorage(temp_dir)
        
        try:
            conn = sqlite3.connect(production_db)
            cursor = conn.cursor()
            
            # Create a test file
            test_filename = "hansard_20240115_P.pdf"
            storage.write(test_filename, b"Test PDF content")
            
            # Insert session with file path
            cursor.execute("""
                INSERT INTO hansard_sessions 
                (term_id, date, title, pdf_url, pdf_path)
                VALUES (1, '2024-01-15', 'Test Session', 
                        'https://example.com/test.pdf', ?)
            """, (test_filename,))
            conn.commit()
            
            # Get all file paths from database
            cursor.execute("SELECT pdf_path FROM hansard_sessions WHERE pdf_path IS NOT NULL")
            file_paths = [row[0] for row in cursor.fetchall()]
            
            # Verify all file paths reference existing files
            for file_path in file_paths:
                assert storage.exists(file_path), (
                    f"File path in database doesn't exist: {file_path}"
                )
            
            conn.close()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_downloaded_pdfs_file_paths_reference_existing_files(self, production_db):
        """
        Test that file paths in downloaded_pdfs reference existing files.
        
        Validates: Requirement 5.9 (file path validation)
        """
        import tempfile
        import shutil
        from hansard_tales.storage.filesystem import FilesystemStorage
        
        # Create temporary storage directory
        temp_dir = tempfile.mkdtemp()
        storage = FilesystemStorage(temp_dir)
        
        try:
            conn = sqlite3.connect(production_db)
            cursor = conn.cursor()
            
            # Create test files
            test_files = [
                "hansard_20240115_P.pdf",
                "hansard_20240116_A.pdf"
            ]
            
            for filename in test_files:
                storage.write(filename, b"Test PDF content")
                
                # Insert record with file path
                cursor.execute("""
                    INSERT INTO downloaded_pdfs 
                    (original_url, file_path, date, file_size)
                    VALUES (?, ?, '2024-01-15', 1024)
                """, (f"https://example.com/{filename}", filename))
            
            conn.commit()
            
            # Get all file paths from database
            cursor.execute("SELECT file_path FROM downloaded_pdfs WHERE file_path IS NOT NULL")
            file_paths = [row[0] for row in cursor.fetchall()]
            
            # Verify all file paths reference existing files
            for file_path in file_paths:
                assert storage.exists(file_path), (
                    f"File path in database doesn't exist: {file_path}"
                )
            
            conn.close()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_file_path_validation_detects_missing_files(self, production_db):
        """
        Test that file path validation detects missing files.
        
        Validates: Requirement 5.9 (file path validation)
        """
        import tempfile
        import shutil
        from hansard_tales.storage.filesystem import FilesystemStorage
        
        # Create temporary storage directory
        temp_dir = tempfile.mkdtemp()
        storage = FilesystemStorage(temp_dir)
        
        try:
            conn = sqlite3.connect(production_db)
            cursor = conn.cursor()
            
            # Insert record with non-existent file path
            missing_filename = "nonexistent_file.pdf"
            cursor.execute("""
                INSERT INTO downloaded_pdfs 
                (original_url, file_path, date, file_size)
                VALUES (?, ?, '2024-01-15', 1024)
            """, (f"https://example.com/{missing_filename}", missing_filename))
            conn.commit()
            
            # Get file path from database
            cursor.execute("SELECT file_path FROM downloaded_pdfs WHERE file_path = ?", 
                          (missing_filename,))
            file_path = cursor.fetchone()[0]
            
            # Verify that storage.exists() returns False for missing file
            assert not storage.exists(file_path), (
                f"Expected file to not exist: {file_path}"
            )
            
            conn.close()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_file_path_validation_with_null_paths(self, production_db):
        """
        Test that file path validation handles NULL paths gracefully.
        
        Validates: Requirement 5.9 (file path validation)
        """
        import tempfile
        import shutil
        from hansard_tales.storage.filesystem import FilesystemStorage
        
        # Create temporary storage directory
        temp_dir = tempfile.mkdtemp()
        storage = FilesystemStorage(temp_dir)
        
        try:
            conn = sqlite3.connect(production_db)
            cursor = conn.cursor()
            
            # Insert record with NULL file path
            cursor.execute("""
                INSERT INTO hansard_sessions 
                (term_id, date, title, pdf_url, pdf_path)
                VALUES (1, '2024-01-15', 'Test Session', 
                        'https://example.com/test.pdf', NULL)
            """)
            conn.commit()
            
            # Get all non-NULL file paths from database
            cursor.execute("SELECT pdf_path FROM hansard_sessions WHERE pdf_path IS NOT NULL")
            file_paths = [row[0] for row in cursor.fetchall()]
            
            # Should not include NULL paths
            assert None not in file_paths
            
            # All non-NULL paths should be validated
            for file_path in file_paths:
                # This test just ensures we can call exists() without error
                # The actual existence check is done in other tests
                result = storage.exists(file_path)
                assert isinstance(result, bool)
            
            conn.close()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestInitDBCLI:
    """Test suite for init_db CLI."""
    
    @patch('hansard_tales.database.init_db.initialize_database')
    @patch('sys.argv', ['hansard-init-db', '--db-path', 'test.db'])
    def test_main_with_arguments(self, mock_init_db):
        """Test init_db main() with custom arguments."""
        from hansard_tales.database.init_db import main
        
        # Run main
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Should exit with 0 (success)
        assert exc_info.value.code == 0
        
        # Verify initialize_database was called
        mock_init_db.assert_called_once_with('test.db')
    
    @patch('pathlib.Path.exists')
    @patch('hansard_tales.database.init_db.initialize_database')
    @patch('sys.argv', ['hansard-init-db'])
    def test_main_default_path(self, mock_init_db, mock_path_exists):
        """Test init_db main() with default database path."""
        from hansard_tales.database.init_db import main
        
        # Mock that database doesn't exist
        mock_path_exists.return_value = False
        
        # Mock successful initialization
        mock_init_db.return_value = True
        
        # Run main
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Should exit with 0 (success)
        assert exc_info.value.code == 0
        
        # Verify initialize_database was called with default path
        mock_init_db.assert_called_once_with('data/hansard.db')
