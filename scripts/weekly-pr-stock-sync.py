#!/usr/bin/env python3
"""Weekly Prada stock + catalogue sync for Briq.

Re-scrapes all official GB Prada PLPs, rebuilds pr-catalog.json, and
preserves catalogue rows when a scrape returns no GBP price
(PR_SKIP_NO_PRICE_UPDATE=1).

Designed for GitHub Actions (cron) and local runs:

  python3 scripts/weekly-pr-stock-sync.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "src/data/pr/pr-catalog.json"

SCRIPTS = (
    "scrape-pr-handbags.py",
    "scrape-pr-mens-handbags.py",
    "scrape-pr-womens-rtw.py",
    "scrape-pr-mens-rtw.py",
    "scrape-pr-womens-shoes.py",
    "scrape-pr-mens-shoes.py",
    "scrape-pr-womens-slg.py",
    "scrape-pr-mens-slg.py",
    "scrape-pr-womens-travel.py",
    "scrape-pr-mens-travel.py",
    "scrape-pr-womens-accessories.py",
    "scrape-pr-mens-accessories.py",
    "scrape-pr-linea-rossa.py",
    "scrape-pr-beauty.py",
    "scrape-pr-fragrances.py",
    "scrape-pr-fine-jewelry.py",
    "build-pr-catalog.py",
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
        f"Prada delta: +{len(added)} new, -{len(removed)} dropped, "
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
    env["PR_REFRESH_STOCK"] = "1"
    env["PR_SKIP_NO_PRICE_UPDATE"] = "1"
    print(
        "PR_REFRESH_STOCK=1 PR_SKIP_NO_PRICE_UPDATE=1 "
        "(re-fetch PLP availability; skip no-price updates)",
        flush=True,
    )
    since = utc_now_iso()

    before = stock_map(OUT_JSON)
    print(f"Previous catalogue SKUs: {len(before)}", flush=True)

    for script in SCRIPTS:
        run(script, env)

    after = stock_map(OUT_JSON)
    print_delta(before, after)
    check_new_korean("pr", since)
    print("Prada weekly sync complete.", flush=True)


if __name__ == "__main__":
    main()
