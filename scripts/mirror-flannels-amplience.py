#!/usr/bin/env python3
"""Mirror Flannels Amplience hotlinks onto /products/fl-pdp for the Briq CDN.

Korean networks often stall on cdn.media.amplience.net (Frasers UK). ProductImage
gives up after 4.5s and shows the Briq mark. Rewrite every catalogue URL to a
local /products/fl-pdp/<id>/N.jpg path, then push with push-product-images-tag.py.

  python3 scripts/mirror-flannels-amplience.py
  python3 scripts/mirror-flannels-amplience.py --limit 100  # homepage subset
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from curl_cffi import requests as cffi_requests

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "src/data/fl/fl-catalog.json"
OUT = ROOT / "public/products/fl-pdp"
MIN_BYTES = 2048
WORKERS = 12
# Keep gallery sharp but avoid shipping 1600px originals when 1200 is enough.
TARGET_W = 1200
TARGET_H = 1500

AMPLIENCE_HOST = "cdn.media.amplience.net"


def is_amplience(url: str | None) -> bool:
    return isinstance(url, str) and AMPLIENCE_HOST in url


def resize_amplience(url: str) -> str:
    """Force a modest packshot size for CDN storage."""
    parts = urlparse(url)
    q = parse_qs(parts.query, keep_blank_values=True)
    q["w"] = [str(TARGET_W)]
    q["h"] = [str(TARGET_H)]
    q.setdefault("fmt", ["jpg"])
    q.setdefault("sm", ["scaleFit"])
    # parse_qs values are lists; flatten for urlencode doseq
    new_q = urlencode({k: v[-1] if isinstance(v, list) else v for k, v in q.items()})
    return urlunparse(parts._replace(query=new_q))


def collect_jobs(products: list[dict]) -> list[tuple[str, int, str]]:
    """(product_id, 1-based index, remote_url) — stable gallery order."""
    jobs: list[tuple[str, int, str]] = []
    for p in products:
        pid = str(p.get("id") or "").strip()
        if not pid:
            continue
        ordered: list[str] = []
        seen: set[str] = set()

        def add(u: str | None) -> None:
            if not is_amplience(u):
                return
            assert u is not None
            if u in seen:
                return
            seen.add(u)
            ordered.append(u)

        add(p.get("image"))
        add(p.get("hoverImage"))
        for u in p.get("images") or []:
            add(u if isinstance(u, str) else None)
        for sec in p.get("storySections") or []:
            if isinstance(sec, dict):
                add(sec.get("image"))
        for v in p.get("variants") or []:
            if not isinstance(v, dict):
                continue
            add(v.get("image"))
            add(v.get("hoverImage"))
            for u in v.get("images") or []:
                add(u if isinstance(u, str) else None)
        for i, u in enumerate(ordered, start=1):
            jobs.append((pid, i, u))
    return jobs


def download_one(pid: str, idx: int, url: str) -> tuple[str, int, bool, str]:
    dest = OUT / pid / f"{idx}.jpg"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size >= MIN_BYTES:
        return pid, idx, True, "cached"
    src = resize_amplience(url)
    last_err = ""
    for attempt in range(4):
        try:
            r = cffi_requests.get(
                src,
                timeout=45,
                impersonate="chrome",
                headers={"Accept": "image/*,*/*", "Referer": "https://www.flannels.com/"},
            )
            if r.status_code != 200 or len(r.content) < MIN_BYTES:
                last_err = f"http {r.status_code} bytes={len(r.content)}"
                time.sleep(0.4 * (attempt + 1))
                continue
            # Basic JPEG/WebP magic
            head = r.content[:3]
            if head != b"\xff\xd8\xff" and r.content[:4] != b"RIFF":
                # Amplience sometimes returns webp/avif; accept if large enough PNG
                if r.content[:8] != b"\x89PNG\r\n\x1a\n" and len(r.content) < MIN_BYTES:
                    last_err = "bad magic"
                    time.sleep(0.4 * (attempt + 1))
                    continue
            dest.write_bytes(r.content)
            return pid, idx, True, f"ok {len(r.content)}"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            time.sleep(0.5 * (attempt + 1))
    return pid, idx, False, last_err


def rewrite_url(pid: str, remote: str, mapping: dict[str, str]) -> str:
    return mapping.get(remote, remote)


def rewrite_catalog(products: list[dict], mapping: dict[tuple[str, str], str]) -> int:
    """mapping key = (pid, remote_url) → local path."""
    changed = 0

    def map_one(pid: str, u: str | None) -> str | None:
        if not isinstance(u, str):
            return u
        key = (pid, u)
        if key in mapping:
            return mapping[key]
        return u

    for p in products:
        pid = str(p.get("id") or "")
        before = (p.get("image"), p.get("hoverImage"), tuple(p.get("images") or []))
        if is_amplience(p.get("image")):
            p["image"] = map_one(pid, p.get("image"))
        if is_amplience(p.get("hoverImage")):
            p["hoverImage"] = map_one(pid, p.get("hoverImage"))
        if isinstance(p.get("images"), list):
            p["images"] = [map_one(pid, u) if isinstance(u, str) else u for u in p["images"]]
        for sec in p.get("storySections") or []:
            if isinstance(sec, dict) and is_amplience(sec.get("image")):
                sec["image"] = map_one(pid, sec.get("image"))
        # Primary must stay first gallery frame when rewritten
        if isinstance(p.get("images"), list) and p["images"]:
            if not p.get("image") or is_amplience(p.get("image")):
                p["image"] = p["images"][0]
            if len(p["images"]) > 1 and (
                not p.get("hoverImage") or is_amplience(p.get("hoverImage"))
            ):
                p["hoverImage"] = p["images"][1]
        for v in p.get("variants") or []:
            if not isinstance(v, dict):
                continue
            if is_amplience(v.get("image")):
                v["image"] = map_one(pid, v.get("image"))
            if is_amplience(v.get("hoverImage")):
                v["hoverImage"] = map_one(pid, v.get("hoverImage"))
            if isinstance(v.get("images"), list):
                v["images"] = [
                    map_one(pid, u) if isinstance(u, str) else u for u in v["images"]
                ]
        after = (p.get("image"), p.get("hoverImage"), tuple(p.get("images") or []))
        if before != after:
            changed += 1
    return changed


def still_amplience(products: list[dict]) -> int:
    n = 0
    for p in products:
        for u in [p.get("image"), p.get("hoverImage"), *(p.get("images") or [])]:
            if is_amplience(u if isinstance(u, str) else None):
                n += 1
        for v in p.get("variants") or []:
            if not isinstance(v, dict):
                continue
            for u in [v.get("image"), v.get("hoverImage"), *(v.get("images") or [])]:
                if is_amplience(u if isinstance(u, str) else None):
                    n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="Only first N products")
    ap.add_argument("--download-only", action="store_true")
    ap.add_argument("--rewrite-only", action="store_true")
    ap.add_argument("--workers", type=int, default=WORKERS)
    args = ap.parse_args()

    products = json.loads(CATALOG.read_text())
    if not isinstance(products, list):
        print("catalog is not a list", file=sys.stderr)
        return 1
    if args.limit:
        products = products[: args.limit]

    jobs = collect_jobs(products)
    print(f"products={len(products)} jobs={len(jobs)} out={OUT}", flush=True)

    mapping: dict[tuple[str, str], str] = {}
    if not args.rewrite_only:
        ok = fail = 0
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = {
                pool.submit(download_one, pid, idx, url): (pid, idx, url)
                for pid, idx, url in jobs
            }
            done = 0
            for fut in as_completed(futs):
                pid, idx, url = futs[fut]
                _pid, _idx, success, msg = fut.result()
                done += 1
                local = f"/products/fl-pdp/{pid}/{idx}.jpg"
                if success:
                    ok += 1
                    mapping[(pid, url)] = local
                else:
                    fail += 1
                    print(f"FAIL {pid}#{idx}: {msg}", flush=True)
                if done % 50 == 0 or done == len(jobs):
                    print(f"… {done}/{len(jobs)} ok={ok} fail={fail}", flush=True)
        print(f"download done ok={ok} fail={fail}", flush=True)
        if fail:
            print("aborting rewrite — fix failed downloads first", file=sys.stderr)
            return 2
    else:
        # Rebuild mapping from files already on disk
        for pid, idx, url in jobs:
            dest = OUT / pid / f"{idx}.jpg"
            if dest.is_file() and dest.stat().st_size >= MIN_BYTES:
                mapping[(pid, url)] = f"/products/fl-pdp/{pid}/{idx}.jpg"

    if args.download_only:
        return 0

    # Full catalog rewrite (not just --limit slice)
    all_products = json.loads(CATALOG.read_text())
    # Extend mapping for all products if we only downloaded a subset — only rewrite those we have
    if args.limit:
        # Also map from any files already present for the rest
        for p in all_products:
            pid = str(p.get("id") or "")
            jobs_p = collect_jobs([p])
            for pid2, idx, url in jobs_p:
                if (pid2, url) in mapping:
                    continue
                dest = OUT / pid2 / f"{idx}.jpg"
                if dest.is_file() and dest.stat().st_size >= MIN_BYTES:
                    mapping[(pid2, url)] = f"/products/fl-pdp/{pid2}/{idx}.jpg"

    changed = rewrite_catalog(all_products, mapping)
    left = still_amplience(all_products)
    CATALOG.write_text(json.dumps(all_products, ensure_ascii=False, indent=2) + "\n")
    print(f"rewrote products={changed} amplience_urls_left={left}", flush=True)
    return 0 if left == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
