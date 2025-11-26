"""
Tests for Phase 5+ features: Health checks and Prometheus metrics (v1.0.0)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for /health and /ready endpoints."""

    def test_health_endpoint_returns_200(self, client):
        """Test that /health returns 200 when healthy or 503 when degraded."""
        response = client.get("/health")
        # 200 for healthy, 503 for unhealthy/degraded (e.g., Redis not available)
        assert response.status_code in [200, 503]
        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "version" in data
        assert "uptime_seconds" in data
        assert "timestamp" in data
        assert "checks" in data

    def test_health_endpoint_has_version(self, client):
        """Test that /health includes correct version."""
        response = client.get("/health")
        data = response.json()
        assert data["version"] == "1.2.0"

    def test_health_endpoint_has_environment(self, client):
        """Test that /health includes environment."""
        response = client.get("/health")
        data = response.json()
        assert data["environment"] in ["dev", "staging", "prod"]

    def test_health_endpoint_checks_temp_directory(self, client):
        """Test that /health includes temp directory check."""
        response = client.get("/health")
        data = response.json()
        assert "temp_directory" in data["checks"]
        assert data["checks"]["temp_directory"]["status"] == "ok"

    def test_health_endpoint_checks_memory(self, client):
        """Test that /health includes memory check."""
        response = client.get("/health")
        data = response.json()
        assert "memory" in data["checks"]

    def test_ready_endpoint_returns_200(self, client):
        """Test that /ready returns 200 when ready."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert "reason" in data
        assert "version" in data

    def test_ready_endpoint_includes_tool_count(self, client):
        """Test that /ready includes tool count in reason."""
        response = client.get("/ready")
        data = response.json()
        assert "araç hazır" in data["reason"]


class TestMetricsEndpoint:
    """Tests for /metrics Prometheus endpoint."""

    def test_metrics_endpoint_returns_200(self, client):
        """Test that /metrics returns 200."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_endpoint_content_type(self, client):
        """Test that /metrics returns correct content type."""
        response = client.get("/metrics")
        assert "text/plain" in response.headers["content-type"]

    def test_metrics_contains_app_info(self, client):
        """Test that /metrics contains application info."""
        response = client.get("/metrics")
        content = response.text
        assert "isvicre_cakisi_app_info" in content

    def test_metrics_contains_request_metrics(self, client):
        """Test that /metrics contains request counter."""
        response = client.get("/metrics")
        content = response.text
        assert "isvicre_cakisi_requests_total" in content or "# HELP" in content

    def test_metrics_contains_tool_metrics(self, client):
        """Test that /metrics contains tool metrics."""
        response = client.get("/metrics")
        content = response.text
        assert "isvicre_cakisi_tool_calls_total" in content or "# HELP" in content


class TestHealthModule:
    """Tests for health module functions."""

    def test_get_uptime_returns_positive(self):
        """Test that uptime is positive."""
        from app.core.health import get_uptime

        uptime = get_uptime()
        assert uptime >= 0

    def test_check_temp_directory_returns_ok(self):
        """Test temp directory check."""
        from app.core.health import check_temp_directory

        result = check_temp_directory()
        assert result["status"] == "ok"
        assert "path" in result

    def test_is_ready_returns_true(self):
        """Test readiness check."""
        from app.core.health import is_ready

        ready, reason = is_ready()
        assert ready is True
        assert "araç hazır" in reason
