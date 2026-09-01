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
import json
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


def sync_banners(tmp: Path, src: Path) -> bool:
    """Replace public/banners on the tag with the local tree (desktop/m/t)."""
    dest = tmp / "public" / "banners"
    if dest.exists():
        shutil.rmtree(dest)
    def _ignore(dirpath: str, names: list[str]) -> set[str]:
        # Source download cache — not needed on CDN
        if Path(dirpath).name == "banners" and "_cache" in names:
            return {"_cache"}
        return set()

    shutil.copytree(src, dest, ignore=_ignore)
    run(["git", "add", "-f", "public/banners"], cwd=tmp)
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", "public/banners"],
        cwd=str(tmp),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return bool(status)


def sync_brand(
    tmp: Path,
    name: str,
    src: Path,
    *,
    merge: bool = False,
    only: list[str] | None = None,
) -> bool:
    """Copy one brand tree into the worktree and stage it. Returns True if dirty.

    merge=True replaces only colour (or SKU) subfolders present locally, so
    sibling colourways already on the tag are preserved. Use this when the
    local tree is a partial redownload (e.g. pale Arc'teryx colourways only).
    only= limits the copy to those product-id folder names (flat SKU trees
    like ch-pdp/<sku>/1.jpg).
    """
    dest = tmp / "public" / "products" / name
    dest.mkdir(parents=True, exist_ok=True)
    if only:
        copied = 0
        for sku in only:
            child = src / sku
            if not child.is_dir():
                print(f"skip missing {child}", flush=True)
                continue
            target = dest / sku
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(child, target)
            copied += 1
        print(f"copied {copied}/{len(only)} ids → public/products/{name}", flush=True)
        run(["git", "add", "-f", f"public/products/{name}"], cwd=tmp)
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", f"public/products/{name}"],
            cwd=str(tmp),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return bool(status)
    if merge:
        for pid_dir in src.iterdir():
            if not pid_dir.is_dir():
                continue
            for colour_dir in pid_dir.iterdir():
                if not colour_dir.is_dir():
                    continue
                target = dest / pid_dir.name / colour_dir.name
                if target.exists():
                    shutil.rmtree(target)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(colour_dir, target)
    else:
        for child in src.iterdir():
            target = dest / child.name
            if child.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(child, target)
            elif child.is_file() and child.suffix.lower() in {
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
            }:
                # Flat listing thumbs (e.g. public/products/cw/*.jpg)
                shutil.copy2(child, target)
    run(["git", "add", "-f", f"public/products/{name}"], cwd=tmp)
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", f"public/products/{name}"],
        cwd=str(tmp),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return bool(status)


