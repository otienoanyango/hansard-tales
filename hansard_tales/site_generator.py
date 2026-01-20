#!/usr/bin/env python3
"""
Generate complete static HTML site from Jinja2 templates and database.
This script generates all MP profiles, party pages, and other pages for deployment.
"""
import os
import sys
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape


def get_db_connection(db_path):
    """Get database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def url_for(endpoint, **kwargs):
    """Mock Flask's url_for for static site generation."""
    if endpoint == 'static':
        filename = kwargs.get('filename', '')
        return f'/static/{filename}'
    elif endpoint == 'index':
        return '/index.html'
    elif endpoint == 'mps_list':
        return '/mps/index.html'
    elif endpoint == 'mp_profile':
        mp_id = kwargs.get('mp_id')
        return f'/mp/{mp_id}/index.html'
    elif endpoint == 'parties':
        return '/parties/index.html'
    elif endpoint == 'party_detail':
        party_slug = kwargs.get('party_slug')
        return f'/party/{party_slug}/index.html'
    elif endpoint == 'about':
        return '/about.html'
    elif endpoint == 'disclaimer':
        return '/disclaimer.html'
    elif endpoint == 'privacy':
        return '/privacy.html'
    else:
        return f'/{endpoint}.html'


def get_logo_filename(party_name):
    """
    Generate logo filename from party name, handling special cases.
    Normalizes party names to match generated logo files.
    """
    normalized = party_name.strip()
    
    # Handle special cases
    if normalized in ['FORD - K', 'FORD-K']:
        return 'FORD-K.svg'
    elif normalized in ['IND', 'IND.']:
        return 'IND.svg'
    
    # Default: remove spaces and periods
    return normalized.replace(' ', '-').replace('.', '') + '.svg'


def generate_static_site(db_path=None, output_dir=None):
    """Generate complete static HTML site."""
    # Setup paths
    base_dir = Path(__file__).parent.parent
    template_dir = base_dir / 'templates'
    
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
    
    # Clean and create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    
    # Copy static files
    static_src = base_dir / 'static'
    static_dst = output_dir / 'static'
    if static_src.exists():
        shutil.copytree(static_src, static_dst)
        print(f'Copied static files to {static_dst}')
    
    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # Add global functions and variables
    env.globals['url_for'] = url_for
    env.globals['current_year'] = datetime.now().year
    env.globals['last_updated'] = datetime.now().strftime('%B %d, %Y')
    
    # Connect to database
    conn = get_db_connection(str(db_path))
    
    # Generate homepage
    print('\nGenerating homepage...')
    template = env.get_template('pages/homepage.html')
    html = template.render(active_page='home')
    (output_dir / 'index.html').write_text(html)
    print('✓ Generated index.html')
    
    # Generate MPs listing page
    print('\nGenerating MPs listing page...')
    generate_mps_listing(conn, env, output_dir)
    
    # Generate individual MP profile pages
    print('\nGenerating MP profile pages...')
    generate_mp_profiles(conn, env, output_dir)
    
    # Generate parties listing page
    print('\nGenerating parties listing page...')
    generate_parties_listing(conn, env, output_dir)
    
    # Generate individual party pages
    print('\nGenerating party detail pages...')
    generate_party_pages(conn, env, output_dir)
    
    # Generate placeholder pages
    print('\nGenerating placeholder pages...')
    generate_placeholder_pages(env, output_dir)
    
    # Create .nojekyll file
    (output_dir / '.nojekyll').touch()
    
    # Close database
    conn.close()
    
    # Print summary
    print(f'\n{"="*60}')
    print(f'Static site generated successfully!')
    print(f'Output directory: {output_dir}')
    print(f'Total files: {len(list(output_dir.rglob("*")))}')
    print(f'{"="*60}')


def generate_mps_listing(conn, env, output_dir):
    """Generate MPs listing page."""
    # Get all current MPs with performance data
    mps = conn.execute('''
        SELECT 
            m.id,
            m.name,
            mt.constituency,
            mt.party,
            m.photo_url,
            COUNT(DISTINCT s.id) as statement_count,
            COUNT(DISTINCT s.session_id) as sessions_attended
        FROM mps m
        JOIN mp_terms mt ON m.id = mt.mp_id
        LEFT JOIN statements s ON s.mp_id = m.id
        LEFT JOIN hansard_sessions hs ON s.session_id = hs.id
        LEFT JOIN parliamentary_terms pt ON hs.term_id = pt.id AND pt.is_current = 1
        WHERE mt.is_current = 1
        GROUP BY m.id
        ORDER BY statement_count DESC, m.name ASC
    ''').fetchall()
    
    # Get party counts for filter dropdown
    parties = conn.execute('''
        SELECT 
            mt.party as name,
            COUNT(DISTINCT mt.mp_id) as count
        FROM mp_terms mt
        WHERE mt.is_current = 1 AND mt.party IS NOT NULL AND mt.party != ''
        GROUP BY mt.party
        ORDER BY count DESC, mt.party ASC
    ''').fetchall()
    
    # Create mps directory
    mps_dir = output_dir / 'mps'
    mps_dir.mkdir(parents=True, exist_ok=True)
    
    # Render template
    template = env.get_template('pages/mps_list.html')
    html = template.render(
        mps=mps,
        parties=parties,
        total_mps=len(mps),
        active_page='mps'
    )
    
    # Write to file
    (mps_dir / 'index.html').write_text(html)
    print(f'✓ Generated mps/index.html ({len(mps)} MPs)')


