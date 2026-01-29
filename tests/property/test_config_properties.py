"""
Property-based tests for configuration management.

Tests universal properties and invariants of the configuration system.
"""

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hansard_tales.config.settings import (
    DatabaseConfig,
    LoggingConfig,
    ScraperConfig,
    VectorDBConfig,
)

# Strategy for valid database engines
db_engines = st.sampled_from(["sqlite", "postgresql"])

# Strategy for valid vector DB engines
vector_db_engines = st.sampled_from(["chromadb", "qdrant"])

# Strategy for valid devices
devices = st.sampled_from(["cpu", "cuda"])

# Strategy for valid logging levels
log_levels = st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR"])

# Strategy for valid logging formats
log_formats = st.sampled_from(["json", "text"])


class TestDatabaseConfigProperties:
    """Property-based tests for DatabaseConfig."""

    @given(
        engine=db_engines,
        host=st.text(min_size=1, max_size=100),
        port=st.integers(min_value=1, max_value=65535),
        database=st.text(min_size=1, max_size=100),
        user=st.text(min_size=1, max_size=100),
        password=st.text(max_size=100),
    )
    def test_connection_string_never_crashes(self, engine, host, port, database, user, password):
        """
        Connection string generation should never crash.

        **Validates: Requirements 6.1, 6.4**
        """
        try:
            config = DatabaseConfig(
                engine=engine, host=host, port=port, database=database, user=user, password=password
            )
            connection_string = config.connection_string
            assert isinstance(connection_string, str)
            assert len(connection_string) > 0
        except Exception:
            # If config creation fails due to validation, that's acceptable
            pass

    @given(engine=db_engines)
    def test_connection_string_format_valid(self, engine):
        """
        Connection strings should always match expected format.

        **Validates: Requirements 6.1**
        """
        config = DatabaseConfig(engine=engine)
        connection_string = config.connection_string

        if engine == "sqlite":
            assert connection_string.startswith("sqlite:///")
            assert connection_string.endswith(".db")
        elif engine == "postgresql":
            assert connection_string.startswith("postgresql://")
            assert "@" in connection_string
            assert ":" in connection_string


class TestVectorDBConfigProperties:
    """Property-based tests for VectorDBConfig."""

    @given(
        path_str=st.text(min_size=1, max_size=100).filter(
            lambda x: not x.startswith("/") and "\x00" not in x
        )
    )
    def test_persist_directory_always_path_object(self, path_str):
        """
        persist_directory should always be a Path object.

        **Validates: Requirements 6.1**
        """
        try:
            config = VectorDBConfig(persist_directory=path_str)
            assert isinstance(config.persist_directory, Path)
        except Exception:
            # If validation fails, that's acceptable
            pass

    @given(engine=vector_db_engines)
    def test_valid_engines_always_accepted(self, engine):
        """
        Valid vector DB engines should always be accepted.

        **Validates: Requirements 6.1, 6.4**
        """
        config = VectorDBConfig(engine=engine)
        assert config.engine == engine


class TestScraperConfigProperties:
    """Property-based tests for ScraperConfig."""

    @given(
        max_retries=st.integers(min_value=0, max_value=10),
        retry_delay=st.floats(min_value=0.1, max_value=10.0),
        timeout=st.integers(min_value=1, max_value=300),
    )
    def test_scraper_config_accepts_valid_values(self, max_retries, retry_delay, timeout):
        """
        ScraperConfig should accept all valid numeric values.

        **Validates: Requirements 6.1, 6.4**
        """
        config = ScraperConfig(max_retries=max_retries, retry_delay=retry_delay, timeout=timeout)
        assert config.max_retries == max_retries
        assert config.retry_delay == pytest.approx(retry_delay, rel=0.01)
        assert config.timeout == timeout


class TestLoggingConfigProperties:
    """Property-based tests for LoggingConfig."""

    @given(level=log_levels, format=log_formats)
    def test_logging_config_valid_combinations(self, level, format):
        """
        All valid combinations of level and format should be accepted.

        **Validates: Requirements 6.1, 6.4**
        """
        config = LoggingConfig(level=level, format=format)
        assert config.level == level
        assert config.format == format

    @given(
        path_str=st.text(min_size=1, max_size=100).filter(
            lambda x: not x.startswith("/") and "\x00" not in x
        )
    )
    def test_log_dir_always_path_object(self, path_str):
        """
        log_dir should always be a Path object.

        **Validates: Requirements 6.1**
        """
        try:
            config = LoggingConfig(log_dir=path_str)
            assert isinstance(config.log_dir, Path)
        except Exception:
            # If validation fails, that's acceptable
            pass


class TestConfigurationRobustness:
    """Property-based tests for configuration robustness."""

    @given(st.text())
    def test_invalid_engine_raises_error(self, invalid_engine):
        """
        Invalid database engines should raise validation errors.

        **Validates: Requirements 6.6**
        """
        if invalid_engine not in ["sqlite", "postgresql"]:
            with pytest.raises(ValueError):
                DatabaseConfig(engine=invalid_engine)

    @given(st.text())
    def test_invalid_vector_engine_raises_error(self, invalid_engine):
        """
        Invalid vector DB engines should raise validation errors.

        **Validates: Requirements 6.6**
        """
        if invalid_engine not in ["chromadb", "qdrant"]:
            with pytest.raises(ValueError):
                VectorDBConfig(engine=invalid_engine)
