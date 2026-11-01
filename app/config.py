from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    api_key: str = os.getenv("API_KEY", "")
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    max_image_pixels: int = int(os.getenv("MAX_IMAGE_PIXELS", "25000000"))
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "12"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    template_path: Path = ROOT_DIR / "templates" / "default.attheme"
    mapping_path: Path = ROOT_DIR / "config" / "color_mapping.json"


settings = Settings()


def validate_startup_config() -> None:
    if len(settings.api_key) < 32:
        raise RuntimeError("API_KEY must be set and contain at least 32 characters.")
    if settings.max_upload_bytes <= 0 or settings.max_image_pixels <= 0:
        raise RuntimeError("Upload and image limits must be positive.")
    if settings.rate_limit_requests <= 0 or settings.rate_limit_window_seconds <= 0:
        raise RuntimeError("Rate-limit settings must be positive.")
    if not settings.template_path.is_file() or not settings.mapping_path.is_file():
        raise RuntimeError("Theme template or color mapping file is missing.")
