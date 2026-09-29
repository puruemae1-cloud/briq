#!/usr/bin/env python3
"""Weekly Bottega Veneta stock + catalogue sync for Briq.

  python3 scripts/weekly-bv-stock-sync.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "src/data/bv/bv-catalog.json"


def run(cmd: list[str], env: dict[str, str]) -> None:
    print(f"→ {' '.join(cmd)}", flush=True)
    subprocess.check_call(cmd, cwd=str(ROOT), env=env)


def stock_map(path: Path) -> dict[str, bool]:
    if not path.exists():
        return {}
    out: dict[str, bool] = {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return {}
    for p in data:
        sku = str(p.get("sku") or p.get("id") or "").strip()
        if not sku:
            continue
        out[sku.upper()] = bool(p.get("inStock", True))
    return out


def print_delta(before: dict[str, bool], after: dict[str, bool]) -> None:
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    restocked = sorted(s for s in after if s in before and not before[s] and after[s])
    sold_out = sorted(s for s in after if s in before and before[s] and not after[s])
    print(
        f"Bottega Veneta delta: +{len(added)} new, -{len(removed)} dropped, "
        f"{len(restocked)} restocked, {len(sold_out)} sold-out "
        f"(catalogue {len(before)} → {len(after)})",
        flush=True,
    )
    if added[:12]:
        print(f"  new sample: {', '.join(added[:12])}", flush=True)
    if restocked[:12]:
        print(f"  restocked sample: {', '.join(restocked[:12])}", flush=True)
    if sold_out[:12]:
        print(f"  sold-out sample: {', '.join(sold_out[:12])}", flush=True)
    if removed[:12]:
        print(f"  dropped sample: {', '.join(removed[:12])}", flush=True)


def main() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from weekly_korean_gate import check_new_korean, utc_now_iso

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env["BV_REFRESH_STOCK"] = "1"
    # Never build with offline KO — English leftovers were shipping to PDP.
    env.pop("BV_OFFLINE_KO", None)
    env["PYTHONPATH"] = f"{ROOT / 'scripts'}:{env.get('PYTHONPATH', '')}"
    print("BV_REFRESH_STOCK=1 (re-fetch PLP availability + new SKUs)", flush=True)
    since = utc_now_iso()

    before = stock_map(OUT_JSON)
    print(f"Previous catalogue SKUs: {len(before)}", flush=True)

    run([sys.executable, "-u", "scripts/scrape-bv-hub.py", "--all"], env)
    run([sys.executable, "-u", "scripts/build-bv-catalog.py"], env)

    after = stock_map(OUT_JSON)
    print_delta(before, after)

    # Full-catalog KO repair (Bing) — build-time gtx often leaves EN names/bodies.
    last_rc = 1
    for attempt in range(1, 6):
        print(f"== BV KO retranslate attempt {attempt}/5 ==", flush=True)
        r = subprocess.run(
            [sys.executable, "-u", "scripts/retranslate-bv-ko.py", "--workers", "2"],
            cwd=str(ROOT),
            env=env,
        )
        last_rc = r.returncode
        qa = subprocess.run(
            [
                sys.executable,
                "scripts/check-catalog-korean.py",
                "--brand",
                "bv",
                "--strict",
                "--fail",
            ],
            cwd=str(ROOT),
            env=env,
        )
        # Also fail when product titles are still English (nameKo).
        name_qa = subprocess.run(
            [sys.executable, "-u", "scripts/check-bv-nameko.py", "--fail"],
            cwd=str(ROOT),
            env=env,
        )
        if qa.returncode == 0 and name_qa.returncode == 0:
            break
        print(
            f"WARN attempt {attempt}: retranslate_rc={last_rc} "
            f"qa_rc={qa.returncode} name_rc={name_qa.returncode}",
            flush=True,
        )
    else:
        # Ship stock on the committed Korean copy instead of dropping the sync;
        # untranslated new SKUs wait for the next run.
        import importlib.util

        from ko_qa import find_hybrid_fields
        from stock_only_fallback import apply_fallback

        spec = importlib.util.spec_from_file_location(
            "check_bv_nameko", ROOT / "scripts" / "check-bv-nameko.py"
        )
        names = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(names)
        apply_fallback(
            OUT_JSON,
            lambda p: names.name_ok(p) and not find_hybrid_fields([p]),
        )
        run([sys.executable, "scripts/check-catalog-korean.py", "--brand", "bv", "--strict", "--fail"], env)
        run([sys.executable, "-u", "scripts/check-bv-nameko.py", "--fail"], env)

    # KO repair can rewrite nameKo, so make every title unique (colour, then real differences) last.
    run([sys.executable, "-u", "scripts/fix-bv-name-colors.py"], env)
    # Bags/shoes PLPs read slices, not bv-catalog.json — keep them in step.
    run([sys.executable, "-u", "scripts/extract-bags-catalogs.py", "bv"], env)
    run([sys.executable, "-u", "scripts/extract-shoes-catalogs.py", "bv"], env)

    check_new_korean("bv", since)
    print("Bottega Veneta weekly sync complete.", flush=True)


if __name__ == "__main__":
    main()
