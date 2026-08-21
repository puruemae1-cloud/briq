#!/usr/bin/env python3
"""Re-download catalog PDP images that are missing on disk.

Prevents shipping a catalogue that points at `/products/*-pdp/...` paths which
never made it onto the `product-images` tag (broken cards on Vercel/jsDelivr).

Looks up official CDN URLs from the brand raw scrape JSON, writes files under
`public/products/`, then exit 0. Pair with `push-product-images-tag.py` +
`verify-product-images.py --remote` (hard fail — do not `|| true`).

  python3 scripts/repair-missing-catalog-images.py --brand ch
  python3 scripts/repair-missing-catalog-images.py --brand ch --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from curl_cffi import requests as cffi_requests

ROOT = Path(__file__).resolve().parents[1]

BRAND_CFG: dict[str, dict] = {
    "ch": {
        "catalog": ROOT / "src/data/ch/ch-catalog.json",
        "raw_glob": "src/data/ch/*catalog-raw.json",
        "referer": "https://www.chanel.com/gb/",
        "pdp_prefix": "/products/ch-pdp/",
    },
    "pr": {
        "catalog": ROOT / "src/data/pr/pr-catalog.json",
        "raw_glob": "src/data/pr/*catalog-raw.json",
        "referer": "https://www.prada.com/gb/en/",
        "pdp_prefix": "/products/pr-pdp/",
    },
    "gc": {
        "catalog": ROOT / "src/data/gc/gc-catalog.json",
        "raw_glob": "src/data/gc/*raw*.json",
        "referer": "https://www.gucci.com/",
        "pdp_prefix": "/products/gc-pdp/",
    },
}


def load_catalog(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    return data if isinstance(data, list) else list(data.get("products") or [])


def sku_from_image(web: str, prefix: str) -> str | None:
    if not web.startswith(prefix):
        return None
    rest = web[len(prefix) :]
    return rest.split("/", 1)[0] or None


def collect_remote_urls(raw_glob: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for path in sorted(ROOT.glob(raw_glob)):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        prods = data.get("products") if isinstance(data, dict) else data
        if not isinstance(prods, list):
            continue
        for row in prods:
            if not isinstance(row, dict):
                continue
            code = str(
                row.get("productCode") or row.get("sku") or row.get("id") or ""
            ).strip()
            if not code:
                continue
            urls = [
                u
                for u in (row.get("images") or [])
                if isinstance(u, str) and u.startswith("http")
            ]
            if urls:
                # Prefer richer gallery if duplicate SKUs across raw files
                prev = out.get(code) or []
                if len(urls) >= len(prev):
                    out[code] = urls
    return out


def missing_skus(products: list[dict], prefix: str) -> dict[str, list[str]]:
    """sku → list of missing web paths under that sku folder."""
    need: dict[str, list[str]] = {}
    for p in products:
        paths: list[str] = []
        for key in ("image", "hoverImage"):
            v = p.get(key)
            if isinstance(v, str) and v.startswith(prefix):
                paths.append(v)
        for v in p.get("images") or []:
            if isinstance(v, str) and v.startswith(prefix):
                paths.append(v)
        for web in paths:
            sku = sku_from_image(web, prefix)
            if not sku:
                continue
            disk = ROOT / "public" / web.lstrip("/")
            if disk.is_file() and disk.stat().st_size > 2048:
                continue
            need.setdefault(sku, [])
            if web not in need[sku]:
                need[sku].append(web)
    return need


def download_sku(
    sku: str,
    remote_urls: list[str],
    missing_webs: list[str],
    *,
    referer: str,
    prefix: str,
    dry_run: bool,
) -> tuple[str, int, str]:
    if not remote_urls:
        return sku, 0, "no remote urls in raw"
    # Map 1.jpg → remote[0], etc.
    wanted_idx: set[int] = set()
    for web in missing_webs:
        name = web.rsplit("/", 1)[-1]
        if name.endswith(".jpg") and name[:-4].isdigit():
            wanted_idx.add(int(name[:-4]))
    if not wanted_idx:
        wanted_idx = {i for i in range(1, min(9, len(remote_urls) + 1))}

    if dry_run:
        return sku, len(wanted_idx), "dry-run"

    dest_dir = ROOT / "public" / prefix.strip("/") / sku
    dest_dir.mkdir(parents=True, exist_ok=True)
    s = cffi_requests.Session()
    ok = 0
    for i in sorted(wanted_idx):
        if i < 1 or i > len(remote_urls):
            continue
        url = remote_urls[i - 1]
        dest = dest_dir / f"{i}.jpg"
        if dest.is_file() and dest.stat().st_size > 2048:
            ok += 1
            continue
        try:
            r = s.get(
                url,
                headers={"Accept": "image/*,*/*", "Referer": referer},
                impersonate="chrome124",
                timeout=90,
            )
            if r.status_code != 200 or len(r.content) < 1500:
                return sku, ok, f"bad HTTP {r.status_code} #{i}"
            dest.write_bytes(r.content)
            ok += 1
            time.sleep(0.04)
        except Exception as e:
            return sku, ok, f"{type(e).__name__}: {e}"
    return sku, ok, "ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", required=True, choices=sorted(BRAND_CFG))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    cfg = BRAND_CFG[args.brand]
    catalog_path: Path = cfg["catalog"]
    if not catalog_path.is_file():
        print(f"missing catalog {catalog_path}", flush=True)
        return 1

    products = load_catalog(catalog_path)
    need = missing_skus(products, cfg["pdp_prefix"])
    if not need:
        print(f"{args.brand}: all catalog images present locally", flush=True)
        return 0

    remotes = collect_remote_urls(cfg["raw_glob"])
    print(f"{args.brand}: repairing {len(need)} SKUs missing on disk", flush=True)

    failed = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = [
            ex.submit(
                download_sku,
                sku,
                remotes.get(sku) or remotes.get(sku.lower()) or [],
                webs,
                referer=cfg["referer"],
                prefix=cfg["pdp_prefix"],
                dry_run=args.dry_run,
            )
            for sku, webs in sorted(need.items())
        ]
        for fut in as_completed(futs):
            sku, n, msg = fut.result()
            print(f"  {sku}: {n} files ({msg})", flush=True)
            if msg not in {"ok", "dry-run"} and n == 0:
                failed += 1

    if failed:
        print(f"ERROR: {failed} SKUs could not be repaired", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