def generate_mp_profiles(conn, env, output_dir):
    """Generate individual MP profile pages."""
    # Get all current MPs
    mps = conn.execute('''
        SELECT m.id, m.name
        FROM mps m
        JOIN mp_terms mt ON m.id = mt.mp_id
        WHERE mt.is_current = 1
        ORDER BY m.name ASC
    ''').fetchall()
    
    # Get current term
    current_term = conn.execute('''
        SELECT * FROM parliamentary_terms WHERE is_current = 1
    ''').fetchone()
    
    if not current_term:
        print('Warning: No current parliamentary term found')
        return
    
    template = env.get_template('pages/mp_profile.html')
    
    for mp_row in mps:
        mp_id = mp_row['id']
        
        # Get MP basic info
        mp = conn.execute('''
            SELECT m.*, mt.constituency, mt.party, mt.elected_date
            FROM mps m
            JOIN mp_terms mt ON m.id = mt.mp_id
            WHERE m.id = ? AND mt.is_current = 1
        ''', (mp_id,)).fetchone()
        
        if not mp:
            continue
        
        # Get current term performance
        performance = conn.execute('''
            SELECT 
                COUNT(DISTINCT s.id) as statement_count,
                COUNT(DISTINCT s.session_id) as sessions_attended,
                COUNT(DISTINCT CASE WHEN s.bill_reference IS NOT NULL THEN s.bill_reference END) as bills_mentioned,
                MAX(hs.date) as last_active_date
            FROM statements s
            JOIN hansard_sessions hs ON s.session_id = hs.id
            WHERE s.mp_id = ? AND hs.term_id = ?
        ''', (mp_id, current_term['id'])).fetchone()
        
        # Get historical terms
        historical_terms = conn.execute('''
            SELECT 
                pt.term_number,
                mt.constituency,
                mt.party,
                mt.elected_date,
                mt.left_date,
                mt.is_current,
                COUNT(DISTINCT s.id) as statement_count,
                COUNT(DISTINCT s.session_id) as sessions_attended
            FROM mp_terms mt
            JOIN parliamentary_terms pt ON mt.term_id = pt.id
            LEFT JOIN hansard_sessions hs ON hs.term_id = pt.id
            LEFT JOIN statements s ON s.mp_id = mt.mp_id AND s.session_id = hs.id
            WHERE mt.mp_id = ?
            GROUP BY pt.term_number
            ORDER BY pt.term_number DESC
        ''', (mp_id,)).fetchall()
        
        # Get recent statements (limit to 20)
        statements = conn.execute('''
            SELECT 
                s.text,
                s.page_number,
                s.bill_reference,
                hs.date,
                hs.pdf_url as hansard_url,
                pt.term_number
            FROM statements s
            JOIN hansard_sessions hs ON s.session_id = hs.id
            JOIN parliamentary_terms pt ON hs.term_id = pt.id
            WHERE s.mp_id = ?
            ORDER BY hs.date DESC
            LIMIT 20
        ''', (mp_id,)).fetchall()
        
        # Render template
        html = template.render(
            mp=mp,
            current_term=current_term,
            performance=performance,
            historical_terms=historical_terms,
            statements=statements,
            active_page='mps'
        )
        
        # Create MP directory and write file
        mp_dir = output_dir / 'mp' / str(mp_id)
        mp_dir.mkdir(parents=True, exist_ok=True)
        (mp_dir / 'index.html').write_text(html)
    
    print(f'✓ Generated {len(mps)} MP profile pages')


