#!/usr/bin/env python3
"""
Generate search index JSON for client-side search with Fuse.js.

This script queries the database for current MPs with their performance data
and historical terms, then formats the data for Fuse.js fuzzy search.

The search index includes:
- MP name, constituency, party
- Current term metadata (term number, performance stats)
- Historical terms data
- Keywords for enhanced search

Output: output/data/mp-search-index.json
"""
import json
import sqlite3
import sys
from pathlib import Path


def get_db_connection(db_path):
    """Get database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def generate_keywords(mp_data):
    """
    Generate search keywords from MP data.
    
    Keywords include:
    - Name components
    - Constituency
    - Party
    - County
    
    Args:
        mp_data: Dictionary with MP information
        
    Returns:
        List of keyword strings
    """
    keywords = []
    
    # Add name components
    if mp_data.get('name'):
        keywords.extend(mp_data['name'].split())
    
    # Add constituency
    if mp_data.get('constituency'):
        keywords.append(mp_data['constituency'])
        keywords.extend(mp_data['constituency'].split())
    
    # Add party
    if mp_data.get('party'):
        keywords.append(mp_data['party'])
    
    # Add county if available
    if mp_data.get('county'):
        keywords.append(mp_data['county'])
    
    # Remove duplicates and empty strings
    keywords = list(set(k.strip() for k in keywords if k and k.strip()))
    
    return keywords


def generate_search_index(db_path=None, output_dir=None):
    """
    Generate search index JSON file.
    
    Args:
        db_path: Path to SQLite database (default: data/hansard.db)
        output_dir: Output directory (default: output/)
    """
    # Setup paths
    base_dir = Path(__file__).parent.parent
    
    if db_path is None:
        db_path = base_dir / 'data' / 'hansard.db'
    else:
        db_path = Path(db_path)
    
    if output_dir is None:
        output_dir = base_dir / 'output'
    else:
        output_dir = Path(output_dir)
    
    # Verify database exists
    if not db_path.exists():
        print(f'Error: Database not found at {db_path}')
        sys.exit(1)
    
    # Connect to database
    conn = get_db_connection(str(db_path))
    
    # Get current MPs with performance data
    print('Querying current MPs...')
    current_mps = conn.execute('''
        SELECT 
            m.id,
            m.name,
            mt.constituency,
            mt.party,
            m.photo_url,
            pt.term_number as current_term,
            COUNT(DISTINCT s.id) as statement_count,
            COUNT(DISTINCT s.session_id) as sessions_attended,
            COUNT(DISTINCT CASE WHEN s.bill_reference IS NOT NULL THEN s.bill_reference END) as bills_mentioned
        FROM mps m
        JOIN mp_terms mt ON m.id = mt.mp_id
        JOIN parliamentary_terms pt ON mt.term_id = pt.id
        LEFT JOIN hansard_sessions hs ON hs.term_id = pt.id
        LEFT JOIN statements s ON s.mp_id = m.id AND s.session_id = hs.id
        WHERE mt.is_current = 1
        GROUP BY m.id
        ORDER BY m.name ASC
    ''').fetchall()
    
    print(f'Found {len(current_mps)} current MPs')
    
    # Build search index
    search_index = []
    
    for mp_row in current_mps:
        mp_id = mp_row['id']
        
        # Get historical terms for this MP
        historical_terms = conn.execute('''
            SELECT 
                pt.term_number,
                mt.constituency,
                mt.party,
                mt.elected_date,
                mt.left_date
            FROM mp_terms mt
            JOIN parliamentary_terms pt ON mt.term_id = pt.id
            WHERE mt.mp_id = ?
            ORDER BY pt.term_number DESC
        ''', (mp_id,)).fetchall()
        
        # Format MP data for search
        mp_data = {
            'id': mp_row['id'],
            'name': mp_row['name'],
            'constituency': mp_row['constituency'],
            'party': mp_row['party'],
            'photo_url': mp_row['photo_url'],
            'current_term': {
                'term_number': mp_row['current_term'],
                'statement_count': mp_row['statement_count'] if mp_row['statement_count'] else 0,
                'sessions_attended': mp_row['sessions_attended'] if mp_row['sessions_attended'] else 0,
                'bills_mentioned': mp_row['bills_mentioned'] if mp_row['bills_mentioned'] else 0
            },
            'historical_terms': [
                {
                    'term_number': term['term_number'],
                    'constituency': term['constituency'],
                    'party': term['party'],
                    'elected_date': term['elected_date'],
                    'left_date': term['left_date']
                }
                for term in historical_terms
            ]
        }
        
        # Generate keywords
        mp_data['keywords'] = generate_keywords(mp_data)
        
        search_index.append(mp_data)
    
    # Close database
    conn.close()
    
    # Create output directory
    data_dir = output_dir / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Write search index to JSON
    output_file = data_dir / 'mp-search-index.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(search_index, f, indent=2, ensure_ascii=False)
    
    print(f'\n✓ Search index generated successfully')
    print(f'  Output: {output_file}')
    print(f'  Total MPs: {len(search_index)}')
    print(f'  File size: {output_file.stat().st_size / 1024:.1f} KB')


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate search index JSON for client-side search'
    )
    parser.add_argument(
        '--db',
        help='Path to SQLite database (default: data/hansard.db)'
    )
    parser.add_argument(
        '--output',
        help='Output directory (default: output/)'
    )
    
    args = parser.parse_args()
    
    generate_search_index(db_path=args.db, output_dir=args.output)


if __name__ == '__main__':
    main()
