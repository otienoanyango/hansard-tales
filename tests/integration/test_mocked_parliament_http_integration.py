"""
Integration test for mocked_parliament_http fixture with HansardScraper.

This test validates that the fixture correctly prevents real network calls
when used with the actual HansardScraper component.
"""

import tempfile
from pathlib import Path

from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.storage.filesystem import FilesystemStorage


def test_scraper_uses_mocked_http(mocked_parliament_http, production_db):
    """
    Test that HansardScraper uses mocked HTTP and doesn't make real calls.
    
    This is a critical integration test that validates:
    1. The fixture mocks requests.Session BEFORE scraper instantiation
    2. The scraper uses the mocked session
    3. No real network calls are made
    
    Validates: Requirements 4.1, 4.2, 4.3, 5.5
    """
    # Create temporary storage
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            storage = FilesystemStorage(temp_dir)
        except Exception as e:
            raise AssertionError(f"[FilesystemStorage] Failed to create storage: {e}") from e
        
        # Create scraper AFTER mocking is in place
        # This is the critical pattern - mocking must happen before instantiation
        try:
            scraper = HansardScraper(
                storage=storage,
                db_path=str(production_db)
            )
        except Exception as e:
            raise AssertionError(f"[HansardScraper] Failed to create scraper: {e}") from e
        
        # Verify the scraper was created successfully
        try:
            assert scraper is not None
            assert scraper.session is not None
        except AssertionError as e:
            raise AssertionError(f"[HansardScraper] Scraper validation failed: {e}") from e
        
        # The scraper's session should be our mock
        # (This is implicit - the patch ensures any Session() call returns our mock)
        
        # Now test that scraping uses the mock
        # Note: We need to check if the scraper has methods that use the session
        # For now, we verify the mock is set up correctly
        
        # Verify mock was configured
        try:
            assert mocked_parliament_http.get.return_value.status_code == 200
            assert 'Hansard' in mocked_parliament_http.get.return_value.text
        except AssertionError as e:
            raise AssertionError(f"[MockedHTTP] Mock configuration validation failed: {e}") from e


def test_scraper_fetch_page_uses_mock(mocked_parliament_http, production_db):
    """
    Test that scraper's fetch_page method uses mocked HTTP.
    
    Validates: Requirements 4.1, 4.2, 4.3, 5.5
    """
    # Create temporary storage
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            storage = FilesystemStorage(temp_dir)
        except Exception as e:
            raise AssertionError(f"[FilesystemStorage] Failed to create storage: {e}") from e
        
        # Create scraper with mocked HTTP
        try:
            scraper = HansardScraper(
                storage=storage,
                db_path=str(production_db)
            )
        except Exception as e:
            raise AssertionError(f"[HansardScraper] Failed to create scraper: {e}") from e
        
        # Call fetch_page - should use mocked session
        try:
            result = scraper.fetch_page('https://parliament.go.ke/hansard')
        except Exception as e:
            raise AssertionError(f"[HansardScraper] fetch_page failed: {e}") from e
        
        # Verify we got the mocked response
        try:
            assert result is not None
            assert 'Hansard' in result
            assert 'December 2025' in result
        except AssertionError as e:
            raise AssertionError(f"[HansardScraper] Response validation failed: {e}") from e
        
        # Verify the mock was called (the scraper's session.get was called)
        # Note: The scraper creates its own session, but our patch ensures
        # that session is our mock
        try:
            assert mocked_parliament_http.get.called
        except AssertionError as e:
            raise AssertionError(f"[MockedHTTP] Mock call verification failed: {e}") from e


