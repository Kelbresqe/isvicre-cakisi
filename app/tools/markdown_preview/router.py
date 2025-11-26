import time

import markdown
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from app.core.observability import log_tool_call
from app.core.rate_limit import rate_limit_dependency
from app.core.utils import get_tool_templates
from app.tools.registry import Category, ToolInfo, ToolRegistry

# 1. Router Tanımlama
router = APIRouter(
    prefix="/tools/markdown-preview",
    tags=["Markdown Preview"],
    dependencies=[Depends(rate_limit_dependency)],
)

# 2. Şablon Ayarları
templates = get_tool_templates(__file__)

# 3. Aracı Kaydetme (Registry)
tool_info = ToolInfo(
    slug="markdown-preview",
    title="Markdown Önizleme",
    category=Category.DEV,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path></svg>',
    image_url="/static/images/markdown_preview.png",
    description="Markdown metinlerinizi anında HTML'e dönüştürün ve önizleyin.",
    short_description="Canlı Markdown editörü ve önizleyici",
    detailed_description="GitHub Flavored Markdown destekli editör. Kod blokları, tablolar ve listeler için tam destek. Yazdıkça anlık önizleme.",
    seo_title="Online Markdown Editörü ve Önizleme - Markdown Preview | İsviçre Çakısı",
    seo_description="Ücretsiz online Markdown editörü. Markdown kodlarınızı HTML'e çevirin ve canlı önizleyin. Geliştiriciler ve yazarlar için ideal.",
    keywords="markdown editör, markdown preview, markdown html çevirici, online markdown",
    long_description="""İsviçre Çakısı Markdown Önizleme, README dosyaları, blog yazıları ve teknik dökümantasyon yazarken canlı olarak Markdown'ınızın nasıl görüneceğini sunar. GitHub Flavored Markdown (GFM) formatını destekler.

Araç, siz yazdıkça otomatik olarak HTML önizleme üretir. Kod blokları, tablolar, listeler, başlıklar ve bağlantılar gibi tüm Markdown elemanları doğru şekilde işlenir.

İki panel tasarımı ile sol tarafta yazarken sağ tarafta anlık sonucu görürsünüz. Bu sayede format hatalarını anında fark edebilir ve düzeltebilirsiniz.

Çıktı HTML kopyalama özelliği ile oluşturduğunuz içeriği doğrudan web sitenize veya CMS'inize yapıştırabilirsiniz. Dökümantasyon yazarları ve geliştiriciler için ideal.""",
    use_cases=[
        "GitHub README.md dosyalarını yazarken önizleme yapın",
        "Blog yazılarınızı markdown formatında hazırlayın ve HTML çıktısını alın",
        "Teknik dökümantasyon yazarken kod bloklarının düzgün göründüğünü kontrol edin",
        "Markdown öğrenirken syntax'ı test edin ve sonuçları görün",
        "Wiki içeriği hazırlarken format kontrol aracı olarak kullanın",
    ],
    faq=[
        {
            "question": "GitHub Flavored Markdown nedir?",
            "answer": "GFM, GitHub'ın kullandığı markdown formatıdır. Standart markdown'a ek olarak tablo, görev listesi (checkbox) ve kod bloğu syntax highlighting desteği sunar.",
        },
        {
            "question": "Hangi markdown elementleri destekleniyor?",
            "answer": "Başlıklar, paragraflar, listeler (ordered/unoderd), kod blokları, tablolar, bağlantılar, görüntüler, kalın/italic metin ve blockquote desteklenmektedir.",
        },
        {
            "question": "HTML çıktısı güvenli mi?",
            "answer": "Evet, Python markdown kütüphanesi kullanılarak güvenli HTML üretilir. Ancak çıktıyı kendi web sitenizde kullanırken mutlaka sanitize edin.",
        },
    ],
    # Tool capabilities
    accepts_files=False,
    accepts_text=True,
    max_upload_mb=None,
)

ToolRegistry.register(tool_info, router)


# 4. Endpointler
@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    # v0.7.0: Analytics tracking
    from app.core.observability import record_page_view

    record_page_view(
        "markdown-preview",
        request.headers.get("user-agent"),
        request.headers.get("referer"),
    )

    return templates.TemplateResponse(
        request=request, name="markdown_preview.html", context={"tool": tool_info}
    )


@router.post("/render", response_class=HTMLResponse)
async def render_markdown(
    request: Request,
    content: str = Form(""),
):
    start_time = time.time()
    try:
        if not content.strip():
            return ""

        # Render Markdown
        html = markdown.markdown(
            content, extensions=["fenced_code", "tables", "nl2br", "sane_lists"]
        )

        duration = (time.time() - start_time) * 1000
        log_tool_call("markdown-preview", "success", duration, {"length": len(content)})

        return f"""
        <div class="prose prose-invert max-w-none animate-fade-in">
            {html}
        </div>
        """
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        log_tool_call("markdown-preview", "error", duration, {"error": str(e)})

        return f"""
        <div class="bg-red-500/10 border border-red-500/50 rounded-xl p-4 animate-fade-in">
            <h3 class="text-red-500 font-bold mb-1">Hata</h3>
            <p class="text-red-300 text-sm">{str(e)}</p>
        </div>
        """
