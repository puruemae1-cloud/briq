#!/usr/bin/env python3
"""Weekly Paul Smith sync for Briq.

  1) Re-scrape men + women/gifts PLPs (merge new SKUs, refresh PLP stock)
  2) Prune raw keys no longer on any tracked PLP
  3) Apply PLP inStock → entity.items.stock for sellable / sold-out
  4) Rebuild ps-catalog.json (preserves registeredAt; new SKUs stamp now)

  python3 scripts/weekly-ps-stock-sync.py
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/ps/ps-catalog-raw.json"
IMG_ROOT = ROOT / "public/products/ps-pdp"

_spec = importlib.util.spec_from_file_location(
    "ps_mens", ROOT / "scripts/scrape-ps-mens.py"
)
mens = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(mens)

_espec = importlib.util.spec_from_file_location(
    "ps_ext", ROOT / "scripts/scrape-ps-extend.py"
)
ext = importlib.util.module_from_spec(_espec)
assert _espec and _espec.loader
_espec.loader.exec_module(ext)


def run(script: str) -> None:
    print(f"→ {script}", flush=True)
    subprocess.check_call(
        [sys.executable, "-u", str(ROOT / "scripts" / script)],
        cwd=str(ROOT),
    )


def live_keys() -> set[str]:
    """Union of product keys currently listed on all tracked PLPs."""
    keys: set[str] = set()
    for section in [*mens.SECTIONS, *ext.SECTIONS]:
        print(f"membership {section['channel']}…", flush=True)
        items = mens.scrape_section(section)
        for p in items:
            k = str(p.get("key") or "")
            if k:
                keys.add(k)
        time.sleep(0.2)
    return keys


def apply_plp_stock(raw: dict[str, dict]) -> int:
    updated = 0
    for row in raw.values():
        plp_vars = (row.get("plp") or {}).get("variants") or []
        if not plp_vars:
            continue
        by_label = {
            str(v.get("label") or "").strip(): bool(v.get("inStock"))
            for v in plp_vars
            if v.get("label") is not None
        }
        if not by_label:
            continue
        items = (row.get("entity") or {}).get("items") or []
        for item in items:
            name = str(item.get("name") or "").strip()
            if name not in by_label:
                continue
            want = "yes" if by_label[name] else "no"
            if str(item.get("stock") or "").lower() != want:
                item["stock"] = want
                if want == "no":
                    item["quantity"] = 0
                updated += 1
        if items:
            row["isOutOfStock"] = not any(
                str(i.get("stock") or "").lower() in {"yes", "true"}
                or int(i.get("quantity") or 0) > 0
                for i in items
            )
    return updated


def prune_images(raw: dict[str, dict]) -> int:
    if not IMG_ROOT.exists():
        return 0
    keep = {str(r.get("handle") or "") for r in raw.values() if r.get("handle")}
    removed = 0
    for d in list(IMG_ROOT.iterdir()):
        if d.is_dir() and d.name not in keep:
            shutil.rmtree(d, ignore_errors=True)
            removed += 1
    if removed:
        print(f"pruned {removed} orphan ps-pdp folders", flush=True)
    return removed


def assert_local_images(raw: dict[str, dict]) -> None:
    """Fail the weekly job if catalogue points at missing PDP files."""
    missing: list[str] = []
    for row in raw.values():
        handle = row.get("handle") or "?"
        images = row.get("images") or []
        if not images:
            missing.append(f"{handle}: no images[]")
            continue
        for img in images:
            path = ROOT / "public" / str(img).lstrip("/")
            if not path.is_file() or path.stat().st_size < 800:
                missing.append(str(img))
    if missing:
        sample = ", ".join(missing[:12])
        raise SystemExit(
            f"Paul Smith sync aborted: {len(missing)} missing local image(s). "
            f"Sample: {sample}"
        )
    print(f"local image check ok ({len(raw)} products)", flush=True)


def main() -> None:
    from weekly_korean_gate import check_new_korean, utc_now_iso

    since = utc_now_iso()
    run("scrape-ps-mens.py")
    run("scrape-ps-extend.py")

    raw = json.loads(RAW_PATH.read_text())
    before = len(raw)
    keep = live_keys()
    pruned = {k: v for k, v in raw.items() if k in keep}
    dropped = before - len(pruned)
    print(f"prune raw: {before} → {len(pruned)} (dropped {dropped})", flush=True)

    stock_updates = apply_plp_stock(pruned)
    print(f"entity stock fields updated: {stock_updates}", flush=True)

    RAW_PATH.write_text(
        json.dumps(pruned, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    prune_images(pruned)
    assert_local_images(pruned)

    run("build-ps-catalog.py")
    check_new_korean("ps", since)
    print("Paul Smith weekly sync complete.", flush=True)


if __name__ == "__main__":
    main()
