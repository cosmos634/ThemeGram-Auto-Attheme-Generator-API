from __future__ import annotations

import io
from collections import Counter

from PIL import Image, ImageStat

from app.config import settings


def _rgb_hex(color: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*color)


def _linear_luminance(rgb: tuple[int, int, int]) -> float:
    channels = []
    for value in rgb:
        channel = value / 255
        channels.append(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _saturation(rgb: tuple[int, int, int]) -> float:
    high, low = max(rgb), min(rgb)
    return 0.0 if high == 0 else (high - low) / high


def _blend(rgb: tuple[int, int, int], target: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(a * (1 - amount) + b * amount) for a, b in zip(rgb, target))


def _theme_background(colors: list[tuple[tuple[int, int, int], int]], average_luminance: float) -> tuple[int, int, int]:
    # Choose light/dark mode from the whole image, not one accidentally dominant pixel.
    dark_mode = average_luminance < 0.46
    ordered = sorted(colors, key=lambda item: _linear_luminance(item[0]))
    source = ordered[0][0] if dark_mode else ordered[-1][0]
    target = (16, 18, 24) if dark_mode else (247, 247, 250)
    threshold = 0.10 if dark_mode else 0.88
    for step in range(1, 11):
        candidate = _blend(source, target, step / 10)
        lum = _linear_luminance(candidate)
        if (dark_mode and lum <= threshold) or (not dark_mode and lum >= threshold):
            return candidate
    return target


def analyze_image(image_bytes: bytes) -> dict[str, str]:
    """Build a stable palette from the whole image and separate UI background roles."""
    with Image.open(io.BytesIO(image_bytes)) as source:
        image = source.convert("RGB")
        image.thumbnail((320, 320))
        stats = ImageStat.Stat(image)
        average_rgb = tuple(round(value) for value in stats.mean)
        average_luminance = _linear_luminance(average_rgb)

        # Sample image-wide color distribution, then merge near-duplicate quantized colors.
        quantized = image.quantize(colors=12, method=Image.Quantize.MEDIANCUT)
        palette = quantized.getpalette()
        counts = Counter(quantized.getdata())
        colors: list[tuple[tuple[int, int, int], int]] = []
        for index, count in counts.most_common():
            offset = index * 3
            rgb = tuple(palette[offset:offset + 3])
            colors.append((rgb, count))
        if not colors:
            raise ValueError("No colors could be extracted.")

        merged: list[tuple[tuple[int, int, int], int]] = []
        for rgb, count in colors:
            match = next((i for i, (existing, _) in enumerate(merged)
                          if sum((rgb[c] - existing[c]) ** 2 for c in range(3)) < 22 ** 2 * 3), None)
            if match is None:
                merged.append((rgb, count))
            else:
                old, old_count = merged[match]
                total = old_count + count
                average = tuple(round((old[c] * old_count + rgb[c] * count) / total) for c in range(3))
                merged[match] = (average, total)

        merged.sort(key=lambda item: item[1], reverse=True)
        primary = merged[0][0]
        secondary = merged[1][0] if len(merged) > 1 else primary
        accent = max(merged[:8], key=lambda item: _saturation(item[0]))[0]
        background = _theme_background(merged, average_luminance)

        return {
            "primary": _rgb_hex(primary),
            "secondary": _rgb_hex(secondary),
            "accent": _rgb_hex(accent),
            "background": _rgb_hex(background),
        }
