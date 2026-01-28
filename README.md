# Hansard Tales

Parliamentary Data Analysis System for Kenya's National Assembly and Senate.

## Overview

Hansard Tales is a comprehensive system for collecting, processing, and analyzing Kenyan parliamentary data including Hansard records, bills, votes, questions, and petitions. The system provides tools for semantic search, MP performance tracking, and legislative analysis.

## Features

- **Data Collection**: Automated scrapers for parliament.go.ke
- **Document Processing**: PDF parsing and text extraction
- **Semantic Search**: Vector-based document retrieval using embeddings
- **Analysis Tools**: MP performance tracking, bill analysis, voting patterns
- **Anti-Hallucination**: Immutable source tracking for all data

## Project Structure

```
hansard-tales/
├── hansard_tales/          # Main package
│   ├── config/            # Configuration management
│   ├── models/            # Data models
│   ├── database/          # Database operations
│   ├── scrapers/          # Web scrapers
│   ├── processors/        # PDF and document processors
│   ├── analysis/          # Analysis tools
│   └── utils/             # Utility functions
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── property/         # Property-based tests
├── data/                  # Data storage
│   ├── pdfs/             # Downloaded PDFs
│   ├── vector_db/        # Vector database
│   └── logs/             # Application logs
├── config/                # Configuration files
│   └── environments/     # Environment-specific configs
└── docs/                  # Documentation
```

## Setup

### Prerequisites

- Python 3.12+
- Virtual environment (venv)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd hansard-tales
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

The system uses environment-specific YAML configuration files:

- `config/environments/development.yaml` - Local development
- `config/environments/staging.yaml` - Staging environment
- `config/environments/production.yaml` - Production environment

Environment variables can override configuration values using the `__` delimiter:
```bash
export DB__PASSWORD=secret
export SENTRY__DSN=https://example.com/sentry
```

## Testing

Run all tests:
```bash
pytest
```

Run specific test categories:
```bash
pytest tests/unit/              # Unit tests only
pytest tests/property/          # Property-based tests only
pytest tests/integration/       # Integration tests only
```

Run with coverage:
```bash
pytest --cov=hansard_tales --cov-report=html
```

## Development

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Maximum line length: 100 characters
- Use docstrings for all public functions and classes

### Testing Guidelines

- Maintain ≥90% code coverage
- Write both unit tests and property-based tests
- Use fixtures for test data
- Mock external dependencies

## Project Status

**Phase 0: Foundation** - In Progress
- ✅ Project setup and configuration
- ⏳ Data models and database schema
- ⏳ Vector database integration
- ⏳ Web scrapers
- ⏳ PDF processing pipeline

## License

[License information to be added]

## Contributing

[Contributing guidelines to be added]

## Contact

[Contact information to be added]
