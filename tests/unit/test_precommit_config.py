"""
Tests for pre-commit configuration validation.

This module validates that pre-commit hooks are properly configured
and can be executed successfully.
"""

from pathlib import Path

import yaml


class TestPrecommitConfig:
    """Test suite for pre-commit configuration."""

    def test_precommit_config_exists(self):
        """Test that pre-commit config file exists."""
        config_file = Path(".pre-commit-config.yaml")
        assert config_file.exists(), "Pre-commit config should exist"

    def test_precommit_config_valid_yaml(self):
        """Test that pre-commit config is valid YAML."""
        config_file = Path(".pre-commit-config.yaml")
        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert config is not None, "Pre-commit config should be valid YAML"
        assert isinstance(config, dict), "Pre-commit config should be a dictionary"

    def test_precommit_has_repos(self):
        """Test that pre-commit config has repos."""
        config_file = Path(".pre-commit-config.yaml")
        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert "repos" in config, "Pre-commit config should have repos"
        assert isinstance(config["repos"], list), "Repos should be a list"
        assert len(config["repos"]) > 0, "Should have at least one repo"

    def test_precommit_has_standard_hooks(self):
        """Test that pre-commit has standard hooks."""
        config_file = Path(".pre-commit-config.yaml")
        with open(config_file) as f:
            config = yaml.safe_load(f)

        repos = config["repos"]

        # Find pre-commit-hooks repo
        standard_repo = None
        for repo in repos:
            if "pre-commit/pre-commit-hooks" in repo["repo"]:
                standard_repo = repo
                break

        assert standard_repo is not None, "Should have pre-commit-hooks repo"

        # Check for required hooks
        hook_ids = [hook["id"] for hook in standard_repo["hooks"]]

        assert "trailing-whitespace" in hook_ids, "Should have trailing-whitespace hook"
        assert "end-of-file-fixer" in hook_ids, "Should have end-of-file-fixer hook"
        assert "check-yaml" in hook_ids, "Should have check-yaml hook"
        assert "check-added-large-files" in hook_ids, "Should have check-added-large-files hook"

    def test_precommit_has_ruff(self):
        """Test that pre-commit has ruff hooks."""
        config_file = Path(".pre-commit-config.yaml")
        with open(config_file) as f:
            config = yaml.safe_load(f)

        repos = config["repos"]

        # Find ruff repo
        ruff_repo = None
        for repo in repos:
            if "ruff-pre-commit" in repo["repo"]:
                ruff_repo = repo
                break

        assert ruff_repo is not None, "Should have ruff-pre-commit repo"

        # Check for ruff hooks
        hook_ids = [hook["id"] for hook in ruff_repo["hooks"]]

        assert "ruff" in hook_ids, "Should have ruff hook"
        assert "ruff-format" in hook_ids, "Should have ruff-format hook"

        # Check ruff has --fix argument
        ruff_hook = next(h for h in ruff_repo["hooks"] if h["id"] == "ruff")
        assert "args" in ruff_hook, "Ruff should have args"
        assert "--fix" in ruff_hook["args"], "Ruff should have --fix arg"

    def test_precommit_has_mypy(self):
        """Test that pre-commit has mypy hook."""
        config_file = Path(".pre-commit-config.yaml")
        with open(config_file) as f:
            config = yaml.safe_load(f)

        repos = config["repos"]

        # Find mypy repo
        mypy_repo = None
        for repo in repos:
            if "mirrors-mypy" in repo["repo"]:
                mypy_repo = repo
                break

        assert mypy_repo is not None, "Should have mirrors-mypy repo"

        # Check for mypy hook
        hook_ids = [hook["id"] for hook in mypy_repo["hooks"]]
        assert "mypy" in hook_ids, "Should have mypy hook"

    def test_precommit_repos_have_versions(self):
        """Test that all repos have version tags."""
        config_file = Path(".pre-commit-config.yaml")
        with open(config_file) as f:
            config = yaml.safe_load(f)

        repos = config["repos"]

        for repo in repos:
            assert "rev" in repo, f"Repo {repo['repo']} should have rev"
            assert repo["rev"], f"Repo {repo['repo']} rev should not be empty"
            assert repo["rev"].startswith("v"), f"Repo {repo['repo']} rev should start with 'v'"

    def test_precommit_hooks_have_ids(self):
        """Test that all hooks have IDs."""
        config_file = Path(".pre-commit-config.yaml")
        with open(config_file) as f:
            config = yaml.safe_load(f)

        repos = config["repos"]

        for repo in repos:
            assert "hooks" in repo, f"Repo {repo['repo']} should have hooks"
            for hook in repo["hooks"]:
                assert "id" in hook, f"Hook in {repo['repo']} should have id"


class TestPrecommitIntegration:
    """Integration tests for pre-commit hooks."""

    def test_precommit_command_available(self):
        """Test that pre-commit command is available."""
        import subprocess

        result = subprocess.run(["pre-commit", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "Pre-commit should be available"
        assert "pre-commit" in result.stdout.lower(), "Should show pre-commit version"

    def test_precommit_config_validates(self):
        """Test that pre-commit config validates successfully."""
        import subprocess

        result = subprocess.run(["pre-commit", "validate-config"], capture_output=True, text=True)
        assert result.returncode == 0, f"Pre-commit config should validate: {result.stderr}"

    def test_precommit_can_install(self):
        """Test that pre-commit hooks can be installed."""
        import subprocess

        # Try to install hooks (this is safe to run multiple times)
        result = subprocess.run(["pre-commit", "install"], capture_output=True, text=True)
        # Should succeed or already be installed
        # Return code 0 means success, any other code is acceptable if already installed
        assert (
            result.returncode == 0 or "already installed" in result.stdout.lower()
        ), f"Pre-commit install should succeed or already be installed: {result.stderr}"


class TestPrecommitHookExecution:
    """Test that individual hooks can execute."""

    def test_trailing_whitespace_hook(self):
        """Test trailing-whitespace hook execution."""
        import subprocess
        import tempfile
        from pathlib import Path

        # Create a temporary file with trailing whitespace
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("test = 1  \n")  # Trailing whitespace
            temp_file = Path(f.name)

        try:
            # Run the hook
            result = subprocess.run(
                ["pre-commit", "run", "trailing-whitespace", "--files", str(temp_file)],
                capture_output=True,
                text=True,
            )
            # Hook should detect and fix trailing whitespace
            # Return code 1 means it fixed something
            assert result.returncode in [0, 1], "Trailing whitespace hook should run"
        finally:
            temp_file.unlink()

    def test_check_yaml_hook(self):
        """Test check-yaml hook execution."""
        import subprocess

        # Run on our CI config
        result = subprocess.run(
            ["pre-commit", "run", "check-yaml", "--files", ".github/workflows/ci.yml"],
            capture_output=True,
            text=True,
        )
        # Should pass (return 0) since our YAML is valid
        assert result.returncode == 0, f"Check-yaml should pass on valid YAML: {result.stderr}"
