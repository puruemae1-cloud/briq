#!/usr/bin/env python3
"""Retry Prada men's RTW Korean copy when translate APIs recover from 429.

Exits:
  0 — nothing pending, or batch completed (maybe partial)
  2 — translate API still rate-limited (retry later)
  1 — fatal error

Usage:
  python3 scripts/retry-pr-mens-rtw-ko.py
  python3 scripts/retry-pr-mens-rtw-ko.py --rebuild --max-batch 60
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "src/data/pr/pr-mens-rtw-catalog-raw.json"
CACHE_PATH = ROOT / "src/data/pr/pr-translate-cache.json"
STATE_PATH = ROOT / "src/data/pr/pr-mens-rtw-translate-state.json"

spec = importlib.util.spec_from_file_location(
    "build_pr_catalog", ROOT / "scripts/build-pr-catalog.py"
)
build = importlib.util.module_from_spec(spec)
sys.modules["build_pr_catalog"] = build
spec.loader.exec_module(build)


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def probe_translate_api() -> bool:
    """Return True when gtx responds (not 429)."""
    q = "Cotton shirt"
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl=ko&dt=t&q={urllib.parse.quote(q)}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode())
        out = "".join(part[0] for part in data[0] if part and part[0])
        return bool(out.strip()) and build.en_ratio(out) < 0.5
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return False
        return False
    except Exception:
        return False


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


def pending_strings() -> list[str]:
    build.seed_mens_rtw_cache(build._KO)
    todo: list[str] = []
    for s in collect_strings():
        hit = build._KO.get(s)
        if hit and build.en_ratio(hit) < build._MAX_KO_EN_RATIO:
            continue
        if s in build._GLOSSARY:
            continue
        if build.en_ratio(s) < 0.35 or len(s) < 3:
            continue
        todo.append(s)
    return todo


def write_state(**extra: object) -> None:
    payload = {
        "updatedAt": _now_iso(),
        **extra,
    }
    STATE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-batch", type=int, default=80)
    ap.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild mens-rtw catalog after new translations land",
    )
    ap.add_argument(
        "--skip-probe",
        action="store_true",
        help="Skip API probe (use when caller already checked)",
    )
    args = ap.parse_args()

    if not RAW.exists():
        raise SystemExit(f"Missing {RAW}")

    todo = pending_strings()
    if not todo:
        write_state(status="complete", pending=0, message="All strings translated")
        print("retry-pr-mens-rtw-ko: nothing pending", flush=True)
        return

    if not args.skip_probe and not probe_translate_api():
        write_state(
            status="rate_limited",
            pending=len(todo),
            message="Translate API 429 — will retry on next schedule",
        )
        print(
            f"retry-pr-mens-rtw-ko: API rate-limited, {len(todo)} pending",
            flush=True,
        )
        raise SystemExit(2)

    batch = todo[: max(1, args.max_batch)]
    print(
        f"retry-pr-mens-rtw-ko: translating {len(batch)}/{len(todo)} pending…",
        flush=True,
    )
    added = 0
    for i, s in enumerate(batch, start=1):
        ko = build.t(s)
        if ko and build.en_ratio(ko) < build._MAX_KO_EN_RATIO:
            if build._KO.get(s) != ko:
                added += 1
            build._KO[s] = ko
        if i % 20 == 0 or i == len(batch):
            CACHE_PATH.write_text(json.dumps(build._KO, ensure_ascii=False, indent=2))
            print(f"  batch {i}/{len(batch)} (+{added} new)", flush=True)
        time.sleep(0.35)

    CACHE_PATH.write_text(json.dumps(build._KO, ensure_ascii=False, indent=2))
    remaining = len(pending_strings())
    write_state(
        status="in_progress" if remaining else "complete",
        pending=remaining,
        lastBatch=len(batch),
        lastAdded=added,
    )
    print(f"Done batch — added {added}, {remaining} still pending", flush=True)

    if args.rebuild and added > 0:
        print("Rebuilding Prada mens-rtw catalog…", flush=True)
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/build-pr-catalog.py"),
                "--only",
                "mens-rtw",
            ],
            cwd=str(ROOT),
            check=True,
        )


if __name__ == "__main__":
    main()
