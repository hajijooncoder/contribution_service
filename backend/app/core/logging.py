"""
Structured logging configuration for MAHOUNN Contribution Service.
Uses structlog for JSON-formatted logs with correlation IDs.
"""

import logging
import sys
from typing import Any, Dict
import structlog
from app.config import settings


def configure_logging() -> None:
    """Configure structured logging for the application."""
    
    # Standard library logging setup
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Correlation ID middleware support
class CorrelationIdMiddleware:
    """Middleware to add correlation ID to request context."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract or generate correlation ID
        correlation_id = None
        for header_name, header_value in scope.get("headers", []):
            if header_name.decode().lower() == "x-correlation-id":
                correlation_id = header_value.decode()
                break
        
        if not correlation_id:
            import uuid
            correlation_id = str(uuid.uuid4())
        
        # Bind correlation ID to structlog context
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        
        try:
            await self.app(scope, receive, send)
        finally:
            structlog.contextvars.clear_contextvars()


# Initialize logging on import
configure_logging()

# Default logger
logger = get_logger(__name__)