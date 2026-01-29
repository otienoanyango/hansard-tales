"""
Error handling infrastructure for Hansard Tales.

This module provides a custom exception hierarchy, error context tracking,
and utilities for consistent error handling across the application.
"""

import logging
import traceback
from dataclasses import dataclass
from typing import Any


class HansardTalesError(Exception):
    """
    Base exception for all Hansard Tales errors.

    All custom exceptions in the application should inherit from this class
    to enable consistent error handling and filtering.
    """

    pass


class DataCollectionError(HansardTalesError):
    """
    Error during data collection (scraping).

    Raised when:
    - Network requests fail
    - HTML parsing fails
    - Document download fails
    - Website structure changes
    """

    pass


class ProcessingError(HansardTalesError):
    """
    Error during document processing.

    Raised when:
    - PDF parsing fails
    - Text extraction fails
    - Entity extraction fails
    - Data transformation fails
    """

    pass


class StorageError(HansardTalesError):
    """
    Error during data storage.

    Raised when:
    - Database operations fail
    - Vector DB operations fail
    - File system operations fail
    """

    pass


class ConfigurationError(HansardTalesError):
    """
    Error in configuration.

    Raised when:
    - Configuration validation fails
    - Required configuration missing
    - Invalid configuration values
    """

    pass


class ValidationError(HansardTalesError):
    """
    Error in data validation.

    Raised when:
    - Data model validation fails
    - Schema validation fails
    - Business rule validation fails
    """

    pass


@dataclass
class ErrorContext:
    """
    Context information for errors.

    Captures comprehensive error information for debugging and monitoring,
    including stack trace, component information, and operation state.

    Attributes:
        error_type: Type of error (exception class name)
        error_message: Error message
        stack_trace: Full stack trace
        component: Component where error occurred
        operation: Operation being performed
        input_data: Input data that caused error (optional)
        state: Application state at time of error (optional)
        request_id: Request ID for tracing (optional)
    """

    error_type: str
    error_message: str
    stack_trace: str
    component: str
    operation: str
    input_data: dict[str, Any] | None = None
    state: dict[str, Any] | None = None
    request_id: str | None = None


def capture_error_context(
    error: Exception,
    component: str,
    operation: str,
    input_data: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
) -> ErrorContext:
    """
    Capture full error context.

    Creates an ErrorContext object with comprehensive error information
    including stack trace and optional context data.

    Args:
        error: Exception that occurred
        component: Component where error occurred (e.g., "scraper", "processor")
        operation: Operation being performed (e.g., "download_pdf", "extract_text")
        input_data: Input data that caused error (optional)
        state: Application state at time of error (optional)

    Returns:
        ErrorContext with full error information

    Example:
        >>> try:
        ...     process_pdf(pdf_path)
        ... except Exception as e:
        ...     context = capture_error_context(
        ...         error=e,
        ...         component="pdf_processor",
        ...         operation="extract_text",
        ...         input_data={"pdf_path": str(pdf_path)}
        ...     )
    """
    from hansard_tales.utils.logging import get_request_id

    return ErrorContext(
        error_type=type(error).__name__,
        error_message=str(error),
        stack_trace=traceback.format_exc(),
        component=component,
        operation=operation,
        input_data=input_data,
        state=state,
        request_id=get_request_id(),
    )


def log_error(logger: logging.Logger, error_context: ErrorContext) -> None:
    """
    Log error with full context.

    Logs error information using structured logging with all available
    context for debugging and monitoring.

    Args:
        logger: Logger instance (from hansard_tales.utils.logging)
        error_context: Error context to log

    Example:
        >>> from hansard_tales.utils.logging import get_logger
        >>> logger = get_logger("app")
        >>> log_error(logger, error_context)
    """
    logger.error(
        "operation_failed",
        error_type=error_context.error_type,
        error_message=error_context.error_message,
        component=error_context.component,
        operation=error_context.operation,
        request_id=error_context.request_id,
        input_data=error_context.input_data,
        state=error_context.state,
        stack_trace=error_context.stack_trace,
    )
