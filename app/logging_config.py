"""Structured logging configuration using structlog.

This module configures structlog for the application with:
- JSON output in production
- Pretty console output in development
- Contextual logging with automatic metadata
- Integration with standard library logging
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.config import settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to all log entries.

    Args:
        logger: The logger instance
        method_name: The name of the method being called
        event_dict: The event dictionary to modify

    Returns:
        Modified event dictionary with app context
    """
    event_dict["app"] = "quality-agent"
    event_dict["environment"] = settings.environment
    return event_dict


def configure_logging() -> None:
    """Configure structured logging for the application.

    This sets up structlog with appropriate processors based on the environment:
    - Development: Pretty console output with colors
    - Production: JSON output for log aggregation

    The configuration integrates with Python's standard logging module to capture
    logs from third-party libraries.
    """
    # Determine log level from settings
    log_level = getattr(logging, settings.log_level)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Common processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        # Don't use add_logger_name with PrintLogger (it doesn't have .name attribute)
        # structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        structlog.processors.StackInfoRenderer(),
    ]

    # Environment-specific processors
    if settings.is_production:
        # Production: JSON output for log aggregation (e.g., CloudWatch, Datadog)
        processors: list[Processor] = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Pretty console output with colors
        processors = shared_processors + [
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Optional logger name. If not provided, uses the calling module name.

    Returns:
        Configured structlog logger

    Example:
        ```python
        from app.logging_config import get_logger

        logger = get_logger(__name__)
        logger.info("webhook_received", pr_number=123, action="opened")
        ```
    """
    return structlog.get_logger(name)
