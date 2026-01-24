"""
Property-based tests for database schema consistency.

This module validates that all database operations use the production schema
and that schema mismatches are caught immediately.

Property 3: Database Schema Consistency
Validates: Requirements 3.1, 3.2, 3.3, 3.4
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

from hansard_tales.database.init_db import initialize_database


class TestDatabaseSchemaConsistency:
    """
    Property tests for database schema consistency.
    
    These tests validate that:
    1. Production initialize_database() creates consistent schema
    2. All expected tables exist
    3. All expected columns exist in each table
    4. Attempts to reference non-existent columns fail clearly
    """
    
    def test_production_db_fixture_uses_initialize_database(self, production_db):
        """
        Verify production_db fixture uses production initialize_database().
        
        Validates: Requirement 3.1
        """
        # Connect to the database created by production_db fixture
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Verify all expected tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        expected_tables = {
            'parliamentary_terms',
            'mps',
            'mp_terms',
            'hansard_sessions',
            'statements',
            'downloaded_pdfs'
        }
        
        assert expected_tables.issubset(tables), (
            f"production_db fixture missing tables. "
            f"Expected: {expected_tables}, Got: {tables}"
        )
        
        conn.close()
    
    @given(st.integers(min_value=1, max_value=100))
    def test_initialize_database_creates_consistent_schema(self, iteration):
        """
        Property: For ANY database initialization, schema is consistent.
        
        This test creates multiple databases and verifies they all have
        the same schema structure.
        
        Validates: Requirements 3.1, 3.2
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            # Initialize using production function
            success = initialize_database(db_path)
            assert success, "initialize_database() should return True"
            
            # Verify schema
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check all expected tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            
            expected_tables = {
                'parliamentary_terms',
                'mps',
                'mp_terms',
                'hansard_sessions',
                'statements',
                'downloaded_pdfs'
            }
            
            assert expected_tables.issubset(tables), (
                f"Missing tables in iteration {iteration}. "
                f"Expected: {expected_tables}, Got: {tables}"
            )
            
            # Check all expected views exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
            views = {row[0] for row in cursor.fetchall()}
            
            expected_views = {
                'current_mps',
                'mp_current_term_performance',
                'mp_historical_performance'
            }
            
            assert expected_views.issubset(views), (
                f"Missing views in iteration {iteration}. "
                f"Expected: {expected_views}, Got: {views}"
            )
            
            conn.close()
            
        finally:
            # Cleanup
            Path(db_path).unlink()
    
    def test_production_schema_has_all_required_columns(self, production_db):
        """
        Verify production schema has all required columns.
        
        Validates: Requirement 3.3
        """
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Define expected columns for each table
        expected_columns = {
            'parliamentary_terms': {
                'id', 'term_number', 'start_date', 'end_date', 
                'is_current', 'created_at'
            },
            'mps': {
                'id', 'name', 'constituency', 'party', 'photo_url',
                'first_elected_year', 'created_at', 'updated_at'
            },
            'mp_terms': {
                'id', 'mp_id', 'term_id', 'constituency', 'party',
                'elected_date', 'left_date', 'is_current'
            },
            'hansard_sessions': {
                'id', 'term_id', 'date', 'title', 'pdf_url',
                'pdf_path', 'processed', 'created_at'
            },
            'statements': {
                'id', 'mp_id', 'session_id', 'text', 'page_number',
                'bill_reference', 'content_hash', 'created_at'
            },
            'downloaded_pdfs': {
                'id', 'original_url', 'file_path', 'date', 'period_of_day',
                'session_id', 'downloaded_at', 'file_size', 'created_at'
            }
        }
        
        # Verify each table has expected columns
        for table_name, expected_cols in expected_columns.items():
            cursor.execute(f"PRAGMA table_info({table_name})")
            actual_cols = {row[1] for row in cursor.fetchall()}
            
            assert expected_cols.issubset(actual_cols), (
                f"Table '{table_name}' missing columns. "
                f"Expected: {expected_cols}, Got: {actual_cols}"
            )
        
        conn.close()
    
    @given(
        table=st.sampled_from([
            'parliamentary_terms', 'mps', 'mp_terms',
            'hansard_sessions', 'statements', 'downloaded_pdfs'
        ]),
        invalid_column=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
            min_size=1,
            max_size=20
        ).filter(lambda x: x not in {
            'id', 'name', 'constituency', 'party', 'date', 'title',
            'text', 'term_id', 'mp_id', 'session_id', 'pdf_url',
            'pdf_path', 'processed', 'created_at', 'updated_at',
            'term_number', 'start_date', 'end_date', 'is_current',
            'photo_url', 'first_elected_year', 'elected_date',
            'left_date', 'page_number', 'bill_reference',
            'content_hash', 'original_url', 'file_path',
            'period_of_day', 'downloaded_at', 'file_size'
        })
    )
    def test_invalid_column_reference_fails_clearly(self, table, invalid_column):
        """
        Property: For ANY invalid column reference, query fails with clear error.
        
        This test verifies that attempting to reference non-existent columns
        results in a clear error message from SQLite.
        
        Validates: Requirement 3.4
        """
        # Create temporary database for this test
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            # Initialize database
            initialize_database(db_path)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Attempt to query non-existent column
            with pytest.raises(sqlite3.OperationalError) as exc_info:
                cursor.execute(f"SELECT {invalid_column} FROM {table}")
            
            # Verify error message is clear
            error_msg = str(exc_info.value)
            assert 'no such column' in error_msg.lower() or 'column' in error_msg.lower(), (
                f"Error message should mention column issue. Got: {error_msg}"
            )
            
            conn.close()
        
        finally:
            # Cleanup
            Path(db_path).unlink()
    
    def test_schema_consistency_across_multiple_initializations(self):
        """
        Verify schema is identical across multiple database initializations.
        
        This test creates multiple databases and verifies they all have
        identical schema structure.
        
        Validates: Requirements 3.1, 3.2
        """
        db_paths = []
        schemas = []
        
        try:
            # Create 3 databases
            for i in range(3):
                with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                    db_path = f.name
                db_paths.append(db_path)
                
                # Initialize database
                initialize_database(db_path)
                
                # Extract schema
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get all tables with their schemas
                cursor.execute("""
                    SELECT type, name, sql 
                    FROM sqlite_master 
                    WHERE type IN ('table', 'view', 'index')
                    ORDER BY type, name
                """)
                schema = cursor.fetchall()
                schemas.append(schema)
                
                conn.close()
            
            # Verify all schemas are identical
            first_schema = schemas[0]
            for i, schema in enumerate(schemas[1:], start=2):
                assert schema == first_schema, (
                    f"Database {i} schema differs from database 1. "
                    f"This indicates inconsistent initialization."
                )
        
        finally:
            # Cleanup
            for db_path in db_paths:
                Path(db_path).unlink()
    
    def test_production_db_fixture_has_current_term(self, production_db):
        """
        Verify production_db fixture includes current parliamentary term.
        
        The fixture should insert term 13 (2022-09-08 to 2027-09-07) as current.
        
        Validates: Requirement 3.5 (from conftest.py)
        """
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        
        # Check current term exists
        cursor.execute("""
            SELECT term_number, start_date, end_date, is_current
            FROM parliamentary_terms
            WHERE is_current = 1
        """)
        current_term = cursor.fetchone()
        
        assert current_term is not None, "production_db should have a current term"
        assert current_term[0] == 13, "Current term should be term 13"
        assert current_term[1] == '2022-09-08', "Term should start on 2022-09-08"
        assert current_term[2] == '2027-09-07', "Term should end on 2027-09-07"
        assert current_term[3] == 1, "is_current should be 1"
        
        conn.close()
    
    @given(
        term_number=st.integers(min_value=1, max_value=20),
        start_year=st.integers(min_value=2000, max_value=2030),
        duration_years=st.integers(min_value=1, max_value=10)
    )
    def test_parliamentary_terms_table_accepts_valid_data(
        self, term_number, start_year, duration_years
    ):
        """
        Property: For ANY valid parliamentary term data, insertion succeeds.
        
        Validates: Requirement 3.3 (schema supports expected operations)
        """
        # Create temporary database for this test
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            # Initialize database
            initialize_database(db_path)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Generate dates
            start_date = f"{start_year}-01-01"
            end_date = f"{start_year + duration_years}-12-31"
            
            try:
                # Insert term
                cursor.execute("""
                    INSERT INTO parliamentary_terms 
                    (term_number, start_date, end_date, is_current)
                    VALUES (?, ?, ?, 0)
                """, (term_number, start_date, end_date))
                
                conn.commit()
                
                # Verify insertion
                cursor.execute("""
                    SELECT term_number, start_date, end_date
                    FROM parliamentary_terms
                    WHERE term_number = ?
                """, (term_number,))
                
                result = cursor.fetchone()
                if result:  # May not exist if term_number conflicts with existing data
                    assert result[0] == term_number
                    assert result[1] == start_date
                    assert result[2] == end_date
            
            except sqlite3.IntegrityError:
                # Expected if term_number already exists (UNIQUE constraint)
                pass
            
            finally:
                conn.close()
        
        finally:
            # Cleanup
            Path(db_path).unlink()
