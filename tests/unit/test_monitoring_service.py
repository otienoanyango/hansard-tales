"""
Unit tests for MonitoringService.

Tests cover:
- Metric recording
- Log formatting
- Error logging
- Metrics endpoint
"""

from unittest.mock import MagicMock, patch

import pytest

from hansard_tales.monitoring.service import (
    MonitoringService,
    get_monitoring_service,
)


class TestMonitoringService:
    """Test suite for MonitoringService."""

    def test_initialization(self):
        """Test MonitoringService initialization."""
        service = MonitoringService()

        assert service is not None
        assert service.logger is not None

    def test_track_statement_processed(self):
        """Test statement processing tracking."""
        service = MonitoringService()

        # Should not raise
        service.track_statement_processed(
            status="success",
            statement_type="substantive",
            mp_id="mp-123",
            quality_score=85.5,
        )

        service.track_statement_processed(
            status="error",
            statement_type="filler",
        )

    def test_track_stage_duration(self):
        """Test stage duration tracking."""
        service = MonitoringService()

        # Should not raise
        service.track_stage_duration(
            stage="segmentation",
            duration=2.5,
            items_processed=150,
            success=True,
        )

        service.track_stage_duration(
            stage="classification",
            duration=1.2,
            items_processed=0,
            success=False,
        )

    def test_track_llm_call(self):
        """Test LLM call tracking."""
        service = MonitoringService()

        # Should not raise
        service.track_llm_call(
            model="claude-3-5-haiku-20241022",
            status="success",
            input_tokens=500,
            output_tokens=200,
            cost_usd=0.001,
            duration=1.2,
        )

        service.track_llm_call(
            model="claude-3-5-haiku-20241022",
            status="error",
            input_tokens=500,
            output_tokens=0,
        )

    def test_track_error(self):
        """Test error tracking."""
        service = MonitoringService()

        error = ValueError("Test error")

        # Should not raise
        service.track_error(
            stage="llm_analysis",
            error_type="ValueError",
            error=error,
            context={"statement_id": "stmt-123"},
        )

        service.track_error(
            stage="segmentation",
            error_type="RuntimeError",
            error=RuntimeError("Another error"),
        )

    def test_track_mp_identification(self):
        """Test MP identification tracking."""
        service = MonitoringService()

        # Should not raise
        service.track_mp_identification(
            status="success",
            confidence=0.95,
            mp_name="Hon. John Doe",
        )

        service.track_mp_identification(
            status="failed",
        )

    def test_track_citation_verification(self):
        """Test citation verification tracking."""
        service = MonitoringService()

        # Should not raise
        service.track_citation_verification(
            status="verified",
            similarity_score=0.98,
            source_id="stmt-456",
        )

        service.track_citation_verification(
            status="unverified",
            similarity_score=0.65,
        )

    def test_track_bill_mention(self):
        """Test bill mention tracking."""
        service = MonitoringService()

        # Should not raise
        service.track_bill_mention(
            confidence="high",
            bill_title="Finance Bill, 2024",
            mention_text="The Finance Bill",
        )

        service.track_bill_mention(
            confidence="low",
        )

    def test_start_end_processing(self):
        """Test processing start/end tracking."""
        service = MonitoringService()

        # Should not raise
        service.start_processing()
        service.end_processing()

    def test_track_processing_decorator_success(self):
        """Test processing decorator with successful function."""
        service = MonitoringService()

        @service.track_processing_decorator("test_stage")
        def successful_function():
            return [1, 2, 3]

        result = successful_function()

        assert result == [1, 2, 3]

    def test_track_processing_decorator_error(self):
        """Test processing decorator with failing function."""
        service = MonitoringService()

        @service.track_processing_decorator("test_stage")
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

    def test_track_processing_decorator_non_list_result(self):
        """Test processing decorator with non-list result."""
        service = MonitoringService()

        @service.track_processing_decorator("test_stage")
        def single_result_function():
            return "result"

        result = single_result_function()

        assert result == "result"

    def test_get_metrics_endpoint_default(self):
        """Test metrics endpoint with default port."""
        service = MonitoringService()

        endpoint = service.get_metrics_endpoint()

        assert "http://localhost:" in endpoint
        assert "/metrics" in endpoint

    @patch("hansard_tales.config.settings.get_config")
    def test_get_metrics_endpoint_custom_port(self, mock_get_config):
        """Test metrics endpoint with custom port."""
        mock_config = MagicMock()
        mock_config.monitoring.prometheus_port = 8080
        mock_get_config.return_value = mock_config

        service = MonitoringService()
        endpoint = service.get_metrics_endpoint()

        assert endpoint == "http://localhost:8080/metrics"

    def test_get_monitoring_service_singleton(self):
        """Test global monitoring service singleton."""
        service1 = get_monitoring_service()
        service2 = get_monitoring_service()

        assert service1 is service2


