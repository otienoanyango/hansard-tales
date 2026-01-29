"""
Sentry error tracking integration for Hansard Tales.

This module configures Sentry for error tracking and monitoring,
integrating with the logging system to capture errors and exceptions.
"""

import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from hansard_tales.config.settings import MonitoringConfig

logger = logging.getLogger(__name__)


def configure_sentry(config: MonitoringConfig, environment: str = "development") -> None:
    """
    Configure Sentry error tracking.

    This function initializes Sentry with the provided configuration,
    setting up error tracking, performance monitoring, and logging integration.

    Args:
        config: Monitoring configuration containing Sentry settings
        environment: Environment name (development, staging, production)

    Example:
        >>> from hansard_tales.config.settings import get_config
        >>> config = get_config()
        >>> configure_sentry(config.monitoring, config.environment)
    """
    if not config.sentry_enabled:
        logger.info("Sentry error tracking is disabled")
        return

    if not config.dsn:
        logger.warning("Sentry is enabled but DSN is not configured")
        return

    try:
        # Configure logging integration
        # Capture INFO and above as breadcrumbs
        # Capture ERROR and above as events
        logging_integration = LoggingIntegration(
            level=logging.INFO,  # Breadcrumb level
            event_level=logging.ERROR,  # Event level
        )

        # Initialize Sentry
        sentry_sdk.init(
            dsn=config.dsn,
            environment=environment,
            # Sample 10% of transactions for performance monitoring
            traces_sample_rate=0.1,
            # Capture 100% of errors
            sample_rate=1.0,
            # Enable performance monitoring
            enable_tracing=True,
            # Integrations
            integrations=[logging_integration],
            # Send default PII (Personally Identifiable Information)
            send_default_pii=False,
            # Attach stack traces to messages
            attach_stacktrace=True,
            # Maximum breadcrumbs
            max_breadcrumbs=50,
        )

        logger.info(f"Sentry error tracking configured for environment: {environment}")

    except Exception as e:
        logger.error(f"Failed to configure Sentry: {e}")
        # Don't raise - we don't want Sentry configuration to break the app
        return


def capture_exception(
    exception: Exception, context: dict | None = None, level: str = "error"
) -> str | None:
    """
    Capture an exception and send it to Sentry.

    Args:
        exception: The exception to capture
        context: Additional context to attach to the error
        level: Severity level (fatal, error, warning, info, debug)

    Returns:
        Event ID if captured, None otherwise

    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     event_id = capture_exception(e, {"pdf_path": "test.pdf"})
        ...     logger.error(f"Error captured: {event_id}")
    """
    try:
        # Set context if provided
        if context:
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, value)
                scope.level = level
                return sentry_sdk.capture_exception(exception)
        else:
            return sentry_sdk.capture_exception(exception)
    except Exception as e:
        logger.error(f"Failed to capture exception in Sentry: {e}")
        return None


def capture_message(message: str, level: str = "info", context: dict | None = None) -> str | None:
    """
    Capture a message and send it to Sentry.

    Args:
        message: The message to capture
        level: Severity level (fatal, error, warning, info, debug)
        context: Additional context to attach to the message

    Returns:
        Event ID if captured, None otherwise

    Example:
        >>> event_id = capture_message(
        ...     "Processing completed with warnings",
        ...     level="warning",
        ...     context={"warnings": 5}
        ... )
    """
    try:
        # Set context if provided
        if context:
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, value)
                scope.level = level
                return sentry_sdk.capture_message(message, level=level)
        else:
            return sentry_sdk.capture_message(message, level=level)
    except Exception as e:
        logger.error(f"Failed to capture message in Sentry: {e}")
        return None


def set_user(user_id: str, email: str | None = None, username: str | None = None) -> None:
    """
    Set user context for Sentry events.

    Args:
        user_id: Unique user identifier
        email: User email address
        username: Username

    Example:
        >>> set_user("user123", email="user@example.com", username="john_doe")
    """
    try:
        sentry_sdk.set_user({"id": user_id, "email": email, "username": username})
    except Exception as e:
        logger.error(f"Failed to set user context in Sentry: {e}")


def set_tag(key: str, value: str) -> None:
    """
    Set a tag for Sentry events.

    Tags are searchable key-value pairs that can be used to filter events.

    Args:
        key: Tag key
        value: Tag value

    Example:
        >>> set_tag("document_type", "hansard")
        >>> set_tag("chamber", "national_assembly")
    """
    try:
        sentry_sdk.set_tag(key, value)
    except Exception as e:
        logger.error(f"Failed to set tag in Sentry: {e}")


def add_breadcrumb(
    message: str, category: str = "default", level: str = "info", data: dict | None = None
) -> None:
    """
    Add a breadcrumb to the current scope.

    Breadcrumbs are a trail of events that happened prior to an error,
    helping to understand the context of the error.

    Args:
        message: Breadcrumb message
        category: Breadcrumb category (e.g., "http", "db", "ui")
        level: Severity level (fatal, error, warning, info, debug)
        data: Additional data to attach

    Example:
        >>> add_breadcrumb(
        ...     "Starting PDF processing",
        ...     category="processing",
        ...     level="info",
        ...     data={"pdf_path": "test.pdf"}
        ... )
    """
    try:
        sentry_sdk.add_breadcrumb(message=message, category=category, level=level, data=data or {})
    except Exception as e:
        logger.error(f"Failed to add breadcrumb in Sentry: {e}")


def flush(timeout: float = 2.0) -> bool:
    """
    Flush pending Sentry events.

    This is useful when shutting down the application to ensure
    all events are sent before exit.

    Args:
        timeout: Maximum time to wait in seconds

    Returns:
        True if all events were sent, False otherwise

    Example:
        >>> # Before application shutdown
        >>> flush(timeout=5.0)
    """
    try:
        return sentry_sdk.flush(timeout=timeout)
    except Exception as e:
        logger.error(f"Failed to flush Sentry events: {e}")
        return False
