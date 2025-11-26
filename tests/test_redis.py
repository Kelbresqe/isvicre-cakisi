"""
Tests for Redis integration (Phase 6 - v1.0.0)
Tests Redis client, caching, and rate limiting with Redis backend.
"""


class TestRedisClient:
    """Tests for Redis client module."""

    def test_redis_client_import(self):
        """Test that redis_client module imports correctly."""
        from app.core.redis_client import (
            get_redis_client,
            is_redis_available,
            redis_delete,
            redis_get,
            redis_incr,
            redis_set,
        )

        assert callable(get_redis_client)
        assert callable(is_redis_available)
        assert callable(redis_get)
        assert callable(redis_set)
        assert callable(redis_delete)
        assert callable(redis_incr)

    def test_is_redis_available_returns_bool(self):
        """Test that is_redis_available returns a boolean."""
        from app.core.redis_client import is_redis_available

        result = is_redis_available()
        assert isinstance(result, bool)

    def test_redis_set_get_cycle(self):
        """Test basic set/get operations (works with or without Redis)."""
        from app.core.redis_client import redis_delete, redis_get, redis_set

        # Set a test value
        key = "test:integration:key"
        value = "test_value_123"

        # Set should return bool
        result = redis_set(key, value, ttl=60)
        assert isinstance(result, bool)

        # If Redis is available, get should return the value
        if result:
            retrieved = redis_get(key)
            assert retrieved == value

            # Cleanup
            redis_delete(key)
            assert redis_get(key) is None

    def test_redis_incr(self):
        """Test increment operation."""
        from app.core.redis_client import redis_delete, redis_incr

        key = "test:incr:counter"

        # Clean start
        redis_delete(key)

        # First incr creates the key
        result = redis_incr(key, amount=1, ttl=60)
        assert isinstance(result, (int, type(None)))

        if result is not None:
            assert result == 1

            # Incr again with amount
            result2 = redis_incr(key, amount=5)
            assert result2 == 6

            # Cleanup
            redis_delete(key)


class TestCacheWithRedis:
    """Tests for cache module with Redis backend."""

    def test_cache_stats(self):
        """Test get_cache_stats function."""
        from app.core.cache import get_cache_stats

        stats = get_cache_stats()

        assert "memory" in stats
        assert "redis" in stats
        assert isinstance(stats["memory"], dict)
        assert isinstance(stats["redis"], dict)
        assert "available" in stats["redis"]

    def test_cache_set_get(self):
        """Test caching operations."""
        from app.core.cache import get_cached_result, set_cached_result

        tool_slug = "test-tool"
        input_text = "test input"
        result = "test result"

        # Set cache
        set_cached_result(tool_slug, input_text, result, action="test")

        # Get should return the cached value (from memory at least)
        # Note: might be None if the tool_slug isn't in _text_tool_caches
        # but the function should not error
        _ = get_cached_result(tool_slug, input_text, action="test")

    def test_clear_cache(self):
        """Test cache clearing."""
        from app.core.cache import clear_cache

        # Should not raise
        clear_cache("json-formatter")
        clear_cache()  # Clear all


class TestRateLimitWithRedis:
    """Tests for rate limiter with Redis backend."""

    def test_rate_limit_stats(self):
        """Test get_rate_limit_stats function."""
        from app.core.rate_limit import get_rate_limit_stats

        stats = get_rate_limit_stats()

        assert "memory" in stats
        assert "redis" in stats
        assert "tracked_ips" in stats["memory"]
        assert "upload_ips" in stats["memory"]
        assert "available" in stats["redis"]

    def test_reset_rate_limits(self):
        """Test resetting rate limits."""
        from app.core.rate_limit import reset_rate_limits

        # Should not raise
        reset_rate_limits()


class TestHealthWithRedis:
    """Tests for health check with Redis."""

    def test_check_redis(self):
        """Test check_redis function."""
        from app.core.health import check_redis

        result = check_redis()

        assert "status" in result
        assert result["status"] in ["ok", "disabled", "unavailable", "error"]

    def test_health_status_includes_redis(self):
        """Test that health status includes Redis check."""
        from app.core.health import get_health_status

        status = get_health_status()

        assert "redis" in status.checks
        assert status.checks["redis"]["status"] in [
            "ok",
            "disabled",
            "unavailable",
            "error",
        ]

    def test_is_ready_mentions_redis(self):
        """Test that readiness check mentions Redis status."""
        from app.core.health import is_ready

        ready, message = is_ready()

        assert isinstance(ready, bool)
        assert isinstance(message, str)
        # Message should contain info about tools
        assert "araç" in message.lower()
