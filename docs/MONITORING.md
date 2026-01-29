# Monitoring Guide

This guide explains how to use the monitoring infrastructure in Hansard Tales.

## Overview

The monitoring system consists of:

1. **Prometheus**: Metrics collection and storage
2. **Grafana**: Metrics visualization (configured separately)
3. **Application Metrics**: Custom metrics exposed by the application

## Quick Start

### 1. Start the Monitoring Stack

Start all services including Prometheus:

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Qdrant (port 6333)
- Prometheus (port 9090)
- Grafana (port 3000)

### 2. Start the Application Metrics Server

In your application code:

```python
from hansard_tales.monitoring.metrics import start_metrics_server

# Start metrics server
start_metrics_server(port=9090)
```

Or run the example:

```bash
python examples/prometheus_example.py
```

### 3. Access the Monitoring UIs

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Metrics Endpoint**: http://localhost:9090/metrics

## Using Metrics in Your Code

### Automatic Tracking with Decorator

The easiest way to track metrics is using the `@track_processing_time` decorator:

```python
from hansard_tales.monitoring.metrics import track_processing_time

@track_processing_time('hansard', 'national_assembly')
def process_hansard(pdf_path):
    # Your processing logic here
    pass
```

This automatically tracks:
- Processing time (histogram)
- Success/failure count (counter)
- Errors by type (counter)

### Manual Metrics Updates

For more control, update metrics manually:

```python
from hansard_tales.monitoring.metrics import (
    documents_processed,
    processing_time,
    error_count,
    queue_depth,
    vector_db_size
)

# Increment counter
documents_processed.labels(
    document_type='hansard',
    chamber='national_assembly',
    status='success'
).inc()

# Record timing
with processing_time.labels(
    document_type='hansard',
    chamber='national_assembly'
).time():
    # Your code here
    pass

# Set gauge value
queue_depth.labels(document_type='hansard').set(42)

# Track errors
error_count.labels(
    component='scraper',
    error_type='NetworkError'
).inc()
```

## Available Metrics

### 1. documents_processed_total (Counter)

Total number of documents processed.

**Labels**:
- `document_type`: Type of document (hansard, votes, bills, etc.)
- `chamber`: Parliamentary chamber (national_assembly, senate)
- `status`: Processing status (success, error)

**Example Query**:
```promql
# Documents processed per second
rate(documents_processed_total[5m])

# Success rate
rate(documents_processed_total{status="success"}[5m])
/
rate(documents_processed_total[5m])
```

### 2. document_processing_seconds (Histogram)

Time spent processing documents.

**Labels**:
- `document_type`: Type of document
- `chamber`: Parliamentary chamber

**Example Query**:
```promql
# 95th percentile processing time
histogram_quantile(0.95, rate(document_processing_seconds_bucket[5m]))

# Average processing time
rate(document_processing_seconds_sum[5m])
/
rate(document_processing_seconds_count[5m])
```

### 3. errors_total (Counter)

Total number of errors.

**Labels**:
- `component`: Component where error occurred (scraper, processor, storage)
- `error_type`: Type of error (NetworkError, ParseError, etc.)

**Example Query**:
```promql
# Error rate
rate(errors_total[5m])

# Errors by component
sum by (component) (rate(errors_total[5m]))
```

### 4. processing_queue_depth (Gauge)

Number of documents in processing queue.

**Labels**:
- `document_type`: Type of document

**Example Query**:
```promql
# Current queue depth
processing_queue_depth

# Queue depth by document type
sum by (document_type) (processing_queue_depth)
```

### 5. vector_db_documents_total (Gauge)

Total number of documents in vector database.

**Labels**:
- `collection`: Vector DB collection name

**Example Query**:
```promql
# Total documents in vector DB
sum(vector_db_documents_total)

# Documents by collection
vector_db_documents_total
```

## Common Queries

### System Health

```promql
# Overall processing rate
sum(rate(documents_processed_total[5m]))

# Error rate percentage
100 * sum(rate(errors_total[5m])) / sum(rate(documents_processed_total[5m]))

# Average processing time
avg(rate(document_processing_seconds_sum[5m]) / rate(document_processing_seconds_count[5m]))
```

### Performance Analysis

```promql
# Slowest document types (p95)
histogram_quantile(0.95, sum by (document_type, le) (rate(document_processing_seconds_bucket[5m])))

# Processing time by chamber
histogram_quantile(0.95, sum by (chamber, le) (rate(document_processing_seconds_bucket[5m])))
```

### Error Analysis

```promql
# Top error types
topk(5, sum by (error_type) (rate(errors_total[5m])))

# Errors by component
sum by (component) (rate(errors_total[5m]))
```

### Capacity Planning

```promql
# Queue growth rate
deriv(processing_queue_depth[5m])

# Vector DB growth rate
deriv(vector_db_documents_total[1h])
```

## Alerting (Future)

Example alert rules (to be added to `config/prometheus.yml`):

```yaml
groups:
  - name: hansard_tales
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"

      # Slow processing
      - alert: SlowProcessing
        expr: histogram_quantile(0.95, rate(document_processing_seconds_bucket[5m])) > 60
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Processing time is slow"

      # Queue backup
      - alert: QueueBackup
        expr: processing_queue_depth > 1000
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Processing queue is backing up"
```

