"""Locked dark endcard for every Briq Instagram reel.

Dark charcoal background, cream Fraunces 「briq.kr」, thin gold rule above.
No subtitle. Hold this frame at the end of every reel for 4.5 seconds.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from slide_layout import DISPLAY, INK, W, H

BG = INK  # (20, 18, 16)
CREAM = (247, 244, 236)
RULE_GOLD = (198, 168, 106)
DISPLAY_SIZE = 92
RULE_W = 72
RULE_GAP = 36
END_SECONDS = 4.5
SECONDS_PER_SLIDE = 1.8

_FONT_URL = (
    "https://github.com/googlefonts/fraunces/raw/main/fonts/ttf/"
    "Fraunces%5BSOFT%2CWONK%2Copsz%2Cwght%5D.ttf"
)


def ensure_display_font() -> str:
    """Fraunces at the path slide_layout already expects."""
    path = Path(DISPLAY)
    if path.is_file() and path.stat().st_size > 10_000:
        return str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    local = Path(__file__).resolve().parent / "fonts" / "Fraunces-500.ttf"
    if local.is_file():
        path.write_bytes(local.read_bytes())
        return str(path)
    tmp = path.with_suffix(".download")
    urllib.request.urlretrieve(_FONT_URL, tmp)
    tmp.replace(path)
    return str(path)


def render_endcard() -> Image.Image:
    """1080×1350 dark card: gold rule + briq.kr only."""
    ensure_display_font()
    font = ImageFont.truetype(DISPLAY, DISPLAY_SIZE)
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    text = "briq.kr"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (W - tw) // 2
    ty = H // 2 - th // 2
    rx = (W - RULE_W) // 2
    ry = ty - RULE_GAP
    draw.line([(rx, ry), (rx + RULE_W, ry)], fill=RULE_GOLD, width=2)
    draw.text((tx, ty), text, font=font, fill=CREAM)
    return img


def save_endcard(path) -> Path:
    """Write the locked endcard JPEG to path."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    render_endcard().save(out, quality=95)
    return out
