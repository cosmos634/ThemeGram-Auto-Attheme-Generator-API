from __future__ import annotations

import logging
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import Response

from app.config import settings
from app.security.api_key import require_api_key
from app.services.attheme_generator import generate_attheme
from app.services.color_processor import process_colors
from app.services.image_analyzer import analyze_image
from app.services.wallpaper_generator import create_wallpaper
from app.utils.file_validation import read_and_validate_image

logger = logging.getLogger(__name__)
router = APIRouter()
_rate_lock = Lock()
_rate_events: dict[str, deque[float]] = defaultdict(deque)


def _check_rate_limit(client_key: str) -> None:
    now = monotonic()
    cutoff = now - settings.rate_limit_window_seconds
    with _rate_lock:
        events = _rate_events[client_key]
        while events and events[0] <= cutoff:
            events.popleft()
        if len(events) >= settings.rate_limit_requests:
            raise HTTPException(429, detail={"error": "rate_limited", "message": "Too many requests. Try again later."})
        events.append(now)


@router.post("/api/v1/generate", dependencies=[Depends(require_api_key)], tags=["themes"])
async def generate_theme(request: Request, image: UploadFile) -> Response:
    client_key = request.client.host if request.client else "unknown"
    _check_rate_limit(client_key)
    image_bytes = await read_and_validate_image(image)
    try:
        palette = analyze_image(image_bytes)
        colors = process_colors(palette)
        wallpaper = create_wallpaper(image_bytes)
        content = generate_attheme(
            settings.template_path,
            settings.mapping_path,
            colors,
            wallpaper_bytes=wallpaper,
        )
    except (ValueError, OSError) as exc:
        logger.warning("Theme generation rejected: %s", type(exc).__name__)
        raise HTTPException(422, detail={"error": "generation_failed", "message": "The image could not be processed into a theme."}) from None
    except Exception:
        logger.exception("Unexpected theme generation failure")
        raise HTTPException(500, detail={"error": "internal_error", "message": "An internal server error occurred."}) from None
    finally:
        await image.close()

    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": 'attachment; filename="generated_theme.attheme"',
            "Cache-Control": "no-store",
        },
    )
