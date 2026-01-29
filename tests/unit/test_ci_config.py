"""
Tests for CI/CD configuration validation.

This module validates that CI/CD configuration files are properly structured
and contain required elements for automated testing and deployment.
"""

from pathlib import Path

import yaml


class TestCIWorkflow:
    """Test suite for GitHub Actions CI workflow configuration."""

    def test_ci_workflow_exists(self):
        """Test that CI workflow file exists."""
        ci_file = Path(".github/workflows/ci.yml")
        assert ci_file.exists(), "CI workflow file should exist"

    def test_ci_workflow_valid_yaml(self):
        """Test that CI workflow is valid YAML."""
        ci_file = Path(".github/workflows/ci.yml")
        with open(ci_file) as f:
            config = yaml.safe_load(f)

        assert config is not None, "CI workflow should be valid YAML"
        assert isinstance(config, dict), "CI workflow should be a dictionary"

    def test_ci_workflow_has_required_jobs(self):
        """Test that CI workflow has required jobs."""
        ci_file = Path(".github/workflows/ci.yml")
        with open(ci_file) as f:
            config = yaml.safe_load(f)

        assert "jobs" in config, "CI workflow should have jobs"
        jobs = config["jobs"]

        # Required jobs
        assert "lint" in jobs, "CI should have lint job"
        assert "test" in jobs, "CI should have test job"
        assert "build" in jobs, "CI should have build job"

    def test_ci_workflow_lint_job_structure(self):
        """Test that lint job has correct structure."""
        ci_file = Path(".github/workflows/ci.yml")
        with open(ci_file) as f:
            config = yaml.safe_load(f)

        lint_job = config["jobs"]["lint"]

        assert "runs-on" in lint_job, "Lint job should specify runner"
        assert lint_job["runs-on"] == "ubuntu-latest"
        assert "steps" in lint_job, "Lint job should have steps"

        # Check for ruff and mypy steps
        steps = lint_job["steps"]
        step_names = [step.get("name", "") for step in steps]

        assert any("ruff" in name.lower() for name in step_names), "Lint job should run ruff"
        assert any("mypy" in name.lower() for name in step_names), "Lint job should run mypy"

    def test_ci_workflow_test_job_matrix(self):
        """Test that test job has Python version matrix."""
        ci_file = Path(".github/workflows/ci.yml")
        with open(ci_file) as f:
            config = yaml.safe_load(f)

        test_job = config["jobs"]["test"]

        assert "strategy" in test_job, "Test job should have strategy"
        assert "matrix" in test_job["strategy"], "Test job should have matrix"

        matrix = test_job["strategy"]["matrix"]
        assert "python-version" in matrix, "Matrix should specify Python versions"

        python_versions = matrix["python-version"]
        assert isinstance(python_versions, list), "Python versions should be a list"
        assert len(python_versions) >= 3, "Should test multiple Python versions"

        # Check for specific versions
        assert "3.10" in python_versions, "Should test Python 3.10"
        assert "3.11" in python_versions, "Should test Python 3.11"
        assert "3.12" in python_versions, "Should test Python 3.12"

    def test_ci_workflow_test_job_coverage(self):
        """Test that test job includes coverage reporting."""
        ci_file = Path(".github/workflows/ci.yml")
        with open(ci_file) as f:
            config = yaml.safe_load(f)

        test_job = config["jobs"]["test"]
        steps = test_job["steps"]

        # Check for pytest with coverage
        run_commands = [step.get("run", "") for step in steps if "run" in step]

        pytest_commands = [cmd for cmd in run_commands if "pytest" in cmd]
        assert len(pytest_commands) > 0, "Test job should run pytest"

        # Check for coverage flags
        pytest_cmd = pytest_commands[0]
        assert "--cov" in pytest_cmd, "Pytest should include coverage"
        assert "--cov-report" in pytest_cmd, "Pytest should generate coverage report"

    def test_ci_workflow_build_job_dependencies(self):
        """Test that build job depends on lint and test."""
        ci_file = Path(".github/workflows/ci.yml")
        with open(ci_file) as f:
            config = yaml.safe_load(f)

        build_job = config["jobs"]["build"]

        assert "needs" in build_job, "Build job should have dependencies"
        needs = build_job["needs"]

        assert "lint" in needs, "Build should depend on lint"
        assert "test" in needs, "Build should depend on test"

    def test_ci_workflow_triggers(self):
        """Test that CI workflow has correct triggers."""
        ci_file = Path(".github/workflows/ci.yml")
        with open(ci_file) as f:
            config = yaml.safe_load(f)

        # YAML parses "on" as boolean True, so we check for True key
        assert True in config, "CI workflow should have triggers"
        triggers = config[True]

        assert "push" in triggers, "CI should trigger on push"
        assert "pull_request" in triggers, "CI should trigger on pull request"

        # Check branches
        push_branches = triggers["push"]["branches"]
        assert "main" in push_branches, "CI should trigger on main branch"


class TestPyprojectConfig:
    """Test suite for pyproject.toml configuration."""

    def test_pyproject_exists(self):
        """Test that pyproject.toml exists."""
        pyproject = Path("pyproject.toml")
        assert pyproject.exists(), "pyproject.toml should exist"

    def test_pyproject_has_dev_dependencies(self):
        """Test that pyproject.toml has dev dependencies."""
        import tomli

        pyproject = Path("pyproject.toml")
        with open(pyproject, "rb") as f:
            config = tomli.load(f)

        assert "project" in config, "pyproject.toml should have project section"
        assert "optional-dependencies" in config["project"], "Should have optional dependencies"
        assert "dev" in config["project"]["optional-dependencies"], "Should have dev dependencies"

        dev_deps = config["project"]["optional-dependencies"]["dev"]

        # Check for required dev tools
        dev_deps_str = " ".join(dev_deps)
        assert "pytest" in dev_deps_str, "Should include pytest"
        assert "pytest-cov" in dev_deps_str, "Should include pytest-cov"
        assert "hypothesis" in dev_deps_str, "Should include hypothesis"
        assert "ruff" in dev_deps_str, "Should include ruff"
        assert "mypy" in dev_deps_str, "Should include mypy"

    def test_pyproject_python_version(self):
        """Test that pyproject.toml specifies correct Python version."""
        import tomli

        pyproject = Path("pyproject.toml")
        with open(pyproject, "rb") as f:
            config = tomli.load(f)

        requires_python = config["project"]["requires-python"]
        assert ">=3.10" in requires_python, "Should require Python 3.10 or higher"

    def test_pyproject_coverage_threshold(self):
        """Test that coverage threshold is set to 90%."""
        import tomli

        pyproject = Path("pyproject.toml")
        with open(pyproject, "rb") as f:
            config = tomli.load(f)

        pytest_config = config["tool"]["pytest"]["ini_options"]
        addopts = pytest_config["addopts"]

        # Check for coverage threshold
        assert any(
            "--cov-fail-under=90" in opt for opt in addopts
        ), "Coverage threshold should be 90%"


class TestCIIntegration:
    """Integration tests for CI configuration."""

    def test_lint_commands_work(self):
        """Test that lint commands can be executed."""
        import subprocess

        # Test ruff is available (use --help instead of --version)
        result = subprocess.run(["ruff", "--help"], capture_output=True, text=True)
        assert result.returncode == 0, "Ruff should be available"

    def test_test_commands_work(self):
        """Test that test commands can be executed."""
        import subprocess

        # Test pytest version
        result = subprocess.run(["pytest", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "Pytest should be available"
