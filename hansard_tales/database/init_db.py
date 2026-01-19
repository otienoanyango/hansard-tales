#!/usr/bin/env python3
"""
Database initialization script for Hansard Tales.

This script creates the SQLite database schema including:
- parliamentary_terms: Parliamentary sessions (e.g., 13th Parliament 2022-2027)
- mps: Members of Parliament
- mp_terms: Junction table linking MPs to parliamentary terms
- hansard_sessions: Daily parliamentary sittings
- statements: Individual MP statements in sessions

Usage:
    python scripts/init_db.py [--db-path PATH]
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all database tables."""
    cursor = conn.cursor()
    
    # Parliamentary terms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parliamentary_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_number INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            is_current BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(term_number)
        )
    """)
    
    # MPs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            constituency TEXT NOT NULL,
            party TEXT,
            photo_url TEXT,
            first_elected_year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # MP terms junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mp_terms (
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
    """)
    
    # Hansard sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hansard_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_id INTEGER NOT NULL,
            date DATE NOT NULL,
            title TEXT,
            pdf_url TEXT NOT NULL,
            pdf_path TEXT,
            processed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (term_id) REFERENCES parliamentary_terms(id),
            UNIQUE(date, title)
        )
    """)
    
    # Statements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS statements (
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
    """)
    
    conn.commit()
    print("✓ Created all tables")


def create_indexes(conn: sqlite3.Connection) -> None:
    """Create database indexes for performance."""
    cursor = conn.cursor()
    
    indexes = [
        ("idx_statements_mp", "statements", "mp_id"),
        ("idx_statements_session", "statements", "session_id"),
        ("idx_statements_bill", "statements", "bill_reference"),
        ("idx_hansard_date", "hansard_sessions", "date"),
        ("idx_hansard_term", "hansard_sessions", "term_id"),
        ("idx_mp_terms_current", "mp_terms", "is_current"),
        ("idx_mp_terms_mp", "mp_terms", "mp_id"),
        ("idx_mp_terms_term", "mp_terms", "term_id"),
    ]
    
    for index_name, table_name, column_name in indexes:
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {index_name} 
            ON {table_name}({column_name})
        """)
    
    conn.commit()
    print("✓ Created all indexes")


def create_views(conn: sqlite3.Connection) -> None:
    """Create database views for common queries."""
    cursor = conn.cursor()
    
    # View for current MPs
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS current_mps AS
        SELECT 
            m.id,
            m.name,
            mt.constituency,
            mt.party,
            m.photo_url,
            m.first_elected_year,
            mt.elected_date as current_term_start,
            pt.term_number
        FROM mps m
        JOIN mp_terms mt ON m.id = mt.mp_id
        JOIN parliamentary_terms pt ON mt.term_id = pt.id
        WHERE mt.is_current = 1
    """)
    
    # View for MP performance in current term
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS mp_current_term_performance AS
        SELECT 
            m.id,
            m.name,
            mt.constituency,
            mt.party,
            pt.term_number,
            COUNT(DISTINCT s.id) as statement_count,
            COUNT(DISTINCT s.session_id) as sessions_attended,
            COUNT(DISTINCT s.bill_reference) as bills_mentioned,
            MAX(hs.date) as last_active_date,
            MIN(hs.date) as first_active_date
        FROM mps m
        JOIN mp_terms mt ON m.id = mt.mp_id
        JOIN parliamentary_terms pt ON mt.term_id = pt.id
        LEFT JOIN hansard_sessions hs ON hs.term_id = pt.id
        LEFT JOIN statements s ON s.mp_id = m.id AND s.session_id = hs.id
        WHERE mt.is_current = 1
        GROUP BY m.id
    """)
    
    # View for MP historical performance (all terms)
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS mp_historical_performance AS
        SELECT 
            m.id,
            m.name,
            pt.term_number,
            mt.constituency,
            mt.party,
            mt.elected_date,
            mt.left_date,
            COUNT(DISTINCT s.id) as statement_count,
            COUNT(DISTINCT s.session_id) as sessions_attended,
            COUNT(DISTINCT s.bill_reference) as bills_mentioned
        FROM mps m
        JOIN mp_terms mt ON m.id = mt.mp_id
        JOIN parliamentary_terms pt ON mt.term_id = pt.id
        LEFT JOIN hansard_sessions hs ON hs.term_id = pt.id
        LEFT JOIN statements s ON s.mp_id = m.id AND s.session_id = hs.id
        GROUP BY m.id, pt.term_number
    """)
    
    conn.commit()
    print("✓ Created all views")


def verify_schema(conn: sqlite3.Connection) -> bool:
    """Verify that all tables, indexes, and views were created."""
    cursor = conn.cursor()
    
    # Check tables
    expected_tables = [
        'parliamentary_terms', 'mps', 'mp_terms', 
        'hansard_sessions', 'statements'
    ]
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in expected_tables:
        if table not in tables:
            print(f"✗ Missing table: {table}")
            return False
    
    # Check views
    expected_views = [
        'current_mps', 'mp_current_term_performance', 
        'mp_historical_performance'
    ]
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = [row[0] for row in cursor.fetchall()]
    
    for view in expected_views:
        if view not in views:
            print(f"✗ Missing view: {view}")
            return False
    
    # Check indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cursor.fetchall()]
    
    expected_index_prefixes = ['idx_statements_', 'idx_hansard_', 'idx_mp_terms_']
    has_indexes = any(
        any(idx.startswith(prefix) for idx in indexes)
        for prefix in expected_index_prefixes
    )
    
    if not has_indexes:
        print("✗ Missing indexes")
        return False
    
    print("✓ Schema verification passed")
    return True


def initialize_database(db_path: str = "data/hansard.db") -> bool:
    """
    Initialize the database with schema.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        True if successful, False otherwise
    """
    # Ensure data directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        print(f"Connected to database: {db_path}")
        
        # Create schema
        create_tables(conn)
        create_indexes(conn)
        create_views(conn)
        
        # Verify schema
        if not verify_schema(conn):
            print("✗ Schema verification failed")
            return False
        
        conn.close()
        print(f"\n✓ Database initialized successfully: {db_path}")
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
        description="Initialize Hansard Tales database schema"
    )
    parser.add_argument(
        "--db-path",
        default="data/hansard.db",
        help="Path to SQLite database file (default: data/hansard.db)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of database (WARNING: deletes existing data)"
    )
    
    args = parser.parse_args()
    
    # Check if database exists
    if Path(args.db_path).exists() and not args.force:
        print(f"Database already exists: {args.db_path}")
        print("Use --force to recreate (WARNING: this will delete all data)")
        sys.exit(1)
    
    # Remove existing database if force flag is set
    if args.force and Path(args.db_path).exists():
        Path(args.db_path).unlink()
        print(f"Removed existing database: {args.db_path}")
    
    # Initialize database
    success = initialize_database(args.db_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
