#!/usr/bin/env python3
"""Strip recommendation-rail shots from VW raw galleries (offline).

Re-applies ``filter_product_images`` to every ``*catalog-raw.json`` row so
shared colourway codes (J00BL etc.) and other styles cannot leak into PDP
galleries. Optionally rematerializes local ``public/products/vw-pdp`` files.

Usage:
  python3 scripts/sanitize-vw-images.py
  python3 scripts/sanitize-vw-images.py --rematerialize --family rtw
  python3 scripts/sanitize-vw-images.py --check  # exit 1 if mixed remotes remain
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
    slugify,
    vw_style_and_colorway,
    with_browser,
)


def iter_raw_paths(family: str | None) -> list[Path]:
    paths = sorted((ROOT / "src/data/vw").glob("*catalog-raw.json"))
    if not family:
        return paths
    fam = family.lower()
    if fam == "rtw":
        return [p for p in paths if "rtw" in p.name]
    return [p for p in paths if fam in p.name]


def remote_is_clean(sku: str, remotes: list[str]) -> bool:
    filtered = filter_product_images(sku, remotes)
    if len(filtered) != len(remotes):
        return False
    # Compare without query-string noise
    a = [u.split("?")[0] for u in filtered]
    b = [u.split("?")[0] for u in remotes]
    return a == b


def sanitize_raw_file(path: Path) -> tuple[int, list[dict]]:
    data = json.loads(path.read_text())
    items = data.get("products") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return 0, []
    changed = 0
    need_materialize: list[dict] = []
    for row in items:
        if not isinstance(row, dict):
            continue
        sku = str(row.get("sku") or row.get("id") or "").strip()
        rem = list(row.get("remoteImages") or [])
        if not sku or not rem:
            continue
        filtered = filter_product_images(sku, rem)
        if not filtered and rem:
            # Keep a single best-effort frame rather than empty PDP.
            filtered = filter_product_images(sku, rem[:1]) or rem[:1]
        folder = slugify(sku.replace(".", "-"))
        new_images = [f"/products/vw-pdp/{folder}/{i}.jpg" for i in range(1, len(filtered) + 1)]
        before = [u.split("?")[0] for u in rem]
        after = [u.split("?")[0] for u in filtered]
        if before != after or list(row.get("images") or []) != new_images:
            row["remoteImages"] = filtered
            row["images"] = new_images
            changed += 1
            need_materialize.append(
                {
                    "sku": sku,
                    "remoteImages": filtered,
                    "rawPath": str(path),
                }
            )
    if changed and isinstance(data, dict):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return changed, need_materialize


def check_all(family: str | None) -> int:
    bad = 0
    for path in iter_raw_paths(family):
        data = json.loads(path.read_text())
        items = data.get("products") if isinstance(data, dict) else data
        for row in items or []:
            if not isinstance(row, dict):
                continue
            sku = str(row.get("sku") or "").strip()
            rem = row.get("remoteImages") or []
            if not sku or not rem:
                continue
            if not remote_is_clean(sku, rem):
                style, cw = vw_style_and_colorway(sku)
                print(
                    f"MIXED {path.name} {sku} style={style} cw={cw} "
                    f"n={len(rem)}→{len(filter_product_images(sku, rem))}",
                    flush=True,
                )
                bad += 1
    print(f"check mixed_rows={bad}", flush=True)
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", default="", help="rtw|bags|jewellery|… subset")
    ap.add_argument("--rematerialize", action="store_true")
    ap.add_argument(
        "--force-all",
        action="store_true",
        help="With --rematerialize, rewrite every SKU in scope (not only newly sanitized)",
    )
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    family = args.family.strip() or None

    if args.check:
        bad = check_all(family)
        return 1 if bad else 0

    total_changed = 0
    to_mat: list[dict] = []
    for path in iter_raw_paths(family):
        n, need = sanitize_raw_file(path)
        print(f"{path.name}: sanitized {n} row(s)", flush=True)
        total_changed += n
        to_mat.extend(need)

    # de-dupe by sku (men/women overlap)
    seen: set[str] = set()
    uniq: list[dict] = []
    for row in to_mat:
        sku = row["sku"].upper()
        if sku in seen:
            continue
        seen.add(sku)
        uniq.append(row)

    # Rematerialize every row in scope even when remotes were already clean
    # (rewrites polluted CDN/local 1..N.jpg prefixes from older scrapes).
    if args.rematerialize and args.force_all:
        uniq = []
        seen.clear()
        for path in iter_raw_paths(family):
            data = json.loads(path.read_text())
            items = data.get("products") if isinstance(data, dict) else data
            for row in items or []:
                if not isinstance(row, dict):
                    continue
                sku = str(row.get("sku") or "").strip()
                rem = list(row.get("remoteImages") or [])
                if not sku or not rem:
                    continue
                key = sku.upper()
                if key in seen:
                    continue
                seen.add(key)
                uniq.append({"sku": sku, "remoteImages": rem, "rawPath": str(path)})

    if args.limit:
        uniq = uniq[: args.limit]

    print(f"total sanitized rows={total_changed} unique skus={len(uniq)}", flush=True)

    if args.rematerialize and uniq:

        def run(page):
            ok = 0
            for i, row in enumerate(uniq, 1):
                sku = row["sku"]
                rem = row["remoteImages"]
                print(f"[{i}/{len(uniq)}] rematerialize {sku} n={len(rem)}", flush=True)
                try:
                    local = materialize_images(
                        page.request, sku, rem, force=True, max_n=12
                    )
                except Exception as e:
                    print(f"  FAIL {sku}: {e}", flush=True)
                    continue
                print(f"  OK {len(local)} files", flush=True)
                ok += 1
            return ok

        fixed = with_browser(run, headed=args.headed)
        print(f"rematerialized={fixed}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
