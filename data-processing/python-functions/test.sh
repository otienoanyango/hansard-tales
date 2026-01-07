#!/bin/bash
# Python functions test runner - self-contained

set -e

echo "🐍 Hansard Tales Python Functions - Running Tests"
echo "================================================="

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check Python availability
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python3 not found. Please install Python 3.11+"
    exit 1
fi

# Set up virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -e .[dev] -q

# Run tests
echo "🧪 Running pytest..."
pytest tests/ --cov=shared --cov-report=term-missing --cov-report=xml -v

# Check coverage
COVERAGE=$(python3 -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('coverage.xml')
    root = tree.getroot()
    coverage = float(root.get('line-rate', 0)) * 100
    print(f'{coverage:.1f}')
except:
    print('0')
")

echo "📊 Coverage: ${COVERAGE}%"

# Validate coverage threshold
if (( $(echo "$COVERAGE < 90" | bc -l) )); then
    echo "❌ Coverage ${COVERAGE}% below required 90%"
    exit 1
fi

echo "✅ Python functions tests passed!"
