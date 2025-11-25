"""
Rate limiting module for request throttling.
Implements IP-based rate limiting with Redis support for distributed environments.
Falls back to in-memory storage when Redis is unavailable.
"""

import time
from collections import defaultdict, deque
from typing import Optional

import structlog
from fastapi import HTTPException, Request

from app.core.config import settings
from app.core.observability import log_security_event

logger = structlog.get_logger()


class RateLimiter:
    """
    Rate limiter with Redis support for distributed deployments.
    Falls back to in-memory storage when Redis is unavailable.
    """

    def __init__(self):
        # In-memory fallback stores
        self._request_times: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._upload_bytes: dict[str, dict[str, int | float]] = defaultdict(
            lambda: {"bytes": 0, "window_start": time.time()}
        )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, considering proxies."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        if request.client:
            return request.client.host

        return "unknown"

    def _get_redis_request_count(self, ip: str) -> Optional[int]:
        """Get request count from Redis. Returns None if Redis unavailable."""
        try:
            from app.core.redis_client import redis_get

            key = f"ratelimit:requests:{ip}"
            value = redis_get(key)
            if value is not None:
                return int(value)
            return 0
        except Exception as e:
            logger.debug("redis_ratelimit_get_failed", error=str(e))
            return None

    def _increment_redis_request_count(self, ip: str) -> bool:
        """Increment request count in Redis. Returns True if successful."""
        try:
            from app.core.redis_client import redis_incr

            key = f"ratelimit:requests:{ip}"
            redis_incr(key, ttl=60)  # 60 second window
            return True
        except Exception as e:
            logger.debug("redis_ratelimit_incr_failed", error=str(e))
            return False

    def _get_redis_upload_bytes(self, ip: str) -> Optional[int]:
        """Get upload bytes from Redis. Returns None if Redis unavailable."""
        try:
            from app.core.redis_client import redis_get

            key = f"ratelimit:upload:{ip}"
            value = redis_get(key)
            if value is not None:
                return int(value)
            return 0
        except Exception as e:
            logger.debug("redis_upload_get_failed", error=str(e))
            return None

    def _increment_redis_upload_bytes(self, ip: str, bytes_count: int) -> bool:
        """Increment upload bytes in Redis. Returns True if successful."""
        try:
            from app.core.redis_client import redis_get, redis_incr

            key = f"ratelimit:upload:{ip}"
            current = redis_get(key)
            if current is None:
                # First upload in window, set with expiry
                redis_incr(key, amount=bytes_count, ttl=3600)  # 1 hour window
            else:
                redis_incr(key, amount=bytes_count)
            return True
        except Exception as e:
            logger.debug("redis_upload_incr_failed", error=str(e))
            return False

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, considering proxies."""
        # Check X-Forwarded-For header first (for proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to direct client
        if request.client:
            return request.client.host

        return "unknown"

    def check_rate_limit(self, request: Request) -> None:
        """
        Check if request should be rate limited.
        Uses Redis if available, falls back to in-memory.

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        # Skip rate limiting in dev mode if configured
        if settings.is_dev and settings.MAX_REQUESTS_PER_MINUTE > 1000:
            return

        ip = self._get_client_ip(request)

        # Try Redis first
        redis_count = self._get_redis_request_count(ip)
        if redis_count is not None:
            # Using Redis
            if redis_count >= settings.MAX_REQUESTS_PER_MINUTE:
                log_security_event(
                    "rate_limit_exceeded",
                    {"ip": ip, "limit": settings.MAX_REQUESTS_PER_MINUTE, "type": "requests", "source": "redis"},
                )
                raise HTTPException(
                    status_code=429,
                    detail="Çok sık istek gönderdiniz. Lütfen 60 saniye sonra tekrar deneyin.",
                )
            self._increment_redis_request_count(ip)
            return

        # Fallback to in-memory
        now = time.time()
        request_times = self._request_times[ip]
        cutoff = now - 60

        while request_times and request_times[0] < cutoff:
            request_times.popleft()

        if len(request_times) >= settings.MAX_REQUESTS_PER_MINUTE:
            log_security_event(
                "rate_limit_exceeded",
                {"ip": ip, "limit": settings.MAX_REQUESTS_PER_MINUTE, "type": "requests", "source": "memory"},
            )
            raise HTTPException(
                status_code=429,
                detail="Çok sık istek gönderdiniz. Lütfen 60 saniye sonra tekrar deneyin.",
            )

        request_times.append(now)

    def check_upload_limit(self, request: Request, file_size_bytes: int) -> None:
        """
        Check if upload size limit is exceeded for this IP.
        Uses Redis if available, falls back to in-memory.

        Args:
            request: FastAPI request object
            file_size_bytes: Size of upload in bytes

        Raises:
            HTTPException: 413 if upload limit exceeded
        """
        # Skip in dev mode
        if settings.is_dev and settings.MAX_UPLOAD_MB_PER_HOUR > 10000:
            return

        ip = self._get_client_ip(request)
        max_bytes = settings.MAX_UPLOAD_MB_PER_HOUR * 1024 * 1024

        # Try Redis first
        redis_bytes = self._get_redis_upload_bytes(ip)
        if redis_bytes is not None:
            # Using Redis
            if redis_bytes + file_size_bytes > max_bytes:
                log_security_event(
                    "upload_limit_exceeded",
                    {
                        "ip": ip,
                        "current_mb": redis_bytes / (1024 * 1024),
                        "limit_mb": settings.MAX_UPLOAD_MB_PER_HOUR,
                        "source": "redis",
                    },
                )
                raise HTTPException(
                    status_code=413,
                    detail=f"Saatlik upload limitini aştınız. Limit: {settings.MAX_UPLOAD_MB_PER_HOUR} MB.",
                )
            self._increment_redis_upload_bytes(ip, file_size_bytes)
            return

        # Fallback to in-memory
        now = time.time()
        upload_data = self._upload_bytes[ip]

        if now - upload_data["window_start"] > 3600:
            upload_data["bytes"] = 0
            upload_data["window_start"] = now

        if upload_data["bytes"] + file_size_bytes > max_bytes:
            log_security_event(
                "upload_limit_exceeded",
                {
                    "ip": ip,
                    "current_mb": upload_data["bytes"] / (1024 * 1024),
                    "limit_mb": settings.MAX_UPLOAD_MB_PER_HOUR,
                    "source": "memory",
                },
            )
            raise HTTPException(
                status_code=413,
                detail=f"Saatlik upload limitini aştınız. Limit: {settings.MAX_UPLOAD_MB_PER_HOUR} MB.",
            )

        upload_data["bytes"] += file_size_bytes


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_dependency(request: Request) -> None:
    """
    FastAPI dependency for rate limiting.

    Usage:
        @router.post("/endpoint", dependencies=[Depends(rate_limit_dependency)])
        async def my_endpoint():
            ...
    """
    rate_limiter.check_rate_limit(request)