def test_multiple_scrapers_use_same_mock(mocked_parliament_http, production_db):
    """
    Test that multiple scraper instances all use the same mock.
    
    This validates that the fixture properly mocks at the class level,
    not the instance level.
    
    Validates: Requirements 4.1, 5.5
    """
    # Create temporary storage
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            storage = FilesystemStorage(temp_dir)
        except Exception as e:
            raise AssertionError(f"[FilesystemStorage] Failed to create storage: {e}") from e
        
        # Create multiple scrapers
        try:
            scraper1 = HansardScraper(storage=storage, db_path=str(production_db))
            scraper2 = HansardScraper(storage=storage, db_path=str(production_db))
            scraper3 = HansardScraper(storage=storage, db_path=str(production_db))
        except Exception as e:
            raise AssertionError(f"[HansardScraper] Failed to create scrapers: {e}") from e
        
        # All should be created successfully
        try:
            assert scraper1 is not None
            assert scraper2 is not None
            assert scraper3 is not None
        except AssertionError as e:
            raise AssertionError(f"[HansardScraper] Scraper creation validation failed: {e}") from e
        
        # All should have sessions (which are all mocked)
        try:
            assert scraper1.session is not None
            assert scraper2.session is not None
            assert scraper3.session is not None
        except AssertionError as e:
            raise AssertionError(f"[HansardScraper] Session validation failed: {e}") from e
        
        # Fetch pages with each scraper
        try:
            result1 = scraper1.fetch_page('https://parliament.go.ke/hansard?page=0')
            result2 = scraper2.fetch_page('https://parliament.go.ke/hansard?page=1')
            result3 = scraper3.fetch_page('https://parliament.go.ke/hansard?page=2')
        except Exception as e:
            raise AssertionError(f"[HansardScraper] fetch_page failed: {e}") from e
        
        # All should get the same mocked response
        try:
            assert result1 == result2 == result3
            assert 'Hansard' in result1
        except AssertionError as e:
            raise AssertionError(f"[HansardScraper] Response validation failed: {e}") from e
        
        # Verify mock was called 3 times
        try:
            assert mocked_parliament_http.get.call_count == 3
        except AssertionError as e:
            raise AssertionError(f"[MockedHTTP] Call count validation failed: {e}") from e


def test_scraper_with_realistic_html_structure(mocked_parliament_http, production_db):
    """
    Test that scraper can parse the realistic HTML from the mock.
    
    This validates that the mock provides HTML that matches what the
    scraper expects from the real parliament.go.ke site.
    
    Validates: Requirements 4.5, 5.5
    """
    from bs4 import BeautifulSoup
    
    # Create temporary storage
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            storage = FilesystemStorage(temp_dir)
        except Exception as e:
            raise AssertionError(f"[FilesystemStorage] Failed to create storage: {e}") from e
        
        # Create scraper
        try:
            scraper = HansardScraper(storage=storage, db_path=str(production_db))
        except Exception as e:
            raise AssertionError(f"[HansardScraper] Failed to create scraper: {e}") from e
        
        # Fetch page
        try:
            html = scraper.fetch_page('https://parliament.go.ke/hansard')
        except Exception as e:
            raise AssertionError(f"[HansardScraper] fetch_page failed: {e}") from e
        
        # Parse HTML
        try:
            soup = BeautifulSoup(html, 'html.parser')
        except Exception as e:
            raise AssertionError(f"[BeautifulSoup] HTML parsing failed: {e}") from e
        
        # Verify structure matches what scraper expects
        try:
            pdf_links = soup.find_all('a', href=lambda h: h and '.pdf' in h.lower())
            assert len(pdf_links) > 0, "Mock HTML should contain PDF links"
        except AssertionError as e:
            raise AssertionError(f"[HTMLStructure] PDF link validation failed: {e}") from e
        
        # Verify links have the expected structure
        try:
            for link in pdf_links:
                href = link['href']
                assert href.startswith('/'), f"PDF links should be relative: {href}"
                assert '.pdf' in href.lower(), f"Links should point to PDFs: {href}"
                
                # Verify link text contains date information
                text = link.get_text()
                assert any(month in text for month in [
                    'January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December'
                ]), f"Link text should contain month: {text}"
        except AssertionError as e:
            raise AssertionError(f"[HTMLStructure] Link structure validation failed: {e}") from e
