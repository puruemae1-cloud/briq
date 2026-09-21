#!/usr/bin/env python3
"""Push AllSaints (or any brand) PDP images missing from the product-images tag.

Pushes in small waves so GitHub force-push of the giant tag does not hang /
disconnect (full missing-list pushes regularly fail with pack-objects / hangup).

Usage:
  python3 scripts/push-missing-pdp-chunked.py --dirs al-pdp
  python3 scripts/push-missing-pdp-chunked.py --dirs al-pdp --chunk 12 --max-waves 50
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> int:
    print(f"→ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=str(ROOT), env=env).returncode


def list_missing(dirs: list[str], out: Path) -> list[str]:
    rc = subprocess.run(
        [
            sys.executable,
            "scripts/list-missing-pdp-on-cdn.py",
            "--dirs",
            *dirs,
            "--write",
            str(out),
        ],
        cwd=str(ROOT),
    )
    # rc 1 = missing found
    if not out.exists():
        return []
    return [ln.strip() for ln in out.read_text(encoding="utf-8").splitlines() if ln.strip()]


def sync_tag_to_remote() -> None:
    r = subprocess.run(
        ["git", "ls-remote", "origin", "refs/tags/product-images"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    tip = (r.stdout.split() or [""])[0]
    if not tip:
        print("WARN: could not read remote product-images tip", flush=True)
        return
    subprocess.run(
        ["git", "update-ref", "refs/tags/product-images", tip],
        cwd=str(ROOT),
        check=True,
    )
    print(f"synced local product-images → {tip[:12]}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", required=True)
    ap.add_argument(
        "--chunk",
        type=int,
        default=2,
        help="SKUs per force-push wave (default 2 — larger packs often hang the product-images tag)",
    )
    ap.add_argument("--max-waves", type=int, default=80)
    ap.add_argument("--skip-whiten", action="store_true", default=True)
    args = ap.parse_args()

    # Bottega trees are large JPEGs — prefer even smaller waves unless overridden.
    if args.chunk >= 4 and any(d.startswith("bv") for d in args.dirs):
        print(
            f"NOTE: lowering chunk {args.chunk} → 2 for BV (pack-objects stability)",
            flush=True,
        )
        args.chunk = 2

    env = os.environ.copy()
    env["SKIP_TAG_FETCH"] = "1"
    env.setdefault("PYTHONUNBUFFERED", "1")

    miss_path = Path("/tmp/briq-cdn-missing.txt")
    fails = 0
    for wave in range(args.max_waves):
        skus = list_missing(args.dirs, miss_path)
        print(f"WAVE {wave}: missing={len(skus)}", flush=True)
        if not skus:
            print("OK — no missing SKUs on product-images tag", flush=True)
            return 0

        batch = skus[: max(1, args.chunk)]
        batch_path = Path(f"/tmp/briq-cdn-wave-{wave}.txt")
        batch_path.write_text("\n".join(batch) + "\n", encoding="utf-8")
        print(f"  pushing {len(batch)}: {', '.join(batch[:4])}…", flush=True)

        cmd = [
            sys.executable,
            "-u",
            "scripts/push-product-images-tag.py",
            "--dirs",
            *args.dirs,
            "--merge",
            "--only-file",
            str(batch_path),
            "--skip-purge",
        ]
        if args.skip_whiten:
            cmd.append("--skip-whiten")

        rc = run(cmd, env=env)
        if rc == 0:
            fails = 0
            continue

        fails += 1
        print(f"WARN wave {wave} failed rc={rc} — reset tag to remote and retry half", flush=True)
        sync_tag_to_remote()
        half = batch[: max(1, len(batch) // 2)]
        batch_path.write_text("\n".join(half) + "\n", encoding="utf-8")
        rc2 = run(cmd, env=env)
        if rc2 != 0:
            sync_tag_to_remote()
            if fails >= 6:
                print("ERROR: too many consecutive CDN push failures", flush=True)
                return rc2
            time.sleep(8)
            continue
        fails = 0

    left = list_missing(args.dirs, miss_path)
    if left:
        print(f"ERROR: still missing {len(left)} after {args.max_waves} waves", flush=True)
        return 1
    print("OK — CDN catch-up complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
