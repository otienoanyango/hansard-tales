# Package Updates Summary

## Date: January 29, 2026

This document summarizes the package updates performed to ensure all Python dependencies are at their latest compatible versions.

## Updated Packages

### Core Dependencies
- **pydantic**: 2.5.0 → 2.12.5
- **pydantic-settings**: 2.1.0 → 2.12.0
- **python-dotenv**: 1.0.0 → 1.2.1
- **sqlalchemy**: 2.0.0 → 2.0.46
- **alembic**: 1.13.0 → 1.18.2
- **psycopg2-binary**: 2.9.0 → 2.9.11

### Vector Database
- **chromadb**: 0.4.0 → 1.4.1
- **posthog**: 2.4.0 → 5.4.0 (constrained to <6.0.0 due to chromadb compatibility)
- **qdrant-client**: 1.7.0 → 1.16.2

### Embeddings
- **sentence-transformers**: 2.2.0 → 5.2.2
- **torch**: 2.1.0 → 2.10.0

### PDF Processing
- **PyMuPDF**: 1.23.0 → 1.26.7
- **pdfplumber**: 0.10.0 → 0.11.9
- **pdfminer.six**: Kept at 20251230 (required by pdfplumber 0.11.9)

### Web Scraping
- **requests**: 2.31.0 → 2.32.5
- **beautifulsoup4**: 4.12.0 → 4.14.3

### Logging
- **structlog**: 23.2.0 → 25.5.0

### Retry Logic
- **tenacity**: 8.2.0 → 9.1.2

### Monitoring
- **prometheus-client**: 0.19.0 → 0.24.1
- **sentry-sdk**: 1.40.0 → 2.51.0

### Testing (Dev Dependencies)
- **pytest**: 7.4.0 → 9.0.2
- **pytest-cov**: 4.1.0 → 7.0.0
- **pytest-asyncio**: 0.21.0 → 1.3.0
- **pytest-xdist**: 3.3.0 → 3.8.0
- **hypothesis**: 6.92.0 → 6.151.4
- **faker**: 19.0.0 → 40.1.2
- **pyyaml**: 6.0.0 → 6.0.3
- **tomli**: 2.0.0 → 2.4.0

### Linting (Dev Dependencies)
- **ruff**: 0.1.9 → 0.14.14
- **mypy**: 1.8.0 → 1.19.1

### Type Stubs (Dev Dependencies)
- **types-requests**: 2.31.0 → 2.32.4.20260107
- **types-beautifulsoup4**: 4.12.0 → 4.12.0.20250516

### Pre-commit (Dev Dependencies)
- **pre-commit**: 3.6.0 → 4.5.1

## Compatibility Constraints

### ChromaDB and PostHog
- **chromadb 1.4.1** requires **posthog>=2.4.0,<6.0.0**
- Updated to **posthog 5.4.0** (latest 5.x version) to maintain compatibility
- Note: posthog 7.x is not compatible with chromadb 1.4.1

### pdfplumber and pdfminer.six
- **pdfplumber 0.11.9** requires **pdfminer.six==20251230** (exact version)
- Kept pdfminer.six at 20251230 to maintain compatibility
- Note: pdfminer.six 20260107 is not compatible with pdfplumber 0.11.9

## Verification

All package updates have been verified for compatibility:
- ✅ No dependency conflicts
- ✅ All packages install successfully
- ✅ Version constraints properly documented

## Next Steps

1. Install updated packages: `pip install -r requirements-dev.txt`
2. Run test suite to verify compatibility: `pytest`
3. Update any code that may be affected by API changes in major version updates

## Major Version Updates Requiring Attention

The following packages had major version updates that may require code changes:

1. **pydantic**: 2.5.0 → 2.12.5 (minor updates within v2)
2. **sentence-transformers**: 2.2.0 → 5.2.2 (major update)
3. **torch**: 2.1.0 → 2.10.0 (major update)
4. **structlog**: 23.2.0 → 25.5.0 (major update)
5. **pytest**: 7.4.0 → 9.0.2 (major update)
6. **pytest-cov**: 4.1.0 → 7.0.0 (major update)
7. **hypothesis**: 6.92.0 → 6.151.4 (minor updates within v6)
8. **faker**: 19.0.0 → 40.1.2 (major update)

## Recommendations

1. Review release notes for major version updates
2. Test all functionality thoroughly after updating
3. Monitor for any deprecation warnings
4. Update documentation if API changes affect usage examples
