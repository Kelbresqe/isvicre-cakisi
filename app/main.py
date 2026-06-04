import importlib
import os
import pkgutil
import shutil
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.datastructures import URL, Headers
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import ENFORCE_DOMAIN_WILDCARD
from starlette.responses import PlainTextResponse, RedirectResponse
from starlette.types import ASGIApp, Receive, Scope, Send

import app.tools as tools_pkg
from app.core.config import settings
from app.core.health import get_health_status, is_ready
from app.tools.registry import Category, ToolRegistry

settings.validate_production_safety()


class IPv6AwareTrustedHostMiddleware:
    """Trusted host middleware that preserves bracketed IPv6 hosts."""

    def __init__(
        self,
        app: ASGIApp,
        allowed_hosts: list[str] | None = None,
        www_redirect: bool = True,
    ) -> None:
        if allowed_hosts is None:
            allowed_hosts = ["*"]

        for pattern in allowed_hosts:
            assert "*" not in pattern[1:], ENFORCE_DOMAIN_WILDCARD
            if pattern.startswith("*") and pattern != "*":
                assert pattern.startswith("*."), ENFORCE_DOMAIN_WILDCARD

        self.app = app
        self.allowed_hosts = list(allowed_hosts)
        self.allow_any = "*" in allowed_hosts
        self.www_redirect = www_redirect

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.allow_any or scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        host_header = headers.get("host", "")
        host = host_header.split(":")[0]
        if host_header.startswith("[") and "]" in host_header:
            host = host_header.split("]", 1)[0] + "]"

        is_valid_host = False
        found_www_redirect = False
        for pattern in self.allowed_hosts:
            if host == pattern or (
                pattern.startswith("*") and host.endswith(pattern[1:])
            ):
                is_valid_host = True
                break
            if "www." + host == pattern:
                found_www_redirect = True

        if is_valid_host:
            await self.app(scope, receive, send)
        elif found_www_redirect and self.www_redirect:
            url = URL(scope=scope)
            redirect_url = url.replace(netloc="www." + url.netloc)
            response = RedirectResponse(url=str(redirect_url))
            await response(scope, receive, send)
        else:
            response = PlainTextResponse("Invalid host header", status_code=400)
            await response(scope, receive, send)


def clean_directory_contents(path: Path) -> None:
    """Create a directory if needed and remove only its contents.

    Docker runs the app as a non-root user. Removing /app/temp itself requires
    write permission on /app, but removing files inside /app/temp only requires
    write permission on the temp directory. This keeps startup safe in both
    local and containerized environments.
    """
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifecycle Events
    """
    # Startup: Clean temp directory
    # Sunucu her başladığında temp klasörünü temizle ki disk dolmasın
    clean_directory_contents(settings.TEMP_DIR)

    # Warm up Redis connection at startup
    try:
        from app.core.redis_client import get_redis_client

        client = get_redis_client()
        if client:
            print("✅ Redis bağlantısı kuruldu")
        else:
            print("⚠️ Redis bağlantısı kurulamadı, in-memory cache kullanılacak")
    except Exception as e:
        print(f"⚠️ Redis warm-up hatası: {e}")

    yield

    # Shutdown events (if any)


# Initialize App with environment-aware configuration
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(IPv6AwareTrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def require_admin_token(request: Request) -> None:
    if settings.is_dev:
        return
    if not settings.ADMIN_API_KEY:
        raise HTTPException(status_code=404, detail="Not Found")
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or token != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


# Mount Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup Templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Add settings to Jinja2 globals for SEO (v0.7.0)
templates.env.globals["settings"] = settings


# --- TOOL REGISTRATION (AUTO-DISCOVERY) ---
def autodiscover_tools():
    """
    app/tools/ altındaki tüm klasörleri tarar ve 'router.py' modüllerini import eder.
    Bu sayede araçlar kendilerini ToolRegistry'ye otomatik olarak kaydeder.
    """
    package = tools_pkg
    prefix = package.__name__ + "."

    for _, name, is_pkg in pkgutil.iter_modules(package.__path__, prefix):
        if is_pkg:
            try:
                # Her aracın router.py dosyasını import etmeye çalış
                # Örn: app.tools.resim_cevirici.router
                importlib.import_module(f"{name}.router")
            except ImportError as e:
                # Eğer router.py yoksa veya hata varsa logla ama uygulamayı durdurma
                print(f"⚠️ Araç yüklenirken hata: {name} -> {e}")


autodiscover_tools()
# ------------------------------------------

# Mount Tool Routers
for router in ToolRegistry.get_routers():
    app.include_router(router)


# --- HEALTH CHECK ENDPOINTS (v0.9.0) ---
@app.get("/health", response_class=JSONResponse, tags=["Health"])
async def health_check():
    """
    Liveness probe endpoint.
    Returns comprehensive health status including all system checks.
    Used by container orchestration (Kubernetes, Docker) for liveness probes.
    """
    health = get_health_status()
    status_code = 200 if health.status == "healthy" else 503
    return JSONResponse(content=asdict(health), status_code=status_code)


@app.get("/ready", response_class=JSONResponse, tags=["Health"])
async def readiness_check(_: None = Depends(require_admin_token)):
    """
    Readiness probe endpoint.
    Returns whether the application is ready to serve traffic.
    Used by load balancers and container orchestration for traffic routing.
    """
    ready, reason = is_ready()
    status_code = 200 if ready else 503
    return JSONResponse(
        content={"ready": ready, "reason": reason, "version": settings.VERSION},
        status_code=status_code,
    )


# ------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Dashboard showing all registered tools."""
    tools = ToolRegistry.get_tools()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"tools": tools, "settings": settings},
    )


@app.get("/admin/stats", response_class=HTMLResponse)
async def admin_stats(request: Request):
    """Admin dashboard with statistics (v0.5.0) and analytics (v0.7.0)"""
    from app.core.observability import get_analytics_stats, get_stats

    # Only allow in dev environment
    if not settings.is_dev:
        raise HTTPException(status_code=404, detail="Not Found")

    stats = get_stats()
    analytics = get_analytics_stats()  # v0.7.0

    return templates.TemplateResponse(
        request=request,
        name="admin/stats.html",
        context={"stats": stats, "analytics": analytics},
    )


@app.get("/sitemap.xml", response_class=Response)
async def sitemap(request: Request):
    """Generate sitemap with category-based priorities (v0.7.0)"""
    from datetime import datetime

    base_url = str(request.base_url).rstrip("/")
    tools = ToolRegistry.get_tools()
    today = datetime.now().strftime("%Y-%m-%d")

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>"""

    # Category-based priorities
    category_priorities = {
        Category.IMAGE: 0.9,  # High priority - popular tools
        Category.OFFICE: 0.9,  # High priority - business use
        Category.DEV: 0.8,  # Medium-high - developer tools
        Category.SECURITY: 0.85,  # High - security critical
        Category.OTHER: 0.7,  # Medium - utility tools
    }

    for tool in tools:
        priority = category_priorities.get(tool.category, 0.7)
        xml_content += f"""
    <url>
        <loc>{base_url}/tools/{tool.slug}/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>{priority}</priority>
    </url>"""

    xml_content += "\n</urlset>"

    return Response(content=xml_content, media_type="application/xml")


@app.get("/metrics", response_class=Response, tags=["Monitoring"])
async def prometheus_metrics(_: None = Depends(require_admin_token)):
    """
    Prometheus metrics endpoint (v0.9.0).
    Exposes application metrics for Prometheus scraping.
    """
    from app.core.metrics import get_metrics, get_metrics_content_type

    return Response(content=get_metrics(), media_type=get_metrics_content_type())
