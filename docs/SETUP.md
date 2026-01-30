# Setup Guide

**Version**: 1.0 (Phase 1)
**Last Updated**: January 2025

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

---

## Prerequisites

### System Requirements

- **Operating System**: macOS, Linux, or Windows (WSL2 recommended)
- **Python**: 3.12+ (3.10+ supported)
- **Memory**: 8GB RAM minimum (16GB recommended)
- **Storage**: 10GB free space minimum
- **Network**: Internet connection for downloading models and PDFs

### Required Software

1. **Python 3.12+**
   ```bash
   # Check Python version
   python3 --version

   # Should output: Python 3.12.x or higher
   ```

2. **pip** (Python package manager)
   ```bash
   # Check pip version
   pip --version
   ```

3. **Git** (for cloning repository)
   ```bash
   # Check Git version
   git --version
   ```

### Optional Software

1. **Docker & Docker Compose** (for production-like setup)
   ```bash
   # Check Docker version
   docker --version
   docker-compose --version
   ```

2. **PostgreSQL** (for production database)
   ```bash
   # Check PostgreSQL version
   psql --version
   ```

### API Keys

1. **Anthropic API Key** (required for Phase 1 LLM analysis)
   - Sign up at: https://console.anthropic.com/
   - Create API key
   - Keep it secure (never commit to Git)

---

## Quick Start

### 1. Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/hansard-tales.git
cd hansard-tales
```

### 2. Run Automated Setup

```bash
# Run setup script (creates venv, installs dependencies)
bash setup.sh
```

The setup script will:
- Create Python virtual environment
- Install all dependencies
- Create necessary directories
- Copy example configuration

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API key
# ANTHROPIC_API_KEY=your-key-here
```

### 4. Verify Installation

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Validate configuration
python scripts/validate_config.py

# Run tests
pytest
```

### 5. Start Using

```python
# Example: Scrape Hansard documents
from hansard_tales.scrapers import HansardScraper
from hansard_tales.config import get_config

config = get_config()
scraper = HansardScraper(config.scraper)
documents = scraper.scrape(skip_existing=True)
print(f"Downloaded {len(documents)} documents")
```

---

## Detailed Setup

### Step 1: Install Python 3.12+

#### macOS

```bash
# Using Homebrew
brew install python@3.12

# Verify installation
python3.12 --version
```

#### Linux (Ubuntu/Debian)

```bash
# Add deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.12
sudo apt install python3.12 python3.12-venv python3.12-dev

# Verify installation
python3.12 --version
```

#### Windows

1. Download Python 3.12 from https://www.python.org/downloads/
2. Run installer
3. Check "Add Python to PATH"
4. Verify: `python --version`

### Step 2: Clone Repository

```bash
# Clone repository
git clone https://github.com/yourusername/hansard-tales.git
cd hansard-tales

# Verify you're in the right directory
ls -la
# Should see: README.md, setup.sh, requirements.txt, etc.
```

### Step 3: Create Virtual Environment

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Verify activation (should see (venv) in prompt)
which python
# Should output: /path/to/hansard-tales/venv/bin/python
```

### Step 4: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt

# Verify installation
pip list | grep hansard
```

### Step 5: Create Directories

```bash
# Create data directories
mkdir -p data/pdfs
mkdir -p data/vector_db
mkdir -p data/logs
mkdir -p site_output

# Verify directories
ls -la data/
```

### Step 6: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env  # or vim, code, etc.
```

Add your API key:
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional (for development, defaults work)
ENVIRONMENT=development
DB_ENGINE=sqlite
```

### Step 7: Initialize Database

```bash
# Run database migrations
alembic upgrade head

# Verify database created
ls -la data/
# Should see: hansard_dev.db
```

### Step 8: Download spaCy Model

```bash
# Download English language model
python -m spacy download en_core_web_sm

