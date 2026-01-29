"""
Unit tests for Sentry error tracking configuration.

Tests cover Sentry initialization, exception capture, message logging,
context management, and integration with the logging system.

Note: These tests are marked with @pytest.mark.sentry_isolated due to
logging capture issues when run with the full test suite. They should
be run separately in CI/CD.
"""

import logging
from unittest.mock import Mock, patch

import pytest

from hansard_tales.config.settings import MonitoringConfig
from hansard_tales.monitoring.sentry_config import (
    add_breadcrumb,
    capture_exception,
    capture_message,
    configure_sentry,
    flush,
    set_tag,
    set_user,
)


@pytest.mark.sentry_isolated
class TestConfigureSentry:
    """Test suite for Sentry configuration."""

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_configure_sentry_enabled(self, mock_sentry_sdk):
        """Test Sentry configuration when enabled."""
        config = MonitoringConfig(sentry_enabled=True, dsn="https://test@sentry.io/123")

        configure_sentry(config, environment="production")

        # Verify Sentry was initialized
        mock_sentry_sdk.init.assert_called_once()
        call_kwargs = mock_sentry_sdk.init.call_args[1]

        assert call_kwargs["dsn"] == "https://test@sentry.io/123"
        assert call_kwargs["environment"] == "production"
        assert call_kwargs["traces_sample_rate"] == 0.1
        assert call_kwargs["sample_rate"] == 1.0
        assert call_kwargs["enable_tracing"] is True
        assert call_kwargs["send_default_pii"] is False
        assert call_kwargs["attach_stacktrace"] is True
        assert call_kwargs["max_breadcrumbs"] == 50

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_configure_sentry_disabled(self, mock_sentry_sdk):
        """Test Sentry configuration when disabled."""
        config = MonitoringConfig(sentry_enabled=False, dsn="")

        configure_sentry(config, environment="development")

        # Verify Sentry was not initialized
        mock_sentry_sdk.init.assert_not_called()

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_configure_sentry_no_dsn(self, mock_sentry_sdk, caplog):
        """Test Sentry configuration with missing DSN."""
        caplog.clear()
        config = MonitoringConfig(sentry_enabled=True, dsn="")

        caplog.set_level(logging.WARNING)
        configure_sentry(config, environment="production")

        # Verify warning was logged
        assert any(
            "Sentry is enabled but DSN is not configured" in record.message
            for record in caplog.records
        )

        # Verify Sentry was not initialized
        mock_sentry_sdk.init.assert_not_called()

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_configure_sentry_initialization_error(self, mock_sentry_sdk, caplog):
        """Test Sentry configuration handles initialization errors."""
        caplog.clear()
        config = MonitoringConfig(sentry_enabled=True, dsn="https://test@sentry.io/123")
        mock_sentry_sdk.init.side_effect = Exception("Initialization failed")

        caplog.set_level(logging.ERROR)
        configure_sentry(config, environment="production")

        # Verify error was logged
        assert any("Failed to configure Sentry" in record.message for record in caplog.records)

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_configure_sentry_logging_integration(self, mock_sentry_sdk):
        """Test Sentry logging integration configuration."""
        config = MonitoringConfig(sentry_enabled=True, dsn="https://test@sentry.io/123")

        configure_sentry(config, environment="production")

        # Verify logging integration was configured
        call_kwargs = mock_sentry_sdk.init.call_args[1]
        integrations = call_kwargs["integrations"]

        assert len(integrations) == 1
        # LoggingIntegration should be in the list


@pytest.mark.sentry_isolated
class TestCaptureException:
    """Test suite for exception capture."""

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_capture_exception_basic(self, mock_sentry_sdk):
        """Test basic exception capture."""
        mock_sentry_sdk.capture_exception.return_value = "event-123"

        exception = ValueError("Test error")
        event_id = capture_exception(exception)

        assert event_id == "event-123"
        mock_sentry_sdk.capture_exception.assert_called_once_with(exception)

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_capture_exception_with_context(self, mock_sentry_sdk):
        """Test exception capture with context."""
        mock_sentry_sdk.capture_exception.return_value = "event-456"
        mock_sentry_sdk.push_scope.return_value.__enter__ = Mock()
        mock_sentry_sdk.push_scope.return_value.__exit__ = Mock()

        exception = ValueError("Test error")
        context = {"pdf_path": "test.pdf", "page": 5}

        event_id = capture_exception(exception, context=context, level="error")

        assert event_id == "event-456"

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_capture_exception_error_handling(self, mock_sentry_sdk, caplog):
        """Test exception capture handles errors gracefully."""
        caplog.clear()
        mock_sentry_sdk.capture_exception.side_effect = Exception("Capture failed")

        exception = ValueError("Test error")

        caplog.set_level(logging.ERROR)
        event_id = capture_exception(exception)

        assert event_id is None
        assert any(
            "Failed to capture exception in Sentry" in record.message for record in caplog.records
        )


