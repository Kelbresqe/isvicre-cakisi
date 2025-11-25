import os
from io import BytesIO
from pathlib import Path

import httpx
import puremagic
from fastapi import HTTPException, UploadFile
from PIL import Image

from app.core.config import settings


async def load_and_validate_image(file: UploadFile | None, url: str | None) -> tuple[Image.Image, str, int]:
    """
    Loads an image from a file upload or URL, validates magic bytes, and returns the PIL Image object.
    Returns: (PIL.Image, filename, original_size_bytes)
    """
    image_data = b""
    filename = "image"

    # 1. Get Data
    if file:
        image_data = await file.read()
        filename = file.filename or "image"
    elif url:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, timeout=10.0)
                resp.raise_for_status()
                image_data = resp.content
                filename = url.split("/")[-1] or "image"
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"URL indirilemedi: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Dosya veya URL gerekli.")

    original_size = len(image_data)

    # 2. Validate Magic Bytes
    try:
        mime_type = puremagic.from_string(image_data, mime=True)
        if not mime_type or not mime_type.startswith("image/"):
            if mime_type is None:
                raise ValueError("Dosya tipi tespit edilemedi.")
            raise ValueError(f"Geçersiz dosya tipi: {mime_type}")
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Geçersiz dosya formatı. Sadece geçerli resim dosyaları kabul edilir.",
        )

    # 3. Load into Pillow
    try:
        img = Image.open(BytesIO(image_data))
        return img, filename, original_size
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resim yüklenirken hata oluştu: {str(e)}")


def save_image(img: Image.Image, filename: str, target_format: str, **save_kwargs) -> tuple[Path, str, int]:
    """
    Saves the PIL image to a temp file with a unique name.
    Returns: (output_path, output_filename, new_size_bytes)
    """
    try:
        output_filename = f"{os.path.splitext(filename)[0]}.{target_format.lower()}"
        output_path = settings.TEMP_DIR / f"processed_{os.urandom(4).hex()}_{output_filename}"

        img.save(output_path, format=target_format, **save_kwargs)
        new_size = os.path.getsize(output_path)

        return output_path, output_filename, new_size
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resim kaydedilirken hata oluştu: {str(e)}")