def generate_parties_listing(conn, env, output_dir):
    """Generate parties listing page."""
    # Get all parties with MP counts and statistics
    parties_data = conn.execute('''
        SELECT 
            mt.party,
            COUNT(DISTINCT mt.mp_id) as mp_count,
            COUNT(DISTINCT s.id) as statement_count,
            CAST(COUNT(DISTINCT s.id) AS FLOAT) / COUNT(DISTINCT mt.mp_id) as avg_statements_per_mp
        FROM mp_terms mt
        LEFT JOIN statements s ON s.mp_id = mt.mp_id
        LEFT JOIN hansard_sessions hs ON s.session_id = hs.id
        LEFT JOIN parliamentary_terms pt ON hs.term_id = pt.id AND pt.is_current = 1
        WHERE mt.is_current = 1 AND mt.party IS NOT NULL AND mt.party != ''
        GROUP BY mt.party
        ORDER BY mp_count DESC, mt.party ASC
    ''').fetchall()
    
    # Format party data
    parties = []
    for party in parties_data:
        slug = party['party'].lower().replace(' ', '-').replace('.', '')
        logo_filename = get_logo_filename(party['party'])
        parties.append({
            'name': party['party'],
            'full_name': party['party'],
            'slug': slug,
            'logo_filename': logo_filename,
            'mp_count': party['mp_count'],
            'statement_count': party['statement_count'] if party['statement_count'] else 0,
            'avg_statements_per_mp': party['avg_statements_per_mp'] if party['avg_statements_per_mp'] else 0
        })
    
    # Create parties directory
    parties_dir = output_dir / 'parties'
    parties_dir.mkdir(parents=True, exist_ok=True)
    
    # Render template
    template = env.get_template('pages/parties.html')
    html = template.render(parties=parties, active_page='parties')
    
    # Write to file
    (parties_dir / 'index.html').write_text(html)
    print(f'✓ Generated parties/index.html ({len(parties)} parties)')


def generate_party_pages(conn, env, output_dir):
    """Generate individual party detail pages."""
    # Get all parties
    parties = conn.execute('''
        SELECT DISTINCT mt.party
        FROM mp_terms mt
        WHERE mt.is_current = 1 AND mt.party IS NOT NULL AND mt.party != ''
        ORDER BY mt.party ASC
    ''').fetchall()
    
    template = env.get_template('pages/party.html')
    
    for party_row in parties:
        party_name = party_row['party']
        party_name_upper = party_name.upper()
        
        # Get party statistics
        party_stats = conn.execute('''
            SELECT 
                mt.party,
                COUNT(DISTINCT mt.mp_id) as mp_count,
                COUNT(DISTINCT s.id) as total_statements,
                CAST(COUNT(DISTINCT s.id) AS FLOAT) / COUNT(DISTINCT mt.mp_id) as avg_statements,
                COUNT(DISTINCT s.session_id) as total_sessions
            FROM mp_terms mt
            LEFT JOIN statements s ON s.mp_id = mt.mp_id
            LEFT JOIN hansard_sessions hs ON s.session_id = hs.id
            LEFT JOIN parliamentary_terms pt ON hs.term_id = pt.id AND pt.is_current = 1
            WHERE mt.is_current = 1 AND UPPER(mt.party) = ?
            GROUP BY mt.party
        ''', (party_name_upper,)).fetchone()
        
        if not party_stats:
            continue
        
        # Get all MPs for this party
        mps = conn.execute('''
            SELECT 
                m.id,
                m.name,
                mt.constituency,
                m.photo_url,
                COUNT(DISTINCT s.id) as statement_count,
                COUNT(DISTINCT s.session_id) as sessions_attended
            FROM mps m
            JOIN mp_terms mt ON m.id = mt.mp_id
            LEFT JOIN statements s ON s.mp_id = m.id
            LEFT JOIN hansard_sessions hs ON s.session_id = hs.id
            LEFT JOIN parliamentary_terms pt ON hs.term_id = pt.id AND pt.is_current = 1
            WHERE mt.is_current = 1 AND UPPER(mt.party) = ?
            GROUP BY m.id
            ORDER BY statement_count DESC, m.name ASC
        ''', (party_name_upper,)).fetchall()
        
        # Create party slug and logo filename
        party_slug = party_name.lower().replace(' ', '-').replace('.', '')
        party_logo_filename = get_logo_filename(party_stats['party'])
        
        # Render template
        html = template.render(
            party_name=party_stats['party'],
            party_full_name=party_stats['party'],
            party_logo_filename=party_logo_filename,
            mp_count=party_stats['mp_count'],
            total_statements=party_stats['total_statements'],
            avg_statements=party_stats['avg_statements'],
            total_sessions=party_stats['total_sessions'],
            mps=mps,
            active_page='parties'
        )
        
        # Create party directory and write file
        party_dir = output_dir / 'party' / party_slug
        party_dir.mkdir(parents=True, exist_ok=True)
        (party_dir / 'index.html').write_text(html)
    
    print(f'✓ Generated {len(parties)} party detail pages')


def generate_placeholder_pages(env, output_dir):
    """Generate placeholder pages (about, disclaimer, privacy)."""
    template = env.get_template('pages/test.html')
    
    pages = [
        ('about.html', 'about'),
        ('disclaimer.html', 'home'),
        ('privacy.html', 'home'),
    ]
    
    for filename, active_page in pages:
        html = template.render(active_page=active_page)
        (output_dir / filename).write_text(html)
    
    print(f'✓ Generated {len(pages)} placeholder pages')


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate static HTML site from templates and database')
    parser.add_argument('--db', help='Path to SQLite database (default: data/hansard.db)')
    parser.add_argument('--output', help='Output directory (default: output/)')
    
    args = parser.parse_args()
    
    generate_static_site(db_path=args.db, output_dir=args.output)


if __name__ == '__main__':
    main()
