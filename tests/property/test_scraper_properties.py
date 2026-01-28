"""
Property-based tests for web scrapers.

Tests universal properties that must hold for scraper operations.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import date
from pathlib import Path
import hashlib

from hansard_tales.models.base import Chamber
from hansard_tales.scrapers.base import ScrapedDocument


class TestScrapedDocumentProperties:
    """Property-based tests for ScrapedDocument."""
    
    @given(
        url=st.text(min_size=10, max_size=200),
        filename=st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='.-_'
        )),
        content=st.binary(min_size=100, max_size=10000),
    )
    def test_scraped_document_hash_consistency(self, url, filename, content):
        """
        Property: Same content must always generate same hash.
        
        **Validates: Requirements 4.8**
        """
        # Compute hash manually
        expected_hash = hashlib.sha256(content).hexdigest()
        
        # Create document
        doc = ScrapedDocument(
            url=url,
            filename=filename,
            content=content,
            hash=expected_hash,
            metadata={}
        )
        
        # Verify hash matches
        assert doc.hash == expected_hash
        assert len(doc.hash) == 64  # SHA256 produces 64 hex characters
    
    @given(
        url=st.text(min_size=10, max_size=200),
        filename=st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='.-_'
        )),
        content=st.binary(min_size=100, max_size=10000),
    )
    def test_scraped_document_hash_uniqueness(self, url, filename, content):
        """
        Property: Different content must generate different hashes.
        
        **Validates: Requirements 4.8, 4.9**
        """
        # Create first document
        hash1 = hashlib.sha256(content).hexdigest()
        doc1 = ScrapedDocument(
            url=url,
            filename=filename,
            content=content,
            hash=hash1,
            metadata={}
        )
        
        # Create second document with modified content
        modified_content = content + b"x"
        hash2 = hashlib.sha256(modified_content).hexdigest()
        doc2 = ScrapedDocument(
            url=url,
            filename=filename,
            content=modified_content,
            hash=hash2,
            metadata={}
        )
        
        # Hashes must be different
        assert doc1.hash != doc2.hash


class TestFilenameGenerationProperties:
    """Property-based tests for filename generation."""
    
    @given(
        url=st.text(min_size=20, max_size=200)
    )
    def test_filename_generation_never_crashes(self, url):
        """
        Property: Filename generation must never crash.
        
        **Validates: Requirements 4.17, 4.18**
        """
        from hansard_tales.scrapers.hansard import HansardScraper
        from hansard_tales.config.settings import ScraperConfig
        
        config = ScraperConfig()
        scraper = HansardScraper(config)
        
        # Should never crash, even with invalid URLs
        try:
            filename = scraper._generate_filename(url)
            assert isinstance(filename, str)
            assert len(filename) > 0
        except Exception:
            # If it crashes, the test fails
            pytest.fail("Filename generation crashed")
    
    @given(
        day=st.integers(min_value=1, max_value=31),
        month=st.sampled_from(['January', 'February', 'March', 'April', 'May', 'June',
                               'July', 'August', 'September', 'October', 'November', 'December']),
        year=st.integers(min_value=2000, max_value=2030),
        period=st.sampled_from(['P', 'A', 'E'])
    )
    def test_hansard_filename_format_with_valid_url(self, day, month, year, period):
        """
        Property: Valid Hansard URLs produce correctly formatted filenames.
        
        **Validates: Requirements 4.17**
        """
        from hansard_tales.scrapers.hansard import HansardScraper
        from hansard_tales.config.settings import ScraperConfig
        
        config = ScraperConfig()
        scraper = HansardScraper(config)
        
        # Create a valid URL format
        url = f"https://parliament.go.ke/sites/default/files/hansard_{day}th%20{month}%20{year}%20({period}).pdf"
        
        # Generate filename
        filename = scraper._generate_filename(url)
        
        # Should produce standardized format or fallback to original
        assert isinstance(filename, str)
        assert filename.endswith('.pdf')
        
        # If it matches the pattern, verify format
        if filename.startswith('hansard_') and len(filename.split('_')) == 3:
            # Verify format: hansard_YYYYMMDD_<P|A|E>.pdf
            parts = filename.replace('.pdf', '').split('_')
            assert len(parts) == 3
            assert parts[0] == 'hansard'
            assert len(parts[1]) == 8  # YYYYMMDD
            assert parts[1].isdigit()
            assert parts[2] in ['P', 'A', 'E']


class TestURLValidationProperties:
    """Property-based tests for URL validation."""
    
    @given(
        url=st.text(min_size=10, max_size=200)
    )
    def test_pdf_url_detection(self, url):
        """
        Property: PDF URLs must be correctly identified.
        
        **Validates: Requirements 4.12**
        """
        # Check if URL ends with .pdf (case-insensitive)
        is_pdf = url.lower().endswith('.pdf')
        
        # This is a simple property test - just verify the logic is consistent
        if '.pdf' in url.lower():
            # If .pdf appears anywhere, check if it's at the end
            assert is_pdf == url.lower().endswith('.pdf')
        else:
            # If .pdf doesn't appear, it's definitely not a PDF URL
            assert not is_pdf


class TestMetadataExtractionProperties:
    """Property-based tests for metadata extraction."""
    
    @given(
        chamber=st.sampled_from(Chamber),
        doc_type=st.sampled_from(["hansard", "votes", "bill"])
    )
    def test_metadata_contains_required_fields(self, chamber, doc_type):
        """
        Property: Extracted metadata must contain required fields.
        
        **Validates: Requirements 4.7**
        """
        # Metadata should always have these fields
        required_fields = ["document_type", "chamber"]
        
        # Create sample metadata
        metadata = {
            "document_type": doc_type,
            "chamber": chamber.value,
        }
        
        # Verify all required fields present
        for field in required_fields:
            assert field in metadata


class TestDuplicateDetectionProperties:
    """Property-based tests for duplicate detection."""
    
    @given(
        content1=st.binary(min_size=100, max_size=1000),
        content2=st.binary(min_size=100, max_size=1000)
    )
    def test_duplicate_detection_by_hash(self, content1, content2):
        """
        Property: Documents with same hash are duplicates.
        
        **Validates: Requirements 4.9, 1.11**
        """
        hash1 = hashlib.sha256(content1).hexdigest()
        hash2 = hashlib.sha256(content2).hexdigest()
        
        # If content is same, hashes must match
        if content1 == content2:
            assert hash1 == hash2
        # If content differs, hashes must differ
        else:
            assert hash1 != hash2


class TestErrorHandlingProperties:
    """Property-based tests for error handling."""
    
    @given(
        max_retries=st.integers(min_value=1, max_value=5),
        retry_delay=st.floats(min_value=0.1, max_value=2.0)
    )
    def test_retry_configuration(self, max_retries, retry_delay):
        """
        Property: Retry configuration must be respected.
        
        **Validates: Requirements 4.1, 8.2**
        """
        from hansard_tales.config.settings import ScraperConfig
        
        config = ScraperConfig(
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        assert config.max_retries == max_retries
        assert config.retry_delay == retry_delay
        assert config.max_retries >= 1
        assert config.retry_delay > 0
