"""
Simple Flask app for local development and template preview.
"""
from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)


@app.route('/')
def index():
    """Home page."""
    return render_template('pages/test.html', active_page='home')


@app.route('/mps/')
def mps_list():
    """MPs listing page (placeholder)."""
    return render_template('pages/test.html', active_page='mps')


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
