#!/usr/bin/env python3
"""
Tests for MP Data Scraper

Tests the scraping functionality for MP data from parliament.go.ke
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup

from hansard_tales.scrapers.mp_data_scraper import MPDataScraper


# Sample HTML for testing - matches actual parliament.go.ke structure with CSS classes
SAMPLE_MP_ROW_HTML = """
<tr class="mp">
    <td class="views-field-field-name">HON. JOHN DOE</td>
    <td class="views-field-field-image">
        <img src="/sites/default/files/photos/john_doe.jpg" alt="John Doe"/>
    </td>
    <td class="views-field-field-county">NAIROBI</td>
    <td class="views-field-field-constituency">WESTLANDS</td>
    <td class="views-field-field-party">ODM</td>
    <td class="views-field-field-status">Elected</td>
</tr>
"""

SAMPLE_NOMINATED_MP_ROW_HTML = """
<tr class="mp">
    <td class="views-field-field-name">HON. JANE SMITH</td>
    <td class="views-field-field-image"></td>
    <td class="views-field-field-county"></td>
    <td class="views-field-field-constituency"></td>
    <td class="views-field-field-party">UDA</td>
    <td class="views-field-field-status">Nominated</td>
</tr>
"""

SAMPLE_TABLE_HTML = """
<table class="views-table">
    <thead>
        <tr>
            <th>Member of Parliament</th>
            <th>Photo</th>
            <th>County</th>
            <th>Constituency</th>
            <th>Party</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
        {rows}
    </tbody>
</table>
"""

SAMPLE_PAGE_WITH_NEXT = """
<html>
    <body>
        {table}
        <nav class="pager">
            <a href="?page=1">Next</a>
        </nav>
    </body>
</html>
"""

SAMPLE_PAGE_WITHOUT_NEXT = """
<html>
    <body>
        {table}
        <nav class="pager">
            <a href="?page=0">Previous</a>
        </nav>
    </body>
