from fastapi.testclient import TestClient


def test_qr_code_page(client: TestClient):
    response = client.get("/tools/qr-code/")
    assert response.status_code == 200
    assert "QR Kod Oluşturucu" in response.text
    assert "Metin veya URL" in response.text
    assert 'name="text"' in response.text
    assert 'name="fill_color"' in response.text
    assert 'name="back_color"' in response.text
    assert 'name="error_correction"' in response.text
    assert 'name="size"' in response.text


def test_qr_code_generation(client: TestClient):
    data = {
        "text": "https://example.com",
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


def test_qr_code_still_accepts_content_field(client: TestClient):
    response = client.post(
        "/tools/qr-code/generate", data={"content": "https://example.com"}
    )
    assert response.status_code == 200
    assert "data:image/png;base64" in response.text


def test_qr_code_missing_content(client: TestClient):
    response = client.post("/tools/qr-code/generate", data={})
    assert response.status_code == 200
    assert "QR kod oluşturmak için metin veya URL girin." in response.text
