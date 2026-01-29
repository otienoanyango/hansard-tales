# Sentry Error Tracking Setup

This guide explains how to configure and use Sentry for error tracking and monitoring in Hansard Tales.

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

Sentry provides real-time error tracking and monitoring for the Hansard Tales system. It captures:

- **Exceptions**: Unhandled and handled exceptions with full stack traces
- **Messages**: Custom log messages and warnings
- **Breadcrumbs**: Trail of events leading up to errors
- **Performance**: Transaction traces and performance metrics
- **Context**: User information, tags, and custom data

### Benefits

- **Real-time Alerts**: Get notified immediately when errors occur
- **Context-Rich**: See exactly what happened before an error
- **Performance Monitoring**: Track slow operations and bottlenecks
- **Release Tracking**: Monitor errors across different deployments
- **Search & Filter**: Find specific errors using tags and filters

## Setup

### 1. Create Sentry Account

1. Go to [sentry.io](https://sentry.io)
2. Sign up for a free account (5,000 events/month)
3. Create a new project for "Python"
4. Copy your DSN (Data Source Name)

### 2. Install Dependencies

The Sentry SDK is already included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Add your Sentry DSN to your environment. There are multiple ways to set environment variables:

**Option 1: Direct Environment Variables (Recommended)**
```bash
# Using SENTRY_ prefix (works with MonitoringConfig directly)
export SENTRY_SENTRY_ENABLED=true
export SENTRY_DSN="https://your-dsn@sentry.io/project-id"
```

**Option 2: Nested Environment Variables**
```bash
# Using MONITORING__ prefix (works with full Config)
export MONITORING__SENTRY_ENABLED=true
export MONITORING__DSN="https://your-dsn@sentry.io/project-id"
```

**Option 3: .env File**
```bash
# .env
# Either format works:
SENTRY_SENTRY_ENABLED=true
SENTRY_DSN=https://your-dsn@sentry.io/project-id

# Or:
MONITORING__SENTRY_ENABLED=true
MONITORING__DSN=https://your-dsn@sentry.io/project-id
```

**Option 3: Configuration File**
```yaml
# config/production.yaml
monitoring:
  sentry_enabled: true
  # DSN should be set via environment variable for security
```

## Configuration

### Basic Configuration

```python
from hansard_tales.config.settings import get_config
from hansard_tales.monitoring import configure_sentry

# Load configuration
config = get_config()

# Configure Sentry
configure_sentry(config.monitoring, config.environment)
```

### Configuration Options

The `MonitoringConfig` class provides the following Sentry settings:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `sentry_enabled` | bool | `False` | Enable/disable Sentry |
| `dsn` | str | `""` | Sentry DSN (from environment) |

Additional settings configured automatically:

- **Environment**: Set from `config.environment` (development/staging/production)
- **Traces Sample Rate**: 10% of transactions for performance monitoring
- **Sample Rate**: 100% of errors captured
- **Logging Integration**: INFO+ as breadcrumbs, ERROR+ as events
- **Max Breadcrumbs**: 50 events tracked before an error

### Environment-Specific Configuration

**Development**:
```yaml
environment: development
monitoring:
  sentry_enabled: false  # Disable in development
```

**Staging**:
```yaml
environment: staging
monitoring:
  sentry_enabled: true
```

**Production**:
```yaml
environment: production
monitoring:
  sentry_enabled: true
```

## Usage

### 1. Exception Capture

Capture exceptions with context:

```python
from hansard_tales.monitoring import capture_exception

try:
    process_pdf(pdf_path)
except Exception as e:
    event_id = capture_exception(
        e,
        context={
            "pdf_path": str(pdf_path),
            "document_type": "hansard",
            "chamber": "national_assembly"
        },
        level="error"
    )
    logger.error(f"Processing failed: {event_id}")
    raise
```

### 2. Message Capture

Send custom messages to Sentry:

```python
from hansard_tales.monitoring import capture_message

# Info message
capture_message(
    "Processing started",
    level="info",
    context={"document_count": 10}
)

# Warning message
capture_message(
    "Processing completed with warnings",
    level="warning",
    context={"warnings": 5, "errors": 0}
)
```

### 3. User Context

Associate errors with specific users:

```python
from hansard_tales.monitoring import set_user

set_user(
    user_id="user123",
    email="user@example.com",
    username="john_doe"
)
```

### 4. Tags

Add searchable tags to events:

```python
from hansard_tales.monitoring import set_tag

set_tag("document_type", "hansard")
set_tag("chamber", "national_assembly")
set_tag("processing_stage", "pdf_extraction")
```

### 5. Breadcrumbs

Track the sequence of events:

```python
from hansard_tales.monitoring import add_breadcrumb

add_breadcrumb(
    "Started PDF download",
    category="download",
    level="info"
)

add_breadcrumb(
    "PDF downloaded successfully",
    category="download",
    level="info",
    data={"file_size": 1024000, "duration": 2.5}
)

add_breadcrumb(
    "Starting text extraction",
    category="processing",
    level="info"
)
```

### 6. Flushing Events

Ensure all events are sent before shutdown:

```python
from hansard_tales.monitoring import flush

# Before application exit
success = flush(timeout=5.0)
if not success:
    logger.warning("Some Sentry events may not have been sent")
```

## Best Practices

### 1. Use Context Liberally

Always include relevant context with errors:

```python
# Good: Rich context
capture_exception(
    e,
    context={
        "pdf_path": str(pdf_path),
        "document_type": "hansard",
        "chamber": "national_assembly",
        "page_count": 50,
        "file_size": 1024000
    }
)

# Bad: No context
capture_exception(e)
```

### 2. Set Tags for Filtering

Use tags to make errors searchable:

```python
# Set tags at the start of processing
set_tag("document_type", "hansard")
set_tag("chamber", "national_assembly")
set_tag("parliament_term", "13")
```

### 3. Add Breadcrumbs for Context

Track important events:

```python
add_breadcrumb("Validating PDF", category="validation")
add_breadcrumb("Extracting text", category="processing")
add_breadcrumb("Storing in database", category="storage")
```

### 4. Use Appropriate Severity Levels

- **fatal**: System is unusable
- **error**: Operation failed, needs attention
- **warning**: Something unexpected, but handled
- **info**: Informational message
- **debug**: Detailed debugging information

### 5. Don't Capture Sensitive Data

Avoid capturing PII (Personally Identifiable Information):

```python
# Bad: Includes sensitive data
capture_exception(e, context={"email": user_email, "password": password})

# Good: No sensitive data
capture_exception(e, context={"user_id": user_id})
```

### 6. Flush Before Shutdown

Always flush events before application exit:

```python
import atexit
from hansard_tales.monitoring import flush

# Register flush on exit
atexit.register(lambda: flush(timeout=5.0))
```

## Integration with Existing Code

### PDF Processor

```python
from hansard_tales.monitoring import capture_exception, add_breadcrumb, set_tag

def process_pdf(pdf_path: Path) -> ProcessedPDF:
    """Process PDF with Sentry tracking."""
    set_tag("document_type", "hansard")

    add_breadcrumb("Starting PDF processing", category="processing")

    try:
        # Extract text
        add_breadcrumb("Extracting text", category="processing")
        text = extract_text(pdf_path)

        # Store in database
        add_breadcrumb("Storing in database", category="storage")
        store_document(text)

        return ProcessedPDF(status="success")

    except Exception as e:
        capture_exception(
            e,
            context={"pdf_path": str(pdf_path)},
            level="error"
        )
        raise
```

### Web Scraper

```python
from hansard_tales.monitoring import capture_exception, capture_message, set_tag

def scrape_hansard(start_date: date, end_date: date):
    """Scrape Hansard with Sentry tracking."""
    set_tag("scraper", "hansard")
    set_tag("chamber", "national_assembly")

    try:
        documents = fetch_documents(start_date, end_date)

        if not documents:
            capture_message(
                "No documents found",
                level="warning",
                context={"start_date": str(start_date), "end_date": str(end_date)}
            )

        return documents

    except Exception as e:
        capture_exception(
            e,
            context={
                "start_date": str(start_date),
                "end_date": str(end_date)
            },
            level="error"
        )
        raise
```

## Troubleshooting

### Sentry Not Capturing Events

**Check Configuration**:
```python
from hansard_tales.config.settings import get_config

config = get_config()
print(f"Sentry enabled: {config.monitoring.sentry_enabled}")
print(f"Sentry DSN: {config.monitoring.dsn[:20]}...")  # Don't print full DSN
```

**Check Environment Variables**:
```bash
# Check SENTRY_ prefix format
echo $SENTRY_SENTRY_ENABLED
echo $SENTRY_DSN

# Or check MONITORING__ prefix format
echo $MONITORING__SENTRY_ENABLED
echo $MONITORING__DSN
```

**Test Manually**:
```python
from hansard_tales.monitoring import configure_sentry, capture_message
from hansard_tales.config.settings import get_config

config = get_config()
configure_sentry(config.monitoring, config.environment)

# This should appear in Sentry
event_id = capture_message("Test message", level="info")
print(f"Event ID: {event_id}")
```

### Events Not Appearing in Sentry

1. **Check DSN**: Ensure DSN is correct
2. **Check Network**: Ensure outbound HTTPS is allowed
3. **Check Rate Limits**: Free tier has 5,000 events/month
4. **Flush Events**: Call `flush()` before exit
5. **Check Filters**: Ensure events aren't filtered in Sentry settings

### Too Many Events

**Adjust Sample Rate**:
```python
# In sentry_config.py, modify:
sentry_sdk.init(
    dsn=config.dsn,
    sample_rate=0.5,  # Capture 50% of errors
    traces_sample_rate=0.05,  # Sample 5% of transactions
)
```

**Filter Events**:
```python
def before_send(event, hint):
    """Filter events before sending to Sentry."""
    # Don't send certain errors
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if isinstance(exc_value, KeyboardInterrupt):
            return None
    return event

sentry_sdk.init(
    dsn=config.dsn,
    before_send=before_send
)
```

## Monitoring Dashboard

### Sentry Dashboard

Access your Sentry dashboard at: https://sentry.io/organizations/your-org/issues/

**Key Sections**:
- **Issues**: All captured errors and exceptions
- **Performance**: Transaction traces and slow operations
- **Releases**: Track errors across deployments
- **Alerts**: Configure notifications for critical errors

### Useful Queries

**Errors by Document Type**:
```
document_type:hansard
```

**Errors in Production**:
```
environment:production
```

**Recent Errors**:
```
is:unresolved age:-24h
```

## Cost Management

### Free Tier Limits

- **Events**: 5,000 errors/month
- **Performance**: 10,000 transactions/month
- **Attachments**: 1 GB/month
- **Data Retention**: 30 days

### Staying Within Limits

1. **Sample Transactions**: Only 10% by default
2. **Filter Noise**: Don't capture expected errors
3. **Use Breadcrumbs**: More context, fewer events
4. **Monitor Usage**: Check Sentry dashboard regularly

## Examples

See `examples/sentry_example.py` for complete working examples:

```bash
python examples/sentry_example.py
```

## References

- [Sentry Python SDK Documentation](https://docs.sentry.io/platforms/python/)
- [Sentry Best Practices](https://docs.sentry.io/product/best-practices/)
- [Sentry Pricing](https://sentry.io/pricing/)
