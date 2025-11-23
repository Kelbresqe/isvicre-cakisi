import os
import time
import urllib.parse

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.observability import log_tool_call
from app.tools.registry import Category, ToolInfo, ToolRegistry, ToolRelation

router = APIRouter(prefix="/tools/url-encoder", tags=["URL Tool"])

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(
    directory=[
        os.path.join(TOOL_DIR, "templates"),
        os.path.join(settings.BASE_DIR, "app", "templates"),
    ]
)

tool_info = ToolInfo(
    slug="url-encoder",
    title="URL Kodlayıcı/Çözücü",
    category=Category.DEV,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>',
    image_url="/static/images/url_tool.png",
    description="URL'leri güvenli formatlara kodlayın veya çözün.",
    short_description="URL encode/decode, özel karakter dönüşümü",
    detailed_description="URL'lerinizi web için güvenli formatlara kodlayın veya kodlanmış URL'leri çözün. Akıllı algılama ile tam URL'lerde sadece gerekli kısımlar kodlanır. Query parametreleri ve özel karakterler için idealdir.",
    seo_title="Ücretsiz URL Encoder/Decoder - Online URL Çevirici | İsviçre Çakısı",
    seo_description="URL'lerinizi encode (kodlama) veya decode (çözme) işlemi yapın. Web geliştiriciler için ücretsiz, hızlı ve güvenli URL dönüştürme aracı.",
    keywords="url encoder, url decoder, url kodlama, url çözme, online url tool, url encode decode",
    long_description="""İsviçre Çakısı URL Kodlayıcı/Çözücü, web adreslerinizi güvenli formatlara dönüştürür veya kodlanmış URL'leri orijinal haline çevirir. Web geliştiriciler, SEO uzmanları ve sistem yöneticileri için vazgeçilmez bir araçtır.

URL encoding, özel karakterleri (Türkçe harfler, boşluklar, semboller) web tarayıcılarının anlayabileceği %XX formatına çevirir. Bu, URL'lerin doğru çalışması ve veri transferinin güvenli olması için gereklidir.

Araç akıllı algılama özelliğine sahiptir - tam bir URL girdiğinizde sadece query string ve path parametrelerini kodlar, protocol ve domain kısımlarına dokunmaz.

LRU cache sistemi sayesinde sık kullanılan dönüşümler anında gerçekleşir. Batch işlem desteği ile birden fazla URL'yi aynı anda işleyebilirsiniz.""",
    use_cases=[
        "API endpoint'lerine Türkçe parametreler gönderirken karakterleri encode edin",
        "Email içindeki tıklanabilir linkleri düzgün formatlayın",
        "Google Analytics UTM parametrelerini doğru şekilde kodlayın",
        "Redirect URL'lerini web sunucusuna göndermeden önce encode edin",
        "Log dosyalarındaki kodlanmış URL'leri okunabilir hale getirin",
    ],
    faq=[
        {
            "question": "URL encoding ne zaman gereklidir?",
            "answer": "URL'de Türkçe karakter, boşluk veya özel semboller varsa encoding gereklidir. Örneğin 'merhaba dünya' → 'merhaba%20d%C3%BCnya' olur.",
        },
        {
            "question": "Hangi karakterler encode edilir?",
            "answer": "Boşluk, Türkçe karakterler (ç, ğ, ı, ö, ş, ü), ve özel semboller (&, =, ?, #, vb.) encode edilir. a-z, A-Z, 0-9 ve bazı güvenli karakterler (-_.~) encode edilmez.",
        },
        {
            "question": "Double encoding problemi nedir?",
            "answer": "Zaten kodlanmış bir URL'yi tekrar kodlarsanız bozulur. Aracımız bunu otomatik algılar ve uyarı verir.",
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
            description="URL parametrelerini JSON olarak görüntüleyin",
        ),
    ],
)

ToolRegistry.register(tool_info, router)


@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    # v0.7.0: Analytics tracking
    from app.core.observability import record_page_view

    record_page_view("url-encoder", request.headers.get("user-agent"), request.headers.get("referer"))

    return templates.TemplateResponse(request=request, name="url_tool.html", context={"tool": tool_info})


@router.post("/convert", response_class=HTMLResponse)
async def convert_url(
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
        cached = get_cached_result("url-encoder", text_input, action=action)
        if cached:
            log_tool_call("url-encoder", "success", 0, {"action": action, "cached": True})
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
            # Smart encoding: detect if already encoded to prevent double-encoding
            # Strategy: Try to decode first. If it changes, it was already encoded.
            try_decoded = urllib.parse.unquote(text_input)
            is_already_encoded = try_decoded != text_input

            # If already encoded, use the decoded version as starting point
            work_text = try_decoded if is_already_encoded else text_input

            # Detect if input is a full URL or just a fragment
            parsed = urllib.parse.urlparse(work_text)
            if parsed.scheme and parsed.netloc:
                # It's a full URL - encode only path, query, and fragment
                # Use more comprehensive safe characters for URLs
                encoded_path = urllib.parse.quote(parsed.path, safe="/")
                # For query strings, preserve common safe characters
                encoded_query = urllib.parse.quote(parsed.query, safe="=&+-_.~")
                encoded_fragment = urllib.parse.quote(parsed.fragment, safe="")

                result = urllib.parse.urlunparse(
                    (parsed.scheme, parsed.netloc, encoded_path, parsed.params, encoded_query, encoded_fragment)
                )
            else:
                # Just a fragment or text - encode everything except URL-safe chars
                result = urllib.parse.quote(work_text, safe="")
        else:
            # Decode: apply unquote
            parsed = urllib.parse.urlparse(text_input)
            if parsed.scheme and parsed.netloc:
                # It's a full URL - decode only path, query, and fragment
                decoded_path = urllib.parse.unquote(parsed.path)
                decoded_query = urllib.parse.unquote(parsed.query)
                decoded_fragment = urllib.parse.unquote(parsed.fragment)

                result = urllib.parse.urlunparse(
                    (parsed.scheme, parsed.netloc, decoded_path, parsed.params, decoded_query, decoded_fragment)
                )
            else:
                # Just a fragment - decode everything
                result = urllib.parse.unquote(text_input)

        # Set cache
        set_cached_result("url-encoder", text_input, result, action=action)

        duration = (time.time() - start_time) * 1000
        log_tool_call("url-encoder", "success", duration, {"action": action, "size": len(text_input)})

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
        log_tool_call("url-encoder", "error", duration, {"error": str(e)})

        return f"""
        <div class="bg-red-500/10 border border-red-500/50 rounded-xl p-4 animate-fade-in">
            <h3 class="text-red-500 font-bold mb-1">Hata</h3>
            <p class="text-red-300 text-sm font-mono">{str(e)}</p>
        </div>
        """
