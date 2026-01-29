"""
Structured logging infrastructure for Hansard Tales.

This module provides structured logging with JSON formatting, context tracking,
and request ID propagation for debugging and monitoring.
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any

import structlog

# Context variable for request ID tracking
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def generate_request_id() -> str:
    """
    Generate unique request ID.

    Returns:
        UUID string for request tracking
    """
    return str(uuid.uuid4())


def set_request_id(request_id: str) -> None:
    """
    Set request ID for current context.

    Args:
        request_id: Request ID to set
    """
    request_id_var.set(request_id)


def get_request_id() -> str:
    """
    Get request ID for current context.

    Returns:
        Current request ID or empty string if not set
    """
    return request_id_var.get()


def add_request_id(logger, method_name, event_dict):
    """
    Add request ID to log event.

    This processor adds the current request ID to all log entries
    for request tracing across components.

    Args:
        logger: Logger instance
        method_name: Log method name
        event_dict: Log event dictionary

    Returns:
        Modified event dictionary with request_id
    """
    request_id = get_request_id()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging(
    level: str = "INFO", format: str = "json", output: str = "stdout", log_dir: str = "data/logs"
) -> None:
    """
    Configure structured logging.

    Sets up structlog with appropriate processors for JSON or console output,
    including request ID tracking and exception formatting.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format ("json" or "text")
        output: Output destination ("stdout", "file", or "both")
        log_dir: Directory for log files (used when output is "file" or "both")
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout if output in ["stdout", "both"] else None,
        level=getattr(logging, level.upper()),
    )

    # Setup file logging with rotation if needed
    if output in ["file", "both"]:
        setup_file_logging(log_dir, level)

    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add appropriate renderer
    if format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper())),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def setup_file_logging(log_dir: str, level: str = "INFO") -> None:
    """
    Setup file logging with rotation.

    Configures a TimedRotatingFileHandler that rotates logs daily
    and keeps 30 days of history.

    Args:
        log_dir: Directory for log files
        level: Log level
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    handler = TimedRotatingFileHandler(
        filename=log_path / "hansard_tales.log",
        when="midnight",
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding="utf-8",
    )

    handler.setFormatter(logging.Formatter("%(message)s"))

    handler.setLevel(getattr(logging, level.upper()))

    logging.getLogger().addHandler(handler)


class Logger:
    """
    Structured logger wrapper.

    Provides a clean interface for structured logging with context binding
    and automatic request ID tracking.

    Example:
        >>> logger = Logger("hansard_tales.scraper")
        >>> logger.info("document_downloaded", document_type="hansard", file_size=1024)
    """

    def __init__(self, name: str):
        """
        Initialize logger.

        Args:
            name: Logger name (typically module path)
        """
        self.logger = structlog.get_logger(name)
        self._name = name

    def debug(self, message: str, **kwargs: Any) -> None:
        """
        Log debug message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """
        Log info message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """
        Log warning message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """
        Log error message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """
        Log critical message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self.logger.critical(message, **kwargs)

    def bind(self, **kwargs: Any) -> "Logger":
        """
        Bind context to logger.

        Creates a new logger with bound context that will be included
        in all subsequent log messages.

        Args:
            **kwargs: Context fields to bind

        Returns:
            New logger with bound context

        Example:
            >>> logger = Logger("app")
            >>> request_logger = logger.bind(request_id="123", user_id="456")
            >>> request_logger.info("processing_request")
        """
        bound_logger = self.logger.bind(**kwargs)
        new_logger = Logger(self._name)
        new_logger.logger = bound_logger
        return new_logger


def get_logger(name: str) -> Logger:
    """
    Get logger instance.

    Args:
        name: Logger name (typically module path)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger("hansard_tales.scraper")
        >>> logger.info("starting_scrape", chamber="national_assembly")
    """
    return Logger(name)
