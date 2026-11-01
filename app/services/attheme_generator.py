from __future__ import annotations

import json
import re
from pathlib import Path

from app.services.color_processor import rgb_to_telegram_int

_KEY = re.compile(r"^[A-Za-z0-9_.-]+$")


def generate_attheme(
    template_path: Path,
    mapping_path: Path,
    colors: dict[str, str],
    wallpaper_bytes: bytes | None = None,
) -> bytes:
    """Generate a Telegram Android .attheme with an optional binary JPEG wallpaper.

    Telegram stores image wallpapers as raw image bytes between WPS and WPE
    markers. The payload must not be Base64-encoded.
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

    # Do not put image data in chat_wallpaper: that variable is a color value.
    # The actual image is a separate binary section in the .attheme container.
    output = ("\n".join(lines).rstrip() + "\n").encode("utf-8")
    if not any("=" in line for line in lines):
        raise ValueError("Generated theme is empty.")

    if wallpaper_bytes:
        output += b"\nWPS\n" + wallpaper_bytes + b"\nWPE\n"

    return output
