#!/usr/bin/env python3
"""Homepage lookbook rails — one brand per category rail (weekly guard).

Mirrors ``src/lib/homepage-rails.ts`` so weekly syncs keep the same exclusivity
contract: if Arc'teryx fills 시그니처, it must not also fill 슈즈 / 악세서리 등.

  python3 scripts/refresh-homepage-rail-picks.py
  python3 scripts/refresh-homepage-rail-picks.py --fail

Writes ``src/data/homepage-rail-picks.json`` (audit + ids) for the weekly commit.
The live homepage still assigns at runtime via ``assignHomepageCategoryRails``.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RAIL_ORDER = [
    ("luxury", "luxury"),
    ("watches", "watches"),
    ("bags", "bags"),
    ("shoes", "shoes"),
    ("accessories", "accessories"),
    ("sports", "sports"),
]

ID_PREFIX_BRAND = [
    ("axa-", "arcteryx"),
    ("axg-", "arcteryx"),
    ("axo-", "arcteryx"),
    ("ax-", "arcteryx"),
    ("ce-", "celine"),
    ("ch-", "chanel"),
    ("gc-", "gucci"),
    ("gg-", "galvin-green"),
    ("di-", "dior"),
    ("pr-", "prada"),
    ("lv-", "louis-vuitton"),
    ("mb-", "mulberry"),
    ("vw-", "vivienne-westwood"),
    ("bb-", "burberry"),
    ("bs-", "belstaff"),
    ("ps-", "paul-smith"),
    ("cw-", "christopher-ward"),
    ("lu-", "london-undercover"),
]

BRAND_ALIASES = [
    (re.compile(r"arc'?teryx|아크테릭스", re.I), "arcteryx"),
    (re.compile(r"celine|셀린", re.I), "celine"),
    (re.compile(r"chanel|샤넬", re.I), "chanel"),
    (re.compile(r"gucci|구찌", re.I), "gucci"),
    (re.compile(r"galvin\s*green|갈빈", re.I), "galvin-green"),
    (re.compile(r"dior|디올", re.I), "dior"),
    (re.compile(r"prada|프라다", re.I), "prada"),
    (re.compile(r"louis\s*vuitton|루이\s*비통", re.I), "louis-vuitton"),
    (re.compile(r"mulberry|멀버리", re.I), "mulberry"),
    (re.compile(r"vivienne|웨스트우드|westwood", re.I), "vivienne-westwood"),
    (re.compile(r"burberry|버버리", re.I), "burberry"),
    (re.compile(r"belstaff|벨스타프", re.I), "belstaff"),
    (re.compile(r"paul\s*smith|폴\s*스미스", re.I), "paul-smith"),
    (re.compile(r"christopher\s*ward|크리스토퍼", re.I), "christopher-ward"),
    (re.compile(r"london\s*undercover|런던언더커버", re.I), "london-undercover"),
]

CATALOG_GLOBS = [
    "src/data/**/*catalog.json",
    "src/data/**/*-catalog.json",
]


def brand_key(row: dict) -> str:
    pid = str(row.get("id") or "").lower()
    for prefix, brand in ID_PREFIX_BRAND:
        if pid.startswith(prefix):
            return brand
    blob = " ".join(
        str(x)
        for x in [
            row.get("brand"),
            row.get("subcategory"),
            *list(row.get("tags") or []),
        ]
        if x
    )
    for cre, brand in BRAND_ALIASES:
        if cre.search(blob):
            return brand
    brand = str(row.get("brand") or "").strip().lower()
    if brand:
        return re.sub(r"\s+", "-", brand)
    return pid or "unknown"


def registered_ms(row: dict) -> float:
    for key in ("updatedAt", "registeredAt"):
        raw = row.get(key)
        if not raw:
            continue
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp()
        except Exception:
            continue
    return 0.0


def in_stock(row: dict) -> bool:
    if row.get("inStock") is False:
        return False
    variants = row.get("variants") or []
    if variants:
        return any(v.get("inStock") is not False for v in variants if isinstance(v, dict))
    return True


def load_products() -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for pattern in CATALOG_GLOBS:
        for path in ROOT.glob(pattern):
            if "raw" in path.name or "cache" in path.name:
                continue
            try:
                data = json.loads(path.read_text())
            except Exception:
                continue
            items = data if isinstance(data, list) else data.get("products") or []
            for row in items:
                if not isinstance(row, dict) or not row.get("id"):
                    continue
                pid = str(row["id"])
                if pid in seen:
                    continue
                seen.add(pid)
                rows.append(row)
    # Also parse TS catalogues that have no JSON twin (AX apparel / gear).
    for ts in ROOT.glob("src/data/**/*catalog.ts"):
        if "raw" in ts.name:
            continue
        text = ts.read_text()
        for part in re.split(r"\n  \{\n    id: ", text)[1:]:
            try:
                pid = part.split('"', 2)[1]
            except IndexError:
                continue
            if pid in seen:
                continue
            cat_m = re.search(r'category:\s*"([^"]+)"', part)
            brand_m = re.search(r'brand:\s*"([^"]*)"', part)
            name_m = re.search(r'nameKo:\s*"([^"]*)"', part)
            reg_m = re.search(r'registeredAt:\s*"([^"]+)"', part)
            stock_m = re.search(r"inStock:\s*(true|false)", part)
            row = {
                "id": pid,
                "category": cat_m.group(1) if cat_m else "",
                "brand": brand_m.group(1) if brand_m else "",
                "nameKo": name_m.group(1) if name_m else "",
                "registeredAt": reg_m.group(1) if reg_m else "",
                "inStock": (stock_m.group(1) == "true") if stock_m else True,
            }
            seen.add(pid)
            rows.append(row)
    return rows


def assign(products: list[dict], limit: int = 4) -> dict[str, list[dict]]:
    by_cat: dict[str, list[dict]] = {}
    for row in products:
        cat = str(row.get("category") or "")
        by_cat.setdefault(cat, []).append(row)

    used: set[str] = set()
    out: dict[str, list[dict]] = {}
    for rail_id, category in RAIL_ORDER:
        pool = by_cat.get(category) or []
        stocked = [p for p in pool if in_stock(p)]
        use = stocked if len(stocked) >= limit else pool
        use = sorted(use, key=registered_ms, reverse=True)
        picked: list[dict] = []
        for row in use:
            key = brand_key(row)
            if key in used:
                continue
            picked.append(row)
            if len(picked) >= limit:
                break
        out[rail_id] = picked
        for row in picked:
            used.add(brand_key(row))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail", action="store_true", help="Exit 1 on brand overlap")
    ap.add_argument("--limit", type=int, default=4)
    args = ap.parse_args()

    products = load_products()
    rails = assign(products, limit=args.limit)

    brand_to_rails: dict[str, list[str]] = {}
    report = {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": args.limit,
        "rails": {},
        "brands": {},
    }
    for rail_id, rows in rails.items():
        brands = []
        ids = []
        for row in rows:
            key = brand_key(row)
            brands.append(key)
            ids.append(row.get("id"))
            brand_to_rails.setdefault(key, []).append(rail_id)
            print(
                f"{rail_id:12} {key:20} {row.get('id')} {(row.get('nameKo') or row.get('name') or '')[:40]}",
                flush=True,
            )
        report["rails"][rail_id] = {
            "productIds": ids,
            "brands": brands,
        }

    overlaps = {b: rs for b, rs in brand_to_rails.items() if len(set(rs)) > 1}
    report["brands"] = {b: rs for b, rs in sorted(brand_to_rails.items())}
    report["overlaps"] = overlaps

    out_path = ROOT / "src/data/homepage-rail-picks.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {out_path.relative_to(ROOT)} overlaps={len(overlaps)}", flush=True)

    if overlaps:
        print("OVERLAP", overlaps, flush=True)
        if args.fail:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
