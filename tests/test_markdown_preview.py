from fastapi.testclient import TestClient


def test_markdown_preview_page(client: TestClient):
    response = client.get("/tools/markdown-preview/")
    assert response.status_code == 200
    assert "Markdown Önizleme" in response.text
    assert "Markdown Editör" in response.text


def test_markdown_rendering(client: TestClient):
    data = {"content": "# Hello World\n\n**Bold**"}
    response = client.post("/tools/markdown-preview/render", data=data)
    assert response.status_code == 200
    assert "<h1>Hello World</h1>" in response.text
    assert "<strong>Bold</strong>" in response.text


def test_markdown_rendering_empty(client: TestClient):
    response = client.post("/tools/markdown-preview/render", data={"content": ""})
    assert response.status_code == 200
    assert response.text.strip() == ""
