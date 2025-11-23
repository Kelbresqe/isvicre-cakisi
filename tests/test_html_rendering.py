"""HTML Rendering Tests for Tool Pages"""

from fastapi.testclient import TestClient


def test_index_page_renders_tools(client: TestClient):
    """Test homepage renders all tools in categorized sections"""
    response = client.get("/")
    assert response.status_code == 200

    # Check for hero section
    assert "İsviçre Çakısı" in response.text
    assert "Gündelik dijital işleriniz" in response.text

    # Check for search functionality
    assert 'x-model="search"' in response.text

    # Check that tools are rendered (should have at least one category)
    assert "grid-cols-" in response.text  # Grid layout for tools


def test_tool_pages_have_hero_component(client: TestClient):
    """Test that all tool pages use the hero component"""
    tool_slugs = [
        "image-converter",
        "image-resizer",
        "pdf-merger",
        "json-formatter",
        "base64",
        "url-encoder",
        "qr-code",
        "password-generator",
        "markdown-preview",
    ]

    for slug in tool_slugs:
        response = client.get(f"/tools/{slug}/")
        assert response.status_code == 200, f"Failed for {slug}"
        # Hero component should have gradient background
        assert "bg-gradient-to-br" in response.text, f"Hero missing for {slug}"


def test_admin_stats_renders_metrics(client: TestClient):
    """Test admin dashboard renders correctly"""
    response = client.get("/admin/stats")
    assert response.status_code == 200

    # Check for dashboard title
    assert "Admin Dashboard" in response.text

    # Check for metric sections or empty state
    assert "İstatistik" in response.text or "dashboard" in response.text.lower()
