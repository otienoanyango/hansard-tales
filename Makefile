.PHONY: help install dev-setup test test-unit test-property test-integration coverage lint format clean migrate migrate-create run docker-up docker-down docker-logs docker-clean

help:
	@echo "Hansard Tales - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies"
	@echo "  make dev-setup        Setup development environment (Docker + migrations)"
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
	@echo "Database:"
	@echo "  make migrate          Run database migrations"
	@echo "  make migrate-create   Create new migration"
	@echo ""
	@echo "Application:"
	@echo "  make run              Run application"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        Start Docker services"
	@echo "  make docker-down      Stop Docker services"
	@echo "  make docker-logs      View Docker logs"
	@echo "  make docker-clean     Stop and remove Docker volumes"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove generated files"
	@echo ""

setup:
	@bash setup.sh

install:
	pip install -e .[dev]

dev-setup:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	make migrate
	@echo "Development environment ready!"

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

migrate:
	alembic upgrade head

migrate-create:
	@read -p "Migration name: " name; \
	alembic revision --autogenerate -m "$$name"

run:
	python -m hansard_tales.main

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v

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
