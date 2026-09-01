#!/usr/bin/env python3
"""Re-download all Arc'teryx PDP images from official CDN (no greymat/rembg).

Arc'teryx packshots use warm tan / light-grey studio mats — forcing #e7e7e7
via rembg flattened gear harnesses and footwear. Restore pristine
images.arcteryx.com bytes for axa / axg / ax / axo trees.
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ax_image_common import save_colour_gallery, slugify  # noqa: E402

WORKERS = 12

CACHE_SPECS: list[tuple[Path, Path]] = [
    (ROOT / "src/data/ax/ax-apparel-pdp-cache.json", ROOT / "public/products/axa-pdp"),
    (ROOT / "src/data/ax/ax-gear-pdp-cache.json", ROOT / "public/products/axg-pdp"),
    (ROOT / "src/data/ax/ax-pdp-cache.json", ROOT / "public/products/ax-pdp"),
]

OUTLET_RAW = ROOT / "src/data/ax/ax-outlet-raw.json"
OUTLET_IMG = ROOT / "public/products/axo-pdp"


def jobs_from_cache(cache_path: Path, img_root: Path) -> list[tuple[Path, list[str]]]:
    cache = json.loads(cache_path.read_text())
    jobs: list[tuple[Path, list[str]]] = []
    for pid, row in cache.items():
        if not isinstance(row, dict):
            continue
        colours = row.get("colourImages") or {}
        if not isinstance(colours, dict):
            continue
        for color, urls in colours.items():
            if not isinstance(urls, list) or not urls:
                continue
            cslug = slugify(str(color))
            jobs.append((img_root / str(pid) / cslug, list(urls)))
    return jobs


def jobs_from_outlet_raw() -> list[tuple[Path, list[str]]]:
    if not OUTLET_RAW.exists():
        return []
    raw = json.loads(OUTLET_RAW.read_text())
    jobs: list[tuple[Path, list[str]]] = []
    for p in raw.get("products") or []:
        pid = str(p.get("id") or "")
        if not pid:
            continue
        for c in p.get("colours") or []:
            if not isinstance(c, dict):
                continue
            color = str(c.get("color") or "")
            if not color:
                continue
            urls: list[str] = []
            for key in ("profile", "hover", "thumb"):
                u = (c.get(key) or "").strip()
                if u and u not in urls:
                    urls.append(u)
            if not urls:
                continue
            jobs.append((OUTLET_IMG / pid / slugify(color), urls))
    return jobs


def run_job(dest_dir: Path, urls: list[str]) -> tuple[str, int, int]:
    ok, fail = save_colour_gallery(dest_dir, urls, greymat=False)
    return str(dest_dir.relative_to(ROOT)), ok, fail


def main() -> None:
    jobs: list[tuple[Path, list[str]]] = []
    for cache_path, img_root in CACHE_SPECS:
        jobs.extend(jobs_from_cache(cache_path, img_root))
    jobs.extend(jobs_from_outlet_raw())
    print(f"AX official redownload colourways={len(jobs)} workers={WORKERS}", flush=True)
    total_ok = total_fail = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(run_job, d, u) for d, u in jobs]
        done = 0
        for fut in as_completed(futs):
            key, ok, fail = fut.result()
            total_ok += ok
            total_fail += fail
            done += 1
            if done <= 10 or done % 50 == 0 or done == len(jobs):
                print(
                    f"{done}/{len(jobs)} {key} ok={ok} fail={fail} "
                    f"(total_ok={total_ok} fail={total_fail})",
                    flush=True,
                )
            time.sleep(0.005)
    print(f"done colourways={len(jobs)} imgs_ok={total_ok} fail={total_fail}", flush=True)
    if total_ok == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
