#!/bin/bash
# Hansard Tales Local Development Setup Script

set -e

echo "🏛️ Hansard Tales - Local Development Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on macOS or Linux
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "🖥️  Detected OS: $MACHINE"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Go
install_go() {
    if command_exists go; then
        GO_VERSION=$(go version | cut -d' ' -f3 | cut -d'o' -f2)
        echo "✅ Go already installed: $GO_VERSION"
        return
    fi
    
    echo "📦 Installing Go 1.21..."
    if [ "$MACHINE" == "Mac" ]; then
        if command_exists brew; then
            brew install go
        else
            echo "❌ Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
    else
        # Linux installation
        wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
        sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
        echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
        rm go1.21.0.linux-amd64.tar.gz
    fi
}

# Function to install Python
install_python() {
    if command_exists python3.11; then
        PYTHON_VERSION=$(python3.11 --version)
        echo "✅ Python already installed: $PYTHON_VERSION"
        return
    fi
    
    echo "📦 Installing Python 3.11..."
    if [ "$MACHINE" == "Mac" ]; then
        if command_exists brew; then
            brew install python@3.11
        else
            echo "❌ Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
    else
        # Linux installation (Ubuntu/Debian)
        sudo apt update
        sudo apt install -y python3.11 python3.11-venv python3.11-pip
    fi
}

# Function to install Node.js
install_nodejs() {
    if command_exists node; then
        NODE_VERSION=$(node --version)
        echo "✅ Node.js already installed: $NODE_VERSION"
        return
    fi
    
    echo "📦 Installing Node.js 18..."
    if [ "$MACHINE" == "Mac" ]; then
        if command_exists brew; then
            brew install node@18
        else
            echo "❌ Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
    else
        # Linux installation via NodeSource
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
}

# Function to install Docker
install_docker() {
    if command_exists docker; then
        echo "✅ Docker already installed"
        return
    fi
    
    echo "📦 Installing Docker..."
    if [ "$MACHINE" == "Mac" ]; then
        echo "⚠️  Please install Docker Desktop for Mac manually:"
        echo "   https://docs.docker.com/desktop/mac/install/"
    else
        # Linux installation
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        echo "⚠️  Please log out and back in for Docker permissions to take effect"
    fi
}

echo "🔍 Checking required dependencies..."

# Install required tools
install_go
install_python
install_nodejs
install_docker

# Install Go tools
echo "📦 Installing Go development tools..."
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Set up Python virtual environment
echo "📦 Setting up Python virtual environment..."
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install black flake8 mypy pre-commit pytest pytest-cov pytest-mock pytest-asyncio

# Install Python dependencies for existing scraper
if [ -f data-processing/python-functions/requirements.txt ]; then
    pip install -r data-processing/python-functions/requirements.txt
fi

# Create requirements-dev.txt for development dependencies
cat > data-processing/python-functions/requirements-dev.txt << EOF
# Development dependencies
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-asyncio>=0.21.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
types-requests>=2.0.0
EOF

# Install Node.js dependencies (create basic package.json if needed)
echo "📦 Setting up Node.js environment..."

# Create basic Next.js structure if it doesn't exist
mkdir -p frontend/web
if [ ! -f frontend/web/package.json ]; then
    cd frontend/web
    cat > package.json << EOF
{
  "name": "hansard-tales-web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "14.0.0",
    "prettier": "^3.0.0",
    "typescript": "^5.0.0",
    "jest": "^29.0.0",
    "@testing-library/react": "^13.0.0",
    "@testing-library/jest-dom": "^6.0.0"
  }
}
EOF
    cd ../../
fi

# Create Docker Compose for local development
echo "🐳 Creating Docker Compose configuration..."
cat > docker-compose.yml << EOF
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: hansard_tales_dev
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/database/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev_user -d hansard_tales_dev"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  localstack:
    image: localstack/localstack:latest
    environment:
      - SERVICES=s3,lambda
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
    ports:
      - "4566:4566"
    volumes:
      - localstack_data:/tmp/localstack
      - /var/run/docker.sock:/var/run/docker.sock

volumes:
  postgres_data:
  localstack_data:
EOF

