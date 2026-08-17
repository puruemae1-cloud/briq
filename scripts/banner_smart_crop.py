"""Smart cover-crops for Briq homepage / shop banners.

Desktop / tablet / mobile targets match the live CSS frames:
  hero desktop    2400×600  (4:1)  — homepage PC hero is a short panoramic strip
  look desktop    2400×800  (3:1)  — homepage PC look-banners (~56svh × full width)
  look/hero tablet 1600×640 (2.5:1)
  mobile          1200×800  (3:2)  — phones are closer to square
  shop desktop    2400×1200 (2:1)  — category strip
  shop tablet     1600×800
  shop mobile     1200×600

Crops bias toward the subject (and faces in the upper half) so models and
product don't get cut off awkwardly under CSS object-fit: cover.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageOps

# Homepage PC hero: ~38svh × full width ≈ 4:1
HERO_DESKTOP = (2400, 600)
HERO_TABLET = (1600, 500)
HERO_MOBILE = (1200, 800)
# Homepage PC look-banner: ~56svh × full width ≈ 3:1
LOOK_DESKTOP = (2400, 800)
LOOK_TABLET = (1600, 640)
LOOK_MOBILE = (1200, 800)
SHOP_DESKTOP = (2400, 1200)
SHOP_TABLET = (1600, 800)
SHOP_MOBILE = (1200, 600)

# Back-compat aliases
DESKTOP = LOOK_DESKTOP
TABLET = LOOK_TABLET
MOBILE = LOOK_MOBILE

JPEG_QUALITY = 82


@dataclass(frozen=True)
class FocalPoint:
    """Normalised subject centre (0–1) + suggested CSS object-position."""

    x: float
    y: float

    @property
    def css(self) -> str:
        return f"{int(round(self.x * 100))}% {int(round(self.y * 100))}%"


def _luma(rgb: np.ndarray) -> np.ndarray:
    return (
        0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    )


def estimate_focal(im: Image.Image) -> FocalPoint:
    """Guess where the model / product sits for a safe cover crop."""
    rgb = np.asarray(im.convert("RGB"), dtype=np.float32)
    h, w = rgb.shape[:2]
    # Downsample for speed
    step = max(1, min(h, w) // 160)
    small = rgb[::step, ::step]
    sh, sw = small.shape[:2]

    # Studio mat estimate from corners
    s = max(2, min(sh, sw) // 12)
    corners = np.stack(
        [
            small[:s, :s].reshape(-1, 3).mean(0),
            small[:s, -s:].reshape(-1, 3).mean(0),
            small[-s:, :s].reshape(-1, 3).mean(0),
            small[-s:, -s:].reshape(-1, 3).mean(0),
        ]
    )
    bg = np.median(corners, axis=0)
    dist = np.linalg.norm(small - bg.reshape(1, 1, 3), axis=2)
    mask = dist > 28.0

    # Skin-ish pixels in the upper 55% (faces / collarbone)
    r, g, b = small[..., 0], small[..., 1], small[..., 2]
    skin = (
        (r > 95)
        & (g > 40)
        & (b > 20)
        & (r > g)
        & (r > b)
        & ((r - g) > 12)
        & (_luma(small) < 230)
    )
    skin[: int(sh * 0.05), :] = False
    skin[int(sh * 0.55) :, :] = False

    ys, xs = np.where(skin & mask)
    if len(xs) >= 40:
        cx = float(np.median(xs) / max(1, sw - 1))
        cy = float(np.median(ys) / max(1, sh - 1))
        # Keep faces a bit high in frame for banner crops
        cy = min(cy, 0.42)
        return FocalPoint(x=float(np.clip(cx, 0.25, 0.75)), y=float(np.clip(cy, 0.22, 0.48)))

    ys, xs = np.where(mask)
    if len(xs) >= 80:
        cx = float(np.median(xs) / max(1, sw - 1))
        cy = float(np.median(ys) / max(1, sh - 1))
        return FocalPoint(x=float(np.clip(cx, 0.28, 0.72)), y=float(np.clip(cy, 0.28, 0.55)))

    return FocalPoint(0.5, 0.4)


def cover_crop(
    im: Image.Image,
    size: tuple[int, int],
    focal: FocalPoint | None = None,
    *,
    mobile_bias: bool = False,
) -> Image.Image:
    """Scale-to-cover then crop so focal stays inside the frame."""
    im = ImageOps.exif_transpose(im.convert("RGB"))
    tw, th = size
    sw, sh = im.size
    if sw < 8 or sh < 8:
        return im.resize(size, Image.Resampling.LANCZOS)

    scale = max(tw / sw, th / sh)
    nw, nh = max(tw, int(round(sw * scale))), max(th, int(round(sh * scale)))
    resized = im.resize((nw, nh), Image.Resampling.LANCZOS)

    fp = focal or estimate_focal(im)
    cx, cy = fp.x, fp.y
    if mobile_bias:
        # Phones crop tighter; keep headroom for faces.
        cy = min(cy, 0.36)
    elif tw / max(th, 1) >= 2.4:
        # Panoramic PC strip: keep the face in the short vertical window.
        cy = min(max(cy, 0.22), 0.30)

    left = int(round(cx * nw - tw / 2))
    top = int(round(cy * nh - th / 2))
    left = int(np.clip(left, 0, max(0, nw - tw)))
    top = int(np.clip(top, 0, max(0, nh - th)))
    return resized.crop((left, top, left + tw, top + th))


def has_on_model_face(im: Image.Image) -> bool:
    """True when the photo looks like a person (skin in the upper half)."""
    rgb = np.asarray(im.convert("RGB"), dtype=np.float32)
    h, w = rgb.shape[:2]
    step = max(1, min(h, w) // 160)
    small = rgb[::step, ::step]
    sh, sw = small.shape[:2]
    r, g, b = small[..., 0], small[..., 1], small[..., 2]
    skin = (
        (r > 95)
        & (g > 40)
        & (b > 20)
        & (r > g)
        & (r > b)
        & ((r - g) > 12)
        & (_luma(small) < 230)
    )
    skin[: int(sh * 0.05), :] = False
    skin[int(sh * 0.62) :, :] = False
    return int(skin.sum()) >= 40


def is_extreme_closeup(im: Image.Image) -> bool:
    """True when the subject fills almost the whole frame (collar / fabric crop)."""
    rgb = np.asarray(im.convert("RGB"), dtype=np.float32)
    h, w = rgb.shape[:2]
    step = max(1, min(h, w) // 160)
    small = rgb[::step, ::step]
    sh, sw = small.shape[:2]
    s = max(2, min(sh, sw) // 12)
    corners = np.stack(
        [
            small[:s, :s].reshape(-1, 3).mean(0),
            small[:s, -s:].reshape(-1, 3).mean(0),
            small[-s:, :s].reshape(-1, 3).mean(0),
            small[-s:, -s:].reshape(-1, 3).mean(0),
        ]
    )
    bg = np.median(corners, axis=0)
    dist = np.linalg.norm(small - bg.reshape(1, 1, 3), axis=2)
    mask = dist > 28.0
    return float(mask.mean()) > 0.78


def aspect_ratio(im: Image.Image) -> float:
    w, h = im.size
    return w / max(h, 1)


def is_thin_studio_crop(im: Image.Image) -> bool:
    """True when a wide crop is just a vertical product on empty studio grey.

    That's the failure mode on PC look-banners: portrait packshots sliced into
    a panoramic frame leave a dark strip with blank sides.
    """
    rgb = np.asarray(im.convert("RGB"), dtype=np.float32)
    h, w = rgb.shape[:2]
    if w < 32 or h < 16:
        return True
    band = max(8, w // 6)
    left = rgb[:, :band].reshape(-1, 3).mean(0)
    right = rgb[:, -band:].reshape(-1, 3).mean(0)
    mid = rgb[:, 2 * w // 5 : 3 * w // 5].reshape(-1, 3).mean(0)
    side = (left + right) / 2
    if np.linalg.norm(left - right) > 18:
        return False
    if np.linalg.norm(mid - side) < 38:
        return False
    # Sides look like studio paper (near-neutral, similar luma)
    side_chroma = float(np.std(side))
    return side_chroma < 18


def sizes_for_kind(kind: str) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if kind == "shop":
        return SHOP_DESKTOP, SHOP_TABLET, SHOP_MOBILE
    if kind == "hero":
        return HERO_DESKTOP, HERO_TABLET, HERO_MOBILE
    return LOOK_DESKTOP, LOOK_TABLET, LOOK_MOBILE


def save_jpeg(im: Image.Image, path, *, quality: int = JPEG_QUALITY) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, format="JPEG", quality=quality, optimize=True, progressive=True)


def export_banner_set(
    source: Image.Image,
    *,
    desktop_path,
    tablet_path,
    mobile_path,
    shop: bool = False,
    kind: str | None = None,
) -> FocalPoint:
    """Write desktop / tablet / mobile JPEGs from one source photo."""
    focal = estimate_focal(source)
    slot_kind = kind or ("shop" if shop else "look")
    d, t, m = sizes_for_kind(slot_kind)
    desktop = cover_crop(source, d, focal, mobile_bias=False)
    if slot_kind in {"look", "hero"} and is_thin_studio_crop(desktop):
        raise ValueError("thin-studio-crop")
    save_jpeg(desktop, desktop_path)
    save_jpeg(cover_crop(source, t, focal, mobile_bias=False), tablet_path)
    save_jpeg(cover_crop(source, m, focal, mobile_bias=True), mobile_path)
    return focal
