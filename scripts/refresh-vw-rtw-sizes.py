#!/usr/bin/env python3
"""Refresh Vivienne Westwood RTW sizes + official size charts in-place.

Re-visits each clothing PDP (men/women RTW raw), fixes empty→OS size bugs,
and stores official sizeGuide charts. Does not re-download images.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from vw_common import (
    fetch_size_guide_chart,
    load_json,
    save_json,
    scrape_pdp,
    with_browser,
)
from vw_config import RAW_DIR

RTW_RAW = [
    RAW_DIR / "vw-men-rtw-catalog-raw.json",
    RAW_DIR / "vw-women-rtw-catalog-raw.json",
]


def _needs_refresh(row: dict) -> bool:
    sizes = [str(x).strip() for x in (row.get("sizes") or []) if str(x).strip()]
    if not sizes or sizes == ["OS"]:
        return True
    if not row.get("sizeChart") and not row.get("sizeGuideUrl"):
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    def run(page):
        touched = 0
        for path in RTW_RAW:
            if not path.is_file():
                print(f"skip missing {path.name}", flush=True)
                continue
            data = load_json(path, {"products": []})
            products = data.get("products") or []
            print(f"== {path.name} n={len(products)} ==", flush=True)
            for i, row in enumerate(products):
                if args.limit and touched >= args.limit:
                    break
                url = (row.get("url") or "").strip()
                if not url:
                    continue
                if not args.force and not _needs_refresh(row):
                    continue
                try:
                    pdp = scrape_pdp(page, url)
                except Exception as e:
                    print(f"  WARN pdp {row.get('id')}: {e}", flush=True)
                    continue
                sizes = pdp.get("sizes") or []
                if sizes:
                    row["sizes"] = sizes
                if pdp.get("sizeStock"):
                    row["sizeStock"] = pdp["sizeStock"]
                guide = (pdp.get("sizeGuideUrl") or "").strip()
                if guide:
                    row["sizeGuideUrl"] = guide
                    try:
                        chart = fetch_size_guide_chart(page, guide)
                        if chart:
                            row["sizeChart"] = chart
                    except Exception as e:
                        print(f"  WARN guide {row.get('id')}: {e}", flush=True)
                touched += 1
                if touched % 10 == 0:
                    save_json(path, {**data, "products": products})
                    print(f"  refreshed {touched} …", flush=True)
            save_json(path, {**data, "products": products})
            filled = sum(1 for p in products if len(p.get("sizes") or []) > 1)
            charts = sum(1 for p in products if p.get("sizeChart"))
            empty = sum(1 for p in products if not (p.get("sizes") or []))
            print(
                f"  done filled_multi={filled} charts={charts} empty_sizes={empty}",
                flush=True,
            )
        print(f"OK refreshed={touched}", flush=True)

    with_browser(run, headed=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
