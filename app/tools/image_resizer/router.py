import os

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from PIL import Image

from app.core.config import settings
from app.core.image_utils import save_image
from app.core.rate_limit import rate_limit_dependency
from app.core.upload import validate_and_load_image
from app.core.utils import get_random_tech_trivia
from app.tools.registry import Category, ToolInfo, ToolRegistry, ToolRelation

# 1. Router Tanımlama
router = APIRouter(
    prefix="/tools/image-resizer",
    tags=["Image Resizer"],
    dependencies=[Depends(rate_limit_dependency)],
)

# 2. Şablon Ayarları
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(
    directory=[
        os.path.join(TOOL_DIR, "templates"),
        os.path.join(settings.BASE_DIR, "app", "templates"),
    ]
)

# 3. Aracı Kaydetme (Registry)
tool_info = ToolInfo(
    slug="image-resizer",
    title="Resim Boyutlandırıcı",
    category=Category.IMAGE,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>',
    image_url="/static/images/image_resizer.png",
    description="Resimlerinizi piksel veya yüzde bazında yeniden boyutlandırın.",
    short_description="Piksel veya yüzde ile boyutlandırma",
    detailed_description="Resimlerinizi istediğiniz boyutlara getirin. Piksel cinsinden tam boyut veya yüzde oranı belirleyerek boyutlandırma yapabilirsiniz. En-boy oranı koruma özelliği ile profesyonel sonuçlar alın. Web için optimize edilmiş çıktılar.",
    seo_title="Ücretsiz Online Resim Boyutlandırıcı - Fotoğraf Küçültme | İsviçre Çakısı",
    seo_description="Resimlerinizi online olarak ücretsiz boyutlandırın. Piksel veya yüzde bazında küçültme, büyütme işlemleri. Kalite kaybı olmadan fotoğraf boyutlandırma aracı.",
    keywords="resim boyutlandırıcı, fotoğraf küçültme, online image resizer, resim ölçekleme, görsel boyutlandırma, ücretsiz resim aracı",
    long_description="""İsviçre Çakısı Resim Boyutlandırıcı, görsellerinizi ihtiyacınıza göre küçültme veya büyütme işlemi yapmanızı sağlar. Web siteniz için optimize edilmiş boyutlarda resimler oluşturabilir, sosyal medya platformlarının  gereksinimlerine uygun görseller hazırlayabilir veya e-posta ekleri için dosya boyutunu azaltabilirsiniz.

Araç, en-boy oranını koruyarak bozulma olmadan yeniden boyutlandırma yapar. İster piksel cinsinden kesin değerler verin, ister yüzde oranı kullanarak ölçeklendirin - sonuç her zaman profesyoneldir.

Yüksek kaliteli yeniden örnekleme algoritmaları sayesinde büyütme işlemlerinde bile kabul edilebilir sonuçlar alırsınız. Küçültme işlemlerinde ise detay korunarak dosya boyutu optimize edilir.

Modern web standartlarına uygun çıktı üretir ve tüm popüler tarayıcılarda sorunsuz çalışır.""",
    use_cases=[
        "Web siteniz için görselleri 1920x1080 gibi standart boyutlara getirerek performansı artırın",
        "Instagram için kare (1080x1080) veya dikey (1080x1350) formatında görseller hazırlayın",
        "E-posta eklerinde dosya boyutunu küçülterek gönderim sorunlarını önleyin",
        "Profil fotoğraflarınızı 200x200 gibi standart boyutlara getirin",
        "Ürün kataloğunuz için tüm görselleri aynı boyutta standartlaştırın",
    ],
    faq=[
        {
            "question": "En-boy oranı koruması ne demek?",
            "answer": "Bu özellik etkinken resim bozulmadan yeniden boyutlandırılır. Sadece genişlik veya yükseklikten birini verirseniz, diğeri otomatik hesaplanır.",
        },
        {
            "question": "Maksimum boyutlandırma oranı nedir?",
            "answer": "İstediğiniz boyuta getirebilirsiniz ancak orijinal boyutun 4 katından fazla büyütme kalite kaybına yol açabilir.",
        },
        {
            "question": "Hangi resim formatları destekleniyor?",
            "answer": "JPG, PNG, WebP, GIF, BMP, TIFF ve ICO formatları desteklenmektedir.",
        },
    ],
    # Tool capabilities
    accepts_files=True,
    accepts_text=False,
    max_upload_mb=settings.MAX_IMAGE_SIZE_MB,
    # v0.8.0: Pipeline capabilities
    accepts_pipeline_files=True,
    produces_pipeline_files=True,
    suggested_next=[
        ToolRelation(
            slug="image-metadata",
            relation_type="next",
            label="Metadata İncele",
            description="Boyutlandırdığınız görselin metadatasını kontrol edin",
        ),
        ToolRelation(
            slug="image-cropper", relation_type="next", label="Kırp", description="Görseli istediğiniz alana kırpın"
        ),
    ],
)

ToolRegistry.register(tool_info, router)


# 4. Endpointler
@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    # v0.7.0: Analytics tracking
    from app.core.observability import record_page_view

    record_page_view("image-resizer", request.headers.get("user-agent"), request.headers.get("referer"))

    return templates.TemplateResponse(request=request, name="resizer.html", context={"tool": tool_info})


