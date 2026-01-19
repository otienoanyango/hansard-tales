#!/usr/bin/env python3
"""
Initialize parliamentary term data for Hansard Tales.

This script populates the database with parliamentary term information:
- 13th Parliament (2022-2027): Current term
- 12th Parliament (2017-2022): Optional historical data

Usage:
    python scripts/init_parliament_data.py [--db-path PATH] [--include-historical]
"""

import argparse
import sqlite3
import sys
from pathlib import Path
from datetime import datetime


def insert_parliamentary_term(
    conn: sqlite3.Connection,
    term_number: int,
    start_date: str,
    end_date: str,
    is_current: bool = False
) -> int:
    """
    Insert a parliamentary term into the database.
    
    Args:
        conn: Database connection
        term_number: Parliamentary term number (e.g., 13)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        is_current: Whether this is the current term
        
    Returns:
        ID of the inserted term
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO parliamentary_terms 
            (term_number, start_date, end_date, is_current)
            VALUES (?, ?, ?, ?)
        """, (term_number, start_date, end_date, is_current))
        
        conn.commit()
        term_id = cursor.lastrowid
        
        status = "CURRENT" if is_current else "HISTORICAL"
        print(f"✓ Inserted {term_number}th Parliament ({start_date} to {end_date}) [{status}]")
        
        return term_id
        
    except sqlite3.IntegrityError as e:
        print(f"✗ Term {term_number} already exists: {e}")
        # Get existing term ID
        cursor.execute(
            "SELECT id FROM parliamentary_terms WHERE term_number = ?",
            (term_number,)
        )
        result = cursor.fetchone()
        return result[0] if result else None


def verify_parliamentary_terms(conn: sqlite3.Connection) -> bool:
    """
    Verify that parliamentary terms were inserted correctly.
    
    Args:
        conn: Database connection
        
    Returns:
        True if verification passes, False otherwise
    """
    cursor = conn.cursor()
    
    # Check that at least one term exists
    cursor.execute("SELECT COUNT(*) FROM parliamentary_terms")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("✗ No parliamentary terms found")
        return False
    
    # Check that exactly one term is marked as current
    cursor.execute("SELECT COUNT(*) FROM parliamentary_terms WHERE is_current = 1")
    current_count = cursor.fetchone()[0]
    
    if current_count == 0:
        print("✗ No current parliamentary term found")
        return False
    
    if current_count > 1:
        print("✗ Multiple terms marked as current")
        return False
    
    # Get current term details
    cursor.execute("""
        SELECT term_number, start_date, end_date 
        FROM parliamentary_terms 
        WHERE is_current = 1
    """)
    current_term = cursor.fetchone()
    
    print(f"\n✓ Current term: {current_term[0]}th Parliament")
    print(f"  Start: {current_term[1]}")
    print(f"  End: {current_term[2]}")
    
    # List all terms
    cursor.execute("""
        SELECT term_number, start_date, end_date, is_current
        FROM parliamentary_terms
        ORDER BY term_number DESC
    """)
    
    print(f"\n✓ All parliamentary terms in database:")
    for row in cursor.fetchall():
        status = "CURRENT" if row[3] else "HISTORICAL"
        print(f"  - {row[0]}th Parliament: {row[1]} to {row[2]} [{status}]")
    
    return True


def initialize_parliament_data(
    db_path: str = "data/hansard.db",
    include_historical: bool = False
) -> bool:
    """
    Initialize parliamentary term data.
    
    Args:
        db_path: Path to the SQLite database file
        include_historical: Whether to include 12th Parliament data
        
    Returns:
        True if successful, False otherwise
    """
    # Check if database exists
    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        print("  Run 'python scripts/init_db.py' first to create the database")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        print(f"Connected to database: {db_path}\n")
        
        # Insert 13th Parliament (current term)
        insert_parliamentary_term(
            conn,
            term_number=13,
            start_date="2022-09-08",
            end_date="2027-09-07",
            is_current=True
        )
        
        # Optionally insert 12th Parliament (historical)
        if include_historical:
            insert_parliamentary_term(
                conn,
                term_number=12,
                start_date="2017-08-31",
                end_date="2022-09-07",
                is_current=False
            )
        
        # Verify data
        if not verify_parliamentary_terms(conn):
            print("\n✗ Verification failed")
            return False
        
        conn.close()
        print(f"\n✓ Parliamentary term data initialized successfully")
        return True
        
    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize parliamentary term data for Hansard Tales"
    )
    parser.add_argument(
        "--db-path",
        default="data/hansard.db",
        help="Path to SQLite database file (default: data/hansard.db)"
    )
    parser.add_argument(
        "--include-historical",
        action="store_true",
        help="Include 12th Parliament (2017-2022) historical data"
    )
    
    args = parser.parse_args()
    
    # Initialize parliament data
    success = initialize_parliament_data(
        args.db_path,
        args.include_historical
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
