# Grafana Dashboards Quick Start Guide

This guide will help you get started with the Grafana dashboards for Hansard Tales in under 5 minutes.

## Step 1: Start the Services

Start the monitoring stack using Docker Compose:

```bash
# Start all services (including Grafana and Prometheus)
docker-compose up -d

# Or start only monitoring services
docker-compose up -d grafana prometheus
```

Wait for services to start (about 30 seconds):

```bash
# Check service status
docker-compose ps
```

## Step 2: Access Grafana

1. Open your browser and navigate to: **http://localhost:3000**

2. Log in with default credentials:
   - **Username**: `admin`
   - **Password**: `admin`

3. You'll be prompted to change the password. You can:
   - Set a new password, or
   - Click "Skip" to keep using `admin`

## Step 3: View Dashboards

1. Click on the **Dashboards** icon (four squares) in the left sidebar

2. Click **Browse**

3. Look for the **"Hansard Tales"** folder

4. You'll see three dashboards:
   - **System Overview** - Start here for general health
   - **Processing Metrics** - Detailed performance analysis
   - **Error Monitoring** - Error tracking and debugging

5. Click on **"Hansard Tales - System Overview"** to open it

## Step 4: Understanding the System Overview Dashboard

The System Overview dashboard shows six key panels:

### Top Row
- **Documents Processed (Success Rate)**: Line graph showing how many documents are being processed successfully over time
- **Processing Time (p95)**: Gauge showing the 95th percentile processing time (how long most documents take)

### Middle Row
- **Error Rate**: Line graph showing errors occurring in the system
- **Queue Depth**: Gauge showing how many documents are waiting to be processed

### Bottom Row
- **Vector DB Size**: Line graph showing growth of the vector database
- **Total Documents Processed**: Big number showing cumulative documents processed

## Step 5: Exploring Other Dashboards

### Processing Metrics Dashboard

Best for: Performance optimization and capacity planning

Key panels:
- **Processing Time Percentiles**: See p50, p95, and p99 processing times
- **Documents Processed per Hour**: Hourly volume by document type
- **Success vs Error Rate**: Visual comparison of success and failures
- **Overall Success Rate**: Current success rate gauge

### Error Monitoring Dashboard

Best for: Debugging and troubleshooting

Key panels:
- **Error Rate by Component**: Which components are having issues
- **Total Errors (Last Hour)**: Quick error count
- **Error Distribution**: Pie charts showing error breakdown
- **Error Rate Percentage**: Errors as percentage of operations

## Step 6: Customizing Time Range

All dashboards default to showing the last 6 hours of data. To change this:

1. Look for the time picker in the top-right corner
2. Click on it to see options:
   - **Last 5 minutes** - For real-time monitoring
   - **Last 1 hour** - For recent activity
   - **Last 6 hours** - Default view
   - **Last 24 hours** - Daily overview
   - **Last 7 days** - Weekly trends
   - **Custom range** - Pick specific dates

3. Click **Apply** to update the dashboard

## Step 7: Refreshing Data

Dashboards auto-refresh every 10 seconds by default. To change this:

1. Look for the refresh icon in the top-right corner
2. Click the dropdown next to it
3. Select refresh interval:
   - **Off** - Manual refresh only
   - **5s** - Very frequent updates
   - **10s** - Default
   - **30s** - Less frequent
   - **1m** - Minimal updates

## Common Use Cases

### Monitoring a Processing Job

1. Open **System Overview** dashboard
2. Set time range to **Last 5 minutes**
3. Set refresh to **5s**
4. Watch the **Documents Processed** panel for activity
5. Check **Error Rate** panel for any issues
6. Monitor **Queue Depth** to see if documents are backing up

### Investigating Slow Processing

1. Open **Processing Metrics** dashboard
2. Look at **Processing Time Percentiles**
3. Check if p95 or p99 are high (> 30 seconds)
4. Look at **Documents Processed per Hour** to see which document types are slow
5. Use **Processing Rate by Document Type** for detailed breakdown

### Debugging Errors

1. Open **Error Monitoring** dashboard
2. Check **Total Errors (Last Hour)** for recent error count
3. Look at **Error Distribution by Component** to identify problematic component
4. Check **Error Distribution by Type** to see what kind of errors
5. Use **Error Rate by Component** to see when errors started

### Checking System Health

Quick health check (30 seconds):

1. Open **System Overview**
2. Check these indicators:
   - ✅ **Documents Processed**: Should show activity (line going up)
   - ✅ **Processing Time**: Should be < 30 seconds
   - ✅ **Error Rate**: Should be near zero
   - ✅ **Queue Depth**: Should be < 50
   - ✅ **Success Rate**: Should be > 95%

If any indicator is red, investigate using the specialized dashboards.

## Troubleshooting

### "No Data" in Panels

**Problem**: Panels show "No data" or empty graphs

**Solutions**:
1. Check if Prometheus is running:
   ```bash
   docker-compose ps prometheus
   ```

2. Verify metrics are being exposed:
   ```bash
   curl http://localhost:9090/metrics
   ```

3. Check if your application is running and exposing metrics

4. Verify Prometheus is scraping:
   - Open http://localhost:9090
   - Go to Status → Targets
   - Check if `hansard_tales` is UP

### Dashboards Not Appearing

**Problem**: Can't find Hansard Tales dashboards

**Solutions**:
1. Wait 30 seconds after starting Grafana (provisioning takes time)

2. Refresh the browser page

3. Check Grafana logs:
   ```bash
   docker-compose logs grafana | grep -i error
   ```

4. Manually import dashboards:
   - Go to Dashboards → Import
   - Upload JSON files from `config/grafana/dashboards/`

### Slow Dashboard Loading

**Problem**: Dashboards take a long time to load

**Solutions**:
1. Reduce time range (e.g., from 24h to 6h)
2. Increase refresh interval (e.g., from 5s to 30s)
3. Close unused browser tabs
4. Check Prometheus performance

## Next Steps

Now that you're familiar with the basics:

1. **Set up alerts**: Configure notifications for critical issues
2. **Customize dashboards**: Add panels for your specific needs
3. **Create new dashboards**: Build dashboards for specific workflows
4. **Explore Prometheus**: Learn PromQL for custom queries
5. **Read the full README**: Check `config/grafana/README.md` for advanced features

## Quick Reference

### URLs
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Metrics Endpoint**: http://localhost:9090/metrics

### Default Credentials
- **Username**: admin
- **Password**: admin

### Dashboard UIDs
- **System Overview**: `hansard-tales-overview`
- **Processing Metrics**: `hansard-tales-processing`
- **Error Monitoring**: `hansard-tales-errors`

### Key Metrics
- `documents_processed_total` - Documents processed counter
- `document_processing_seconds` - Processing time histogram
- `errors_total` - Error counter
- `processing_queue_depth` - Queue size gauge
- `vector_db_documents_total` - Vector DB size gauge

### Useful PromQL Queries

```promql
# Success rate over 5 minutes
rate(documents_processed_total{status="success"}[5m])

# 95th percentile processing time
histogram_quantile(0.95, rate(document_processing_seconds_bucket[5m]))

# Error rate
rate(errors_total[5m])

# Current queue depth
processing_queue_depth

# Total documents in vector DB
sum(vector_db_documents_total)
```

## Getting Help

- **Full Documentation**: See `config/grafana/README.md`
- **Grafana Docs**: https://grafana.com/docs/
- **Prometheus Docs**: https://prometheus.io/docs/
- **Project Issues**: Open an issue in the repository

Happy monitoring! 📊
