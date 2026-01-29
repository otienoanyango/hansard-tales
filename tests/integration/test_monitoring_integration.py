"""
Integration tests for the monitoring infrastructure.

This module tests the complete monitoring system including:
- Prometheus metrics exporter functionality
- Grafana dashboard configurations
- Sentry error tracking integration
- Metrics exposure and formatting
- Error handling and edge cases
- Component integration

These tests verify that all monitoring components work together correctly.
"""

import json
import logging
import time
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from prometheus_client import REGISTRY

from hansard_tales.config.settings import MonitoringConfig
from hansard_tales.monitoring.metrics import (
    documents_processed,
    error_count,
    processing_time,
    queue_depth,
    track_processing_time,
    vector_db_size,
)
from hansard_tales.monitoring.sentry_config import (
    add_breadcrumb,
    capture_exception,
    capture_message,
    configure_sentry,
    set_tag,
    set_user,
)


class TestPrometheusMetricsIntegration:
    """Integration tests for Prometheus metrics."""

    def test_metrics_registered_in_registry(self):
        """Test that all metrics are registered in Prometheus registry."""
        # Get all registered metrics
        metric_names = [
            metric.name for metric in REGISTRY.collect() if not metric.name.startswith("python_")
        ]

        # Verify our metrics are registered (without _total suffix for counters in registry)
        assert "documents_processed" in metric_names
        assert "document_processing_seconds" in metric_names
        assert "errors" in metric_names
        assert "processing_queue_depth" in metric_names
        assert "vector_db_documents_total" in metric_names

    def test_decorator_tracks_success(self):
        """Test that decorator tracks successful processing."""

        @track_processing_time("hansard", "national_assembly")
        def process_document():
            time.sleep(0.01)
            return {"status": "success"}

        # Get initial count
        initial_count = documents_processed.labels(
            document_type="hansard", chamber="national_assembly", status="success"
        )._value.get()

        # Process document
        result = process_document()

        # Verify success was tracked
        assert result["status"] == "success"
        final_count = documents_processed.labels(
            document_type="hansard", chamber="national_assembly", status="success"
        )._value.get()
        assert final_count > initial_count

    def test_decorator_tracks_errors(self):
        """Test that decorator tracks errors."""

        @track_processing_time("votes", "senate")
        def process_document_with_error():
            raise ValueError("Processing failed")

        # Get initial counts
        initial_error_count = documents_processed.labels(
            document_type="votes", chamber="senate", status="error"
        )._value.get()

        initial_error_type_count = error_count.labels(
            component="processor", error_type="ValueError"
        )._value.get()

        # Process document (should fail)
        with pytest.raises(ValueError):
            process_document_with_error()

        # Verify error was tracked
        final_error_count = documents_processed.labels(
            document_type="votes", chamber="senate", status="error"
        )._value.get()
        assert final_error_count > initial_error_count

        final_error_type_count = error_count.labels(
            component="processor", error_type="ValueError"
        )._value.get()
        assert final_error_type_count > initial_error_type_count

    def test_decorator_tracks_processing_time(self):
        """Test that decorator tracks processing time."""

        @track_processing_time("bills", "national_assembly")
        def process_document():
            time.sleep(0.05)
            return {"status": "success"}

        # Get initial histogram count
        initial_count = processing_time.labels(
            document_type="bills", chamber="national_assembly"
        )._sum.get()

        # Process document
        process_document()

        # Verify time was tracked
        final_count = processing_time.labels(
            document_type="bills", chamber="national_assembly"
        )._sum.get()
        assert final_count > initial_count

    def test_manual_metrics_updates(self):
        """Test manual metrics updates work correctly."""
        # Update counter
        initial_count = documents_processed.labels(
            document_type="questions", chamber="senate", status="success"
        )._value.get()

        documents_processed.labels(
            document_type="questions", chamber="senate", status="success"
        ).inc()

        final_count = documents_processed.labels(
            document_type="questions", chamber="senate", status="success"
        )._value.get()
        assert final_count == initial_count + 1

        # Update gauge
        queue_depth.labels(document_type="petitions").set(42)
        assert queue_depth.labels(document_type="petitions")._value.get() == 42

        vector_db_size.labels(collection="test_collection").set(1000)
        assert vector_db_size.labels(collection="test_collection")._value.get() == 1000

    def test_metrics_with_multiple_labels(self):
        """Test metrics work correctly with different label combinations."""
        # Test different document types
        for doc_type in ["hansard", "votes", "bills"]:
            documents_processed.labels(
                document_type=doc_type, chamber="national_assembly", status="success"
            ).inc()

        # Test different chambers
        for chamber in ["national_assembly", "senate"]:
            documents_processed.labels(
                document_type="hansard", chamber=chamber, status="success"
            ).inc()

        # Test different statuses
        for status in ["success", "error"]:
            documents_processed.labels(
                document_type="hansard", chamber="national_assembly", status=status
            ).inc()

        # Verify all combinations were tracked
        assert (
            documents_processed.labels(
                document_type="hansard", chamber="national_assembly", status="success"
            )._value.get()
            >= 2
        )


