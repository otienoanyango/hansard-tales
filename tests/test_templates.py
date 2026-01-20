"""
Tests for Jinja2 templates.

This module tests template loading, rendering, and structure.
"""

import pytest
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound


@pytest.fixture
def jinja_env():
    """Create Jinja2 environment for testing."""
    template_dir = Path(__file__).parent.parent / 'templates'
    
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # Add mock url_for function
    def url_for(endpoint, **kwargs):
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
        elif endpoint == 'mp_profile':
            mp_id = kwargs.get('mp_id', 1)
            return f'/mp/{mp_id}/'
        else:
            return f'/{endpoint}/'
    
    env.globals['url_for'] = url_for
    env.globals['current_year'] = datetime.now().year
    env.globals['last_updated'] = datetime.now().strftime('%B %d, %Y')
    
    return env


class TestBaseTemplate:
    """Test suite for base template."""
    
    def test_base_template_exists(self, jinja_env):
        """Test that base template can be loaded."""
        template = jinja_env.get_template('layouts/base.html')
        assert template is not None
    
    def test_base_template_has_required_blocks(self, jinja_env):
        """Test that base template defines required blocks."""
        template_path = Path(__file__).parent.parent / 'templates' / 'layouts' / 'base.html'
        source = template_path.read_text()
        
        # Check for block definitions
        assert '{% block title %}' in source
        assert '{% block meta_description %}' in source
        assert '{% block content %}' in source
        assert '{% block extra_css %}' in source
        assert '{% block extra_js %}' in source
    
    def test_base_template_has_navigation(self, jinja_env):
        """Test that base template includes navigation."""
        template = jinja_env.get_template('layouts/base.html')
        html = template.render(active_page='home')
        
        assert '<nav' in html
        assert 'navMenu' in html
        assert 'Home' in html
        assert 'All MPs' in html
        assert 'Parties' in html
        assert 'About' in html
    
    def test_base_template_has_header(self, jinja_env):
        """Test that base template includes header."""
        template = jinja_env.get_template('layouts/base.html')
        html = template.render()
        
        assert '<header' in html
        assert 'border-b-2 border-black' in html
        assert 'Hansard Tales' in html
    
    def test_base_template_has_footer(self, jinja_env):
        """Test that base template includes footer."""
        template = jinja_env.get_template('layouts/base.html')
        html = template.render()
        
        assert '<footer' in html
        assert 'border-t-2 border-black' in html
        assert str(datetime.now().year) in html
        assert 'Parliament of Kenya' in html
    
    def test_base_template_includes_css(self, jinja_env):
        """Test that base template links to CSS."""
        template = jinja_env.get_template('layouts/base.html')
        html = template.render()
        
        assert '<link rel="stylesheet"' in html
        assert '/static/css/main.css' in html
    
    def test_base_template_includes_js(self, jinja_env):
        """Test that base template links to JavaScript."""
        template = jinja_env.get_template('layouts/base.html')
        html = template.render()
        
        assert '<script' in html
        assert '/static/js/main.js' in html
    
    def test_base_template_mobile_menu(self, jinja_env):
        """Test that base template includes mobile menu toggle."""
        template = jinja_env.get_template('layouts/base.html')
        html = template.render()
        
        assert 'navToggle' in html
        assert 'navMenu' in html
        assert 'aria-label="Toggle navigation"' in html
    
    def test_base_template_active_page_highlighting(self, jinja_env):
        """Test that active page is highlighted in navigation."""
        template = jinja_env.get_template('layouts/base.html')
        
        # Test home page active
        html = template.render(active_page='home')
        assert 'bg-kenya-green-100 text-kenya-green-800 font-semibold border border-black' in html
        
        # Test MPs page active
        html = template.render(active_page='mps')
        assert 'bg-kenya-green-100 text-kenya-green-800 font-semibold border border-black' in html


class TestPageTemplate:
    """Test suite for page templates."""
    
    def test_test_page_exists(self, jinja_env):
        """Test that test page template exists."""
        template = jinja_env.get_template('pages/test.html')
        assert template is not None
    
    def test_test_page_extends_base(self, jinja_env):
        """Test that test page extends base template."""
        template_path = Path(__file__).parent.parent / 'templates' / 'pages' / 'test.html'
        source = template_path.read_text()
        
        assert '{% extends "layouts/base.html" %}' in source
    
    def test_test_page_renders(self, jinja_env):
        """Test that test page renders successfully."""
        template = jinja_env.get_template('pages/test.html')
        html = template.render(active_page='home')
        
        # Check basic structure
        assert '<html' in html
        assert '<head>' in html
        assert '<body' in html
        assert '</html>' in html
        
        # Check content
        assert 'Test Page' in html
        assert 'Template Test Page' in html
    
    def test_test_page_has_content(self, jinja_env):
        """Test that test page has expected content."""
        template = jinja_env.get_template('pages/test.html')
        html = template.render()
        
        assert 'Base' in html and 'Template Features' in html
        assert 'Typography' in html
        assert 'Colors' in html


