import importlib
import os
import pkgutil
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import app.tools as tools_pkg
from app.core.config import settings
from app.tools.registry import Category, ToolRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifecycle Events
    """
    # Startup: Clean temp directory
    # Sunucu her başladığında temp klasörünü temizle ki disk dolmasın
    if settings.TEMP_DIR.exists():
        shutil.rmtree(settings.TEMP_DIR)
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

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


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Dashboard showing all registered tools."""
    tools = ToolRegistry.get_tools()
    return templates.TemplateResponse(
        request=request, name="index.html", context={"tools": tools, "settings": settings}
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
        request=request, name="admin/stats.html", context={"stats": stats, "analytics": analytics}
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