@pytest.mark.sentry_isolated
class TestCaptureMessage:
    """Test suite for message capture."""

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_capture_message_basic(self, mock_sentry_sdk):
        """Test basic message capture."""
        mock_sentry_sdk.capture_message.return_value = "event-789"

        event_id = capture_message("Test message", level="info")

        assert event_id == "event-789"
        mock_sentry_sdk.capture_message.assert_called_once_with("Test message", level="info")

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_capture_message_with_context(self, mock_sentry_sdk):
        """Test message capture with context."""
        mock_sentry_sdk.capture_message.return_value = "event-101"
        mock_sentry_sdk.push_scope.return_value.__enter__ = Mock()
        mock_sentry_sdk.push_scope.return_value.__exit__ = Mock()

        context = {"document_count": 10, "warnings": 5}
        event_id = capture_message("Processing completed", level="warning", context=context)

        assert event_id == "event-101"

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_capture_message_error_handling(self, mock_sentry_sdk, caplog):
        """Test message capture handles errors gracefully."""
        caplog.clear()
        mock_sentry_sdk.capture_message.side_effect = Exception("Capture failed")

        caplog.set_level(logging.ERROR)
        event_id = capture_message("Test message", level="info")

        assert event_id is None
        assert any(
            "Failed to capture message in Sentry" in record.message for record in caplog.records
        )


@pytest.mark.sentry_isolated
class TestSetUser:
    """Test suite for user context."""

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_set_user_complete(self, mock_sentry_sdk):
        """Test setting complete user information."""
        set_user(user_id="user123", email="user@example.com", username="john_doe")

        mock_sentry_sdk.set_user.assert_called_once_with(
            {"id": "user123", "email": "user@example.com", "username": "john_doe"}
        )

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_set_user_minimal(self, mock_sentry_sdk):
        """Test setting minimal user information."""
        set_user(user_id="user456")

        mock_sentry_sdk.set_user.assert_called_once_with(
            {"id": "user456", "email": None, "username": None}
        )

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_set_user_error_handling(self, mock_sentry_sdk, caplog):
        """Test set_user handles errors gracefully."""
        caplog.clear()
        mock_sentry_sdk.set_user.side_effect = Exception("Set user failed")

        caplog.set_level(logging.ERROR)
        set_user(user_id="user789")

        assert any(
            "Failed to set user context in Sentry" in record.message for record in caplog.records
        )


@pytest.mark.sentry_isolated
class TestSetTag:
    """Test suite for tags."""

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_set_tag(self, mock_sentry_sdk):
        """Test setting a tag."""
        set_tag("document_type", "hansard")

        mock_sentry_sdk.set_tag.assert_called_once_with("document_type", "hansard")

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_set_tag_error_handling(self, mock_sentry_sdk, caplog):
        """Test set_tag handles errors gracefully."""
        caplog.clear()
        mock_sentry_sdk.set_tag.side_effect = Exception("Set tag failed")

        caplog.set_level(logging.ERROR)
        set_tag("chamber", "national_assembly")

        assert any("Failed to set tag in Sentry" in record.message for record in caplog.records)


