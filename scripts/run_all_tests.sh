#!/bin/bash
# Script to run all tests with proper isolation for Sentry tests
# This ensures CI/CD passes without test isolation issues

set -e

echo "Running main test suite (excluding Sentry isolated tests)..."
pytest -m "not sentry_isolated" --cov=hansard_tales --cov-report=xml --cov-report=term

echo ""
echo "Running Sentry isolated tests..."
pytest -m "sentry_isolated" --cov=hansard_tales --cov-append --cov-report=xml --cov-report=term

echo ""
echo "All tests completed successfully!"
