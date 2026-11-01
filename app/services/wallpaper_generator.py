from __future__ import annotations

import io

from PIL import Image, ImageOps


def create_wallpaper(image_bytes: bytes, max_dimension: int = 2560) -> bytes:
    """Create a Telegram-friendly JPEG wallpaper while preserving the image aspect ratio."""
    with Image.open(io.BytesIO(image_bytes)) as source:
        image = ImageOps.exif_transpose(source)
        if image.mode in ("RGBA", "LA") or "transparency" in image.info:
            rgba = image.convert("RGBA")
            background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            image = Image.alpha_composite(background, rgba).convert("RGB")
        else:
            image = image.convert("RGB")
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=92, optimize=True, progressive=True)
        return output.getvalue()
