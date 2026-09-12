#!/usr/bin/env python3
"""Backfill missing Celine PDP images via official SFCC Product-Variation.

Fills products that currently fall back to the (wrong) sandal placeholder.
Updates matching rows in ce-*-catalog-raw.json and downloads into public/products/ce-pdp/.

  python3 scripts/repair-ce-missing-images.py
  python3 scripts/repair-ce-missing-images.py --category bags
  python3 scripts/repair-ce-missing-images.py --limit 40
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from celine_common import (  # noqa: E402
    SFCC_VARIATION,
    UA,
    load_json,
    materialize_images,
    save_json,
    slugify,
)
from celine_config import celine_raw_paths  # noqa: E402

OUT_JSON = ROOT / "src/data/ce/ce-catalog.json"


def sfcc_image_urls(pid: str) -> list[str]:
    sku = (pid or "").strip()
    if not sku:
        return []
    url = f"{SFCC_VARIATION}?{urllib.parse.urlencode({'pid': sku})}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = json.loads(resp.read().decode("utf-8", "ignore"))
    except Exception as e:
        print(f"  sfcc fail {sku}: {e}", flush=True)
        return []
    prod = data.get("product") if isinstance(data, dict) else None
    if not isinstance(prod, dict):
        return []
    blob = json.dumps(prod)
    urls = re.findall(r"https://image\.celine\.com/asset/[^\"\\]+", blob)
    # Prefer _1_ / first gallery frame ordering by trailing _N_
    def sort_key(u: str) -> tuple:
        m = re.search(r"_(\d+)_", u)
        return (int(m.group(1)) if m else 99, u)

    seen: set[str] = set()
    out: list[str] = []
    for u in sorted(urls, key=sort_key):
        base = u.split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        out.append(u if "?V2" in u else f"{base}?V2")
    return out


def needs_images(row: dict) -> bool:
    imgs = [x for x in (row.get("images") or []) if x and "placeholder" not in x]
    return len(imgs) == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category-hint", choices=["bags", "shoes", "all"], default="all")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=0.15)
    args = ap.parse_args()

    # Prefer bags first when repairing the reported shop bug
    paths = celine_raw_paths()
    if args.category_hint == "bags":
        paths = [p for p in paths if "bags" in p.name]
    elif args.category_hint == "shoes":
        paths = [p for p in paths if "shoes" in p.name]

    fixed = 0
    failed = 0
    touched_folders: list[str] = []

    for path in paths:
        payload = load_json(path, {"products": []})
        products = payload.get("products") or []
        changed = False
        for row in products:
            if not needs_images(row):
                continue
            sku = str(row.get("sku") or row.get("id") or "").strip()
            if not sku:
                continue
            print(f"fetch {sku}", flush=True)
            remote = sfcc_image_urls(sku)
            if not remote:
                failed += 1
                time.sleep(args.sleep)
                continue
            local = materialize_images(sku, remote[:8])
            if not local:
                failed += 1
                time.sleep(args.sleep)
                continue
            row["images"] = local
            row["remoteImages"] = remote[:8]
            folder = slugify(sku.replace(".", "-"))
            touched_folders.append(folder)
            fixed += 1
            changed = True
            print(f"  ok {len(local)} images -> {folder}", flush=True)
            time.sleep(args.sleep)
            if args.limit and fixed >= args.limit:
                break
        if changed:
            payload["products"] = products
            save_json(path, payload)
            print(f"saved {path.name}", flush=True)
        if args.limit and fixed >= args.limit:
            break

    print(f"DONE fixed={fixed} failed={failed} folders={len(touched_folders)}", flush=True)
    list_path = ROOT / "tmp/ce-repaired-image-folders.txt"
    list_path.parent.mkdir(parents=True, exist_ok=True)
    list_path.write_text("\n".join(dict.fromkeys(touched_folders)) + "\n")
    print(f"wrote {list_path}", flush=True)
    return 0 if fixed or not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