# Verify installation
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('OK')"
```

### Step 9: Validate Configuration

```bash
# Run configuration validation
python scripts/validate_config.py

# Should output: ✅ Validation passed!
```

### Step 10: Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hansard_tales --cov-report=term

# Should see: ====== X passed in Y.YYs ======
```

---

## Configuration

### Minimal Configuration

For quick start, minimal configuration is:

```yaml
# config/environments/development.yaml
environment: development

database:
  engine: sqlite
  database: data/hansard_dev.db

vector_db:
  engine: chromadb
  persist_directory: data/vector_db

llm:
  api_key: ${ANTHROPIC_API_KEY}
```

### Development Configuration

For local development with all features:

```bash
# Copy example configuration
cp config/examples/local-development.yaml config/environments/development.yaml

# Edit as needed
nano config/environments/development.yaml
```

### Docker Configuration

For production-like setup with Docker:

```bash
# Start Docker services
docker-compose up -d

# Wait for services to start (10 seconds)
sleep 10

# Copy Docker configuration
cp config/examples/docker-compose.yaml config/environments/development.yaml

# Set environment variables
export DB_PASSWORD=your-password
export ANTHROPIC_API_KEY=your-key

# Run migrations
alembic upgrade head
```

See [Configuration Guide](CONFIGURATION.md) for complete reference.

---

## Verification

### 1. Verify Python Environment

```bash
# Check Python version
python --version
# Should output: Python 3.12.x

# Check virtual environment
which python
# Should output: /path/to/venv/bin/python

# Check installed packages
pip list | grep -E "(pydantic|sqlalchemy|anthropic)"
```

### 2. Verify Configuration

```bash
# Validate configuration
python scripts/validate_config.py

# Should output:
# ✅ All environment variables OK
# ✅ Configuration is valid
# ✅ Validation passed!
```

### 3. Verify Database

```bash
# Check SQLite database
sqlite3 data/hansard_dev.db ".tables"
# Should output: documents, downloaded_files, statements, mps, bills, etc.

# Or for PostgreSQL
psql -h localhost -U hansard -d hansard_tales -c "\dt"
```

### 4. Verify Vector Database

```bash
# For ChromaDB (check directory)
ls -la data/vector_db/
# Should see: chroma.sqlite3

# For Qdrant (check health)
curl http://localhost:6333/health
# Should output: {"status":"ok"}
```

### 5. Verify API Access

```python
# Test Anthropic API
from anthropic import Anthropic

client = Anthropic(api_key="your-key-here")
response = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=10,
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.content[0].text)
# Should output: A greeting response
```

### 6. Run Test Suite

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/property/      # Property-based tests

# All should pass
```

---

## Troubleshooting

### Issue: Python version too old

**Symptoms**: `python --version` shows < 3.10

**Solution**:
```bash
# Install Python 3.12
# See "Step 1: Install Python 3.12+" above

# Create venv with specific version
python3.12 -m venv venv
source venv/bin/activate
```

### Issue: pip install fails

**Symptoms**: `ERROR: Could not install packages`

**Solutions**:
```bash
# Upgrade pip
pip install --upgrade pip

# Install build tools (Linux)
sudo apt install python3.12-dev build-essential

# Install build tools (macOS)
xcode-select --install

# Try again
pip install -r requirements.txt
```

### Issue: spaCy model not found

**Symptoms**: `Can't find model 'en_core_web_sm'`

**Solution**:
```bash
# Download model
python -m spacy download en_core_web_sm

# Verify
python -c "import spacy; spacy.load('en_core_web_sm')"
```

### Issue: Database migration fails

**Symptoms**: `alembic upgrade head` fails

**Solutions**:
```bash
# Check database exists
ls -la data/hansard_dev.db

# If not, create directory
mkdir -p data

# Try again
alembic upgrade head

# If still fails, check alembic.ini
cat alembic.ini | grep sqlalchemy.url
```

### Issue: Configuration validation fails

