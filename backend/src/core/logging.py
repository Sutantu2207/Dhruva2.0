"""Dhruva.AI V2 — Structured Logging Foundation.

Produces structured JSON logs for log ingestion systems (Datadog, CloudWatch, Render)
and human-readable formatted logs during local development.
Enforces redaction of sensitive parameters (passwords, tokens, authorization headers).
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "secret_key",
    "authorization",
    "cookie",
    "credentials",
    "api_key",
}


def sanitize_payload(obj: Any) -> Any:
    """Recursively sanitize dict/list payloads to prevent credential leakage."""
    if isinstance(obj, dict):
        sanitized = {}
        for k, v in obj.items():
            if any(sensitive in k.lower() for sensitive in SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_payload(v)
        return sanitized
    elif isinstance(obj, list):
        return [sanitize_payload(item) for item in obj]
    return obj


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def __init__(self, service_name: str = "dhruva-backend") -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Contextual metadata passed via extra
        context_fields = [
            "request_id",
            "institution_id",
            "user_id",
            "operation",
            "duration_ms",
            "path",
            "method",
            "status_code",
            "client_ip",
        ]
        for field in context_fields:
            val = getattr(record, field, None)
            if val is not None:
                log_entry[field] = str(val) if not isinstance(val, (int, float, bool)) else val

        if hasattr(record, "metadata") and isinstance(record.metadata, dict):
            log_entry["metadata"] = sanitize_payload(record.metadata)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_logging(service_name: str = "dhruva-backend", debug: bool = False) -> logging.Logger:
    """Initialize structured logging system."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter(service_name=service_name))
    root_logger.addHandler(handler)

    # Suppress excessive third-party logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return root_logger


logger = logging.getLogger("dhruva")
