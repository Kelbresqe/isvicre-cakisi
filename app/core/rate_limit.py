"""
Rate limiting module for request throttling.
Implements IP-based rate limiting with configurable thresholds.
"""

import time
from collections import defaultdict, deque
from typing import Dict

from fastapi import HTTPException, Request

from app.core.config import settings
from app.core.observability import log_security_event


class RateLimiter:
    """
    Simple in-memory rate limiter tracking requests per IP.
    """

    def __init__(self):
        # IP -> deque of timestamps (recent requests)
        self._request_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        # IP -> total uploaded bytes in current hour window
        self._upload_bytes: Dict[str, Dict[str, int]] = defaultdict(lambda: {"bytes": 0, "window_start": time.time()})

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

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        # Skip rate limiting in dev mode if configured
        if settings.is_dev and settings.MAX_REQUESTS_PER_MINUTE > 1000:
            return

        ip = self._get_client_ip(request)
        now = time.time()

        # Clean old requests (older than 1 minute)
        request_times = self._request_times[ip]
        cutoff = now - 60  # 60 seconds window

        # Remove old timestamps
        while request_times and request_times[0] < cutoff:
            request_times.popleft()

        # Check request count limit
        if len(request_times) >= settings.MAX_REQUESTS_PER_MINUTE:
            log_security_event(
                "rate_limit_exceeded",
                {"ip": ip, "limit": settings.MAX_REQUESTS_PER_MINUTE, "type": "requests"},
            )
            raise HTTPException(
                status_code=429,
                detail=f"Çok sık istek gönderdiniz. Lütfen {60} saniye sonra tekrar deneyin.",
            )

        # Add current request
        request_times.append(now)

    def check_upload_limit(self, request: Request, file_size_bytes: int) -> None:
        """
        Check if upload size limit is exceeded for this IP.

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
        now = time.time()

        upload_data = self._upload_bytes[ip]

        # Reset window if it's been more than an hour
        if now - upload_data["window_start"] > 3600:
            upload_data["bytes"] = 0
            upload_data["window_start"] = now

        max_bytes = settings.MAX_UPLOAD_MB_PER_HOUR * 1024 * 1024

        # Check if adding this file would exceed limit
        if upload_data["bytes"] + file_size_bytes > max_bytes:
            log_security_event(
                "upload_limit_exceeded",
                {
                    "ip": ip,
                    "current_mb": upload_data["bytes"] / (1024 * 1024),
                    "limit_mb": settings.MAX_UPLOAD_MB_PER_HOUR,
                },
            )
            raise HTTPException(
                status_code=413,
                detail=f"Saatlik upload limitini aştınız. Limit: {settings.MAX_UPLOAD_MB_PER_HOUR} MB.",
            )

        # Add to counter
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
