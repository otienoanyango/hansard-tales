#!/usr/bin/env python3
"""
Database update logic for Hansard processing.

This module handles updating the SQLite database with extracted
Hansard data including MPs, sessions, and statements.

Usage:
    from hansard_tales.database.db_updater import DatabaseUpdater
    
    updater = DatabaseUpdater('data/hansard.db')
    updater.process_hansard_pdf(pdf_path, pdf_url, date)
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from hansard_tales.processors.pdf_processor import PDFProcessor
from hansard_tales.processors.mp_identifier import MPIdentifier, Statement
from hansard_tales.processors.bill_extractor import BillExtractor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseUpdater:
    """Handles database updates for Hansard processing."""
    
    def __init__(self, db_path: str):
        """
        Initialize the database updater.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.pdf_processor = PDFProcessor()
        self.mp_identifier = MPIdentifier()
        self.bill_extractor = BillExtractor()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_or_create_mp(
        self,
        cursor: sqlite3.Cursor,
        mp_name: str,
        constituency: str = "Unknown",
        party: str = None
    ) -> int:
        """
        Get existing MP or create new one.
        
        Args:
            cursor: Database cursor
            mp_name: MP name (normalized)
            constituency: MP constituency
            party: MP party affiliation
            
        Returns:
            MP ID
        """
        # Try to find existing MP by name
        cursor.execute(
            "SELECT id FROM mps WHERE name = ?",
            (mp_name,)
        )
        row = cursor.fetchone()
        
        if row:
            return row['id']
        
        # Create new MP
        cursor.execute("""
            INSERT INTO mps (name, constituency, party)
            VALUES (?, ?, ?)
        """, (mp_name, constituency, party))
        
        mp_id = cursor.lastrowid
        logger.info(f"Created new MP: {mp_name} (ID: {mp_id})")
        
        return mp_id
    
    def link_mp_to_current_term(
        self,
        cursor: sqlite3.Cursor,
        mp_id: int,
        constituency: str = "Unknown",
        party: str = None
    ) -> None:
        """
        Link MP to current parliamentary term.
        
        Args:
            cursor: Database cursor
            mp_id: MP ID
            constituency: MP constituency
            party: MP party affiliation
        """
        # Get current term
        cursor.execute(
            "SELECT id FROM parliamentary_terms WHERE is_current = 1"
        )
        term_row = cursor.fetchone()
        
        if not term_row:
            logger.warning("No current parliamentary term found")
            return
        
        term_id = term_row['id']
        
        # Check if link already exists
        cursor.execute("""
            SELECT id FROM mp_terms 
            WHERE mp_id = ? AND term_id = ?
        """, (mp_id, term_id))
        
        if cursor.fetchone():
            return  # Link already exists
        
        # Create link
        cursor.execute("""
            INSERT INTO mp_terms (mp_id, term_id, constituency, party, is_current)
            VALUES (?, ?, ?, ?, 1)
        """, (mp_id, term_id, constituency, party))
        
        logger.debug(f"Linked MP {mp_id} to term {term_id}")
    
    def get_or_create_session(
        self,
        cursor: sqlite3.Cursor,
        date: str,
        title: str,
        pdf_url: str,
        pdf_path: str = None
    ) -> int:
        """
        Get existing session or create new one.
        
        Args:
            cursor: Database cursor
            date: Session date (YYYY-MM-DD)
            title: Session title
            pdf_url: URL to PDF
            pdf_path: Local path to PDF
            
        Returns:
            Session ID
        """
        # Get current term
        cursor.execute(
            "SELECT id FROM parliamentary_terms WHERE is_current = 1"
        )
        term_row = cursor.fetchone()
        
        if not term_row:
            raise ValueError("No current parliamentary term found")
        
        term_id = term_row['id']
        
        # Try to find existing session
        cursor.execute("""
            SELECT id FROM hansard_sessions 
            WHERE date = ? AND title = ?
        """, (date, title))
        
        row = cursor.fetchone()
        
        if row:
            return row['id']
        
        # Create new session
        cursor.execute("""
            INSERT INTO hansard_sessions (term_id, date, title, pdf_url, pdf_path, processed)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (term_id, date, title, pdf_url, pdf_path))
        
        session_id = cursor.lastrowid
        logger.info(f"Created new session: {date} - {title} (ID: {session_id})")
        
        return session_id
    
    def insert_statement(
        self,
        cursor: sqlite3.Cursor,
        mp_id: int,
        session_id: int,
        statement: Statement,
        bill_references: List[str] = None
    ) -> int:
        """
        Insert a statement into the database.
        
        Args:
            cursor: Database cursor
            mp_id: MP ID
            session_id: Session ID
            statement: Statement object
            bill_references: List of bill reference strings
            
        Returns:
            Statement ID
        """
        # Format bill references
        bill_ref_str = None
        if bill_references:
            bill_ref_str = ", ".join(bill_references)
        
        # Insert statement
        cursor.execute("""
            INSERT INTO statements (mp_id, session_id, text, page_number, bill_reference)
            VALUES (?, ?, ?, ?, ?)
        """, (mp_id, session_id, statement.text, statement.page_number, bill_ref_str))
        
        statement_id = cursor.lastrowid
        logger.debug(f"Inserted statement for MP {mp_id}: {len(statement.text)} chars")
        
        return statement_id
    
    def check_duplicate_session(
        self,
        cursor: sqlite3.Cursor,
        date: str,
        title: str
    ) -> bool:
        """
        Check if session already exists and is processed.
        
        Args:
            cursor: Database cursor
            date: Session date
            title: Session title
            
        Returns:
            True if session exists and is processed
        """
        cursor.execute("""
            SELECT processed FROM hansard_sessions 
            WHERE date = ? AND title = ?
        """, (date, title))
        
        row = cursor.fetchone()
        
        if row and row['processed']:
            return True
        
        return False
    
    def mark_session_processed(
        self,
        cursor: sqlite3.Cursor,
        session_id: int
    ) -> None:
        """
        Mark session as processed.
        
        Args:
            cursor: Database cursor
            session_id: Session ID
        """
        cursor.execute("""
            UPDATE hansard_sessions 
            SET processed = 1 
            WHERE id = ?
        """, (session_id,))
    
    def process_hansard_pdf(
        self,
        pdf_path: str,
        pdf_url: str,
        date: str,
        title: str = None,
        skip_if_processed: bool = True
    ) -> Dict:
        """
        Process a Hansard PDF and update database.
        
        Args:
            pdf_path: Path to PDF file
            pdf_url: URL to PDF
            date: Session date (YYYY-MM-DD)
            title: Session title (optional, derived from filename if not provided)
            skip_if_processed: Skip if session already processed
            
        Returns:
            Dictionary with processing statistics
        """
        # Derive title from filename if not provided
        if not title:
            title = Path(pdf_path).stem
        
        logger.info(f"Processing Hansard: {date} - {title}")
        
        # Start transaction
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check for duplicates
            if skip_if_processed and self.check_duplicate_session(cursor, date, title):
                logger.info(f"Session already processed: {date} - {title}")
                return {
                    'status': 'skipped',
                    'reason': 'already_processed'
                }
            
            # Extract text from PDF
            logger.info("Extracting text from PDF...")
            extracted_data = self.pdf_processor.extract_text_from_pdf(pdf_path)
            
            if not extracted_data:
                logger.error("Failed to extract text from PDF")
                return {
                    'status': 'error',
                    'reason': 'pdf_extraction_failed'
                }
            
            # Extract statements
            logger.info("Identifying MPs and extracting statements...")
            statements = self.mp_identifier.extract_statements_from_pages(
                extracted_data['pages']
            )
            
            if not statements:
                logger.warning("No statements found in PDF")
                return {
                    'status': 'warning',
                    'reason': 'no_statements_found'
                }
            
            # Create or get session
            session_id = self.get_or_create_session(
                cursor, date, title, pdf_url, pdf_path
            )
            
            # Process each statement
            mp_count = 0
            statement_count = 0
            bill_count = 0
            
            for statement in statements:
                # Get or create MP
                mp_id = self.get_or_create_mp(cursor, statement.mp_name)
                
                # Link MP to current term
                self.link_mp_to_current_term(cursor, mp_id)
                
                # Extract bill references from statement
                bills = self.bill_extractor.extract_bill_references(statement.text)
                bill_refs = [self.bill_extractor.format_bill_reference(b) for b in bills]
                
                if bill_refs:
                    bill_count += len(bill_refs)
                
                # Insert statement
                self.insert_statement(
                    cursor, mp_id, session_id, statement, bill_refs
                )
                
                statement_count += 1
            
            # Mark session as processed
            self.mark_session_processed(cursor, session_id)
            
            # Commit transaction
            conn.commit()
            
            # Get unique MP count
            unique_mps = len(self.mp_identifier.get_unique_mp_names(statements))
            
            logger.info(f"✓ Processed {statement_count} statements from {unique_mps} MPs")
            if bill_count > 0:
                logger.info(f"✓ Extracted {bill_count} bill references")
            
            return {
                'status': 'success',
                'session_id': session_id,
                'statements': statement_count,
                'unique_mps': unique_mps,
                'bills': bill_count
            }
        
        except Exception as e:
            conn.rollback()
            logger.error(f"Error processing Hansard: {e}")
            return {
                'status': 'error',
                'reason': str(e)
            }
        
        finally:
            conn.close()
    
    def get_session_statistics(self, session_id: int) -> Dict:
        """
        Get statistics for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary with statistics
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get session info
            cursor.execute("""
                SELECT date, title, processed 
                FROM hansard_sessions 
                WHERE id = ?
            """, (session_id,))
            
            session = cursor.fetchone()
            
            if not session:
                return {'error': 'Session not found'}
            
            # Get statement count
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM statements 
                WHERE session_id = ?
            """, (session_id,))
            
            statement_count = cursor.fetchone()['count']
            
            # Get unique MP count
            cursor.execute("""
                SELECT COUNT(DISTINCT mp_id) as count 
                FROM statements 
                WHERE session_id = ?
            """, (session_id,))
            
            mp_count = cursor.fetchone()['count']
            
            # Get bill reference count
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM statements 
                WHERE session_id = ? AND bill_reference IS NOT NULL
            """, (session_id,))
            
            bill_count = cursor.fetchone()['count']
            
            return {
                'session_id': session_id,
                'date': session['date'],
                'title': session['title'],
                'processed': bool(session['processed']),
                'statements': statement_count,
                'unique_mps': mp_count,
                'statements_with_bills': bill_count
            }
        
        finally:
            conn.close()


