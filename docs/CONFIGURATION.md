# Configuration Guide

**Version**: 1.0 (Phase 1)
**Last Updated**: January 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Files](#configuration-files)
3. [Environment Variables](#environment-variables)
4. [Configuration Sections](#configuration-sections)
5. [Environment-Specific Settings](#environment-specific-settings)
6. [Configuration Validation](#configuration-validation)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)

---

## Overview

Hansard Tales uses a hierarchical configuration system with:
- **YAML configuration files** for structured settings
- **Environment variables** for sensitive data and overrides
- **Pydantic validation** for type safety and defaults
- **Environment-specific configs** for dev/staging/production

### Configuration Priority

Settings are loaded in this order (later overrides earlier):
1. Default values in code (Pydantic models)
2. YAML configuration file
3. Environment variables
4. Command-line arguments (if applicable)

---

## Configuration Files

### File Locations

```
config/
├── environments/
│   ├── development.yaml    # Development settings
│   ├── staging.yaml        # Staging settings
│   └── production.yaml     # Production settings
└── .env.example            # Example environment variables
```

### Loading Configuration

```python
from hansard_tales.config import get_config

# Load configuration (auto-detects environment)
config = get_config()

# Or specify environment explicitly
import os
os.environ['ENVIRONMENT'] = 'production'
config = get_config()
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key for LLM | `sk-ant-...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `development` |
| `DB__HOST` | Database host | `localhost` |
| `DB__PORT` | Database port | `5432` |
| `DB__PASSWORD` | Database password | `` |
| `QDRANT_HOST` | Qdrant host | `localhost` |
| `SENTRY_DSN` | Sentry error tracking DSN | `` |

### Variable Naming Convention

Use double underscore (`__`) to nest configuration:
- `DB__HOST` → `database.host`
- `LLM__API_KEY` → `llm.api_key`
- `VECTOR_DB__ENGINE` → `vector_db.engine`

### Example .env File

```bash
# Environment
ENVIRONMENT=development

# Database
DB__ENGINE=sqlite
DB__DATABASE=data/hansard_dev.db

# LLM
ANTHROPIC_API_KEY=sk-ant-your-key-here
LLM__MONTHLY_BUDGET_USD=20.0

# Monitoring
SENTRY_ENABLED=false
SENTRY_DSN=

# Logging
LOG_LEVEL=DEBUG
```

---

## Configuration Sections

### 1. Database Configuration

Controls relational database settings.

```yaml
database:
  engine: sqlite              # sqlite or postgresql
  host: localhost             # Database host (PostgreSQL only)
  port: 5432                  # Database port (PostgreSQL only)
  database: data/hansard_dev  # Database name/path
  user: hansard               # Database user (PostgreSQL only)
  password: ""                # Database password (PostgreSQL only)
```

**Options**:
- `engine`: Database engine (`sqlite` for dev, `postgresql` for prod)
- `host`: Database server hostname
- `port`: Database server port
- `database`: Database name (PostgreSQL) or file path (SQLite)
- `user`: Database username
- `password`: Database password (use environment variable)

**Connection String**:
- SQLite: `sqlite:///data/hansard_dev.db`
- PostgreSQL: `postgresql://user:pass@host:5432/database`

---

### 2. Vector Database Configuration

Controls vector database for semantic search.

```yaml
vector_db:
  engine: chromadb                    # chromadb or qdrant
  host: localhost                     # Qdrant host (Qdrant only)
  port: 6333                          # Qdrant port (Qdrant only)
  collection_prefix: hansard_tales    # Collection name prefix
  persist_directory: data/vector_db   # Storage directory
```

**Options**:
- `engine`: Vector DB engine (`chromadb` for dev, `qdrant` for prod)
- `host`: Qdrant server hostname
- `port`: Qdrant server port
- `collection_prefix`: Prefix for collection names
- `persist_directory`: Directory for persistent storage

**Collections Created**:
- `{prefix}_documents` - Full document embeddings
- `{prefix}_statements` - Statement embeddings
- `{prefix}_bills` - Bill embeddings

---

### 3. Embedding Configuration

Controls text embedding generation.

```yaml
embedding:
  model_name: sentence-transformers/all-MiniLM-L6-v2
  dimension: 384
  device: cpu                # cpu or cuda
  batch_size: 32             # Batch size for embedding generation
```

**Options**:
- `model_name`: HuggingFace model identifier
- `dimension`: Embedding vector dimension (must match model)
- `device`: Computation device (`cpu` or `cuda`)
- `batch_size`: Number of texts to embed at once

**Supported Models**:
- `all-MiniLM-L6-v2` (384 dim) - Fast, good quality
- `all-mpnet-base-v2` (768 dim) - Higher quality, slower
- `multi-qa-MiniLM-L6-cos-v1` (384 dim) - Optimized for Q&A

---

### 4. Web Scraper Configuration

Controls web scraping behavior.

```yaml
scraper:
  base_url: https://parliament.go.ke
  download_dir: data/pdfs
  max_retries: 3
  retry_delay: 1.0
  timeout: 30
  user_agent: HansardTales/1.0
```

**Options**:
- `base_url`: Parliament website base URL
- `download_dir`: Directory for downloaded PDFs
- `max_retries`: Maximum retry attempts for failed requests
- `retry_delay`: Delay between retries (seconds)
- `timeout`: Request timeout (seconds)
- `user_agent`: User agent string for HTTP requests

---

### 5. LLM Configuration (Phase 1)

Controls LLM API usage for analysis.

```yaml
llm:
  provider: anthropic
  model: claude-3-5-haiku-20241022
  api_key: ${ANTHROPIC_API_KEY}
  max_tokens: 1024
  temperature: 0.0
  timeout: 60
  max_retries: 3
  monthly_budget_usd: 20.0
  cache_enabled: true
  cache_ttl_hours: 24
```

**Options**:
- `provider`: LLM provider (`anthropic`)
- `model`: Model identifier
- `api_key`: API key (use environment variable)
- `max_tokens`: Maximum tokens per response
- `temperature`: Sampling temperature (0.0 = deterministic)
- `timeout`: API request timeout (seconds)
- `max_retries`: Maximum retry attempts
- `monthly_budget_usd`: Monthly spending limit (USD)
- `cache_enabled`: Enable response caching
- `cache_ttl_hours`: Cache time-to-live (hours)

**Cost Management**:
- System tracks API usage and costs
- Alerts when approaching monthly budget
- Caching reduces duplicate API calls

---

### 6. NLP Configuration (Phase 1)

Controls NLP processing components.

#### MP Identification

```yaml
nlp:
  mp_identification:
    fuzzy_threshold: 85        # Minimum fuzzy match score (0-100)
    cache_enabled: true        # Enable MP name caching
    spacy_model: en_core_web_sm  # spaCy model for NER
```

#### Statement Segmentation

```yaml
  statement_segmentation:
    min_statement_length: 20   # Minimum characters per statement
```

#### Filler Detection

```yaml
  filler_detection:
    short_acknowledgment_threshold: 10  # Max chars for short acks
```

#### Context Retrieval (RAG)

```yaml
  context_retrieval:
    top_k_historical: 5        # Historical statements to retrieve
    top_k_bills: 3             # Related bills to retrieve
    top_k_votes: 3             # Related votes to retrieve
    top_k_session: 5           # Session context statements
    max_context_tokens: 200000 # Max tokens for LLM context
```

#### Citation Verification

```yaml
  citation_verification:
    fuzzy_threshold: 85        # Minimum similarity for fuzzy match
    exact_match_required: false  # Require exact quote match
```

---

### 7. Analysis Configuration (Phase 1)

Controls analysis algorithms.

#### Quality Scoring

```yaml
analysis:
  quality_scoring:
    min_score: 0
    max_score: 100
```

Quality factors (each 0-20 points):
- Clarity: How clear and understandable
- Depth: Level of detail and analysis
- Evidence: Use of facts and data
- Policy Content: Substantive policy discussion
- Originality: Novel ideas or perspectives

#### Topic Classification

```yaml
  topic_classification:
    confidence_threshold: 0.7      # Minimum confidence for topic
    max_topics_per_statement: 5    # Maximum topics per statement
```

Default topics: Healthcare, Education, Finance, Infrastructure, Agriculture, Security, Governance, Environment, Energy, Trade

#### Sentiment Analysis

```yaml
  sentiment_analysis:
    confidence_threshold: 0.7      # Minimum confidence for sentiment
```

Sentiments: support, oppose, neutral, mixed

---

### 8. Processing Configuration

Controls document processing.

#### PDF Processing

```yaml
processing:
  pdf_processing:
    max_workers: 4             # Parallel workers for PDF processing
    timeout_seconds: 300       # Processing timeout per PDF
```

#### Batch Processing

```yaml
  batch_processing:
    batch_size: 10             # Items per batch
    max_workers: 4             # Parallel workers
```

#### Vote Processing

```yaml
  vote_processing:
    table_detection_threshold: 0.8  # Confidence for table detection
```

---

### 9. Static Site Generation

Controls static site output.

```yaml
site_generation:
  output_dir: site_output
  template_dir: templates
  base_url: https://hansard-tales.pages.dev
  items_per_page: 20
```

**Options**:
- `output_dir`: Directory for generated HTML files
- `template_dir`: Directory containing Jinja2 templates
- `base_url`: Base URL for absolute links
- `items_per_page`: Pagination size

---

### 10. Logging Configuration

Controls application logging.

```yaml
logging:
  level: INFO                # DEBUG, INFO, WARNING, ERROR
  format: json               # json or text
  output: both               # stdout, file, or both
  log_dir: logs
  rotation: 1 day            # Log rotation interval
  retention: 30 days         # Log retention period
```

**Log Levels**:
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages (non-critical issues)
- `ERROR`: Error messages (critical issues)

**Log Formats**:
- `json`: Structured JSON logs (recommended for production)
- `text`: Human-readable text logs (recommended for development)

---

### 11. Monitoring Configuration

Controls monitoring and observability.

```yaml
monitoring:
  prometheus_enabled: true
  prometheus_port: 9090
  sentry_enabled: false
  sentry_dsn: ${SENTRY_DSN}
```

**Options**:
- `prometheus_enabled`: Enable Prometheus metrics
- `prometheus_port`: Prometheus metrics port
- `sentry_enabled`: Enable Sentry error tracking
- `sentry_dsn`: Sentry DSN (use environment variable)

**Metrics Exposed**:
- `documents_processed_total` - Total documents processed
- `processing_time_seconds` - Processing time histogram
- `errors_total` - Total errors by type
- `llm_calls_total` - Total LLM API calls
- `llm_cost_usd` - Total LLM cost in USD

---

### 12. Pipeline Configuration

Controls processing pipeline behavior.

```yaml
pipeline:
  error_handling:
    max_retries: 3
    retry_delay: 5.0
    continue_on_error: true
```

**Options**:
- `max_retries`: Maximum retry attempts per stage
- `retry_delay`: Delay between retries (seconds)
- `continue_on_error`: Continue pipeline on stage failure

**Pipeline Stages** (Phase 1):
1. MP Identification
2. Statement Segmentation
3. Filler Detection
4. Context Retrieval
5. LLM Analysis
6. Citation Verification
7. Bill Linking
8. Vote Processing
9. Profile Generation
10. Session Summary
11. Site Generation

---

### 13. Performance Configuration

Controls performance optimizations.

#### Caching

```yaml
performance:
  caching:
    enabled: true
    ttl_hours: 24
    max_cache_size_mb: 1000
```

#### Connection Pooling

```yaml
  connection_pooling:
    pool_size: 10
    max_overflow: 20
```

#### Rate Limiting

```yaml
  rate_limiting:
    enabled: true
    requests_per_minute: 60
    llm_calls_per_minute: 30
```

---

## Environment-Specific Settings

### Development

Optimized for local development:
- SQLite database (no server required)
- ChromaDB vector store (embedded)
- Text logging to stdout
- Disabled monitoring
- Small batch sizes
- Low worker counts

### Staging

Mirrors production with reduced resources:
- PostgreSQL database
- Qdrant vector store
- JSON logging to files
- Enabled monitoring
- Medium batch sizes
- Medium worker counts

### Production

Optimized for performance and reliability:
- PostgreSQL database with connection pooling
- Qdrant vector store with persistence
- JSON logging to files with rotation
- Full monitoring (Prometheus + Sentry)
- Large batch sizes
- High worker counts
- Rate limiting enabled

---

## Configuration Validation

### Automatic Validation

Pydantic validates all configuration on load:
- Type checking (string, int, float, bool)
- Range validation (min/max values)
- Format validation (URLs, paths, enums)
- Required field checking

### Validation Errors

```python
from hansard_tales.config import get_config

try:
    config = get_config()
except ValidationError as e:
    print(f"Configuration error: {e}")
```

### Common Validation Errors

1. **Missing required field**:
   ```
   Field required: llm.api_key
   ```
   Solution: Set `ANTHROPIC_API_KEY` environment variable

2. **Invalid type**:
   ```
   Input should be a valid integer: database.port
   ```
   Solution: Ensure port is numeric (e.g., `5432` not `"5432"`)

3. **Invalid enum value**:
   ```
   Input should be 'sqlite' or 'postgresql': database.engine
   ```
   Solution: Use valid enum value

---

## Examples

### Example 1: Development Setup

```yaml
# config/environments/development.yaml
environment: development

database:
  engine: sqlite
  database: data/hansard_dev.db

vector_db:
  engine: chromadb
  persist_directory: data/vector_db_dev

llm:
  api_key: ${ANTHROPIC_API_KEY}
  monthly_budget_usd: 10.0

logging:
  level: DEBUG
  format: text
  output: stdout
```

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Example 2: Production Setup

```yaml
# config/environments/production.yaml
environment: production

database:
  engine: postgresql
  host: ${DB_HOST}
  port: 5432
  database: hansard_tales
  user: hansard
  password: ${DB_PASSWORD}

vector_db:
  engine: qdrant
  host: ${QDRANT_HOST}
  port: 6333

llm:
  api_key: ${ANTHROPIC_API_KEY}
  monthly_budget_usd: 100.0
  cache_enabled: true

monitoring:
  prometheus_enabled: true
  sentry_enabled: true
  sentry_dsn: ${SENTRY_DSN}

performance:
  caching:
    enabled: true
  connection_pooling:
    pool_size: 20
  rate_limiting:
    enabled: true
```

```bash
# .env
ENVIRONMENT=production
DB_HOST=postgres.example.com
DB_PASSWORD=secure-password
QDRANT_HOST=qdrant.example.com
ANTHROPIC_API_KEY=sk-ant-your-key-here
SENTRY_DSN=https://your-sentry-dsn
```

### Example 3: Custom Configuration

```python
from hansard_tales.config import Config, LLMConfig

# Override specific settings
config = Config(
    llm=LLMConfig(
        model="claude-3-5-sonnet-20241022",  # Use Sonnet instead of Haiku
        max_tokens=2048,
        monthly_budget_usd=50.0
    )
)
```

---

## Troubleshooting

### Issue: Configuration not loading

**Symptoms**: Default values used instead of config file

**Solutions**:
1. Check `ENVIRONMENT` variable is set correctly
2. Verify config file exists: `config/environments/{environment}.yaml`
3. Check file permissions (must be readable)
4. Validate YAML syntax (use online validator)

### Issue: Environment variables not working

**Symptoms**: Config uses default instead of env var

**Solutions**:
1. Use correct naming: `DB__HOST` not `DB_HOST`
2. Export variables: `export DB__HOST=localhost`
3. Check `.env` file is in project root
4. Verify no typos in variable names

### Issue: Database connection fails

**Symptoms**: `Connection refused` or `Authentication failed`

**Solutions**:
1. Verify database is running: `pg_isready` (PostgreSQL)
2. Check host/port are correct
3. Verify credentials are correct
4. Check firewall rules
5. For SQLite, verify directory exists and is writable

### Issue: Vector DB connection fails

**Symptoms**: `Connection refused` or `Collection not found`

**Solutions**:
1. Verify Qdrant is running: `curl http://localhost:6333/health`
2. Check host/port are correct
3. For ChromaDB, verify persist_directory exists and is writable
4. Check collections exist: `curl http://localhost:6333/collections`

### Issue: LLM API calls fail

**Symptoms**: `Authentication failed` or `Rate limit exceeded`

**Solutions**:
1. Verify API key is correct: `echo $ANTHROPIC_API_KEY`
2. Check API key has sufficient credits
3. Verify rate limits in config
4. Check monthly budget not exceeded
5. Enable caching to reduce API calls

### Issue: High memory usage

**Symptoms**: System runs out of memory

**Solutions**:
1. Reduce `batch_size` in embedding config
2. Reduce `max_workers` in processing config
3. Enable caching to reduce recomputation
4. Use smaller embedding model
5. Process documents in smaller batches

### Issue: Slow processing

**Symptoms**: Processing takes too long

**Solutions**:
1. Increase `max_workers` in processing config
2. Use GPU for embeddings: `device: cuda`
3. Increase `batch_size` for embeddings
4. Enable caching
5. Use connection pooling for database
6. Optimize database indexes

---

## Additional Resources

- [Architecture Documentation](ARCHITECTURE.md)
- [API Documentation](API.md)
- [Monitoring Guide](MONITORING.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

---

**Last Updated**: January 2025
**Version**: 1.0 (Phase 1)
