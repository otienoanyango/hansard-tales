#!/bin/bash
# Setup script for Hansard Tales development environment

set -e

echo "🚀 Setting up Hansard Tales development environment..."

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python $required_version or higher required"
    exit 1
fi

echo "✅ Python version $python_version is compatible"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -e .[dev]

# Setup pre-commit hooks
echo "🪝 Setting up pre-commit hooks..."
pre-commit install

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️  Please edit .env with your configuration"
    else
        echo "⚠️  .env.example not found, skipping .env creation"
    fi
else
    echo "✅ .env file already exists"
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/{pdfs,vector_db,vector_db_dev,logs}

# Check if Docker is available
if command -v docker-compose &> /dev/null; then
    echo "🐳 Starting Docker services..."
    docker-compose up -d

    # Wait for services to be ready
    echo "⏳ Waiting for services to be ready..."
    sleep 10

    # Run migrations
    echo "🗄️  Running database migrations..."
    alembic upgrade head

    echo "✅ Docker services started successfully"
else
    echo "⚠️  Docker not found. Skipping Docker setup."
    echo "   Install Docker to use PostgreSQL, Qdrant, Prometheus, and Grafana."
fi

# Run basic tests
echo "🧪 Running basic tests..."
pytest tests/unit/test_config.py -v

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "Available commands:"
echo "  make help             Show all available commands"
echo "  make test             Run all tests"
echo "  make docker-up        Start Docker services"
echo "  make migrate          Run database migrations"
echo ""
