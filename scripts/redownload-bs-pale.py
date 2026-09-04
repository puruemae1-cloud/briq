#!/usr/bin/env python3
"""Re-download Belstaff pale colourway PDP images from Shopify CDN (no greymat).

Prior rembg/soft greymat washed white trainers (Walton) and pale apparel onto
#e7e7e7. Restore pristine CDN bytes — same approach as redownload-ax-white.py.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from bs_pale_colour import is_pale_bs_row, pale_bs_handles  # noqa: E402
from studio_whiten import save_product_image  # noqa: E402

RAW = ROOT / "src/data/bs/bs-catalog-raw.json"
IMG_ROOT = ROOT / "public/products/bs-pdp"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
WORKERS = 8


def cdn_url(src: str, width: int = 1600) -> str:
    if not src:
        return src
    if src.startswith("//"):
        src = "https:" + src
    if "width=" in src:
        return src
    sep = "&" if "?" in src else "?"
    return f"{src}{sep}width={width}"


def fetch_bytes(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": UA,
                "Accept": "image/*",
                "Referer": "https://belstaff.com/",
            },
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            data = r.read()
        return data if data and len(data) >= 800 else None
    except Exception:
        return None


def download_handle(handle: str, urls: list[str]) -> tuple[str, int, int]:
    urls = [u for u in urls if u]
    if not urls:
        return handle, 0, 1
    dest_dir = IMG_ROOT / handle
    dest_dir.mkdir(parents=True, exist_ok=True)
    ok = fail = 0
    for i, url in enumerate(urls[:8], start=1):
        data = fetch_bytes(cdn_url(url, 1600))
        if not data:
            fail += 1
            continue
        save_product_image(dest_dir / f"{i}.jpg", data, greymat=False)
        ok += 1
    return handle, ok, fail


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--only",
        nargs="*",
        default=[],
        help="Optional handles to refresh (default: all pale colourways)",
    )
    ap.add_argument("--workers", type=int, default=WORKERS)
    args = ap.parse_args()

    raw = json.loads(RAW.read_text())
    products = [p for p in (raw.get("products") or []) if isinstance(p, dict)]
    by_handle = {
        str(p.get("handle") or ""): p for p in products if p.get("handle")
    }

    if args.only:
        handles = [h for h in args.only if h in by_handle]
    else:
        handles = sorted(pale_bs_handles(raw))

    jobs: list[tuple[str, list[str]]] = []
    for h in handles:
        row = by_handle.get(h) or {}
        if not is_pale_bs_row(row) and not args.only:
            continue
        urls = list(row.get("images") or [])
        jobs.append((h, urls))

    print(
        f"BS pale redownload handles={len(jobs)} workers={args.workers}",
        flush=True,
    )
    total_ok = total_fail = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = [ex.submit(download_handle, h, urls) for h, urls in jobs]
        done = 0
        for fut in as_completed(futs):
            key, ok, fail = fut.result()
            total_ok += ok
            total_fail += fail
            done += 1
            if done <= 15 or done % 25 == 0 or done == len(jobs):
                print(
                    f"{done}/{len(jobs)} {key} ok={ok} fail={fail} "
                    f"(total_ok={total_ok} fail={total_fail})",
                    flush=True,
                )
            time.sleep(0.01)
    print(
        f"done handles={len(jobs)} imgs_ok={total_ok} fail={total_fail}",
        flush=True,
    )
    if total_ok == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