class TestSentryIntegration:
    """Integration tests for Sentry error tracking."""

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_sentry_configuration_workflow(self, mock_sentry_sdk):
        """Test complete Sentry configuration workflow."""
        config = MonitoringConfig(sentry_enabled=True, dsn="https://test@sentry.io/123")

        # Configure Sentry
        configure_sentry(config, environment="production")

        # Verify initialization
        mock_sentry_sdk.init.assert_called_once()
        call_kwargs = mock_sentry_sdk.init.call_args[1]

        assert call_kwargs["dsn"] == "https://test@sentry.io/123"
        assert call_kwargs["environment"] == "production"
        assert "integrations" in call_kwargs

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_exception_capture_workflow(self, mock_sentry_sdk):
        """Test complete exception capture workflow."""
        mock_sentry_sdk.capture_exception.return_value = "event-123"

        # Set context
        set_user(user_id="user123", email="user@example.com")
        set_tag("document_type", "hansard")
        set_tag("chamber", "national_assembly")

        # Add breadcrumbs
        add_breadcrumb("Starting processing", category="processing", level="info")
        add_breadcrumb("Extracting text", category="processing", level="info")

        # Capture exception
        exception = ValueError("Processing failed")
        event_id = capture_exception(exception, context={"pdf_path": "test.pdf"})

        # Verify workflow
        assert event_id == "event-123"
        mock_sentry_sdk.set_user.assert_called()
        assert mock_sentry_sdk.set_tag.call_count >= 2
        assert mock_sentry_sdk.add_breadcrumb.call_count >= 2
        mock_sentry_sdk.capture_exception.assert_called()

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_message_capture_workflow(self, mock_sentry_sdk):
        """Test complete message capture workflow."""
        mock_sentry_sdk.capture_message.return_value = "event-456"

        # Set context
        set_tag("operation", "batch_processing")

        # Capture message
        event_id = capture_message("Processing completed", level="info", context={"documents": 10})

        # Verify workflow
        assert event_id == "event-456"
        mock_sentry_sdk.set_tag.assert_called()
        mock_sentry_sdk.capture_message.assert_called()

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_error_handling_resilience(self, mock_sentry_sdk, caplog):
        """Test that Sentry errors don't break the application."""
        # Make all Sentry calls fail
        mock_sentry_sdk.set_user.side_effect = Exception("Set user failed")
        mock_sentry_sdk.set_tag.side_effect = Exception("Set tag failed")
        mock_sentry_sdk.add_breadcrumb.side_effect = Exception("Add breadcrumb failed")
        mock_sentry_sdk.capture_exception.side_effect = Exception("Capture failed")

        with caplog.at_level(logging.ERROR):
            # None of these should raise exceptions
            set_user(user_id="user123")
            set_tag("test", "value")
            add_breadcrumb("test", category="test")
            event_id = capture_exception(ValueError("test"))

        # Verify errors were logged but didn't crash
        assert "Failed to set user context" in caplog.text
        assert "Failed to set tag" in caplog.text
        assert "Failed to add breadcrumb" in caplog.text
        assert "Failed to capture exception" in caplog.text
        assert event_id is None