@pytest.mark.sentry_isolated
class TestAddBreadcrumb:
    """Test suite for breadcrumbs."""

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_add_breadcrumb_basic(self, mock_sentry_sdk):
        """Test adding a basic breadcrumb."""
        add_breadcrumb("Test event", category="test", level="info")

        mock_sentry_sdk.add_breadcrumb.assert_called_once_with(
            message="Test event", category="test", level="info", data={}
        )

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_add_breadcrumb_with_data(self, mock_sentry_sdk):
        """Test adding a breadcrumb with data."""
        data = {"file_size": 1024, "duration": 2.5}
        add_breadcrumb("PDF downloaded", category="download", level="info", data=data)

        mock_sentry_sdk.add_breadcrumb.assert_called_once_with(
            message="PDF downloaded", category="download", level="info", data=data
        )

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_add_breadcrumb_error_handling(self, mock_sentry_sdk, caplog):
        """Test add_breadcrumb handles errors gracefully."""
        caplog.clear()
        mock_sentry_sdk.add_breadcrumb.side_effect = Exception("Add breadcrumb failed")

        caplog.set_level(logging.ERROR)
        add_breadcrumb("Test event", category="test", level="info")

        assert any(
            "Failed to add breadcrumb in Sentry" in record.message for record in caplog.records
        )


@pytest.mark.sentry_isolated
class TestFlush:
    """Test suite for flushing events."""

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_flush_success(self, mock_sentry_sdk):
        """Test successful flush."""
        mock_sentry_sdk.flush.return_value = True

        result = flush(timeout=2.0)

        assert result is True
        mock_sentry_sdk.flush.assert_called_once_with(timeout=2.0)

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_flush_failure(self, mock_sentry_sdk):
        """Test flush failure."""
        mock_sentry_sdk.flush.return_value = False

        result = flush(timeout=2.0)

        assert result is False

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_flush_error_handling(self, mock_sentry_sdk, caplog):
        """Test flush handles errors gracefully."""
        caplog.clear()
        mock_sentry_sdk.flush.side_effect = Exception("Flush failed")

        caplog.set_level(logging.ERROR)
        result = flush(timeout=2.0)

        assert result is False
        assert any("Failed to flush Sentry events" in record.message for record in caplog.records)


@pytest.mark.sentry_isolated
class TestIntegration:
    """Integration tests for Sentry functionality."""

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_complete_workflow(self, mock_sentry_sdk):
        """Test complete Sentry workflow."""
        # Configure Sentry
        config = MonitoringConfig(sentry_enabled=True, dsn="https://test@sentry.io/123")
        configure_sentry(config, environment="production")

        # Set user context
        set_user(user_id="user123", email="user@example.com")

        # Set tags
        set_tag("document_type", "hansard")
        set_tag("chamber", "national_assembly")

        # Add breadcrumbs
        add_breadcrumb("Starting processing", category="processing", level="info")
        add_breadcrumb("Extracting text", category="processing", level="info")

        # Capture exception
        mock_sentry_sdk.capture_exception.return_value = "event-123"
        exception = ValueError("Processing failed")
        event_id = capture_exception(exception, context={"pdf_path": "test.pdf"})

        # Verify all calls were made
        assert mock_sentry_sdk.init.called
        assert mock_sentry_sdk.set_user.called
        assert mock_sentry_sdk.set_tag.call_count == 2
        assert mock_sentry_sdk.add_breadcrumb.call_count == 2
        assert event_id == "event-123"

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_error_resilience(self, mock_sentry_sdk, caplog):
        """Test that Sentry errors don't break the application."""
        caplog.clear()
        # Make all Sentry calls fail
        mock_sentry_sdk.init.side_effect = Exception("Init failed")
        mock_sentry_sdk.set_user.side_effect = Exception("Set user failed")
        mock_sentry_sdk.set_tag.side_effect = Exception("Set tag failed")
        mock_sentry_sdk.add_breadcrumb.side_effect = Exception("Add breadcrumb failed")
        mock_sentry_sdk.capture_exception.side_effect = Exception("Capture failed")

        config = MonitoringConfig(sentry_enabled=True, dsn="https://test@sentry.io/123")

        caplog.set_level(logging.ERROR)
        # None of these should raise exceptions
        configure_sentry(config, environment="production")
        set_user(user_id="user123")
        set_tag("test", "value")
        add_breadcrumb("test", category="test")
        event_id = capture_exception(ValueError("test"))

        # Verify errors were logged
        messages = [record.message for record in caplog.records]
        assert any("Failed to configure Sentry" in msg for msg in messages)
        assert any("Failed to set user context" in msg for msg in messages)
        assert any("Failed to set tag" in msg for msg in messages)
        assert any("Failed to add breadcrumb" in msg for msg in messages)
        assert any("Failed to capture exception" in msg for msg in messages)

        # Verify capture_exception returned None
        assert event_id is None
