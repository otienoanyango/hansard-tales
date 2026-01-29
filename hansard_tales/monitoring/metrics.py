"""
Prometheus metrics exporter for Hansard Tales.

This module defines and exports Prometheus metrics for tracking system
performance and health.
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = logging.getLogger(__name__)

# Define metrics
documents_processed = Counter(
    "documents_processed_total",
    "Total number of documents processed",
    ["document_type", "chamber", "status"],
)

processing_time = Histogram(
    "document_processing_seconds", "Time spent processing documents", ["document_type", "chamber"]
)

error_count = Counter("errors_total", "Total number of errors", ["component", "error_type"])

queue_depth = Gauge(
    "processing_queue_depth", "Number of documents in processing queue", ["document_type"]
)

vector_db_size = Gauge(
    "vector_db_documents_total", "Total number of documents in vector DB", ["collection"]
)


def track_processing_time(document_type: str, chamber: str) -> Callable:
    """
    Decorator to track processing time and success/failure metrics.

    Args:
        document_type: Type of document being processed
        chamber: Parliamentary chamber

    Returns:
        Decorator function

    Example:
        >>> @track_processing_time('hansard', 'national_assembly')
        ... def process_hansard(pdf_path):
        ...     # Processing logic
        ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                processing_time.labels(document_type=document_type, chamber=chamber).observe(
                    duration
                )
                documents_processed.labels(
                    document_type=document_type, chamber=chamber, status="success"
                ).inc()
                return result
            except Exception as e:
                duration = time.time() - start
                processing_time.labels(document_type=document_type, chamber=chamber).observe(
                    duration
                )
                documents_processed.labels(
                    document_type=document_type, chamber=chamber, status="error"
                ).inc()
                error_count.labels(component="processor", error_type=type(e).__name__).inc()
                raise

        return wrapper

    return decorator


def start_metrics_server(port: int = 9090) -> None:
    """
    Start Prometheus metrics HTTP server.

    Args:
        port: Port to listen on (default: 9090)

    Example:
        >>> start_metrics_server(9090)
    """
    try:
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
        raise