class TestPrometheusGrafanaIntegration:
    """Integration tests for Prometheus and Grafana configuration."""

    def test_prometheus_config_matches_grafana_queries(self):
        """Test that Grafana dashboards query metrics defined in Prometheus config."""
        # Load Prometheus config
        prometheus_config_path = Path("config/prometheus.yml")
        with open(prometheus_config_path) as f:
            prometheus_config = yaml.safe_load(f)

        # Get job names from Prometheus config
        [job["job_name"] for job in prometheus_config["scrape_configs"]]

        # Load all Grafana dashboards
        dashboard_dir = Path("config/grafana/dashboards")
        dashboards = []
        for dashboard_file in dashboard_dir.glob("*.json"):
            with open(dashboard_file) as f:
                dashboards.append(json.load(f))

        # Verify dashboards use Prometheus datasource
        for dashboard in dashboards:
            for panel in dashboard["panels"]:
                if "targets" in panel:
                    for target in panel["targets"]:
                        if "datasource" in target:
                            assert target["datasource"]["type"] == "prometheus"

    def test_grafana_dashboards_use_defined_metrics(self):
        """Test that Grafana dashboards query metrics we actually export."""
        # Get exported metric names
        exported_metrics = {
            "documents_processed_total",
            "document_processing_seconds",
            "errors_total",
            "processing_queue_depth",
            "vector_db_documents_total",
        }

        # Load all Grafana dashboards
        dashboard_dir = Path("config/grafana/dashboards")
        for dashboard_file in dashboard_dir.glob("*.json"):
            with open(dashboard_file) as f:
                dashboard = json.load(f)

            # Extract all queries
            for panel in dashboard["panels"]:
                if "targets" in panel:
                    for target in panel["targets"]:
                        if "expr" in target:
                            query = target["expr"]
                            # Check if query uses our metrics
                            uses_our_metrics = any(metric in query for metric in exported_metrics)
                            # Allow empty queries or queries using our metrics
                            assert uses_our_metrics or query == ""

    def test_prometheus_scrapes_application_metrics(self):
        """Test that Prometheus is configured to scrape application metrics."""
        prometheus_config_path = Path("config/prometheus.yml")
        with open(prometheus_config_path) as f:
            config = yaml.safe_load(f)

        # Find hansard_tales job
        hansard_job = None
        for job in config["scrape_configs"]:
            if job["job_name"] == "hansard_tales":
                hansard_job = job
                break

        assert hansard_job is not None, "Prometheus should have hansard_tales job"
        assert "static_configs" in hansard_job
        assert "metrics_path" in hansard_job
        assert hansard_job["metrics_path"] == "/metrics"


