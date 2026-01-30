"""
Monitoring and observability components.

This module provides metrics collection, health checks, and error tracking
for the Hansard Tales system.
"""

from hansard_tales.monitoring.health import HealthStatus, health_check
from hansard_tales.monitoring.metrics import (
    documents_processed,
    error_count,
    processing_time,
    queue_depth,
    start_metrics_server,
    track_processing_time,
    vector_db_size,
)
from hansard_tales.monitoring.sentry_config import (
    add_breadcrumb,
    capture_exception,
    capture_message,
    configure_sentry,
    flush,
    set_tag,
    set_user,
)
from hansard_tales.monitoring.service import (
    MonitoringService,
    get_monitoring_service,
)

__all__ = [
    "documents_processed",
    "processing_time",
    "error_count",
    "queue_depth",
    "vector_db_size",
    "track_processing_time",
    "start_metrics_server",
    "health_check",
    "HealthStatus",
    "configure_sentry",
    "capture_exception",
    "capture_message",
    "set_user",
    "set_tag",
    "add_breadcrumb",
    "flush",
    "MonitoringService",
    "get_monitoring_service",
]
