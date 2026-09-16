#!/usr/bin/env python3
"""Back-compat wrapper — accessories Korean QA via check-vw-korean.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "check-vw-korean.py"),
        "--category",
        "accessories",
        *sys.argv[1:],
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
