#!/usr/bin/env python3
"""Check that every product image the shop serves exists on the product-images tag.

References are collected from what the site actually reads: every
`readCatalogJson("…")` catalogue and every TS module under src/ (TS-literal
catalogues such as Christopher Ward / Galvin Green / Arc'teryx). The tag's file
list comes from a tree-only fetch (no blobs, ~10MB), so no checkout is needed.

  python3 scripts/audit-catalog-images.py               # report, exit 1 on misses
  python3 scripts/audit-catalog-images.py --write tmp/missing-images.txt
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
REPO_URL = f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'puruemae1-cloud/briq')}.git"
TAG = "product-images"
IMG_RE = re.compile(r"/products/([\w.-]+/[^\"'\s)?#\\]+?\.(?:jpg|jpeg|png|webp|gif|avif))", re.I)


def catalogue_sources() -> list[Path]:
    files: list[Path] = []
    for p in SRC.rglob("*"):
        if p.suffix in {".ts", ".tsx"}:
            files.append(p)
            text = p.read_text(encoding="utf-8", errors="ignore")
            for rel in re.findall(r'readCatalogJson\(\s*"([^"]+\.json)"\s*\)', text):
                files.append(SRC / "data" / rel)
    return sorted(set(files))


def referenced_images() -> dict[str, set[str]]:
    refs: dict[str, set[str]] = defaultdict(set)
    for f in catalogue_sources():
        if not f.is_file():
            print(f"WARN missing source {f.relative_to(ROOT)}", file=sys.stderr)
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for path in IMG_RE.findall(text):
            if "${" not in path:  # template literals in TS, not real paths
                refs[path].add(str(f.relative_to(ROOT)))
    return refs


def tag_files() -> set[str]:
    with tempfile.TemporaryDirectory() as tmp:
        git = ["git", "-C", tmp]
        subprocess.run(["git", "init", "-q", "--bare", tmp], check=True)
        subprocess.run(
            git + ["fetch", "-q", "--depth=1", "--filter=blob:none", REPO_URL,
                   f"+refs/tags/{TAG}:refs/tags/{TAG}"],
            check=True,
        )
        out = subprocess.run(
            git + ["ls-tree", "-r", "--name-only", TAG, "public/products/"],
            check=True, capture_output=True, text=True,
        ).stdout
    prefix = "public/products/"
    return {line[len(prefix):] for line in out.splitlines() if line.startswith(prefix)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", help="Write missing image paths (one per line)")
    args = ap.parse_args()

    refs = referenced_images()
    on_tag = tag_files()
    missing = sorted(p for p in refs if p not in on_tag)

    by_dir: dict[str, list[str]] = defaultdict(list)
    for p in missing:
        by_dir[p.split("/", 1)[0]].append(p)
    print(f"referenced={len(refs)} on_tag={len(on_tag)} missing={len(missing)}")
    for d, paths in sorted(by_dir.items()):
        folders = sorted({p.rsplit("/", 1)[0] for p in paths})
        print(f"  {d}: {len(paths)} file(s) in {len(folders)} folder(s)")
        for folder in folders[:10]:
            sources = sorted({s for p in paths if p.startswith(folder + "/") for s in refs[p]})
            print(f"    {folder}  ← {', '.join(sources)}")
        if len(folders) > 10:
            print(f"    … +{len(folders) - 10} more")

    if args.write:
        out = Path(args.write)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("".join(f"{p}\n" for p in missing))
        print(f"wrote {out}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
