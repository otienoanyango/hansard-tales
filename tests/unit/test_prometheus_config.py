"""
Tests for Prometheus configuration.

This module tests that the Prometheus configuration file is valid and
contains the expected scrape targets and settings.
"""

from pathlib import Path

import pytest
import yaml


class TestPrometheusConfig:
    """Test suite for Prometheus configuration."""

    @pytest.fixture
    def config_path(self):
        """Path to Prometheus configuration file."""
        return Path("config/prometheus.yml")

    @pytest.fixture
    def config(self, config_path):
        """Load Prometheus configuration."""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def test_config_file_exists(self, config_path):
        """Test that Prometheus configuration file exists."""
        assert config_path.exists(), "Prometheus config file should exist"
        assert config_path.is_file(), "Prometheus config should be a file"

    def test_config_is_valid_yaml(self, config_path):
        """Test that configuration is valid YAML."""
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config is not None, "Config should parse as valid YAML"
        assert isinstance(config, dict), "Config should be a dictionary"

    def test_global_config_present(self, config):
        """Test that global configuration is present."""
        assert "global" in config, "Global config section should exist"
        global_config = config["global"]

        assert "scrape_interval" in global_config
        assert "evaluation_interval" in global_config

    def test_scrape_interval_valid(self, config):
        """Test that scrape intervals are valid."""
        global_config = config["global"]

        # Check format (should be like "15s", "1m", etc.)
        scrape_interval = global_config["scrape_interval"]
        assert isinstance(scrape_interval, str)
        assert scrape_interval.endswith("s") or scrape_interval.endswith("m")

    def test_scrape_configs_present(self, config):
        """Test that scrape configurations are present."""
        assert "scrape_configs" in config, "Scrape configs should exist"
        scrape_configs = config["scrape_configs"]

        assert isinstance(scrape_configs, list)
        assert len(scrape_configs) > 0, "Should have at least one scrape config"

    def test_hansard_tales_job_configured(self, config):
        """Test that Hansard Tales application job is configured."""
        scrape_configs = config["scrape_configs"]
        job_names = [job["job_name"] for job in scrape_configs]

        assert "hansard_tales" in job_names, "Should have hansard_tales job"

        # Find the hansard_tales job
        hansard_job = next(job for job in scrape_configs if job["job_name"] == "hansard_tales")

        # Verify it has targets
        assert "static_configs" in hansard_job
        assert len(hansard_job["static_configs"]) > 0
        assert "targets" in hansard_job["static_configs"][0]

    def test_postgres_job_configured(self, config):
        """Test that PostgreSQL job is configured."""
        scrape_configs = config["scrape_configs"]
        job_names = [job["job_name"] for job in scrape_configs]

        assert "postgres" in job_names, "Should have postgres job"

    def test_qdrant_job_configured(self, config):
        """Test that Qdrant job is configured."""
        scrape_configs = config["scrape_configs"]
        job_names = [job["job_name"] for job in scrape_configs]

        assert "qdrant" in job_names, "Should have qdrant job"

    def test_prometheus_self_monitoring_configured(self, config):
        """Test that Prometheus self-monitoring is configured."""
        scrape_configs = config["scrape_configs"]
        job_names = [job["job_name"] for job in scrape_configs]

        assert "prometheus" in job_names, "Should have prometheus self-monitoring"

    def test_retention_policy_configured(self, config):
        """Test that retention policy is configured."""
        assert "storage" in config, "Storage config should exist"
        storage = config["storage"]

        assert "tsdb" in storage, "TSDB config should exist"
        tsdb = storage["tsdb"]

        # Check retention time is set
        assert "retention.time" in tsdb, "Retention time should be configured"
        retention = tsdb["retention.time"]

        # Should be in format like "30d", "90d", etc.
        assert isinstance(retention, str)
        assert retention.endswith("d") or retention.endswith("w") or retention.endswith("y")

    def test_all_jobs_have_targets(self, config):
        """Test that all jobs have at least one target."""
        scrape_configs = config["scrape_configs"]

        for job in scrape_configs:
            job_name = job["job_name"]
            assert "static_configs" in job, f"Job {job_name} should have static_configs"

            static_configs = job["static_configs"]
            assert len(static_configs) > 0, f"Job {job_name} should have at least one static config"

            for static_config in static_configs:
                assert "targets" in static_config, f"Job {job_name} should have targets"
                assert (
                    len(static_config["targets"]) > 0
                ), f"Job {job_name} should have at least one target"

    def test_scrape_intervals_reasonable(self, config):
        """Test that scrape intervals are reasonable (not too frequent)."""
        scrape_configs = config["scrape_configs"]

        for job in scrape_configs:
            if "scrape_interval" in job:
                interval = job["scrape_interval"]
                # Extract number from string like "15s"
                if interval.endswith("s"):
                    seconds = int(interval[:-1])
                    # Should be at least 5 seconds to avoid overload
                    assert seconds >= 5, f"Job {job['job_name']} scrape interval too frequent"

    def test_metrics_path_configured_for_app(self, config):
        """Test that metrics path is configured for application."""
        scrape_configs = config["scrape_configs"]

        hansard_job = next(job for job in scrape_configs if job["job_name"] == "hansard_tales")

        # Should have metrics_path configured
        assert "metrics_path" in hansard_job
        assert hansard_job["metrics_path"] == "/metrics"


class TestPrometheusIntegration:
    """Integration tests for Prometheus configuration."""

    def test_config_compatible_with_docker_compose(self):
        """Test that config is compatible with docker-compose setup."""
        config_path = Path("config/prometheus.yml")
        docker_compose_path = Path("docker-compose.yml")

        # Both files should exist
        assert config_path.exists()
        assert docker_compose_path.exists()

        # Load docker-compose to verify prometheus service references config
        with open(docker_compose_path) as f:
            docker_config = yaml.safe_load(f)

        # Check prometheus service exists
        assert "services" in docker_config
        assert "prometheus" in docker_config["services"]

        prometheus_service = docker_config["services"]["prometheus"]

        # Check volumes mount the config file
        assert "volumes" in prometheus_service
        volumes = prometheus_service["volumes"]

        # Should mount prometheus.yml
        config_mounted = any("./config/prometheus.yml" in volume for volume in volumes)
        assert config_mounted, "Prometheus config should be mounted in docker-compose"