</html>
"""


class TestMPDataScraper:
    """Test suite for MPDataScraper"""
    
    def test_initialization(self):
        """Test scraper initialization"""
        scraper = MPDataScraper(term_start_year=2022, delay=0.5)
        
        assert scraper.term_start_year == 2022
        assert scraper.delay == 0.5
        assert scraper.session is not None
    
    def test_build_url(self):
        """Test URL building"""
        scraper = MPDataScraper(term_start_year=2022)
        
        url = scraper.build_url(page=0)
        
        assert 'parliament.go.ke' in url
        assert 'field_parliament_value=2022' in url
        assert 'page=0' in url
    
    def test_build_url_different_term(self):
        """Test URL building with different term"""
        scraper = MPDataScraper(term_start_year=2017)
        
        url = scraper.build_url(page=0)
        assert 'field_parliament_value=2017' in url
    
    def test_extract_mp_data_elected(self):
        """Test extracting data for elected MP"""
        scraper = MPDataScraper(term_start_year=2022)
        soup = BeautifulSoup(SAMPLE_MP_ROW_HTML, 'html.parser')
        row = soup.find('tr')
        
        mp_data = scraper.extract_mp_data(row)
        
        assert mp_data is not None
        assert mp_data['name'] == 'JOHN DOE'
        assert mp_data['county'] == 'NAIROBI'
        assert mp_data['constituency'] == 'WESTLANDS'
        assert mp_data['party'] == 'ODM'
        assert mp_data['status'] == 'Elected'
        assert 'john_doe.jpg' in mp_data['photo_url']
        assert mp_data['term_start_year'] == 2022
    
    def test_extract_mp_data_nominated(self):
        """Test extracting data for nominated MP"""
        scraper = MPDataScraper(term_start_year=2022)
        soup = BeautifulSoup(SAMPLE_NOMINATED_MP_ROW_HTML, 'html.parser')
        row = soup.find('tr')
        
        mp_data = scraper.extract_mp_data(row)
        
        assert mp_data is not None
        assert mp_data['name'] == 'JANE SMITH'
        assert mp_data['county'] is None
        assert mp_data['constituency'] is None
        assert mp_data['party'] == 'UDA'
        assert mp_data['status'] == 'Nominated'
        assert mp_data['photo_url'] is None
    
    def test_extract_mp_data_removes_hon_prefix(self):
        """Test that HON. prefix is removed from names"""
        scraper = MPDataScraper(term_start_year=2022)
        
        html = '''<tr class="mp">
            <td class="views-field-field-name">HON. DR. JOHN DOE</td>
            <td class="views-field-field-county">NAIROBI</td>
            <td class="views-field-field-constituency">WESTLANDS</td>
            <td class="views-field-field-party">ODM</td>
            <td class="views-field-field-status">Elected</td>
        </tr>'''
        soup = BeautifulSoup(html, 'html.parser')
        row = soup.find('tr')
        
        mp_data = scraper.extract_mp_data(row)
        
        assert mp_data is not None
        assert not mp_data['name'].startswith('HON.')
        assert 'DR. JOHN DOE' in mp_data['name']
    
    def test_extract_mp_data_invalid_row(self):
        """Test extracting data from invalid row"""
        scraper = MPDataScraper(term_start_year=2022)
        
        # Row without required class
        html = '<tr><td>Name</td><td>County</td></tr>'
        soup = BeautifulSoup(html, 'html.parser')
        row = soup.find('tr')
        
        mp_data = scraper.extract_mp_data(row)
        assert mp_data is None
    
    def test_extract_mp_data_empty_name(self):
        """Test extracting data with empty name"""
        scraper = MPDataScraper(term_start_year=2022)
        
        html = '''<tr class="mp">
            <td class="views-field-field-name"></td>
            <td class="views-field-field-county">NAIROBI</td>
            <td class="views-field-field-constituency">WESTLANDS</td>
            <td class="views-field-field-party">ODM</td>
            <td class="views-field-field-status">Elected</td>
        </tr>'''
        soup = BeautifulSoup(html, 'html.parser')
        row = soup.find('tr')
        
        mp_data = scraper.extract_mp_data(row)
        assert mp_data is None
    
    def test_has_next_page_true(self):
        """Test detecting next page when it exists"""
        scraper = MPDataScraper(term_start_year=2022)
        
        table_html = SAMPLE_TABLE_HTML.format(rows=SAMPLE_MP_ROW_HTML)
        page_html = SAMPLE_PAGE_WITH_NEXT.format(table=table_html)
        soup = BeautifulSoup(page_html, 'html.parser')
        
        assert scraper.has_next_page(soup, current_page=0) is True
    
    def test_has_next_page_false(self):
        """Test detecting no next page"""
        scraper = MPDataScraper(term_start_year=2022)
        
        table_html = SAMPLE_TABLE_HTML.format(rows=SAMPLE_MP_ROW_HTML)
        page_html = SAMPLE_PAGE_WITHOUT_NEXT.format(table=table_html)
        soup = BeautifulSoup(page_html, 'html.parser')
        
        assert scraper.has_next_page(soup, current_page=0) is False
    
    def test_has_next_page_no_pager(self):
        """Test detecting no next page when pager is missing"""
        scraper = MPDataScraper(term_start_year=2022)
        
        html = '<html><body><table></table></body></html>'
        soup = BeautifulSoup(html, 'html.parser')
        
        assert scraper.has_next_page(soup, current_page=0) is False
    
    @patch('hansard_tales.scrapers.mp_data_scraper.MPDataScraper.fetch_page')
    def test_scrape_page_success(self, mock_fetch):
        """Test scraping a single page successfully"""
        scraper = MPDataScraper(term_start_year=2022)
        
        # Create mock page with 2 MPs
        rows = SAMPLE_MP_ROW_HTML + SAMPLE_NOMINATED_MP_ROW_HTML
        table_html = SAMPLE_TABLE_HTML.format(rows=rows)
        page_html = f'<html><body>{table_html}</body></html>'
        mock_fetch.return_value = BeautifulSoup(page_html, 'html.parser')
        
        mps = scraper.scrape_page(page=0)
        
        assert len(mps) == 2
        assert mps[0]['name'] == 'JOHN DOE'
        assert mps[1]['name'] == 'JANE SMITH'
    
    @patch('hansard_tales.scrapers.mp_data_scraper.MPDataScraper.fetch_page')
    def test_scrape_page_no_table(self, mock_fetch):
        """Test scraping page with no table"""
        scraper = MPDataScraper(term_start_year=2022)
        
        mock_fetch.return_value = BeautifulSoup('<html><body></body></html>', 'html.parser')
        
        mps = scraper.scrape_page(page=0)
        assert len(mps) == 0
    
    @patch('hansard_tales.scrapers.mp_data_scraper.MPDataScraper.fetch_page')
    def test_scrape_page_fetch_fails(self, mock_fetch):
        """Test scraping when fetch fails"""
        scraper = MPDataScraper(term_start_year=2022)
        
        mock_fetch.return_value = None
        
        mps = scraper.scrape_page(page=0)
        assert len(mps) == 0
    
    def test_save_to_json(self, tmp_path):
        """Test saving MPs to JSON file"""
        scraper = MPDataScraper(term_start_year=2022)
        
        mps = [
            {'name': 'JOHN DOE', 'party': 'ODM'},
            {'name': 'JANE SMITH', 'party': 'UDA'}
        ]
        
        output_file = tmp_path / 'mps.json'
        scraper.save_to_json(mps, str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded_mps = json.load(f)
        
        assert len(loaded_mps) == 2
        assert loaded_mps[0]['name'] == 'JOHN DOE'
    
    def test_save_to_csv(self, tmp_path):
        """Test saving MPs to CSV file"""
        scraper = MPDataScraper(term_start_year=2022)
        
        mps = [
            {
                'name': 'JOHN DOE',
                'county': 'NAIROBI',
                'constituency': 'WESTLANDS',
                'party': 'ODM',
                'status': 'Elected',
                'photo_url': 'http://example.com/john.jpg',
                'term_start_year': 2022
            }
        ]
        
        output_file = tmp_path / 'mps.csv'
        scraper.save_to_csv(mps, str(output_file))
        
        assert output_file.exists()
        
        # Read and verify CSV
        import csv
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['name'] == 'JOHN DOE'
    
    def test_save_to_csv_empty(self, tmp_path):
        """Test saving empty list to CSV"""
        scraper = MPDataScraper(term_start_year=2022)
        
        output_file = tmp_path / 'mps.csv'
        scraper.save_to_csv([], str(output_file))
        
        # Should not create file or create empty file
        # Just ensure no exception is raised


class TestMPDataScraperIntegration:
    """Integration tests that hit real website (marked as slow)"""
    
    @pytest.mark.slow
    def test_fetch_page_real(self):
        """Test fetching a real page from parliament.go.ke"""
        scraper = MPDataScraper(term_start_year=2022, delay=0.5)
        
        soup = scraper.fetch_page(page=0)
        
        assert soup is not None
        assert soup.find('body') is not None
    
    @pytest.mark.slow
    def test_scrape_page_real(self):
        """Test scraping a real page"""
        scraper = MPDataScraper(term_start_year=2022, delay=0.5)
        
        mps = scraper.scrape_page(page=0)
        
        # Should get some MPs (at least 1)
        assert len(mps) > 0
        
        # Verify structure
        mp = mps[0]
        assert 'name' in mp
        assert 'party' in mp
        assert 'term_start_year' in mp



class TestCLI:
    """Test suite for CLI argument parsing and main() function."""
    
    @patch('hansard_tales.scrapers.mp_data_scraper.MPDataScraper')
    @patch('sys.argv', ['hansard-mp-scraper', '--term', '2022', '--output', 'test_mps.json'])
    def test_main_with_arguments(self, mock_scraper_class):
        """Test main() with custom arguments."""
        from hansard_tales.scrapers.mp_data_scraper import main
        
        # Mock scraper instance - return actual list, not Mock
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = [
            {'name': 'Test MP 1', 'constituency': 'Test 1', 'party': 'Party A', 'status': 'Elected'},
            {'name': 'Test MP 2', 'constituency': 'Test 2', 'party': 'Party B', 'status': 'Nominated'}
        ]
        mock_scraper.save_to_json = Mock()
        mock_scraper_class.return_value = mock_scraper
        
        # Run main - returns 0 on success
        result = main()
        
        # Should return 0 (success)
        assert result == 0
        
        # Verify scraper was initialized
        mock_scraper_class.assert_called_once()
        
        # Verify scrape_all was called
        mock_scraper.scrape_all.assert_called_once_with(max_pages=50)
        
        # Verify save_to_json was called
        mock_scraper.save_to_json.assert_called_once()
    
    @patch('hansard_tales.scrapers.mp_data_scraper.MPDataScraper')
    @patch('sys.argv', ['hansard-mp-scraper', '--term', '2022', '--output', 'test.json'])
    def test_main_no_mps_found(self, mock_scraper_class):
        """Test main() when no MPs are found."""
        from hansard_tales.scrapers.mp_data_scraper import main
        
        # Mock scraper instance that returns empty list
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = []
        mock_scraper_class.return_value = mock_scraper
        
        # Run main - returns 1 on failure
        result = main()
        
        # Should return 1 (failure)
        assert result == 1
