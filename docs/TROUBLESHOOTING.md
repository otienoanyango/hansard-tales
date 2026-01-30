# Troubleshooting Guide

**Version**: 1.0 (Phase 1)
**Last Updated**: January 2025

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)
3. [Database Issues](#database-issues)
4. [Vector Database Issues](#vector-database-issues)
5. [LLM API Issues](#llm-api-issues)
6. [Processing Issues](#processing-issues)
7. [Performance Issues](#performance-issues)
8. [Testing Issues](#testing-issues)
9. [Common Error Messages](#common-error-messages)
10. [Getting Help](#getting-help)

---

## Installation Issues

### Python Version Too Old

**Symptoms**:
```
ERROR: This package requires Python 3.10 or higher
```

**Solution**:
```bash
# Check Python version
python3 --version

# Install Python 3.12
# macOS
brew install python@3.12

# Linux
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.12 python3.12-venv

# Create venv with correct version
python3.12 -m venv venv
source venv/bin/activate
```

### pip Install Fails

**Symptoms**:
```
ERROR: Could not build wheels for package
```

**Solution**:
```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install build dependencies (Linux)
sudo apt install python3-dev build-essential

# Install build dependencies (macOS)
xcode-select --install

# Try again
pip install -r requirements.txt
```

### spaCy Model Not Found

**Symptoms**:
```
OSError: Can't find model 'en_core_web_sm'
```

**Solution**:
```bash
# Download model
python -m spacy download en_core_web_sm

# Verify
python -c "import spacy; spacy.load('en_core_web_sm')"
```

---

## Configuration Issues

### Configuration File Not Found

**Symptoms**:
```
FileNotFoundError: config/environments/development.yaml
```

**Solution**:
```bash
# Check environment variable
echo $ENVIRONMENT

# Create config from example
cp config/examples/minimal.yaml config/environments/development.yaml

# Or set environment
export ENVIRONMENT=development
```

### Environment Variables Not Loading

**Symptoms**:
- Configuration uses defaults instead of env vars
- API key not found

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Check variables are set
env | grep -E "(ANTHROPIC|DB|QDRANT)"

# Export variables
export ANTHROPIC_API_KEY=your-key-here

# Use correct naming (double underscore)
export DB__HOST=localhost  # Correct
export DB_HOST=localhost   # Wrong
```

### Validation Fails

**Symptoms**:
```
❌ Validation failed!
Field required: llm.api_key
```

**Solution**:
```bash
# Run validation to see all errors
python scripts/validate_config.py

# Fix each error
export ANTHROPIC_API_KEY=your-key-here

# Validate again
python scripts/validate_config.py
```

---

## Database Issues

### SQLite Database Locked

**Symptoms**:
```
sqlite3.OperationalError: database is locked
```

**Solution**:
```bash
# Check for other processes
lsof data/hansard_dev.db

# Kill processes if safe
kill -9 <PID>

# Or use different database
export DB__DATABASE=data/hansard_dev2.db
```

### PostgreSQL Connection Refused

**Symptoms**:
```
psycopg2.OperationalError: could not connect to server
```

**Solution**:
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Check connection
psql -h localhost -U hansard -d hansard_tales

# Verify credentials
echo $DB__PASSWORD
```

### Migration Fails

**Symptoms**:
```
alembic.util.exc.CommandError: Can't locate revision
```

**Solution**:
```bash
# Check alembic.ini
cat alembic.ini | grep sqlalchemy.url

# Reset migrations (WARNING: destroys data)
rm -rf alembic/versions/*.py
alembic revision --autogenerate -m "initial"
alembic upgrade head

# Or start fresh
rm data/hansard_dev.db
alembic upgrade head
```

### Table Not Found

**Symptoms**:
```
sqlalchemy.exc.OperationalError: no such table: documents
```

**Solution**:
```bash
# Run migrations
alembic upgrade head

# Verify tables exist
sqlite3 data/hansard_dev.db ".tables"

# Or for PostgreSQL
psql -h localhost -U hansard -d hansard_tales -c "\dt"
```

---

## Vector Database Issues

### ChromaDB Directory Not Found

**Symptoms**:
```
FileNotFoundError: data/vector_db
```

**Solution**:
```bash
# Create directory
mkdir -p data/vector_db

# Verify permissions
ls -la data/

# Check config
python -c "from hansard_tales.config import get_config; print(get_config().vector_db.persist_directory)"
```

### Qdrant Connection Refused

**Symptoms**:
```
requests.exceptions.ConnectionError: Connection refused
```

**Solution**:
```bash
# Check Qdrant is running
curl http://localhost:6333/health

# Start Qdrant (Docker)
docker-compose up -d qdrant

# Check logs
docker-compose logs qdrant

# Verify host/port
echo $QDRANT_HOST
```

### Collection Not Found

**Symptoms**:
```
ValueError: Collection 'hansard_tales_statements' not found
```

**Solution**:
```python
# Create collection
from hansard_tales.vector_db import create_vector_db
from hansard_tales.config import get_config

vector_db = create_vector_db(get_config().vector_db)
vector_db.create_collection("statements", dimension=384)
```

---

## LLM API Issues

### API Key Invalid

**Symptoms**:
```
anthropic.AuthenticationError: Invalid API key
```

**Solution**:
```bash
# Check API key is set
echo $ANTHROPIC_API_KEY

# Verify key format (should start with sk-ant-)
# Get new key from: https://console.anthropic.com/

# Set key
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# Test key
python -c "from anthropic import Anthropic; Anthropic(api_key='$ANTHROPIC_API_KEY').messages.create(model='claude-3-5-haiku-20241022', max_tokens=10, messages=[{'role':'user','content':'Hi'}])"
```

### Rate Limit Exceeded

**Symptoms**:
```
anthropic.RateLimitError: Rate limit exceeded
```

**Solution**:
```yaml
# Reduce rate in config
performance:
  rate_limiting:
    enabled: true
    llm_calls_per_minute: 10  # Reduce from 30

# Enable caching
llm:
  cache_enabled: true
  cache_ttl_hours: 24

# Process in smaller batches
processing:
  batch_size: 5  # Reduce from 10
```

### Monthly Budget Exceeded

**Symptoms**:
```
BudgetExceededError: Monthly budget of $20.00 exceeded
```

**Solution**:
```yaml
# Increase budget
llm:
  monthly_budget_usd: 50.0

# Or reduce usage
llm:
  cache_enabled: true  # Enable caching

# Process fewer documents
python scripts/process_historical_data.py --max-documents 10
```

### Timeout Error

**Symptoms**:
```
anthropic.APITimeoutError: Request timed out
```

**Solution**:
```yaml
# Increase timeout
llm:
  timeout: 120  # Increase from 60

# Or reduce max_tokens
llm:
  max_tokens: 512  # Reduce from 1024
```

---

## Processing Issues

### PDF Processing Fails

**Symptoms**:
```
PDFProcessingError: Failed to extract text from PDF
```

**Solution**:
```bash
# Check PDF is valid
pdfinfo data/pdfs/hansard_20251104_P.pdf

# Try different PDF library
# Edit hansard_tales/processors/pdf_processor.py
# Switch from PyMuPDF to pdfplumber or vice versa

# Check file permissions
ls -la data/pdfs/

# Verify PDF is not corrupted
file data/pdfs/hansard_20251104_P.pdf
```

### MP Identification Fails

**Symptoms**:
- No MPs identified in Hansard
- Low identification accuracy

**Solution**:
```yaml
# Lower fuzzy threshold
nlp:
  mp_identification:
    fuzzy_threshold: 75  # Reduce from 85

# Check MP database is populated
python -c "from hansard_tales.database import get_session; from hansard_tales.database.models import MPORM; print(get_session().query(MPORM).count())"

# Scrape MPs if empty
python -c "from hansard_tales.scrapers import MPScraper; from hansard_tales.config import get_config; MPScraper(get_config().scraper).scrape()"
```

### Statement Segmentation Issues

**Symptoms**:
- Too many/few statements
- Incorrect boundaries

**Solution**:
```yaml
# Adjust min length
nlp:
  statement_segmentation:
    min_statement_length: 10  # Reduce from 20

# Check boundary patterns
# Edit hansard_tales/analysis/statement_segmenter.py
# Add custom patterns for your documents
```

### Out of Memory

**Symptoms**:
```
MemoryError: Unable to allocate array
```

**Solution**:
```yaml
# Reduce batch sizes
embedding:
  batch_size: 8  # Reduce from 32

processing:
  max_workers: 2  # Reduce from 4
  batch_size: 5   # Reduce from 10

# Use smaller model
embedding:
  model_name: sentence-transformers/all-MiniLM-L6-v2  # 384 dim
```

---

## Performance Issues

### Slow Processing

**Symptoms**:
- Processing takes too long
- High CPU/memory usage

**Solution**:
```yaml
# Increase workers
processing:
  max_workers: 8  # Increase from 4

# Increase batch size
embedding:
  batch_size: 64  # Increase from 32

# Enable caching
performance:
  caching:
    enabled: true

# Use GPU for embeddings
embedding:
  device: cuda  # Change from cpu
```

### High Memory Usage

**Symptoms**:
- System runs out of memory
- Swap usage high

**Solution**:
```yaml
# Reduce batch sizes
embedding:
  batch_size: 16  # Reduce

processing:
  batch_size: 5   # Reduce
  max_workers: 2  # Reduce

# Process in smaller chunks
python scripts/process_historical_data.py --batch-size 5
```

### Database Slow

**Symptoms**:
- Queries take too long
- High disk I/O

**Solution**:
```sql
-- Add indexes (PostgreSQL)
CREATE INDEX idx_statements_mp_id ON statements(mp_id);
CREATE INDEX idx_statements_classification ON statements(classification);
CREATE INDEX idx_documents_date ON documents(date);

-- Analyze tables
ANALYZE statements;
ANALYZE documents;
```

```yaml
# Enable connection pooling
performance:
  connection_pooling:
    pool_size: 20
    max_overflow: 40
```

---

## Testing Issues

### Tests Fail

**Symptoms**:
```
FAILED tests/unit/test_config.py::TestConfig::test_load_config
```

**Solution**:
```bash
# Run with verbose output
pytest -v tests/unit/test_config.py::TestConfig::test_load_config

# Check test dependencies
pip install -r requirements-dev.txt

# Clear cache
rm -rf .pytest_cache __pycache__
pytest --cache-clear

# Run single test
pytest tests/unit/test_config.py::TestConfig::test_load_config -v
```

### Import Errors in Tests

**Symptoms**:
```
ModuleNotFoundError: No module named 'hansard_tales'
```

**Solution**:
```bash
# Install package in editable mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH=$PWD:$PYTHONPATH

# Verify
python -c "import hansard_tales; print(hansard_tales.__file__)"
```

### Fixtures Not Found

**Symptoms**:
```
FileNotFoundError: tests/fixtures/sample_mps.html
```

**Solution**:
```bash
# Check fixtures exist
ls -la tests/fixtures/

# Create missing fixtures
# See tests/sample_html.md for examples

# Run from project root
cd /path/to/hansard-tales
pytest
```

---

## Common Error Messages

### "No such file or directory"

**Cause**: Missing file or directory

**Solution**:
```bash
# Create missing directories
mkdir -p data/pdfs data/vector_db data/logs site_output

# Check file exists
ls -la path/to/file

# Check current directory
pwd
```

### "Permission denied"

**Cause**: Insufficient permissions

**Solution**:
```bash
# Check permissions
ls -la path/to/file

# Fix permissions
chmod 755 path/to/directory
chmod 644 path/to/file

# Or run with sudo (not recommended)
sudo python script.py
```

### "Connection refused"

**Cause**: Service not running or wrong host/port

**Solution**:
```bash
# Check service is running
# PostgreSQL
pg_isready -h localhost -p 5432

# Qdrant
curl http://localhost:6333/health

# Check host/port in config
python -c "from hansard_tales.config import get_config; c=get_config(); print(f'DB: {c.database.host}:{c.database.port}'); print(f'Qdrant: {c.vector_db.host}:{c.vector_db.port}')"
```

### "Validation error"

**Cause**: Invalid configuration

**Solution**:
```bash
# Run validation
python scripts/validate_config.py

# Check error message
# Fix configuration
# Validate again
```

---

## Getting Help

### Before Asking for Help

1. **Check this guide** - Most issues are covered here
2. **Check logs** - Look in `data/logs/` for error details
3. **Run validation** - `python scripts/validate_config.py`
4. **Check configuration** - Verify all settings are correct
5. **Try minimal config** - Use `config/examples/minimal.yaml`

### Gathering Information

When reporting issues, include:

```bash
# System information
uname -a
python --version
pip list | grep -E "(pydantic|sqlalchemy|anthropic)"

# Configuration
python scripts/validate_config.py

# Error message (full traceback)
# Copy from terminal or logs

# Steps to reproduce
# What you did, what happened, what you expected
```

### Where to Get Help

1. **Documentation**:
   - [Setup Guide](SETUP.md)
   - [Configuration Guide](CONFIGURATION.md)
   - [Usage Guide](USAGE.md)
   - [Architecture](ARCHITECTURE.md)

2. **GitHub**:
   - [Issues](https://github.com/yourusername/hansard-tales/issues) - Bug reports
   - [Discussions](https://github.com/yourusername/hansard-tales/discussions) - Questions

3. **Community**:
   - Check existing issues first
   - Search discussions
   - Ask in appropriate channel

---

**Last Updated**: January 2025
**Version**: 1.0 (Phase 1)
