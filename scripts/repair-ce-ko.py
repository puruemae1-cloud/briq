#!/usr/bin/env python3
"""Purge hybrid CE translate-cache entries and rebuild Korean PDP prose.

Safe to re-run. Do NOT set BRIQ_FAST_BUILD — prose needs gtx/LINE_MAP.
Optional: CE_RAW_FILTER=men-rtw to limit to one raw family file.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ko_qa import is_good_korean  # noqa: E402

CACHE = ROOT / "src/data/ce/ce-translate-cache.json"
STATE = ROOT / "tmp/ce-ko-repair-state.json"
LOG = ROOT / "tmp/ce-ko-repair.log"


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = msg.rstrip()
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_ce_build():
    spec = importlib.util.spec_from_file_location(
        "build_ce_catalog", ROOT / "scripts/build-ce-catalog.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def purge_bad_cache(cache: dict[str, str]) -> int:
    removed = 0
    for k, v in list(cache.items()):
        if v is None:
            cache.pop(k, None)
            removed += 1
            continue
        if not is_good_korean(v):
            cache.pop(k, None)
            removed += 1
    return removed


def main() -> int:
    os.environ.pop("BRIQ_FAST_BUILD", None)
    ce = load_ce_build()
    cache = ce.translate_cache()
    removed = purge_bad_cache(cache)
    ce.save_json(CACHE, cache)
    log(f"purged_bad_cache={removed} remaining={len(cache)}")

    raw_filter = (os.environ.get("CE_RAW_FILTER") or "").strip().lower()
    paths = ce.celine_raw_paths()
    if raw_filter:
        paths = [p for p in paths if raw_filter in p.name.lower()]
        log(f"raw_filter={raw_filter} paths={len(paths)}")
    if not paths:
        log("NO_RAW_PATHS")
        return 1

    need: list[str] = []
    seen: set[str] = set()
    for path in paths:
        payload = ce.load_json(path, {"products": []})
        for row in payload.get("products") or []:
            for label in ("DETAILS", "CARE AND MAINTENANCE", "Size and fit"):
                for line in ce.extract_lines(row, label):
                    if not line or line in seen:
                        continue
                    seen.add(line)
                    cached = cache.get(line)
                    if cached and is_good_korean(cached):
                        continue
                    if is_good_korean(line):
                        cache[line] = line
                        continue
                    need.append(line)

    log(f"unique_lines={len(seen)} need_translate={len(need)}")
    t0 = time.time()
    ok = 0
    fail = 0
    for i, line in enumerate(need, 1):
        out = ce.tr(line, cache, allow_remote=True, prose=True)
        if out and is_good_korean(out):
            ok += 1
        else:
            fail += 1
            if fail <= 8:
                log(f"FAIL_SAMPLE {line!r} -> {out!r}")
        if i % 40 == 0:
            ce.save_json(CACHE, cache)
            log(f"progress {i}/{len(need)} ok={ok} fail={fail} elapsed={time.time()-t0:.0f}s")
            time.sleep(0.4)

    ce.save_json(CACHE, cache)
    log(f"prefetch_done ok={ok} fail={fail}")

    # Full rebuild (uses repaired cache + prose=True path)
    log("rebuild_start")
    # Re-exec main of build-ce-catalog with current env (no FAST_BUILD)
    import subprocess

    env = os.environ.copy()
    env.pop("BRIQ_FAST_BUILD", None)
    env["PYTHONUNBUFFERED"] = "1"
    if raw_filter:
        # build reads all raw files; for filtered repair we still rebuild full catalog
        # after prefetch so other families keep prior good cache.
        pass
    r = subprocess.run(
        [sys.executable, "scripts/build-ce-catalog.py"],
        cwd=ROOT,
        env=env,
    )
    if r.returncode != 0:
        log(f"rebuild_fail rc={r.returncode}")
        return r.returncode
    log("rebuild_ok")

    # Spot-check example SKU
    products = json.loads((ROOT / "src/data/ce/ce-catalog.json").read_text())
    ex = next((p for p in products if p.get("id") == "ce-2z063670q-38aw"), None)
    if ex:
        feats = ex.get("featuresKo") or []
        bad = [f for f in feats if not is_good_korean(f)]
        log(f"example featuresKo={feats}")
        log(f"example_bad={bad}")
        log(f"example_desc={ex.get('descriptionKo')!r}")
    else:
        log("example_missing")

    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(
        json.dumps(
            {
                "purged": removed,
                "need": len(need),
                "ok": ok,
                "fail": fail,
                "at": time.time(),
            },
            indent=2,
        )
        + "\n"
    )
    return 0 if fail == 0 else 0  # catalog may still improve; don't hard-fail on residual EN


if __name__ == "__main__":
    raise SystemExit(main())
