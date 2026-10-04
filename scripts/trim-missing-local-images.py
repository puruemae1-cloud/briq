#!/usr/bin/env python3
"""Drop catalogue photo paths whose files are not on disk under public/.

A product keeps its remaining photos (primary falls back to the first one);
a product left with no photo is removed. Use before image guards so one
missing gallery frame does not block a whole brand's stock sync.

  python3 scripts/trim-missing-local-images.py src/data/al/al-catalog.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def on_disk(src: object) -> bool:
    if not isinstance(src, str) or not src.startswith("/products/"):
        return True
    path = ROOT / "public" / src.split("?")[0].lstrip("/")
    return path.is_file() and path.stat().st_size >= 800


def fix(item: dict) -> bool:
    if isinstance(item.get("images"), list):
        item["images"] = [s for s in item["images"] if on_disk(s)]
    if item.get("hoverImage") and not on_disk(item["hoverImage"]):
        item.pop("hoverImage")
    if item.get("image") and not on_disk(item["image"]):
        item["image"] = (item.get("images") or [None])[0]
    return bool(item.get("image"))


def main() -> int:
    for arg in sys.argv[1:]:
        path = Path(arg)
        products = json.loads(path.read_text(encoding="utf-8"))
        before = json.dumps(products, ensure_ascii=False)
        kept = []
        for p in products:
            keep = fix(p)
            for v in p.get("variants") or []:
                if not fix(v):
                    v["image"] = p.get("image")
            if keep:
                kept.append(p)
        if json.dumps(kept, ensure_ascii=False) != before:
            path.write_text(json.dumps(kept, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"{arg}: removed {len(products) - len(kept)} product(s) without photos; trimmed missing frames")
    return 0


if __name__ == "__main__":
    sys.exit(main())
