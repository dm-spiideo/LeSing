"""
Structured logging configuration for 3D Model Pipeline.

Provides consistent logging across all components with timestamps and performance metrics (FR-036).

Feature: 002-3d-model-pipeline
"""

import logging
import sys
from pathlib import Path
from typing import Any

import structlog


# =============================================================================
# Logging Configuration
# =============================================================================


def configure_logging(
    log_level: str = "INFO",
    log_file: Path | None = None,
    json_format: bool = False,
) -> None:
    """
    Configure structured logging for the pipeline.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for log output
        json_format: If True, output JSON format; otherwise human-readable
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Processors for structlog
    processors = [
        # Add log level
        structlog.stdlib.add_log_level,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
        # Unwrap event dict
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Human-readable output for development
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> Any:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Structlog logger instance
    """
    return structlog.get_logger(name)


# =============================================================================
# Performance Metrics Logging
# =============================================================================


class PerformanceLogger:
    """
    Context manager for logging performance metrics (FR-036, FR-040).

    Usage:
        with PerformanceLogger("vectorization", logger) as perf:
            # Do work
            perf.add_metric("path_count", 150)
    """

    def __init__(self, operation: str, logger: Any):
        self.operation = operation
        self.logger = logger
        self.start_time: float | None = None
        self.metrics: dict[str, Any] = {}

    def __enter__(self) -> "PerformanceLogger":
        import time

        self.start_time = time.time()
        self.logger.info(f"{self.operation}_started", operation=self.operation)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        import time

        if self.start_time is not None:
            duration_seconds = time.time() - self.start_time
            self.metrics["duration_seconds"] = round(duration_seconds, 3)

        if exc_type is None:
            # Success
            self.logger.info(
                f"{self.operation}_completed",
                operation=self.operation,
                **self.metrics,
            )
        else:
            # Failure
            self.logger.error(
                f"{self.operation}_failed",
                operation=self.operation,
                error=str(exc_val),
                **self.metrics,
            )

    def add_metric(self, key: str, value: Any) -> None:
        """Add a metric to be logged on completion."""
        self.metrics[key] = value


# =============================================================================
# Stage Logging Helpers
# =============================================================================


def log_stage_start(logger: Any, stage: str, job_id: str, **kwargs: Any) -> None:
    """Log pipeline stage start (FR-036)."""
    logger.info(
        "stage_started",
        stage=stage,
        job_id=job_id,
        **kwargs,
    )


def log_stage_complete(
    logger: Any,
    stage: str,
    job_id: str,
    duration_seconds: float,
    **kwargs: Any,
) -> None:
    """Log pipeline stage completion (FR-036)."""
    logger.info(
        "stage_completed",
        stage=stage,
        job_id=job_id,
        duration_seconds=round(duration_seconds, 3),
        **kwargs,
    )


def log_stage_error(
    logger: Any,
    stage: str,
    job_id: str,
    error: Exception,
    **kwargs: Any,
) -> None:
    """Log pipeline stage error (FR-036)."""
    logger.error(
        "stage_failed",
        stage=stage,
        job_id=job_id,
        error_type=type(error).__name__,
        error_message=str(error),
        **kwargs,
    )


def log_quality_metrics(logger: Any, job_id: str, metrics: dict[str, Any]) -> None:
    """Log quality metrics (FR-036)."""
    logger.info(
        "quality_metrics",
        job_id=job_id,
        **metrics,
    )


def log_file_operation(
    logger: Any,
    operation: str,
    file_path: Path,
    file_size_bytes: int | None = None,
) -> None:
    """Log file operations (FR-036)."""
    log_data: dict[str, Any] = {
        "operation": operation,
        "file_path": str(file_path),
    }
    if file_size_bytes is not None:
        log_data["file_size_bytes"] = file_size_bytes

    logger.info("file_operation", **log_data)
