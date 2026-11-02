from __future__ import annotations

import colorsys
import re

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_ARGB = re.compile(r"^#[0-9A-Fa-f]{8}$")


def _rgb(value: str) -> tuple[int, int, int]:
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, round(v))) for v in rgb))


def _linear_channel(value: int) -> float:
    channel = value / 255
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def _luminance(color: str) -> float:
    red, green, blue = _rgb(color)
    return 0.2126 * _linear_channel(red) + 0.7152 * _linear_channel(green) + 0.0722 * _linear_channel(blue)


def contrast_ratio(a: str, b: str) -> float:
    if not _HEX.fullmatch(a) or not _HEX.fullmatch(b):
        raise ValueError("Colors must be #RRGGBB values.")
    light, dark = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def _mix(a: str, b: str, amount: float) -> str:
    left, right = _rgb(a), _rgb(b)
    return _hex(tuple(x * (1 - amount) + y * amount for x, y in zip(left, right)))


def _best_text_color(background: str) -> str:
    return max(("#FFFFFF", "#000000"), key=lambda color: contrast_ratio(color, background))


def _ensure_surface_contrast(color: str, background: str, minimum: float = 2.2) -> str:
    if contrast_ratio(color, background) >= minimum:
        return color
    target = max(("#FFFFFF", "#000000"), key=lambda candidate: contrast_ratio(candidate, background))
    low, high = 0.0, 1.0
    for _ in range(18):
        amount = (low + high) / 2
        if contrast_ratio(_mix(color, target, amount), background) >= minimum:
            high = amount
        else:
            low = amount
    return _mix(color, target, high)


def _hue_color(source: str, shift: float, saturation: float = 0.68, value: float = 0.82) -> str:
    hue, _, _ = colorsys.rgb_to_hsv(*(channel / 255 for channel in _rgb(source)))
    return _hex(tuple(round(channel * 255) for channel in colorsys.hsv_to_rgb((hue + shift) % 1, saturation, value)))


def process_colors(palette: dict[str, str]) -> dict[str, str]:
    required = {"primary", "secondary", "accent", "background"}
    if not required.issubset(palette):
        raise ValueError("Palette is missing required color roles.")
    for role, color in palette.items():
        if not isinstance(color, str) or not _HEX.fullmatch(color):
            raise ValueError(f"Invalid color for role: {role}")

    primary_source = palette["primary"].upper()
    secondary_source = palette["secondary"].upper()
    accent_source = palette["accent"].upper()
    background = palette["background"].upper()
    primary = _ensure_surface_contrast(primary_source, background, 2.2)
    secondary = _ensure_surface_contrast(secondary_source, background, 2.0)
    accent = _ensure_surface_contrast(accent_source, background, 3.0)

    text = _best_text_color(background)
    incoming_bg = _ensure_surface_contrast(_mix(background, secondary, 0.22), background, 1.35)
    outgoing_bg = _ensure_surface_contrast(_mix(background, primary, 0.38), background, 1.55)
    incoming_text = _best_text_color(incoming_bg)
    outgoing_text = _best_text_color(outgoing_bg)
    muted = _mix(text, background, 0.38)
    primary_muted = _mix(_best_text_color(primary), primary, 0.35)
    icon = _mix(text, background, 0.16)
    divider_rgb = _mix(text, background, 0.78)

    result = {
        "primary": primary,
        "secondary": secondary,
        "accent": accent,
        "background": background,
        "surface": background,
        "surface_alt": _mix(background, secondary, 0.12),
        "text": text,
        "muted_text": muted,
        "text_on_primary": _best_text_color(primary),
        "text_on_secondary": _best_text_color(secondary),
        "text_on_accent": _best_text_color(accent),
        "incoming_bg": incoming_bg,
        "incoming_text": incoming_text,
        "incoming_accent": _ensure_surface_contrast(accent, incoming_bg, 2.0),
        "outgoing_bg": outgoing_bg,
        "outgoing_text": outgoing_text,
        "outgoing_accent": _ensure_surface_contrast(accent, outgoing_bg, 2.0),
        "on_primary": _best_text_color(primary),
        "primary_muted": primary_muted,
        "icon": icon,
        "link": accent,
        "danger": "#D64545" if _luminance(background) > 0.35 else "#FF7777",
        "success": "#218B55" if _luminance(background) > 0.35 else "#55D68B",
        "divider": divider_rgb,
        "selected": "#33000000" if _luminance(background) > 0.35 else "#33FFFFFF",
        "shadow": "#22000000",
    }

    avatar_roles = ("red", "orange", "green", "cyan", "blue", "violet", "pink", "saved")
    for index, name in enumerate(avatar_roles):
        if name == "saved":
            color = accent
        else:
            color = _hue_color(accent_source, index / 7)
        result[f"avatar_{name}"] = _ensure_surface_contrast(color, background, 1.8)

    for foreground, surface in (
        ("text", "background"),
        ("incoming_text", "incoming_bg"),
        ("outgoing_text", "outgoing_bg"),
        ("text_on_primary", "primary"),
        ("text_on_secondary", "secondary"),
        ("text_on_accent", "accent"),
    ):
        if contrast_ratio(result[foreground], result[surface]) < 4.5:
            result[foreground] = _best_text_color(result[surface])
    return result


def rgb_to_telegram_int(hex_color: str) -> str:
    if _HEX.fullmatch(hex_color):
        alpha = 0xFF
        red, green, blue = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    elif _ARGB.fullmatch(hex_color):
        alpha, red, green, blue = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5, 7))
    else:
        raise ValueError("Color must be #RRGGBB or #AARRGGBB.")
    value = (alpha << 24) | (red << 16) | (green << 8) | blue
    return str(value - 2 ** 32 if value >= 2 ** 31 else value)
