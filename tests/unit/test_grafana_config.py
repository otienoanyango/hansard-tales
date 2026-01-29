"""
Tests for Grafana dashboard configurations.

This module validates that Grafana dashboard JSON files and provisioning
configurations are valid and contain expected panels and queries.
"""

import json
from pathlib import Path

import pytest
import yaml


class TestGrafanaDatasourceConfig:
    """Test Grafana datasource configuration."""

    def test_datasource_config_exists(self):
        """Test that datasource configuration file exists."""
        config_path = Path("config/grafana/datasources/prometheus.yml")
        assert config_path.exists(), "Datasource config file should exist"

    def test_datasource_config_valid_yaml(self):
        """Test that datasource configuration is valid YAML."""
        config_path = Path("config/grafana/datasources/prometheus.yml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config is not None, "Config should be valid YAML"

    def test_datasource_config_has_prometheus(self):
        """Test that datasource configuration includes Prometheus."""
        config_path = Path("config/grafana/datasources/prometheus.yml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "datasources" in config, "Config should have datasources"
        assert len(config["datasources"]) > 0, "Should have at least one datasource"

        prometheus_ds = config["datasources"][0]
        assert prometheus_ds["name"] == "Prometheus", "First datasource should be Prometheus"
        assert prometheus_ds["type"] == "prometheus", "Type should be prometheus"
        assert prometheus_ds["url"] == "http://prometheus:9090", "URL should point to Prometheus"
        assert prometheus_ds["isDefault"] is True, "Should be default datasource"


class TestGrafanaDashboardProvider:
    """Test Grafana dashboard provisioning configuration."""

    def test_dashboard_provider_exists(self):
        """Test that dashboard provider configuration exists."""
        config_path = Path("config/grafana/dashboards/dashboard-provider.yml")
        assert config_path.exists(), "Dashboard provider config should exist"

    def test_dashboard_provider_valid_yaml(self):
        """Test that dashboard provider configuration is valid YAML."""
        config_path = Path("config/grafana/dashboards/dashboard-provider.yml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config is not None, "Config should be valid YAML"

    def test_dashboard_provider_configuration(self):
        """Test dashboard provider configuration values."""
        config_path = Path("config/grafana/dashboards/dashboard-provider.yml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "providers" in config, "Config should have providers"
        assert len(config["providers"]) > 0, "Should have at least one provider"

        provider = config["providers"][0]
        assert provider["name"] == "Hansard Tales Dashboards", "Provider name should be set"
        assert provider["type"] == "file", "Provider type should be file"
        assert "path" in provider["options"], "Provider should have path option"


class TestSystemOverviewDashboard:
    """Test System Overview dashboard configuration."""

    def test_dashboard_exists(self):
        """Test that system overview dashboard exists."""
        dashboard_path = Path("config/grafana/dashboards/system-overview.json")
        assert dashboard_path.exists(), "System overview dashboard should exist"

    def test_dashboard_valid_json(self):
        """Test that dashboard is valid JSON."""
        dashboard_path = Path("config/grafana/dashboards/system-overview.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)
        assert dashboard is not None, "Dashboard should be valid JSON"

    def test_dashboard_has_title(self):
        """Test that dashboard has correct title."""
        dashboard_path = Path("config/grafana/dashboards/system-overview.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)

        assert "title" in dashboard, "Dashboard should have title"
        assert (
            dashboard["title"] == "Hansard Tales - System Overview"
        ), "Dashboard should have correct title"

    def test_dashboard_has_uid(self):
        """Test that dashboard has UID."""
        dashboard_path = Path("config/grafana/dashboards/system-overview.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)

        assert "uid" in dashboard, "Dashboard should have UID"
        assert dashboard["uid"] == "hansard-tales-overview", "Dashboard should have correct UID"

    def test_dashboard_has_panels(self):
        """Test that dashboard has panels."""
        dashboard_path = Path("config/grafana/dashboards/system-overview.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)

        assert "panels" in dashboard, "Dashboard should have panels"
        assert len(dashboard["panels"]) >= 6, "Dashboard should have at least 6 panels"

    def test_dashboard_panel_titles(self):
        """Test that dashboard has expected panel titles."""
        dashboard_path = Path("config/grafana/dashboards/system-overview.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)

        panel_titles = [panel["title"] for panel in dashboard["panels"]]

        expected_titles = [
            "Documents Processed (Success Rate)",
            "Processing Time (p95)",
            "Error Rate",
            "Queue Depth",
            "Vector DB Size",
            "Total Documents Processed",
        ]

        for expected_title in expected_titles:
            assert expected_title in panel_titles, f"Dashboard should have '{expected_title}' panel"

    def test_dashboard_has_prometheus_queries(self):
        """Test that dashboard panels have Prometheus queries."""
        dashboard_path = Path("config/grafana/dashboards/system-overview.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)

        for panel in dashboard["panels"]:
            assert "targets" in panel, f"Panel '{panel['title']}' should have targets"
            assert (
                len(panel["targets"]) > 0
            ), f"Panel '{panel['title']}' should have at least one target"

            for target in panel["targets"]:
                assert "expr" in target, f"Target in panel '{panel['title']}' should have expr"
                assert (
                    len(target["expr"]) > 0
                ), f"Target expr in panel '{panel['title']}' should not be empty"

    def test_dashboard_refresh_interval(self):
        """Test that dashboard has refresh interval set."""
        dashboard_path = Path("config/grafana/dashboards/system-overview.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)

        assert "refresh" in dashboard, "Dashboard should have refresh setting"
        assert dashboard["refresh"] == "10s", "Dashboard should refresh every 10 seconds"


class TestProcessingMetricsDashboard:
    """Test Processing Metrics dashboard configuration."""

    def test_dashboard_exists(self):
        """Test that processing metrics dashboard exists."""
        dashboard_path = Path("config/grafana/dashboards/processing-metrics.json")
        assert dashboard_path.exists(), "Processing metrics dashboard should exist"

    def test_dashboard_valid_json(self):
        """Test that dashboard is valid JSON."""
        dashboard_path = Path("config/grafana/dashboards/processing-metrics.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)
        assert dashboard is not None, "Dashboard should be valid JSON"

    def test_dashboard_has_title(self):
        """Test that dashboard has correct title."""
        dashboard_path = Path("config/grafana/dashboards/processing-metrics.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)

        assert "title" in dashboard, "Dashboard should have title"
        assert (
            dashboard["title"] == "Hansard Tales - Processing Metrics"
        ), "Dashboard should have correct title"

    def test_dashboard_has_uid(self):
        """Test that dashboard has UID."""
        dashboard_path = Path("config/grafana/dashboards/processing-metrics.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)

        assert "uid" in dashboard, "Dashboard should have UID"
        assert dashboard["uid"] == "hansard-tales-processing", "Dashboard should have correct UID"

    def test_dashboard_has_percentile_queries(self):
        """Test that dashboard has percentile queries."""
        dashboard_path = Path("config/grafana/dashboards/processing-metrics.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)

        # Find the percentiles panel
        percentile_panel = None
        for panel in dashboard["panels"]:
            if "Percentile" in panel["title"]:
                percentile_panel = panel
                break

        assert percentile_panel is not None, "Dashboard should have percentile panel"

        # Check for p50, p95, p99 queries
        queries = [target["expr"] for target in percentile_panel["targets"]]
        assert any("0.50" in q for q in queries), "Should have p50 query"
        assert any("0.95" in q for q in queries), "Should have p95 query"
        assert any("0.99" in q for q in queries), "Should have p99 query"


class TestErrorMonitoringDashboard:
    """Test Error Monitoring dashboard configuration."""

    def test_dashboard_exists(self):
        """Test that error monitoring dashboard exists."""
        dashboard_path = Path("config/grafana/dashboards/error-monitoring.json")
        assert dashboard_path.exists(), "Error monitoring dashboard should exist"

    def test_dashboard_valid_json(self):
        """Test that dashboard is valid JSON."""
        dashboard_path = Path("config/grafana/dashboards/error-monitoring.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)
        assert dashboard is not None, "Dashboard should be valid JSON"

    def test_dashboard_has_title(self):
        """Test that dashboard has correct title."""
        dashboard_path = Path("config/grafana/dashboards/error-monitoring.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)

        assert "title" in dashboard, "Dashboard should have title"
        assert (
            dashboard["title"] == "Hansard Tales - Error Monitoring"
        ), "Dashboard should have correct title"

    def test_dashboard_has_uid(self):
        """Test that dashboard has UID."""
        dashboard_path = Path("config/grafana/dashboards/error-monitoring.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)

        assert "uid" in dashboard, "Dashboard should have UID"
        assert dashboard["uid"] == "hansard-tales-errors", "Dashboard should have correct UID"

    def test_dashboard_has_error_queries(self):
        """Test that dashboard has error-related queries."""
        dashboard_path = Path("config/grafana/dashboards/error-monitoring.json")
        with open(dashboard_path) as f:
            dashboard = json.load(f)

        # Collect all queries
        all_queries = []
        for panel in dashboard["panels"]:
            for target in panel["targets"]:
                all_queries.append(target["expr"])

        # Check for errors_total metric
        assert any(
            "errors_total" in q for q in all_queries
        ), "Dashboard should query errors_total metric"


class TestDashboardConsistency:
    """Test consistency across all dashboards."""

    @pytest.fixture
    def all_dashboards(self):
        """Load all dashboard JSON files."""
        dashboard_dir = Path("config/grafana/dashboards")
        dashboards = {}

        for dashboard_file in dashboard_dir.glob("*.json"):
            with open(dashboard_file) as f:
                dashboards[dashboard_file.name] = json.load(f)

        return dashboards

    def test_all_dashboards_have_tags(self, all_dashboards):
        """Test that all dashboards have tags."""
        for name, dashboard in all_dashboards.items():
            assert "tags" in dashboard, f"Dashboard {name} should have tags"
            assert (
                "hansard-tales" in dashboard["tags"]
            ), f"Dashboard {name} should have hansard-tales tag"

    def test_all_dashboards_have_unique_uids(self, all_dashboards):
        """Test that all dashboards have unique UIDs."""
        uids = [dashboard["uid"] for dashboard in all_dashboards.values()]
        assert len(uids) == len(set(uids)), "All dashboard UIDs should be unique"

    def test_all_dashboards_use_prometheus_datasource(self, all_dashboards):
        """Test that all dashboards use Prometheus datasource."""
        for name, dashboard in all_dashboards.items():
            for panel in dashboard["panels"]:
                if "targets" in panel:
                    for target in panel["targets"]:
                        if "datasource" in target:
                            assert (
                                target["datasource"]["type"] == "prometheus"
                            ), f"Panel in {name} should use Prometheus datasource"

    def test_all_dashboards_have_time_settings(self, all_dashboards):
        """Test that all dashboards have time settings."""
        for name, dashboard in all_dashboards.items():
            assert "time" in dashboard, f"Dashboard {name} should have time settings"
            assert "from" in dashboard["time"], f"Dashboard {name} should have 'from' time"
            assert "to" in dashboard["time"], f"Dashboard {name} should have 'to' time"


class TestDocumentation:
    """Test that documentation files exist and are valid."""

    def test_readme_exists(self):
        """Test that README exists."""
        readme_path = Path("config/grafana/README.md")
        assert readme_path.exists(), "Grafana README should exist"

    def test_readme_not_empty(self):
        """Test that README is not empty."""
        readme_path = Path("config/grafana/README.md")
        content = readme_path.read_text()
        assert len(content) > 100, "README should have substantial content"

    def test_readme_has_sections(self):
        """Test that README has expected sections."""
        readme_path = Path("config/grafana/README.md")
        content = readme_path.read_text()

        expected_sections = [
            "## Overview",
            "## Available Dashboards",
            "## Metrics Reference",
            "## Setup Instructions",
            "## Troubleshooting",
        ]

        for section in expected_sections:
            assert section in content, f"README should have '{section}' section"

    def test_quickstart_exists(self):
        """Test that QUICKSTART guide exists."""
        quickstart_path = Path("config/grafana/QUICKSTART.md")
        assert quickstart_path.exists(), "Grafana QUICKSTART should exist"

    def test_quickstart_not_empty(self):
        """Test that QUICKSTART is not empty."""
        quickstart_path = Path("config/grafana/QUICKSTART.md")
        content = quickstart_path.read_text()
        assert len(content) > 100, "QUICKSTART should have substantial content"

    def test_quickstart_has_steps(self):
        """Test that QUICKSTART has step-by-step instructions."""
        quickstart_path = Path("config/grafana/QUICKSTART.md")
        content = quickstart_path.read_text()

        # Should have numbered steps
        assert "## Step 1:" in content, "QUICKSTART should have Step 1"
        assert "## Step 2:" in content, "QUICKSTART should have Step 2"
        assert "## Step 3:" in content, "QUICKSTART should have Step 3"
