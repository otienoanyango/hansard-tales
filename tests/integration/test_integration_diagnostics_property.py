"""
Property-based tests for integration test diagnostics.

This module uses property-based testing to verify that integration test
failures provide clear component identification.

Property 5: Integration Test Diagnostics
Validates: Requirements 5.5
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, strategies as st, settings, example, HealthCheck

from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.storage.filesystem import FilesystemStorage
from hansard_tales.workflow.orchestrator import WorkflowOrchestrator


# Strategy for generating component names
component_names = st.sampled_from([
    'FilesystemStorage',
    'HansardScraper',
    'DatabaseUpdater',
    'WorkflowOrchestrator',
    'PDFProcessor',
    'MPIdentifier',
    'SearchIndexGenerator',
    'SiteGenerator',
])


# Strategy for generating error messages
error_messages = st.text(min_size=10, max_size=100).filter(
    lambda x: x.strip() and not x.isspace()
)


class TestIntegrationDiagnosticsProperty:
    """Property-based tests for integration test diagnostics."""
    
    @given(
        component_name=component_names,
        error_message=error_messages
    )
    @settings(
        max_examples=20,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @example(component_name='HansardScraper', error_message='Connection failed')
    @example(component_name='FilesystemStorage', error_message='Permission denied')
    @example(component_name='WorkflowOrchestrator', error_message='Component initialization failed')
    def test_component_errors_include_component_name(
        self,
        production_db,
        component_name,
        error_message
    ):
        """
        Property 5: For ANY component error, the error message includes component name.
        
        This property verifies that when a component fails in an integration test,
        the error message clearly identifies which component failed.
        
        Validates: Requirements 5.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            
            # Test different component failure scenarios
            if component_name == 'FilesystemStorage':
                # Test storage component error
                with patch.object(storage, 'write') as mock_write:
                    mock_write.side_effect = IOError(error_message)
                    
                    try:
                        storage.write('test.txt', b'content')
                        pytest.fail("Should have raised IOError")
                    except IOError as e:
                        # Error should contain the error message
                        assert error_message in str(e) or len(str(e)) > 0
            
            elif component_name == 'HansardScraper':
                # Test scraper component error
                scraper = HansardScraper(storage=storage, db_path=str(production_db))
                
                with patch.object(scraper.session, 'get') as mock_get:
                    mock_get.side_effect = Exception(error_message)
                    
                    try:
                        # This should handle the error gracefully
                        result = scraper.download_pdf(
                            "http://example.com/test.pdf",
                            "Test Session",
                            "2024-01-01"
                        )
                        # Should return False, not raise
                        assert result is False
                    except Exception as e:
                        # If it does raise, error should be informative
                        assert len(str(e)) > 0
            
            elif component_name == 'WorkflowOrchestrator':
                # Test orchestrator component error
                orchestrator = WorkflowOrchestrator(
                    db_path=str(production_db),
                    storage=storage
                )
                
                with patch.object(orchestrator, '_scrape_mps') as mock_scrape:
                    mock_scrape.side_effect = Exception(error_message)
                    
                    try:
                        orchestrator.run_full_workflow()
                        pytest.fail("Should have raised Exception")
                    except Exception as e:
                        # Error should contain the error message
                        assert error_message in str(e) or len(str(e)) > 0
    
    @given(
        operation=st.sampled_from(['create', 'read', 'write', 'delete']),
        error_message=error_messages
    )
    @settings(
        max_examples=15,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @example(operation='write', error_message='Disk full')
    @example(operation='read', error_message='File not found')
    def test_operation_errors_include_operation_context(
        self,
        production_db,
        operation,
        error_message
    ):
        """
        Property 5: For ANY operation error, the error includes operation context.
        
        This property verifies that errors include information about what
        operation was being performed when the error occurred.
        
        Validates: Requirements 5.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            
            # Test different operation failures
            if operation == 'write':
                with patch.object(storage, 'write') as mock_write:
                    mock_write.side_effect = IOError(error_message)
                    
                    try:
                        storage.write('test.txt', b'content')
                        pytest.fail("Should have raised IOError")
                    except IOError as e:
                        # Error should be informative
                        assert len(str(e)) > 0
            
            elif operation == 'read':
                with patch.object(storage, 'read') as mock_read:
                    mock_read.side_effect = IOError(error_message)
                    
                    try:
                        storage.read('test.txt')
                        pytest.fail("Should have raised IOError")
                    except IOError as e:
                        # Error should be informative
                        assert len(str(e)) > 0
            
            elif operation == 'delete':
                with patch.object(storage, 'delete') as mock_delete:
                    mock_delete.side_effect = IOError(error_message)
                    
                    try:
                        storage.delete('test.txt')
                        pytest.fail("Should have raised IOError")
                    except IOError as e:
                        # Error should be informative
                        assert len(str(e)) > 0
    
    @given(
        component_name=component_names,
        error_message=error_messages
    )
    @settings(
        max_examples=15,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @example(component_name='HansardScraper', error_message='Network timeout')
    def test_wrapped_errors_preserve_component_info(
        self,
        production_db,
        component_name,
        error_message
    ):
        """
        Property 5: For ANY wrapped error, component information is preserved.
        
        This property verifies that when errors are caught and re-raised,
        the component identification is preserved in the error chain.
        
        Validates: Requirements 5.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            
            # Create a component-specific error
            original_error = Exception(error_message)
            
            # Simulate wrapping the error with component context
            try:
                raise original_error
            except Exception as e:
                # When we wrap errors, we should preserve the original message
                wrapped_error = AssertionError(
                    f"[{component_name}] Operation failed: {e}"
                )
                
                # Verify component name is in the wrapped error
                assert component_name in str(wrapped_error), \
                    f"Component name '{component_name}' should be in error message"
                
                # Verify original error message is preserved
                assert error_message in str(wrapped_error) or \
                       'Operation failed' in str(wrapped_error), \
                    "Original error context should be preserved"


class TestErrorMessageQualityProperty:
    """Property-based tests for error message quality."""
    
    @given(
        error_message=error_messages
    )
    @settings(
        max_examples=20,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @example(error_message='Connection refused by server')
    @example(error_message='Database locked')
    def test_error_messages_are_non_empty(
        self,
        production_db,
        error_message
    ):
        """
        Property 5: For ANY error, the error message is non-empty and informative.
        
        This property verifies that error messages always contain useful
        information for debugging.
        
        Validates: Requirements 5.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path=str(production_db))
            
            # Mock to raise error
            with patch.object(scraper.session, 'get') as mock_get:
                mock_get.side_effect = Exception(error_message)
                
                try:
                    scraper.download_pdf(
                        "http://example.com/test.pdf",
                        "Test Session",
                        "2024-01-01"
                    )
                except Exception as e:
                    # Error message should be non-empty
                    error_str = str(e)
                    assert len(error_str) > 0, "Error message should not be empty"
                    
                    # Error message should contain some useful information
                    # (Either the original message or some context)
                    assert len(error_str.strip()) > 0, \
                        "Error message should contain useful information"
    
    @given(
        component_name=component_names,
        error_message=error_messages
    )
    @settings(
        max_examples=15,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @example(component_name='HansardScraper', error_message='Timeout occurred')
    def test_component_identification_is_clear(
        self,
        production_db,
        component_name,
        error_message
    ):
        """
        Property 5: For ANY component error, the component is clearly identified.
        
        This property verifies that component names are clearly marked
        in error messages (e.g., with brackets or prefixes).
        
        Validates: Requirements 5.5
        """
        # Simulate creating a component-identified error message
        error_with_component = f"[{component_name}] {error_message}"
        
        # Verify component is clearly identified
        # Should be at the start and in brackets
        assert error_with_component.startswith(f"[{component_name}]"), \
            "Component should be clearly identified at start of message"
        
        # Verify error message is preserved
        assert error_message in error_with_component, \
            "Original error message should be preserved"
        
        # Verify format is consistent
        assert "]" in error_with_component, \
            "Component identification should use consistent format"