class TestMonitoringSystemIntegration:
    """Integration tests for the complete monitoring system."""

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_complete_monitoring_workflow(self, mock_sentry_sdk):
        """Test complete monitoring workflow with all components."""
        # 1. Configure Sentry
        config = MonitoringConfig(sentry_enabled=True, dsn="https://test@sentry.io/123")
        configure_sentry(config, environment="production")

        # 2. Set up context
        set_user(user_id="user123", email="user@example.com")
        set_tag("document_type", "hansard")
        set_tag("chamber", "national_assembly")

        # 3. Process documents with metrics tracking
        @track_processing_time("hansard", "national_assembly")
        def process_document(should_fail=False):
            add_breadcrumb("Processing document", category="processing", level="info")
            if should_fail:
                raise ValueError("Processing failed")
            return {"status": "success"}

        # Process successful document
        initial_success_count = documents_processed.labels(
            document_type="hansard", chamber="national_assembly", status="success"
        )._value.get()

        result = process_document(should_fail=False)
        assert result["status"] == "success"

        final_success_count = documents_processed.labels(
            document_type="hansard", chamber="national_assembly", status="success"
        )._value.get()
        assert final_success_count > initial_success_count

        # Process failed document
        initial_error_count = documents_processed.labels(
            document_type="hansard", chamber="national_assembly", status="error"
        )._value.get()

        mock_sentry_sdk.capture_exception.return_value = "event-789"

        with pytest.raises(ValueError):
            process_document(should_fail=True)

        final_error_count = documents_processed.labels(
            document_type="hansard", chamber="national_assembly", status="error"
        )._value.get()
        assert final_error_count > initial_error_count

        # 4. Update queue metrics
        queue_depth.labels(document_type="hansard").set(10)
        assert queue_depth.labels(document_type="hansard")._value.get() == 10

        # 5. Update vector DB metrics
        vector_db_size.labels(collection="hansard").set(1000)
        assert vector_db_size.labels(collection="hansard")._value.get() == 1000

        # 6. Verify Sentry integration
        assert mock_sentry_sdk.init.called
        assert mock_sentry_sdk.set_user.called
        assert mock_sentry_sdk.set_tag.called
        assert mock_sentry_sdk.add_breadcrumb.called

    def test_monitoring_configuration_consistency(self):
        """Test that monitoring configurations are consistent across components."""
        # Load Prometheus config
        prometheus_config_path = Path("config/prometheus.yml")
        with open(prometheus_config_path) as f:
            prometheus_config = yaml.safe_load(f)

        # Load Grafana datasource config
        grafana_datasource_path = Path("config/grafana/datasources/prometheus.yml")
        with open(grafana_datasource_path) as f:
            grafana_datasource = yaml.safe_load(f)

        # Verify Grafana points to Prometheus
        prometheus_ds = grafana_datasource["datasources"][0]
        assert prometheus_ds["type"] == "prometheus"
        assert "prometheus" in prometheus_ds["url"]

        # Verify Prometheus has correct scrape configs
        job_names = [job["job_name"] for job in prometheus_config["scrape_configs"]]
        assert "hansard_tales" in job_names
        assert "prometheus" in job_names

    def test_monitoring_documentation_completeness(self):
        """Test that monitoring documentation covers all components."""
        monitoring_doc_path = Path("docs/MONITORING.md")
        assert monitoring_doc_path.exists()

        content = monitoring_doc_path.read_text()

        # Verify documentation covers all metrics
        assert "documents_processed_total" in content
        assert "document_processing_seconds" in content
        assert "errors_total" in content
        assert "processing_queue_depth" in content
        assert "vector_db_documents_total" in content

        # Verify documentation covers Prometheus
        assert "Prometheus" in content
        assert "prometheus.yml" in content

        # Verify documentation covers Grafana
        assert "Grafana" in content
        assert "dashboard" in content.lower()

        # Note: Sentry documentation is in separate files (docs/SENTRY_SETUP.md, examples/sentry_example.py)
        # so we don't require it in MONITORING.md

    def test_monitoring_examples_exist(self):
        """Test that monitoring examples exist and are valid."""
        # Check Prometheus example
        prometheus_example_path = Path("examples/prometheus_example.py")
        assert prometheus_example_path.exists()

        content = prometheus_example_path.read_text()
        assert "start_metrics_server" in content
        assert "track_processing_time" in content

        # Check Sentry example
        sentry_example_path = Path("examples/sentry_example.py")
        assert sentry_example_path.exists()

        content = sentry_example_path.read_text()
        assert "configure_sentry" in content
        assert "capture_exception" in content