## Grafana Dashboards

Hansard Tales includes pre-configured Grafana dashboards that are automatically provisioned when you start the monitoring stack.

### Quick Start

1. **Start Grafana**:
   ```bash
   docker-compose up -d grafana
   ```

2. **Access Grafana**:
   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `admin` (change on first login)

3. **View Dashboards**:
   - Navigate to Dashboards → Browse
   - Open the "Hansard Tales" folder
   - Select a dashboard to view

### Available Dashboards

#### 1. System Overview (`hansard-tales-overview`)

High-level view of system health and performance.

**Panels**:
- Documents Processed (Success Rate)
- Processing Time (p95)
- Error Rate
- Queue Depth
- Vector DB Size
- Total Documents Processed

**Best for**: Quick health checks, identifying bottlenecks

#### 2. Processing Metrics (`hansard-tales-processing`)

Detailed analysis of document processing performance.

**Panels**:
- Processing Time Percentiles (p50, p95, p99)
- Documents Processed per Hour
- Success vs Error Rate
- Overall Success Rate
- Processing Rate by Document Type and Status

**Best for**: Performance optimization, capacity planning

#### 3. Error Monitoring (`hansard-tales-errors`)

Comprehensive error tracking and analysis.

**Panels**:
- Error Rate by Component
- Total Errors (Last Hour)
- Error Distribution by Type
- Error Distribution by Component
- Errors per Hour (Detailed)
- Error Rate Percentage by Component

**Best for**: Debugging, identifying problematic components

### Dashboard Documentation

For detailed information about the dashboards:

- **Full Guide**: See `config/grafana/README.md`
- **Quick Start**: See `config/grafana/QUICKSTART.md`

### Creating Custom Dashboards

1. Open Grafana: http://localhost:3000
2. Login with admin/admin
3. Click "+" → "Dashboard"
4. Add panels with PromQL queries

### Example Panel Configurations

**Documents Processed**:
- Query: `rate(documents_processed_total[5m])`
- Visualization: Time series
- Legend: `{{document_type}} - {{status}}`

**Processing Time (p95)**:
- Query: `histogram_quantile(0.95, rate(document_processing_seconds_bucket[5m]))`
- Visualization: Time series
- Unit: seconds

**Error Rate**:
- Query: `rate(errors_total[5m])`
- Visualization: Time series
- Legend: `{{component}} - {{error_type}}`

**Queue Depth**:
- Query: `processing_queue_depth`
- Visualization: Gauge
- Thresholds: 0-100 (green), 100-500 (yellow), 500+ (red)

### Importing/Exporting Dashboards

**Export a Dashboard**:
1. Open the dashboard
2. Click the gear icon (Dashboard settings)
3. Go to "JSON Model"
4. Copy the JSON
5. Save to `config/grafana/dashboards/`

**Import a Dashboard**:
1. Click "+" → "Import"
2. Upload JSON file or paste JSON
3. Select Prometheus datasource
4. Click "Import"

## Troubleshooting

### Metrics Not Appearing

1. **Check if metrics server is running**:
   ```bash
   curl http://localhost:9090/metrics
   ```

2. **Check Prometheus targets**:
   - Visit http://localhost:9090/targets
   - Ensure "hansard_tales" target is UP

3. **Check application logs**:
   ```bash
   # Look for "Metrics server started" message
   tail -f data/logs/hansard_tales.log
   ```

### Prometheus Not Scraping

1. **Check Prometheus logs**:
   ```bash
   docker-compose logs prometheus
   ```

2. **Verify configuration**:
   ```bash
   # Check config is valid
   docker-compose exec prometheus promtool check config /etc/prometheus/prometheus.yml
   ```

3. **Check network connectivity**:
   ```bash
   # From Prometheus container
   docker-compose exec prometheus wget -O- http://host.docker.internal:9090/metrics
   ```

### High Memory Usage

If Prometheus uses too much memory:

1. **Reduce retention period** in `config/prometheus.yml`:
   ```yaml
   storage:
     tsdb:
       retention.time: 7d  # Reduce from 30d
   ```

2. **Reduce scrape frequency**:
   ```yaml
   global:
     scrape_interval: 30s  # Increase from 15s
   ```

3. **Add storage size limit**:
   ```yaml
   storage:
     tsdb:
       retention.size: 5GB
   ```

## Best Practices

### 1. Use Labels Wisely

- Keep label cardinality low (< 100 unique values per label)
- Don't use user IDs or timestamps as labels
- Use consistent label names across metrics

### 2. Choose the Right Metric Type

- **Counter**: For cumulative values (documents processed, errors)
- **Gauge**: For current values (queue depth, DB size)
- **Histogram**: For distributions (processing time, request size)

### 3. Naming Conventions

- Use `_total` suffix for counters
- Use `_seconds` suffix for durations
- Use descriptive names: `documents_processed_total` not `docs`

### 4. Performance

- Use the decorator for automatic tracking
- Batch metric updates when possible
- Don't create metrics in hot loops

### 5. Testing

- Test metrics in development before production
- Verify metrics appear in Prometheus UI
- Check that queries return expected results

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
