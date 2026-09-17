#!/usr/bin/env python3
"""Retranslate AllSaints Korean PDP fields that still look English."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from al_common import load_json, save_json  # noqa: E402
from ko_qa import is_good_korean  # noqa: E402

CATALOG = ROOT / "src/data/al/al-catalog.json"
CACHE = ROOT / "src/data/al/al-translate-cache.json"


def _load_build():
    spec = importlib.util.spec_from_file_location("build_al", ROOT / "scripts/build-al-catalog.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def needs_ko(s: str) -> bool:
    t = (s or "").strip()
    if not t:
        return False
    return not is_good_korean(t, max_ratio=0.40)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="all")
    args = ap.parse_args()
    if not CATALOG.exists():
        print("no catalog yet")
        return 0
    mod = _load_build()
    cache = load_json(CACHE, {})
    products = json.loads(CATALOG.read_text(encoding="utf-8"))
    if args.category != "all":
        cats = {c.strip() for c in args.category.split(",") if c.strip()}
        scoped = [p for p in products if p.get("category") in cats]
    else:
        scoped = products
    changed = 0
    for p in scoped:
        if needs_ko(str(p.get("descriptionKo") or "")):
            src = str(p.get("name") or "")
            # Prefer English source if description still EN
            p["descriptionKo"] = mod.translate(str(p.get("descriptionKo") or src), cache)
            changed += 1
        feats = []
        for f in p.get("featuresKo") or []:
            if needs_ko(str(f)):
                feats.append(mod.translate(str(f), cache))
                changed += 1
            else:
                feats.append(f)
        if feats:
            p["featuresKo"] = feats
        for sec in p.get("storySections") or []:
            body = str(sec.get("bodyKo") or "")
            if needs_ko(body):
                # translate line by line for bullet blocks
                lines = []
                for line in body.split("\n"):
                    if line.startswith("· ") and needs_ko(line[2:]):
                        lines.append("· " + mod.translate(line[2:], cache))
                    elif needs_ko(line):
                        lines.append(mod.translate(line, cache))
                    else:
                        lines.append(line)
                sec["bodyKo"] = "\n".join(lines)
                changed += 1
        for spec in p.get("techSpecs") or []:
            if (spec or {}).get("labelKo") == "제품 코드":
                continue
            val = str((spec or {}).get("valueKo") or "")
            if needs_ko(val):
                spec["valueKo"] = mod.translate(val, cache)
                changed += 1
        note = ((p.get("sizeChart") or {}).get("noteKo") or "")
        if needs_ko(note):
            p["sizeChart"]["noteKo"] = mod.translate(note, cache)
            changed += 1
    save_json(CACHE, cache)
    CATALOG.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK retranslate touched_fields≈{changed} products={len(scoped)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
