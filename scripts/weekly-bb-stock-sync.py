#!/usr/bin/env python3
"""Weekly Burberry stock + catalogue sync for Briq.

Re-scrapes UK PLPs + PDPs (forcing size/stock refresh), translates
shop copy EN→KO, then rebuilds bb-catalog.ts while preserving
registeredAt for existing styles.

Covers:
  - option-level sold-out / restock (isInStock on each size)
  - new colourways / styles appearing on Burberry PLPs
  - price + collection membership updates
  - women / men / children / gifts / scarves / bag collections / beauty

Designed for GitHub Actions (cron) and local runs:
  BB_REFRESH_STOCK=1 python3 scripts/weekly-bb-stock-sync.py
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCRIPTS = (
    "scrape-bb-women.py",
    "scrape-bb-men.py",
    "scrape-bb-children.py",
    "scrape-bb-gifts.py",
    "scrape-bb-scarves.py",
    "scrape-bb-bags-collections.py",
    "scrape-bb-beauty.py",
    "translate-bb-catalog.py",
    "build-bb-catalog.py",
)


def run(script: str, env: dict[str, str]) -> None:
    print(f"→ {script}", flush=True)
    cmd = [sys.executable, str(ROOT / "scripts" / script)]
    if script == "translate-bb-catalog.py":
        cmd.extend(["--workers", "4"])
    subprocess.check_call(cmd, cwd=str(ROOT), env=env)


def load_translate_module():
    spec = importlib.util.spec_from_file_location(
        "translate_bb_catalog", ROOT / "scripts" / "translate-bb-catalog.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    from weekly_korean_gate import check_new_korean, utc_now_iso

    env = os.environ.copy()
    # Always refresh PDP stock/prices on the weekly job.
    env["BB_REFRESH_STOCK"] = "1"
    print("BB_REFRESH_STOCK=1 (re-fetch size availability + prices)", flush=True)
    since = utc_now_iso()

    for script in SCRIPTS:
        run(script, env)

    print("Checking Burberry Korean copy…", flush=True)
    check = [
        sys.executable,
        str(ROOT / "scripts" / "translate-bb-catalog.py"),
        "--check-catalog",
    ]
    if subprocess.call(check, cwd=str(ROOT), env=env) != 0:
        # Translation was cut short (usually gtx 429). Ship stock/size/price
        # changes on top of the committed Korean copy instead of losing them.
        from stock_only_fallback import apply_fallback

        translate = load_translate_module()
        apply_fallback(ROOT / "src/data/bb/bb-catalog.json", translate.product_copy_ok)
        subprocess.check_call(check, cwd=str(ROOT), env=env)
    check_new_korean("bb", since)
    print("Burberry weekly sync complete.", flush=True)


if __name__ == "__main__":
    main()