# Create .env.example file
echo "⚙️  Creating environment configuration..."
cat > .env.example << EOF
# Development Environment Configuration
NODE_ENV=development
DATABASE_URL=postgresql://dev_user:dev_password@localhost:5432/hansard_tales_dev
REDIS_URL=redis://localhost:6379

# GCP Configuration (for local development)
GCP_PROJECT_ID=hansard-tales-dev
GCP_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# API Keys (get from respective services)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SENDGRID_API_KEY=your_sendgrid_api_key
OPENAI_API_KEY=your_openai_key_if_needed

# Feature Flags
FEATURE_AI_ANALYSIS=true
FEATURE_CARTOON_GENERATION=false
FEATURE_PREMIUM_API=false
EOF

cp .env.example .env

# Create pre-commit configuration
echo "🪝 Setting up pre-commit hooks..."
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: mixed-line-ending
        
  - repo: https://github.com/psf/black
    rev: 23.10.1
    hooks:
      - id: black
        language_version: python3.11
        files: ^data-processing/python-functions/.*\.py$
        
  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        files: ^data-processing/python-functions/.*\.py$
        args: [--max-line-length=88, --extend-ignore=E203,W503]
        
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
      - id: mypy
        files: ^data-processing/python-functions/.*\.py$
        additional_dependencies: [types-requests]
        
  - repo: local
    hooks:
      - id: go-fmt
        name: Go Format
        entry: gofmt
        language: system
        files: ^data-processing/go-functions/.*\.go$
        args: [-l, -d]
        
      - id: go-lint
        name: Go Lint
        entry: golangci-lint
        language: system
        files: ^data-processing/go-functions/.*\.go$
        args: [run]
        pass_filenames: false
        
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.3
    hooks:
      - id: prettier
        files: ^frontend/web/.*\.(js|jsx|ts|tsx|json|css|md)$
EOF

# Install pre-commit hooks
pre-commit install

echo "📁 Creating basic directory structure and scaffolding..."

# Create basic Go function structure
mkdir -p data-processing/go-functions/hansard-scraper
mkdir -p data-processing/go-functions/pdf-processor
mkdir -p data-processing/go-functions/shared

# Create basic Python function structure
mkdir -p data-processing/python-functions/semantic-analyzer
mkdir -p data-processing/python-functions/content-generator
mkdir -p data-processing/python-functions/shared

# Create test directories
mkdir -p tests/unit/go-functions
mkdir -p tests/unit/python-functions
mkdir -p tests/unit/frontend
mkdir -p tests/integration/pipeline
mkdir -p tests/integration/api
mkdir -p tests/e2e/playwright

# Create basic VS Code settings
mkdir -p .vscode
cat > .vscode/settings.json << EOF
{
    "editor.rulers": [80, 120],
    "editor.wordWrap": "wordWrapColumn",
    "editor.wordWrapColumn": 80,
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "files.exclude": {
        "**/.venv": true,
        "**/node_modules": true,
        "**/coverage": true,
        "**/*.pyc": true,
        "**/__pycache__": true
    },
    "go.useLanguageServer": true,
    "go.lintOnSave": "package",
    "go.formatTool": "gofmt",
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "typescript.preferences.importModuleSpecifier": "relative",
    "[typescript]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.formatOnSave": true
    },
    "[typescriptreact]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.formatOnSave": true
    },
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true
    },
    "[go]": {
        "editor.formatOnSave": true
    }
}
EOF

cat > .vscode/extensions.json << EOF
{
    "recommendations": [
        "golang.go",
        "ms-python.python",
        "ms-python.black-formatter",
        "ms-python.flake8",
        "bradlc.vscode-tailwindcss",
        "esbenp.prettier-vscode",
        "ms-vscode.vscode-typescript-next",
        "hashicorp.terraform",
        "redhat.vscode-yaml",
        "ms-playwright.playwright"
    ]
}
EOF

echo "✅ Local development environment setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Copy .env.example to .env and fill in your API keys"
echo "2. Run 'docker-compose up -d' to start local services"
echo "3. Run './tools/run-local-tests.sh' to verify everything works"
echo "4. Start developing with feature branches!"
echo ""
echo "🚀 Happy coding!"
