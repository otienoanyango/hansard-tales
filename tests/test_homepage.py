"""
Tests for homepage template and route.
"""
import pytest
from pathlib import Path
from app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHomepageRoute:
    """Test homepage route."""
    
    def test_homepage_route_exists(self, client):
        """Test that homepage route exists."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_homepage_returns_html(self, client):
        """Test that homepage returns HTML content."""
        response = client.get('/')
        assert response.content_type == 'text/html; charset=utf-8'
    
    def test_homepage_has_content(self, client):
        """Test that homepage has content."""
        response = client.get('/')
        assert len(response.data) > 0


class TestHomepageTemplate:
    """Test homepage template structure."""
    
    def test_template_file_exists(self):
        """Test that homepage.html template exists."""
        template_path = Path('templates/pages/homepage.html')
        assert template_path.exists()
    
    def test_template_extends_base(self):
        """Test that template extends base layout."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert '{% extends "layouts/base.html" %}' in content
    
    def test_template_has_title_block(self):
        """Test that template has title block."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert '{% block title %}' in content
    
    def test_template_has_content_block(self):
        """Test that template has content block."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert '{% block content %}' in content


class TestHomepageContent:
    """Test homepage content sections."""
    
    def test_homepage_has_hero_section(self, client):
        """Test that homepage has hero section with title."""
        response = client.get('/')
        data = response.data.decode('utf-8')
        assert "Track Your MP's Performance" in data or "Track Your MP" in data
    
    def test_homepage_has_search_box(self, client):
        """Test that homepage has search functionality."""
        response = client.get('/')
        data = response.data.decode('utf-8')
        assert 'mp-search' in data
        assert 'Search' in data or 'search' in data.lower()
    
    def test_homepage_has_introduction(self, client):
        """Test that homepage has introduction section."""
        response = client.get('/')
        data = response.data.decode('utf-8')
        assert 'Hansard Tales' in data
        assert 'parliamentary' in data.lower() or 'Parliament' in data
    
    def test_homepage_has_parliament_info(self, client):
        """Test that homepage shows current parliament info."""
        response = client.get('/')
        data = response.data.decode('utf-8')
        assert '13th Parliament' in data or '13th' in data
        assert '349' in data  # Total MPs
    
    def test_homepage_has_navigation_links(self, client):
        """Test that homepage has links to other pages."""
        response = client.get('/')
        data = response.data.decode('utf-8')
        assert '/mps/' in data
        assert '/parties/' in data or 'parties' in data.lower()
        assert '/about/' in data or 'about' in data.lower()


class TestHomepageSearch:
    """Test homepage search functionality."""
    
    def test_search_input_exists(self):
        """Test that search input field exists in template."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'id="mp-search"' in content
        assert 'type="text"' in content
    
    def test_search_has_placeholder(self):
        """Test that search input has placeholder text."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'placeholder=' in content
    
    def test_search_has_aria_label(self):
        """Test that search input has accessibility label."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'aria-label=' in content
    
    def test_search_results_container_exists(self):
        """Test that search results container exists."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'id="search-results"' in content
    
    def test_search_has_javascript(self):
        """Test that search has JavaScript functionality."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert '{% block extra_js %}' in content
        assert 'addEventListener' in content


class TestHomepageParliamentInfo:
    """Test parliament information section."""
    
    def test_shows_current_parliament_term(self):
        """Test that current parliament term is displayed."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert '13th Parliament' in content
    
    def test_shows_parliament_dates(self):
        """Test that parliament dates are shown."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert '2022' in content
        assert '2027' in content
    
    def test_shows_total_mps(self):
        """Test that total MP count is shown."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert '349' in content
    
    def test_shows_what_we_track(self):
        """Test that tracking features are listed."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'Statements' in content or 'statements' in content.lower()
        assert 'attendance' in content.lower() or 'Session' in content


class TestHomepageLinks:
    """Test homepage external and internal links."""
    
    def test_has_browse_all_mps_link(self):
        """Test that homepage has link to browse all MPs."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert '/mps/' in content
        assert 'browse' in content.lower() or 'Browse' in content
    
    def test_has_parties_link(self):
        """Test that homepage has link to parties page."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert '/parties/' in content
    
    def test_has_about_link(self):
        """Test that homepage has link to about page."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert '/about/' in content
    
    def test_has_parliament_source_link(self):
        """Test that homepage links to parliament.go.ke."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'parliament.go.ke' in content
    
    def test_external_links_open_in_new_tab(self):
        """Test that external links open in new tab."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'target="_blank"' in content
        assert 'rel="noopener"' in content


class TestHomepageResponsive:
    """Test homepage responsive design."""
    
    def test_uses_responsive_classes(self):
        """Test that template uses responsive Tailwind classes."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'md:' in content  # Medium breakpoint
    
    def test_uses_grid_layout(self):
        """Test that template uses grid layout."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'grid' in content
    
    def test_uses_max_width_container(self):
        """Test that template uses max-width containers."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'max-w-' in content


class TestHomepageAccessibility:
    """Test homepage accessibility features."""
    
    def test_uses_semantic_html(self):
        """Test that template uses semantic HTML."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert '<section' in content
        assert '<h1' in content
        assert '<h2' in content
    
    def test_has_aria_labels(self):
        """Test that interactive elements have ARIA labels."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'aria-label=' in content
    
    def test_links_have_descriptive_text(self):
        """Test that links have descriptive text."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        # Should not have generic "click here" links
        assert 'click here' not in content.lower()


class TestHomepageStyling:
    """Test homepage styling and design."""
    
    def test_uses_tailwind_classes(self):
        """Test that template uses Tailwind CSS classes."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'bg-' in content
        assert 'text-' in content
        assert 'border-' in content
    
    def test_uses_kenya_colors(self):
        """Test that template uses Kenya color palette."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'kenya-green' in content
        assert 'kenya-red' in content or 'warm-white' in content
    
    def test_uses_rounded_corners(self):
        """Test that template uses rounded corners."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'rounded' in content
    
    def test_uses_borders(self):
        """Test that template uses borders."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'border-' in content


class TestHomepageQuickLinks:
    """Test homepage quick links section."""
    
    def test_has_quick_links_section(self):
        """Test that homepage has quick links section."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'Explore' in content or 'explore' in content.lower()
    
    def test_quick_links_are_cards(self):
        """Test that quick links are styled as cards."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        # Should have card-like styling
        assert 'shadow' in content
        assert 'hover:' in content
    
    def test_has_all_mps_card(self):
        """Test that quick links include All MPs card."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'All MPs' in content
    
    def test_has_parties_card(self):
        """Test that quick links include Parties card."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'Parties' in content
    
    def test_has_about_card(self):
        """Test that quick links include About card."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'About' in content


class TestHomepageDataAttribution:
    """Test data source attribution."""
    
    def test_has_data_source_section(self):
        """Test that homepage has data source attribution."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'Data Source' in content or 'source' in content.lower()
    
    def test_mentions_hansard(self):
        """Test that data source mentions Hansard."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'Hansard' in content
    
    def test_has_last_updated_info(self):
        """Test that homepage shows last updated date."""
        template_path = Path('templates/pages/homepage.html')
        content = template_path.read_text()
        assert 'last_updated' in content or 'Updated' in content
