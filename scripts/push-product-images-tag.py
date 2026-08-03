#!/usr/bin/env python3
"""Push local PDP image trees onto the `product-images` git tag.

Used by weekly brand syncs so Vercel (raw.githubusercontent.com rewrite)
serves new / updated product photos without bloating `main`.

  python3 scripts/push-product-images-tag.py --dirs bs-pdp ps-pdp lu-pdp

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dirs",
        nargs="+",
        required=True,
        help="Image folder names under public/products (e.g. bs-pdp)",
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

    # Need the tag available
    fetched = run(
        ["git", "fetch", "origin", f"refs/tags/{TAG}:refs/tags/{TAG}"],
        check=False,
    )
    if fetched.returncode != 0:
        # Tag may already exist locally
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
                f"WARN: could not check out tag {TAG} — skip image tag update.",
                flush=True,
            )
            return 0

        ensure_git_identity(tmp)

        for name, src in src_roots:
            dest = tmp / "public" / "products" / name
            dest.mkdir(parents=True, exist_ok=True)
            # Copy only — do not --delete whole brand tree (other brands live on tag)
            for child in src.iterdir():
                if not child.is_dir():
                    continue
                target = dest / child.name
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(child, target)
            run(["git", "add", "-f", f"public/products/{name}"], cwd=tmp)

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(tmp),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if not status:
            print("No image changes on product-images tag.", flush=True)
            return 0

        run(
            [
                "git",
                "commit",
                "-m",
                "chore: sync PDP images from weekly brand jobs\n",
            ],
            cwd=tmp,
        )
        run(["git", "tag", "-f", TAG], cwd=tmp)
        pushed = run(
            ["git", "push", "-f", "origin", f"refs/tags/{TAG}"],
            cwd=tmp,
            check=False,
        )
        if pushed.returncode != 0:
            print(
                "WARN: failed to push product-images tag "
                "(check Actions write permissions / tag protection).",
                flush=True,
            )
            # Do not fail the whole weekly job — catalogue sync still valuable.
            return 0
        print("product-images tag updated.", flush=True)
        return 0
    finally:
        run(["git", "worktree", "remove", "--force", str(tmp)], check=False)
        run(["git", "worktree", "prune"], check=False)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
