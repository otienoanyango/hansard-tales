"""
Tests for project structure and setup.

This module verifies that the required directory structure
and configuration files are properly set up.
"""

import os
from pathlib import Path


class TestProjectStructure:
    """Test suite for project directory structure."""

    def test_data_directory_exists(self):
        """Verify data/ directory exists."""
        assert Path("data").exists()
        assert Path("data").is_dir()

    def test_pdfs_directory_exists(self):
        """Verify data/pdfs/ directory exists for PDF storage."""
        assert Path("data/pdfs").exists()
        assert Path("data/pdfs").is_dir()

    def test_scripts_directory_exists(self):
        """Verify scripts/ directory exists for Python scripts."""
        assert Path("scripts").exists()
        assert Path("scripts").is_dir()

    def test_templates_directory_exists(self):
        """Verify templates/ directory exists for Jinja2 templates."""
        assert Path("templates").exists()
        assert Path("templates").is_dir()

    def test_output_directory_exists(self):
        """Verify output/ directory exists for generated static site."""
        assert Path("output").exists()
        assert Path("output").is_dir()

    def test_gitignore_exists(self):
        """Verify .gitignore file exists."""
        assert Path(".gitignore").exists()
        assert Path(".gitignore").is_file()

    def test_gitignore_contains_python_patterns(self):
        """Verify .gitignore includes Python-specific patterns."""
        with open(".gitignore", "r") as f:
            content = f.read()
        
        # Check for essential Python patterns
        assert "__pycache__/" in content
        assert "*.pyc" in content or "*.py[cod]" in content
        assert "venv/" in content or "env/" in content

    def test_gitignore_contains_data_patterns(self):
        """Verify .gitignore includes data file patterns."""
        with open(".gitignore", "r") as f:
            content = f.read()
        
        # Check for data patterns
        assert "*.pdf" in content or "data/pdfs/*.pdf" in content
        assert "*.db" in content or "data/*.db" in content

    def test_gitignore_contains_output_pattern(self):
        """Verify .gitignore includes output directory."""
        with open(".gitignore", "r") as f:
            content = f.read()
        
        assert "output/" in content

    def test_readme_exists(self):
        """Verify README.md file exists."""
        assert Path("README.md").exists()
        assert Path("README.md").is_file()

    def test_readme_contains_project_overview(self):
        """Verify README.md contains essential project information."""
        with open("README.md", "r") as f:
            content = f.read()
        
        # Check for key sections
        assert "Hansard Tales" in content
        assert "Overview" in content or "Project Structure" in content
        assert "Getting Started" in content or "Installation" in content

    def test_all_required_directories_present(self):
        """Verify all required directories are present."""
        required_dirs = ["data", "data/pdfs", "scripts", "templates", "output"]
        
        for dir_path in required_dirs:
            assert Path(dir_path).exists(), f"Required directory {dir_path} is missing"
            assert Path(dir_path).is_dir(), f"{dir_path} exists but is not a directory"

    def test_directory_structure_is_writable(self):
        """Verify directories have write permissions."""
        required_dirs = ["data", "data/pdfs", "scripts", "templates", "output"]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            assert os.access(path, os.W_OK), f"Directory {dir_path} is not writable"
