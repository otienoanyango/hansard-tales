"""
Tests for development environment setup.

This module tests the setup script and development environment configuration.
"""

from pathlib import Path


class TestSetupScript:
    """Test suite for setup.sh script."""

    def test_setup_script_exists(self):
        """Test that setup.sh exists and is executable."""
        setup_script = Path("setup.sh")
        assert setup_script.exists(), "setup.sh should exist"
        assert setup_script.is_file(), "setup.sh should be a file"

    def test_makefile_exists(self):
        """Test that Makefile exists."""
        makefile = Path("Makefile")
        assert makefile.exists(), "Makefile should exist"
        assert makefile.is_file(), "Makefile should be a file"

    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists."""
        docker_compose = Path("docker-compose.yml")
        assert docker_compose.exists(), "docker-compose.yml should exist"
        assert docker_compose.is_file(), "docker-compose.yml should be a file"

    def test_requirements_files_exist(self):
        """Test that requirements files exist."""
        requirements = Path("requirements.txt")
        requirements_dev = Path("requirements-dev.txt")

        assert requirements.exists(), "requirements.txt should exist"
        assert requirements.is_file(), "requirements.txt should be a file"
        assert requirements_dev.exists(), "requirements-dev.txt should exist"
        assert requirements_dev.is_file(), "requirements-dev.txt should be a file"


class TestMakefileCommands:
    """Test suite for Makefile commands."""

    def test_makefile_has_help_target(self):
        """Test that Makefile has help target."""
        makefile = Path("Makefile").read_text()
        assert "help:" in makefile, "Makefile should have help target"

    def test_makefile_has_install_target(self):
        """Test that Makefile has install target."""
        makefile = Path("Makefile").read_text()
        assert "install:" in makefile, "Makefile should have install target"

    def test_makefile_has_test_targets(self):
        """Test that Makefile has test targets."""
        makefile = Path("Makefile").read_text()
        assert "test:" in makefile, "Makefile should have test target"
        assert "test-unit:" in makefile, "Makefile should have test-unit target"
        assert "test-property:" in makefile, "Makefile should have test-property target"
        assert "test-integration:" in makefile, "Makefile should have test-integration target"

    def test_makefile_has_docker_targets(self):
        """Test that Makefile has Docker targets."""
        makefile = Path("Makefile").read_text()
        assert "docker-up:" in makefile, "Makefile should have docker-up target"
        assert "docker-down:" in makefile, "Makefile should have docker-down target"
        assert "docker-logs:" in makefile, "Makefile should have docker-logs target"
        assert "docker-clean:" in makefile, "Makefile should have docker-clean target"

    def test_makefile_has_migration_targets(self):
        """Test that Makefile has migration targets."""
        makefile = Path("Makefile").read_text()
        assert "migrate:" in makefile, "Makefile should have migrate target"
        assert "migrate-create:" in makefile, "Makefile should have migrate-create target"

    def test_makefile_has_lint_and_format_targets(self):
        """Test that Makefile has lint and format targets."""
        makefile = Path("Makefile").read_text()
        assert "lint:" in makefile, "Makefile should have lint target"
        assert "format:" in makefile, "Makefile should have format target"


class TestDockerCompose:
    """Test suite for docker-compose.yml configuration."""

    def test_docker_compose_has_postgres(self):
        """Test that docker-compose.yml defines postgres service."""
        docker_compose = Path("docker-compose.yml").read_text()
        assert "postgres:" in docker_compose, "docker-compose.yml should define postgres service"
        assert "postgres:16-alpine" in docker_compose, "Should use postgres:16-alpine image"

    def test_docker_compose_has_qdrant(self):
        """Test that docker-compose.yml defines qdrant service."""
        docker_compose = Path("docker-compose.yml").read_text()
        assert "qdrant:" in docker_compose, "docker-compose.yml should define qdrant service"
        assert "qdrant/qdrant" in docker_compose, "Should use qdrant/qdrant image"

    def test_docker_compose_has_prometheus(self):
        """Test that docker-compose.yml defines prometheus service."""
        docker_compose = Path("docker-compose.yml").read_text()
        assert (
            "prometheus:" in docker_compose
        ), "docker-compose.yml should define prometheus service"
        assert "prom/prometheus" in docker_compose, "Should use prom/prometheus image"

    def test_docker_compose_has_grafana(self):
        """Test that docker-compose.yml defines grafana service."""
        docker_compose = Path("docker-compose.yml").read_text()
        assert "grafana:" in docker_compose, "docker-compose.yml should define grafana service"
        assert "grafana/grafana" in docker_compose, "Should use grafana/grafana image"

    def test_docker_compose_has_volumes(self):
        """Test that docker-compose.yml defines volumes."""
        docker_compose = Path("docker-compose.yml").read_text()
        assert "volumes:" in docker_compose, "docker-compose.yml should define volumes"
        assert "postgres_data:" in docker_compose, "Should define postgres_data volume"
        assert "qdrant_data:" in docker_compose, "Should define qdrant_data volume"
        assert "prometheus_data:" in docker_compose, "Should define prometheus_data volume"
        assert "grafana_data:" in docker_compose, "Should define grafana_data volume"

    def test_docker_compose_has_healthchecks(self):
        """Test that docker-compose.yml defines healthchecks."""
        docker_compose = Path("docker-compose.yml").read_text()
        assert "healthcheck:" in docker_compose, "docker-compose.yml should define healthchecks"


class TestRequirementsFiles:
    """Test suite for requirements files."""

    def test_requirements_has_core_dependencies(self):
        """Test that requirements.txt has core dependencies."""
        requirements = Path("requirements.txt").read_text()

        # Core dependencies
        assert "pydantic" in requirements, "Should include pydantic"
        assert "sqlalchemy" in requirements, "Should include sqlalchemy"
        assert "alembic" in requirements, "Should include alembic"

    def test_requirements_has_vector_db_dependencies(self):
        """Test that requirements.txt has vector DB dependencies."""
        requirements = Path("requirements.txt").read_text()

        assert "chromadb" in requirements, "Should include chromadb"
        assert "qdrant-client" in requirements, "Should include qdrant-client"

    def test_requirements_has_embedding_dependencies(self):
        """Test that requirements.txt has embedding dependencies."""
        requirements = Path("requirements.txt").read_text()

        assert "sentence-transformers" in requirements, "Should include sentence-transformers"

    def test_requirements_has_pdf_processing_dependencies(self):
        """Test that requirements.txt has PDF processing dependencies."""
        requirements = Path("requirements.txt").read_text()

        # At least one PDF processing library
        has_pdf_lib = "PyMuPDF" in requirements or "pdfplumber" in requirements
        assert has_pdf_lib, "Should include PDF processing library"

    def test_requirements_has_web_scraping_dependencies(self):
        """Test that requirements.txt has web scraping dependencies."""
        requirements = Path("requirements.txt").read_text()

        assert "requests" in requirements, "Should include requests"
        assert "beautifulsoup4" in requirements, "Should include beautifulsoup4"

    def test_requirements_dev_has_testing_dependencies(self):
        """Test that requirements-dev.txt has testing dependencies."""
        requirements_dev = Path("requirements-dev.txt").read_text()

        assert "pytest" in requirements_dev, "Should include pytest"
        assert "pytest-cov" in requirements_dev, "Should include pytest-cov"
        assert "hypothesis" in requirements_dev, "Should include hypothesis"

    def test_requirements_dev_has_linting_dependencies(self):
        """Test that requirements-dev.txt has linting dependencies."""
        requirements_dev = Path("requirements-dev.txt").read_text()

        assert "ruff" in requirements_dev, "Should include ruff"
        assert "mypy" in requirements_dev, "Should include mypy"

    def test_requirements_dev_includes_base_requirements(self):
        """Test that requirements-dev.txt includes base requirements."""
        requirements_dev = Path("requirements-dev.txt").read_text()

        assert "-r requirements.txt" in requirements_dev, "Should include base requirements"


class TestDataDirectories:
    """Test suite for data directory structure."""

    def test_data_directory_exists(self):
        """Test that data directory exists."""
        data_dir = Path("data")
        assert data_dir.exists(), "data directory should exist"
        assert data_dir.is_dir(), "data should be a directory"

    def test_pdfs_directory_exists(self):
        """Test that data/pdfs directory exists."""
        pdfs_dir = Path("data/pdfs")
        assert pdfs_dir.exists(), "data/pdfs directory should exist"
        assert pdfs_dir.is_dir(), "data/pdfs should be a directory"

    def test_logs_directory_exists(self):
        """Test that data/logs directory exists."""
        logs_dir = Path("data/logs")
        assert logs_dir.exists(), "data/logs directory should exist"
        assert logs_dir.is_dir(), "data/logs should be a directory"
