# VS Code Development Container

This development container provides a consistent Linux environment that matches our GitHub Actions workflows, perfect for Windows users who want to ensure local development works exactly like CI/CD.

## What's Included

### Languages & Runtimes
- **Go 1.21.6** - matches GitHub Actions `GO_VERSION`
- **Python 3.11** - matches GitHub Actions `PYTHON_VERSION`
- **Node.js 18** - matches GitHub Actions `NODE_VERSION`

### Development Tools
- **Go Tools**: golangci-lint, go fmt, go test with race detection
- **Python Tools**: black, flake8, mypy, pytest, pytest-cov
- **Node.js Tools**: prettier, eslint, typescript
- **Git**: pre-commit hooks support
- **Docker**: Docker-in-Docker for local services

### VS Code Extensions (Auto-installed)
- Go language support with testing
- Python with black formatter and linting
- TypeScript/React development
- Terraform and YAML support
- Playwright for E2E testing
- GitHub Copilot support

## Quick Start

### 1. Prerequisites
- VS Code with "Remote - Containers" extension
- Docker Desktop running

### 2. Open in Container
```bash
# Option 1: Command Palette
Ctrl+Shift+P → "Remote-Containers: Reopen in Container"

# Option 2: VS Code notification
Click "Reopen in Container" when VS Code detects .devcontainer/
```

### 3. Verify Setup
```bash
# Check all tools installed
go version          # Should show go1.21.6
python3 --version   # Should show Python 3.11.x
node --version      # Should show v18.x.x

# Run all tests
test-all           # Alias for ./tools/run-local-tests.sh

# Run individual component tests
test-go            # Go functions tests
test-python        # Python functions tests (should pass with 96.2% coverage)
test-frontend      # Frontend tests
```

## Development Workflow

### Testing (Same as GitHub Actions)
```bash
# Run all tests (exactly like CI/CD)
./tools/run-local-tests.sh

# Run individual subproject tests
cd data-processing/go-functions && ./test.sh
cd data-processing/python-functions && ./test.sh
cd frontend/web && ./test.sh

# Start local services
docker-compose up -d    # PostgreSQL, Redis, LocalStack
```

### Code Quality (Same as CI/CD)
```bash
# Go formatting and linting
cd data-processing/go-functions
go fmt ./...
golangci-lint run

# Python formatting and linting
cd data-processing/python-functions
black .
flake8 .
mypy .

# Frontend formatting and linting
cd frontend/web
npm run format
npm run lint
npm run type-check
```

## Features

### Port Forwarding
- **3000**: Next.js development server
- **5432**: PostgreSQL database
- **6379**: Redis cache
- **4566**: LocalStack (AWS emulation)
- **8080**: Additional services

### Persistent Caching
- **Go modules**: Cached in `.devcontainer/cache/go/`
- **NPM packages**: Cached in `.devcontainer/cache/npm/`
- Speeds up dependency installation between container rebuilds

### Environment Match
```yaml
Matches GitHub Actions Environment:
  OS: Ubuntu 22.04 (jammy)
  Go: 1.21.6
  Python: 3.11
  Node.js: 18
  Tools: Same versions as CI/CD
```

## Troubleshooting

### Container Build Issues
```bash
# Rebuild container
Ctrl+Shift+P → "Remote-Containers: Rebuild Container"

# Clear cache and rebuild
rm -rf .devcontainer/cache/
# Then rebuild container
```

### Network Issues
```bash
# If Go modules fail to download
export GOPROXY=direct
go mod download

# Check container network
docker network ls
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R vscode:vscode /workspaces/hansard-tales
```

## VS Code Integration

### Automatic Setup
- Extensions installed on container creation
- Settings configured for consistent formatting
- Debug configurations ready
- Test discovery enabled

### Recommended Workflow
1. Open project in devcontainer
2. Run `test-all` to verify everything works
3. Create feature branch: `git checkout -b feature/task-X.X`
4. Develop using the same tools as CI/CD
5. Test locally: `test-all`  
6. Push and create PR (all checks will pass)

## Performance Notes

### Fast Development
- Cached dependencies between rebuilds
- Pre-installed tools (no installation wait)
- Docker-in-Docker for local services
- Same environment as GitHub Actions (no surprises)

### Resource Usage
- Container uses ~2GB RAM
- Go, Python, Node.js caches persist
- Docker-in-Docker requires privileged mode

This devcontainer ensures your Windows development environment exactly matches the Linux environment used in GitHub Actions, eliminating environment-specific issues.
