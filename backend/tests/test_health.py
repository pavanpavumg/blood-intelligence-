import pytest
from httpx import AsyncClient
from unittest.mock import patch

@pytest.mark.asyncio
async def test_health_endpoint_healthy(async_client: AsyncClient) -> None:
    """
    Test GET /api/health returns status 200 and {'status': 'ok'} when DB & Redis connected.
    """
    with patch("app.services.health.check_database_connection", return_value=True), \
         patch("app.services.health.check_redis_connection", return_value=True):
        
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"
        assert data["redis"] == "connected"

@pytest.mark.asyncio
async def test_health_endpoint_unhealthy_when_db_down(async_client: AsyncClient) -> None:
    """
    Test GET /api/health reports unhealthy when PostgreSQL database connection fails.
    """
    with patch("app.services.health.check_database_connection", return_value=False), \
         patch("app.services.health.check_redis_connection", return_value=True):
        
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
        assert data["redis"] == "connected"
