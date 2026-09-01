#!/usr/bin/env python3
"""Weekly Arc'teryx sync for Briq — outdoor apparel, footwear, accessories/bags.

Designed for cron / GitHub Actions:
  AX_REFRESH_STOCK=1 python3 scripts/weekly-ax-stock-sync.py

Steps:
  1) Refresh PLP feeds (new + removed styles)
  2) Playwright-enrich PDPs with stock refresh (sold-out / restock)
  3) Prune PDP caches + image dirs for styles gone from feed
  4) Rebuild catalogues

Outlet (outlet.arcteryx.com) is not included — separate market.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(script: str, extra: list[str] | None = None) -> None:
    cmd = [sys.executable, "-u", str(ROOT / "scripts" / script), *(extra or [])]
    print(f"→ {' '.join(cmd)}", flush=True)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["AX_REFRESH_STOCK"] = "1"
    site = Path.home() / "Library/Python/3.9/lib/python/site-packages"
    if site.exists():
        env["PYTHONPATH"] = f"{site}:{env.get('PYTHONPATH', '')}"
    subprocess.check_call(cmd, cwd=str(ROOT), env=env)


def raw_ids(raw_path: Path) -> set[str]:
    if not raw_path.exists():
        return set()
    data = json.loads(raw_path.read_text())
    return {str(p["id"]) for p in data.get("products") or [] if p.get("id")}


def prune_pdp_cache(cache_path: Path, keep: set[str]) -> int:
    if not cache_path.exists():
        return 0
    cache = json.loads(cache_path.read_text())
    before = len(cache)
    pruned = {k: v for k, v in cache.items() if k in keep}
    removed = before - len(pruned)
    if removed:
        cache_path.write_text(json.dumps(pruned, indent=2, ensure_ascii=False) + "\n")
        print(f"  pruned {removed} from {cache_path.name}", flush=True)
    return removed


def prune_image_dirs(img_root: Path, keep: set[str]) -> int:
    if not img_root.exists():
        return 0
    removed = 0
    for d in list(img_root.iterdir()):
        if not d.is_dir():
            continue
        if d.name not in keep:
            shutil.rmtree(d, ignore_errors=True)
            removed += 1
    if removed:
        print(f"  pruned {removed} image dirs under {img_root.name}", flush=True)
    return removed


def prune_line(raw_name: str, cache_name: str, img_name: str) -> None:
    keep = raw_ids(ROOT / "src/data/ax" / raw_name)
    print(f"prune {raw_name}: keep {len(keep)} skus", flush=True)
    prune_pdp_cache(ROOT / "src/data/ax" / cache_name, keep)
    prune_image_dirs(ROOT / "public/products" / img_name, keep)


def main() -> None:
    from weekly_korean_gate import check_new_korean, utc_now_iso

    os.environ["AX_REFRESH_STOCK"] = "1"
    print("AX_REFRESH_STOCK=1 (re-fetch colour×size availability)", flush=True)
    since = utc_now_iso()

    # 1) Feeds — discover new styles / drop discontinued
    run("scrape-ax-outdoor-apparel.py")
    run("scrape-ax-footwear.py")
    run("scrape-ax-gear.py")

    # 2) PDP enrich — stock + galleries for new; refresh stock for existing
    run("enrich-ax-apparel-playwright.py")
    run("enrich-ax-gear-playwright.py")
    run(
        "enrich-ax-apparel-playwright.py",
        [
            "--raw",
            "src/data/ax/ax-catalog-raw.json",
            "--out",
            "src/data/ax/ax-pdp-cache.json",
            "--img",
            "public/products/ax-pdp",
        ],
    )

    # 3) Prune artefacts for SKUs removed from feed
    prune_line("ax-apparel-raw.json", "ax-apparel-pdp-cache.json", "axa-pdp")
    prune_line("ax-catalog-raw.json", "ax-pdp-cache.json", "ax-pdp")
    prune_line("ax-gear-raw.json", "ax-gear-pdp-cache.json", "axg-pdp")

    # 4) Translate EN→KO then rebuild catalogues
    # Footwear curated seed (covers PDP when gtx is rate-limited / flaky)
    run("seed-ax-footwear-ko.py")
    run("translate-ax-catalog.py")
    run("build-ax-apparel-catalog.py")
    run("build-ax-catalog.py")
    run("build-ax-gear-catalog.py")
    # Ensure gear size charts survive rebuilds / partial image skips.
    run("patch-ax-gear-size-charts.py")
    # Hard-fail on leftover English in all Arc'teryx PDP copy (apparel, footwear, gear).
    print("Checking Korean copy for all Arc'teryx catalogues…", flush=True)
    subprocess.check_call(
        [
            sys.executable,
            str(ROOT / "scripts" / "check-catalog-korean.py"),
            "--brand",
            "ax",
            "--strict",
            "--fail",
            "--max-ratio",
            "0.40",
        ],
        cwd=str(ROOT),
    )
    check_new_korean("ax", since)

    print("Arc'teryx weekly sync complete.", flush=True)


if __name__ == "__main__":
    main()
