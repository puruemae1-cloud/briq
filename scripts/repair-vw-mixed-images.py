#!/usr/bin/env python3
"""Re-scrape VW PDP galleries that may contain mixed recommendation-rail shots.

Usage:
  python3 scripts/repair-vw-mixed-images.py --sku 3G010068-J00BL--BLACK
  python3 scripts/repair-vw-mixed-images.py --min-images 10 --limit 50
  python3 scripts/repair-vw-mixed-images.py --all-suspect
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vw_common import (  # noqa: E402
    filter_product_images,
    materialize_images,
    scrape_pdp,
    slugify,
    with_browser,
)


def load_catalog() -> list[dict]:
    return json.loads((ROOT / "src/data/vw/vw-catalog.json").read_text())


def load_all_raw() -> list[dict]:
    out: list[dict] = []
    for path in sorted((ROOT / "src/data/vw").glob("*catalog-raw.json")):
        data = json.loads(path.read_text())
        items = data.get("products") if isinstance(data, dict) else data
        if not isinstance(items, list):
            continue
        for row in items:
            if isinstance(row, dict) and row.get("url"):
                row = dict(row)
                row["_rawPath"] = str(path)
                out.append(row)
    return out


def repair_one(page, row: dict, *, force: bool = True) -> dict | None:
    url = (row.get("url") or row.get("sourceUrl") or "").strip()
    sku = (row.get("sku") or row.get("id") or "").strip()
    if not url or not sku:
        return None
    pdp = scrape_pdp(page, url)
    sku = (pdp.get("sku") or sku).strip()
    remote = filter_product_images(sku, pdp.get("images") or [])
    local = materialize_images(page.request, sku, remote, force=force, max_n=12)
    if not local:
        print(f"WARN no images for {sku}", flush=True)
        return None
    return {
        "sku": sku,
        "id": sku,
        "images": local,
        "remoteImages": remote,
        "url": url,
        "title": (pdp.get("title") or row.get("title") or "").strip(),
    }


def apply_to_raw(raw_path: Path, sku: str, images: list[str], remote: list[str]) -> None:
    data = json.loads(raw_path.read_text())
    items = data.get("products") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return
    sku_u = sku.upper()
    changed = 0
    for row in items:
        if not isinstance(row, dict):
            continue
        if str(row.get("sku") or row.get("id") or "").upper() != sku_u:
            continue
        row["images"] = images
        row["remoteImages"] = remote
        changed += 1
    if changed and isinstance(data, dict):
        raw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"updated {changed} raw row(s) in {raw_path.name}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sku", action="append", default=[])
    ap.add_argument("--min-images", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--all-suspect", action="store_true", help="min-images default 10")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    raw_rows = load_all_raw()
    by_sku = {
        str(r.get("sku") or r.get("id") or "").upper(): r
        for r in raw_rows
        if str(r.get("sku") or r.get("id") or "").strip()
    }

    targets: list[dict] = []
    if args.sku:
        for s in args.sku:
            key = s.upper().removeprefix("VW-")
            # also try catalog id form
            row = by_sku.get(key) or by_sku.get(s.upper())
            if not row:
                # fuzzy
                row = next(
                    (
                        r
                        for k, r in by_sku.items()
                        if key in k or k in key
                    ),
                    None,
                )
            if row:
                targets.append(row)
            else:
                print(f"missing raw row for sku={s}", flush=True)
    else:
        min_n = args.min_images or (10 if args.all_suspect else 0)
        catalog = load_catalog()
        suspect_ids = {
            str(p.get("sku") or "").upper()
            for p in catalog
            if len(p.get("images") or []) >= min_n
        }
        for sku, row in by_sku.items():
            if sku in suspect_ids or len(row.get("images") or []) >= min_n:
                targets.append(row)

    # de-dupe by sku
    seen: set[str] = set()
    uniq: list[dict] = []
    for row in targets:
        sku = str(row.get("sku") or row.get("id") or "").upper()
        if not sku or sku in seen:
            continue
        seen.add(sku)
        uniq.append(row)
    if args.limit:
        uniq = uniq[: args.limit]

    print(f"repairing {len(uniq)} VW product(s)…", flush=True)
    if not uniq:
        return 0

    def run(page):
        ok = 0
        for i, row in enumerate(uniq, 1):
            sku = str(row.get("sku") or row.get("id") or "")
            print(f"[{i}/{len(uniq)}] {sku}", flush=True)
            try:
                fixed = repair_one(page, row, force=True)
            except Exception as e:
                print(f"  FAIL {sku}: {e}", flush=True)
                continue
            if not fixed:
                continue
            raw_path = Path(row.get("_rawPath") or "")
            if raw_path.is_file():
                apply_to_raw(
                    raw_path, fixed["sku"], fixed["images"], fixed["remoteImages"]
                )
            print(
                f"  OK {len(fixed['images'])} images (was {len(row.get('images') or [])})",
                flush=True,
            )
            ok += 1
        return ok

    fixed_n = with_browser(run, headed=args.headed)
    print(f"done fixed={fixed_n}", flush=True)
    print("Next: python3 scripts/build-vw-catalog.py", flush=True)
    print(
        "Then: python3 scripts/push-product-images-tag.py --dirs vw-pdp --merge --skip-whiten",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
