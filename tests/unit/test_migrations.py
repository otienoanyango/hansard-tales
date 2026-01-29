"""
Unit tests for database migrations.

Tests migration reversibility and data preservation.
"""

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

from alembic import command
from alembic.config import Config


@pytest.fixture
def temp_db_path():
    """Create temporary database path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def alembic_config(temp_db_path):
    """Create Alembic configuration for testing."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{temp_db_path}")
    return config


class TestMigrations:
    """Test suite for database migrations."""

    def test_upgrade_creates_all_tables(self, alembic_config, temp_db_path):
        """Test that upgrade creates all expected tables."""
        # Run migration
        command.upgrade(alembic_config, "head")

        # Verify tables were created
        engine = create_engine(f"sqlite:///{temp_db_path}")
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = [
            "documents",
            "mps",
            "statements",
            "bills",
            "bill_versions",
            "votes",
            "mp_votes",
            "questions",
            "petitions",
            "alembic_version",  # Alembic tracking table
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} not found"

    def test_downgrade_removes_all_tables(self, alembic_config, temp_db_path):
        """Test that downgrade removes all tables."""
        # Run migration
        command.upgrade(alembic_config, "head")

        # Verify tables exist
        engine = create_engine(f"sqlite:///{temp_db_path}")
        inspector = inspect(engine)
        tables_before = inspector.get_table_names()
        assert len(tables_before) > 1  # Should have multiple tables

        # Downgrade
        command.downgrade(alembic_config, "base")

        # Verify tables were removed (except alembic_version)
        inspector = inspect(engine)
        tables_after = inspector.get_table_names()

        # Only alembic_version should remain
        assert len(tables_after) <= 1

    def test_migration_reversibility(self, alembic_config, temp_db_path):
        """Test that migrations are reversible."""
        # Upgrade
        command.upgrade(alembic_config, "head")

        engine = create_engine(f"sqlite:///{temp_db_path}")
        inspector = inspect(engine)
        tables_after_upgrade = set(inspector.get_table_names())

        # Downgrade
        command.downgrade(alembic_config, "base")

        inspector = inspect(engine)
        set(inspector.get_table_names())

        # Upgrade again
        command.upgrade(alembic_config, "head")

        inspector = inspect(engine)
        tables_after_second_upgrade = set(inspector.get_table_names())

        # Tables should be the same after both upgrades
        assert tables_after_upgrade == tables_after_second_upgrade

    def test_documents_table_has_required_columns(self, alembic_config, temp_db_path):
        """Test that documents table has all required columns."""
        # Run migration
        command.upgrade(alembic_config, "head")

        # Check columns
        engine = create_engine(f"sqlite:///{temp_db_path}")
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("documents")]

        required_columns = [
            "id",
            "type",
            "chamber",
            "title",
            "date",
            "parliament_term",
            "source_url",
            "source_hash",
            "download_date",
            "vector_doc_id",
            "doc_metadata",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert col in columns, f"Column {col} not found in documents table"

    def test_documents_table_has_indexes(self, alembic_config, temp_db_path):
        """Test that documents table has required indexes."""
        # Run migration
        command.upgrade(alembic_config, "head")

        # Check indexes
        engine = create_engine(f"sqlite:///{temp_db_path}")
        inspector = inspect(engine)
        indexes = inspector.get_indexes("documents")

        index_names = [idx["name"] for idx in indexes]

        expected_indexes = [
            "idx_documents_type_chamber_date",
            "idx_documents_source_hash",
            "idx_documents_date",
        ]

        for idx in expected_indexes:
            assert idx in index_names, f"Index {idx} not found"

    def test_foreign_key_constraints(self, alembic_config, temp_db_path):
        """Test that foreign key constraints are created."""
        # Run migration
        command.upgrade(alembic_config, "head")

        # Check foreign keys on statements table
        engine = create_engine(f"sqlite:///{temp_db_path}")
        inspector = inspect(engine)
        foreign_keys = inspector.get_foreign_keys("statements")

        # Should have foreign keys to documents and mps
        fk_tables = [fk["referred_table"] for fk in foreign_keys]
        assert "documents" in fk_tables
        assert "mps" in fk_tables
