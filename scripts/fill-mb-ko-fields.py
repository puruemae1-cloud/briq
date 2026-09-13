#!/usr/bin/env python3
"""Fill leftover English features/story/dims in mb-catalog.json via curl GTX.

Run after build-mb-catalog.py. Saves cache + catalog every few products so
429s never wipe progress. Safe to re-run.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ko_qa import is_good_korean  # noqa: E402
from mulberry_common import load_json, save_json  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "build_mb_catalog", ROOT / "scripts" / "build-mb-catalog.py"
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)
tr = _mod.tr
CACHE = _mod.CACHE
OUT_JSON = _mod.OUT_JSON
write_catalog = _mod.write_catalog

LATIN = re.compile(r"[A-Za-z]{3,}")


def needs_ko(s: str) -> bool:
    s = (s or "").strip()
    if not s or not LATIN.search(s):
        return False
    if is_good_korean(s):
        return False
    # Pure measurements like "27cm" are fine as-is.
    if re.fullmatch(r"[\d.\s\-–—cmx×/]+", s, flags=re.I):
        return False
    return True


def fill_text(s: str, cache: dict[str, str]) -> str:
    if not needs_ko(s):
        return s
    return tr(s, cache, allow_remote=True, prose=True) or s


def main() -> None:
    cache = load_json(CACHE, {})
    products = load_json(OUT_JSON, [])
    print(f"fill-mb-ko: products={len(products)} cache={len(cache)}", flush=True)
    changed = 0
    for i, p in enumerate(products):
        before = json.dumps(p, ensure_ascii=False, sort_keys=True)
        p["featuresKo"] = [fill_text(f, cache) for f in (p.get("featuresKo") or [])]

        stories = []
        for sec in p.get("storySections") or []:
            sec = dict(sec)
            body = sec.get("bodyKo") or ""
            if needs_ko(body):
                if " · " in body and len(body) < 600:
                    parts = [fill_text(x.strip(), cache) for x in body.split(" · ")]
                    sec["bodyKo"] = " · ".join(parts)
                else:
                    sec["bodyKo"] = fill_text(body[:1800], cache)
            stories.append(sec)
        p["storySections"] = stories

        tech = []
        for row in p.get("techSpecs") or []:
            row = dict(row)
            if needs_ko(row.get("valueKo") or ""):
                row["valueKo"] = fill_text(row["valueKo"], cache)
            tech.append(row)
        p["techSpecs"] = tech

        if needs_ko(p.get("descriptionKo") or ""):
            p["descriptionKo"] = fill_text(p["descriptionKo"][:1800], cache)

        after = json.dumps(p, ensure_ascii=False, sort_keys=True)
        if after != before:
            changed += 1
        if (i + 1) % 5 == 0 or (i + 1) == len(products):
            save_json(CACHE, cache)
            write_catalog(products)
            print(
                f"filled {i+1}/{len(products)} changed={changed} cache={len(cache)}",
                flush=True,
            )
            time.sleep(0.4)

    save_json(CACHE, cache)
    write_catalog(products)
    print(f"done changed={changed} cache={len(cache)}", flush=True)


if __name__ == "__main__":
    main()
