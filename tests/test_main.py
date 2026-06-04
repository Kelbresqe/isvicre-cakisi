from pathlib import Path

from app.core.config import Environment, settings
from app.core.utils import resolve_temp_file, safe_upload_path
from app.main import clean_directory_contents


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "İsviçre Çakısı" in response.text


def test_sitemap(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert "<urlset" in response.text


def test_admin_stats(client, monkeypatch):
    monkeypatch.setattr(settings, "ENV", Environment.DEV)
    response = client.get("/admin/stats")
    assert response.status_code == 200
    # Should return HTML in dev mode
    assert "text/html" in response.headers.get("content-type", "")
    assert "Admin Dashboard" in response.text


def test_clean_directory_contents_keeps_parent_directory(tmp_path: Path):
    temp_dir = tmp_path / "temp"
    nested_dir = temp_dir / "nested"
    nested_dir.mkdir(parents=True)
    (temp_dir / "file.txt").write_text("remove me")
    (nested_dir / "nested.txt").write_text("remove me too")

    clean_directory_contents(temp_dir)

    assert temp_dir.exists()
    assert list(temp_dir.iterdir()) == []


def test_resolve_temp_file_rejects_path_traversal():
    assert resolve_temp_file("../secret.txt") is None
    assert resolve_temp_file("nested/secret.txt") is None


def test_resolve_temp_file_accepts_plain_temp_filename():
    resolved = resolve_temp_file("output.pdf")
    assert resolved == settings.TEMP_DIR.resolve() / "output.pdf"


def test_safe_upload_path_ignores_user_filename_suffix():
    upload_path = safe_upload_path("split_in", ".pdf")

    assert upload_path.parent == settings.TEMP_DIR
    assert upload_path.name.startswith("split_in_")
    assert upload_path.suffix == ".pdf"
    assert "evil" not in upload_path.name


def test_admin_endpoints_require_bearer_token_in_prod(client, monkeypatch):
    monkeypatch.setattr(settings, "ENV", Environment.PROD)
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "test-token")

    assert client.get("/ready").status_code == 401
    assert client.get("/metrics").status_code == 401

    headers = {"Authorization": "Bearer test-token"}
    assert client.get("/ready", headers=headers).status_code in {200, 503}
    assert client.get("/metrics", headers=headers).status_code == 200
