#!/usr/bin/env python3
"""Map light studio mats to Gucci DarkGray (#e7e7e7) for all catalog PDP photos.

White / cream packshot backgrounds hide pale garments. This module replaces
those mats with the same neutral grey gucci.com uses (RGB 231).

Two paths:
  - fast: soft color remap when the product itself is darker than the mat
  - rembg: background removal + grey composite when the subject is also light
    (white tees, chalk polos, etc.)

Importable helpers for scrapers / weekly syncs / image tag pushes.
"""
from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / "public" / "products"

# Official Gucci DarkGray studio mat.
TARGET_RGB = (231, 231, 231)
TARGET = np.array(TARGET_RGB, dtype=np.float32)

DEFAULT_DIRS = [
    # bb-pdp excluded — Burberry official Scene7 crops must stay untouched
    # (greymat/rembg damaged on-model lifestyle shots).
    "ps-pdp",
    "bs-pdp",
    "ax-pdp",
    "axa-pdp",
    "axg-pdp",
    "axo-pdp",
    "gg-pdp",
    "lu-pdp",
    "cw-pdp",
    # gc-pdp is already DarkGray from gucci.com — skip by default
]


def _luma(rgb: tuple[float, float, float]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def corner_samples(arr: np.ndarray) -> list[np.ndarray]:
    h, w = arr.shape[:2]
    s = max(4, min(h, w) // 40)
    patches = [
        arr[0:s, 0:s],
        arr[0:s, w - s : w],
        arr[h - s : h, 0:s],
        arr[h - s : h, w - s : w],
    ]
    return [p.reshape(-1, 3).mean(axis=0) for p in patches]


def studio_bg_color(arr: np.ndarray) -> np.ndarray | None:
    """Return estimated light studio mat RGB, or None if not a packshot mat."""
    corners = corner_samples(arr)
    luminances = [_luma(tuple(c)) for c in corners]
    light_idx = [i for i, L in enumerate(luminances) if L >= 168]
    if len(light_idx) < 2:
        return None
    light_corners = [corners[i] for i in light_idx]
    bg = np.median(np.stack(light_corners, axis=0), axis=0)
    if len(light_idx) < 3:
        if np.linalg.norm(light_corners[0] - light_corners[1]) > 40:
            return None
        if _luma(tuple(bg)) < 185:
            return None
    for c in light_corners:
        if np.linalg.norm(c - bg) > 65:
            return None
    if _luma(tuple(bg)) < 172:
        return None
    return bg


def already_darkgray(bg: np.ndarray) -> bool:
    """True when mat is already near Gucci DarkGray (skip)."""
    mx, mn = float(np.max(bg)), float(np.min(bg))
    L = _luma(tuple(bg))
    if (mx - mn) < 14 and 218 <= L <= 242:
        return True
    if float(np.linalg.norm(bg.astype(np.float32) - TARGET)) < 10:
        return True
    return False


def needs_rembg(arr: np.ndarray, bg: np.ndarray) -> bool:
    """Pale subjects on light mats need matting — soft remap greys the garment too."""
    h, w = arr.shape[:2]
    cy0, cy1 = h * 2 // 5, h * 3 // 5
    cx0, cx1 = w * 2 // 5, w * 3 // 5
    center = arr[cy0:cy1, cx0:cx1].reshape(-1, 3).astype(np.float32)
    mid_l = float(
        np.median(
            0.2126 * center[:, 0] + 0.7152 * center[:, 1] + 0.0722 * center[:, 2]
        )
    )
    bg_l = _luma(tuple(bg))
    dist = float(np.median(np.linalg.norm(center - bg.reshape(1, 3), axis=1)))
    # Light garment close to mat colour (chalk / white packshots).
    if bg_l >= 220 and mid_l >= 210 and dist < 32:
        return True
    return False


def greymat_array(arr: np.ndarray, bg: np.ndarray) -> np.ndarray:
    """Softly map pixels near the studio mat toward DarkGray."""
    f = arr.astype(np.float32)
    dist = np.linalg.norm(f - bg.reshape(1, 1, 3), axis=2)
    hard = 28.0
    soft = 68.0
    alpha = 1.0 - (dist - hard) / (soft - hard)
    alpha = np.clip(alpha, 0.0, 1.0)
    lum = 0.2126 * f[:, :, 0] + 0.7152 * f[:, :, 1] + 0.0722 * f[:, :, 2]
    alpha = np.where(lum < 155, 0.0, alpha)
    a = alpha[..., None]
    out = f * (1.0 - a) + TARGET.reshape(1, 1, 3) * a
    return np.clip(out, 0, 255).astype(np.uint8)


_SESSION = None


def _get_session():
    global _SESSION
    if _SESSION is None:
        import os

        # CoreML EP crashes on some macOS / image sizes — force CPU.
        os.environ.setdefault("OMP_NUM_THREADS", "1")
        from rembg import new_session

        # Full u2net keeps white garments; u2netp often erases chalk/white fabric.
        try:
            _SESSION = new_session(
                "u2net", providers=["CPUExecutionProvider"]
            )
        except TypeError:
            _SESSION = new_session("u2net")
    return _SESSION


def rembg_greymat(path: Path) -> tuple[Image.Image, bool]:
    """Return (composited RGB, ok). ok=False when the model ate a pale garment."""
    from rembg import remove

    im = Image.open(path).convert("RGBA")
    src = np.asarray(im.convert("RGB"))
    cut = remove(im, session=_get_session())
    arr = np.asarray(cut).copy()
    alpha = arr[:, :, 3].astype(np.float32)
    h, w = alpha.shape
    cy0, cy1 = h * 2 // 5, h * 3 // 5
    cx0, cx1 = w * 2 // 5, w * 3 // 5
    center_a = alpha[cy0:cy1, cx0:cx1]
    opaque = float(np.mean(center_a > 128))
    src_center = src[cy0:cy1, cx0:cx1].reshape(-1, 3).astype(np.float32)
    src_mid_l = float(
        np.median(
            0.2126 * src_center[:, 0]
            + 0.7152 * src_center[:, 1]
            + 0.0722 * src_center[:, 2]
        )
    )
    # Pale garment erased → caller should fall back to soft remap / skip
    if src_mid_l >= 200 and opaque < 0.45:
        return im.convert("RGB"), False
    alpha = np.where(alpha < 28, 0.0, alpha)
    arr[:, :, 3] = alpha.astype(np.uint8)
    cut = Image.fromarray(arr, mode="RGBA")
    bg = Image.new("RGBA", cut.size, TARGET_RGB + (255,))
    return Image.alpha_composite(bg, cut).convert("RGB"), True


def process_one(path_str: str) -> tuple[str, str]:
    path = Path(path_str)
    try:
        with Image.open(path) as im:
            rgb = im.convert("RGB")
            arr = np.asarray(rgb)
            bg = studio_bg_color(arr)
            if bg is None:
                return path_str, "skip"
            if already_darkgray(bg):
                return path_str, "skip"
            if needs_rembg(arr, bg):
                out_im, ok = rembg_greymat(path)
                if ok:
                    out = np.asarray(out_im)
                    tag = "rembg"
                else:
                    # Soft remap would paint the white garment grey — leave as-is.
                    return path_str, "skip"
            else:
                out = greymat_array(arr, bg)
                tag = "fast"
            if np.mean(np.abs(out.astype(np.int16) - arr.astype(np.int16))) < 0.6:
                return path_str, "skip"
            Image.fromarray(out, mode="RGB").save(
                path, format="JPEG", quality=92, optimize=True
            )
        return path_str, f"ok:{tag}"
    except Exception as e:
        return path_str, f"fail:{e}"


def greymat_file(path: Path | str) -> str:
    """Greymat a single image in place. Returns status string."""
    return process_one(str(path))[1]


def save_product_image(path: Path | str, data: bytes) -> str:
    """Write downloaded PDP bytes then greymat studio mats in place."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return greymat_file(dest)


def collect_images(dirs: list[str]) -> list[Path]:
    files: list[Path] = []
    for name in dirs:
        root = PRODUCTS / name
        if not root.exists():
            continue
        files.extend(root.rglob("*.jpg"))
        files.extend(root.rglob("*.jpeg"))
        files.extend(root.rglob("*.webp"))
    return sorted({p.resolve() for p in files if p.is_file()})


def greymat_dirs(
    dirs: list[str],
    *,
    workers: int | None = None,
    limit: int = 0,
) -> tuple[int, int, int]:
    """Greymat all images under the given public/products/* dirs.

    Returns (ok, skip, fail).
    """
    files = collect_images(dirs)
    if limit:
        files = files[:limit]
    if not files:
        print(f"candidates=0 dirs={dirs}", flush=True)
        return 0, 0, 0

    n_workers = workers if workers is not None else max(
        2, min(6, (os.cpu_count() or 4) // 2)
    )
    print(f"candidates={len(files)} dirs={dirs} workers={n_workers}", flush=True)

    ok = skip = fail = 0
    with ProcessPoolExecutor(max_workers=max(1, n_workers)) as ex:
        futs = [ex.submit(process_one, str(p)) for p in files]
        done = 0
        for fut in as_completed(futs):
            _, status = fut.result()
            done += 1
            if status.startswith("ok"):
                ok += 1
            elif status == "skip":
                skip += 1
            else:
                fail += 1
                if fail <= 20:
                    print(status, flush=True)
            if done % 200 == 0 or done == len(files):
                print(
                    f"{done}/{len(files)} ok={ok} skip={skip} fail={fail}",
                    flush=True,
                )
    print(f"done ok={ok} skip={skip} fail={fail}", flush=True)
    return ok, skip, fail


# Back-compat aliases so existing scrapers / push scripts keep importing names.
whiten_file = greymat_file
whiten_dirs = greymat_dirs
whiten_array = greymat_array  # type: ignore[assignment]
