from fastapi.testclient import TestClient


def test_password_generator_page(client: TestClient):
    response = client.get("/tools/password-generator/")
    assert response.status_code == 200
    assert "Şifre Oluşturucu" in response.text
    assert "Şifre Uzunluğu" in response.text


def test_password_generation_default(client: TestClient):
    response = client.post("/tools/password-generator/generate", data={})
    assert response.status_code == 200
    assert "kopyala" in response.text.lower()
    # Default length is 16
    # We can't easily check the length in the HTML without parsing,
    # but we can check if the response contains a password field


def test_password_generation_custom(client: TestClient):
    data = {"length": 32, "use_uppercase": True, "use_lowercase": True, "use_numbers": True, "use_symbols": True}
    response = client.post("/tools/password-generator/generate", data=data)
    assert response.status_code == 200
    assert "Çok Güçlü" in response.text


def test_password_generation_invalid_length(client: TestClient):
    # Should be clamped
    data = {"length": 200}
    response = client.post("/tools/password-generator/generate", data=data)
    assert response.status_code == 200
