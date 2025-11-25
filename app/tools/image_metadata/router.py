import os
import time
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from PIL import Image
from PIL.ExifTags import TAGS

from app.core.config import settings
from app.core.rate_limit import rate_limit_dependency
from app.core.utils import get_tool_templates
from app.tools.registry import Category, ToolInfo, ToolRegistry, ToolRelation

# Router
router = APIRouter(
    prefix="/tools/image-metadata",
    tags=["Image Metadata"],
    dependencies=[Depends(rate_limit_dependency)],
)

# Templates
templates = get_tool_templates(__file__)

# Tool Registration
tool_info = ToolInfo(
    slug="image-metadata",
    title="Resim Metadata İnceleyici",
    category=Category.IMAGE,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
    image_url="/static/images/metadata.png",
    description="Resimlerinizin EXIF metadata bilgilerini görüntüleyin ve temizleyin.",
    short_description="EXIF görüntüleme ve temizleme",
    detailed_description="Resimlerinizin içindeki EXIF, GPS ve kamera bilgilerini detaylı inceyin. Gizlilik için tüm metadata'yı tek tıkla temizleyin.",
    seo_title="Ücretsiz Resim EXIF Metadata Görüntüleme ve Temizleme | İsviçre Çakısı",
    seo_description="Fotoğraflarınızın EXIF metadata bilgilerini görüntüleyin, GPS konumu ve kamera bilgilerini kontrol edin. Gizlilik için metadata temizleyin.",
    keywords="exif görüntüleyici, metadata temizleme, gps bilgisi silme, fotoğraf bilgileri, exif cleaner",
    long_description="""Resim Metadata İnceleyici ile fotoğraflarınızın içindeki gizli bilgileri keşfedin ve kontrol edin. Her dijital fotoğraf, çekim anındaki kamera ayarları, GPS konumu, tarih-saat ve daha fazla bilgiyi EXIF formatında saklar.

Bu araç ile hangi bilgilerin paylaşıldığını görebilir ve istemediğiniz verileri temizleyebilirsiniz. Özellikle sosyal medyada paylaşım yapmadan önce konum bilgilerinizi korumak için idealdir.

Metadata temizleme işlemi orijinal görüntü kalitesini korur, sadece gizli bilgileri kaldırır. Fotoğrafınız aynı çözünürlük ve kalitede yeni bir dosya olarak kaydedilir.""",
    use_cases=[
        "Sosyal medyada paylaşmadan önce fotoğraflarınızdan GPS konumunu kaldırın",
        "Satılık ilan fotoğraflarından ev adresinizi gizleyin",
        "Profesyonel portfolyo için kamera ve lens bilgilerini kontrol edin",
        "Web sitesine yüklemeden önce metadata boyutunu azaltarak performans kazanın",
        "Fotoğraf yarışmalarına gönderimde EXIF kurallarına uygunluğu kontrol edin",
    ],
    faq=[
        {
            "question": "EXIF nedir?",
            "answer": "EXIF (Exchangeable Image File Format), dijital fotoğraflara gömülü metadata'dır. Kamera modeli, çekim ayarları, tarih-saat, GPS konumu gibi bilgileri içerir.",
        },
        {
            "question": "Metadata temizlemek görüntü kalitesini etkiler mi?",
            "answer": "Hayır. Sadece metadata bilgileri silinir, piksel verisi ve görüntü kalitesi değişmez. Aynı çözünürlük ve kalitede yeni dosya elde edersiniz.",
        },
        {
            "question": "Hangi tür metadata görüntülenebilir?",
            "answer": "Kamera modeli, lens bilgisi, ISO, diyafram, enstantane hızı, odak uzaklığı, GPS koordinatları, çekim tarihi-saati ve yazılım bilgileri görüntülenebilir.",
        },
    ],
    accepts_files=True,
    accepts_text=False,
    max_upload_mb=10,
    # v0.8.0: Pipeline
    accepts_pipeline_files=True,
    produces_pipeline_files=True,
    suggested_next=[
        ToolRelation(
            slug="image-resizer",
            relation_type="next",
            label="Boyutlandır",
            description="Temizlediğiniz görseli yeniden boyutlandırın",
        ),
        ToolRelation(
            slug="image-converter", relation_type="next", label="Format Dönüştür", description="Farklı formata çevirin"
        ),
    ],
)

ToolRegistry.register(tool_info, router)


@router.get("/", response_class=HTMLResponse)
async def page(request: Request, pipeline_id: str | None = None):
    """Metadata inspector page"""
    from app.core.observability import record_page_view

    record_page_view("image-metadata", request.headers.get("user-agent"), request.headers.get("referer"))

    # v0.8.0: Pipeline consumption
    pipeline_file = None
    if pipeline_id and tool_info.accepts_pipeline_files:
        from app.core.pipeline import resolve_pipeline_file

        pipeline_file = resolve_pipeline_file(pipeline_id)
        if pipeline_file and not pipeline_file["mime_type"].startswith("image/"):
            pipeline_file = None

    return templates.TemplateResponse(
        request=request, name="metadata.html", context={"tool": tool_info, "pipeline_file": pipeline_file}
    )


