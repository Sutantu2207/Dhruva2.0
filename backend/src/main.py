"""Dhruva.AI V2 — Main Application Entry Point.

Initializes FastAPI, registers security middlewares, sets up global error envelopes,
and mounts API v1 routes.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.core.config import get_settings
from src.core.errors import DhruvaException
from src.core.logging import logger, setup_logging
from src.interfaces.http.api.v1.api_router import api_v1_router
from src.interfaces.http.middlewares.correlation import CorrelationIdMiddleware
from src.interfaces.http.middlewares.security_headers import SecurityHeadersMiddleware
from src.interfaces.http.schemas.envelope import ApiErrorResponse, ErrorBody


settings = get_settings()
setup_logging(service_name=settings.SERVICE_NAME, debug=settings.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    logger.info("Initializing Dhruva.AI V2 Core Application Engine...")
    yield
    logger.info("Shutting down Dhruva.AI V2 Core Application Engine...")
    from src.infrastructure.persistence.postgres.database import engine
    await engine.dispose()


app = FastAPI(
    title="Dhruva.AI V2 Core API",
    description="Multi-tenant institutional intelligence and learning operating system API",
    version="2.0.0",
    docs_url="/api/docs" if settings.ENVIRONMENT.value != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT.value != "production" else None,
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT.value != "production" else None,
    lifespan=lifespan,
)

# Register Middlewares (Order: Correlation -> Security Headers -> CORS)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# Global Exception Handlers conforming to Standard Error Envelope
@app.exception_handler(DhruvaException)
async def dhruva_exception_handler(request: Request, exc: DhruvaException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    logger.warning(
        f"Domain exception [{exc.code}]: {exc.message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        },
    )
    error_payload = ApiErrorResponse(
        success=False,
        error=ErrorBody(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        ),
    )
    return JSONResponse(status_code=exc.status_code, content=error_payload.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    details = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        details.append({"field": field, "issue": err.get("msg", "Invalid value")})

    logger.warning(
        f"Validation error on {request.url.path}",
        extra={"request_id": request_id, "path": request.url.path},
    )
    error_payload = ApiErrorResponse(
        success=False,
        error=ErrorBody(
            code="VALIDATION_FAILED",
            message="Request payload failed schema validation",
            details=details,
            request_id=request_id,
        ),
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_payload.model_dump())


@app.exception_handler(StarletteHTTPException)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    code = "HTTP_ERROR"
    if exc.status_code == 404:
        code = "RESOURCE_NOT_FOUND"
    elif exc.status_code == 401:
        code = "AUTHENTICATION_FAILED"
    elif exc.status_code == 403:
        code = "PERMISSION_DENIED"

    error_payload = ApiErrorResponse(
        success=False,
        error=ErrorBody(
            code=code,
            message=str(exc.detail),
            details=[],
            request_id=request_id,
        ),
    )
    return JSONResponse(status_code=exc.status_code, content=error_payload.model_dump())


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    logger.exception(
        f"Unhandled server error on {request.url.path}: {str(exc)}",
        extra={"request_id": request_id, "path": request.url.path},
    )
    # Strictly sanitize in production: do NOT leak stack trace or internal SQL
    error_payload = ApiErrorResponse(
        success=False,
        error=ErrorBody(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred. Please contact support with the request ID.",
            details=[],
            request_id=request_id,
        ),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump(),
    )


# Mount API V1 routes
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


# Kubernetes / Edge Liveness & Readiness Aliases
@app.get("/health/live", tags=["Platform & System Operations"], include_in_schema=False)
async def k8s_liveness(request: Request) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    return JSONResponse(
        status_code=200,
        content={"success": True, "data": {"status": "UP"}, "meta": {"request_id": request_id}},
    )


@app.get("/health/ready", tags=["Platform & System Operations"], include_in_schema=False)
async def k8s_readiness(request: Request) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    return JSONResponse(
        status_code=200,
        content={"success": True, "data": {"status": "READY"}, "meta": {"request_id": request_id}},
    )
