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


def _rgb(hex_color: str) -> tuple[int, int, int]:
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _mix(a: str, b: str, amount: float) -> str:
    left, right = _rgb(a), _rgb(b)
    return _hex(tuple(round(x * (1 - amount) + y * amount) for x, y in zip(left, right)))


def _best_text_color(background: str, minimum: float = 4.5) -> str:
    # Pure black/white provide the strongest reliable contrast for arbitrary images.
    candidates = ("#FFFFFF", "#000000")
    best = max(candidates, key=lambda color: contrast_ratio(color, background))
    if contrast_ratio(best, background) >= minimum:
        return best
    return best


def _ensure_surface_contrast(color: str, background: str, minimum: float = 2.2) -> str:
    if contrast_ratio(color, background) >= minimum:
        return color
    # Move the sampled hue toward whichever neutral gives better separation.
    targets = ("#FFFFFF", "#000000")
    target = max(targets, key=lambda candidate: contrast_ratio(candidate, background))
    low, high = 0.0, 1.0
    for _ in range(16):
        amount = (low + high) / 2
        candidate = _mix(color, target, amount)
        if contrast_ratio(candidate, background) >= minimum:
            high = amount
        else:
            low = amount
    return _mix(color, target, high)


def process_colors(palette: dict[str, str]) -> dict[str, str]:
    required = {"primary", "secondary", "accent", "background"}
    if not required.issubset(palette):
        raise ValueError("Palette is missing required color roles.")
    result = dict(palette)
    for role, color in result.items():
        if not isinstance(color, str) or not _HEX.fullmatch(color):
            raise ValueError(f"Invalid color for role: {role}")
        result[role] = color.upper()

    background = result["background"]
    primary = _ensure_surface_contrast(result["primary"], background)
    secondary = _ensure_surface_contrast(result["secondary"], background)
    accent = _ensure_surface_contrast(result["accent"], background, 3.0)

    result["primary"] = primary
    result["secondary"] = secondary
    result["accent"] = accent
    result["text"] = _best_text_color(background)
    result["muted_text"] = "#D0D3DA" if result["text"] == "#FFFFFF" else "#454852"
    result["text_on_primary"] = _best_text_color(primary)
    result["text_on_secondary"] = _best_text_color(secondary)
    result["text_on_accent"] = _best_text_color(accent)

    # Guard every foreground/surface pair after all automatic adjustments.
    for foreground, surface in (
        ("text", "background"),
        ("text_on_primary", "primary"),
        ("text_on_secondary", "secondary"),
        ("text_on_accent", "accent"),
    ):
        if contrast_ratio(result[foreground], result[surface]) < 4.5:
            result[foreground] = "#FFFFFF" if _luminance(result[surface]) < 0.179 else "#000000"
    return result


def rgb_to_telegram_int(hex_color: str) -> str:
    if not _HEX.fullmatch(hex_color):
        raise ValueError("Color must be #RRGGBB.")
    red, green, blue = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    value = 0xFF000000 | (red << 16) | (green << 8) | blue
    if value >= 2 ** 31:
        value -= 2 ** 32
    return str(value)
