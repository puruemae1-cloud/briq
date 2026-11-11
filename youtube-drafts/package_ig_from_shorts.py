#!/usr/bin/env python3
"""Package a Shorts/IG build folder for Instagram Reels publish.

Always uses each topic's clean ``poster.jpg`` (product-only still) as the
Graph API ``cover_url``. Never copies ``frames/01.jpg`` — that frame has VO
text and shade and makes a bad feed thumbnail.

Usage:
  python3 package_ig_from_shorts.py 14-ig-1 \\
    --out ../instagram-drafts/contents-yt-bgm-sample1
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _strip_https(caption: str) -> str:
    lines = []
    for line in caption.splitlines():
        if re.search(r"https?://", line):
            continue
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


def _topic_dir(batch: Path, topic: dict) -> Path:
    slug = topic.get("slug") or ""
    d = batch / slug
    if d.is_dir():
        return d
    # fallback: numbered folder matching id
    pid = topic.get("id") or ""
    for cand in sorted(batch.glob("*/")):
        meta = cand / "meta.json"
        if not meta.is_file():
            continue
        try:
            mid = json.loads(meta.read_text(encoding="utf-8")).get("id")
        except Exception:
            mid = None
        if mid == pid:
            return cand
    raise SystemExit(f"topic folder missing for {pid or slug}")


def package_batch(batch: Path, out: Path) -> list[dict]:
    index_path = batch / "INDEX.json"
    if not index_path.is_file():
        raise SystemExit(f"missing INDEX.json in {batch}")
    topics = json.loads(index_path.read_text(encoding="utf-8"))
    if not topics:
        raise SystemExit(f"empty INDEX.json: {index_path}")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    manifest: list[dict] = []
    for i, topic in enumerate(topics, 1):
        src = _topic_dir(batch, topic)
        poster = src / "poster.jpg"
        if not poster.is_file():
            raise SystemExit(
                f"blocked: {src.name} has no poster.jpg — rebuild with "
                "build_multi_brand_shorts_10.py so IG cover is a clean product still. "
                "Do not use frames/01.jpg as the thumbnail."
            )
        # Refuse accidental texted-frame covers.
        frame01 = src / "frames" / "01.jpg"
        if frame01.is_file() and poster.resolve() == frame01.resolve():
            raise SystemExit(
                f"blocked: {src.name}/poster.jpg points at frames/01.jpg "
                "(VO text overlay). Rebuild a clean product poster."
            )
        if poster.stat().st_size == frame01.stat().st_size if frame01.is_file() else False:
            # Same bytes as texted frame → almost certainly wrong.
            if poster.read_bytes() == frame01.read_bytes():
                raise SystemExit(
                    f"blocked: {src.name}/poster.jpg is identical to frames/01.jpg. "
                    "Rebuild so the cover is a text-free product still."
                )

        mp4s = sorted(src.glob("*.mp4"))
        if not mp4s:
            raise SystemExit(f"no mp4 in {src}")
        dest = out / f"{i:02d}"
        dest.mkdir(parents=True)
        shutil.copy2(mp4s[0], dest / "reel.mp4")
        shutil.copy2(poster, dest / "poster.jpg")
        # Guard cover check for YT-style captions usually skips stamp; keep poster as 01.jpg too.
        shutil.copy2(poster, dest / "01.jpg")

        cap_src = src / "description.txt"
        caption = cap_src.read_text(encoding="utf-8") if cap_src.is_file() else topic.get("description") or ""
        (dest / "caption.txt").write_text(_strip_https(caption), encoding="utf-8")

        row = {
            "n": i,
            "id": topic.get("id"),
            "keyword": topic.get("search") or "",
            "brand": topic.get("brandKo") or topic.get("brand") or "",
            "title": topic.get("title") or topic.get("displayName") or "",
            "poster": f"{i:02d}/poster.jpg",
            "reel": f"{i:02d}/reel.mp4",
            "sourceSlug": src.name,
        }
        manifest.append(row)
        print(f"OK {i:02d} poster=product-still {topic.get('search')} ← {src.name}")

    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"DONE {out} ({len(manifest)} reels) — use poster.jpg as Graph cover_url")
    return manifest


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("batch", help="build folder with INDEX.json + per-topic poster.jpg")
    p.add_argument(
        "--out",
        required=True,
        help="instagram-drafts contents folder to create",
    )
    args = p.parse_args(argv)
    batch = Path(args.batch).expanduser()
    if not batch.is_absolute():
        batch = (HERE / batch).resolve()
    out = Path(args.out).expanduser()
    if not out.is_absolute():
        out = (HERE / out).resolve()
    package_batch(batch, out)


if __name__ == "__main__":
    main()
