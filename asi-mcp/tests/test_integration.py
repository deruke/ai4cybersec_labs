"""Integration tests for MCP Security Server."""

import pytest
import asyncio
from httpx import AsyncClient
import os


@pytest.fixture
def auth_headers():
    """Fixture for authentication headers."""
    token = os.getenv('MCP_TOKEN', 'test-token')
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    async with AsyncClient(base_url="http://localhost:3000") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    async with AsyncClient(base_url="http://localhost:3000") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "endpoints" in data


@pytest.mark.asyncio
async def test_tools_endpoint_requires_auth():
    """Test tools endpoint requires authentication."""
    async with AsyncClient(base_url="http://localhost:3000") as client:
        response = await client.get("/tools")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_tools_endpoint_with_auth(auth_headers):
    """Test tools endpoint with authentication."""
    async with AsyncClient(base_url="http://localhost:3000") as client:
        response = await client.get("/tools", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "count" in data
        assert data["count"] > 0


@pytest.mark.asyncio
async def test_sse_endpoint_requires_auth():
    """Test SSE endpoint requires authentication."""
    async with AsyncClient(base_url="http://localhost:3000") as client:
        response = await client.get("/sse")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_messages_endpoint_requires_auth():
    """Test messages endpoint requires authentication."""
    async with AsyncClient(base_url="http://localhost:3000") as client:
        response = await client.post("/messages", json={})
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_tool_execution_authorized_target(auth_headers):
    """Test tool execution with authorized target."""
    message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "nmap_scan",
            "arguments": {
                "target": "192.168.1.100",
                "scan_type": "sV",
                "ports": "80,443"
            }
        }
    }

    async with AsyncClient(base_url="http://localhost:3000") as client:
        response = await client.post("/messages", json=message, headers=auth_headers)
        assert response.status_code == 200


class TestToolIntegration:
    """Integration tests for individual tools."""

    @pytest.mark.asyncio
    async def test_nmap_scan_basic(self):
        """Test basic nmap scan."""
        from src.tools.network import nmap_scan

        result = await nmap_scan(
            target="192.168.1.1",
            scan_type="sV",
            ports="80"
        )

        assert result["tool"] == "nmap"
        assert result["target"] == "192.168.1.1"
        assert "success" in result

    @pytest.mark.asyncio
    async def test_httpx_scan_basic(self):
        """Test basic httpx scan."""
        from src.tools.web import httpx_scan

        result = await httpx_scan(
            target="http://192.168.1.1"
        )

        assert result["tool"] == "httpx"
        assert "success" in result


@pytest.mark.asyncio
async def test_invalid_tool_name(auth_headers):
    """Test execution with invalid tool name."""
    message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "nonexistent_tool",
            "arguments": {}
        }
    }

    async with AsyncClient(base_url="http://localhost:3000") as client:
        response = await client.post("/messages", json=message, headers=auth_headers)
        # Should return success with appropriate error message
        assert response.status_code == 200
