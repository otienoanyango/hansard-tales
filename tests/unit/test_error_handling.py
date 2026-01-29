"""
Unit tests for error handling infrastructure.

Tests exception hierarchy, error context, retry logic, and batch processing.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from hansard_tales.utils.batch import BatchProcessor, process_in_batches
from hansard_tales.utils.errors import (
    ConfigurationError,
    DataCollectionError,
    HansardTalesError,
    ProcessingError,
    StorageError,
    ValidationError,
    capture_error_context,
    log_error,
)
from hansard_tales.utils.logging import configure_logging, get_logger
from hansard_tales.utils.retry import (
    download_with_retry,
    retry_on_network_error,
    retry_on_storage_error,
    store_with_retry,
)


class TestExceptionHierarchy:
    """Test custom exception hierarchy."""

    def test_base_exception(self):
        """Test that HansardTalesError is base exception."""
        error = HansardTalesError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_data_collection_error_inherits_base(self):
        """Test that DataCollectionError inherits from base."""
        error = DataCollectionError("scraping failed")
        assert isinstance(error, HansardTalesError)
        assert isinstance(error, Exception)

    def test_processing_error_inherits_base(self):
        """Test that ProcessingError inherits from base."""
        error = ProcessingError("processing failed")
        assert isinstance(error, HansardTalesError)

    def test_storage_error_inherits_base(self):
        """Test that StorageError inherits from base."""
        error = StorageError("storage failed")
        assert isinstance(error, HansardTalesError)

    def test_configuration_error_inherits_base(self):
        """Test that ConfigurationError inherits from base."""
        error = ConfigurationError("config invalid")
        assert isinstance(error, HansardTalesError)

    def test_validation_error_inherits_base(self):
        """Test that ValidationError inherits from base."""
        error = ValidationError("validation failed")
        assert isinstance(error, HansardTalesError)


class TestErrorContext:
    """Test error context capture."""

    def test_capture_error_context_basic(self):
        """Test capturing basic error context."""
        try:
            raise ValueError("test error")
        except Exception as e:
            context = capture_error_context(
                error=e, component="test_component", operation="test_operation"
            )

        assert context.error_type == "ValueError"
        assert context.error_message == "test error"
        assert context.component == "test_component"
        assert context.operation == "test_operation"
        assert "ValueError" in context.stack_trace

    def test_capture_error_context_with_input_data(self):
        """Test capturing error context with input data."""
        try:
            raise ProcessingError("processing failed")
        except Exception as e:
            context = capture_error_context(
                error=e,
                component="processor",
                operation="process_pdf",
                input_data={"pdf_path": "/path/to/file.pdf"},
            )

        assert context.input_data == {"pdf_path": "/path/to/file.pdf"}

    def test_capture_error_context_with_state(self):
        """Test capturing error context with state."""
        try:
            raise StorageError("storage failed")
        except Exception as e:
            context = capture_error_context(
                error=e,
                component="storage",
                operation="save_document",
                state={"documents_processed": 10},
            )

        assert context.state == {"documents_processed": 10}

    def test_log_error_with_context(self, capsys):
        """Test logging error with context."""
        configure_logging(level="INFO", format="json", output="stdout")
        logger = get_logger("test")

        try:
            raise ValueError("test error")
        except Exception as e:
            context = capture_error_context(error=e, component="test", operation="test_op")
            log_error(logger, context)

        captured = capsys.readouterr()
        assert "operation_failed" in captured.out
        assert "ValueError" in captured.out
        assert "test error" in captured.out


class TestRetryLogic:
    """Test retry logic."""

    def test_retry_on_network_error_decorator(self):
        """Test retry decorator for network errors."""
        call_count = 0

        @retry_on_network_error(max_attempts=3, min_wait=0.1, max_wait=0.2)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.RequestException("network error")
            return "success"

        result = failing_function()

        assert result == "success"
        assert call_count == 3

    def test_retry_on_network_error_exhausts_retries(self):
        """Test that retry exhausts after max attempts."""
        from tenacity import RetryError

        call_count = 0

        @retry_on_network_error(max_attempts=3, min_wait=0.1, max_wait=0.2)
        def always_failing():
            nonlocal call_count
            call_count += 1
            raise requests.RequestException("network error")

        with pytest.raises(RetryError):
            always_failing()

        assert call_count == 3

    def test_retry_on_storage_error_decorator(self):
        """Test retry decorator for storage errors."""
        call_count = 0

        @retry_on_storage_error(max_attempts=3, min_wait=0.1, max_wait=0.2)
        def failing_storage():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise StorageError("storage error")
            return "saved"

        result = failing_storage()

        assert result == "saved"
        assert call_count == 2

    @patch("requests.get")
    def test_download_with_retry_success(self, mock_get):
        """Test successful download with retry."""
        mock_response = Mock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        content = download_with_retry("https://example.com/file.pdf")

        assert content == b"test content"
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_download_with_retry_retries_on_error(self, mock_get):
        """Test that download retries on network error."""
        # First two calls fail, third succeeds
        mock_response = Mock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()

        mock_get.side_effect = [
            requests.RequestException("error 1"),
            requests.RequestException("error 2"),
            mock_response,
        ]

        content = download_with_retry("https://example.com/file.pdf")

        assert content == b"test content"
        assert mock_get.call_count == 3

    def test_store_with_retry_success(self):
        """Test successful storage with retry."""
        stored_data = []

        def save_func(data):
            stored_data.append(data)

        store_with_retry("test data", save_func)

        assert stored_data == ["test data"]

    def test_store_with_retry_retries_on_error(self):
        """Test that storage retries on error."""
        call_count = 0
        stored_data = []

        def failing_save(data):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("connection failed")
            stored_data.append(data)

        store_with_retry("test data", failing_save)

        assert stored_data == ["test data"]
        assert call_count == 2


class TestBatchProcessor:
    """Test batch processing."""

    def setup_method(self):
        """Setup for each test."""
        configure_logging(level="INFO", format="json", output="stdout")
        self.logger = get_logger("test")

    def test_batch_processor_all_success(self):
        """Test batch processing with all items succeeding."""
        processor = BatchProcessor(self.logger)

        items = [1, 2, 3, 4, 5]
        results, errors = processor.process_batch(items=items, process_func=lambda x: x * 2)

        assert results == [2, 4, 6, 8, 10]
        assert errors == []

    def test_batch_processor_with_errors_continue(self):
        """Test batch processing continues on error."""
        processor = BatchProcessor(self.logger)

        def process_item(x):
            if x == 3:
                raise ValueError("error on 3")
            return x * 2

        items = [1, 2, 3, 4, 5]
        results, errors = processor.process_batch(
            items=items, process_func=process_item, continue_on_error=True
        )

        assert results == [2, 4, 8, 10]
        assert len(errors) == 1
        assert errors[0][0] == 3
        assert isinstance(errors[0][1], ValueError)

    def test_batch_processor_stops_on_error(self):
        """Test batch processing stops on error when configured."""
        processor = BatchProcessor(self.logger)

        def process_item(x):
            if x == 3:
                raise ValueError("error on 3")
            return x * 2

        items = [1, 2, 3, 4, 5]

        with pytest.raises(ValueError):
            processor.process_batch(items=items, process_func=process_item, continue_on_error=False)

    def test_batch_processor_with_progress(self, capsys):
        """Test batch processing with progress logging."""
        processor = BatchProcessor(self.logger)

        items = list(range(1, 26))  # 25 items
        results, errors = processor.process_batch_with_progress(
            items=items, process_func=lambda x: x * 2, log_interval=10
        )

        assert len(results) == 25
        assert errors == []

        # Check that progress was logged
        captured = capsys.readouterr()
        assert "batch_processing_progress" in captured.out

    def test_process_in_batches(self):
        """Test processing items in smaller batches."""
        items = list(range(1, 101))  # 100 items

        results, errors = process_in_batches(
            items=items, process_func=lambda x: x * 2, logger=self.logger, batch_size=25
        )

        assert len(results) == 100
        assert errors == []
        assert results[0] == 2
        assert results[-1] == 200

    def test_process_in_batches_with_errors(self):
        """Test processing in batches with some errors."""

        def process_item(x):
            if x % 10 == 0:
                raise ValueError(f"error on {x}")
            return x * 2

        items = list(range(1, 51))  # 50 items

        results, errors = process_in_batches(
            items=items,
            process_func=process_item,
            logger=self.logger,
            batch_size=10,
            continue_on_error=True,
        )

        # Should have 45 successes (50 - 5 multiples of 10)
        assert len(results) == 45
        assert len(errors) == 5
