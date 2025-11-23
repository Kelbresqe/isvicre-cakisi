import pytest
from app.core.cache import get_cached_result, set_cached_result, clear_cache


def test_cache_operations():
    # Clear cache
    clear_cache()

    tool = "test-tool"
    input_text = "test-input"
    result = "test-result"

    # Should be miss
    assert get_cached_result(tool, input_text) is None

    # Set cache (need to register tool first or mock it, but cache module checks tool_slug existence)
    # The cache module checks: if tool_slug not in _text_tool_caches: return
    # So we need to use a valid tool slug or mock _text_tool_caches

    # Use a real tool slug for testing
    tool = "json-formatter"

    set_cached_result(tool, input_text, result)

    # Should be hit
    assert get_cached_result(tool, input_text) == result

    # Different input should be miss
    assert get_cached_result(tool, "other-input") is None


def test_cache_key_generation():
    from app.core.cache import _generate_cache_key

    key1 = _generate_cache_key("tool", "input", action="encode")
    key2 = _generate_cache_key("tool", "input", action="encode")
    key3 = _generate_cache_key("tool", "input", action="decode")

    assert key1 == key2
    assert key1 != key3
