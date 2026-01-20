#!/usr/bin/env python3
"""
Test script for Jinja2 template rendering.

This script tests that templates can be loaded and rendered correctly.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jinja2 import Environment, FileSystemLoader, select_autoescape


def create_jinja_env():
    """Create and configure Jinja2 environment."""
    template_dir = project_root / 'templates'
    
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # Add custom filters
    env.filters['format_date'] = lambda d: d.strftime('%B %d, %Y') if d else ''
    
    # Add global functions
    def url_for(endpoint, **kwargs):
        """Mock url_for function for testing."""
        if endpoint == 'static':
            filename = kwargs.get('filename', '')
            return f'/static/{filename}'
        elif endpoint == 'index':
            return '/'
        elif endpoint == 'mps_list':
            return '/mps/'
        elif endpoint == 'parties':
            return '/parties/'
        elif endpoint == 'about':
            return '/about/'
        elif endpoint == 'disclaimer':
            return '/disclaimer/'
        elif endpoint == 'privacy':
            return '/privacy/'
        else:
            return f'/{endpoint}/'
    
    env.globals['url_for'] = url_for
    env.globals['current_year'] = datetime.now().year
    env.globals['last_updated'] = datetime.now().strftime('%B %d, %Y')
    
    return env


def test_base_template():
    """Test that base template can be loaded."""
    print("Testing base template...")
    env = create_jinja_env()
    
    try:
        template = env.get_template('layouts/base.html')
        print("✓ Base template loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to load base template: {e}")
        return False


def test_page_template():
    """Test that page template can be rendered."""
    print("\nTesting page template rendering...")
    env = create_jinja_env()
    
    try:
        template = env.get_template('pages/test.html')
        
        # Render with test data
        html = template.render(
            active_page='home'
        )
        
        # Basic checks
        assert '<html' in html, "Missing HTML tag"
        assert '<head>' in html, "Missing head tag"
        assert '<body>' in html, "Missing body tag"
        assert 'Hansard Tales' in html, "Missing site name"
        assert 'Test Page' in html, "Missing page title"
        
        print("✓ Page template rendered successfully")
        print(f"  Generated {len(html)} characters of HTML")
        return True
    except Exception as e:
        print(f"✗ Failed to render page template: {e}")
        return False


def test_css_file():
    """Test that CSS file exists."""
    print("\nTesting CSS file...")
    css_file = project_root / 'static' / 'css' / 'main.css'
    
    if css_file.exists():
        size = css_file.stat().st_size
        print(f"✓ CSS file exists ({size} bytes)")
        return True
    else:
        print("✗ CSS file not found")
        return False


def test_js_file():
    """Test that JavaScript file exists."""
    print("\nTesting JavaScript file...")
    js_file = project_root / 'static' / 'js' / 'main.js'
    
    if js_file.exists():
        size = js_file.stat().st_size
        print(f"✓ JavaScript file exists ({size} bytes)")
        return True
    else:
        print("✗ JavaScript file not found")
        return False


def main():
    """Run all tests."""
    print("="*50)
    print("Hansard Tales - Template Testing")
    print("="*50)
    
    tests = [
        test_base_template,
        test_page_template,
        test_css_file,
        test_js_file
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "="*50)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("="*50)
    
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
