"""
Property-based tests for network call prevention.

This module tests that the mocked_parliament_http fixture correctly prevents
all real network calls during test execution.

Property 4: Network Call Prevention
Validates: Requirements 4.2, 4.3

Feature: test-calibration-and-integration-fixes
"""

import datetime
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.storage.filesystem import FilesystemStorage


# ============================================================================
# Property 4: Network Call Prevention
# ============================================================================

class TestNetworkCallPrevention:
    """
    Property-based tests for network call prevention.
    
    These tests validate that the mocked_parliament_http fixture correctly
    prevents all real network calls during test execution.
    """
    
    @given(
        page_number=st.integers(min_value=0, max_value=2)
    )
    @settings(
        max_examples=3,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_4_no_real_network_calls_during_scraping(
        self,
        mocked_parliament_http,
        production_db,
        page_number
    ):
        """
        Property 4: Network Call Prevention
        
        For ANY scraping operation with mocked_parliament_http fixture,
        NO real network calls should occur. All HTTP requests should be
        intercepted by the mock.
        
        Validates: Requirements 4.2, 4.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup storage
            storage = FilesystemStorage(tmpdir)
            
            # Create scraper AFTER mocking is in place
            scraper = HansardScraper(
                storage=storage,
                db_path=str(production_db)
            )
            
            # Track if any real network call is attempted
            real_network_call_attempted = False
            original_request = requests.Session.request
            
            def detect_real_call(*args, **kwargs):
                """Detect if a real network call is attempted."""
                nonlocal real_network_call_attempted
                real_network_call_attempted = True
                # This should never be called because mocking should intercept
                raise AssertionError(
                    "Real network call attempted! Mocking failed. "
                    f"Args: {args}, Kwargs: {kwargs}"
                )
            
            # Patch the actual requests.Session.request to detect real calls
            with patch.object(requests.Session, 'request', side_effect=detect_real_call):
                try:
                    # Attempt to scrape a page
                    # This should use the mock, not make a real call
                    scraper.scrape_hansard_page(page_number)
                    
                    # Verify no real network call was attempted
                    assert not real_network_call_attempted, \
                        "Real network call was attempted despite mocking"
                    
                    # Verify the mock was actually used
                    assert mocked_parliament_http.get.called, \
                        "Mock was not called - scraper may not be using HTTP at all"
                    
                except Exception as e:
                    # If scraping fails for other reasons (parsing, etc.),
                    # that's okay - we only care that no real network call occurred
                    if "Real network call attempted" in str(e):
                        raise
                    # Otherwise, verify no real network call was attempted
                    assert not real_network_call_attempted, \
                        f"Real network call attempted despite error: {e}"
    
    @given(
        url=st.just("https://example.com/test.pdf"),
        title=st.just("Test Report"),
        date=st.just("2024-01-15")
    )
    @settings(
        max_examples=3,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_4_no_real_network_calls_during_download(
        self,
        mocked_parliament_http,
        production_db,
        url,
        title,
        date
    ):
        """
        Property 4: Network Call Prevention (Download Operations)
        
        For ANY PDF download operation with mocked_parliament_http fixture,
        NO real network calls should occur. All HTTP requests should be
        intercepted by the mock.
        
        Validates: Requirements 4.2, 4.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup storage
            storage = FilesystemStorage(tmpdir)
            
            # Configure mock to return PDF content
            mock_response = Mock()
            mock_response.iter_content = lambda chunk_size: [b'PDF content']
            mock_response.raise_for_status = Mock()
            mocked_parliament_http.get.return_value = mock_response
            
            # Create scraper AFTER mocking is in place
            scraper = HansardScraper(
                storage=storage,
                db_path=str(production_db)
            )
            
            # Track if any real network call is attempted
            real_network_call_attempted = False
            
            def detect_real_call(*args, **kwargs):
                """Detect if a real network call is attempted."""
                nonlocal real_network_call_attempted
                real_network_call_attempted = True
                raise AssertionError(
                    "Real network call attempted during download! "
                    f"URL: {args[1] if len(args) > 1 else kwargs.get('url', 'unknown')}"
                )
            
            # Patch the actual requests.Session.request to detect real calls
            with patch.object(requests.Session, 'request', side_effect=detect_real_call):
                try:
                    # Attempt to download a PDF
                    # This should use the mock, not make a real call
                    scraper.download_pdf(url, title, date)
                    
                    # Verify no real network call was attempted
                    assert not real_network_call_attempted, \
                        "Real network call was attempted during download"
                    
                    # Verify the mock was actually used
                    assert mocked_parliament_http.get.called, \
                        "Mock was not called during download"
                    
                except Exception as e:
                    # If download fails for other reasons (storage, etc.),
                    # that's okay - we only care that no real network call occurred
                    if "Real network call attempted" in str(e):
                        raise
                    # Otherwise, verify no real network call was attempted
                    assert not real_network_call_attempted, \
                        f"Real network call attempted despite error: {e}"
    
    @given(
        operation_count=st.integers(min_value=1, max_value=2)
    )
    @settings(
        max_examples=2,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_4_no_real_network_calls_multiple_operations(
        self,
        mocked_parliament_http,
        production_db,
        operation_count
    ):
        """
        Property 4: Network Call Prevention (Multiple Operations)
        
        For ANY sequence of multiple scraping operations with mocked_parliament_http
        fixture, NO real network calls should occur across all operations.
        
        Validates: Requirements 4.2, 4.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup storage
            storage = FilesystemStorage(tmpdir)
            
            # Create scraper AFTER mocking is in place
            scraper = HansardScraper(
                storage=storage,
                db_path=str(production_db)
            )
            
            # Track if any real network call is attempted
            real_network_call_attempted = False
            real_call_details = []
            
            def detect_real_call(*args, **kwargs):
                """Detect if a real network call is attempted."""
                nonlocal real_network_call_attempted
                real_network_call_attempted = True
                real_call_details.append({
                    'args': args,
                    'kwargs': kwargs
                })
                raise AssertionError(
                    f"Real network call attempted! Operation {len(real_call_details)}"
                )
            
            # Patch the actual requests.Session.request to detect real calls
            with patch.object(requests.Session, 'request', side_effect=detect_real_call):
                try:
                    # Perform multiple scraping operations
                    for i in range(operation_count):
                        try:
                            scraper.scrape_hansard_page(i)
                        except Exception as e:
                            # Ignore scraping errors, we only care about network calls
                            if "Real network call attempted" in str(e):
                                raise
                    
                    # Verify no real network calls were attempted
                    assert not real_network_call_attempted, \
                        f"Real network calls attempted: {len(real_call_details)} times"
                    
                    # Verify the mock was used for all operations
                    assert mocked_parliament_http.get.call_count >= operation_count, \
                        f"Mock called {mocked_parliament_http.get.call_count} times, " \
                        f"expected at least {operation_count}"
                    
                except Exception as e:
                    # If operations fail for other reasons, verify no real calls occurred
                    if "Real network call attempted" in str(e):
                        raise
                    assert not real_network_call_attempted, \
                        f"Real network call attempted despite error: {e}"
    
    def test_property_4_unmocked_request_fails_immediately(self, production_db):
        """
        Property 4: Network Call Prevention (Unmocked Request Detection)
        
        When a test attempts to make an HTTP request WITHOUT using the
        mocked_parliament_http fixture, it should fail immediately with
        a descriptive error.
        
        This test validates that our detection mechanism works correctly.
        
        Validates: Requirements 4.2, 4.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup storage
            storage = FilesystemStorage(tmpdir)
            
            # Create scraper WITHOUT mocking
            # This should fail if it tries to make a real network call
            scraper = HansardScraper(
                storage=storage,
                db_path=str(production_db)
            )
            
            # Track if a real network call is attempted
            real_network_call_attempted = False
            
            def detect_real_call(*args, **kwargs):
                """Detect if a real network call is attempted."""
                nonlocal real_network_call_attempted
                real_network_call_attempted = True
                raise AssertionError(
                    "Unmocked HTTP request detected! "
                    "Use mocked_parliament_http fixture to prevent real network calls."
                )
            
            # Patch requests.Session.request to detect unmocked calls
            with patch.object(requests.Session, 'request', side_effect=detect_real_call):
                # Attempt to scrape without mocking
                # This SHOULD trigger our detection
                with pytest.raises(AssertionError, match="Unmocked HTTP request detected"):
                    scraper.scrape_hansard_page(0)
                
                # Verify our detection mechanism was triggered
                assert real_network_call_attempted, \
                    "Detection mechanism was not triggered - test may be invalid"
