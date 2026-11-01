from __future__ import annotations

import base64
import json
import re
from pathlib import Path

from app.services.color_processor import rgb_to_telegram_int

_KEY = re.compile(r"^[A-Za-z0-9_.-]+$")
_WALLPAPER_OVERRIDE_KEYS = {
    "chat_wallpaper",
    "chat_wallpaper_gradient_to",
    "chat_wallpaper_gradient_to1",
    "chat_wallpaper_gradient_to2",
    "chat_wallpaper_gradient_to3",
}


def generate_attheme(
    template_path: Path,
    mapping_path: Path,
    colors: dict[str, str],
    wallpaper_bytes: bytes | None = None,
) -> bytes:
    """Generate an Android .attheme, optionally embedding a base64 JPEG wallpaper.

    Telegram's .attheme wallpaper block is delimited by WPS/WPE. The payload
    between those markers is the base64-encoded image, not a color variable.
    """
    template = template_path.read_text(encoding="utf-8")
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError("Color mapping must be a non-empty JSON object.")

    lines = template.splitlines()
    positions: dict[str, list[int]] = {}
    for index, line in enumerate(lines):
        if not line or line.lstrip().startswith(("#", "//")) or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        positions.setdefault(key, []).append(index)

    for key, role in mapping.items():
        if not isinstance(key, str) or not _KEY.fullmatch(key):
            raise ValueError("Invalid theme key in mapping.")
        if not isinstance(role, str) or role not in colors:
            raise ValueError(f"Unknown color role for theme key: {key}")
        indexes = positions.get(key)
        if not indexes:
            # Never add unverified keys absent from the trusted template.
            continue
        value = rgb_to_telegram_int(colors[role])
        for index in indexes:
            lines[index] = f"{key}={value}"

    if wallpaper_bytes:
        # A solid chat_wallpaper color takes precedence over the embedded image.
        lines = [
            line for line in lines
            if line.split("=", 1)[0].strip() not in _WALLPAPER_OVERRIDE_KEYS
        ]

    output = "\n".join(lines).rstrip() + "\n"
    if not any("=" in line for line in output.splitlines()):
        raise ValueError("Generated theme is empty.")

    if wallpaper_bytes:
        encoded_wallpaper = base64.b64encode(wallpaper_bytes).decode("ascii")
        output += f"\nWPS\n{encoded_wallpaper}\nWPE\n"

    return output.encode("utf-8")