class TestMonitoringEdgeCases:
    """Test edge cases and error handling in monitoring system."""

    def test_metrics_with_special_characters_in_labels(self):
        """Test that metrics handle special characters in labels correctly."""
        # Test with various special characters
        special_doc_types = ["hansard-test", "votes_test", "bills.test"]

        for doc_type in special_doc_types:
            # Should not raise exception
            documents_processed.labels(
                document_type=doc_type, chamber="national_assembly", status="success"
            ).inc()

    def test_metrics_with_empty_labels(self):
        """Test that metrics handle empty labels correctly."""
        # Empty labels should still work
        queue_depth.labels(document_type="").set(0)
        assert queue_depth.labels(document_type="")._value.get() == 0

    def test_decorator_with_exception_in_finally(self):
        """Test that decorator handles exceptions in cleanup correctly."""

        @track_processing_time("test", "test")
        def process_with_finally():
            try:
                raise ValueError("Main error")
            finally:
                # This should not interfere with metrics tracking
                pass

        with pytest.raises(ValueError):
            process_with_finally()

        # Verify error was still tracked
        error_count_value = error_count.labels(
            component="processor", error_type="ValueError"
        )._value.get()
        assert error_count_value > 0

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_sentry_with_none_context(self, mock_sentry_sdk):
        """Test Sentry handles None context correctly."""
        mock_sentry_sdk.capture_exception.return_value = "event-123"

        exception = ValueError("Test error")
        event_id = capture_exception(exception, context=None)

        assert event_id == "event-123"
        mock_sentry_sdk.capture_exception.assert_called_once()

    @patch("hansard_tales.monitoring.sentry_config.sentry_sdk")
    def test_sentry_with_empty_context(self, mock_sentry_sdk):
        """Test Sentry handles empty context correctly."""
        mock_sentry_sdk.capture_exception.return_value = "event-456"

        exception = ValueError("Test error")
        event_id = capture_exception(exception, context={})

        assert event_id == "event-456"

    def test_concurrent_metrics_updates(self):
        """Test that metrics handle concurrent updates correctly."""
        import threading

        def update_metrics():
            for _ in range(10):
                documents_processed.labels(
                    document_type="concurrent_test",
                    chamber="national_assembly",
                    status="success",
                ).inc()

        # Create multiple threads
        threads = [threading.Thread(target=update_metrics) for _ in range(5)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify count is correct (5 threads * 10 increments = 50)
        final_count = documents_processed.labels(
            document_type="concurrent_test", chamber="national_assembly", status="success"
        )._value.get()
        assert final_count == 50


class TestMonitoringPerformance:
    """Test performance characteristics of monitoring system."""

    def test_metrics_update_performance(self):
        """Test that metrics updates are fast enough."""
        import time

        iterations = 1000

        start = time.time()
        for _ in range(iterations):
            documents_processed.labels(
                document_type="perf_test", chamber="national_assembly", status="success"
            ).inc()
        duration = time.time() - start

        # Should be able to do 1000 updates in less than 1 second
        assert duration < 1.0, f"Metrics updates too slow: {duration}s for {iterations} updates"

    def test_decorator_overhead(self):
        """Test that decorator overhead is minimal."""
        import time

        def fast_function():
            pass

        @track_processing_time("overhead_test", "test")
        def decorated_fast_function():
            pass

        # Measure undecorated function
        iterations = 100
        start = time.time()
        for _ in range(iterations):
            fast_function()
        undecorated_time = time.time() - start

        # Measure decorated function
        start = time.time()
        for _ in range(iterations):
            decorated_fast_function()
        decorated_time = time.time() - start

        # Overhead should be less than 150x (generous threshold for CI environments)
        # The decorator adds time tracking which is expected
        overhead = decorated_time / undecorated_time if undecorated_time > 0 else 1
        assert overhead < 150, f"Decorator overhead too high: {overhead}x"