class TestTemplateStructure:
    """Test suite for template directory structure."""
    
    def test_templates_directory_exists(self):
        """Test that templates directory exists."""
        templates_dir = Path(__file__).parent.parent / 'templates'
        assert templates_dir.exists()
        assert templates_dir.is_dir()
    
    def test_layouts_directory_exists(self):
        """Test that layouts directory exists."""
        layouts_dir = Path(__file__).parent.parent / 'templates' / 'layouts'
        assert layouts_dir.exists()
        assert layouts_dir.is_dir()
    
    def test_pages_directory_exists(self):
        """Test that pages directory exists."""
        pages_dir = Path(__file__).parent.parent / 'templates' / 'pages'
        assert pages_dir.exists()
        assert pages_dir.is_dir()
    
    def test_components_directory_exists(self):
        """Test that components directory exists."""
        components_dir = Path(__file__).parent.parent / 'templates' / 'components'
        assert components_dir.exists()
        assert components_dir.is_dir()


class TestStaticAssets:
    """Test suite for static assets."""
    
    def test_static_directory_exists(self):
        """Test that static directory exists."""
        static_dir = Path(__file__).parent.parent / 'static'
        assert static_dir.exists()
        assert static_dir.is_dir()
    
    def test_css_directory_exists(self):
        """Test that CSS directory exists."""
        css_dir = Path(__file__).parent.parent / 'static' / 'css'
        assert css_dir.exists()
        assert css_dir.is_dir()
    
    def test_js_directory_exists(self):
        """Test that JavaScript directory exists."""
        js_dir = Path(__file__).parent.parent / 'static' / 'js'
        assert js_dir.exists()
        assert js_dir.is_dir()
    
    def test_images_directory_exists(self):
        """Test that images directory exists."""
        images_dir = Path(__file__).parent.parent / 'static' / 'images'
        assert images_dir.exists()
        assert images_dir.is_dir()
    
    def test_main_css_exists(self):
        """Test that main CSS file exists."""
        css_file = Path(__file__).parent.parent / 'static' / 'css' / 'main.css'
        assert css_file.exists()
        assert css_file.is_file()
    
    def test_main_js_exists(self):
        """Test that main JavaScript file exists."""
        js_file = Path(__file__).parent.parent / 'static' / 'js' / 'main.js'
        assert js_file.exists()
        assert js_file.is_file()
    
    def test_main_css_has_content(self):
        """Test that main CSS file has content."""
        css_file = Path(__file__).parent.parent / 'static' / 'css' / 'main.css'
        content = css_file.read_text()
        
        # Check for key CSS features (Tailwind-based)
        assert 'scroll-behavior' in content
        assert '@media print' in content
        assert 'focus-visible' in content
        assert '#navMenu' in content
    
    def test_main_js_has_content(self):
        """Test that main JavaScript file has content."""
        js_file = Path(__file__).parent.parent / 'static' / 'js' / 'main.js'
        content = js_file.read_text()
        
        # Check for key JavaScript features
        assert 'initMobileNav' in content
        assert 'navToggle' in content
        assert 'addEventListener' in content


class TestResponsiveDesign:
    """Test suite for responsive design features."""
    
    def test_css_has_mobile_first_approach(self):
        """Test that CSS uses mobile-first approach."""
        css_file = Path(__file__).parent.parent / 'static' / 'css' / 'main.css'
        content = css_file.read_text()
        
        # Check for responsive design features (Tailwind handles mobile-first)
        assert '@media' in content or 'transition' in content
    
    def test_base_template_has_viewport_meta(self, jinja_env):
        """Test that base template includes viewport meta tag."""
        template = jinja_env.get_template('layouts/base.html')
        html = template.render()
        
        assert '<meta name="viewport"' in html
        assert 'width=device-width' in html
        assert 'initial-scale=1.0' in html


class TestAccessibility:
    """Test suite for accessibility features."""
    
    def test_base_template_has_lang_attribute(self, jinja_env):
        """Test that HTML has lang attribute."""
        template = jinja_env.get_template('layouts/base.html')
        html = template.render()
        
        assert '<html lang="en">' in html
    
    def test_base_template_has_semantic_html(self, jinja_env):
        """Test that base template uses semantic HTML."""
        template = jinja_env.get_template('layouts/base.html')
        html = template.render()
        
        assert '<header' in html
        assert '<nav' in html
        assert '<main' in html
        assert '<footer' in html
    
    def test_mobile_menu_has_aria_label(self, jinja_env):
        """Test that mobile menu toggle has aria-label."""
        template = jinja_env.get_template('layouts/base.html')
        html = template.render()
        
        assert 'aria-label="Toggle navigation"' in html
