# Prometheus Configuration

This directory contains the Prometheus configuration for the Hansard Tales monitoring system.

## Overview

Prometheus is configured to scrape metrics from multiple services:

1. **Hansard Tales Application** (port 9090)
   - Custom application metrics (documents processed, processing time, errors, queue depth)
   - Scrape interval: 15 seconds

2. **PostgreSQL Database** (port 5432)
   - Database performance metrics
   - Scrape interval: 30 seconds

3. **Qdrant Vector Database** (port 6333)
   - Vector database metrics
   - Scrape interval: 30 seconds

4. **Prometheus Self-Monitoring** (port 9090)
   - Prometheus internal metrics
   - Scrape interval: 15 seconds

## Configuration Details

### Scrape Intervals

- **Application metrics**: 15 seconds (frequent updates for real-time monitoring)
- **Database metrics**: 30 seconds (less frequent, more stable metrics)
- **Evaluation interval**: 15 seconds (for alerting rules)

### Retention Policy

- **Time-based retention**: 30 days
- Data older than 30 days is automatically deleted
- Can be adjusted in `prometheus.yml` under `storage.tsdb.retention.time`

### Scrape Targets

#### Hansard Tales Application
- **Target**: `host.docker.internal:9090`
- **Metrics Path**: `/metrics`
- **Note**: Uses `host.docker.internal` to access the host machine from Docker container

#### PostgreSQL
- **Target**: `postgres:5432`
- **Note**: Requires postgres_exporter to be configured (future enhancement)

#### Qdrant
- **Target**: `qdrant:6333`
- **Metrics Path**: `/metrics`
- **Note**: Qdrant exposes metrics natively

## Starting the Metrics Server

To expose metrics from the Hansard Tales application:

```python
from hansard_tales.monitoring.metrics import start_metrics_server

# Start the metrics server on port 9090
start_metrics_server(port=9090)
```

## Accessing Prometheus

Once the Docker Compose stack is running:

1. **Prometheus UI**: http://localhost:9090
2. **Metrics endpoint**: http://localhost:9090/metrics
3. **Targets status**: http://localhost:9090/targets

## Available Metrics

### Application Metrics

1. **documents_processed_total**
   - Type: Counter
   - Labels: document_type, chamber, status
   - Description: Total number of documents processed

2. **document_processing_seconds**
   - Type: Histogram
   - Labels: document_type, chamber
   - Description: Time spent processing documents

3. **errors_total**
   - Type: Counter
   - Labels: component, error_type
   - Description: Total number of errors

4. **processing_queue_depth**
   - Type: Gauge
   - Labels: document_type
   - Description: Number of documents in processing queue

5. **vector_db_documents_total**
   - Type: Gauge
   - Labels: collection
   - Description: Total number of documents in vector DB

## Example Queries

### Documents Processed Per Second
```promql
rate(documents_processed_total[5m])
```

### 95th Percentile Processing Time
```promql
histogram_quantile(0.95, rate(document_processing_seconds_bucket[5m]))
```

### Error Rate
```promql
rate(errors_total[5m])
```

### Current Queue Depth
```promql
processing_queue_depth
```

## Configuration for Different Environments

### Development
- Uses `host.docker.internal` to access host machine
- Shorter retention period (30 days)
- More frequent scraping for debugging

### Production
- Should use proper service discovery or static IPs
- Longer retention period (90+ days)
- May include alerting rules
- Should configure external storage for long-term retention

## Troubleshooting

### Metrics Not Appearing

1. **Check if metrics server is running**:
   ```bash
   curl http://localhost:9090/metrics
   ```

2. **Check Prometheus targets**:
   - Visit http://localhost:9090/targets
   - Ensure all targets show as "UP"

3. **Check Docker networking**:
   ```bash
   docker-compose ps
   docker-compose logs prometheus
   ```

### Target Down

If a target shows as "DOWN":

1. **Verify service is running**:
   ```bash
   docker-compose ps
   ```

2. **Check service logs**:
   ```bash
   docker-compose logs <service-name>
   ```

3. **Verify network connectivity**:
   ```bash
   docker-compose exec prometheus ping <service-name>
   ```

## Future Enhancements

1. **Alerting Rules**: Add alert definitions for critical conditions
2. **PostgreSQL Exporter**: Configure postgres_exporter for detailed DB metrics
3. **Service Discovery**: Use Consul or Kubernetes service discovery
4. **Remote Storage**: Configure long-term storage (e.g., Thanos, Cortex)
5. **Recording Rules**: Pre-compute expensive queries

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Prometheus Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
