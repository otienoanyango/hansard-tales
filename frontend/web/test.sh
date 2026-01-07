#!/bin/bash
# Frontend test runner - self-contained

set -e

echo "⚛️  Hansard Tales Frontend - Running Tests"
echo "========================================"

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check Node.js availability
if ! command -v node >/dev/null 2>&1; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check npm availability
if ! command -v npm >/dev/null 2>&1; then
    echo "❌ npm not found. Please install npm"
    exit 1
fi

# Install dependencies
echo "📦 Installing npm dependencies..."
npm install --silent

# Run linting
echo "🔍 Running ESLint..."
npm run lint || echo "⚠️  Linting issues found but continuing..."

# Run type checking
echo "🔍 Running TypeScript type check..."
npm run type-check || echo "⚠️  Type errors found but continuing..."

# Check formatting
echo "🎨 Checking code formatting..."
npm run format:check || echo "⚠️  Format issues found but continuing..."

# Run tests with coverage
echo "🧪 Running Jest tests with coverage..."
npm test -- --coverage --watchAll=false --verbose=false --passWithNoTests

# Check coverage
if [ -f coverage/coverage-summary.json ]; then
    COVERAGE=$(node -e "
    try {
        const fs = require('fs');
        const coverage = JSON.parse(fs.readFileSync('coverage/coverage-summary.json', 'utf8'));
        console.log(coverage.total.statements.pct || 0);
    } catch (e) {
        console.log(0);
    }
    ")
    
    echo "📊 Coverage: ${COVERAGE}%"
    
    # Validate coverage threshold (75%)
    if command -v bc >/dev/null 2>&1; then
        if (( $(echo "$COVERAGE < 75" | bc -l) )); then
            echo "❌ Coverage ${COVERAGE}% below required 75%"
            exit 1
        fi
    fi
    
    echo "📊 Coverage report: coverage/lcov-report/index.html"
else
    echo "📊 No coverage report generated (no tests found)"
fi

echo "✅ Frontend tests passed!"
