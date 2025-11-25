import json
import time

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.core.observability import log_tool_call
from app.core.rate_limit import rate_limit_dependency
from app.core.utils import get_tool_templates
from app.tools.registry import Category, ToolInfo, ToolRegistry, ToolRelation

router = APIRouter(
    prefix="/tools/json-formatter", tags=["JSON Formatter"], dependencies=[Depends(rate_limit_dependency)]
)

templates = get_tool_templates(__file__)

tool_info = ToolInfo(
    slug="json-formatter",
    title="JSON Formatlayıcı",
    category=Category.DEV,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>',
    image_url="/static/images/json_formatter.png",
    description="JSON verilerinizi doğrulayın, güzelleştirin ve optimize edin.",
    short_description="JSON doğrulama, güzelleştirme, sıkıştırma",
    detailed_description="JSON verilerinizi doğrulayın ve okunabilir hale getirin. Karmaşık JSON yapılarını güzelleştirin veya yer kazanmak için sıkıştırın. Sözdizimi hataları otomatik tespit edilir. API geliştirme ve hata ayıklama için ideal.",
    seo_title="Ücretsiz Online JSON Formatlayıcı - Validator, Prettify, Minify | İsviçre Çakısı",
    seo_description="JSON verilerinizi doğrulayın, güzelleştirin veya sıkıştırın. Sözdizimi kontrolü, hata tespiti. Geliştiriciler için ücretsiz online araç.",
    keywords="json formatter, json validator, json prettify, json minify, online json tools, json doğrulama",
    long_description="""İsviçre Çakısı JSON Formatlayıcı, geliştiriciler için vazgeçilmez bir araçtır. API yanıtlarını okunaklı hale getirir, JSON verilerinizi doğrular ve otomatik olarak düzenler.

Araç, tek satır veya karışık JSON'ları anında güzelleştirir (prettify), girinti seviyelerini ayarlar ve syntax hatalarını tespit eder. Geçersiz JSON girişlerinde hangi satırda hata olduğunu gösterir.

Minify özelliği ile JSON'inizi sıkıştırarak API'lerde network transfer boyutunu azaltabilirsiniz. Escape/unescape fonksiyonları ile string içindeki özel karakterleri yönetebilirsiniz.

LRU cache sistemi sayesinde sık kullanılan JSON'lar anında işlenir. Büyük JSON dosyaları için optimization yapılmıştır.""",
    use_cases=[
        "API response'ları debug ederken JSON'u okunabilir formata getirin",
        "Frontend kodundan kopyaladığınız JSON'ı validation için kontrol edin",
        "Config dosyalarınızı düzgün formatlayarak kod kalitesini artırın",
        "Veritabanından çektiğiniz JSON verileri insan okuyabilir hale getirin",
        "CI/CD pipeline'ında JSON syntax kontrolü yapın",
    ],
    faq=[
        {
            "question": "Maksimum JSON boyutu ne kadar?",
            "answer": "1MB'a kadar JSON verisi işleyebilirsiniz. Daha büyük dosyalar için CLI araçları önerilir.",
        },
        {
            "question": "Syntax hatalarını gösteriyor mu?",
            "answer": "Evet, geçersiz JSON girişlerinde hata mesajı ve yaklaşık satır numarası gösterilir.",
        },
        {
            "question": "Minify ne işe yarar?",
            "answer": "JSON'ı tek satıra sıkıştırarak dosya boyutunu %30-40 azaltır, API transferlerinde hız kazandırır.",
        },
    ],
    # Tool capabilities
    accepts_files=False,
    accepts_text=True,
    max_upload_mb=settings.MAX_TEXT_INPUT_MB,
    suggested_next=[
        ToolRelation(
            slug="base64",
            relation_type="alternative",
            label="Base64 Encode/Decode",
            description="JSON'u base64 ile encode edin",
        ),
        ToolRelation(
            slug="url-encoder",
            relation_type="alternative",
            label="URL Encode",
            description="JSON'u URL parametresi olarak kullanın",
        ),
    ],
)

ToolRegistry.register(tool_info, router)


@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    # v0.7.0: Analytics tracking
    from app.core.observability import record_page_view

    record_page_view("json-formatter", request.headers.get("user-agent"), request.headers.get("referer"))

    return templates.TemplateResponse(request=request, name="formatter.html", context={"tool": tool_info})


@router.post("/format", response_class=HTMLResponse)
async def format_json(
    request: Request,
    json_input: str = Form(...),
    action: str = Form(...),  # "prettify" or "minify"
):
    from app.core.cache import get_cached_result, set_cached_result
    from app.core.rate_limit import rate_limit_dependency

    # Rate limiting applied
    await rate_limit_dependency(request)

    start_time = time.time()
    try:
        # Check cache first
        cached = get_cached_result("json-formatter", json_input, action=action)

        if cached:
            log_tool_call("json-formatter", "success", 0, {"action": action, "cached": True})
            return f"""
            <div class="bg-slate-900 rounded-lg border border-slate-700 overflow-hidden animate-fade-in">
                <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                    <span class="text-xs text-slate-400 font-mono">Sonuç (Cache)</span>
                    <button onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.innerText)" class="text-xs text-emerald-500 hover:text-emerald-400 transition-colors">
                        Kopyala
                    </button>
                </div>
                <pre class="p-4 text-sm text-emerald-300 font-mono overflow-x-auto whitespace-pre-wrap">{cached}</pre>
            </div>
            """

        # Process normally
        parsed = json.loads(json_input)

        if action == "prettify":
            result = json.dumps(parsed, indent=4, ensure_ascii=False)
        else:
            result = json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)

        # Cache the result
        set_cached_result("json-formatter", json_input, result, action=action)

        duration = (time.time() - start_time) * 1000
        log_tool_call("json-formatter", "success", duration, {"action": action, "size": len(json_input)})

        return f"""
        <div class="bg-slate-900 rounded-lg border border-slate-700 overflow-hidden animate-fade-in">
            <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                <span class="text-xs text-slate-400 font-mono">Sonuç</span>
                <button onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.innerText)" class="text-xs text-emerald-500 hover:text-emerald-400 transition-colors">
                    Kopyala
                </button>
            </div>
            <pre class="p-4 text-sm text-emerald-300 font-mono overflow-x-auto whitespace-pre-wrap">{result}</pre>
        </div>
        """
    except json.JSONDecodeError as e:
        duration = (time.time() - start_time) * 1000
        log_tool_call("json-formatter", "error", duration, {"error": str(e)})

        return f"""
        <div class="bg-red-500/10 border border-red-500/50 rounded-xl p-4 animate-fade-in">
            <h3 class="text-red-500 font-bold mb-1">Geçersiz JSON</h3>
            <p class="text-red-300 text-sm font-mono">Satır {e.lineno}, Sütun {e.colno}: {e.msg}</p>
        </div>
        """
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        log_tool_call("json-formatter", "error", duration, {"error": str(e)})
        return f"""
        <div class="bg-red-500/10 border border-red-500/50 rounded-xl p-4 animate-fade-in">
            <p class="text-red-300 text-sm">Beklenmeyen bir hata oluştu: {str(e)}</p>
        </div>
        """
