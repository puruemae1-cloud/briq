#!/usr/bin/env python3
"""Re-download Arc'teryx pale apparel colourways from official CDN (no greymat).

Prior rembg/soft greymat flattened White Light / Arctic Silk / Sea Salt /
Solitude / Moondrop / Atmos garments onto #e7e7e7. Restore pristine
images.arcteryx.com bytes — same approach as redownload-ps-white.py.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ax_pale_colour import is_pale_ax_colour, pale_axa_colour_dirs, slugify  # noqa: E402
from studio_whiten import save_product_image  # noqa: E402

CACHE = ROOT / "src/data/ax/ax-apparel-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/axa-pdp"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
WORKERS = 10


def fetch_bytes(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Accept": "image/*"}
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            data = r.read()
        return data if data and len(data) >= 800 else None
    except Exception:
        return None


def download_colour(pid: str, color: str, urls: list[str]) -> tuple[str, int, int]:
    urls = [u for u in urls if u and "placeholder" not in u.lower()]
    if not urls:
        return f"{pid}/{color}", 0, 1
    cslug = slugify(color)
    dest_dir = IMG_ROOT / pid / cslug
    dest_dir.mkdir(parents=True, exist_ok=True)
    ok = fail = 0
    for i, url in enumerate(urls[:8], start=1):
        data = fetch_bytes(url)
        if not data:
            fail += 1
            continue
        path = dest_dir / f"{i}.jpg"
        save_product_image(path, data, greymat=False)
        ok += 1
        # Official Hover frame → hover.jpg when present in the gallery.
        if i == 2 or re.search(r"[-_]Hover\.", url, re.I):
            save_product_image(dest_dir / "hover.jpg", data, greymat=False)
    # PLP thumb = primary packshot
    primary = dest_dir / "1.jpg"
    if primary.exists() and primary.stat().st_size > 800:
        save_product_image(
            dest_dir / "thumb.jpg", primary.read_bytes(), greymat=False
        )
    return f"{pid}/{cslug}", ok, fail


def main() -> None:
    cache = json.loads(CACHE.read_text())
    jobs: list[tuple[str, str, list[str]]] = []
    for pid, row in cache.items():
        if not isinstance(row, dict):
            continue
        colours = row.get("colourImages") or {}
        if not isinstance(colours, dict):
            continue
        for color, urls in colours.items():
            if not is_pale_ax_colour(color=str(color)):
                continue
            if not isinstance(urls, list) or not urls:
                continue
            jobs.append((str(pid), str(color), list(urls)))

    pale_dirs = pale_axa_colour_dirs(cache)
    print(
        f"AX pale redownload colourways={len(jobs)} "
        f"dirs={len(pale_dirs)} workers={WORKERS}",
        flush=True,
    )
    total_ok = total_fail = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(download_colour, *job) for job in jobs]
        done = 0
        for fut in as_completed(futs):
            key, ok, fail = fut.result()
            total_ok += ok
            total_fail += fail
            done += 1
            if done <= 12 or done % 20 == 0 or done == len(jobs):
                print(
                    f"{done}/{len(jobs)} {key} ok={ok} fail={fail} "
                    f"(total_ok={total_ok} fail={total_fail})",
                    flush=True,
                )
            time.sleep(0.01)
    print(
        f"done colourways={len(jobs)} imgs_ok={total_ok} fail={total_fail}",
        flush=True,
    )
    if total_ok == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
