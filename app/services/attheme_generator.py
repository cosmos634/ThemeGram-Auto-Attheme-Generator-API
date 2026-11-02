from __future__ import annotations

import json
import re
from pathlib import Path

from app.services.color_processor import rgb_to_telegram_int

_KEY = re.compile(r"^[A-Za-z0-9_.-]+$")


def _wallpaper_file_offset(color_body: bytes) -> tuple[bytes, int]:
    offset = 0
    while True:
        header = f"wallpaperFileOffset={offset}\n".encode("ascii")
        calculated = len(header) + len(color_body) + len(b"WPS\n")
        if calculated == offset:
            return header, offset
        offset = calculated


def generate_attheme(
    template_path: Path,
    mapping_path: Path,
    colors: dict[str, str],
    wallpaper_bytes: bytes | None = None,
) -> bytes:
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

    missing_keys = []
    for key, role in mapping.items():
        if not isinstance(key, str) or not _KEY.fullmatch(key):
            raise ValueError("Invalid theme key in mapping.")
        if not isinstance(role, str) or role not in colors:
            raise ValueError(f"Unknown color role for theme key: {key}")
        indexes = positions.get(key)
        if not indexes:
            missing_keys.append(key)
            continue
        value = rgb_to_telegram_int(colors[role])
        for index in indexes:
            lines[index] = f"{key}={value}"

    if missing_keys:
        raise ValueError(f"Template is missing mapped Telegram keys: {', '.join(missing_keys[:10])}")

    lines = [
        line for line in lines
        if not line.startswith("wallpaperFileOffset=")
        and not (wallpaper_bytes and line.split("=", 1)[0].strip() == "chat_wallpaper")
    ]
    color_body = ("\n".join(lines).rstrip() + "\n").encode("utf-8")
    if not any("=" in line for line in lines):
        raise ValueError("Generated theme is empty.")

    if not wallpaper_bytes:
        return color_body

    header, offset = _wallpaper_file_offset(color_body)
    output = header + color_body + b"WPS\n" + wallpaper_bytes + b"\nWPE\n"
    if output[offset:offset + len(wallpaper_bytes)] != wallpaper_bytes:
        raise ValueError("Wallpaper byte offset verification failed.")
    return output