@router.post("/resize", response_class=HTMLResponse)
async def resize(
    request: Request,
    file: UploadFile | None = None,
    url: str | None = Form(None),
    width: str | None = Form(None),
    height: str | None = Form(None),
    scale: str | None = Form(None),
):
    import time

    from app.core.observability import log_tool_call

    start_time = time.time()
    try:
        # 1. Yükle (Common Pipeline)
        if url:
            raise HTTPException(status_code=400, detail="URL'den yükleme şu an devre dışı.")

        img, filename, original_size = await validate_and_load_image(file)

        # Parse inputs (handle empty strings)
        w_int = int(width) if width and width.strip() else None
        h_int = int(height) if height and height.strip() else None
        s_int = int(scale) if scale and scale.strip() else None

        # 2. Boyutlandırma Mantığı
        orig_w, orig_h = img.size
        new_w, new_h = orig_w, orig_h

        if s_int:
            ratio = s_int / 100.0
            new_w = int(orig_w * ratio)
            new_h = int(orig_h * ratio)
        elif w_int and h_int:
            new_w, new_h = w_int, h_int
        elif w_int:
            ratio = w_int / orig_w
            new_w = w_int
            new_h = int(orig_h * ratio)
        elif h_int:
            ratio = h_int / orig_h
            new_h = h_int
            new_w = int(orig_w * ratio)

        # Minimum boyut kontrolü
        new_w = max(1, new_w)
        new_h = max(1, new_h)

        # Resize
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 3. Kaydet
        # Orijinal formatı korumaya çalış, yoksa JPEG
        fmt = img.format or "JPEG"
        if fmt == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        output_path, output_filename, new_size = save_image(img, filename, fmt)

        # v0.8.0: Pipeline production
        pipeline_id = None
        if tool_info.produces_pipeline_files:
            from app.core.pipeline import create_pipeline_file

            try:
                pipeline_id = create_pipeline_file(
                    source_tool_slug="image-resizer",
                    input_file_path=output_path,
                    mime_type=f"image/{fmt.lower()}",
                    original_name=output_filename,
                )
            except Exception:
                pass

        # Trivia
        trivia = get_random_tech_trivia()

        # Boyut formatlama
        def fmt_size(size):
            for unit in ["B", "KB", "MB", "GB"]:
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024
            return f"{size:.2f} GB"

        return f"""
        <div class="bg-emerald-500/10 border border-emerald-500/50 rounded-xl p-6 animate-fade-in">
            <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-3">
                    <div class="p-2 bg-emerald-500 rounded-lg text-white">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                    </div>
                    <div>
                        <h3 class="text-lg font-bold text-white">İşlem Başarılı!</h3>
                        <p class="text-emerald-400 text-sm">{filename}</p>
                    </div>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4 mb-6">
                <div class="bg-slate-900/50 p-3 rounded-lg">
                    <div class="text-xs text-slate-500 mb-1">Orijinal Boyut</div>
                    <div class="text-slate-300 font-mono">{orig_w}x{orig_h} px</div>
                    <div class="text-slate-500 text-xs mt-1">{fmt_size(original_size)}</div>
                </div>
                <div class="bg-slate-900/50 p-3 rounded-lg border border-emerald-500/30">
                    <div class="text-xs text-emerald-500 mb-1">Yeni Boyut</div>
                    <div class="text-white font-mono">{new_w}x{new_h} px</div>
                    <div class="text-emerald-500/70 text-xs mt-1">{fmt_size(new_size)}</div>
                </div>
            </div>
            
            <div class="flex flex-col gap-4">
                <div class="flex items-center justify-end">
                    <a href="/tools/image-resizer/download/{os.path.basename(output_path)}" 
                       hx-boost="false"
                       class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                        İndir
                    </a>
                </div>
                
                <div class="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50 text-xs text-slate-400 flex gap-2 items-start">
                    <span class="text-lg">💡</span>
                    <div>
                        <span class="font-bold text-slate-300">Biliyor muydun?</span>
                        <p>{trivia}</p>
                    </div>
                </div>
            </div>
        </div>
        """
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        log_tool_call("image-resizer", "error", duration, {"error": str(e)})

        error_msg = str(e.detail) if hasattr(e, "detail") else str(e)
        status_code = e.status_code if hasattr(e, "status_code") else 400

        return HTMLResponse(
            content=f"""
        <div class="bg-red-500/10 border border-red-500/50 rounded-xl p-4 animate-fade-in flex items-start gap-3">
            <div class="p-2 bg-red-500/20 rounded-lg text-red-500 shrink-0">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
            </div>
            <div>
                <h3 class="text-lg font-bold text-white mb-1">Hata Oluştu</h3>
                <p class="text-red-200 text-sm">{error_msg}</p>
            </div>
        </div>
        """,
            status_code=status_code,
        )


@router.get("/download/{filename}")
async def download(filename: str, background_tasks: BackgroundTasks):
    from app.core.config import settings

    file_path = settings.TEMP_DIR / filename

    if not file_path.exists():
        return HTMLResponse("Dosya bulunamadı veya süresi doldu.", status_code=404)

    # Dosyayı gönderdikten sonra sil
    background_tasks.add_task(os.remove, file_path)

    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")
