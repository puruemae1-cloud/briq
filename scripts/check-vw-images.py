#!/usr/bin/env python3
"""Fail weekly VW sync when raw galleries still contain foreign style shots."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail", action="store_true")
    ap.add_argument("--family", default="")
    args = ap.parse_args()
    cmd = [sys.executable, str(ROOT / "scripts/sanitize-vw-images.py"), "--check"]
    if args.family:
        cmd.extend(["--family", args.family])
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0 and args.fail:
        return 1
    return 0 if r.returncode == 0 else (1 if args.fail else 0)


if __name__ == "__main__":
    raise SystemExit(main())
