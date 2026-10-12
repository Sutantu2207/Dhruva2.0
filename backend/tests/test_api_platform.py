"""Dhruva.AI V2 — Integration Tests: Platform Health & Readiness Probes.

Tests:
- /health/live (Kubernetes liveness probe)
- /health/ready (Kubernetes readiness probe)
- /api/v1/platform/health (Service liveness probe with standard response envelope)
- /api/v1/platform/ready (Service readiness probe verifying database connectivity)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestPlatformAPI:
    """Platform health check and operational readiness probe tests."""

    async def test_k8s_liveness(self, client: AsyncClient):
        response = await client.get("/health/live")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["status"] == "UP"

    async def test_k8s_readiness(self, client: AsyncClient):
        response = await client.get("/health/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["status"] == "READY"

    async def test_api_v1_health(self, client: AsyncClient):
        response = await client.get("/api/v1/platform/health")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["status"] == "UP"
        assert "Dhruva.AI" in body["data"]["message"]

    async def test_api_v1_ready_db_connected(self, client: AsyncClient):
        response = await client.get("/api/v1/platform/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["status"] == "READY"
        assert body["data"]["infrastructure"]["database"]["status"] == "CONNECTED"
        assert "latency_ms" in body["data"]["infrastructure"]["database"]
