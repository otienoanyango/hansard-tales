#!/usr/bin/env python3
"""
Configuration validation script.

This script validates configuration files and environment variables
to ensure they are correct before running the application.

Usage:
    python scripts/validate_config.py
    python scripts/validate_config.py --environment production
    python scripts/validate_config.py --config config/environments/custom.yaml
"""

import argparse
import sys
from pathlib import Path

try:
    from pydantic import ValidationError

    from hansard_tales.config import Config, get_config
except ImportError as e:
    print(f"Error: Failed to import required modules: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)


def validate_config(config_path: Path | None = None) -> tuple[bool, list[str]]:
    """
    Validate configuration.

    Args:
        config_path: Optional path to config file

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    try:
        # Load configuration
        if config_path:
            # TODO: Add support for loading from custom path
            config = get_config()
        else:
            config = get_config()

        # Validate database configuration
        if config.database.engine == "postgresql":
            if not config.database.host:
                errors.append("PostgreSQL requires database.host")
            if not config.database.user:
                errors.append("PostgreSQL requires database.user")
            if config.database.port <= 0 or config.database.port > 65535:
                errors.append(f"Invalid database port: {config.database.port}")

        # Validate vector DB configuration
        if config.vector_db.engine == "qdrant":
            if not config.vector_db.host:
                errors.append("Qdrant requires vector_db.host")
            if config.vector_db.port <= 0 or config.vector_db.port > 65535:
                errors.append(f"Invalid vector DB port: {config.vector_db.port}")

        # Validate embedding configuration
        if config.embedding.dimension <= 0:
            errors.append(f"Invalid embedding dimension: {config.embedding.dimension}")
        if config.embedding.batch_size <= 0:
            errors.append(f"Invalid batch size: {config.embedding.batch_size}")

        # Validate LLM configuration
        if not config.llm.api_key or config.llm.api_key == "":
            errors.append("LLM API key is required (set ANTHROPIC_API_KEY)")
        if config.llm.max_tokens <= 0:
            errors.append(f"Invalid max_tokens: {config.llm.max_tokens}")
        if config.llm.temperature < 0.0 or config.llm.temperature > 2.0:
            errors.append(f"Invalid temperature: {config.llm.temperature}")
        if config.llm.monthly_budget_usd <= 0:
            errors.append(f"Invalid monthly budget: {config.llm.monthly_budget_usd}")

        # Validate scraper configuration
        if not config.scraper.base_url.startswith("http"):
            errors.append(f"Invalid base URL: {config.scraper.base_url}")
        if config.scraper.max_retries < 0:
            errors.append(f"Invalid max_retries: {config.scraper.max_retries}")
        if config.scraper.timeout <= 0:
            errors.append(f"Invalid timeout: {config.scraper.timeout}")

        # Validate paths exist or can be created
        paths_to_check = [
            ("download_dir", config.scraper.download_dir),
            ("vector_db persist_directory", config.vector_db.persist_directory),
            ("log_dir", config.logging.log_dir),
        ]

        for name, path in paths_to_check:
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create {name}: {path} - {e}")

        # Validate monitoring configuration
        if config.monitoring.sentry_enabled and not config.monitoring.dsn:
            errors.append("Sentry enabled but DSN not provided")

        return len(errors) == 0, errors

    except ValidationError as e:
        # Pydantic validation errors
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            message = error["msg"]
            errors.append(f"{field}: {message}")
        return False, errors

    except Exception as e:
        errors.append(f"Unexpected error: {e}")
        return False, errors


def check_environment_variables() -> tuple[bool, list[str]]:
    """
    Check required environment variables.

    Returns:
        Tuple of (is_valid, warnings)
    """
    import os

    warnings = []

    # Required variables
    required = ["ANTHROPIC_API_KEY"]
    for var in required:
        if not os.getenv(var):
            warnings.append(f"Required environment variable not set: {var}")

    # Optional but recommended
    recommended = {
        "DB_HOST": "PostgreSQL host (if using PostgreSQL)",
        "DB_PASSWORD": "PostgreSQL password (if using PostgreSQL)",
        "QDRANT_HOST": "Qdrant host (if using Qdrant)",
        "SENTRY_DSN": "Sentry DSN (if using Sentry)",
    }

    for var, description in recommended.items():
        if not os.getenv(var):
            warnings.append(f"Optional variable not set: {var} - {description}")

    return len([w for w in warnings if "Required" in w]) == 0, warnings


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate Hansard Tales configuration")
    parser.add_argument(
        "--environment",
        "-e",
        help="Environment name (development, staging, production)",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )

    args = parser.parse_args()

    # Set environment if specified
    if args.environment:
        import os

        os.environ["ENVIRONMENT"] = args.environment

    print("=" * 70)
    print("Hansard Tales Configuration Validation")
    print("=" * 70)
    print()

    # Check environment variables
    print("Checking environment variables...")
    env_valid, env_warnings = check_environment_variables()

    if env_warnings:
        print()
        for warning in env_warnings:
            if "Required" in warning:
                print(f"  ❌ {warning}")
            else:
                print(f"  ⚠️  {warning}")
    else:
        print("  ✅ All environment variables OK")

    print()

    # Validate configuration
    print("Validating configuration...")
    config_valid, config_errors = validate_config(args.config)

    if config_errors:
        print()
        for error in config_errors:
            print(f"  ❌ {error}")
    else:
        print("  ✅ Configuration is valid")

    print()
    print("=" * 70)

    # Summary
    all_valid = env_valid and config_valid

    if args.strict and env_warnings:
        all_valid = False

    if all_valid:
        print("✅ Validation passed!")
        print()
        print("You can now run the application:")
        print("  python -m hansard_tales.pipeline")
        return 0
    else:
        print("❌ Validation failed!")
        print()
        print("Please fix the errors above before running the application.")
        print()
        print("Common fixes:")
        print("  - Set ANTHROPIC_API_KEY: export ANTHROPIC_API_KEY=your-key")
        print("  - Check config file: config/environments/{environment}.yaml")
        print("  - Verify database is running: pg_isready (PostgreSQL)")
        print("  - Verify Qdrant is running: curl http://localhost:6333/health")
        return 1


if __name__ == "__main__":
    sys.exit(main())
