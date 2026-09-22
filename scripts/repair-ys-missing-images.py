#!/usr/bin/env python3
"""Re-download YS PDP photos that are missing from disk / product-images tag.

  python3 scripts/repair-ys-missing-images.py
  python3 scripts/repair-ys-missing-images.py --push
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ysl_common import (  # noqa: E402
    best_image_urls,
    fetch_pdp,
    materialize_images,
    pdp_path_from_url,
)

TAG = "product-images"
CATALOG = ROOT / "src/data/ys/ys-catalog.json"


def tag_paths() -> set[str]:
    subprocess.run(
        ["git", "fetch", "origin", f"refs/tags/{TAG}:refs/tags/{TAG}"],
        cwd=ROOT,
        capture_output=True,
    )
    r = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", TAG, "public/products/ys-pdp"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {ln.strip() for ln in r.stdout.splitlines() if ln.strip()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true", help="Push recovered SKUs to product-images")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    products = json.loads(CATALOG.read_text())
    on_tag = tag_paths()
    missing: list[dict] = []
    for p in products:
        img = p.get("image") or ""
        if not isinstance(img, str) or not img.startswith("/products/ys-pdp/"):
            continue
        if f"public{img}" not in on_tag:
            missing.append(p)

    print(f"YS catalog CDN-missing primary images: {len(missing)}", flush=True)
    recovered: list[str] = []
    failed: list[str] = []

    for i, p in enumerate(missing, 1):
        if args.limit and i > args.limit:
            break
        pid = str(p.get("id") or "")
        sku = pid.removeprefix("ys-")
        source = str(p.get("sourceUrl") or "")
        path = pdp_path_from_url(source) if source else ""
        print(f"[{i}/{len(missing)}] {pid}", flush=True)
        urls: list[str] = []
        if path:
            try:
                pp = fetch_pdp(path)
                prod = pp.get("product") or {}
                urls = best_image_urls(prod.get("images") or [])
            except Exception as e:
                print(f"  WARN pdp fetch: {e}", flush=True)
        local = materialize_images(sku, urls) if urls else []
        if not local:
            failed.append(pid)
            print("  FAIL no images", flush=True)
            continue
        # Rewrite catalog paths to recovered local files
        p["image"] = local[0]
        p["images"] = local
        p["hoverImage"] = local[1] if len(local) > 1 else local[0]
        recovered.append(sku)
        print(f"  OK {len(local)} files", flush=True)
        time.sleep(0.15)

    if recovered:
        CATALOG.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
        print(f"Updated {CATALOG} ({len(recovered)} recovered)", flush=True)

        only = ROOT / "tmp" / "ys-repaired-skus.txt"
        only.parent.mkdir(parents=True, exist_ok=True)
        only.write_text("\n".join(recovered) + "\n")
        if args.push:
            cmd = [
                sys.executable,
                "-u",
                "scripts/push-product-images-tag.py",
                "--dirs",
                "ys-pdp",
                "--merge",
                "--skip-whiten",
                "--skip-purge",
                "--only-file",
                str(only),
            ]
            print("+", " ".join(cmd), flush=True)
            rc = subprocess.run(cmd, cwd=ROOT).returncode
            if rc != 0:
                rc = subprocess.run(
                    [
                        sys.executable,
                        "-u",
                        "scripts/push-missing-pdp-chunked.py",
                        "--dirs",
                        "ys-pdp",
                        "--chunk",
                        "4",
                        "--max-waves",
                        "40",
                    ],
                    cwd=ROOT,
                ).returncode
            if rc != 0:
                print("ERROR push failed", flush=True)
                return rc

    print(f"recovered={len(recovered)} failed={len(failed)}", flush=True)
    if failed:
        print("failed ids:", ", ".join(failed[:20]), flush=True)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
