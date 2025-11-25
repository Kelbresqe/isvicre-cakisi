import base64
import io
import time

import qrcode
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from app.core.observability import log_tool_call
from app.core.rate_limit import rate_limit_dependency
from app.core.utils import get_tool_templates
from app.tools.registry import Category, ToolInfo, ToolRegistry

# 1. Router Tanımlama
router = APIRouter(
    prefix="/tools/qr-code",
    tags=["QR Code Generator"],
    dependencies=[Depends(rate_limit_dependency)],
)

# 2. Şablon Ayarları
templates = get_tool_templates(__file__)

# 3. Aracı Kaydetme (Registry)
tool_info = ToolInfo(
    slug="qr-code",
    title="QR Kod Oluşturucu",
    category=Category.OTHER,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"></path></svg>',
    image_url="/static/images/qr_code.png",
    description="Metin veya URL'leriniz için özelleştirilebilir QR kodlar oluşturun.",
    short_description="Hızlı ve özelleştirilebilir QR kod üretimi",
    detailed_description="URL, metin, e-posta veya Wi-Fi bilgileri için yüksek kaliteli QR kodlar oluş ururun. Renk, boyut ve hata düzeltme seviyesini ayarlayabilirsiniz. PNG formatında indirin.",
    seo_title="Ücretsiz Online QR Kod Oluşturucu - QR Code Generator | İsviçre Çakısı",
    seo_description="Ücretsiz ve sınırsız QR kod oluşturma aracı. URL, metin, vCard için QR kod üretin. Renkli ve logolu QR kod yapma.",
    keywords="qr kod oluşturucu, qr code generator, karekod yapma, online qr kod, ücretsiz qr code",
    long_description="""İsviçre Çakısı QR Kod Oluşturucu, web siteniz, blog yazısı, kartvizit veya ürün paketlemeniz için profesyonel QR kodlar oluşturmanızı sağlar. Herhangi bir metin, URL, e-posta adresi veya Wi-Fi bilgisini QR kod formatına dönüştürebilirsiniz.

Araç, Python qrcode kütüphanesi kullanarak yüksek kaliteli ve taranabilir QR kodlar üretir. 4 farklı hata düzeltme seviyesi sayesinde bozulmuş veya kirli yüzeylerde bile okunabilir kodlar oluşturabilirsiniz.

Renk özelleştirmesi ile markanıza uygun QR kodlar tasarlayın. Boyut ve kenarlık ayarları ile baskı veya dijital kullanım için optimize edilmiş çıktılar alın.

Oluşturulan QR kodlar PNG formatında yüksek çözünürlükte indirilir ve herhangi bir kamera veya QR okuyucu ile taranabilir.""",
    use_cases=[
        "Restoranızdaki menüyü QR kodla dijitalleştirin, müşteriler telefonda görüntülesin",
        "Kartvizitinize QR kod ekleyerek iletişim bilgilerinizi paylaşın",
        "Etkinlik davetiyelerinde kayıt formuna yönlendiren QR kod kullanın",
        "Ürün paketlerinde garanti ve kullanım kılavuzuna QR kodla erişim sağlayın",
        "Wi-Fi şifresini QR koduyla paylaşarak konuklarınızın bağlanmasını kolaylaştırın",
    ],
    faq=[
        {
            "question": "Hangi veri türleri için QR kod oluşturabilirim?",
            "answer": "URL, düz metin, e-posta adresi, telefon numarası, SMS, Wi-Fi bilgileri ve vCard (kartvizit) formatları desteklenmektedir.",
        },
        {
            "question": "Hata düzeltme seviyesi ne demek?",
            "answer": "L (Düşük) %7, M (Orta) %15, Q (Yüksek) %25, H (Çok Yüksek) %30 oranında hasara dayanıklıdır. Baskılı QR kodlar için H seviyesi önerilir.",
        },
        {
            "question": "Oluşturduğum QR kod kalıcı mı?",
            "answer": "Evet, QR kod içindeki veri sabittir. Ancak içinde URL varsa o siteyi siz kontrol ediyorsanız içeriği değiştirebilirsiniz.",
        },
    ],
    # Tool capabilities
    accepts_files=False,
    accepts_text=True,
    max_upload_mb=None,
    # v0.8.0: Pipeline capabilities
    produces_pipeline_files=True,
)

ToolRegistry.register(tool_info, router)


# 4. Endpointler
@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    # v0.7.0: Analytics tracking
    from app.core.observability import record_page_view

    record_page_view("qr-code", request.headers.get("user-agent"), request.headers.get("referer"))

    return templates.TemplateResponse(request=request, name="qr_code.html", context={"tool": tool_info})


@router.post("/generate", response_class=HTMLResponse)
async def generate_qr(
    request: Request,
    content: str = Form(...),
    size: int = Form(10),  # Box size (pixel multiplier)
    border: int = Form(4),
    fill_color: str = Form("black"),
    back_color: str = Form("white"),
    error_correction: str = Form("M"),  # L, M, Q, H
):
    start_time = time.time()
    try:
        # Map error correction level
        ec_map = {
            "L": qrcode.constants.ERROR_CORRECT_L,
            "M": qrcode.constants.ERROR_CORRECT_M,
            "Q": qrcode.constants.ERROR_CORRECT_Q,
            "H": qrcode.constants.ERROR_CORRECT_H,
        }

        qr = qrcode.QRCode(
            version=None,  # Auto-detect
            error_correction=ec_map.get(error_correction, qrcode.constants.ERROR_CORRECT_M),
            box_size=max(1, min(size, 20)),  # Limit size
            border=max(0, min(border, 10)),
        )

        qr.add_data(content)
        qr.make(fit=True)

        img = qr.make_image(fill_color=fill_color, back_color=back_color)

        # Convert to base64 for display
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        duration = (time.time() - start_time) * 1000
        log_tool_call("qr-code", "success", duration, {"size": len(content)})

        return f"""
        <div class="bg-slate-800/50 rounded-2xl p-8 border border-slate-700/50 shadow-xl text-center animate-fade-in">
            <div class="inline-block bg-white p-4 rounded-xl mb-6">
                <img src="data:image/png;base64,{img_str}" alt="QR Code" class="max-w-full h-auto shadow-lg">
            </div>
            
            <div class="flex justify-center gap-4">
                <a href="data:image/png;base64,{img_str}" download="qrcode.png" 
                   class="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold transition-all shadow-lg shadow-emerald-900/20 flex items-center gap-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                    PNG İndir
                </a>
            </div>
        </div>
        """
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        log_tool_call("qr-code", "error", duration, {"error": str(e)})

        return f"""
        <div class="bg-red-500/10 border border-red-500/50 rounded-xl p-4 animate-fade-in">
            <h3 class="text-red-500 font-bold mb-1">Hata</h3>
            <p class="text-red-300 text-sm">{str(e)}</p>
        </div>
        """
