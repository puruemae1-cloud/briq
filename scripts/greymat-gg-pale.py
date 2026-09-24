#!/usr/bin/env python3
"""Rembg-only greymat for Galvin Green pale colourways (never soft remap)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from gg_pale_colour import pale_gg_handles  # noqa: E402
from gg_pale_rembg import rembg_only_greymat  # noqa: E402


def main() -> None:
    root = ROOT / "public/products/gg-pdp"
    handles = sorted(pale_gg_handles())
    files: list[Path] = []
    for h in handles:
        files.extend(sorted((root / h).glob("*.jpg")))
    print(f"rembg-only {len(files)} images across {len(handles)} handles", flush=True)
    ok = skip = fail = 0
    for i, path in enumerate(files, 1):
        status = rembg_only_greymat(path)
        if status.startswith("ok"):
            ok += 1
        elif status.startswith("skip"):
            skip += 1
        else:
            fail += 1
        if i <= 12 or i % 40 == 0 or i == len(files):
            print(
                f"{i}/{len(files)} {path.parent.name}/{path.name} {status} "
                f"(ok={ok} skip={skip} fail={fail})",
                flush=True,
            )
    print(f"done ok={ok} skip={skip} fail={fail}", flush=True)
    if ok == 0 and fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
