#!/usr/bin/env python3
"""Download Arc'teryx colourways that are in PDP cache but missing on disk.

Prevents shop 404s when catalog/build references ultima/mongoose/… but only
one colour (e.g. black) was previously saved under public/products/ax*-pdp.

  python3 scripts/repair-ax-missing-colour-images.py
  python3 scripts/repair-ax-missing-colour-images.py --limit 20
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ax_image_common import save_colour_gallery, slugify  # noqa: E402

CACHE_SPECS: list[tuple[Path, Path]] = [
    (ROOT / "src/data/ax/ax-apparel-pdp-cache.json", ROOT / "public/products/axa-pdp"),
    (ROOT / "src/data/ax/ax-gear-pdp-cache.json", ROOT / "public/products/axg-pdp"),
    (ROOT / "src/data/ax/ax-pdp-cache.json", ROOT / "public/products/ax-pdp"),
]

OUTLET_RAW = ROOT / "src/data/ax/ax-outlet-raw.json"
OUTLET_IMG = ROOT / "public/products/axo-pdp"
WORKERS = 10


def primary_ok(dest: Path) -> bool:
    p = dest / "1.jpg"
    return p.is_file() and p.stat().st_size >= 800


def jobs_from_cache(cache_path: Path, img_root: Path) -> list[tuple[Path, list[str]]]:
    if not cache_path.exists():
        return []
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
            dest = img_root / str(pid) / cslug
            if primary_ok(dest):
                continue
            clean = [u for u in urls if u and "placeholder" not in u.lower()]
            if clean:
                jobs.append((dest, clean))
    return jobs


def jobs_from_outlet() -> list[tuple[Path, list[str]]]:
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
            dest = OUTLET_IMG / pid / slugify(color)
            if primary_ok(dest):
                continue
            urls: list[str] = []
            for key in ("profile", "hover", "thumb"):
                u = (c.get(key) or "").strip()
                if u and u not in urls:
                    urls.append(u)
            if urls:
                jobs.append((dest, urls))
    return jobs


def run_job(dest: Path, urls: list[str]) -> tuple[str, int, int]:
    ok, fail = save_colour_gallery(dest, urls, greymat=False)
    return str(dest.relative_to(ROOT)), ok, fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=WORKERS)
    args = ap.parse_args()

    jobs: list[tuple[Path, list[str]]] = []
    for cache_path, img_root in CACHE_SPECS:
        jobs.extend(jobs_from_cache(cache_path, img_root))
    jobs.extend(jobs_from_outlet())
    if args.limit:
        jobs = jobs[: args.limit]

    print(f"AX missing colourways to fetch: {len(jobs)}", flush=True)
    if not jobs:
        return 0

    total_ok = total_fail = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = [ex.submit(run_job, d, u) for d, u in jobs]
        done = 0
        for fut in as_completed(futs):
            key, ok, fail = fut.result()
            total_ok += ok
            total_fail += fail
            done += 1
            if done <= 15 or done % 25 == 0 or done == len(jobs):
                print(
                    f"{done}/{len(jobs)} {key} ok={ok} fail={fail}",
                    flush=True,
                )
            time.sleep(0.002)

    still = [d for d, _ in jobs if not primary_ok(d)]
    print(
        f"done fetched_ok_frames={total_ok} fail_frames={total_fail} "
        f"still_missing_primary={len(still)}",
        flush=True,
    )
    return 0 if not still else 1


if __name__ == "__main__":
    raise SystemExit(main())
