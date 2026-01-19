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

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from mp_data_scraper import MPDataScraper


# Sample HTML for testing
SAMPLE_MP_ROW_HTML = """
<tr>
    <td>
        <img src="/sites/default/files/photos/john_doe.jpg" alt="John Doe"/>
        HON. JOHN DOE
    </td>
    <td>NAIROBI</td>
    <td>WESTLANDS</td>
    <td>ODM</td>
    <td>Elected</td>
    <td><a href="/mp/john-doe">More...</a></td>
</tr>
"""

SAMPLE_NOMINATED_MP_ROW_HTML = """
<tr>
    <td>HON. JANE SMITH</td>
    <td></td>
    <td></td>
    <td>UDA</td>
    <td>Nominated</td>
    <td><a href="/mp/jane-smith">More...</a></td>
</tr>
"""

SAMPLE_TABLE_HTML = """
<table class="views-table">
    <thead>
        <tr>
            <th>Member of Parliament</th>
            <th>County</th>
            <th>Constituency</th>
            <th>Party</th>
            <th>Status</th>
            <th></th>
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
        <ul class="pager">
            <li class="pager-next"><a href="?page=1">Next</a></li>
        </ul>
    </body>
</html>
"""

SAMPLE_PAGE_WITHOUT_NEXT = """
<html>
    <body>
        {table}
        <ul class="pager">
            <li class="pager-previous"><a href="?page=0">Previous</a></li>
        </ul>
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
        
        # Test page 0
        url = scraper.build_url(page=0)
        assert 'field_parliament_value=2022' in url
        assert 'page=0' in url
        
        # Test page 5
        url = scraper.build_url(page=5)
        assert 'page=5' in url
    
    def test_build_url_different_term(self):
        """Test URL building for different parliamentary term"""
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
        
        html = '<tr><td>HON. DR. JOHN DOE</td><td>NAIROBI</td><td>WESTLANDS</td><td>ODM</td><td>Elected</td></tr>'
        soup = BeautifulSoup(html, 'html.parser')
        row = soup.find('tr')
        
        mp_data = scraper.extract_mp_data(row)
        
        assert mp_data is not None
        assert not mp_data['name'].startswith('HON.')
        assert 'DR. JOHN DOE' in mp_data['name']
    
    def test_extract_mp_data_invalid_row(self):
        """Test extracting data from invalid row"""
        scraper = MPDataScraper(term_start_year=2022)
        
        # Row with too few cells
        html = '<tr><td>Name</td><td>County</td></tr>'
        soup = BeautifulSoup(html, 'html.parser')
        row = soup.find('tr')
        
        mp_data = scraper.extract_mp_data(row)
        assert mp_data is None
    
    def test_extract_mp_data_empty_name(self):
        """Test extracting data with empty name"""
        scraper = MPDataScraper(term_start_year=2022)
        
        html = '<tr><td></td><td>NAIROBI</td><td>WESTLANDS</td><td>ODM</td><td>Elected</td></tr>'
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
        
        assert scraper.has_next_page(soup) is True
    
    def test_has_next_page_false(self):
        """Test detecting no next page"""
        scraper = MPDataScraper(term_start_year=2022)
        
        table_html = SAMPLE_TABLE_HTML.format(rows=SAMPLE_MP_ROW_HTML)
        page_html = SAMPLE_PAGE_WITHOUT_NEXT.format(table=table_html)
        soup = BeautifulSoup(page_html, 'html.parser')
        
        assert scraper.has_next_page(soup) is False
    
    def test_has_next_page_no_pager(self):
        """Test detecting no next page when pager is missing"""
        scraper = MPDataScraper(term_start_year=2022)
        
        html = '<html><body><table></table></body></html>'
        soup = BeautifulSoup(html, 'html.parser')
        
        assert scraper.has_next_page(soup) is False
    
    @patch('mp_data_scraper.MPDataScraper.fetch_page')
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
    
    @patch('mp_data_scraper.MPDataScraper.fetch_page')
    def test_scrape_page_no_table(self, mock_fetch):
        """Test scraping page with no table"""
        scraper = MPDataScraper(term_start_year=2022)
        
        mock_fetch.return_value = BeautifulSoup('<html><body></body></html>', 'html.parser')
        
        mps = scraper.scrape_page(page=0)
        assert len(mps) == 0
    
    @patch('mp_data_scraper.MPDataScraper.fetch_page')
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
            {
                'name': 'JOHN DOE',
                'county': 'NAIROBI',
                'constituency': 'WESTLANDS',
                'party': 'ODM',
                'status': 'Elected',
                'photo_url': 'http://example.com/photo.jpg',
                'term_start_year': 2022
            }
        ]
        
        output_file = tmp_path / 'mps.json'
        scraper.save_to_json(mps, str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded_mps = json.load(f)
        
        assert len(loaded_mps) == 1
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
                'photo_url': 'http://example.com/photo.jpg',
                'term_start_year': 2022
            }
        ]
        
        output_file = tmp_path / 'mps.csv'
        scraper.save_to_csv(mps, str(output_file))
        
        assert output_file.exists()
        
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
        
        # Should not create file or should create empty file
        # Either behavior is acceptable


class TestMPDataScraperIntegration:
    """Integration tests (require network access)"""
    
    @pytest.mark.integration
    def test_fetch_page_real(self):
        """Test fetching a real page from parliament.go.ke"""
        scraper = MPDataScraper(term_start_year=2022, delay=2.0)
        
        soup = scraper.fetch_page(page=0)
        
        assert soup is not None
        assert soup.find('table') is not None
    
    @pytest.mark.integration
    def test_scrape_page_real(self):
        """Test scraping real data from parliament.go.ke"""
        scraper = MPDataScraper(term_start_year=2022, delay=2.0)
        
        mps = scraper.scrape_page(page=0)
        
        assert len(mps) > 0
        assert all('name' in mp for mp in mps)
        assert all('party' in mp for mp in mps)
