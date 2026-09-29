#!/usr/bin/env python3
"""Keep weekly stock sync alive when translation is incomplete.

When the machine-translation step is rate limited, a freshly built catalogue
can carry English shop copy. Rather than aborting the whole sync (and losing
option-level sold-out / restock updates), merge the new build onto the last
committed catalogue:

  * products whose new copy passes the Korean check ship as built
  * existing products keep their committed Korean copy, but take stock,
    size options and prices from the new build
  * brand-new products that are still English are held back until a later
    sync can translate them
"""
from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]

PRODUCT_STOCK_FIELDS = ("inStock", "price", "compareAtPrice", "gbpPrice", "variants")
VARIANT_TEXT_FIELDS = ("nameKo", "colorNameKo")


def committed_catalog(rel_path: str, ref: str = "HEAD") -> list[dict]:
    out = subprocess.run(
        ["git", "show", f"{ref}:{rel_path}"],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return json.loads(out)


def merge_stock_only(
    old: list[dict],
    new: list[dict],
    text_ok: Callable[[dict], bool],
) -> tuple[list[dict], dict[str, int]]:
    old_by_id = {str(p.get("id")): p for p in old}
    merged: list[dict] = []
    stats = {"as_built": 0, "stock_only": 0, "held_back": 0}
    for p in new:
        pid = str(p.get("id"))
        if text_ok(p):
            merged.append(p)
            stats["as_built"] += 1
            continue
        prev = old_by_id.get(pid)
        if prev is None:
            stats["held_back"] += 1
            continue
        row = copy.deepcopy(prev)
        prev_variants = {str(v.get("id")): v for v in prev.get("variants") or []}
        for field in PRODUCT_STOCK_FIELDS:
            if field in p:
                row[field] = copy.deepcopy(p[field])
        for v in row.get("variants") or []:
            pv = prev_variants.get(str(v.get("id")))
            if pv:
                for field in VARIANT_TEXT_FIELDS:
                    if field in pv:
                        v[field] = pv[field]
        merged.append(row)
        stats["stock_only"] += 1
    return merged, stats


def apply_fallback(
    catalog_path: Path,
    text_ok: Callable[[dict], bool],
) -> dict[str, int]:
    rel = str(catalog_path.resolve().relative_to(ROOT))
    new = json.loads(catalog_path.read_text())
    old = committed_catalog(rel)
    merged, stats = merge_stock_only(old, new, text_ok)
    catalog_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n")
    print(
        f"stock-only fallback {rel}: as_built={stats['as_built']} "
        f"stock_only={stats['stock_only']} held_back={stats['held_back']}",
        flush=True,
    )
    return stats