class TestMetricRecording:
    """Test metric recording functionality."""

    def test_statements_processed_counter(self):
        """Test statements_processed counter increments."""
        from hansard_tales.monitoring.service import statements_processed

        # Get initial value
        initial_value = statements_processed.labels(
            status="success",
            type="substantive",
        )._value.get()

        # Track statement
        service = MonitoringService()
        service.track_statement_processed("success", "substantive")

        # Verify increment
        new_value = statements_processed.labels(
            status="success",
            type="substantive",
        )._value.get()

        assert new_value == initial_value + 1

    def test_llm_api_calls_counter(self):
        """Test llm_api_calls counter increments."""
        from hansard_tales.monitoring.service import llm_api_calls

        # Get initial value
        initial_value = llm_api_calls.labels(
            model="test-model",
            status="success",
        )._value.get()

        # Track LLM call
        service = MonitoringService()
        service.track_llm_call(
            model="test-model",
            status="success",
            input_tokens=100,
            output_tokens=50,
        )

        # Verify increment
        new_value = llm_api_calls.labels(
            model="test-model",
            status="success",
        )._value.get()

        assert new_value == initial_value + 1

    def test_llm_tokens_counter(self):
        """Test llm_tokens counter increments."""
        from hansard_tales.monitoring.service import llm_tokens

        # Get initial values
        initial_input = llm_tokens.labels(
            model="test-model",
            type="input",
        )._value.get()

        initial_output = llm_tokens.labels(
            model="test-model",
            type="output",
        )._value.get()

        # Track LLM call
        service = MonitoringService()
        service.track_llm_call(
            model="test-model",
            status="success",
            input_tokens=100,
            output_tokens=50,
        )

        # Verify increments
        new_input = llm_tokens.labels(
            model="test-model",
            type="input",
        )._value.get()

        new_output = llm_tokens.labels(
            model="test-model",
            type="output",
        )._value.get()

        assert new_input == initial_input + 100
        assert new_output == initial_output + 50

    def test_llm_cost_counter(self):
        """Test llm_cost counter increments."""
        from hansard_tales.monitoring.service import llm_cost

        # Get initial value
        initial_cost = llm_cost.labels(model="test-model")._value.get()

        # Track LLM call with cost
        service = MonitoringService()
        service.track_llm_call(
            model="test-model",
            status="success",
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.005,
        )

        # Verify increment
        new_cost = llm_cost.labels(model="test-model")._value.get()

        assert new_cost == pytest.approx(initial_cost + 0.005, rel=1e-6)

    def test_pipeline_errors_counter(self):
        """Test pipeline_errors counter increments."""
        from hansard_tales.monitoring.service import pipeline_errors

        # Get initial value
        initial_value = pipeline_errors.labels(
            stage="test_stage",
            error_type="ValueError",
        )._value.get()

        # Track error
        service = MonitoringService()
        service.track_error(
            stage="test_stage",
            error_type="ValueError",
            error=ValueError("Test"),
        )

        # Verify increment
        new_value = pipeline_errors.labels(
            stage="test_stage",
            error_type="ValueError",
        )._value.get()

        assert new_value == initial_value + 1

    def test_active_processing_gauge(self):
        """Test active_processing gauge increments/decrements."""
        from hansard_tales.monitoring.service import active_processing

        # Get initial value
        initial_value = active_processing._value.get()

        # Start processing
        service = MonitoringService()
        service.start_processing()

        # Verify increment
        after_start = active_processing._value.get()
        assert after_start == initial_value + 1

        # End processing
        service.end_processing()

        # Verify decrement
        after_end = active_processing._value.get()
        assert after_end == initial_value

    def test_mp_identifications_counter(self):
        """Test mp_identifications counter increments."""
        from hansard_tales.monitoring.service import mp_identifications

        # Get initial value
        initial_value = mp_identifications.labels(status="success")._value.get()

        # Track MP identification
        service = MonitoringService()
        service.track_mp_identification(status="success", confidence=0.95)

        # Verify increment
        new_value = mp_identifications.labels(status="success")._value.get()

        assert new_value == initial_value + 1

    def test_citation_verifications_counter(self):
        """Test citation_verifications counter increments."""
        from hansard_tales.monitoring.service import citation_verifications

        # Get initial value
        initial_value = citation_verifications.labels(status="verified")._value.get()

        # Track citation verification
        service = MonitoringService()
        service.track_citation_verification(status="verified", similarity_score=0.98)

        # Verify increment
        new_value = citation_verifications.labels(status="verified")._value.get()

        assert new_value == initial_value + 1

    def test_bill_mentions_counter(self):
        """Test bill_mentions counter increments."""
        from hansard_tales.monitoring.service import bill_mentions

        # Get initial value
        initial_value = bill_mentions.labels(confidence="high")._value.get()

        # Track bill mention
        service = MonitoringService()
        service.track_bill_mention(confidence="high", bill_title="Test Bill")

        # Verify increment
        new_value = bill_mentions.labels(confidence="high")._value.get()

        assert new_value == initial_value + 1


