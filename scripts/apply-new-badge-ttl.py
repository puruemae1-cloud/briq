#!/usr/bin/env python3
"""Apply Briq NEW badge TTL across brand catalogues.

- Newly registered rows (registeredAt within 7 days) keep / receive badge New
  + newBadgeAt when missing.
- badge New older than 7 days is cleared (Sale / Nearly New untouched).

Run after weekly catalog builds, before commit:

  python3 scripts/apply-new-badge-ttl.py
  python3 scripts/apply-new-badge-ttl.py --brand al
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from briq_new_badge import (  # noqa: E402
    NEW_BADGE_DAYS,
    NEW_BADGE_LABEL,
    apply_new_badge_ttl,
    is_within_new_window,
    stamp_new_badge,
    utc_now,
)

CATALOGS: dict[str, list[Path]] = {
    "al": [ROOT / "src/data/al/al-catalog.json"],
    "bb": [ROOT / "src/data/bb/bb-catalog.json"],
    "bs": [ROOT / "src/data/bs/bs-catalog.json"],
    "ch": [ROOT / "src/data/ch/ch-catalog.json"],
    "gc": [ROOT / "src/data/gc/gc-catalog.json"],
    "ps": [ROOT / "src/data/ps/ps-catalog.json"],
    "pr": [ROOT / "src/data/pr/pr-catalog.json"],
    "di": [ROOT / "src/data/di/di-catalog.json"],
    "mb": [ROOT / "src/data/mb/mb-catalog.json"],
    "ce": [ROOT / "src/data/ce/ce-catalog.json"],
    "vw": [ROOT / "src/data/vw/vw-catalog.json"],
    "ys": [ROOT / "src/data/ys/ys-catalog.json"],
    "gg": [ROOT / "src/data/gg/gg-catalog.json"],
    "ax": [
        ROOT / "src/data/ax/ax-catalog.json",
        ROOT / "src/data/ax/ax-apparel-catalog.json",
        ROOT / "src/data/ax/ax-gear-catalog.json",
        ROOT / "src/data/ax/ax-outlet-catalog.json",
    ],
}


def _load_products(path: Path) -> tuple[list[dict] | None, dict | list | None]:
    if not path.exists():
        return None, None
    if path.suffix == ".ts":
        # TS catalogs are codegen'd elsewhere — skip binary-safe JSON only here.
        return None, None
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return data, data
    if isinstance(data, dict) and isinstance(data.get("products"), list):
        return data["products"], data
    return None, None


def _save(path: Path, root: dict | list) -> None:
    path.write_text(json.dumps(root, ensure_ascii=False, indent=2) + "\n")


def process_products(products: list[dict]) -> tuple[int, int, int]:
    now = utc_now()
    stamped = expired = touched = 0
    for p in products:
        if not isinstance(p, dict):
            continue
        before = json.dumps(
            {k: p.get(k) for k in ("badge", "newBadgeAt", "editTier")},
            sort_keys=True,
        )
        badge = (p.get("badge") or "").strip()
        has_new_mark = badge == NEW_BADGE_LABEL or bool(p.get("newBadgeAt"))

        if has_new_mark:
            # Migrate legacy badge:New → newBadgeAt from registeredAt.
            if badge == NEW_BADGE_LABEL and not p.get("newBadgeAt") and p.get("registeredAt"):
                p["newBadgeAt"] = p["registeredAt"]
            if is_within_new_window(p, now=now):
                if stamp_new_badge(p, now=now):
                    stamped += 1
            else:
                if apply_new_badge_ttl(p, now=now, newly_synced=False):
                    expired += 1
        else:
            # No Briq NEW mark — leave Sale / Nearly New / plain rows alone.
            pass

        after = json.dumps(
            {k: p.get(k) for k in ("badge", "newBadgeAt", "editTier")},
            sort_keys=True,
        )
        if before != after:
            touched += 1
    return stamped, expired, touched


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", action="append", dest="brands")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    brands = args.brands or sorted(CATALOGS)
    now = utc_now()
    print(f"NEW badge TTL={NEW_BADGE_DAYS}d now={now.isoformat()}", flush=True)

    total_touched = 0
    for brand in brands:
        paths = CATALOGS.get(brand)
        if not paths:
            print(f"skip unknown brand {brand}", flush=True)
            continue
        for path in paths:
            products, root = _load_products(path)
            if products is None or root is None:
                if path.exists() and path.suffix == ".ts":
                    print(f"skip ts catalog {path.relative_to(ROOT)}", flush=True)
                elif not path.exists():
                    print(f"skip missing {path.relative_to(ROOT)}", flush=True)
                continue
            stamped, expired, touched = process_products(products)
            print(
                f"{path.relative_to(ROOT)}: stamped={stamped} expired={expired} "
                f"touched={touched} n={len(products)}",
                flush=True,
            )
            total_touched += touched
            if touched and not args.dry_run:
                _save(path, root)
    print(f"done touched={total_touched} dry_run={args.dry_run}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