**Symptoms**: `❌ Validation failed!`

**Solutions**:
```bash
# Check environment variables
env | grep ANTHROPIC_API_KEY

# If not set
export ANTHROPIC_API_KEY=your-key-here

# Check config file exists
ls -la config/environments/development.yaml

# If not, copy example
cp config/examples/minimal.yaml config/environments/development.yaml

# Try again
python scripts/validate_config.py
```

### Issue: Tests fail

**Symptoms**: `pytest` shows failures

**Solutions**:
```bash
# Run tests with verbose output
pytest -v

# Run specific failing test
pytest tests/unit/test_config.py::TestConfig::test_load_config -v

# Check test dependencies
pip install -r requirements-dev.txt

# Clear pytest cache
rm -rf .pytest_cache
pytest --cache-clear
```

### Issue: Docker services won't start

**Symptoms**: `docker-compose up` fails

**Solutions**:
```bash
# Check Docker is running
docker ps

# Check docker-compose.yml exists
ls -la docker-compose.yml

# Check ports are available
lsof -i :5432  # PostgreSQL
lsof -i :6333  # Qdrant

# Stop conflicting services
sudo systemctl stop postgresql

# Try again
docker-compose up -d
```

### Issue: Out of memory

**Symptoms**: System freezes or crashes

**Solutions**:
```bash
# Reduce batch sizes in config
# config/environments/development.yaml
embedding:
  batch_size: 8  # Reduce from 32

processing:
  max_workers: 2  # Reduce from 4
  batch_size: 5   # Reduce from 10

# Use smaller embedding model
embedding:
  model_name: sentence-transformers/all-MiniLM-L6-v2  # 384 dim
```

---

## Next Steps

### 1. Download Sample Data

```bash
# Download sample Hansard documents
python scripts/download_historical_data.py --year 2025 --max-documents 10
```

### 2. Process Documents

```bash
# Process downloaded PDFs
python scripts/process_historical_data.py
```

### 3. Run Analysis Pipeline

```python
from hansard_tales.pipeline import ProcessingPipeline
from hansard_tales.config import get_config

config = get_config()
pipeline = ProcessingPipeline(config)

# Process a single document
result = pipeline.process_hansard("data/pdfs/hansard_20251104_P.pdf")
print(f"Processed {result.statements_count} statements")
```

### 4. Generate Static Site

```python
from hansard_tales.site.generator import StaticSiteGenerator

generator = StaticSiteGenerator(config)
generator.generate_all()
print("Site generated in site_output/")
```

### 5. Explore Documentation

- [Configuration Guide](CONFIGURATION.md) - Complete configuration reference
- [Usage Guide](USAGE.md) - How to use the system
- [API Documentation](API.md) - API reference
- [Architecture](ARCHITECTURE.md) - System architecture
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

### 6. Join Community

- GitHub Issues: Report bugs and request features
- GitHub Discussions: Ask questions and share ideas
- Contributing: See [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Additional Resources

### Documentation

- [README.md](../README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration guide
- [USAGE.md](USAGE.md) - Usage guide
- [API.md](API.md) - API reference
- [MONITORING.md](MONITORING.md) - Monitoring setup
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Troubleshooting guide

### Example Scripts

- `examples/prometheus_example.py` - Prometheus metrics example
- `examples/sentry_example.py` - Sentry error tracking example
- `scripts/download_historical_data.py` - Download historical data
- `scripts/process_historical_data.py` - Process historical data
- `scripts/validate_historical_data.py` - Validate data integrity

### Configuration Examples

- `config/examples/minimal.yaml` - Minimal configuration
- `config/examples/local-development.yaml` - Local development
- `config/examples/docker-compose.yaml` - Docker setup
- `config/examples/production-cloudflare.yaml` - Production setup
- `config/examples/testing.yaml` - Testing configuration

---

**Last Updated**: January 2025
**Version**: 1.0 (Phase 1)
