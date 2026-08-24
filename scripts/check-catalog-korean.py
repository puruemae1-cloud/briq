#!/usr/bin/env python3
"""Check Briq product catalogues for hybrid / leftover English in Korean fields.

Examples:
  python3 scripts/check-catalog-korean.py --brand pr --fail
  python3 scripts/check-catalog-korean.py --brand all --new-since 2026-08-24T00:00:00Z --fail
  python3 scripts/check-catalog-korean.py --brand gc --ids gc-abc,gc-def --fail

Weekly syncs should pass --new-since <sync-start-iso> so only newly registered
SKUs block the job (legacy hybrid copy is reported but not hard-failed unless
--strict is set).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ko_qa import CATALOG_PATHS, MAX_KO_EN_RATIO, check_brand  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--brand",
        default="all",
        help=f"Brand key or 'all'. Known: {', '.join(sorted(CATALOG_PATHS))}",
    )
    ap.add_argument(
        "--new-since",
        default=None,
        help="Only check products with registeredAt >= this ISO timestamp",
    )
    ap.add_argument(
        "--ids",
        default="",
        help="Comma-separated product ids to check (overrides --new-since)",
    )
    ap.add_argument(
        "--max-ratio",
        type=float,
        default=MAX_KO_EN_RATIO,
        help=f"Max Latin-letter ratio allowed in KO fields (default {MAX_KO_EN_RATIO})",
    )
    ap.add_argument(
        "--fail",
        action="store_true",
        help="Exit 1 when any checked field fails Korean QA",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Check every product in the brand (ignore --new-since)",
    )
    ap.add_argument("--limit", type=int, default=40, help="Max rows to print")
    args = ap.parse_args()

    brands = sorted(CATALOG_PATHS) if args.brand == "all" else [args.brand]
    ids = {x.strip() for x in args.ids.split(",") if x.strip()} or None
    new_since = None if args.strict or ids else args.new_since

    all_bad: list[tuple[str, str, str, float, str]] = []
    for brand in brands:
        try:
            bad = check_brand(
                brand,
                max_ratio=args.max_ratio,
                ids=ids,
                new_since=new_since,
            )
        except KeyError as e:
            print(f"error: {e}", flush=True)
            return 2
        scope = (
            f"ids={len(ids)}"
            if ids
            else ("strict" if args.strict or not new_since else f"new-since={new_since}")
        )
        print(f"{brand}: bad={len(bad)} ({scope})", flush=True)
        all_bad.extend(bad)

    for brand, pid, field, ratio, snippet in all_bad[: args.limit]:
        print(f"  {brand} {pid} {field} en_ratio={ratio:.2f} {snippet}", flush=True)
    if len(all_bad) > args.limit:
        print(f"  … +{len(all_bad) - args.limit} more", flush=True)

    if all_bad and args.fail:
        print(
            f"Korean QA failed ({len(all_bad)} fields). "
            "Translate all English PDP copy to natural Korean before shipping.",
            flush=True,
        )
        return 1
    if not all_bad:
        print("OK — checked Korean PDP fields look good.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
