import base64
import os
import time

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.observability import log_tool_call
from app.tools.registry import Category, ToolInfo, ToolRegistry, ToolRelation

router = APIRouter(prefix="/tools/base64", tags=["Base64 Tool"])

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(
    directory=[
        os.path.join(TOOL_DIR, "templates"),
        os.path.join(settings.BASE_DIR, "app", "templates"),
    ]
)

tool_info = ToolInfo(
    slug="base64",
    title="Base64 Dönüştürücü",
    category=Category.DEV,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path></svg>',
    image_url="/static/images/base64.png",
    description="Metinlerinizi Base64 formatına kodlayın veya çözün.",
    short_description="Text to Base64 encode/decode",
    detailed_description="Metinlerinizi Base64 formatına kodlayın veya Base64 kodlarını tekrar metne çevirin. Email, API entegrasyonu ve veri aktarımı için kullanışlı. Güvenli ve hızlı dönüşüm işlemi.",
    seo_title="Ücretsiz Online Base64 Dönüştürücü - Encode & Decode | İsviçre Çakısı",
    seo_description="Metinlerinizi Base64 formatına çevirin veya Base64 kodlarını metne dönüştürün. Geliştiriciler için ücretsiz, hızlı ve güvenli Base64 aracı.",
    keywords="base64 dönüştürücü, base64 encoder, base64 decoder, base64 çeviri, online base64 tool, metin şifreleme",
    long_description="""İsviçre Çakısı Base64 Dönüştürücü, metinlerinizi ve dosyalarınızı Base64 formatına kodlar veya Base64 stringlerini orijinal haline çevirir. Web geliştirme, API entegrasyonları ve veri transferi için vazgeçilmez bir araçtır.

Hem metin bazlı (encode/decode) hem de dosya bazlı dönüşümler yapabilirsiniz. Görsel dosyalarınızı Base64 Data URI'ye çevirerek inline CSS/HTML'de kullanabilir, API'lerde binary veri transfer edebilirsiniz.

UTF-8 encoding desteği ile Türkçe karakterler sorunsuz işlenir. Output kopyalama özelliği ile sonucu tek tıkla kullanıma hazır hale getirebilirsiniz.

Geliştiriciler için debugging, frontend developers için data URI oluşturma, backend developers için token encoding işlemlerinde kullanılır.""",
    use_cases=[
        "API Bearer token'ları Base64 encode ederek güvenlik katmanı ekleyin",
        "Küçük ikonları Base64 Data URI olarak CSS'e gömün ve HTTP request sayısını azaltın",
        "Email sistemlerinde binary attachment'ları Base64 ile kodlayın",
        "Basic Authentication header'ları oluşturun",
        "QR kod verilerini Base64 formatına çevirin",
    ],
    faq=[
        {
            "question": "Base64 nedir ve ne işe yarar?",
            "answer": "Base64, binary verileri ASCII metin formatına çeviren bir encoding şemasıdır. Email, URL ve JSON gibi sadece metin kabul eden sistemlerde binary veri taşımak için kullanılır.",
        },
        {
            "question": "Dosya boyutu limiti var mı?",
            "answer": "Base64 encoding işlemi dosya boyutunu ~33% artırır. Maksimum 1MB dosya yükleyebilirsiniz.",
        },
        {
            "question": "Türkçe karakterler destekleniyor mu?",
            "answer": "Evet, UTF-8 encoding kullanılarak tüm Türkçe karakterler doğru şekilde işlenir.",
        },
    ],
    # Tool capabilities
    accepts_files=False,
    accepts_text=True,
    max_upload_mb=settings.MAX_TEXT_INPUT_MB,
    suggested_next=[
        ToolRelation(
            slug="json-formatter",
            relation_type="alternative",
            label="JSON Format",
            description="Decode sonucunu JSON olarak formatlayın",
        ),
    ],
)

ToolRegistry.register(tool_info, router)


@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    # v0.7.0: Analytics tracking
    from app.core.observability import record_page_view

    record_page_view("base64", request.headers.get("user-agent"), request.headers.get("referer"))

    return templates.TemplateResponse(request=request, name="base64.html", context={"tool": tool_info})


@router.post("/convert", response_class=HTMLResponse)
async def convert_base64(
    request: Request,
    text_input: str = Form(...),
    action: str = Form(...),  # "encode" or "decode"
):
    from app.core.cache import get_cached_result, set_cached_result
    from app.core.rate_limit import rate_limit_dependency

    # Rate limiting
    await rate_limit_dependency(request)

    start_time = time.time()
    try:
        # Check cache
        cached = get_cached_result("base64", text_input, action=action)
        if cached:
            log_tool_call("base64", "success", 0, {"action": action, "cached": True})
            return f"""
            <div class="bg-slate-900 rounded-lg border border-slate-700 overflow-hidden animate-fade-in">
                <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                    <span class="text-xs text-slate-400 font-mono">Sonuç (Cache)</span>
                    <button onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.innerText)" class="text-xs text-emerald-500 hover:text-emerald-400 transition-colors">
                        Kopyala
                    </button>
                </div>
                <pre class="p-4 text-sm text-emerald-300 font-mono overflow-x-auto whitespace-pre-wrap break-all">{cached}</pre>
            </div>
            """

        if action == "encode":
            result = base64.b64encode(text_input.encode("utf-8")).decode("utf-8")
        else:
            result = base64.b64decode(text_input).decode("utf-8")

        # Set cache
        set_cached_result("base64", text_input, result, action=action)

        duration = (time.time() - start_time) * 1000
        log_tool_call("base64", "success", duration, {"action": action, "size": len(text_input)})

        return f"""
        <div class="bg-slate-900 rounded-lg border border-slate-700 overflow-hidden animate-fade-in">
            <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                <span class="text-xs text-slate-400 font-mono">Sonuç</span>
                <button onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.innerText)" class="text-xs text-emerald-500 hover:text-emerald-400 transition-colors">
                    Kopyala
                </button>
            </div>
            <pre class="p-4 text-sm text-emerald-300 font-mono overflow-x-auto whitespace-pre-wrap break-all">{result}</pre>
        </div>
        """
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        log_tool_call("base64", "error", duration, {"error": str(e)})

        return f"""
        <div class="bg-red-500/10 border border-red-500/50 rounded-xl p-4 animate-fade-in">
            <h3 class="text-red-500 font-bold mb-1">Hata</h3>
            <p class="text-red-300 text-sm font-mono">{str(e)}</p>
        </div>
        """
