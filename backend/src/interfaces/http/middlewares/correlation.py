"""Dhruva.AI V2 — Correlation ID Middleware.

Ensures every incoming request carries a unique X-Request-ID for distributed tracing.
"""

import secrets
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract existing X-Request-ID or generate new unique ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"req_{secrets.token_hex(8)}"

        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
