"""
Configuration management for Hansard Tales.

This module provides centralized configuration with validation and
environment-specific overrides using Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Literal
from pathlib import Path


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    
    model_config = SettingsConfigDict(env_prefix="DB_")
    
    engine: Literal["sqlite", "postgresql"] = "sqlite"
    host: str = "localhost"
    port: int = 5432
    database: str = "hansard_tales"
    user: str = "hansard"
    password: str = ""
    
    @property
    def connection_string(self) -> str:
        """Generate database connection string."""
        if self.engine == "sqlite":
            return f"sqlite:///{self.database}.db"
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class VectorDBConfig(BaseSettings):
    """Vector database configuration."""
    
    engine: Literal["chromadb", "qdrant"] = "chromadb"
    host: str = "localhost"
    port: int = 6333
    collection_prefix: str = "hansard_tales"
    persist_directory: Path = Path("data/vector_db")
    
    @field_validator('persist_directory', mode='before')
    @classmethod
    def validate_persist_directory(cls, v):
        """Ensure persist_directory is a Path object."""
        if isinstance(v, str):
            return Path(v)
        return v


class EmbeddingConfig(BaseSettings):
    """Embedding model configuration."""
    
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 32
    device: Literal["cpu", "cuda"] = "cpu"


class ScraperConfig(BaseSettings):
    """Web scraper configuration."""
    
    base_url: str = "https://parliament.go.ke"
    download_dir: Path = Path("data/pdfs")
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30
    user_agent: str = "HansardTales/1.0"
    
    @field_validator('download_dir', mode='before')
    @classmethod
    def validate_download_dir(cls, v):
        """Ensure download_dir is a Path object."""
        if isinstance(v, str):
            return Path(v)
        return v


class LoggingConfig(BaseSettings):
    """Logging configuration."""
    
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: Literal["json", "text"] = "json"
    output: Literal["stdout", "file", "both"] = "both"
    log_dir: Path = Path("logs")
    rotation: str = "1 day"
    retention: str = "30 days"
    
    @field_validator('log_dir', mode='before')
    @classmethod
    def validate_log_dir(cls, v):
        """Ensure log_dir is a Path object."""
        if isinstance(v, str):
            return Path(v)
        return v


class MonitoringConfig(BaseSettings):
    """Monitoring configuration."""
    
    model_config = SettingsConfigDict(env_prefix="SENTRY_")
    
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    sentry_enabled: bool = False
    dsn: str = ""


class Config(BaseSettings):
    """Main application configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore"
    )
    
    environment: Literal["development", "staging", "production"] = "development"
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    scraper: ScraperConfig = Field(default_factory=ScraperConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)


# Global configuration instance
_config: Config | None = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config: The global configuration object
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """
    Reload the configuration from files and environment.
    
    Returns:
        Config: The reloaded configuration object
    """
    global _config
    _config = Config()
    return _config
