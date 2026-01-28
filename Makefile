.PHONY: help install test test-unit test-property test-integration coverage lint format clean

help:
	@echo "Hansard Tales - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies"
	@echo "  make setup            Run full setup (venv + install)"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-property    Run property-based tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make coverage         Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linters (ruff, mypy)"
	@echo "  make format           Format code with ruff"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove generated files"
	@echo ""

setup:
	@bash setup.sh

install:
	pip install -r requirements.txt

test:
	pytest

test-unit:
	pytest tests/unit/ -v

test-property:
	pytest tests/property/ -v

test-integration:
	pytest tests/integration/ -v

coverage:
	pytest --cov=hansard_tales --cov-report=html --cov-report=term

lint:
	@echo "Running ruff..."
	ruff check hansard_tales tests
	@echo "Running mypy..."
	mypy hansard_tales

format:
	ruff format hansard_tales tests
	ruff check --fix hansard_tales tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
