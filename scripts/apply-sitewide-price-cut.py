#!/usr/bin/env python3
"""Apply a silent site-wide KRW price cut (no new sale badges).

Cuts `price` and existing `compareAtPrice` by the same factor so already-on-sale
items keep the same %-OFF badge, and full-price items stay badge-free (no new
compareAt is invented). Flannels (`src/data/fl/**`) is skipped.

  python3 scripts/apply-sitewide-price-cut.py
  python3 scripts/apply-sitewide-price-cut.py --factor 0.95 --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "data"
PRICE_KEYS = {"price", "compareAtPrice"}
# Do not touch source FX, fees, etc.
SKIP_KEYS = {
    "gbpPrice",
    "gbpListPrice",
    "feeKrw",
    "braceletResize",
}


def round_krw(n: float) -> int:
    if n <= 0:
        return 0
    # Catalogues are almost always 천원 단위.
    return max(1000, int(round(n / 1000.0) * 1000))


def cut_number(n: float, factor: float) -> int:
    return round_krw(float(n) * factor)


def is_flannels_path(path: Path) -> bool:
    parts = path.parts
    return "fl" in parts and "data" in parts and parts[parts.index("data") + 1] == "fl"


def cut_obj(obj, factor: float, stats: dict) -> None:
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k in SKIP_KEYS:
                continue
            if k in PRICE_KEYS and isinstance(v, (int, float)) and not isinstance(v, bool):
                new = cut_number(v, factor)
                if new != int(v):
                    obj[k] = new
                    stats["fields"] += 1
                    stats["delta"] += int(v) - new
                continue
            cut_obj(v, factor, stats)
    elif isinstance(obj, list):
        for item in obj:
            cut_obj(item, factor, stats)


def process_json(path: Path, factor: float, dry: bool) -> dict:
    data = json.loads(path.read_text())
    stats = {"fields": 0, "delta": 0, "products": 0}
    if isinstance(data, list):
        stats["products"] = len(data)
        cut_obj(data, factor, stats)
    elif isinstance(data, dict):
        prods = data.get("products")
        if isinstance(prods, list):
            stats["products"] = len(prods)
        cut_obj(data, factor, stats)
    else:
        return stats
    if not dry and stats["fields"]:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return stats


_TS_PRICE_RE = re.compile(
    r"(?P<prefix>\b(?P<key>price|compareAtPrice)\s*:\s*)(?P<num>\d+)\b"
)


def process_ts(path: Path, factor: float, dry: bool) -> dict:
    text = path.read_text()
    stats = {"fields": 0, "delta": 0, "products": text.count("\n    id:")}

    def repl(m: re.Match) -> str:
        old = int(m.group("num"))
        new = cut_number(old, factor)
        if new != old:
            stats["fields"] += 1
            stats["delta"] += old - new
        return f"{m.group('prefix')}{new}"

    new_text = _TS_PRICE_RE.sub(repl, text)
    if not dry and new_text != text:
        path.write_text(new_text)
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--factor", type=float, default=0.95)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not (0.5 < args.factor < 1.0):
        print("factor must be between 0.5 and 1.0", file=sys.stderr)
        return 2

    # `*-catalog.ts` already includes straps/lifestyle (*-straps-catalog.ts).
    paths = sorted(
        {
            *DATA.glob("*/*-catalog.json"),
            *DATA.glob("*/*-catalog.ts"),
        }
    )

    total_files = 0
    total_fields = 0
    total_delta = 0
    skipped = []

    for path in paths:
        if is_flannels_path(path):
            skipped.append(str(path.relative_to(ROOT)))
            continue
        if path.suffix == ".json":
            st = process_json(path, args.factor, args.dry_run)
        else:
            st = process_ts(path, args.factor, args.dry_run)
        if st["fields"]:
            total_files += 1
            total_fields += st["fields"]
            total_delta += st["delta"]
            print(
                f"{path.relative_to(ROOT)}: fields={st['fields']} "
                f"~products={st.get('products', '?')} delta_krw={st['delta']:,}",
                flush=True,
            )

    print(
        f"done files={total_files} fields={total_fields} "
        f"total_delta_krw={total_delta:,} factor={args.factor} "
        f"dry={args.dry_run} skipped_fl={len(skipped)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
