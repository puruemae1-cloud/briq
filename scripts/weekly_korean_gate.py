#!/usr/bin/env python3
"""Shared helper for weekly sync scripts: keep English PDP copy off new SKUs."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _run_check(brand: str, since_iso: str) -> int:
    return subprocess.call(
        [
            sys.executable,
            str(ROOT / "scripts" / "check-catalog-korean.py"),
            "--brand",
            brand,
            "--new-since",
            since_iso,
            "--fail",
        ],
        cwd=str(ROOT),
    )


def hold_back_untranslated(brand: str, since_iso: str) -> int:
    """Drop new SKUs whose copy is still English from JSON catalogues.

    They are re-registered as new on the next sync once translation succeeds,
    so stock updates for the rest of the brand are not blocked meanwhile.
    Returns the number of products removed; generated .ts catalogues are left
    untouched (0) because they cannot be rewritten safely here.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    from ko_qa import CATALOG_PATHS, find_hybrid_fields, load_products

    removed = 0
    for path in CATALOG_PATHS.get(brand) or []:
        if path.suffix != ".json" or not path.is_file():
            continue
        ts = path.with_suffix(".ts")
        if ts.is_file() and "import data from" not in ts.read_text()[:2000]:
            continue
        products = load_products(path)
        bad_ids = {pid for pid, *_ in find_hybrid_fields(products, new_since=since_iso)}
        if not bad_ids:
            continue
        text = path.read_text()
        pretty = "\n" in text[:200]
        data = json.loads(text)
        rows = data if isinstance(data, list) else data.get("products")
        kept = [p for p in rows if str(p.get("id")) not in bad_ids]
        removed += len(rows) - len(kept)
        if isinstance(data, list):
            data = kept
        else:
            data["products"] = kept
        body = (
            json.dumps(data, ensure_ascii=False, indent=2)
            if pretty
            else json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        )
        path.write_text(body + "\n")
        print(
            f"held back {len(rows) - len(kept)} untranslated new {brand} products "
            f"from {path.relative_to(ROOT)}: {sorted(bad_ids)[:10]}",
            flush=True,
        )
    return removed


def check_new_korean(brand: str, since_iso: str) -> None:
    """Fail only if new English SKUs cannot be held back from the catalogue."""
    print(f"Checking Korean copy for new {brand} products since {since_iso}…", flush=True)
    if _run_check(brand, since_iso) == 0:
        return
    if hold_back_untranslated(brand, since_iso) and _run_check(brand, since_iso) == 0:
        return
    raise SystemExit(f"{brand}: new products still have English copy")
