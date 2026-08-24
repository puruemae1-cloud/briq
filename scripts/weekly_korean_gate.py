#!/usr/bin/env python3
"""Shared helper for weekly sync scripts: fail if new SKUs have English PDP copy."""
from __future__ import annotations

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


def check_new_korean(brand: str, since_iso: str) -> None:
    """Hard-fail when products registered at/after since_iso still have English."""
    print(f"Checking Korean copy for new {brand} products since {since_iso}…", flush=True)
    subprocess.check_call(
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