def reset_rate_limits() -> None:
    """Reset all rate limits (useful for testing)."""
    rate_limiter._request_times.clear()
    rate_limiter._upload_bytes.clear()

    # Also clear Redis rate limit keys
    try:
        from app.core.redis_client import get_redis_client

        client = get_redis_client()
        if client:
            for pattern in ["ratelimit:requests:*", "ratelimit:upload:*"]:
                keys = client.keys(f"{settings.REDIS_KEY_PREFIX}{pattern}")
                if keys:
                    client.delete(*keys)
    except Exception as e:
        logger.debug("redis_ratelimit_reset_failed", error=str(e))


def get_rate_limit_stats() -> dict:
    """Get rate limiter statistics."""
    stats = {
        "memory": {
            "tracked_ips": len(rate_limiter._request_times),
            "upload_ips": len(rate_limiter._upload_bytes),
        },
        "redis": {"available": False, "request_keys": 0, "upload_keys": 0},
    }

    try:
        from app.core.redis_client import get_redis_client

        client = get_redis_client()
        if client:
            stats["redis"]["available"] = True
            req_pattern = f"{settings.REDIS_KEY_PREFIX}ratelimit:requests:*"
            up_pattern = f"{settings.REDIS_KEY_PREFIX}ratelimit:upload:*"
            stats["redis"]["request_keys"] = len(client.keys(req_pattern))
            stats["redis"]["upload_keys"] = len(client.keys(up_pattern))
    except Exception:
        pass

    return stats
