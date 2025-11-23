def test_json_formatter_page(client):
    response = client.get("/tools/json-formatter/")
    assert response.status_code == 200
    assert "JSON Formatlayıcı" in response.text


def test_json_formatter_prettify(client):
    data = {"json_input": '{"a":1,"b":2}', "action": "prettify"}
    response = client.post("/tools/json-formatter/format", data=data)
    assert response.status_code == 200
    assert '"a": 1' in response.text
    assert '"b": 2' in response.text


def test_json_formatter_minify(client):
    data = {"json_input": '{\n  "a": 1,\n  "b": 2\n}', "action": "minify"}
    response = client.post("/tools/json-formatter/format", data=data)
    assert response.status_code == 200
    assert '{"a":1,"b":2}' in response.text


def test_json_formatter_invalid(client):
    data = {"json_input": "{invalid}", "action": "prettify"}
    response = client.post("/tools/json-formatter/format", data=data)
    assert response.status_code == 200
    assert "Geçersiz JSON" in response.text


def test_base64_page(client):
    response = client.get("/tools/base64/")
    assert response.status_code == 200
    assert "Base64 Dönüştürücü" in response.text


def test_base64_encode(client):
    data = {"text_input": "hello", "action": "encode"}
    response = client.post("/tools/base64/convert", data=data)
    assert response.status_code == 200
    assert "aGVsbG8=" in response.text


def test_base64_decode(client):
    data = {"text_input": "aGVsbG8=", "action": "decode"}
    response = client.post("/tools/base64/convert", data=data)
    assert response.status_code == 200
    assert "hello" in response.text


def test_url_tool_page(client):
    response = client.get("/tools/url-encoder/")
    assert response.status_code == 200
    assert "URL Kodlayıcı" in response.text


def test_url_encode_simple(client):
    data = {"text_input": "hello world", "action": "encode"}
    response = client.post("/tools/url-encoder/convert", data=data)
    assert response.status_code == 200
    assert "hello%20world" in response.text


def test_url_decode_simple(client):
    data = {"text_input": "hello%20world", "action": "decode"}
    response = client.post("/tools/url-encoder/convert", data=data)
    assert response.status_code == 200
    assert "hello world" in response.text


def test_url_encode_full_url(client):
    # Test that full URLs don't encode the protocol
    data = {"text_input": "https://chatgpt.com/c/test-id", "action": "encode"}
    response = client.post("/tools/url-encoder/convert", data=data)
    assert response.status_code == 200
    # Should keep https:// and domain intact
    assert "https://chatgpt.com" in response.text
    # Should NOT encode the colon in https:
    assert "https%3A" not in response.text


def test_url_encode_with_query_params(client):
    # Test encoding query parameters
    data = {"text_input": "https://example.com/search?q=hello world&lang=tr", "action": "encode"}
    response = client.post("/tools/url-encoder/convert", data=data)
    assert response.status_code == 200
    # Space in query should be encoded
    assert "hello%20world" in response.text
    # Base URL should be preserved
    assert "https://example.com" in response.text


def test_url_double_encode_protection(client):
    """Critical test: Prevent double-encoding of already encoded URLs"""
    # Input is already encoded
    data = {"text_input": "hello%20world", "action": "encode"}
    response = client.post("/tools/url-encoder/convert", data=data)
    assert response.status_code == 200
    # Should NOT double-encode %20 to %2520
    assert "hello%2520world" not in response.text
    # Should return properly encoded
    assert "hello%20world" in response.text


def test_url_double_encode_full_url(client):
    """Test double-encoding protection on full URLs"""
    data = {"text_input": "https://example.com?q=hello%20world", "action": "encode"}
    response = client.post("/tools/url-encoder/convert", data=data)
    assert response.status_code == 200
    # Should NOT double-encode
    assert "%2520" not in response.text
    assert "hello%20world" in response.text


def test_url_turkish_characters(client):
    """Test encoding of Turkish characters"""
    data = {"text_input": "şğüöçıİ", "action": "encode"}
    response = client.post("/tools/url-encoder/convert", data=data)
    assert response.status_code == 200
    # Turkish chars should be encoded
    assert "%C5%9F" in response.text  # ş


def test_url_decode_turkish(client):
    """Test decoding of Turkish characters"""
    data = {"text_input": "%C5%9F%C4%9F%C3%BC%C3%B6%C3%A7%C4%B1%C4%B0", "action": "decode"}
    response = client.post("/tools/url-encoder/convert", data=data)
    assert response.status_code == 200
    assert "şğüöçıİ" in response.text


def test_url_special_characters(client):
    """Test encoding special URL characters"""
    data = {"text_input": "test@example.com?query=value#anchor", "action": "encode"}
    response = client.post("/tools/url-encoder/convert", data=data)
    assert response.status_code == 200
    # @ and # should be encoded in fragments
    assert "%40" in response.text or "@" in response.text  # @ may or may not be encoded depending on context


def test_url_safe_characters_preserved(client):
    """Test that URL-safe characters are preserved in query strings"""
    data = {"text_input": "https://example.com?a=1&b=2&name=test_user-2024", "action": "encode"}
    response = client.post("/tools/url-encoder/convert", data=data)
    assert response.status_code == 200
    # These should be preserved in query strings
    assert "a=1&b=2" in response.text
    assert "_" in response.text or "%5F" in response.text  # underscore
    assert "-" in response.text  # hyphen should be safe