class TestLogFormatting:
    """Test log formatting functionality."""

    @patch("hansard_tales.monitoring.service.structlog.get_logger")
    def test_structured_logging_configuration(self, mock_get_logger):
        """Test structured logging is configured."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        service = MonitoringService()

        # Verify logger was obtained
        mock_get_logger.assert_called_once()

    @patch("hansard_tales.monitoring.service.structlog.configure")
    def test_structlog_processors(self, mock_configure):
        """Test structlog processors are configured."""
        service = MonitoringService()

        # Verify configure was called
        mock_configure.assert_called_once()

        # Verify processors were set
        call_kwargs = mock_configure.call_args[1]
        assert "processors" in call_kwargs
        assert len(call_kwargs["processors"]) > 0


class TestErrorLogging:
    """Test error logging functionality."""

    def test_error_logging_with_context(self):
        """Test error logging includes context."""
        service = MonitoringService()

        error = ValueError("Test error")
        context = {
            "statement_id": "stmt-123",
            "mp_id": "mp-456",
        }

        # Should not raise
        service.track_error(
            stage="test_stage",
            error_type="ValueError",
            error=error,
            context=context,
        )

    def test_error_logging_without_context(self):
        """Test error logging without context."""
        service = MonitoringService()

        error = RuntimeError("Test error")

        # Should not raise
        service.track_error(
            stage="test_stage",
            error_type="RuntimeError",
            error=error,
        )

    def test_error_logging_in_decorator(self):
        """Test error logging in decorator."""
        service = MonitoringService()

        @service.track_processing_decorator("test_stage")
        def failing_function():
            raise ValueError("Decorator error")

        with pytest.raises(ValueError, match="Decorator error"):
            failing_function()


class TestMetricsEndpoint:
    """Test metrics endpoint functionality."""

    def test_metrics_endpoint_format(self):
        """Test metrics endpoint URL format."""
        service = MonitoringService()

        endpoint = service.get_metrics_endpoint()

        assert endpoint.startswith("http://")
        assert "localhost" in endpoint
        assert endpoint.endswith("/metrics")

    @patch("hansard_tales.config.settings.get_config")
    def test_metrics_endpoint_with_config(self, mock_get_config):
        """Test metrics endpoint uses config."""
        mock_config = MagicMock()
        mock_config.monitoring.prometheus_port = 9999
        mock_get_config.return_value = mock_config

        service = MonitoringService()
        endpoint = service.get_metrics_endpoint()

        assert "9999" in endpoint

    @patch("hansard_tales.config.settings.get_config")
    def test_metrics_endpoint_without_monitoring_config(self, mock_get_config):
        """Test metrics endpoint falls back to default port."""
        mock_config = MagicMock()
        del mock_config.monitoring  # Remove monitoring attribute
        mock_get_config.return_value = mock_config

        service = MonitoringService()
        endpoint = service.get_metrics_endpoint()

        assert "9090" in endpoint  # Default port
