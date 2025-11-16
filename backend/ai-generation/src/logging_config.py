"""Logging configuration for AI Image Generation component.

This module sets up structured logging using structlog with:
- JSON format for easy parsing
- Context processors for request tracking
- Sensitive data filtering (API keys, etc.)
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor


def filter_sensitive_data(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Filter sensitive data from log events.

    This processor masks sensitive information like API keys before logging.

    Args:
        logger: Logger instance
        method_name: Log method name
        event_dict: Event dictionary to filter

    Returns:
        Filtered event dictionary
    """
    # List of keys that should be masked
    sensitive_keys = {
        "api_key",
        "openai_api_key",
        "authorization",
        "token",
        "secret",
        "password",
    }

    for key in sensitive_keys:
        if key in event_dict:
            event_dict[key] = "***REDACTED***"

    # Also check nested details dict
    if "details" in event_dict and isinstance(event_dict["details"], dict):
        for key in sensitive_keys:
            if key in event_dict["details"]:
                event_dict["details"][key] = "***REDACTED***"

    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application.

    Sets up structlog with JSON formatting and sensitive data filtering.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Processors that process every log entry
    processors: list[Processor] = [
        # Add log level
        structlog.stdlib.add_log_level,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
        # Filter sensitive data
        filter_sensitive_data,
        # Format as JSON
        structlog.processors.JSONRenderer(),
    ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ of calling module)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
