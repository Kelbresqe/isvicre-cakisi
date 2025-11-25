import os

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from app.core.config import settings
from app.core.rate_limit import rate_limit_dependency
from app.core.utils import get_random_tech_trivia, get_tool_templates
from app.tools.image_converter.utils import process_image
from app.tools.registry import Category, ToolInfo, ToolRegistry, ToolRelation

# 1. Router Tanımlama
router = APIRouter(
    prefix="/tools/image-converter",
    tags=["Image Converter"],
    dependencies=[Depends(rate_limit_dependency)],
)

# 2. Şablon Ayarları
templates = get_tool_templates(__file__)

# 3. Aracı Kaydetme (Registry)
# v0.8.0: Tool Graph & Pipeline configuration

tool_info = ToolInfo(
    slug="image-converter",
    title="Resim Dönüştürücü",
    category=Category.IMAGE,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>',
    image_url="/static/images/image_converter.png",
    description="Görüntü dosyalarınızı istediğiniz formata dönüştürün.",
    short_description="Resim formatı dönüştürme (JPG, PNG, WebP, vb.)",
    detailed_description="Resim dosyalarınızı JPG, PNG, WebP, GIF, TIFF, BMP ve ICO formatları arasında dönüştürün. Web için optimize edilmiş WebP formatına dönüşüm özelliği ile yükleme hızlarını artırın.",
    seo_title="Ücretsiz Online Resim Dönüştürücü - JPG, PNG, WebP | İsviçre Çakısı",
    seo_description="Resimlerinizi JPG, PNG, WebP gibi formatlara ücretsiz dönüştürün. EXIF verisi otomatik temizlenir. Hızlı ve güvenli online resim format dönüştürücü.",
    keywords="resim dönüştürücü, image converter, jpg png çevirici, webp converter, online resim format değiştirme",
    long_description="""İsviçre Çakısı Resim Dönüştürücü, görsel dosyalarınızı farklı formatlara dönüştürmenizi sağlayan güçlü ve kullanımı kolay bir araçtır. Web siteniz için WebP formatında daha hızlı yüklenen görseller oluşturabilir, sosyal medya için PNG transparanlığından faydalanabilir veya ofis belgeleri için JPG formatına geçebilirsiniz.

Araç, JPG/JPEG, PNG, WebP, GIF, TIFF, BMP ve ICO formatları arasında dönüşüm yapabilir. Dönüştürme sırasında EXIF verisini otomatik olarak temizler, böylece konum, cihaz modeli gibi hassas bilgiler görsel dosyasından çıkarılır.

Modern WebP formatı desteği ile web sitenizin performansını artırabilirsiniz. WebP, JPG ve PNG'ye göre %30-40 daha küçük dosya boyutu sunarken aynı görsel kaliteyi korur.

Maksimum dosya boyutu 10MB'dır ve işlem tamamen tarayıcınızda gerçekleşir, dosyalarınız sunucuya yüklenmez.""",
    use_cases=[
        "Web sitenizdeki görselleri WebP formatına çevirerek sayfa yükleme hızını %30-50 oranında artırın",
        "Sosyal medya için PNG logolarınızı transparent arkaplan ile kullanın",
        "Ofis belgelerine eklemek için TIFF dosyalarını JPG formatına dönüştürün",
        "E-posta ekleri için büyük PNG dosyalarını daha küçük JPG formatına geçirin",
        "EXIF verilerini temizleyerek fotoğraflarınızı gizlilik dostu hale getirin",
    ],
    faq=[
        {
            "question": "Hangi resim formatları destekleniyor?",
            "answer": "JPG/JPEG, PNG, WebP, GIF, TIFF, BMP ve ICO formatları desteklenmektedir.",
        },
        {
            "question": "EXIF verileri neden temizleniyor?",
            "answer": "EXIF verileri GPS konumu, cihaz modeli, çekim tarihi gibi hassas bilgileri içerebilir. Gizliliğinizi korumak için otomatik olarak temizliyoruz.",
        },
        {
            "question": "WebP formatı nedir ve neden kullanmalıyım?",
            "answer": "WebP, Google tarafından geliştirilen modern bir resim formatıdır. JPG ve PNG'ye göre %30-40 daha küçük dosya boyutu sunarken aynı kaliteyi korur. Web siteleri için idealdir.",
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
            slug="image-resizer",
            relation_type="next",
            label="Boyutlandır",
            description="Dönüştürdüğünüz görseli istediğiniz boyuta getirin",
        ),
        ToolRelation(
            slug="image-metadata",
            relation_type="next",
            label="Metadata İncele",
            description="EXIF verilerini detaylı inceleyin ve temizleyin",
        ),
    ],
)

ToolRegistry.register(tool_info, router)


# 4. Endpointler
@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    # v0.7.0: Analytics tracking
    from app.core.observability import record_page_view

    record_page_view("image-converter", request.headers.get("user-agent"), request.headers.get("referer"))

    return templates.TemplateResponse(request=request, name="converter.html", context={"tool": tool_info})


@router.post("/convert", response_class=HTMLResponse)
async def convert(
    request: Request,
    file: UploadFile | None = None,
    url: str | None = Form(None),
    target_format: str = Form(...),
    quality: int = Form(80),
    strip_exif: bool = Form(False),
):
    import time

    from app.core.observability import log_tool_call

    start_time = time.time()
    try:
        # process_image returns (output_path, output_filename, new_size, original_size)
        output_path, filename, new_size, original_size = await process_image(
            file=file,
            url=url,
            target_format=target_format,
            quality=quality,
            strip_exif=strip_exif,
        )

        duration = (time.time() - start_time) * 1000
        log_tool_call(
            "image-converter",
            "success",
            duration,
            {"size": original_size, "format": target_format},
        )

        # Tasarruf hesapla
        savings = original_size - new_size
        savings_percent = (savings / original_size) * 100 if original_size > 0 else 0

        # v0.8.0: Pipeline production
        if tool_info.produces_pipeline_files:
            from app.core.pipeline import create_pipeline_file

            try:
                create_pipeline_file(
                    source_tool_slug="image-converter",
                    input_file_path=output_path,
                    mime_type=f"image/{target_format.lower()}",
                    original_name=filename,
                )
            except Exception:
                pass  # Pipeline creation is optional, don't break main flow

        # Trivia
        trivia = get_random_tech_trivia()

        # Dosya boyutu formatlama
        def fmt_size(size):
            for unit in ["B", "KB", "MB", "GB"]:
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024
            return f"{size:.2f} GB"

        return templates.TemplateResponse(
            request=request,
            name="partials/success.html",
            context={
                "filename": filename,
                "original_size_fmt": fmt_size(original_size),
                "new_size_fmt": fmt_size(new_size),
                "savings_percent": f"{savings_percent:.1f}",
                "output_filename": os.path.basename(output_path),
                "trivia": trivia,
            },
        )
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        log_tool_call("image-converter", "error", duration, {"error": str(e)})

        # Hata mesajını HTML olarak döndür
        error_msg = str(e.detail) if hasattr(e, "detail") else str(e)
        status_code = e.status_code if hasattr(e, "status_code") else 400

        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={"error_msg": error_msg},
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
