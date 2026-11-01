from __future__ import annotations

import io
from collections import Counter

from PIL import Image

from app.config import settings


def _rgb_hex(color: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*color)


def analyze_image(image_bytes: bytes) -> dict[str, str]:
    """Extract a compact palette using Pillow quantization; no external AI is used."""
    with Image.open(io.BytesIO(image_bytes)) as source:
        image = source.convert("RGB")
        image.thumbnail((256, 256))
        quantized = image.quantize(colors=8, method=Image.Quantize.MEDIANCUT)
        palette = quantized.getpalette()
        counts = Counter(quantized.getdata())
        colors: list[tuple[tuple[int, int, int], int]] = []
        for index, count in counts.most_common():
            offset = index * 3
            rgb = tuple(palette[offset:offset + 3])
            colors.append((rgb, count))
        if not colors:
            raise ValueError("No colors could be extracted.")

        # Merge near-identical palette entries to reduce noisy color variation.
        merged: list[tuple[tuple[int, int, int], int]] = []
        for rgb, count in colors:
            match = next((i for i, (existing, _) in enumerate(merged)
                          if sum((rgb[c] - existing[c]) ** 2 for c in range(3)) < 18 ** 2 * 3), None)
            if match is None:
                merged.append((rgb, count))
            else:
                old, old_count = merged[match]
                total = old_count + count
                average = tuple(round((old[c] * old_count + rgb[c] * count) / total) for c in range(3))
                merged[match] = (average, total)

        merged.sort(key=lambda item: item[1], reverse=True)
        main = merged[0][0]
        secondary = merged[1][0] if len(merged) > 1 else main
        accent = max(merged[:6], key=lambda item: _saturation(item[0]))[0]
        background = min(merged, key=lambda item: _luminance(item[0]))[0] if _luminance(main) > 0.5 else max(merged, key=lambda item: _luminance(item[0]))[0]

        return {
            "primary": _rgb_hex(main),
            "secondary": _rgb_hex(secondary),
            "accent": _rgb_hex(accent),
            "background": _rgb_hex(background),
        }


def _luminance(rgb: tuple[int, int, int]) -> float:
    values = []
    for value in rgb:
        channel = value / 255
        values.append(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2]


def _saturation(rgb: tuple[int, int, int]) -> float:
    high, low = max(rgb), min(rgb)
    return 0.0 if high == 0 else (high - low) / high
