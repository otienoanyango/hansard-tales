"""
Unit tests for configuration management.

Tests configuration validation, environment overrides, and default values.
"""

import pytest
from pathlib import Path
from unittest.mock import patch
from hansard_tales.config.settings import (
    Config,
    DatabaseConfig,
    VectorDBConfig,
    EmbeddingConfig,
    ScraperConfig,
    LoggingConfig,
    MonitoringConfig,
    get_config,
    reload_config,
)


class TestDatabaseConfig:
    """Test suite for DatabaseConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = DatabaseConfig()
        assert config.engine == "sqlite"
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "hansard_tales"
        assert config.user == "hansard"
        assert config.password == ""
    
    def test_sqlite_connection_string(self):
        """Test SQLite connection string generation."""
        config = DatabaseConfig(engine="sqlite", database="test_db")
        assert config.connection_string == "sqlite:///test_db.db"
    
    def test_postgresql_connection_string(self):
        """Test PostgreSQL connection string generation."""
        config = DatabaseConfig(
            engine="postgresql",
            host="db.example.com",
            port=5432,
            database="hansard",
            user="admin",
            password="secret123"
        )
        expected = "postgresql://admin:secret123@db.example.com:5432/hansard"
        assert config.connection_string == expected
    
    @patch.dict('os.environ', {'DB_PASSWORD': 'env_password'})
    def test_password_from_environment(self):
        """Test password override from environment variable."""
        config = DatabaseConfig()
        assert config.password == "env_password"


class TestVectorDBConfig:
    """Test suite for VectorDBConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = VectorDBConfig()
        assert config.engine == "chromadb"
        assert config.host == "localhost"
        assert config.port == 6333
        assert config.collection_prefix == "hansard_tales"
        assert config.persist_directory == Path("data/vector_db")
    
    def test_persist_directory_as_string(self):
        """Test persist_directory conversion from string."""
        config = VectorDBConfig(persist_directory="custom/path")
        assert isinstance(config.persist_directory, Path)
        assert config.persist_directory == Path("custom/path")
    
    def test_persist_directory_as_path(self):
        """Test persist_directory as Path object."""
        config = VectorDBConfig(persist_directory=Path("custom/path"))
        assert isinstance(config.persist_directory, Path)
        assert config.persist_directory == Path("custom/path")


class TestEmbeddingConfig:
    """Test suite for EmbeddingConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = EmbeddingConfig()
        assert config.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert config.dimension == 384
        assert config.batch_size == 32
        assert config.device == "cpu"
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = EmbeddingConfig(
            model_name="custom-model",
            dimension=768,
            batch_size=64,
            device="cuda"
        )
        assert config.model_name == "custom-model"
        assert config.dimension == 768
        assert config.batch_size == 64
        assert config.device == "cuda"


class TestScraperConfig:
    """Test suite for ScraperConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = ScraperConfig()
        assert config.base_url == "https://parliament.go.ke"
        assert config.download_dir == Path("data/pdfs")
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.timeout == 30
        assert config.user_agent == "HansardTales/1.0"
    
    def test_download_dir_conversion(self):
        """Test download_dir conversion from string."""
        config = ScraperConfig(download_dir="downloads")
        assert isinstance(config.download_dir, Path)
        assert config.download_dir == Path("downloads")


class TestLoggingConfig:
    """Test suite for LoggingConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.output == "both"
        assert config.log_dir == Path("logs")
        assert config.rotation == "1 day"
        assert config.retention == "30 days"
    
    def test_log_dir_conversion(self):
        """Test log_dir conversion from string."""
        config = LoggingConfig(log_dir="/var/log/app")
        assert isinstance(config.log_dir, Path)
        assert config.log_dir == Path("/var/log/app")


class TestMonitoringConfig:
    """Test suite for MonitoringConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = MonitoringConfig()
        assert config.prometheus_enabled is True
        assert config.prometheus_port == 9090
        assert config.sentry_enabled is False
        assert config.dsn == ""
    
    @patch.dict('os.environ', {'SENTRY_DSN': 'https://example.com/sentry'})
    def test_sentry_dsn_from_environment(self):
        """Test Sentry DSN override from environment variable."""
        config = MonitoringConfig()
        assert config.dsn == "https://example.com/sentry"


class TestMainConfig:
    """Test suite for main Config class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = Config()
        assert config.environment == "development"
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.vector_db, VectorDBConfig)
        assert isinstance(config.embedding, EmbeddingConfig)
        assert isinstance(config.scraper, ScraperConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.monitoring, MonitoringConfig)
    
    def test_nested_configuration(self):
        """Test nested configuration access."""
        config = Config()
        assert config.database.engine == "sqlite"
        assert config.vector_db.engine == "chromadb"
        assert config.embedding.device == "cpu"
        assert config.scraper.max_retries == 3
        assert config.logging.level == "INFO"
        assert config.monitoring.prometheus_enabled is True
    
    def test_get_config_singleton(self):
        """Test get_config returns singleton instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
    
    def test_reload_config(self):
        """Test reload_config creates new instance."""
        config1 = get_config()
        config2 = reload_config()
        # After reload, get_config should return the new instance
        config3 = get_config()
        assert config2 is config3
        # But it should be different from the original
        assert config1 is not config2


class TestConfigurationValidation:
    """Test suite for configuration validation."""
    
    def test_invalid_database_engine(self):
        """Test validation of invalid database engine."""
        with pytest.raises(ValueError):
            DatabaseConfig(engine="mysql")  # Only sqlite and postgresql allowed
    
    def test_invalid_vector_db_engine(self):
        """Test validation of invalid vector DB engine."""
        with pytest.raises(ValueError):
            VectorDBConfig(engine="pinecone")  # Only chromadb and qdrant allowed
    
    def test_invalid_embedding_device(self):
        """Test validation of invalid embedding device."""
        with pytest.raises(ValueError):
            EmbeddingConfig(device="tpu")  # Only cpu and cuda allowed
    
    def test_invalid_logging_level(self):
        """Test validation of invalid logging level."""
        with pytest.raises(ValueError):
            LoggingConfig(level="TRACE")  # Only DEBUG, INFO, WARNING, ERROR allowed
    
    def test_invalid_logging_format(self):
        """Test validation of invalid logging format."""
        with pytest.raises(ValueError):
            LoggingConfig(format="xml")  # Only json and text allowed
    
    def test_invalid_environment(self):
        """Test validation of invalid environment."""
        with pytest.raises(ValueError):
            Config(environment="testing")  # Only development, staging, production allowed
