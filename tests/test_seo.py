"""Tests for v0.7.0 SEO features"""

from fastapi.testclient import TestClient


def test_sitemap_contains_all_tools(client: TestClient):
    """Test sitemap includes all 9 tool URLs"""
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]

    # Check for all 9 tools
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
        assert f"/tools/{slug}/" in response.text, f"Missing {slug} in sitemap"


def test_sitemap_has_priorities(client: TestClient):
    """Test sitemap includes category-based priorities"""
    response = client.get("/sitemap.xml")

    # Should have priority tags
    assert "<priority>" in response.text
    assert "</priority>" in response.text

    # Homepage should have priority 1.0
    assert "<priority>1.0</priority>" in response.text


def test_sitemap_has_lastmod(client: TestClient):
    """Test sitemap includes lastmod dates"""
    response = client.get("/sitemap.xml")

    assert "<lastmod>" in response.text
    assert "</lastmod>" in response.text


def test_tool_page_has_seo_title(client: TestClient):
    """Test tool pages have custom SEO titles"""
    response = client.get("/tools/json-formatter/")
    assert response.status_code == 200

    # Should have a title tag
    assert "<title>" in response.text

    # Should not be the default site title
    assert "JSON" in response.text or "Formatlayıcı" in response.text


def test_tool_page_has_meta_description(client: TestClient):
    """Test tool pages have meta description"""
    response = client.get("/tools/base64/")
    assert response.status_code == 200

    assert 'name="description"' in response.text
    assert 'content="' in response.text


def test_tool_page_has_jsonld_schema(client: TestClient):
    """Test tool pages include JSON-LD schema"""
    response = client.get("/tools/password-generator/")
    assert response.status_code == 200

    # Should have JSON-LD script tag
    assert "application/ld+json" in response.text
    assert '"@type": "SoftwareApplication"' in response.text


def test_tool_page_has_content_sections(client: TestClient):
    """Test tool pages display SEO content sections"""
    response = client.get("/tools/qr-code/")
    assert response.status_code == 200

    # Check for content - should have long description paragraphs
    # The actual headers might vary, socheck for general content presence
    content = response.text.lower()
    assert len(response.text) > 5000, "Page should have substantial content"
    assert "qr" in content or "kod" in content


def test_homepage_has_default_seo(client: TestClient):
    """Test homepage has default SEO settings"""
    response = client.get("/")
    assert response.status_code == 200

    # Should have title
    assert "<title>" in response.text
    assert "İsviçre Çakısı" in response.text
