# Contributing to Hansard Tales

Thank you for your interest in contributing to Hansard Tales! This document provides guidelines and instructions for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone <your-fork-url>`
3. Create a virtual environment: `python3 -m venv venv`
4. Activate the virtual environment: `source venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Create a branch: `git checkout -b feature/your-feature-name`

## Development Workflow

### 1. Make Your Changes

- Follow the code style guidelines (see below)
- Write tests for new functionality
- Update documentation as needed

### 2. Run Tests

Before submitting your changes, ensure all tests pass:

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-property
make test-integration

# Check coverage
make coverage
```

### 3. Code Quality

Run linters and formatters:

```bash
# Format code
make format

# Run linters
make lint
```

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add new feature description"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions or changes
- `refactor:` - Code refactoring
- `style:` - Code style changes
- `chore:` - Maintenance tasks

### 5. Submit a Pull Request

1. Push your branch: `git push origin feature/your-feature-name`
2. Open a pull request on GitHub
3. Describe your changes clearly
4. Link any related issues

## Code Style Guidelines

### Python Style

- Follow PEP 8 guidelines
- Maximum line length: 100 characters
- Use type hints for all functions
- Write docstrings for all public functions and classes

Example:

```python
def process_document(doc_path: Path, force: bool = False) -> ProcessedDocument:
    """
    Process a single document.
    
    Args:
        doc_path: Path to the document
        force: Force reprocessing even if already processed
        
    Returns:
        ProcessedDocument with processing results
        
    Raises:
        ValueError: If doc_path is invalid
    """
    # Implementation
```

### Testing Guidelines

1. **Write Tests First**: Follow TDD when possible
2. **Test Coverage**: Maintain ≥90% code coverage
3. **Test Types**:
   - Unit tests for individual functions
   - Property-based tests for universal invariants
   - Integration tests for component interactions

4. **Test Structure**:
```python
class TestFeatureName:
    """Test suite for specific feature."""
    
    def test_success_case(self):
        """Test normal operation."""
        # Arrange
        input_data = create_test_data()
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        assert result.status == 'success'
```

### Documentation

- Update README.md for user-facing changes
- Update docstrings for API changes
- Add comments for complex logic
- Create ADRs for architectural decisions

## Project Structure

```
hansard-tales/
├── hansard_tales/          # Main package
│   ├── config/            # Configuration management
│   ├── models/            # Data models
│   ├── database/          # Database operations
│   ├── scrapers/          # Web scrapers
│   ├── processors/        # Document processors
│   ├── analysis/          # Analysis tools
│   └── utils/             # Utility functions
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── property/         # Property-based tests
├── config/                # Configuration files
└── docs/                  # Documentation
```

## Common Tasks

### Adding a New Feature

1. Create a new branch: `git checkout -b feature/feature-name`
2. Implement the feature in the appropriate module
3. Write tests (unit + property-based)
4. Update documentation
5. Run tests and linters
6. Submit pull request

### Fixing a Bug

1. Create a new branch: `git checkout -b fix/bug-description`
2. Write a failing test that reproduces the bug
3. Fix the bug
4. Verify the test passes
5. Submit pull request

### Adding Tests

1. Identify untested code using coverage report
2. Write appropriate tests (unit/property/integration)
3. Ensure tests pass and coverage increases
4. Submit pull request

## Questions?

If you have questions or need help:

1. Check existing documentation
2. Search existing issues
3. Open a new issue with your question

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## License

By contributing to Hansard Tales, you agree that your contributions will be licensed under the project's license.
