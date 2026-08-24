#!/usr/bin/env python3
"""Batch-translate Prada men's RTW strings into pr-translate-cache.json."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "src/data/pr/pr-mens-rtw-catalog-raw.json"
CACHE_PATH = ROOT / "src/data/pr/pr-translate-cache.json"

spec = importlib.util.spec_from_file_location(
    "build_pr_catalog", ROOT / "scripts/build-pr-catalog.py"
)
build = importlib.util.module_from_spec(spec)
sys.modules["build_pr_catalog"] = build
spec.loader.exec_module(build)


def collect_strings() -> list[str]:
    raw = json.loads(RAW.read_text())
    seen: set[str] = set()
    out: list[str] = []
    for row in raw.get("products") or []:
        for key in ("officialNameEn", "title", "color", "material", "description"):
            val = row.get(key)
            if not val:
                continue
            s = re.sub(r"\s+", " ", str(val).strip())
            if s and s not in seen:
                seen.add(s)
                out.append(s)
        for key in ("details", "materialsCare"):
            for item in row.get(key) or []:
                s = re.sub(r"\s+", " ", str(item).strip())
                if s and s not in seen:
                    seen.add(s)
                    out.append(s)
    return out


def main() -> None:
    if not RAW.exists():
        raise SystemExit(f"Missing {RAW}")

    build.seed_mens_rtw_cache(build._KO)
    strings = collect_strings()
    todo = []
    for s in strings:
        hit = build._KO.get(s)
        if hit and build.en_ratio(hit) < build._MAX_KO_EN_RATIO:
            continue
        if s in build._GLOSSARY:
            continue
        if build.en_ratio(s) < 0.35 or len(s) < 3:
            continue
        todo.append(s)

    print(f"seed-pr-mens-rtw: {len(strings)} unique, {len(todo)} to translate", flush=True)
    for i, s in enumerate(todo, start=1):
        ko = build.t(s)
        if ko and build.en_ratio(ko) < build._MAX_KO_EN_RATIO:
            build._KO[s] = ko
        if i % 25 == 0 or i == len(todo):
            CACHE_PATH.write_text(json.dumps(build._KO, ensure_ascii=False, indent=2))
            print(f"  translated {i}/{len(todo)}", flush=True)
        time.sleep(0.08)

    CACHE_PATH.write_text(json.dumps(build._KO, ensure_ascii=False, indent=2))
    print(f"Done — cache keys={len(build._KO)}", flush=True)


if __name__ == "__main__":
    main()
