"""Smart cover-crops for Briq homepage / shop banners.

Desktop / tablet / mobile targets match the live CSS frames:
  hero desktop    2400×600  (4:1)  — homepage PC hero is a short panoramic strip
  look desktop    2400×1200 (2:1)  — taller campaign look-banners (editorial room)
  look/hero tablet 1600×900 (~16:9)
  mobile          1200×1000 (6:5)  — phones keep more vertical subject
  shop desktop    2400×1400 (~1.7:1)  — category strip
  shop tablet     1600×1000
  shop mobile     1200×800

Crops bias toward the subject (and faces in the upper half) so models and
product don't get cut off awkwardly under CSS object-fit: cover.
Prefer campaign / lifestyle sources over flat packshots — see weekly-banner-refresh.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageFilter, ImageOps

# Homepage PC hero: ~38svh × full width ≈ 4:1
HERO_DESKTOP = (2400, 600)
HERO_TABLET = (1600, 500)
HERO_MOBILE = (1200, 800)
# Homepage look-banners: taller so campaign / on-model frames keep legs, bags, outfit
LOOK_DESKTOP = (2400, 1200)
LOOK_TABLET = (1600, 900)
LOOK_MOBILE = (1200, 1000)
SHOP_DESKTOP = (2400, 1400)
SHOP_TABLET = (1600, 1000)
SHOP_MOBILE = (1200, 800)

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
    vertical_bias: str = "torso",
) -> Image.Image:
    """Scale-to-cover then crop so focal stays inside the frame.

    vertical_bias for panoramic PC strips:
      torso   — apparel lookbooks (shoulders → waist), never a face-only crop
      product — shoes / bags / accessories (keep the item in the short window)
      face    — rare; only when a headshot strip is explicitly requested
    """
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
        # Phones crop tighter; keep a little headroom without losing the outfit.
        cy = min(max(cy, 0.28), 0.42)
    elif tw / max(th, 1) >= 1.85:
        # Wide PC / tablet strips — keep torso / product mid-frame (not face-only).
        if vertical_bias == "face":
            cy = min(max(cy, 0.12), 0.28)
        elif vertical_bias == "product":
            cy = min(max(cy, 0.40), 0.60)
        else:
            cy = min(max(cy, 0.32), 0.52)

    left = int(round(cx * nw - tw / 2))
    top = int(round(cy * nh - th / 2))
    left = int(np.clip(left, 0, max(0, nw - tw)))
    top = int(np.clip(top, 0, max(0, nh - th)))
    return resized.crop((left, top, left + tw, top + th))


def subject_bbox(im: Image.Image, *, threshold: float = 28.0) -> tuple[int, int, int, int] | None:
    """Tight box around non-studio pixels, or None when the frame is empty."""
    rgb = np.asarray(im.convert("RGB"), dtype=np.float32)
    h, w = rgb.shape[:2]
    step = max(1, min(h, w) // 200)
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
    mask = dist > threshold
    ys, xs = np.where(mask)
    if len(xs) < 40:
        return None
    y0, y1 = int(ys.min() * step), int(min(h, (ys.max() + 1) * step))
    x0, x1 = int(xs.min() * step), int(min(w, (xs.max() + 1) * step))
    if (y1 - y0) < h * 0.08 or (x1 - x0) < w * 0.08:
        return None
    return x0, y0, x1, y1


def trim_studio_subject(im: Image.Image, *, pad_ratio: float = 0.10) -> Image.Image:
    """Crop away empty studio paper so tiny packshot products fill the frame."""
    im = ImageOps.exif_transpose(im.convert("RGB"))
    box = subject_bbox(im)
    if box is None:
        return im
    x0, y0, x1, y1 = box
    w, h = im.size
    bw, bh = x1 - x0, y1 - y0
    # Only trim when the subject is a small island on a huge canvas.
    if (bw * bh) / max(w * h, 1) > 0.55:
        return im
    pad = int(round(max(bw, bh) * pad_ratio))
    left = max(0, x0 - pad)
    top = max(0, y0 - pad)
    right = min(w, x1 + pad)
    bottom = min(h, y1 + pad)
    return im.crop((left, top, right, bottom))


def fit_panorama(
    im: Image.Image,
    size: tuple[int, int],
    focal: FocalPoint | None = None,
    *,
    vertical_bias: str = "torso",
) -> Image.Image:
    """Build a panoramic PC frame that keeps the full product readable.

    Portrait / square PDP stills cannot be cover-cropped into ~3:1 without
    turning into a face or fabric strip. Fit the source to the banner height,
    centre it, and fill the sides with a soft blur of the same image.
    True landscape sources still use cover_crop.
    """
    im = ImageOps.exif_transpose(im.convert("RGB"))
    if vertical_bias == "product":
        im = trim_studio_subject(im)
    tw, th = size
    sw, sh = im.size
    if sw < 8 or sh < 8:
        return im.resize(size, Image.Resampling.LANCZOS)

    target_ar = tw / max(th, 1)
    source_ar = sw / max(sh, 1)
    # Wide enough to cover without slicing the subject into a macro strip.
    if source_ar >= target_ar * 0.88:
        return cover_crop(im, size, focal, mobile_bias=False, vertical_bias=vertical_bias)

    # Fit height so the whole garment / shoe / bag stays in frame.
    scale = th / sh
    nw = max(1, int(round(sw * scale)))
    nh = th
    fg = im.resize((nw, nh), Image.Resampling.LANCZOS)

    # Soft panoramic backdrop from a cover crop of the same still.
    bg = cover_crop(
        im, size, focal or FocalPoint(0.5, 0.45), vertical_bias=vertical_bias
    ).filter(ImageFilter.GaussianBlur(radius=32))
    # Keep the product side readable — slightly darken the blur.
    bg = Image.blend(bg, Image.new("RGB", size, (28, 28, 30)), 0.22)
    canvas = bg.copy()
    x = (tw - fg.size[0]) // 2
    canvas.paste(fg, (x, 0))
    return canvas


def has_on_model_face(im: Image.Image) -> bool:
    """True when the photo looks like a person (a face/neck blob, not hardware)."""
    rgb = np.asarray(im.convert("RGB"), dtype=np.float32)
    h, w = rgb.shape[:2]
    step = max(1, min(h, w) // 160)
    small = rgb[::step, ::step]
    sh, sw = small.shape[:2]
    r, g, b = small[..., 0], small[..., 1], small[..., 2]
    skin = (
        (r > 110)
        & (g > 40)
        & (b > 20)
        & (r > g)
        & (r > b)
        & ((r - g) > 18)
        & ((r - b) > 18)
        & (_luma(small) < 220)
        & (_luma(small) > 55)
    )
    skin[: int(sh * 0.04), :] = False
    skin[int(sh * 0.58) :, :] = False
    ys, xs = np.where(skin)
    if len(xs) < 90:
        return False
    # Buttons / labels are tiny; a face or neck spans a real slice of the frame.
    hspan = float(ys.max() - ys.min()) / max(sh, 1)
    wspan = float(xs.max() - xs.min()) / max(sw, 1)
    if hspan < 0.08 or wspan < 0.06:
        return False
    # Wall-to-wall "skin" is usually khaki fabric, not a person.
    if float(skin.mean()) > 0.22:
        return False
    return True


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


def is_face_dominant(im: Image.Image) -> bool:
    """True when a face fills most of the short axis (headshot, not an outfit)."""
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
        & (_luma(small) > 50)
    )
    # Face lives in the upper ~55% of a portrait lookbook frame.
    skin[int(sh * 0.58) :, :] = False
    ys, xs = np.where(skin)
    if len(xs) < 80:
        return False
    hspan = float(ys.max() - ys.min()) / max(sh, 1)
    wspan = float(xs.max() - xs.min()) / max(sw, 1)
    # Headshot: face covers a large slice of height (and often width).
    if hspan >= 0.38 and wspan >= 0.22:
        return True
    if float(skin[: int(sh * 0.45), :].mean()) > 0.12 and hspan >= 0.28:
        return True
    return False


def subject_fill_ratio(im: Image.Image) -> float:
    """Fraction of non-studio pixels — used to reject empty panoramic crops."""
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
    return float((dist > 28.0).mean())


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


def is_unbalanced_wide_crop(im: Image.Image) -> bool:
    """True when a panoramic crop is empty studio on one side and product on the other."""
    rgb = np.asarray(im.convert("RGB"), dtype=np.float32)
    h, w = rgb.shape[:2]
    if w < 48 or h < 16:
        return True
    luma = _luma(rgb)
    thirds = []
    for i in range(3):
        sl = luma[:, i * w // 3 : (i + 1) * w // 3]
        thirds.append(float(sl.std()))
    lo, hi = min(thirds), max(thirds)
    if hi < 12:
        return True
    # One third is busy product, another is flat grey paper
    return hi > 3.2 * max(lo, 1.0) and lo < 14


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
    require_face: bool = False,
    vertical_bias: str = "torso",
) -> FocalPoint:
    """Write desktop / tablet / mobile JPEGs from one source photo."""
    focal = estimate_focal(source)
    slot_kind = kind or ("shop" if shop else "look")
    d, t, m = sizes_for_kind(slot_kind)
    # Desktop / tablet are panoramic — fit portrait product stills so the
    # garment or shoe stays whole. Mobile is closer to square; cover is fine.
    if slot_kind in {"look", "hero"}:
        desktop = fit_panorama(source, d, focal, vertical_bias=vertical_bias)
    else:
        desktop = cover_crop(
            source, d, focal, mobile_bias=False, vertical_bias=vertical_bias
        )
    if require_face:
        if not has_on_model_face(desktop):
            raise ValueError("crop-missed-face")
    if slot_kind in {"look", "hero"}:
        src_ar = aspect_ratio(source)
        dst_ar = d[0] / max(d[1], 1)
        # Skip thin-studio check when we intentionally padded a portrait still.
        if src_ar >= dst_ar * 0.88:
            if is_thin_studio_crop(desktop) or is_unbalanced_wide_crop(desktop):
                raise ValueError("thin-studio-crop")
        if vertical_bias != "face" and is_face_dominant(desktop):
            raise ValueError("face-dominant-crop")
        fill = subject_fill_ratio(desktop)
        if vertical_bias == "product" and fill < 0.08:
            raise ValueError("empty-product-crop")
        if vertical_bias == "torso" and fill < 0.06:
            raise ValueError("empty-torso-crop")
    save_jpeg(desktop, desktop_path)
    if slot_kind in {"look", "hero"}:
        save_jpeg(
            fit_panorama(source, t, focal, vertical_bias=vertical_bias),
            tablet_path,
        )
    else:
        save_jpeg(
            cover_crop(
                source, t, focal, mobile_bias=False, vertical_bias=vertical_bias
            ),
            tablet_path,
        )
    save_jpeg(
        cover_crop(source, m, focal, mobile_bias=True, vertical_bias=vertical_bias),
        mobile_path,
    )
    return focal
