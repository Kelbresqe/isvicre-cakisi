import os
import time
import uuid
import cv2
import numpy as np

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.rate_limit import rate_limit_dependency
from app.tools.registry import Category, ToolInfo, ToolRegistry, ToolRelation

# Router
router = APIRouter(
    prefix="/tools/qr-code-reader",
    tags=["QR Code Reader"],
    dependencies=[Depends(rate_limit_dependency)],
)

# Templates
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(
    directory=[
        os.path.join(TOOL_DIR, "templates"),
        os.path.join(settings.BASE_DIR, "app", "templates"),
    ]
)

# Tool Registration
tool_info = ToolInfo(
    slug="qr-code-reader",
    title="QR Kod Okuyucu",
    category=Category.IMAGE,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4h2v-4zM6 20h2v-4H6v4zM6 10h2V6H6v4zM16 6h2v4h-2V6zM6 14h2v-4H6v4zM10 20h2v-6h-2v6zM10 10h2V4h-2v6zM10 14h2v-2h-2v2zM14 14h2v-2h-2v2zM14 20h2v-2h-2v2z"></path></svg>',
    image_url="/static/images/qr_code_reader.png",
    description="Resim dosyalarından QR kodları okuyun.",
    short_description="Resimden QR kod okuma",
    detailed_description="Yüklediğiniz resimlerdeki QR kodları otomatik olarak tespit eder ve içeriğini okur. URL, metin veya diğer verileri anında görüntüler.",
    seo_title="Online QR Kod Okuyucu - Resimden QR Kod Çözücü | İsviçre Çakısı",
    seo_description="Resim dosyalarınızdaki QR kodları ücretsiz okuyun. JPG, PNG formatlarını destekler. Hızlı, güvenli ve kurulum gerektirmeyen online QR kod okuyucu.",
    keywords="qr kod okuyucu, qr code reader, resimden qr okuma, online qr çözücü",
    long_description="""İsviçre Çakısı QR Kod Okuyucu ile bilgisayarınızdaki veya telefonunuzdaki resim dosyalarından QR kodları kolayca okuyabilirsiniz. Kamera kullanmanıza gerek kalmadan, ekran görüntüsü veya kayıtlı fotoğraflardaki QR kodların içeriğine ulaşın.

Araç, yüklenen resimdeki QR kodu otomatik olarak algılar ve içeriğini (web sitesi adresi, metin, iletişim bilgisi vb.) size sunar. Eğer içerik bir web sitesi adresi ise, tek tıkla o adrese gidebilirsiniz.

Tüm işlemler tarayıcınız üzerinden güvenli bir şekilde gerçekleştirilir.""",
    use_cases=[
        "Ekran görüntüsü aldığınız QR kodları okuyun",
        "Bilgisayarınızda kayıtlı QR kodlu biletleri kontrol edin",
        "Sosyal medyada paylaşılan QR kodların içeriğini görüntüleyin",
        "Bozuk veya silik QR kodları dijital ortamda okumayı deneyin",
    ],
    faq=[
        {
            "question": "Hangi resim formatları destekleniyor?",
            "answer": "JPG, PNG, WebP ve diğer yaygın resim formatlarını destekliyoruz.",
        },
        {
            "question": "Kamera erişimi gerekiyor mu?",
            "answer": "Hayır, bu araç sadece yüklediğiniz resim dosyalarından okuma yapar. Kamera izni istemez.",
        },
        {
            "question": "Okunan veriler kaydediliyor mu?",
            "answer": "Hayır, yüklediğiniz resimler ve okunan veriler sunucularımızda saklanmaz. İşlem bittikten sonra silinir.",
        },
    ],
    accepts_files=True,
    accepts_text=False,
    max_upload_mb=10,
    accepts_pipeline_files=True,
    produces_pipeline_files=False,
    suggested_next=[
        ToolRelation(
            slug="url-encoder",
            relation_type="next",
            label="URL İşlemleri",
            description="Okunan URL'i kodlayın veya çözün",
        ),
        ToolRelation(
            slug="qr-code",
            relation_type="next",
            label="QR Kod Oluştur",
            description="Kendi QR kodunuzu oluşturun",
        ),
    ],
)

ToolRegistry.register(tool_info, router)


@router.get("/", response_class=HTMLResponse)
async def page(request: Request, pipeline_id: str | None = None):
    """QR Code Reader page"""
    from app.core.observability import record_page_view

    record_page_view("qr-code-reader", request.headers.get("user-agent"), request.headers.get("referer"))

    # Pipeline consumption
    pipeline_file = None
    if pipeline_id and tool_info.accepts_pipeline_files:
        from app.core.pipeline import resolve_pipeline_file

        pipeline_file = resolve_pipeline_file(pipeline_id)
        if pipeline_file and not pipeline_file["mime_type"].startswith("image/"):
            pipeline_file = None

    return templates.TemplateResponse(
        request=request, name="reader.html", context={"tool": tool_info, "pipeline_file": pipeline_file}
    )


@router.post("/read", response_class=HTMLResponse)
async def read_qr(
    request: Request,
    files: list[UploadFile] | None = None,
    pipeline_id: str | None = None,
):
    """Read QR code from image"""
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
        else:
            if not files or not files[0]:
                raise ValueError("Lütfen bir resim dosyası yükleyin")

            file = files[0]
            if not file.content_type.startswith("image/"):
                raise ValueError("Sadece resim dosyaları kabul edilir")

            # Read file content directly into memory
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                # Fallback: save to temp and read (sometimes needed for certain formats)
                temp_path = settings.TEMP_DIR / f"qr_read_{uuid.uuid4().hex}.png"
                with open(temp_path, "wb") as f:
                    f.write(contents)
                img = cv2.imread(str(temp_path))
                os.remove(temp_path)

                if img is None:
                    raise ValueError("Resim dosyası okunamadı")

        # If pipeline, we need to read from path
        if pipeline_id:
            img = cv2.imread(file_path)
            if img is None:
                raise ValueError("Pipeline dosyası okunamadı")

        # Detect and Decode
        detector = cv2.QRCodeDetector()
        data, bbox, straight_qrcode = detector.detectAndDecode(img)

        if not data:
            # Try to use pyzbar if available (better detection) or just fail
            # For now, stick to OpenCV as requested, but handle empty result
            raise ValueError("QR kod bulunamadı veya okunamadı")

        duration = (time.time() - start_time) * 1000
        log_tool_call("qr-code-reader", "success", duration, {"length": len(data)})

        is_url = data.startswith("http://") or data.startswith("https://")

        return templates.TemplateResponse(
            request=request,
            name="reader.html",
            context={
                "tool": tool_info,
                "result": data,
                "is_url": is_url,
                "pipeline_id": pipeline_id,  # Pass back to keep context if needed
            },
        )

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        log_tool_call("qr-code-reader", "error", duration, {"error": str(e)})
        return HTMLResponse(content=f'<div class="text-red-500">Hata: {str(e)}</div>', status_code=400)
