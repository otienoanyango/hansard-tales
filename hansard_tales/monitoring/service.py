"""
Monitoring service for Hansard Tales pipeline.

This module provides comprehensive monitoring and observability for the
analysis pipeline, including Prometheus metrics, structured logging,
and error tracking.
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

import structlog
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


# Define Prometheus metrics for Phase 1 analysis pipeline
statements_processed = Counter(
    "statements_processed_total",
    "Total statements processed",
    ["status", "type"],  # status: success/error, type: substantive/filler
)

processing_duration = Histogram(
    "processing_duration_seconds",
    "Time to process document or stage",
    ["stage"],  # stage: segmentation, classification, llm_analysis, etc.
)

llm_api_calls = Counter(
    "llm_api_calls_total",
    "Total LLM API calls",
    ["model", "status"],  # model: claude-3-5-haiku, status: success/error
)

llm_tokens = Counter(
    "llm_tokens_total",
    "Total LLM tokens used",
    ["model", "type"],  # model: claude-3-5-haiku, type: input/output
)

llm_cost = Counter(
    "llm_cost_usd_total",
    "Total LLM cost in USD",
    ["model"],
)

pipeline_errors = Counter(
    "pipeline_errors_total",
    "Total pipeline errors",
    ["stage", "error_type"],
)

active_processing = Gauge(
    "active_processing_jobs",
    "Number of active processing jobs",
)

citation_verifications = Counter(
    "citation_verifications_total",
    "Total citation verifications",
    ["status"],  # status: verified/unverified/failed
)

mp_identifications = Counter(
    "mp_identifications_total",
    "Total MP identifications",
    ["status"],  # status: success/failed
)

bill_mentions = Counter(
    "bill_mentions_total",
    "Total bill mentions detected",
    ["confidence"],  # confidence: high/medium/low
)


class MonitoringService:
    """
    Comprehensive monitoring service for the analysis pipeline.

    This service provides:
    - Prometheus metrics tracking
    - Structured logging with structlog
    - Statement processing tracking
    - Stage duration tracking
    - LLM call tracking
    - Error tracking
    - Metrics endpoint

    Example:
        >>> monitoring = MonitoringService()
        >>> monitoring.track_statement_processed("success", "substantive")
        >>> monitoring.track_llm_call("claude-3-5-haiku", "success", 500, 200)
    """

    def __init__(self):
        """Initialize monitoring service with structured logging."""
        self.logger = structlog.get_logger(__name__)
        self._configure_structlog()

    def _configure_structlog(self) -> None:
        """
        Configure structured logging with JSON output.

        Sets up processors for:
        - Log level filtering
        - Timestamp addition
        - Exception formatting
        - JSON rendering
        """
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def track_statement_processed(
        self,
        status: str,
        statement_type: str,
        mp_id: str | None = None,
        quality_score: float | None = None,
    ) -> None:
        """
        Track statement processing.

        Args:
            status: Processing status (success/error)
            statement_type: Type of statement (substantive/filler/procedural/etc.)
            mp_id: Optional MP identifier
            quality_score: Optional quality score (0-100)

        Example:
            >>> monitoring.track_statement_processed(
            ...     "success",
            ...     "substantive",
            ...     mp_id="mp-123",
            ...     quality_score=85.5
            ... )
        """
        statements_processed.labels(status=status, type=statement_type).inc()

        self.logger.info(
            "statement_processed",
            status=status,
            statement_type=statement_type,
            mp_id=mp_id,
            quality_score=quality_score,
        )

    def track_stage_duration(
        self,
        stage: str,
        duration: float,
        items_processed: int = 0,
        success: bool = True,
    ) -> None:
        """
        Track pipeline stage processing time.

        Args:
            stage: Pipeline stage name (segmentation, classification, etc.)
            duration: Duration in seconds
            items_processed: Number of items processed
            success: Whether stage completed successfully

        Example:
            >>> monitoring.track_stage_duration(
            ...     "segmentation",
            ...     2.5,
            ...     items_processed=150,
            ...     success=True
            ... )
        """
        processing_duration.labels(stage=stage).observe(duration)

        self.logger.info(
            "stage_completed",
            stage=stage,
            duration=duration,
            items_processed=items_processed,
            success=success,
        )

    def track_llm_call(
        self,
        model: str,
        status: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float | None = None,
        duration: float | None = None,
    ) -> None:
        """
        Track LLM API call.

        Args:
            model: Model name (e.g., "claude-3-5-haiku-20241022")
            status: Call status (success/error)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost_usd: Optional cost in USD
            duration: Optional call duration in seconds

        Example:
            >>> monitoring.track_llm_call(
            ...     "claude-3-5-haiku-20241022",
            ...     "success",
            ...     500,
            ...     200,
            ...     cost_usd=0.001,
            ...     duration=1.2
            ... )
        """
        llm_api_calls.labels(model=model, status=status).inc()
        llm_tokens.labels(model=model, type="input").inc(input_tokens)
        llm_tokens.labels(model=model, type="output").inc(output_tokens)

        if cost_usd is not None:
            llm_cost.labels(model=model).inc(cost_usd)

        self.logger.info(
            "llm_call",
            model=model,
            status=status,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            duration=duration,
        )

    def track_error(
        self,
        stage: str,
        error_type: str,
        error: Exception,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Track pipeline error.

        Args:
            stage: Pipeline stage where error occurred
            error_type: Type of error (e.g., ValueError, APIError)
            error: The exception object
            context: Optional additional context

        Example:
            >>> try:
            ...     risky_operation()
            ... except ValueError as e:
            ...     monitoring.track_error(
            ...         "llm_analysis",
            ...         "ValueError",
            ...         e,
            ...         context={"statement_id": "stmt-123"}
            ...     )
        """
        pipeline_errors.labels(stage=stage, error_type=error_type).inc()

        log_context = {
            "stage": stage,
            "error_type": error_type,
            "error": str(error),
        }
        if context:
            log_context.update(context)

        self.logger.error("pipeline_error", **log_context, exc_info=True)

    def track_mp_identification(
        self,
        status: str,
        confidence: float | None = None,
        mp_name: str | None = None,
    ) -> None:
        """
        Track MP identification.

        Args:
            status: Identification status (success/failed)
            confidence: Optional confidence score (0.0-1.0)
            mp_name: Optional MP name

        Example:
            >>> monitoring.track_mp_identification(
            ...     "success",
            ...     confidence=0.95,
            ...     mp_name="Hon. John Doe"
            ... )
        """
        mp_identifications.labels(status=status).inc()

        self.logger.info(
            "mp_identification",
            status=status,
            confidence=confidence,
            mp_name=mp_name,
        )

    def track_citation_verification(
        self,
        status: str,
        similarity_score: float | None = None,
        source_id: str | None = None,
    ) -> None:
        """
        Track citation verification.

        Args:
            status: Verification status (verified/unverified/failed)
            similarity_score: Optional similarity score (0.0-1.0)
            source_id: Optional source document ID

        Example:
            >>> monitoring.track_citation_verification(
            ...     "verified",
            ...     similarity_score=0.98,
            ...     source_id="stmt-456"
            ... )
        """
        citation_verifications.labels(status=status).inc()

        self.logger.info(
            "citation_verification",
            status=status,
            similarity_score=similarity_score,
            source_id=source_id,
        )

    def track_bill_mention(
        self,
        confidence: str,
        bill_title: str | None = None,
        mention_text: str | None = None,
    ) -> None:
        """
        Track bill mention detection.

        Args:
            confidence: Confidence level (high/medium/low)
            bill_title: Optional bill title
            mention_text: Optional mention text

        Example:
            >>> monitoring.track_bill_mention(
            ...     "high",
            ...     bill_title="Finance Bill, 2024",
            ...     mention_text="The Finance Bill"
            ... )
        """
        bill_mentions.labels(confidence=confidence).inc()

        self.logger.info(
            "bill_mention",
            confidence=confidence,
            bill_title=bill_title,
            mention_text=mention_text,
        )

    def start_processing(self) -> None:
        """
        Mark start of processing job.

        Increments active processing gauge.

        Example:
            >>> monitoring.start_processing()
        """
        active_processing.inc()
        self.logger.info("processing_started")

    def end_processing(self) -> None:
        """
        Mark end of processing job.

        Decrements active processing gauge.

        Example:
            >>> monitoring.end_processing()
        """
        active_processing.dec()
        self.logger.info("processing_ended")

    def track_processing_decorator(self, stage: str) -> Callable:
        """
        Decorator to track processing time and errors for a function.

        Args:
            stage: Pipeline stage name

        Returns:
            Decorator function

        Example:
            >>> @monitoring.track_processing_decorator("segmentation")
            ... def segment_text(text):
            ...     # Processing logic
            ...     return segments
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start

                    # Track success
                    self.track_stage_duration(
                        stage=stage,
                        duration=duration,
                        items_processed=len(result) if isinstance(result, list) else 1,
                        success=True,
                    )

                    return result
                except Exception as e:
                    duration = time.time() - start

                    # Track error
                    self.track_stage_duration(
                        stage=stage,
                        duration=duration,
                        items_processed=0,
                        success=False,
                    )
                    self.track_error(
                        stage=stage,
                        error_type=type(e).__name__,
                        error=e,
                    )
                    raise

            return wrapper

        return decorator

    def get_metrics_endpoint(self) -> str:
        """
        Get Prometheus metrics endpoint URL.

        Returns:
            Metrics endpoint URL

        Example:
            >>> endpoint = monitoring.get_metrics_endpoint()
            >>> print(endpoint)
            'http://localhost:9090/metrics'
        """
        from hansard_tales.config.settings import get_config

        config = get_config()
        port = config.monitoring.prometheus_port if hasattr(config, "monitoring") else 9090

        return f"http://localhost:{port}/metrics"


# Global monitoring instance
_monitoring_service: MonitoringService | None = None


def get_monitoring_service() -> MonitoringService:
    """
    Get global monitoring service instance.

    Returns:
        MonitoringService instance

    Example:
        >>> monitoring = get_monitoring_service()
        >>> monitoring.track_statement_processed("success", "substantive")
    """
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service
