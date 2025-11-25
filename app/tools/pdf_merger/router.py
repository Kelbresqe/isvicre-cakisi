import os
import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from pypdf import PdfWriter

from app.core.config import settings
from app.core.rate_limit import rate_limit_dependency
from app.core.utils import get_random_tech_trivia, get_tool_templates
from app.tools.registry import Category, ToolInfo, ToolRegistry, ToolRelation

# 1. Router Tanımlama
router = APIRouter(
    prefix="/tools/pdf-merger",
    tags=["PDF Merger"],
    dependencies=[Depends(rate_limit_dependency)],
)

# 2. Şablon Ayarları
templates = get_tool_templates(__file__)

# 3. Aracı Kaydetme (Registry)
tool_info = ToolInfo(
    slug="pdf-merger",
    title="PDF Birleştirici",
    category=Category.OFFICE,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>',
    image_url="/static/images/pdf_merger.png",
    description="Birden fazla PDF dosyasını tek bir dokümanda birleştirin.",
    short_description="PDF dosyalarını birleştirme",
    detailed_description="PDF dosyalarınızı kolayca tek bir dokümanda toplayın. Sürükle-bırak ile sıralama yapın, istediğiniz sırada birleştirin. Ofis işleri, faturalar, sözleşmeler için ideal. Maksimum 25MB toplam boyut.",
    seo_title="Ücretsiz PDF Birleştirme Aracı - PDF Dosyalarını Tek PDF Yapma | İsviçre Çakısı",
    seo_description="Birden fazla PDF dosyasını ücretsiz online birleştirin. Sürükle-bırak ile sıralama, hızlı birleştirme. Fatura, sözleşme ve raporlarınızı tek PDF'de toplayın.",
    keywords="pdf birleştirme, pdf merge, pdf dosya birleştir, çoklu pdf tek pdf, online pdf merger, ücretsiz pdf aracı",
    long_description="""İsviçre Çakısı PDF Birleştirici, birden fazla PDF dosyanızı tek bir dokümanda birleştirmenizi sağlar. Ofis işlerinizde ayrı ayrı gelen fatura, sözleşme veya raporları tek PDF'de toplayabilir, böylece organizasyonunuzu kolaylaştırabilirsiniz.

Araç, pypdf kütüphanesi kullanarak PDF dosyalarının içeriğini ve formatını koruyarak birleştirir. İşlem tamamen sunucu tarafında yapılır ve dosyalarınız işlem sonrası otomatik silinir.

Sıralama özelliği sayesinde PDF'lerin birleştirilme sırasını istediğiniz gibi ayarlayabilirsiniz. Sürükle-bırak arayüzü ile kolayca organize edebilir, istenmeyen dosyaları kaldırabilirsiniz.

Maksimum dosya boyutu limiti içinde istediğiniz kadar PDF dosyasını birleştirebilirsiniz. Hem bireysel kullanıcılar hem de küçük işletmeler için ideal.""",
    use_cases=[
        "Ay sonu faturalarınızı tek PDF'de toplayarak muhasebe süreçlerini hızlandırın",
        "Sözleşme ve ekleri tek dokümanda birleştirerek e-imza işlemlerini basitleştirin",
        "Üniversite ödevlerinizi farklı bölümlerden tek PDF haline getirin",
        "İhale dosyalarını tek pakette sunun",
        "Portfolyonuzu tek PDF dosyasında profesyonel şekilde sunun",
    ],
    faq=[
        {
            "question": "Maksimum kaç PDF birleştirebilirim?",
            "answer": "Dosya sayısında limit yoktur ancak toplam boyut maksimum 25MB olmalıdır.",
        },
        {
            "question": "PDF sıralamasını değiştirebilir miyim?",
            "answer": "Evet, sürükle-bırak özelliği ile PDF'lerin sırasını istediğiniz gibi ayarlayabilirsiniz.",
        },
        {
            "question": "Şifreli PDF'ler birleştirilebilir mi?",
            "answer": "Şu anda şifreli PDF desteği bulunmamaktadır. Önce şifre kaldırmanız gerekir.",
        },
    ],
    # Tool capabilities
    accepts_files=True,
    accepts_text=False,
    max_upload_mb=settings.MAX_PDF_SIZE_MB,
    # v0.8.0: Pipeline capabilities
    accepts_pipeline_files=True,
    produces_pipeline_files=True,
    suggested_next=[
        ToolRelation(
            slug="pdf-splitter",
            relation_type="next",
            label="PDF Ayır",
            description="Birleştirdiğiniz PDF'den istediğiniz sayfaları seçin",
        ),
    ],
)

ToolRegistry.register(tool_info, router)


# 4. Endpointler
@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    # v0.7.0: Analytics tracking
    from app.core.observability import record_page_view

    record_page_view("pdf-merger", request.headers.get("user-agent"), request.headers.get("referer"))

    return templates.TemplateResponse(request=request, name="merger.html", context={"tool": tool_info})


@router.post("/merge", response_class=HTMLResponse)
async def merge(
    request: Request,
    files: List[UploadFile],
):
    if not files or len(files) < 2:
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={"error_msg": "En az 2 PDF dosyası seçmelisiniz."},
        )

    import time

    from app.core.observability import log_tool_call
    from app.core.upload import validate_pdf

    start_time = time.time()

    try:
        merger = PdfWriter()

        for file in files:
            content = await validate_pdf(file)

            # Write to temp file for pypdf (it handles file objects better)
            # But pypdf can also handle BytesIO. Let's try BytesIO first to avoid too many temp files.
            from io import BytesIO

            merger.append(BytesIO(content))

        # Save merged file
        output_filename = f"merged_{uuid.uuid4().hex[:8]}.pdf"
        output_path = settings.TEMP_DIR / output_filename

        merger.write(output_path)
        merger.close()

        file_size = output_path.stat().st_size

        # v0.8.0: Pipeline production
        if tool_info.produces_pipeline_files:
            from app.core.pipeline import create_pipeline_file

            try:
                create_pipeline_file(
                    source_tool_slug="pdf-merger",
                    input_file_path=str(output_path),
                    mime_type="application/pdf",
                    original_name=output_filename,
                )
            except Exception:
                pass

        # Trivia
        trivia = get_random_tech_trivia()

        # Format size
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
                "file_count": len(files),
                "file_size_fmt": fmt_size(file_size),
                "output_filename": output_filename,
                "trivia": trivia,
            },
        )

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        log_tool_call("pdf-merger", "error", duration, {"error": str(e)})

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
    file_path = settings.TEMP_DIR / filename

    if not file_path.exists():
        return HTMLResponse("Dosya bulunamadı veya süresi doldu.", status_code=404)

    # Dosyayı gönderdikten sonra sil
    background_tasks.add_task(os.remove, file_path)

    return FileResponse(path=file_path, filename=filename, media_type="application/pdf")
