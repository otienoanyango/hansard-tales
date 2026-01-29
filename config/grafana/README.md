# Grafana Dashboards for Hansard Tales

This directory contains Grafana dashboard configurations and provisioning files for monitoring the Hansard Tales system.

## Overview

The Grafana setup provides comprehensive monitoring and visualization of system metrics collected by Prometheus. The dashboards are automatically provisioned when Grafana starts via Docker Compose.

## Directory Structure

```
config/grafana/
├── README.md                           # This file
├── datasources/
│   └── prometheus.yml                  # Prometheus datasource configuration
└── dashboards/
    ├── dashboard-provider.yml          # Dashboard provisioning configuration
    ├── system-overview.json            # Main system overview dashboard
    ├── processing-metrics.json         # Detailed processing metrics
    └── error-monitoring.json           # Error tracking and analysis
```

## Available Dashboards

### 1. System Overview Dashboard

**UID**: `hansard-tales-overview`
**Purpose**: High-level view of system health and performance

**Panels**:
- **Documents Processed (Success Rate)**: Rate of successfully processed documents over time
- **Processing Time (p95)**: 95th percentile processing time gauge
- **Error Rate**: Rate of errors across all components
- **Queue Depth**: Current number of documents in processing queue
- **Vector DB Size**: Total documents stored in vector database
- **Total Documents Processed**: Cumulative count of all processed documents

**Use Cases**:
- Quick health check of the system
- Identifying processing bottlenecks
- Monitoring overall system performance
- Tracking vector database growth

### 2. Processing Metrics Dashboard

**UID**: `hansard-tales-processing`
**Purpose**: Detailed analysis of document processing performance

**Panels**:
- **Processing Time Percentiles**: p50, p95, and p99 processing times
- **Documents Processed per Hour**: Hourly processing volume by document type
- **Success vs Error Rate**: Stacked percentage view of success/error rates
- **Overall Success Rate**: Gauge showing current success rate
- **Processing Rate by Document Type and Status**: Detailed breakdown of processing rates

**Use Cases**:
- Performance optimization and tuning
- Identifying slow document types
- Tracking processing trends over time
- Capacity planning

### 3. Error Monitoring Dashboard

**UID**: `hansard-tales-errors`
**Purpose**: Comprehensive error tracking and analysis

**Panels**:
- **Error Rate by Component**: Time series of errors per component
- **Total Errors (Last Hour)**: Quick stat showing recent error count
- **Error Distribution by Type**: Pie chart of error types
- **Error Distribution by Component**: Pie chart of errors per component
- **Errors per Hour (Detailed)**: Stacked bar chart of hourly errors
- **Error Rate Percentage by Component**: Error rate as percentage of total operations

**Use Cases**:
- Identifying problematic components
- Tracking error trends
- Debugging system issues
- Monitoring error recovery

## Metrics Reference

### Documents Processed

```promql
documents_processed_total{document_type, chamber, status}
```

**Labels**:
- `document_type`: Type of document (hansard, votes, bill, etc.)
- `chamber`: Parliamentary chamber (national_assembly, senate)
- `status`: Processing status (success, error)

**Example Queries**:
```promql
# Success rate over 5 minutes
rate(documents_processed_total{status="success"}[5m])

# Total documents processed
sum(documents_processed_total)

# Success rate by document type
sum by (document_type) (rate(documents_processed_total{status="success"}[5m]))
```

### Processing Time

```promql
document_processing_seconds{document_type, chamber}
```

**Type**: Histogram
**Labels**:
- `document_type`: Type of document
- `chamber`: Parliamentary chamber

**Example Queries**:
```promql
# 95th percentile processing time
histogram_quantile(0.95, rate(document_processing_seconds_bucket[5m]))

# Average processing time
rate(document_processing_seconds_sum[5m]) / rate(document_processing_seconds_count[5m])

# Processing time by document type
histogram_quantile(0.95, sum by (document_type, le) (rate(document_processing_seconds_bucket[5m])))
```

### Error Count

```promql
errors_total{component, error_type}
```

**Labels**:
- `component`: System component (processor, scraper, storage, etc.)
- `error_type`: Exception class name

**Example Queries**:
```promql
# Error rate over 5 minutes
rate(errors_total[5m])

# Errors by component
sum by (component) (increase(errors_total[1h]))

# Most common error types
topk(5, sum by (error_type) (increase(errors_total[1h])))
```

### Queue Depth

```promql
processing_queue_depth{document_type}
```

**Type**: Gauge
**Labels**:
- `document_type`: Type of document in queue

**Example Queries**:
```promql
# Current queue depth
processing_queue_depth

# Queue depth by document type
sum by (document_type) (processing_queue_depth)

# Maximum queue depth in last hour
max_over_time(processing_queue_depth[1h])
```

### Vector DB Size

```promql
vector_db_documents_total{collection}
```

**Type**: Gauge
**Labels**:
- `collection`: Vector database collection name

**Example Queries**:
```promql
# Total documents in vector DB
sum(vector_db_documents_total)

# Documents by collection
vector_db_documents_total

# Growth rate
rate(vector_db_documents_total[1h])
```

## Setup Instructions

### Prerequisites

- Docker and Docker Compose installed
- Prometheus running and collecting metrics
- Hansard Tales application exposing metrics on port 9090

### Quick Start

