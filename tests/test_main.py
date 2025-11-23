def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "İsviçre Çakısı" in response.text


def test_sitemap(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert "<urlset" in response.text


def test_admin_stats(client):
    response = client.get("/admin/stats")
    assert response.status_code == 200
    # Should return HTML in dev mode
    assert "text/html" in response.headers.get("content-type", "")
    assert "Admin Dashboard" in response.text
