#!/usr/bin/env python3
"""Weekly Gucci stock + catalogue sync for Briq.

Re-scrapes official UK PLPs (women/men handbags, RTW, shoes, wallets,
fashion accessories, travel, jewellery, gifts), then rebuilds
gc-catalog.json while preserving registeredAt for existing SKUs.

Covers:
  - sold-out / restock from PLP showOutOfStockLabel / inStockEntry
  - new colourways appearing on tracked Gucci categories
  - price + collection membership updates
  - images for new SKUs (existing local files are skipped)

Designed for GitHub Actions (cron) and local runs:

  python3 scripts/weekly-gc-stock-sync.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "src/data/gc/gc-catalog.json"

# Order matters: primary category scrapers first (full stock refresh),
# gifts last (membership tagging onto existing PDPs).
SCRIPTS = (
    "scrape-gc-handbags.py",
    "scrape-gc-mens-handbags.py",
    "scrape-gc-womens-rtw.py",
    "scrape-gc-mens-rtw.py",
    "scrape-gc-womens-shoes.py",
    "scrape-gc-mens-shoes.py",
    "scrape-gc-womens-wallets.py",
    "scrape-gc-mens-wallets.py",
    "scrape-gc-womens-fashion-accessories.py",
    "scrape-gc-mens-fashion-accessories.py",
    "scrape-gc-womens-travel.py",
    "scrape-gc-mens-travel.py",
    "scrape-gc-jewellery-watches.py",
    "scrape-gc-gifts.py",
    "scrape-gc-mens-gifts.py",
    "build-gc-catalog.py",
)


def run(script: str, env: dict[str, str]) -> None:
    print(f"→ {script}", flush=True)
    subprocess.check_call(
        [sys.executable, "-u", str(ROOT / "scripts" / script)],
        cwd=str(ROOT),
        env=env,
    )


def stock_map(path: Path) -> dict[str, bool]:
    if not path.exists():
        return {}
    out: dict[str, bool] = {}
    for p in json.loads(path.read_text()):
        sku = str(p.get("sku") or "").strip()
        if not sku:
            continue
        out[sku.upper()] = bool(p.get("inStock", True))
    return out


def print_delta(before: dict[str, bool], after: dict[str, bool]) -> None:
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    restocked = sorted(
        s for s in after if s in before and not before[s] and after[s]
    )
    sold_out = sorted(
        s for s in after if s in before and before[s] and not after[s]
    )
    print(
        f"Gucci delta: +{len(added)} new, -{len(removed)} dropped, "
        f"{len(restocked)} restocked, {len(sold_out)} sold-out "
        f"(catalogue {len(before)} → {len(after)})",
        flush=True,
    )
    if added[:12]:
        print(f"  new sample: {', '.join(added[:12])}", flush=True)
    if restocked[:12]:
        print(f"  restocked sample: {', '.join(restocked[:12])}", flush=True)
    if sold_out[:12]:
        print(f"  sold-out sample: {', '.join(sold_out[:12])}", flush=True)
    if removed[:12]:
        print(f"  dropped sample: {', '.join(removed[:12])}", flush=True)


def main() -> None:
    from weekly_korean_gate import check_new_korean, utc_now_iso

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    # Hint scrapers / future size-level refresh paths.
    env["GC_REFRESH_STOCK"] = "1"
    print("GC_REFRESH_STOCK=1 (re-fetch PLP availability + new SKUs)", flush=True)
    since = utc_now_iso()

    before = stock_map(OUT_JSON)
    print(f"Previous catalogue SKUs: {len(before)}", flush=True)

    for script in SCRIPTS:
        run(script, env)

    after = stock_map(OUT_JSON)
    print_delta(before, after)
    check_new_korean("gc", since)
    print("Gucci weekly sync complete.", flush=True)


if __name__ == "__main__":
    main()
