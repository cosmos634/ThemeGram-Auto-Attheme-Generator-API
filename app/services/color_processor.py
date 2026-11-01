from __future__ import annotations

import re

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _luminance(hex_color: str) -> float:
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(a: str, b: str) -> float:
    if not _HEX.fullmatch(a) or not _HEX.fullmatch(b):
        raise ValueError("Colors must be #RRGGBB values.")
    light, dark = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def _best_text_color(background: str) -> str:
    return "#FFFFFF" if contrast_ratio(background, "#FFFFFF") >= contrast_ratio(background, "#000000") else "#000000"


def process_colors(palette: dict[str, str]) -> dict[str, str]:
    required = {"primary", "secondary", "accent", "background"}
    if not required.issubset(palette):
        raise ValueError("Palette is missing required color roles.")
    result = dict(palette)
    for role, color in result.items():
        if not isinstance(color, str) or not _HEX.fullmatch(color):
            raise ValueError(f"Invalid color for role: {role}")
        result[role] = color.upper()

    # Preserve the sampled palette while selecting readable foreground colors.
    result["text"] = _best_text_color(result["background"])
    result["muted_text"] = "#D6D6D6" if result["text"] == "#FFFFFF" else "#333333"
    # Ensure accent is distinguishable from the background; fall back to primary if needed.
    if contrast_ratio(result["accent"], result["background"]) < 2.0:
        result["accent"] = result["primary"]
    return result


def rgb_to_telegram_int(hex_color: str) -> str:
    if not _HEX.fullmatch(hex_color):
        raise ValueError("Color must be #RRGGBB.")
    red, green, blue = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    value = 0xFF000000 | (red << 16) | (green << 8) | blue
    if value >= 2 ** 31:
        value -= 2 ** 32
    return str(value)
