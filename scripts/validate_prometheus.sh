#!/bin/bash
# Validation script for Prometheus configuration

set -e

echo "Validating Prometheus configuration..."
echo "======================================"

# Check if config file exists
if [ ! -f "config/prometheus.yml" ]; then
    echo "❌ Error: config/prometheus.yml not found"
    exit 1
fi
echo "✓ Configuration file exists"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    exit 1
fi
echo "✓ Docker Compose file exists"

# Validate YAML syntax using Python
python3 << 'EOF'
import yaml
import sys

try:
    with open('config/prometheus.yml', 'r') as f:
        config = yaml.safe_load(f)

    # Check required sections
    required_sections = ['global', 'scrape_configs']
    for section in required_sections:
        if section not in config:
            print(f"❌ Error: Missing required section: {section}")
            sys.exit(1)

    # Check scrape configs
    if not config['scrape_configs']:
        print("❌ Error: No scrape configs defined")
        sys.exit(1)

    # Check for required jobs
    job_names = [job['job_name'] for job in config['scrape_configs']]
    required_jobs = ['hansard_tales', 'prometheus']
    for job in required_jobs:
        if job not in job_names:
            print(f"❌ Error: Missing required job: {job}")
            sys.exit(1)

    print("✓ YAML syntax is valid")
    print(f"✓ Found {len(config['scrape_configs'])} scrape jobs")
    print(f"  Jobs: {', '.join(job_names)}")

except yaml.YAMLError as e:
    print(f"❌ Error: Invalid YAML syntax: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
EOF

# Check if metrics module exists
if [ ! -f "hansard_tales/monitoring/metrics.py" ]; then
    echo "❌ Error: metrics.py not found"
    exit 1
fi
echo "✓ Metrics module exists"

# Check if example script exists
if [ ! -f "examples/prometheus_example.py" ]; then
    echo "❌ Error: prometheus_example.py not found"
    exit 1
fi
echo "✓ Example script exists"

echo ""
echo "======================================"
echo "✓ All validations passed!"
echo ""
echo "Next steps:"
echo "1. Start services: docker-compose up -d"
echo "2. Run example: python examples/prometheus_example.py"
echo "3. View metrics: http://localhost:9090/metrics"
echo "4. View Prometheus UI: http://localhost:9090"
