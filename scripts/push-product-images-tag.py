#!/usr/bin/env python3
"""Push local PDP image trees onto the `product-images` git tag.

Used by weekly brand syncs so Vercel (raw.githubusercontent.com rewrite)
serves new / updated product photos without bloating `main`.

  python3 scripts/push-product-images-tag.py --dirs bs-pdp ps-pdp lu-pdp

Commits and force-pushes one brand directory at a time so large multi-brand
updates do not trip GitHub HTTP 500 limits.

Exits 0 when there is nothing to do. Never leaves a dirty worktree behind.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = "product-images"


def run(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=str(cwd or ROOT), check=check)


def ensure_git_identity(cwd: Path) -> None:
    run(
        ["git", "config", "user.name", "briq-bot"],
        cwd=cwd,
        check=False,
    )
    run(
        ["git", "config", "user.email", "briq-bot@users.noreply.github.com"],
        cwd=cwd,
        check=False,
    )


def sync_brand(tmp: Path, name: str, src: Path) -> bool:
    """Copy one brand tree into the worktree and stage it. Returns True if dirty."""
    dest = tmp / "public" / "products" / name
    dest.mkdir(parents=True, exist_ok=True)
    for child in src.iterdir():
        if not child.is_dir():
            continue
        target = dest / child.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(child, target)
    run(["git", "add", "-f", f"public/products/{name}"], cwd=tmp)
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", f"public/products/{name}"],
        cwd=str(tmp),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return bool(status)


def push_tag(tmp: Path) -> bool:
    """Force-push the product-images tag. Returns True on success."""
    run(["git", "tag", "-f", TAG], cwd=tmp)
    pushed = run(
        [
            "git",
            "-c",
            "http.postBuffer=524288000",
            "-c",
            "http.version=HTTP/1.1",
            "push",
            "-f",
            "origin",
            f"refs/tags/{TAG}",
        ],
        cwd=tmp,
        check=False,
    )
    return pushed.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dirs",
        nargs="+",
        required=True,
        help="Image folder names under public/products (e.g. bs-pdp)",
    )
    ap.add_argument(
        "--skip-whiten",
        action="store_true",
        help="Skip studio-background whitening before push",
    )
    args = ap.parse_args()

    src_roots = []
    for name in args.dirs:
        src = ROOT / "public" / "products" / name
        if src.is_dir() and any(src.iterdir()):
            src_roots.append((name, src))
        else:
            print(f"skip missing/empty {src}", flush=True)

    if not src_roots:
        print("No local image dirs to push.", flush=True)
        return 0

    # Always lift warm/gray studio mats to white before publishing (Gucci-like PLP).
    # Required for newly scraped products — do not skip in weekly CI.
    if not args.skip_whiten:
        names = [n for n, _ in src_roots]
        print(f"Whitening studio backgrounds: {names}", flush=True)
        scripts_dir = str(ROOT / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        try:
            from studio_whiten import whiten_dirs  # type: ignore
        except ImportError as e:
            print(
                "ERROR: studio whitening requires pillow + numpy "
                f"(`pip install pillow numpy`). Import failed: {e}",
                flush=True,
            )
            return 1
        try:
            whiten_dirs(
                names,
                workers=max(2, (os.cpu_count() or 4) // 2),
            )
        except Exception as e:
            print(f"ERROR: studio whitening failed: {e}", flush=True)
            return 1

    fetched = run(
        ["git", "fetch", "origin", f"refs/tags/{TAG}:refs/tags/{TAG}"],
        check=False,
    )
    if fetched.returncode != 0:
        show = run(["git", "rev-parse", "--verify", TAG], check=False)
        if show.returncode != 0:
            print(
                f"WARN: tag {TAG} not available — skip image tag update "
                "(catalogue commit can still proceed).",
                flush=True,
            )
            return 0

    tmp = Path(tempfile.mkdtemp(prefix="briq-product-images-"))
    try:
        added = run(
            ["git", "worktree", "add", "--detach", str(tmp), TAG],
            check=False,
        )
        if added.returncode != 0:
            print(
                f"ERROR: could not check out tag {TAG} — abort image tag update.",
                flush=True,
            )
            return 1

        ensure_git_identity(tmp)

        any_pushed = False
        for name, src in src_roots:
            print(f"=== sync {name} ===", flush=True)
            if not sync_brand(tmp, name, src):
                print(f"No image changes for {name}.", flush=True)
                continue

            run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"chore: sync PDP images ({name})\n",
                ],
                cwd=tmp,
            )
            if not push_tag(tmp):
                print(
                    "ERROR: failed to push product-images tag "
                    "(check Actions write permissions / tag protection / size).",
                    flush=True,
                )
                return 1
            any_pushed = True
            print(f"product-images tag updated ({name}).", flush=True)

        if not any_pushed:
            print("No image changes on product-images tag.", flush=True)
        return 0
    finally:
        run(["git", "worktree", "remove", "--force", str(tmp)], check=False)
        run(["git", "worktree", "prune"], check=False)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
