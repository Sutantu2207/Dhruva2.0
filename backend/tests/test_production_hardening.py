"""Dhruva.AI V2 — Production Hardening, Security Headers & OpenAPI Contract Tests (Phase 10)."""

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from src.core.config import EnvironmentType, Settings
from src.main import app


@pytest.mark.asyncio
class TestProductionConfigValidation:
    """Verifies fail-fast security constraints to prevent insecure production deployments."""

    def test_insecure_secret_rejected_in_production(self):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                ENVIRONMENT=EnvironmentType.PRODUCTION,
                SECRET_KEY="dev_insecure_short_key",
                DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dhruva",
                DEBUG=False,
            )
        assert "SECRET_KEY must be a cryptographically secure random string" in str(exc_info.value)

    def test_short_secret_rejected_in_production(self):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                ENVIRONMENT=EnvironmentType.PRODUCTION,
                SECRET_KEY="too_short_secret_less_than_32",
                DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dhruva",
                DEBUG=False,
            )
        assert "SECRET_KEY must be a cryptographically secure random string" in str(exc_info.value)

    def test_sqlite_rejected_in_production(self):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                ENVIRONMENT=EnvironmentType.PRODUCTION,
                SECRET_KEY="a" * 32,
                DATABASE_URL="sqlite+aiosqlite:///./production.db",
                DEBUG=False,
            )
        assert "SQLite cannot be used in production" in str(exc_info.value)

    def test_debug_enabled_rejected_in_production(self):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                ENVIRONMENT=EnvironmentType.PRODUCTION,
                SECRET_KEY="a" * 32,
                DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dhruva",
                DEBUG=True,
            )
        assert "DEBUG mode must be disabled in production" in str(exc_info.value)

    def test_valid_production_configuration_accepted(self):
        valid_settings = Settings(
            ENVIRONMENT=EnvironmentType.PRODUCTION,
            SECRET_KEY="prod_super_secure_cryptographic_random_token_minimum_32_bytes_ok",
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dhruva_prod",
            DEBUG=False,
            COOKIE_SECURE=True,
        )
        assert valid_settings.ENVIRONMENT == EnvironmentType.PRODUCTION
        assert valid_settings.DEBUG is False
        assert valid_settings.COOKIE_SECURE is True

    def test_render_postgres_url_automatically_normalized(self):
        # Render and Heroku inject postgres:// or postgresql:// without asyncpg driver
        s1 = Settings(
            ENVIRONMENT=EnvironmentType.PRODUCTION,
            SECRET_KEY="prod_super_secure_cryptographic_random_token_minimum_32_bytes_ok",
            DATABASE_URL="postgres://user:pass@ep-host.oregon.render.com:5432/dhruva_db",
            DEBUG=False,
        )
        assert s1.DATABASE_URL.startswith("postgresql+asyncpg://")

        s2 = Settings(
            ENVIRONMENT=EnvironmentType.PRODUCTION,
            SECRET_KEY="prod_super_secure_cryptographic_random_token_minimum_32_bytes_ok",
            DATABASE_URL="postgresql://user:pass@ep-host.oregon.render.com:5432/dhruva_db",
            DEBUG=False,
        )
        assert s2.DATABASE_URL.startswith("postgresql+asyncpg://")


@pytest.mark.asyncio
class TestSecurityHeadersMiddleware:
    """Verifies OWASP-compliant security headers on all responses."""

    async def test_security_headers_injected(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health/live")
            assert resp.status_code == 200

            # OWASP Mandated Security Headers
            assert resp.headers.get("X-Content-Type-Options") == "nosniff"
            assert resp.headers.get("X-Frame-Options") == "DENY"
            assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
            assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
            assert resp.headers.get("Permissions-Policy") == "geolocation=(), camera=(), microphone=()"

            # Correlation ID Header
            assert "X-Request-ID" in resp.headers


@pytest.mark.asyncio
class TestStandardErrorEnvelopes:
    """Verifies that all error scenarios return standard error envelopes without leaking PII or stack traces."""

    async def test_404_resource_not_found_envelope(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/non_existent_endpoint_xyz")
            assert resp.status_code == 404
            payload = resp.json()
            assert payload["success"] is False
            assert payload["error"]["code"] == "RESOURCE_NOT_FOUND"
            assert "request_id" in payload["error"]

    async def test_401_unauthenticated_envelope(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/me")
            assert resp.status_code == 401
            payload = resp.json()
            assert payload["success"] is False
            assert payload["error"]["code"] in ("UNAUTHORIZED", "AUTHENTICATION_FAILED")
            assert "request_id" in payload["error"]

    async def test_422_validation_failed_envelope(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/login", json={"invalid": "payload"})
            assert resp.status_code == 422
            payload = resp.json()
            assert payload["success"] is False
            assert payload["error"]["code"] == "VALIDATION_FAILED"
            assert len(payload["error"]["details"]) > 0
            assert "request_id" in payload["error"]


@pytest.mark.asyncio
class TestHealthChecksAndLiveness:
    """Verifies Kubernetes and Edge container probes."""

    async def test_k8s_liveness_probe(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health/live")
            assert resp.status_code == 200
            assert resp.json()["data"]["status"] == "UP"

    async def test_k8s_readiness_probe(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health/ready")
            assert resp.status_code == 200
            assert resp.json()["data"]["status"] == "READY"

    async def test_platform_health_endpoint(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/platform/health")
            assert resp.status_code == 200
            payload = resp.json()
            assert payload["success"] is True
            assert payload["data"]["status"] == "UP"


@pytest.mark.asyncio
class TestOpenAPIContractConformity:
    """Verifies that the generated OpenAPI schema meets standard contract specifications."""

    def test_openapi_schema_structure(self):
        openapi = app.openapi()
        assert openapi["openapi"].startswith("3.1.")
        assert openapi["info"]["title"] == "Dhruva.AI V2 Core API"
        assert openapi["info"]["version"] == "2.0.0"

        # Verify key resource paths are present in schema
        paths = openapi.get("paths", {})
        assert "/api/v1/auth/login" in paths
        assert "/api/v1/platform/health" in paths
        assert len(paths) >= 90