def main():
    """Main entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Process Hansard PDF and update database"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to Hansard PDF file"
    )
    parser.add_argument(
        "--db-path",
        default="data/hansard.db",
        help="Path to database (default: data/hansard.db)"
    )
    parser.add_argument(
        "--pdf-url",
        required=True,
        help="URL to PDF file"
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Session date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--title",
        help="Session title (optional, derived from filename if not provided)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Process even if session already exists"
    )
    
    args = parser.parse_args()
    
    # Initialize updater
    updater = DatabaseUpdater(args.db_path)
    
    # Process PDF
    result = updater.process_hansard_pdf(
        args.pdf_path,
        args.pdf_url,
        args.date,
        args.title,
        skip_if_processed=not args.force
    )
    
    # Print results
    print("\n" + "="*50)
    print("PROCESSING RESULTS")
    print("="*50)
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"Session ID: {result['session_id']}")
        print(f"Statements: {result['statements']}")
        print(f"Unique MPs: {result['unique_mps']}")
        print(f"Bill references: {result['bills']}")
        
        # Get detailed statistics
        stats = updater.get_session_statistics(result['session_id'])
        print(f"\nSession: {stats['date']} - {stats['title']}")
        print(f"Processed: {stats['processed']}")
    
    elif result['status'] == 'skipped':
        print(f"Reason: {result['reason']}")
    
    elif result['status'] == 'error':
        print(f"Error: {result['reason']}")
        return 1
    
    print("="*50)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
