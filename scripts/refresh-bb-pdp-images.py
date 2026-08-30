#!/usr/bin/env python3
"""Re-fetch Burberry PDPs for colourways with thin galleries and restore Scene7 frames.

Updates:
  - public/products/bb-pdp/<id>/*.jpg
  - src/data/bb/bb-catalog-raw.json remoteImages/images
  - src/data/bb/bb-catalog.json variant/product images
  - src/data/bb/bb-pdp-cache.json

Keeps bb-catalog.ts as a thin JSON import (never inline the catalog).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "src/data/bb/bb-catalog-raw.json"
CAT = ROOT / "src/data/bb/bb-catalog.json"
OUT_TS = ROOT / "src/data/bb/bb-catalog.ts"
PDP_CACHE = ROOT / "src/data/bb/bb-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/bb-pdp"
BASE = "https://uk.burberry.com"
MAX_IMG = 12
WORKERS = 8

spec = importlib.util.spec_from_file_location("bbw", ROOT / "scripts/scrape-bb-women.py")
bbw = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bbw)


def write_thin_ts() -> None:
    OUT_TS.write_text(
        "/** Auto-generated Burberry catalogue — do not edit by hand. */\n"
        'import type { Product } from "@/data/products";\n'
        'import data from "./bb-catalog.json";\n\n'
        "export const bbCatalogProducts = data as unknown as Product[];\n"
    )


def folder_from_images(imgs: list[str]) -> str | None:
    for img in imgs or []:
        parts = str(img).split("/")
        if "bb-pdp" in parts:
            i = parts.index("bb-pdp")
            if i + 1 < len(parts):
                return parts[i + 1]
    return None


def collect_targets(cat: list[dict], *, max_imgs: int, only_ids: set[str] | None) -> list[dict]:
    """Unique colourway folders that currently have <= max_imgs local frames."""
    seen: set[str] = set()
    out: list[dict] = []
    for p in cat:
        pid = p.get("id") or ""
        if only_ids and pid not in only_ids and not any(
            folder_from_images(v.get("images") or []) in only_ids for v in (p.get("variants") or [])
        ):
            # allow only_ids to be product ids OR scene7 colour ids
            pass
        for v in p.get("variants") or []:
            imgs = v.get("images") or []
            folder = folder_from_images(imgs)
            if not folder:
                continue
            if folder in seen:
                continue
            if only_ids and pid not in only_ids and folder not in only_ids:
                continue
            if len(imgs) > max_imgs:
                continue
            url = v.get("sourceUrl") or p.get("sourceUrl") or ""
            if not url:
                continue
            seen.add(folder)
            out.append(
                {
                    "productId": pid,
                    "folder": folder,
                    "colorKey": v.get("colorKey"),
                    "url": url,
                    "oldCount": len(imgs),
                }
            )
    return out


def refresh_one(job: dict) -> dict:
    folder = job["folder"]
    url = job["url"]
    if not url.startswith("http"):
        url = f"{BASE}{url}"
    try:
        html = bbw.fetch(url)
        pdp = bbw.extract_pdp(html, folder)
        remotes = list(dict.fromkeys(pdp.get("images") or []))
        # Always re-download (force) so disk matches official gallery.
        local: list[str] = []
        if remotes:
            # Temporarily clear cache entry images so download_images rewrites.
            dest = IMG_ROOT / folder
            if dest.exists():
                for old in dest.glob("*.jpg"):
                    # keep until replaced; download_images skips existing >1000B
                    # so remove first when we have more remotes than local
                    pass
            # Force overwrite when remote count differs or oldCount low
            for i, remote in enumerate(remotes[:MAX_IMG], start=1):
                out = dest / f"{i}.jpg"
                out.parent.mkdir(parents=True, exist_ok=True)
                fetch_url = remote
                if "burberry.com/is/image" in remote and "?" not in remote:
                    fetch_url = f"{remote}?$BBY_V2_SL_3x4$&wid=1200&hei=1600&fmt=jpg"
                # overwrite
                try:
                    import urllib.request

                    req = urllib.request.Request(
                        fetch_url,
                        headers={"User-Agent": getattr(bbw, "UA", "Mozilla/5.0")},
                    )
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        data = resp.read()
                    if len(data) > 1000:
                        out.write_bytes(data)
                        local.append(f"/products/bb-pdp/{folder}/{i}.jpg")
                except Exception as e:  # noqa: BLE001
                    return {**job, "ok": False, "error": f"img {i}: {e}", "remotes": remotes, "local": local}
            # remove leftover higher-index files only when we successfully saved frames
            if local:
                for old in dest.glob("*.jpg"):
                    try:
                        idx = int(old.stem)
                    except ValueError:
                        continue
                    if idx > len(local):
                        old.unlink(missing_ok=True)
        return {
            **job,
            "ok": True,
            "remotes": remotes,
            "local": local,
            "newCount": len(local),
            "pdp": pdp,
        }
    except Exception as e:  # noqa: BLE001
        return {**job, "ok": False, "error": str(e), "remotes": [], "local": []}


def apply_to_raw(raw: dict, results: list[dict]) -> int:
    by = {str(p.get("id")): p for p in (raw.get("products") or []) if p.get("id")}
    n = 0
    for r in results:
        if not r.get("ok"):
            continue
        folder = r["folder"]
        local = r.get("local") or []
        remotes = r.get("remotes") or []
        if not local:
            continue
        p = by.get(folder)
        if not p:
            continue
        if len(local) <= len(p.get("images") or []) and len(local) <= 2:
            # no improvement
            if len(local) == len(p.get("images") or []):
                continue
        p["images"] = local
        p["image"] = local[0]
        p["remoteImages"] = remotes
        n += 1
    return n


def apply_to_catalog(cat: list[dict], results: list[dict]) -> int:
    by_folder = {r["folder"]: r for r in results if r.get("ok") and r.get("local")}
    n = 0
    for p in cat:
        changed = False
        for v in p.get("variants") or []:
            folder = folder_from_images(v.get("images") or [])
            r = by_folder.get(folder or "")
            if not r:
                continue
            local = r["local"]
            if not local:
                continue
            if local != (v.get("images") or []):
                v["images"] = local
                v["image"] = local[0]
                changed = True
                n += 1
        if changed:
            # refresh product-level images from first variant of each colour
            # keep first variant images as product hero set
            first = (p.get("variants") or [{}])[0]
            if first.get("images"):
                p["images"] = first["images"]
                p["image"] = first["images"][0]
    return n


def apply_to_cache(cache: dict, results: list[dict]) -> None:
    for r in results:
        if not r.get("ok"):
            continue
        folder = r["folder"]
        pdp = r.get("pdp") or {}
        if not pdp:
            continue
        pdp = dict(pdp)
        pdp["localImages"] = r.get("local") or []
        pdp["images"] = r.get("remotes") or pdp.get("images") or []
        cache[folder] = pdp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-imgs", type=int, default=2, help="refresh colourways with <= N images")
    ap.add_argument("--only", default="", help="comma product ids or colour folders")
    ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    only = {x.strip() for x in args.only.split(",") if x.strip()} or None

    cat = json.loads(CAT.read_text())
    raw = json.loads(RAW.read_text()) if RAW.is_file() else {"products": []}
    cache = json.loads(PDP_CACHE.read_text()) if PDP_CACHE.is_file() else {}

    jobs = collect_targets(cat, max_imgs=args.max_imgs, only_ids=only)
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"targets={len(jobs)} max_imgs<={args.max_imgs} workers={args.workers}", flush=True)

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(refresh_one, j) for j in jobs]
        done = 0
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            done += 1
            if r.get("ok"):
                print(
                    f"[{done}/{len(jobs)}] {r['folder']} {r.get('oldCount')}→{r.get('newCount')} {r.get('colorKey')}",
                    flush=True,
                )
            else:
                print(f"[{done}/{len(jobs)}] FAIL {r.get('folder')} {r.get('error')}", flush=True)
            if done % 25 == 0:
                time.sleep(0.5)

    improved = sum(1 for r in results if r.get("ok") and (r.get("newCount") or 0) > (r.get("oldCount") or 0))
    same = sum(1 for r in results if r.get("ok") and (r.get("newCount") or 0) == (r.get("oldCount") or 0))
    fail = sum(1 for r in results if not r.get("ok"))
    print(f"summary improved={improved} same={same} fail={fail}", flush=True)

    n_raw = apply_to_raw(raw, results)
    n_cat = apply_to_catalog(cat, results)
    apply_to_cache(cache, results)
    RAW.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n")
    CAT.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n")
    PDP_CACHE.write_text(json.dumps(cache, ensure_ascii=False) + "\n")
    write_thin_ts()
    print(f"updated raw={n_raw} catalog_variants={n_cat} ts={OUT_TS.stat().st_size}B", flush=True)


if __name__ == "__main__":
    main()
