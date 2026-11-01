from __future__ import annotations

import io
import warnings

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.config import settings

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


async def read_and_validate_image(upload: UploadFile) -> bytes:
    data = await upload.read(settings.max_upload_bytes + 1)
    if not data:
        raise HTTPException(400, detail={"error": "empty_file", "message": "Image file is empty."})
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, detail={"error": "file_too_large", "message": "Maximum image size is 10 MB."})

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                if image.format not in ALLOWED_FORMATS:
                    raise HTTPException(400, detail={"error": "unsupported_format", "message": "Only JPEG, PNG and WEBP are supported."})
                if image.width * image.height > settings.max_image_pixels:
                    raise HTTPException(400, detail={"error": "image_too_large", "message": "Image dimensions exceed the allowed limit."})
                image.verify()
            with Image.open(io.BytesIO(data)) as image:
                image.load()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(400, detail={"error": "invalid_image", "message": "The uploaded file is not a valid supported image."}) from None
    return data