@router.post("/inspect", response_class=HTMLResponse)
async def inspect_metadata(
    request: Request,
    files: list[UploadFile] | None = None,
    pipeline_id: str | None = None,
):
    """Extract and display EXIF metadata"""
    from app.core.observability import log_tool_call

    start_time = time.time()

    try:
        # Get file (upload or pipeline)
        if pipeline_id:
            from app.core.pipeline import resolve_pipeline_file

            pipeline_data = resolve_pipeline_file(pipeline_id)
            if not pipeline_data:
                raise ValueError("Pipeline dosyası bulunamadı veya süresi dolmuş")
            file_path = pipeline_data["file_path"]
            filename = pipeline_data["original_name"]
        else:
            if not files or not files[0]:
                raise ValueError("Lütfen bir resim dosyası yükleyin")

            file = files[0]
            # Simple validation
            if not file.content_type.startswith("image/"):
                raise ValueError("Sadece resim dosyaları kabul edilir")
            temp_path = settings.TEMP_DIR / f"metadata_{file.filename}"
            with open(temp_path, "wb") as f:
                f.write(await file.read())
            file_path = str(temp_path)
            filename = file.filename

        # Extract metadata using PIL's getexif()
        img = Image.open(file_path)
        metadata_items = []
        has_exif = False

        try:
            exif_data = img.getexif()
            if exif_data:
                has_exif = True
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, f"Tag {tag_id}")
                    # Convert bytes to string
                    if isinstance(value, bytes):
                        try:
                            value = value.decode("utf-8", errors="ignore")
                        except Exception:
                            value = str(value)
                    metadata_items.append({"category": "EXIF", "name": tag_name, "value": str(value)[:100]})
        except Exception:
            pass  # No EXIF data

        # Basic info
        basic_info = {
            "format": img.format,
            "mode": img.mode,
            "size": f"{img.width}x{img.height}",
            "file_size": os.path.getsize(file_path),
        }

        duration = (time.time() - start_time) * 1000
        log_tool_call("image-metadata", "success", duration, {"has_exif": has_exif})

        # Clean up temp file
        if not pipeline_id and os.path.exists(file_path):
            os.remove(file_path)

        return templates.TemplateResponse(
            request=request,
            name="metadata.html",
            context={
                "tool": tool_info,
                "metadata": metadata_items,
                "basic_info": basic_info,
                "has_exif": has_exif,
                "filename": filename,
                "original_path": file_path if pipeline_id else None,
                "can_clean": has_exif,
            },
        )

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        log_tool_call("image-metadata", "error", duration, {"error": str(e)})
        return HTMLResponse(content=f'<div class="text-red-500">Hata: {str(e)}</div>', status_code=400)


@router.post("/clean", response_class=HTMLResponse)
async def clean_metadata(
    request: Request,
    file_path: str = Form(...),
):
    """Remove all EXIF metadata from image"""
    from app.core.observability import log_tool_call

    start_time = time.time()

    try:
        # Load image
        img = Image.open(file_path)

        # Create new image without EXIF
        img_clean = Image.new(img.mode, img.size)
        img_clean.putdata(list(img.getdata()))

        # Save
        output_filename = f"clean_{uuid.uuid4().hex[:8]}{os.path.splitext(file_path)[1]}"
        output_path = settings.TEMP_DIR / output_filename
        img_clean.save(output_path, format=img.format or "PNG")

        # v0.8.0: Pipeline production
        pipeline_id = None
        if tool_info.produces_pipeline_files:
            from app.core.pipeline import create_pipeline_file

            try:
                pipeline_id = create_pipeline_file(
                    source_tool_slug="image-metadata",
                    input_file_path=str(output_path),
                    mime_type=f"image/{(img.format or 'png').lower()}",
                    original_name=output_filename,
                )
            except Exception:
                pass

        duration = (time.time() - start_time) * 1000
        log_tool_call("image-metadata", "success", duration, {"cleaned": True})

        # Return Success Card with Pipeline Options
        return templates.TemplateResponse(
            request=request,
            name="components/success_card.html",  # We can reuse a generic success card or inline it. Let's inline for now to match other tools pattern or use a new component if I had one.
            # Actually, I'll inline the HTML here to be safe and consistent with image-converter style
            context={
                "request": request,  # Required for url_for if used
            },
        )

        # Wait, I can't easily inline if I use TemplateResponse without a template.
        # I'll return HTML string like image-converter does.

        return HTMLResponse(f"""
        <div class="bg-emerald-500/10 border border-emerald-500/50 rounded-xl p-6 animate-fade-in">
            <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-3">
                    <div class="p-2 bg-emerald-500 rounded-lg text-white">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    </div>
                    <div>
                        <h3 class="text-lg font-bold text-white">Metadata Temizlendi!</h3>
                        <p class="text-emerald-400 text-sm">{output_filename}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-slate-900/50 p-4 rounded-lg border border-slate-700/50 mb-6">
                <p class="text-slate-300 text-sm">
                    Tüm EXIF, GPS ve kamera bilgileri başarıyla silindi. Görüntü kalitesi korundu.
                </p>
            </div>
            
            <div class="flex flex-col gap-4">
                <div class="flex items-center justify-between gap-4">
                    <a href="/tools/image-metadata/download/{output_filename}" 
                       hx-boost="false"
                       class="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                        İndir
                    </a>
                </div>
                
                <!-- Pipeline Suggestions -->
                {
            '<div class="border-t border-slate-700/50 pt-4">'
            + templates.get_template("components/pipeline_suggestions.html").render(
                pipeline_id=pipeline_id, current_tool="image-metadata", suggested_tools=tool_info.suggested_next
            )
            + "</div>"
            if pipeline_id
            else ""
        }
            </div>
        </div>
        """)

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        log_tool_call("image-metadata", "error", duration, {"error": str(e)})
        return HTMLResponse(content=f'<div class="text-red-500">Hata: {str(e)}</div>', status_code=400)


@router.get("/download/{filename}")
async def download(filename: str, background_tasks: BackgroundTasks):
    from app.core.config import settings

    file_path = settings.TEMP_DIR / filename

    if not file_path.exists():
        return HTMLResponse("Dosya bulunamadı veya süresi doldu.", status_code=404)

    # Dosyayı gönderdikten sonra sil
    background_tasks.add_task(os.remove, file_path)

    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")
