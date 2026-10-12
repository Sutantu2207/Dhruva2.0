"""Dhruva.AI V2 — Security Headers Middleware.

Injects OWASP-recommended HTTP security headers to protect against
clickjacking, MIME confusion, and XSS attacks.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from src.core.config import get_settings


settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        if settings.COOKIE_SECURE or settings.ENVIRONMENT.value in ("staging", "production"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
