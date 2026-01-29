# Contributing to Hansard Tales

Thank you for your interest in contributing to Hansard Tales! This document provides guidelines and instructions for contributing to the project.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Documentation Requirements](#documentation-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting Guidelines](#issue-reporting-guidelines)
- [Communication Channels](#communication-channels)
- [Recognition](#recognition)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors. We pledge to:

- Be respectful and considerate in all interactions
- Welcome diverse perspectives and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing others' private information without permission
- Any conduct that could reasonably be considered inappropriate in a professional setting

### Enforcement

Instances of unacceptable behavior may be reported to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

---

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Python 3.12+** (3.10+ supported)
- **Git** for version control
- **Docker & Docker Compose** for development services
- **Basic knowledge** of Python, SQLAlchemy, and pytest

### First-Time Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/hansard-tales.git
   cd hansard-tales
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/hansard-tales.git
   ```

4. **Run the setup script**:
   ```bash
   bash setup.sh
   ```

   This will:
   - Create a virtual environment
   - Install all dependencies
   - Set up pre-commit hooks
   - Initialize the database

5. **Start development services**:
   ```bash
   make docker-up
   ```

6. **Run tests to verify setup**:
   ```bash
   make test
   ```

### Understanding the Codebase

Before making changes, familiarize yourself with:

- **[README.md](README.md)** - Project overview and quick start
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design
- **[testing-guidelines.md](.kiro/rules/testing-guidelines.md)** - Testing best practices
- **[code-style.md](.kiro/rules/code-style.md)** - Code style guide

### Finding Issues to Work On

Good first issues are labeled with:
- `good first issue` - Suitable for newcomers
- `help wanted` - Extra attention needed
- `documentation` - Documentation improvements
- `bug` - Something isn't working

Browse the [issue tracker](https://github.com/ORIGINAL_OWNER/hansard-tales/issues) to find something that interests you.

---

## Development Workflow

### 1. Create a Feature Branch

Always create a new branch for your work:

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

**Branch naming conventions**:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `chore/` - Maintenance tasks

### 2. Make Your Changes

Follow these guidelines:

- **Write clear, focused commits** - Each commit should represent a single logical change
- **Follow code style** - See [Code Style Guidelines](#code-style-guidelines)
- **Write tests** - See [Testing Requirements](#testing-requirements)
- **Update documentation** - See [Documentation Requirements](#documentation-requirements)

### 3. Commit Your Changes

Write clear, descriptive commit messages:

```bash
# Good commit messages
git commit -m "feat: add Hansard scraper pagination support"
git commit -m "fix: handle missing date in PDF metadata"
git commit -m "docs: update installation instructions"
git commit -m "test: add property tests for scraper"

# Bad commit messages
git commit -m "fixed stuff"
git commit -m "updates"
git commit -m "wip"
```

**Commit message format**:
```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

**Types**:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `test` - Test additions or changes
- `refactor` - Code refactoring
- `style` - Code style changes (formatting, etc.)
- `chore` - Maintenance tasks
- `perf` - Performance improvements

### 4. Keep Your Branch Updated

Regularly sync with upstream:

```bash
# Fetch upstream changes
git fetch upstream

# Rebase your branch
git rebase upstream/main

# Or merge if you prefer
git merge upstream/main
```

### 5. Run Tests and Linters

Before pushing, ensure all checks pass:

```bash
# Run all tests
make test

# Run linters
make lint

# Format code
make format

# Check coverage
make coverage
```

### 6. Push Your Changes

```bash
git push origin feature/your-feature-name
```

### 7. Create a Pull Request

1. Go to your fork on GitHub
2. Click "New Pull Request"
3. Select your feature branch
4. Fill out the PR template (see [Pull Request Process](#pull-request-process))
5. Submit the PR

---

## Code Style Guidelines

We follow Python best practices with emphasis on readability and maintainability.

### Python Version

- **Target**: Python 3.12+
- **Compatibility**: Python 3.10+ when possible

### Code Formatting

- **Line length**: 100 characters (soft limit)
- **Docstrings**: 80 characters
- **Formatter**: ruff (configured in `pyproject.toml`)

### Naming Conventions

```python
# Variables and functions: snake_case
def process_pdf_file(pdf_path, output_dir):
    file_count = 0
    processed_items = []

# Classes: PascalCase
class PDFProcessor:
    class HistoricalDataProcessor:

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Private/Internal: prefix with _
def _internal_helper():
    """Internal function."""
```

### Type Hints

Always use type hints for function signatures:

```python
from typing import Optional, List, Dict
from pathlib import Path
from datetime import date

def extract_date(filename: str) -> Optional[date]:
    """Extract date from filename."""

def process_files(paths: List[Path]) -> Dict[str, int]:
    """Process multiple files."""
```

### Docstrings

All public functions and classes must have docstrings:

```python
def process_single_pdf(pdf_path: Path, db_path: Path, force: bool = False) -> ProcessedPDF:
    """
    Process a single PDF file (stateless, idempotent, portable).

    This function is designed to be:
    - Stateless: No shared state between calls
    - Idempotent: Can be called multiple times safely
    - Portable: Can run on any machine

    Args:
        pdf_path: Path to PDF file
        db_path: Path to database
        force: Force reprocess even if already processed

    Returns:
        ProcessedPDF with processing results

    Raises:
        ValueError: If pdf_path is invalid

    Example:
        >>> result = process_single_pdf(Path("test.pdf"), Path("db.db"))
        >>> print(result.status)
        'success'
    """
```

### Imports

Order imports as follows:

```python
# Standard library
import os
import sys
from pathlib import Path
from datetime import datetime, date

# Third-party
import pytest
import sqlite3
from unittest.mock import Mock, patch

# Local
from hansard_tales.processors.pdf_processor import PDFProcessor
from hansard_tales.database.db_updater import DatabaseUpdater
```

### Error Handling

Use specific exceptions and descriptive error messages:

```python
# Good: Specific exception
try:
    result = parse_date(date_str)
except ValueError as e:
    logger.error(f"Invalid date format: {e}")
    return None

# Bad: Catch-all
try:
    result = parse_date(date_str)
except Exception:  # Too broad
    return None
```

### Additional Guidelines

See [code-style.md](.kiro/rules/code-style.md) for comprehensive style guidelines.

---

## Testing Requirements

We maintain **≥90% code coverage** and use multiple testing strategies.

### Test Types

1. **Unit Tests** - Test individual functions in isolation
2. **Property-Based Tests** - Test universal invariants with Hypothesis
3. **Integration Tests** - Test multiple components working together

### Writing Tests

#### Unit Tests

```python
import pytest
from hansard_tales.scrapers import HansardScraper

class TestHansardScraper:
    """Test suite for Hansard scraper."""

    def test_scrape_success(self, mock_requests):
        """Test successful scraping."""
        # Arrange
        scraper = HansardScraper(config)

        # Act
        documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY)

        # Assert
        assert len(documents) > 0
        assert all(doc.hash for doc in documents)
```

#### Property-Based Tests

```python
from hypothesis import given, strategies as st

@given(st.text())
def test_filename_generation_never_crashes(text):
    """Filename generation should never crash."""
    scraper = HansardScraper(config)
    filename = scraper._generate_filename(text)
    assert isinstance(filename, str)

@given(st.dates(), st.sampled_from(["Morning", "Afternoon", "Evening"]))
def test_filename_always_valid_format(date, period):
    """Generated filenames should always match expected pattern."""
    filename = generate_filename(date, period)
    assert re.match(r'hansard_\d{8}_\d+_[APE]\.pdf', filename)
```

#### Integration Tests

```python
def test_scraper_to_storage_integration(temp_db):
    """Test complete scraping and storage workflow."""
    # Scrape documents
    scraper = HansardScraper(config)
    documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY)

    # Store in database
    storage = StorageService(config)
    for doc in documents:
        storage.store_document(doc)

    # Verify storage
    with get_session() as session:
        stored = session.query(DocumentORM).all()
        assert len(stored) == len(documents)
```

### Test Coverage Requirements

- **Overall project**: ≥90%
- **New modules**: ≥90%
- **Modified modules**: Maintain or improve existing coverage

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
make test-unit              # Unit tests only
make test-property          # Property-based tests only
make test-integration       # Integration tests only

# Run with coverage
make coverage

# Run specific test file
pytest tests/unit/test_scrapers.py

# Run specific test
pytest tests/unit/test_scrapers.py::TestHansardScraper::test_scrape_success
```

### Test Guidelines

- **Use fixtures** for test data
- **Mock external dependencies** (network, filesystem)
- **Test both success and failure** cases
- **Keep tests focused** - One test per behavior
- **Use descriptive names** - `test_<what>_<condition>_<expected>`
- **Avoid test interdependence** - Each test should be independent

### Additional Guidelines

See [testing-guidelines.md](.kiro/rules/testing-guidelines.md) for comprehensive testing guidelines.

---

## Documentation Requirements

Good documentation is essential for maintainability and onboarding.

### Code Documentation

#### Docstrings

All public functions, classes, and modules must have docstrings:

```python
def process_pdf(pdf_path: Path) -> ProcessedPDF:
    """
    Process a PDF file and extract text and metadata.

    Args:
        pdf_path: Path to PDF file

    Returns:
        ProcessedPDF with extracted data

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF is corrupted

    Example:
        >>> result = process_pdf(Path("hansard.pdf"))
        >>> print(result.status)
        'success'
    """
```

#### Inline Comments

Use comments to explain **why**, not **what**:

```python
# Good: Explain WHY
# Use content hashing to detect duplicates across sessions
statement_hash = compute_hash(statement.text)

# Bad: Obvious comment
# Increment counter
counter += 1
```

### Project Documentation

When adding new features, update relevant documentation:

- **README.md** - If adding user-facing features
- **ARCHITECTURE.md** - If changing system architecture
- **MONITORING.md** - If adding metrics or dashboards
- **API docs** - If adding/changing public APIs

### Documentation Style

- Use **clear, concise language**
- Include **code examples** where helpful
- Add **diagrams** for complex concepts
- Keep documentation **up-to-date** with code changes

---

## Pull Request Process

### Before Submitting

Ensure your PR meets these requirements:

- ✅ All tests pass (`make test`)
- ✅ Code coverage ≥90% (`make coverage`)
- ✅ Linters pass (`make lint`)
- ✅ Code is formatted (`make format`)
- ✅ Documentation is updated
- ✅ Commit messages are clear
- ✅ Branch is up-to-date with main

### PR Template

When creating a PR, include:

```markdown
## Description

Brief description of what this PR does.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Test improvements

## Related Issues

Closes #123
Related to #456

## Changes Made

- Added pagination support to Hansard scraper
- Updated tests to cover new functionality
- Updated documentation

## Testing

- [ ] Unit tests added/updated
- [ ] Property-based tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass locally
- [ ] Coverage maintained at ≥90%

## Documentation

- [ ] Code docstrings added/updated
- [ ] README.md updated (if needed)
- [ ] ARCHITECTURE.md updated (if needed)
- [ ] Inline comments added for complex logic

## Screenshots (if applicable)

Add screenshots for UI changes or visual features.

## Checklist

- [ ] My code follows the project's code style
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
```

### Review Process

1. **Automated Checks** - CI/CD runs tests, linters, and coverage checks
2. **Code Review** - Maintainers review your code
3. **Feedback** - Address any requested changes
4. **Approval** - Once approved, your PR will be merged

### Responding to Feedback

- Be **responsive** to review comments
- Be **open** to suggestions and improvements
- **Explain** your reasoning if you disagree
- **Update** your PR based on feedback
- **Thank** reviewers for their time

### After Merge

- **Delete** your feature branch
- **Update** your local repository
- **Celebrate** your contribution! 🎉

---

## Issue Reporting Guidelines

### Before Creating an Issue

1. **Search existing issues** - Your issue may already be reported
2. **Check documentation** - The answer might be in the docs
3. **Try the latest version** - The issue might be fixed

### Creating a Good Issue

#### Bug Reports

Use this template:

```markdown
## Bug Description

Clear and concise description of the bug.

## Steps to Reproduce

1. Go to '...'
2. Run command '...'
3. See error

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened.

## Environment

- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.12.0]
- Hansard Tales version: [e.g., 0.1.0]

## Error Messages

```
Paste error messages here
```

## Additional Context

Any other relevant information.
```

#### Feature Requests

Use this template:

```markdown
## Feature Description

Clear and concise description of the feature.

## Problem Statement

What problem does this feature solve?

## Proposed Solution

How should this feature work?

## Alternatives Considered

What other solutions did you consider?

## Additional Context

Any other relevant information.
```

### Issue Labels

Issues are labeled to help with organization:

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Documentation improvements
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `question` - Further information requested
- `wontfix` - This will not be worked on
- `duplicate` - This issue already exists

---

## Communication Channels

### GitHub

- **Issues** - Bug reports and feature requests
- **Pull Requests** - Code contributions
- **Discussions** - General questions and ideas

### Response Times

- **Issues** - We aim to respond within 48 hours
- **Pull Requests** - We aim to review within 1 week
- **Security Issues** - We aim to respond within 24 hours

### Getting Help

If you need help:

1. **Check documentation** - README, ARCHITECTURE, guides
2. **Search issues** - Someone may have asked before
3. **Create a discussion** - For general questions
4. **Create an issue** - For specific problems

### Security Issues

**Do not** create public issues for security vulnerabilities.

Instead, email security concerns to: [security-email@example.com]

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

---

## Recognition

We value all contributions and recognize contributors in several ways:

### Contributors List

All contributors are listed in:
- **README.md** - Contributors section
- **GitHub Contributors** - Automatic GitHub recognition

### Types of Contributions

We recognize various types of contributions:

- 💻 **Code** - Bug fixes, features, refactoring
- 📖 **Documentation** - Docs, guides, examples
- 🧪 **Testing** - Test improvements, bug reports
- 🎨 **Design** - UI/UX improvements
- 💡 **Ideas** - Feature suggestions, discussions
- 🔍 **Review** - Code reviews, feedback
- 🌍 **Translation** - Internationalization
- 📢 **Outreach** - Blog posts, talks, tutorials

### Hall of Fame

Outstanding contributors may be featured in:
- Project README
- Release notes
- Social media shoutouts

### Becoming a Maintainer

Regular contributors who demonstrate:
- **Technical expertise**
- **Commitment** to the project
- **Collaborative spirit**
- **Good judgment**

May be invited to become maintainers with:
- Commit access
- Issue triage permissions
- PR review responsibilities

---

## Additional Resources

### Documentation

- [README.md](README.md) - Project overview
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [MONITORING.md](docs/MONITORING.md) - Monitoring setup
- [SENTRY_SETUP.md](docs/SENTRY_SETUP.md) - Error tracking
- [testing-guidelines.md](.kiro/rules/testing-guidelines.md) - Testing guide
- [code-style.md](.kiro/rules/code-style.md) - Code style guide

### External Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

### Tools

- [pytest](https://docs.pytest.org/) - Testing framework
- [Hypothesis](https://hypothesis.readthedocs.io/) - Property-based testing
- [ruff](https://docs.astral.sh/ruff/) - Linter and formatter
- [mypy](https://mypy.readthedocs.io/) - Type checker
- [pre-commit](https://pre-commit.com/) - Git hooks

---

## Questions?

If you have questions not covered in this guide:

1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/ORIGINAL_OWNER/hansard-tales/issues)
3. Create a [discussion](https://github.com/ORIGINAL_OWNER/hansard-tales/discussions)
4. Reach out to maintainers

---

## Thank You!

Thank you for contributing to Hansard Tales! Your efforts help improve transparency and accountability in Kenyan governance.

Every contribution, no matter how small, makes a difference. We appreciate your time and expertise.

**Happy coding! 🚀**

---

*Last updated: January 2025*
