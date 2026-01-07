#!/bin/bash
# Go functions test runner - self-contained

set -e

echo "🐹 Hansard Tales Go Functions - Running Tests"
echo "============================================="

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check Go availability
if ! command -v go >/dev/null 2>&1; then
    echo "❌ Go not found. Please install Go 1.21+"
    exit 1
fi

# Install linting tools if not present
if ! command -v golangci-lint >/dev/null 2>&1; then
    echo "📦 Installing golangci-lint..."
    go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
fi

# Tidy dependencies
echo "📦 Tidying Go modules..."
go mod tidy

# Format code
echo "🎨 Formatting Go code..."
go fmt ./...

# Run linting
echo "🔍 Running linting..."
golangci-lint run ./...

# Run tests with coverage
echo "🧪 Running Go tests with coverage..."
go test ./... -v -race -coverprofile=coverage.out -covermode=atomic

# Check coverage
if [ -f coverage.out ]; then
    COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
    echo "📊 Coverage: ${COVERAGE}%"
    
    # Validate coverage threshold  
    if command -v bc >/dev/null 2>&1; then
        if (( $(echo "$COVERAGE < 85" | bc -l) )); then
            echo "❌ Coverage ${COVERAGE}% below required 85%"
            exit 1
        fi
    fi
    
    # Generate HTML coverage report for local viewing
    go tool cover -html=coverage.out -o coverage.html
    echo "📊 Coverage report: coverage.html"
fi

echo "✅ Go functions tests passed!"
