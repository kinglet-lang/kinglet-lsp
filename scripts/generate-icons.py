#!/usr/bin/env python3
"""Generate PNG icons for Perch (extension icon, README, and framed logo)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "image" / "icons"
SIZE = 128
RADIUS = 24
BORDER = 2
PADDING = 6


def run_rsvg(svg: Path, png: Path, width: int, height: int) -> None:
    subprocess.run(
        ["rsvg-convert", "-w", str(width), "-h", str(height), str(svg), "-o", str(png)],
        check=True,
    )


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def generate_icon_png() -> None:
    run_rsvg(ICONS / "icon.svg", ICONS / "icon.png", SIZE, SIZE)


def generate_icon_dark_png() -> None:
    # README displays at 88 CSS px; 2x asset keeps edges sharp.
    run_rsvg(ICONS / "icon-dark.svg", ICONS / "icon-dark.png", 176, 176)


def generate_perch_png() -> None:
    bird = Image.open(ICONS / "icon.png").convert("RGBA")

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (0, 0, SIZE - 1, SIZE - 1),
        radius=RADIUS,
        fill=(245, 246, 248, 255),
        outline=(200, 205, 214, 255),
        width=BORDER,
    )

    inner = SIZE - 2 * PADDING - 2 * BORDER
    bird.thumbnail((inner, inner), Image.Resampling.LANCZOS)
    inner_radius = max(RADIUS - PADDING, 8)
    inner_mask = rounded_mask(inner, inner_radius)
    bird.putalpha(Image.composite(bird.getchannel("A"), Image.new("L", bird.size, 0), inner_mask))

    offset = ((SIZE - bird.width) // 2, (SIZE - bird.height) // 2)
    canvas.paste(bird, offset, bird)

    outer_mask = rounded_mask(SIZE, RADIUS)
    canvas.putalpha(Image.composite(canvas.getchannel("A"), Image.new("L", (SIZE, SIZE), 0), outer_mask))

    canvas.convert("RGB").save(ICONS / "perch.png", optimize=True)


def main() -> int:
    if not ICONS.is_dir():
        print(f"missing icons dir: {ICONS}", file=sys.stderr)
        return 1

    generate_icon_png()
    generate_icon_dark_png()
    generate_perch_png()
    print("Generated image/icons/icon.png, icon-dark.png, perch.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
