"""
Property-based tests for session linking functionality.

This module tests Property 7: Session Linking Updates Database
Validates that when a PDF is processed and linked to a session,
the downloaded_pdfs table is correctly updated with the session_id.
"""

import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from hansard_tales.database.db_updater import DatabaseUpdater
from hansard_tales.processors.mp_identifier import Statement


@contextmanager
def create_temp_db():
    """Create a temporary database with production schema for testing."""
    from hansard_tales.database.init_db import initialize_database
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Initialize with production schema
        initialize_database(db_path)
        
        # Add parliamentary term data for testing
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO parliamentary_terms 
            (term_number, start_date, end_date, is_current)
            VALUES (13, '2000-01-01', '2027-12-31', 1)
        """)
        conn.commit()
        conn.close()
        
        yield db_path
    finally:
        # Cleanup
        Path(db_path).unlink(missing_ok=True)


# Use production_db fixture from conftest.py
# Note: This test creates its own temp database with custom schema for session linking tests


class TestSessionLinkingProperty:
    """
    Property-based tests for session linking.
    
    Feature: end-to-end-workflow-validation
    Property 7: Session Linking Updates Database
    """
    
    @given(
        pdf_url=st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=10,
            max_size=50
        ).map(lambda s: f"http://example.com/{s}.pdf"),
        date=st.dates().map(lambda d: d.strftime('%Y-%m-%d')),
        title=st.text(min_size=5, max_size=50),
        mp_name=st.text(
            alphabet=st.characters(min_codepoint=65, max_codepoint=90) | 
                     st.characters(min_codepoint=97, max_codepoint=122) |
                     st.just(' '),
            min_size=5,
            max_size=30
        ).filter(lambda s: s.strip() != ''),
        statement_text=st.text(min_size=10, max_size=200)
    )
    @settings(max_examples=100, deadline=None)
    def test_session_linking_updates_database(
        self,
        pdf_url,
        date,
        title,
        mp_name,
        statement_text
    ):
        """
        Feature: end-to-end-workflow-validation, Property 7:
        For any processed PDF that is linked to a session,
        the downloaded_pdfs table should be updated with the session_id.
        
        **Validates: Requirements 6.4**
        """
        with create_temp_db() as temp_db:
            # Setup: Create a downloaded_pdfs record without session_id
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO downloaded_pdfs 
                (original_url, file_path, date, period_of_day, session_id)
                VALUES (?, ?, ?, 'P', NULL)
            """, (pdf_url, f"/path/to/{Path(pdf_url).name}", date))
            
            conn.commit()
            conn.close()
            
            # Create updater and mock dependencies
            updater = DatabaseUpdater(temp_db)
            
            # Mock PDF processor
            mock_pdf = Mock()
            mock_pdf.extract_text_from_pdf.return_value = {
                'pages': [{'page_number': 1, 'text': statement_text}]
            }
            updater.pdf_processor = mock_pdf
            
            # Mock MP identifier
            mock_mp = Mock()
            mock_statements = [
                Statement(mp_name, statement_text, 0, len(statement_text), page_number=1)
            ]
            mock_mp.extract_statements_from_pages.return_value = mock_statements
            mock_mp.get_unique_mp_names.return_value = [mp_name]
            updater.mp_identifier = mock_mp
            
            # Mock bill extractor
            mock_bill = Mock()
            mock_bill.extract_bill_references.return_value = []
            updater.bill_extractor = mock_bill
            
            # Act: Process the PDF (which should link it to a session)
            result = updater.process_hansard_pdf(
                pdf_path=f"/path/to/{Path(pdf_url).name}",
                pdf_url=pdf_url,
                date=date,
                title=title,
                skip_if_processed=False
            )
            
            # Assert: Verify the processing was successful
            assert result['status'] == 'success', f"Processing failed: {result}"
            
            # Assert: Verify session was created
            session_id = result.get('session_id')
            assert session_id is not None, "Session ID should be returned"
            assert session_id > 0, "Session ID should be positive"
            
            # Assert: Verify downloaded_pdfs table was updated with session_id
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT session_id FROM downloaded_pdfs 
                WHERE original_url = ?
            """, (pdf_url,))
            
            row = cursor.fetchone()
            conn.close()
            
            # Property verification: session_id in downloaded_pdfs should match the created session
            assert row is not None, f"Downloaded PDF record not found for URL: {pdf_url}"
            assert row[0] is not None, "session_id should not be NULL after processing"
            assert row[0] == session_id, (
                f"session_id in downloaded_pdfs ({row[0]}) should match "
                f"the session created during processing ({session_id})"
            )
    
    @given(
        pdf_url=st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=10,
            max_size=50
        ).map(lambda s: f"http://example.com/{s}.pdf"),
        date=st.dates().map(lambda d: d.strftime('%Y-%m-%d')),
        title=st.text(min_size=5, max_size=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_session_linking_without_existing_pdf_record(
        self,
        pdf_url,
        date,
        title
    ):
        """
        Feature: end-to-end-workflow-validation, Property 7:
        Session linking should handle cases where no downloaded_pdfs record exists.
        
        This tests the edge case where a PDF is processed but was never tracked
        in the downloaded_pdfs table (e.g., manually added PDF).
        
        **Validates: Requirements 6.4**
        """
        with create_temp_db() as temp_db:
            # Create updater and mock dependencies
            updater = DatabaseUpdater(temp_db)
            
            # Mock PDF processor
            mock_pdf = Mock()
            mock_pdf.extract_text_from_pdf.return_value = {
                'pages': [{'page_number': 1, 'text': 'Test statement'}]
            }
            updater.pdf_processor = mock_pdf
            
            # Mock MP identifier
            mock_mp = Mock()
            mock_statements = [
                Statement("Test MP", "Test statement", 0, 100, page_number=1)
            ]
            mock_mp.extract_statements_from_pages.return_value = mock_statements
            mock_mp.get_unique_mp_names.return_value = ["Test MP"]
            updater.mp_identifier = mock_mp
            
            # Mock bill extractor
            mock_bill = Mock()
            mock_bill.extract_bill_references.return_value = []
            updater.bill_extractor = mock_bill
            
            # Act: Process PDF without existing downloaded_pdfs record
            result = updater.process_hansard_pdf(
                pdf_path=f"/path/to/{Path(pdf_url).name}",
                pdf_url=pdf_url,
                date=date,
                title=title,
                skip_if_processed=False
            )
            
            # Assert: Processing should succeed even without downloaded_pdfs record
            assert result['status'] == 'success', f"Processing failed: {result}"
            
            # Assert: Session should be created
            session_id = result.get('session_id')
            assert session_id is not None
            assert session_id > 0
            
            # Assert: Verify no error occurred during linking attempt
            # (The _link_pdf_to_session method should handle missing records gracefully)
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT session_id FROM downloaded_pdfs 
                WHERE original_url = ?
            """, (pdf_url,))
            
            row = cursor.fetchone()
            conn.close()
            
            # Property: If no record exists, linking should not create one
            # (it only updates existing records)
            assert row is None, (
                "No downloaded_pdfs record should exist if one wasn't created beforehand"
            )
