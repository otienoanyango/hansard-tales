#!/usr/bin/env python3
"""
MP Data Import Script

Imports MP data from JSON files into the SQLite database.
Links MPs to their respective parliamentary terms via the mp_terms table.

Usage:
    python scripts/import_mps.py --file data/mps_13th_parliament.json
    python scripts/import_mps.py --file data/mps_12th_parliament.json --term-id 2
"""

import argparse
import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MPImporter:
    """Imports MP data from JSON into SQLite database"""
    
    def __init__(self, db_path: str = 'data/hansard.db'):
        """
        Initialize the importer.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to the database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        logger.info(f"Connected to database: {self.db_path}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def get_term_by_year(self, year: int) -> Optional[int]:
        """
        Get parliamentary term ID by start year.
        
        Args:
            year: Term start year (e.g., 2022, 2017)
            
        Returns:
            Term ID or None if not found
        """
        self.cursor.execute("""
            SELECT id FROM parliamentary_terms
            WHERE strftime('%Y', start_date) = ?
        """, (str(year),))
        
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_or_create_mp(self, mp_data: Dict) -> int:
        """
        Get existing MP or create new one.
        
        Args:
            mp_data: Dictionary with MP information
            
        Returns:
            MP ID
        """
        name = mp_data['name']
        
        # Try to find existing MP by name
        self.cursor.execute("""
            SELECT id FROM mps WHERE name = ?
        """, (name,))
        
        result = self.cursor.fetchone()
        
        if result:
            mp_id = result[0]
            logger.debug(f"Found existing MP: {name} (ID: {mp_id})")
            
            # Update photo URL if provided and not already set
            if mp_data.get('photo_url'):
                self.cursor.execute("""
                    UPDATE mps 
                    SET photo_url = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND (photo_url IS NULL OR photo_url = '')
                """, (mp_data['photo_url'], mp_id))
            
            return mp_id
        
        # Create new MP
        # Use placeholder for constituency if None (nominated MPs)
        constituency = mp_data.get('constituency') or 'Nominated'
        
        self.cursor.execute("""
            INSERT INTO mps (name, constituency, party, photo_url)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            constituency,
            mp_data.get('party'),
            mp_data.get('photo_url')
        ))
        
        mp_id = self.cursor.lastrowid
        logger.info(f"Created new MP: {name} (ID: {mp_id})")
        
        return mp_id
    
    def link_mp_to_term(
        self,
        mp_id: int,
        term_id: int,
        mp_data: Dict,
        is_current: bool = False
    ) -> bool:
        """
        Link MP to parliamentary term via mp_terms table.
        
        Args:
            mp_id: MP ID
            term_id: Parliamentary term ID
            mp_data: Dictionary with MP information
            is_current: Whether this is the current term
            
        Returns:
            True if link created, False if already exists
        """
        # Check if link already exists
        self.cursor.execute("""
            SELECT id FROM mp_terms
            WHERE mp_id = ? AND term_id = ?
        """, (mp_id, term_id))
        
        if self.cursor.fetchone():
            logger.debug(f"MP {mp_id} already linked to term {term_id}")
            return False
        
        # Determine elected date based on term
        # For 13th Parliament: 2022-09-08
        # For 12th Parliament: 2017-08-31
        self.cursor.execute("""
            SELECT start_date FROM parliamentary_terms WHERE id = ?
        """, (term_id,))
        
        term_start = self.cursor.fetchone()[0]
        
        # Create link
        # Use placeholder for constituency if None (nominated MPs)
        constituency = mp_data.get('constituency') or 'Nominated'
        
        self.cursor.execute("""
            INSERT INTO mp_terms (
                mp_id, term_id, constituency, party,
                elected_date, is_current
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            mp_id,
            term_id,
            constituency,
            mp_data.get('party'),
            term_start,  # Use term start date as elected date
            1 if is_current else 0
        ))
        
        logger.info(f"Linked MP {mp_id} to term {term_id}")
        return True
    
    def import_from_json(
        self,
        json_path: str,
        term_id: Optional[int] = None,
        is_current: bool = False
    ) -> Dict[str, int]:
        """
        Import MPs from JSON file.
        
        Args:
            json_path: Path to JSON file
            term_id: Parliamentary term ID (auto-detected if not provided)
            is_current: Whether this is the current term
            
        Returns:
            Dictionary with import statistics
        """
        # Load JSON data
        with open(json_path, 'r', encoding='utf-8') as f:
            mps_data = json.load(f)
        
        logger.info(f"Loaded {len(mps_data)} MPs from {json_path}")
        
        # Auto-detect term if not provided
        if term_id is None and mps_data:
            year = mps_data[0].get('term_start_year')
            if year:
                term_id = self.get_term_by_year(year)
                if not term_id:
                    raise ValueError(f"No parliamentary term found for year {year}")
                logger.info(f"Auto-detected term ID: {term_id} (year: {year})")
        
        if not term_id:
            raise ValueError("Term ID must be provided or auto-detectable from data")
        
        # Import statistics
        stats = {
            'total': len(mps_data),
            'new_mps': 0,
            'existing_mps': 0,
            'new_links': 0,
            'existing_links': 0,
            'errors': 0
        }
        
        # Import each MP
        for mp_data in mps_data:
            try:
                # Check if MP exists before creating
                name = mp_data['name']
                self.cursor.execute("SELECT id FROM mps WHERE name = ?", (name,))
                existing = self.cursor.fetchone()
                
                # Get or create MP
                mp_id = self.get_or_create_mp(mp_data)
                
                # Track if this is a new MP
                if existing:
                    stats['existing_mps'] += 1
                else:
                    stats['new_mps'] += 1
                
                # Link to term
                if self.link_mp_to_term(mp_id, term_id, mp_data, is_current):
                    stats['new_links'] += 1
                else:
                    stats['existing_links'] += 1
            
            except Exception as e:
                logger.error(f"Error importing MP {mp_data.get('name')}: {e}")
                stats['errors'] += 1
        
        # Commit changes
        self.conn.commit()
        logger.info("Import completed successfully")
        
        return stats
    
    def verify_import(self, term_id: int) -> Dict[str, int]:
        """
        Verify imported data.
        
        Args:
            term_id: Parliamentary term ID
            
        Returns:
            Dictionary with verification statistics
        """
        stats = {}
        
        # Count MPs linked to this term
        self.cursor.execute("""
            SELECT COUNT(*) FROM mp_terms WHERE term_id = ?
        """, (term_id,))
        stats['total_mps'] = self.cursor.fetchone()[0]
        
        # Count by status
        self.cursor.execute("""
            SELECT COUNT(*) FROM mp_terms
            WHERE term_id = ? AND constituency != 'Nominated'
        """, (term_id,))
        stats['elected'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("""
            SELECT COUNT(*) FROM mp_terms
            WHERE term_id = ? AND constituency = 'Nominated'
        """, (term_id,))
        stats['nominated'] = self.cursor.fetchone()[0]
        
        # Count by party (top 5)
        self.cursor.execute("""
            SELECT party, COUNT(*) as count
            FROM mp_terms
            WHERE term_id = ?
            GROUP BY party
            ORDER BY count DESC
            LIMIT 5
        """, (term_id,))
        stats['top_parties'] = dict(self.cursor.fetchall())
        
        return stats


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Import MP data from JSON into database'
    )
    parser.add_argument(
        '--file',
        type=str,
        required=True,
        help='Path to JSON file with MP data'
    )
    parser.add_argument(
        '--db',
        type=str,
        default='data/hansard.db',
        help='Path to SQLite database (default: data/hansard.db)'
    )
    parser.add_argument(
        '--term-id',
        type=int,
        help='Parliamentary term ID (auto-detected if not provided)'
    )
    parser.add_argument(
        '--current',
        action='store_true',
        help='Mark this as the current parliamentary term'
    )
    
    args = parser.parse_args()
    
    # Verify file exists
    if not Path(args.file).exists():
        logger.error(f"File not found: {args.file}")
        return 1
    
    # Verify database exists
    if not Path(args.db).exists():
        logger.error(f"Database not found: {args.db}")
        logger.error("Run 'python scripts/init_db.py' first")
        return 1
    
    # Create importer
    importer = MPImporter(db_path=args.db)
    
    try:
        # Connect to database
        importer.connect()
        
        # Import data
        logger.info(f"Importing MPs from {args.file}")
        stats = importer.import_from_json(
            json_path=args.file,
            term_id=args.term_id,
            is_current=args.current
        )
        
        # Print import statistics
        print(f"\n{'='*60}")
        print(f"Import Summary")
        print(f"{'='*60}")
        print(f"Total MPs in file: {stats['total']}")
        print(f"New MPs created: {stats['new_mps']}")
        print(f"Existing MPs updated: {stats['existing_mps']}")
        print(f"New term links created: {stats['new_links']}")
        print(f"Existing term links: {stats['existing_links']}")
        print(f"Errors: {stats['errors']}")
        
        # Verify import
        if args.term_id:
            term_id = args.term_id
        else:
            # Get term ID from first MP
            with open(args.file, 'r') as f:
                data = json.load(f)
                if data:
                    year = data[0].get('term_start_year')
                    term_id = importer.get_term_by_year(year)
        
        if term_id:
            verify_stats = importer.verify_import(term_id)
            
            print(f"\n{'='*60}")
            print(f"Verification Results")
            print(f"{'='*60}")
            print(f"Total MPs in term: {verify_stats['total_mps']}")
            print(f"Elected: {verify_stats['elected']}")
            print(f"Nominated: {verify_stats['nominated']}")
            print(f"\nTop 5 parties:")
            for party, count in verify_stats['top_parties'].items():
                print(f"  {party}: {count}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return 1
    
    finally:
        importer.close()


if __name__ == '__main__':
    exit(main())