def commit_head(tmp: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(tmp),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def remote_tag_rev() -> str:
    run(["git", "fetch", "origin", f"refs/tags/{TAG}:refs/tags/{TAG}"], check=False)
    show = subprocess.run(
        ["git", "rev-parse", TAG],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    return show.stdout.strip() if show.returncode == 0 else ""


def reset_worktree_to_remote_tag(tmp: Path) -> None:
    """Re-base the tag worktree on the latest remote tag after a concurrent push."""
    rev = remote_tag_rev()
    if rev:
        run(["git", "reset", "--hard", rev], cwd=tmp)


def push_tag(tmp: Path) -> bool:
    """Force-push the product-images tag. True only when remote matches our HEAD."""
    head = commit_head(tmp)
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
    if pushed.returncode != 0:
        return False
    return remote_tag_rev() == head


def update_product_images_manifest() -> None:
    """Bump cache-bust token on main after a successful tag push."""
    rev = subprocess.run(
        ["git", "rev-parse", TAG],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not rev:
        print("WARN: could not read product-images tag rev — skip manifest", flush=True)
        return
    from datetime import datetime, timezone

    manifest = {
        "publishedAt": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "tagRev": rev[:12],
    }
    path = ROOT / "src/data/product-images-manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {path.name} tagRev={manifest['tagRev']}", flush=True)


def purge_jsdelivr(dirs: list[str]) -> None:
    """Invalidate jsDelivr so same-path updates show on the live shop."""
    script = ROOT / "scripts" / "purge-jsdelivr-media.py"
    if not script.is_file():
        print("WARN: purge-jsdelivr-media.py missing — skip CDN purge", flush=True)
        return
    cmd = [sys.executable, str(script), "--dirs", *dirs]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=str(ROOT), check=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dirs",
        nargs="+",
        required=True,
        help=(
            "Image folder names under public/products (e.g. bs-pdp), "
            "or 'banners' for public/banners"
        ),
    )
    ap.add_argument(
        "--skip-whiten",
        action="store_true",
        help="Skip studio-background whitening before push",
    )
    ap.add_argument(
        "--merge",
        action="store_true",
        help=(
            "Merge colour/SKU subfolders into the tag without replacing "
            "sibling folders under each product id (for partial redownloads)."
        ),
    )
    ap.add_argument(
        "--only",
        nargs="+",
        help="Only copy these product-id folder names under each --dirs tree",
    )
    ap.add_argument(
        "--only-file",
        help="Newline-separated product-id folder names (same as --only)",
    )
    args = ap.parse_args()
    only_ids: list[str] = list(args.only or [])
    if args.only_file:
        only_ids.extend(
            line.strip()
            for line in Path(args.only_file).read_text().splitlines()
            if line.strip() and not line.startswith("#")
        )

    src_roots: list[tuple[str, Path]] = []
    for name in args.dirs:
        if name == "banners":
            src = ROOT / "public" / "banners"
        else:
            src = ROOT / "public" / "products" / name
        if src.is_dir() and any(src.iterdir()):
            src_roots.append((name, src))
        else:
            print(f"skip missing/empty {src}", flush=True)

    if not src_roots:
        print("No local image dirs to push.", flush=True)
        return 0

    # Always map light studio mats to Gucci DarkGray before publishing so pale
    # garments stay visible. Required for newly scraped products — do not skip
    # in weekly CI (use --skip-whiten only when images were already greymatted).
    # Banner trees are lifestyle photos — never greymat them.
    # Burberry Scene7 and Gucci DarkGray packshots must stay official bytes.
    skip_greymat = {"banners", "bb-pdp", "gc-pdp", "ax-pdp", "axa-pdp", "axg-pdp", "axo-pdp"}
    product_dirs = [n for n, _ in src_roots if n not in skip_greymat]
    if not args.skip_whiten and product_dirs:
        print(f"Greymatting studio backgrounds → DarkGray: {product_dirs}", flush=True)
        scripts_dir = str(ROOT / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        try:
            from studio_greymat import greymat_dirs  # type: ignore
        except ImportError as e:
            print(
                "ERROR: studio greymat requires pillow + numpy + rembg "
                f"(`pip install -r scripts/requirements-images.txt`). "
                f"Import failed: {e}",
                flush=True,
            )
            return 1
        try:
            greymat_dirs(
                product_dirs,
                workers=max(2, min(6, (os.cpu_count() or 4) // 2)),
            )
        except Exception as e:
            print(f"ERROR: studio greymat failed: {e}", flush=True)
            return 1

    fetched = run(
        ["git", "fetch", "origin", f"refs/tags/{TAG}:refs/tags/{TAG}"],
        check=False,
    )
    if fetched.returncode != 0:
        show = run(["git", "rev-parse", "--verify", TAG], check=False)
        if show.returncode != 0:
            print(
                f"ERROR: tag {TAG} not available — refusing to skip image "
                "publish (catalogue must not go live without PDP files).",
                flush=True,
            )
            return 1

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
            mode = "merge" if args.merge else "replace"
            print(f"=== sync {name} ({mode}) ===", flush=True)
            pushed_dir = False
            for attempt in range(5):
                if name == "banners":
                    changed = sync_banners(tmp, src)
                else:
                    changed = sync_brand(
                        tmp, name, src, merge=args.merge, only=only_ids or None
                    )
                if not changed:
                    print(f"No image changes for {name}.", flush=True)
                    pushed_dir = True
                    break

                run(
                    [
                        "git",
                        "commit",
                        "-m",
                        f"chore: sync PDP images ({name})\n",
                    ],
                    cwd=tmp,
                )
                if push_tag(tmp):
                    any_pushed = True
                    pushed_dir = True
                    print(f"product-images tag updated ({name}).", flush=True)
                    if name == "banners":
                        verify = subprocess.run(
                            [sys.executable, str(ROOT / "scripts" / "verify-banner-cdn.py")],
                            cwd=str(ROOT),
                            check=False,
                        )
                        if verify.returncode != 0:
                            print(
                                "ERROR: banner CDN verify failed after tag push.",
                                flush=True,
                            )
                            return 1
                    break

                print(
                    f"WARN: product-images tag race on {name} "
                    f"(attempt {attempt + 1}/5) — rebasing worktree",
                    flush=True,
                )
                reset_worktree_to_remote_tag(tmp)

            if not pushed_dir:
                print(
                    "ERROR: failed to push product-images tag after retries "
                    "(concurrent weekly sync or tag protection).",
                    flush=True,
                )
                return 1

        if any_pushed:
            update_product_images_manifest()

        if not any_pushed:
            print("No image changes on product-images tag.", flush=True)
            # Still purge when banners were requested — jsDelivr can stay stale
            # even if the tag tree already matched local files.
            if any(name == "banners" for name, _ in src_roots):
                purge_jsdelivr(["banners"])
            return 0

        # Same path on @product-images keeps a stale jsDelivr HIT otherwise
        # (homepage banners looked unchanged after refresh).
        purge_jsdelivr([name for name, _ in src_roots])
        return 0
    finally:
        run(["git", "worktree", "remove", "--force", str(tmp)], check=False)
        run(["git", "worktree", "prune"], check=False)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
