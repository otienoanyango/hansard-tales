"""
Example usage of Sentry error tracking in Hansard Tales.

This script demonstrates how to configure and use Sentry for error tracking,
including exception capture, message logging, and context management.
"""

import logging
from pathlib import Path

from hansard_tales.config.settings import get_config
from hansard_tales.monitoring import (
    add_breadcrumb,
    capture_exception,
    capture_message,
    configure_sentry,
    flush,
    set_tag,
    set_user,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def example_basic_setup() -> None:
    """Example 1: Basic Sentry setup."""
    print("\n=== Example 1: Basic Sentry Setup ===")

    # Load configuration
    config = get_config()

    # Configure Sentry
    configure_sentry(config.monitoring, config.environment)

    print(f"Sentry enabled: {config.monitoring.sentry_enabled}")
    print(f"Environment: {config.environment}")


def example_exception_capture() -> None:
    """Example 2: Capturing exceptions."""
    print("\n=== Example 2: Exception Capture ===")

    try:
        # Simulate an error
        pass
    except ZeroDivisionError as e:
        # Capture exception with context
        event_id = capture_exception(
            e, context={"operation": "division", "numerator": 1, "denominator": 0}
        )
        logger.error(f"Exception captured with event ID: {event_id}")
        print(f"Exception captured: {event_id}")


def example_message_capture() -> None:
    """Example 3: Capturing messages."""
    print("\n=== Example 3: Message Capture ===")

    # Capture informational message
    event_id = capture_message("Processing started", level="info", context={"document_count": 10})
    print(f"Info message captured: {event_id}")

    # Capture warning message
    event_id = capture_message(
        "Processing completed with warnings",
        level="warning",
        context={"warnings": 5, "errors": 0},
    )
    print(f"Warning message captured: {event_id}")


def example_user_context() -> None:
    """Example 4: Setting user context."""
    print("\n=== Example 4: User Context ===")

    # Set user information
    set_user(user_id="user123", email="user@example.com", username="john_doe")
    print("User context set")

    # Now any errors will include user information
    try:
        raise ValueError("User-specific error")
    except ValueError as e:
        event_id = capture_exception(e)
        print(f"Exception with user context captured: {event_id}")


def example_tags() -> None:
    """Example 5: Using tags for filtering."""
    print("\n=== Example 5: Tags ===")

    # Set tags for filtering in Sentry
    set_tag("document_type", "hansard")
    set_tag("chamber", "national_assembly")
    set_tag("processing_stage", "pdf_extraction")
    print("Tags set")

    # Capture message with tags
    event_id = capture_message("Processing document", level="info")
    print(f"Message with tags captured: {event_id}")


def example_breadcrumbs() -> None:
    """Example 6: Adding breadcrumbs."""
    print("\n=== Example 6: Breadcrumbs ===")

    # Add breadcrumbs to track the sequence of events
    add_breadcrumb("Started PDF download", category="download", level="info")

    add_breadcrumb(
        "PDF downloaded successfully",
        category="download",
        level="info",
        data={"file_size": 1024000, "duration": 2.5},
    )

    add_breadcrumb("Starting text extraction", category="processing", level="info")

    add_breadcrumb(
        "Text extraction completed",
        category="processing",
        level="info",
        data={"pages": 50, "duration": 5.2},
    )

    print("Breadcrumbs added")

    # Now if an error occurs, all breadcrumbs will be included
    try:
        raise RuntimeError("Processing failed")
    except RuntimeError as e:
        event_id = capture_exception(e)
        print(f"Exception with breadcrumbs captured: {event_id}")


def example_processing_workflow() -> None:
    """Example 7: Complete processing workflow with Sentry."""
    print("\n=== Example 7: Complete Workflow ===")

    pdf_path = Path("data/pdfs/hansard_20240101_A.pdf")

    # Set context
    set_tag("document_type", "hansard")
    set_tag("chamber", "national_assembly")

    # Add breadcrumb for start
    add_breadcrumb(
        "Starting document processing",
        category="processing",
        level="info",
        data={"pdf_path": str(pdf_path)},
    )

    try:
        # Simulate processing steps
        add_breadcrumb("Validating PDF", category="processing", level="info")

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        add_breadcrumb("Extracting text", category="processing", level="info")

        # Simulate an error during processing
        raise ValueError("Invalid PDF format")

    except FileNotFoundError as e:
        event_id = capture_exception(e, context={"pdf_path": str(pdf_path)}, level="error")
        logger.error(f"File not found: {event_id}")
        print(f"File not found error captured: {event_id}")

    except ValueError as e:
        event_id = capture_exception(
            e, context={"pdf_path": str(pdf_path), "stage": "text_extraction"}, level="error"
        )
        logger.error(f"Processing error: {event_id}")
        print(f"Processing error captured: {event_id}")

    except Exception as e:
        event_id = capture_exception(e, context={"pdf_path": str(pdf_path)}, level="error")
        logger.error(f"Unexpected error: {event_id}")
        print(f"Unexpected error captured: {event_id}")


def example_flush() -> None:
    """Example 8: Flushing events before shutdown."""
    print("\n=== Example 8: Flushing Events ===")

    # Capture some events
    capture_message("Application shutting down", level="info")

    # Flush all pending events before exit
    success = flush(timeout=5.0)
    print(f"Events flushed: {success}")


def main() -> None:
    """Run all examples."""
    print("=" * 60)
    print("Sentry Integration Examples")
    print("=" * 60)

    # Note: These examples will only send data to Sentry if:
    # 1. SENTRY_ENABLED=true in environment or config
    # 2. SENTRY_DSN is set to a valid Sentry DSN

    example_basic_setup()
    example_exception_capture()
    example_message_capture()
    example_user_context()
    example_tags()
    example_breadcrumbs()
    example_processing_workflow()
    example_flush()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
