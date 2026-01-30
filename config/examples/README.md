# Configuration Examples

This directory contains example configuration files for different use cases.

## Available Examples

### 1. minimal.yaml
**Use Case**: Absolute minimum configuration to get started

**Features**:
- SQLite database (no server)
- ChromaDB vector store (embedded)
- All defaults for other settings
- Requires only `ANTHROPIC_API_KEY`

**When to use**: Quick testing, learning the system

```bash
cp config/examples/minimal.yaml config/environments/development.yaml
export ANTHROPIC_API_KEY=your-key-here
```

---

### 2. local-development.yaml
**Use Case**: Local development with detailed logging

**Features**:
- SQLite + ChromaDB (no servers)
- DEBUG logging to console
- Small batch sizes (low memory)
- Disabled monitoring
- Short cache TTL for testing

**When to use**: Active development, debugging

```bash
cp config/examples/local-development.yaml config/environments/development.yaml
export ANTHROPIC_API_KEY=your-key-here
```

---

### 3. docker-compose.yaml
**Use Case**: Development with Docker services

**Features**:
- PostgreSQL database
- Qdrant vector store
- Prometheus monitoring
- JSON logging
- Connection pooling

**When to use**: Testing with production-like setup

**Prerequisites**:
```bash
# Start Docker services
docker-compose up -d

# Copy config
cp config/examples/docker-compose.yaml config/environments/development.yaml

# Set environment variables
export ANTHROPIC_API_KEY=your-key-here
export DB_PASSWORD=your-db-password
```

---

### 4. production-cloudflare.yaml
**Use Case**: Production deployment on Cloudflare Pages

**Features**:
- Managed PostgreSQL
- Managed Qdrant
- Full monitoring (Prometheus + Sentry)
- Large batch sizes
- Connection pooling
- Rate limiting
- Log rotation

**When to use**: Production deployment

**Prerequisites**:
```bash
# Set all required environment variables
export ANTHROPIC_API_KEY=your-key-here
export DB_HOST=your-db-host
export DB_PASSWORD=your-db-password
export QDRANT_HOST=your-qdrant-host
export SENTRY_DSN=your-sentry-dsn

# Copy config
cp config/examples/production-cloudflare.yaml config/environments/production.yaml
```

---

### 5. testing.yaml
**Use Case**: Running automated tests

**Features**:
- In-memory SQLite
- Temporary ChromaDB
- Minimal logging
- Single-threaded (deterministic)
- Disabled caching
- Fast timeouts

**When to use**: CI/CD pipelines, automated testing

```bash
# Tests automatically use this config
pytest
```

---

## Customizing Configurations

### Option 1: Copy and Modify

```bash
# Copy example
cp config/examples/local-development.yaml config/environments/my-config.yaml

# Edit as needed
vim config/environments/my-config.yaml

# Use it
export ENVIRONMENT=my-config
python your_script.py
```

### Option 2: Environment Variable Overrides

```bash
# Use base config
export ENVIRONMENT=development

# Override specific settings
export DB__ENGINE=postgresql
export DB__HOST=localhost
export LLM__MONTHLY_BUDGET_USD=50.0

python your_script.py
```

### Option 3: Programmatic Override

```python
from hansard_tales.config import Config, LLMConfig

# Load base config
config = Config()

# Override specific settings
config.llm = LLMConfig(
    model="claude-3-5-sonnet-20241022",
    max_tokens=2048
)
```

---

## Configuration Checklist

### Before Running

- [ ] Choose appropriate example config
- [ ] Copy to `config/environments/{environment}.yaml`
- [ ] Set required environment variables
- [ ] Verify database is accessible
- [ ] Verify vector DB is accessible (if using Qdrant)
- [ ] Test configuration loads: `python -c "from hansard_tales.config import get_config; get_config()"`

### Required Environment Variables

**All environments**:
- `ANTHROPIC_API_KEY` - Anthropic API key

**PostgreSQL environments**:
- `DB_HOST` - Database host
- `DB_PASSWORD` - Database password

**Qdrant environments**:
- `QDRANT_HOST` - Qdrant host

**Production only**:
- `SENTRY_DSN` - Sentry error tracking DSN

---

## Troubleshooting

### Config not loading

```bash
# Check environment variable
echo $ENVIRONMENT

# Verify file exists
ls -la config/environments/$ENVIRONMENT.yaml

# Test loading
python -c "from hansard_tales.config import get_config; print(get_config())"
```

### Environment variables not working

```bash
# Verify variables are set
env | grep -E "(ANTHROPIC|DB|QDRANT|SENTRY)"

# Test override
export DB__HOST=test-host
python -c "from hansard_tales.config import get_config; print(get_config().database.host)"
```

### Database connection fails

```bash
# Test PostgreSQL connection
psql -h $DB_HOST -U hansard -d hansard_tales

# Test SQLite
sqlite3 data/hansard_dev.db ".tables"
```

### Vector DB connection fails

```bash
# Test Qdrant
curl http://$QDRANT_HOST:6333/health

# Test ChromaDB (check directory)
ls -la data/vector_db_dev/
```

---

## Additional Resources

- [Configuration Guide](../../docs/CONFIGURATION.md) - Complete configuration reference
- [Architecture Documentation](../../docs/ARCHITECTURE.md) - System architecture
- [Setup Guide](../../README.md#installation) - Installation instructions

---

**Last Updated**: January 2025
