import pytest
from fastapi.testclient import TestClient

from app.core.config import Environment, settings
from app.main import app


def test_dev_trusted_hosts_always_allow_localhost(monkeypatch):
    monkeypatch.setattr(settings, "ENV", Environment.DEV)
    monkeypatch.setattr(settings, "TRUSTED_HOSTS", ["127.0.0.1", "testserver"])

    middleware = next(
        item
        for item in app.user_middleware
        if item.cls.__name__ == "IPv6AwareTrustedHostMiddleware"
    )

    assert "localhost" in middleware.kwargs["allowed_hosts"]
    assert "127.0.0.1" in middleware.kwargs["allowed_hosts"]
    assert "::1" in middleware.kwargs["allowed_hosts"]
    assert "[::1]" in middleware.kwargs["allowed_hosts"]
    assert settings.trusted_hosts == [
        "127.0.0.1",
        "testserver",
        "localhost",
        "::1",
        "[::1]",
    ]


def test_prod_trusted_hosts_do_not_add_localhost(monkeypatch):
    monkeypatch.setattr(settings, "ENV", Environment.PROD)
    monkeypatch.setattr(settings, "TRUSTED_HOSTS", ["example.com"])

    assert settings.trusted_hosts == ["example.com"]


@pytest.mark.parametrize(
    "host_header",
    [
        pytest.param("localhost:8000", id="curl-localhost-8000"),
        pytest.param("[::1]:8000", id="curl-ipv6-loopback-8000-regression"),
    ],
)
def test_dev_loopback_requests_are_not_rejected_as_invalid_host(
    monkeypatch, host_header
):
    """Dev mode accepts localhost and IPv6 loopback curl-equivalent hosts."""
    monkeypatch.setattr(settings, "ENV", Environment.DEV)
    monkeypatch.setattr(settings, "TRUSTED_HOSTS", ["testserver"])

    with TestClient(app) as client:
        response = client.get("/", headers={"host": host_header})

    assert response.status_code == 200
    assert "Invalid host header" not in response.text


def test_dev_ipv6_loopback_request_is_allowed_without_broad_bracket_trust(monkeypatch):
    monkeypatch.setattr(settings, "ENV", Environment.DEV)
    monkeypatch.setattr(settings, "TRUSTED_HOSTS", ["testserver"])

    assert "[" not in settings.trusted_hosts

    with TestClient(app) as client:
        response = client.get("/", headers={"host": "[::1]:8000"})

    assert response.status_code == 200
    assert "Invalid host header" not in response.text


def test_untrusted_host_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "ENV", Environment.DEV)
    monkeypatch.setattr(settings, "TRUSTED_HOSTS", ["testserver"])

    with TestClient(app) as client:
        response = client.get("/", headers={"host": "example.invalid"})

    assert response.status_code == 400
    assert response.text == "Invalid host header"
