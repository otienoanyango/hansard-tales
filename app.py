"""
Simple Flask app for local development and template preview.
"""
from flask import Flask, render_template
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)


def get_db_connection():
    """Get database connection."""
    # Use test database if available (for testing)
    test_db_path = os.environ.get('TEST_DB_PATH')
    if test_db_path:
        conn = sqlite3.connect(test_db_path)
    else:
        # Use absolute path to database file
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'hansard.db')
        conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Home page."""
    return render_template('pages/test.html', active_page='home')


@app.route('/mps/')
def mps_list():
    """MPs listing page (placeholder)."""
    return render_template('pages/test.html', active_page='mps')


@app.route('/mp/<int:mp_id>/')
def mp_profile(mp_id):
    """MP profile page."""
    conn = get_db_connection()
    
    # Get MP basic info
    mp = conn.execute('''
        SELECT m.*, mt.constituency, mt.party, mt.elected_date
        FROM mps m
        JOIN mp_terms mt ON m.id = mt.mp_id
        WHERE m.id = ? AND mt.is_current = 1
    ''', (mp_id,)).fetchone()
    
    if not mp:
        return "MP not found", 404
    
    # Get current term info
    current_term = conn.execute('''
        SELECT * FROM parliamentary_terms WHERE is_current = 1
    ''').fetchone()
    
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
    
    conn.close()
    
    return render_template('pages/mp_profile.html',
                         mp=mp,
                         current_term=current_term,
                         performance=performance,
                         historical_terms=historical_terms,
                         statements=statements,
                         active_page='mps')


@app.route('/parties/')
def parties():
    """Parties page (placeholder)."""
    return render_template('pages/test.html', active_page='parties')


@app.route('/about/')
def about():
    """About page (placeholder)."""
    return render_template('pages/test.html', active_page='about')


@app.route('/disclaimer/')
def disclaimer():
    """Disclaimer page (placeholder)."""
    return render_template('pages/test.html', active_page='home')


@app.route('/privacy/')
def privacy():
    """Privacy page (placeholder)."""
    return render_template('pages/test.html', active_page='home')


@app.context_processor
def inject_globals():
    """Inject global template variables."""
    return {
        'current_year': datetime.now().year,
        'last_updated': datetime.now().strftime('%B %d, %Y')
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
