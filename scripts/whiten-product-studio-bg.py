#!/usr/bin/env python3
"""CLI: whiten light studio mats on catalog PDP photos.

See studio_whiten.py for the shared library used by scrapers and image pushes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from studio_whiten import DEFAULT_DIRS, whiten_dirs  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dirs",
        nargs="*",
        default=DEFAULT_DIRS,
        help="Product image roots under public/products/",
    )
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    whiten_dirs(args.dirs, workers=args.workers, limit=args.limit)


if __name__ == "__main__":
    main()
    sys.exit(0)
