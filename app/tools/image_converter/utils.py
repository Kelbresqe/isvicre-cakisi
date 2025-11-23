from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image

from app.core.image_utils import save_image
from app.core.upload import validate_and_load_image


async def process_image(
    file: UploadFile | None,
    url: str | None,
    target_format: str,
    quality: int,
    strip_exif: bool,
) -> tuple[Path, str, int, int]:
    """
    Resmi işler, dönüştürür ve geçici dosya yolunu döndürür.
    Dönüş: (dosya_yolu, dosya_adi, orijinal_boyut, yeni_boyut)
    """

    # 1. Yükle ve Doğrula (Common Pipeline)
    if url:
        # TODO: Implement URL validation in common pipeline or keep it here for now
        # For now, let's stick to file upload as per new requirements or handle URL separately
        raise HTTPException(status_code=400, detail="URL'den yükleme şu an devre dışı.")

    img, filename, original_size = await validate_and_load_image(file)

    try:
        # 2. EXIF Temizle
        if strip_exif:
            data = img.getdata()
            img_without_exif = Image.new(img.mode, img.size)
            img_without_exif.putdata(data)
            img = img_without_exif

        # 3. Format Hazırlığı
        target_format = target_format.upper()

        if target_format == "JPG":
            target_format = "JPEG"
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
        elif target_format == "WEBP":
            if img.mode == "P":
                img = img.convert("RGBA")
        elif target_format == "ICO":
            if img.mode not in ("RGBA",):
                img = img.convert("RGBA")

        # 4. Kaydet (Shared Logic)
        save_kwargs = {}
        if target_format in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality
        if target_format in ("JPEG", "PNG"):
            save_kwargs["optimize"] = True

        output_path, output_filename, new_size = save_image(
            img, filename, target_format, **save_kwargs
        )

        return output_path, output_filename, original_size, new_size

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Resim işlenirken hata oluştu: {str(e)}"
        )
