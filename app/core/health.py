"""
Health Check Module (v0.9.0)

Provides health and readiness endpoints for container orchestration.
- /health: Liveness probe - is the app running?
- /ready: Readiness probe - is the app ready to serve traffic?
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from app.core.config import settings


@dataclass
class HealthStatus:
    """Health check response model."""

    status: Literal["healthy", "unhealthy", "degraded"]
    version: str
    environment: str
    uptime_seconds: float
    timestamp: str
    checks: dict[str, dict] = field(default_factory=dict)


# Application start time for uptime calculation
_start_time: float = time.time()


def get_uptime() -> float:
    """Get application uptime in seconds."""
    return time.time() - _start_time


def check_temp_directory() -> dict:
    """Check if temp directory is accessible."""
    try:
        # Try to write and read a test file
        test_file = settings.TEMP_DIR / ".health_check"
        test_file.write_text("ok")
        content = test_file.read_text()
        test_file.unlink()
        return {"status": "ok", "path": str(settings.TEMP_DIR), "writable": content == "ok"}
    except Exception as e:
        return {"status": "error", "path": str(settings.TEMP_DIR), "error": str(e)}


def check_memory() -> dict:
    """Check memory usage (basic check)."""
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        # Convert to MB
        memory_mb = usage.ru_maxrss / (1024 * 1024) if hasattr(usage, "ru_maxrss") else 0
        # On macOS, ru_maxrss is in bytes, on Linux it's in KB
        import sys

        if sys.platform == "darwin":
            memory_mb = usage.ru_maxrss / (1024 * 1024)
        else:
            memory_mb = usage.ru_maxrss / 1024

        return {"status": "ok", "memory_mb": round(memory_mb, 2)}
    except Exception as e:
        return {"status": "unknown", "error": str(e)}


def get_health_status() -> HealthStatus:
    """
    Get comprehensive health status.
    Used by /health endpoint.
    """
    checks = {
        "temp_directory": check_temp_directory(),
        "memory": check_memory(),
    }

    # Determine overall status
    all_ok = all(c.get("status") == "ok" for c in checks.values())
    any_error = any(c.get("status") == "error" for c in checks.values())

    if all_ok:
        status = "healthy"
    elif any_error:
        status = "unhealthy"
    else:
        status = "degraded"

    return HealthStatus(
        status=status,
        version=settings.VERSION,
        environment=settings.ENV.value,
        uptime_seconds=round(get_uptime(), 2),
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        checks=checks,
    )


def is_ready() -> tuple[bool, str]:
    """
    Check if the application is ready to serve traffic.
    Used by /ready endpoint.

    Returns:
        tuple: (is_ready: bool, reason: str)
    """
    # Check temp directory
    temp_check = check_temp_directory()
    if temp_check.get("status") != "ok":
        return False, f"Temp dizini erişilemez: {temp_check.get('error', 'unknown')}"

    # Check if tools are registered
    from app.tools.registry import ToolRegistry

    tools = ToolRegistry.get_tools()
    if not tools:
        return False, "Hiçbir araç yüklenmedi"

    return True, f"{len(tools)} araç hazır"
