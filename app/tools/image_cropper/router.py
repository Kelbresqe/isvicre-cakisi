"""Image Cropper tool - simple manual cropping"""

import time
import uuid

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from PIL import Image

from app.core.config import settings
from app.core.rate_limit import rate_limit_dependency
from app.core.utils import get_tool_templates
from app.tools.registry import Category, ToolInfo, ToolRegistry, ToolRelation

router = APIRouter(prefix="/tools/image-cropper", tags=["Image Cropper"], dependencies=[Depends(rate_limit_dependency)])

templates = get_tool_templates(__file__)

tool_info = ToolInfo(
    slug="image-cropper",
    title="Resim Kırpma",
    category=Category.IMAGE,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z"></path></svg>',
    image_url="/static/images/image_cropper.png",
    description="Resimlerinizi manuel olarak belirttiğiniz boyutlara kırpın.",
    short_description="Manuel koordinat ile görsel kırpma aracı",
    seo_title="Ücretsiz Resim Kırpma Aracı | İsviçre Çakısı",
    seo_description="Resimlerinizi istediğiniz boyutlara kırpın. Manuel koordinat girişi ile hassas kırpma.",
    keywords="resim kırpma, image crop, görsel kesme",
    long_description="Basit ve etkili resim kırpma aracı. Koordinatları manuel girerek görseli istediğiniz alana kırpın.",
    use_cases=["Profil fotoğrafı için kare kırpma", "Banner için belirli boyuta getirme"],
    faq=[
        {
            "question": "Koordinat sistemi nasıl?",
            "answer": "Sol üst köşe (0,0) noktasıdır. X sağa, Y aşağıya doğru artar.",
        }
    ],
    accepts_files=True,
    max_upload_mb=10,
    accepts_pipeline_files=True,
    produces_pipeline_files=True,
    suggested_next=[
        ToolRelation(
            slug="image-resizer",
            relation_type="next",
            label="Boyutlandır",
            description="Kırptıktan sonra yeniden boyutlandırın",
        )
    ],
)

ToolRegistry.register(tool_info, router)


@router.get("/", response_class=HTMLResponse)
async def page(request: Request, pipeline_id: str | None = None):
    from app.core.observability import record_page_view

    record_page_view("image-cropper", request.headers.get("user-agent"), request.headers.get("referer"))

    pipeline_file = None
    if pipeline_id:
        from app.core.pipeline import resolve_pipeline_file

        pipeline_file = resolve_pipeline_file(pipeline_id)
        if pipeline_file and not pipeline_file["mime_type"].startswith("image/"):
            pipeline_file = None

    return templates.TemplateResponse(
        request=request, name="cropper.html", context={"tool": tool_info, "pipeline_file": pipeline_file}
    )


@router.post("/crop", response_class=FileResponse)
async def crop(
    request: Request,
    file: UploadFile | None = None,
    pipeline_id: str | None = None,
    width: int = Form(...),
    height: int = Form(...),
    x: int = Form(default=0),
    y: int = Form(default=0),
):
    from app.core.observability import log_tool_call

    start = time.time()

    try:
        if pipeline_id:
            from app.core.pipeline import resolve_pipeline_file

            pf = resolve_pipeline_file(pipeline_id)
            if not pf:
                raise ValueError("Pipeline dosyası bulunamadı")
            file_path = pf["file_path"]
        else:
            if not file or not file.content_type.startswith("image/"):
                raise ValueError("Geçerli resim gerekli")
            temp = settings.TEMP_DIR / f"crop_in_{file.filename}"
            with open(temp, "wb") as f:
                f.write(await file.read())
            file_path = str(temp)

        img = Image.open(file_path)
        cropped = img.crop((x, y, x + width, y + height))
        output = settings.TEMP_DIR / f"cropped_{uuid.uuid4().hex[:8]}.{img.format.lower() if img.format else 'png'}"
        cropped.save(output, format=img.format or "PNG")

        # Pipeline production
        if tool_info.produces_pipeline_files:
            from app.core.pipeline import create_pipeline_file

            try:
                create_pipeline_file(
                    "image-cropper", str(output), f"image/{(img.format or 'png').lower()}", output.name
                )
            except Exception:
                pass

        log_tool_call("image-cropper", "success", (time.time() - start) * 1000, {})
        return FileResponse(
            path=output, filename=output.name, media_type=f"image/{img.format.lower() if img.format else 'png'}"
        )
    except Exception as e:
        log_tool_call("image-cropper", "error", (time.time() - start) * 1000, {"error": str(e)})
        raise
