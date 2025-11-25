from fastapi.testclient import TestClient


def test_qr_code_page(client: TestClient):
    response = client.get("/tools/qr-code/")
    assert response.status_code == 200
    assert "QR Kod Oluşturucu" in response.text
    assert "Metin veya URL" in response.text


def test_qr_code_generation(client: TestClient):
    data = {
        "content": "https://example.com",
        "size": 10,
        "border": 4,
        "fill_color": "#000000",
        "back_color": "#ffffff",
        "error_correction": "M",
    }
    response = client.post("/tools/qr-code/generate", data=data)
    assert response.status_code == 200
    assert "data:image/png;base64" in response.text
    assert "PNG İndir" in response.text


def test_qr_code_missing_content(client: TestClient):
    response = client.post("/tools/qr-code/generate", data={})
    assert response.status_code == 422  # Validation error