1. **Start the monitoring stack**:
   ```bash
   docker-compose up -d grafana prometheus
   ```

2. **Access Grafana**:
   - URL: http://localhost:3000
   - Default credentials:
     - Username: `admin`
     - Password: `admin` (you'll be prompted to change this)

3. **Verify dashboards**:
   - Navigate to Dashboards → Browse
   - Look for the "Hansard Tales" folder
   - Open any dashboard to view metrics

### Manual Dashboard Import

If automatic provisioning doesn't work, you can manually import dashboards:

1. Log in to Grafana
2. Click the "+" icon → Import
3. Upload the JSON file or paste the JSON content
4. Select the Prometheus datasource
5. Click "Import"

### Datasource Configuration

The Prometheus datasource is automatically configured via `datasources/prometheus.yml`. If you need to configure it manually:

1. Go to Configuration → Data Sources
2. Click "Add data source"
3. Select "Prometheus"
4. Set URL to `http://prometheus:9090`
5. Click "Save & Test"

## Customization

### Modifying Dashboards

1. **Via Grafana UI**:
   - Open the dashboard
   - Click the gear icon (Dashboard settings)
   - Make your changes
   - Click "Save dashboard"
   - Export JSON via "JSON Model" in settings
   - Replace the JSON file in `config/grafana/dashboards/`

2. **Via JSON Files**:
   - Edit the JSON files directly
   - Restart Grafana to reload: `docker-compose restart grafana`

### Adding New Panels

To add a new panel to an existing dashboard:

1. Open the dashboard in Grafana
2. Click "Add panel" → "Add a new panel"
3. Configure the query and visualization
4. Save the panel
5. Export and update the JSON file

### Creating New Dashboards

1. Create a new dashboard in Grafana UI
2. Add panels and configure as needed
3. Export the dashboard JSON
4. Save to `config/grafana/dashboards/`
5. Restart Grafana to provision

## Alerting

Grafana supports alerting based on metric thresholds. To set up alerts:

1. Open a dashboard panel
2. Click "Edit"
3. Go to the "Alert" tab
4. Configure alert conditions
5. Set notification channels

**Recommended Alerts**:
- Error rate exceeds 5% for 5 minutes
- Processing time p95 exceeds 30 seconds
- Queue depth exceeds 100 documents
- Success rate drops below 95%

## Troubleshooting

### Dashboards Not Appearing

1. Check Grafana logs:
   ```bash
   docker-compose logs grafana
   ```

2. Verify provisioning configuration:
   ```bash
   docker-compose exec grafana cat /etc/grafana/provisioning/dashboards/dashboard-provider.yml
   ```

3. Check file permissions:
   ```bash
   ls -la config/grafana/dashboards/
   ```

### No Data in Panels

1. Verify Prometheus is scraping metrics:
   - Open Prometheus UI: http://localhost:9090
   - Go to Status → Targets
   - Check if `hansard_tales` target is UP

2. Check if metrics are being exposed:
   ```bash
   curl http://localhost:9090/metrics
   ```

3. Verify datasource connection:
   - Go to Configuration → Data Sources
   - Click on Prometheus
   - Click "Save & Test"

### Slow Dashboard Loading

1. Reduce time range (e.g., from 24h to 6h)
2. Increase scrape interval in Prometheus
3. Use recording rules for complex queries
4. Reduce panel refresh rate

## Best Practices

### Dashboard Design

- **Keep it simple**: Focus on key metrics
- **Use appropriate visualizations**: Time series for trends, gauges for current values, pie charts for distributions
- **Add descriptions**: Use panel descriptions to explain metrics
- **Group related panels**: Organize panels logically
- **Use consistent colors**: Green for success, red for errors, yellow for warnings

### Query Optimization

- **Use rate() for counters**: Always use `rate()` or `increase()` with counter metrics
- **Choose appropriate time ranges**: Use `[5m]` for recent trends, `[1h]` for longer patterns
- **Aggregate when possible**: Use `sum by ()` to reduce cardinality
- **Use recording rules**: Pre-compute expensive queries in Prometheus

### Monitoring Strategy

- **Start with overview**: Use System Overview for general health
- **Drill down as needed**: Use specialized dashboards for detailed analysis
- **Set up alerts**: Don't rely on manual monitoring
- **Review regularly**: Check dashboards daily during development, weekly in production
- **Iterate**: Continuously improve dashboards based on actual usage

## Integration with Application

The dashboards visualize metrics exposed by the Hansard Tales application. To ensure proper integration:

1. **Start metrics server** in your application:
   ```python
   from hansard_tales.monitoring.metrics import start_metrics_server

   start_metrics_server(port=9090)
   ```

2. **Use tracking decorators**:
   ```python
   from hansard_tales.monitoring.metrics import track_processing_time

   @track_processing_time('hansard', 'national_assembly')
   def process_hansard(pdf_path):
       # Processing logic
       pass
   ```

3. **Update metrics manually** when needed:
   ```python
   from hansard_tales.monitoring.metrics import queue_depth, vector_db_size

   queue_depth.labels(document_type='hansard').set(current_queue_size)
   vector_db_size.labels(collection='documents').set(total_documents)
   ```

## Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/best-practices-for-creating-dashboards/)
- [Prometheus Metric Types](https://prometheus.io/docs/concepts/metric_types/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Grafana and Prometheus logs
3. Consult the main project documentation
4. Open an issue in the project repository
