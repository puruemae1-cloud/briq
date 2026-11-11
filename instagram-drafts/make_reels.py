#!/usr/bin/env python3
"""Build Briq Instagram reels from slide folders with the locked endcard.

Usage:
  python3 make_reels.py contents-briq-reels5
  python3 make_reels.py /absolute/path/to/batch

Each numbered folder (01, 02, …) must already have 01.jpg… slides (and usually
caption.txt). This writes endcard.jpg, encodes reel.mp4 (slides + dark briq.kr
end hold), copies the endcard into each folder, and refreshes preview.html.

Do not invent a different endcard. Always go through reel_endcard + slides2reel.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
import time
from pathlib import Path

from reel_endcard import END_SECONDS, SECONDS_PER_SLIDE, save_endcard

HERE = Path(__file__).resolve().parent
SWIFT = HERE / "slides2reel.swift"
PUBLIC = HERE.parent / "public"
POSTER_W, POSTER_H = 1080, 1920


def _fit_cover(img, w: int, h: int):
    from PIL import Image

    img = img.convert("RGB")
    scale = max(w / img.width, h / img.height)
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def _catalog_photo_from_slide(slide: Path):
    """Resolve the stamped catalog source on a cover slide, if present."""
    try:
        from slide_layout import read_slide_record
    except Exception:
        return None
    try:
        source = (read_slide_record(slide).get("source") or "").strip()
    except Exception:
        return None
    if not source.startswith("/products/"):
        return None
    path = PUBLIC / source.lstrip("/")
    return path if path.is_file() else None


def write_product_poster(folder: Path, slides: list[Path]) -> Path:
    """IG reel cover_url must show the product, not a texted slide.

    Prefer the catalog photo stamped on 01.jpg. Never silently reuse a VO/text
    overlay frame as the feed thumbnail when a clean source exists.
    """
    from PIL import Image

    poster = folder / "poster.jpg"
    photo = _catalog_photo_from_slide(slides[0]) if slides else None
    if photo is not None:
        _fit_cover(Image.open(photo), POSTER_W, POSTER_H).save(poster, quality=92)
        return poster
    # Last resort only — slide still beats a missing file for local preview.
    poster.write_bytes(slides[0].read_bytes())
    print(f"  warn {folder.name}: poster fell back to texted slide (no stamped source)")
    return poster


def _slide_paths(folder: Path) -> list[Path]:
    return sorted(folder.glob("[0-9][0-9].jpg"))


def _encode_reel(out: Path, slides: list[Path], end: Path) -> None:
    if not SWIFT.is_file():
        raise SystemExit(f"missing encoder: {SWIFT}")
    cmd = [
        "xcrun",
        "swift",
        str(SWIFT),
        str(out),
        "--end",
        str(end),
        *[str(p) for p in slides],
    ]
    for attempt in range(3):
        r = subprocess.run(cmd)
        if r.returncode == 0:
            return
        time.sleep(2)
    raise SystemExit(f"encode failed: {out}")


def _load_manifest(batch: Path) -> list[dict]:
    path = batch / "manifest.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    items = []
    for folder in sorted(batch.glob("[0-9][0-9]")):
        if not folder.is_dir():
            continue
        n = int(folder.name)
        cap = (folder / "caption.txt").read_text(encoding="utf-8") if (folder / "caption.txt").is_file() else ""
        keyword = ""
        brand = ""
        if "「" in cap and "」" in cap:
            keyword = cap.split("「", 1)[1].split("」", 1)[0]
        lines = [ln.strip() for ln in cap.splitlines() if ln.strip()]
        if len(lines) >= 2:
            brand = lines[1]
        items.append({"n": n, "keyword": keyword or folder.name, "brand": brand})
    return items


def _write_preview(batch: Path, items: list[dict], bust: str) -> None:
    parts = []
    for item in items:
        n = int(item["n"])
        folder = batch / f"{n:02d}"
        cap_path = folder / "caption.txt"
        cap = cap_path.read_text(encoding="utf-8").strip() if cap_path.is_file() else ""
        seconds = item.get("seconds", "")
        brand = item.get("brand", "")
        keyword = item.get("keyword", f"{n:02d}")
        parts.append(
            "<article>\n"
            f'<div class="n">{n:02d}</div>\n'
            f"<h2>{html.escape(str(keyword))}</h2>\n"
            f'<p class="brand">{html.escape(str(brand))} · {seconds}초 · 맨 끝 briq.kr</p>\n'
            f'<video src="{n:02d}/reel.mp4?v={bust}" poster="{n:02d}/poster.jpg?v={bust}" '
            'controls playsinline preload="auto"></video>\n'
            '<div class="endwrap">\n'
            '  <div class="endlabel">엔딩 카드 (영상 맨 마지막)</div>\n'
            f'  <img class="end" src="{n:02d}/endcard.jpg?v={bust}" alt="briq.kr ending">\n'
            "</div>\n"
            f'<pre class="cap">{html.escape(cap)}</pre>\n'
            "</article>"
        )
    page = f"""<!doctype html>
<meta charset="utf-8">
<meta http-equiv="Cache-Control" content="no-cache">
<title>브릭 릴스 미리보기</title>
<style>
body {{ margin:0; background:#1c1a17; color:#f7f4ec; font-family:"Apple SD Gothic Neo",sans-serif; }}
header {{ padding:28px 32px 8px; }}
h1 {{ font-size:28px; margin:0 0 6px; }}
header p {{ color:rgba(247,244,236,.65); margin:0; max-width:720px; }}
main {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(360px,1fr)); gap:22px; padding:20px 32px 48px; }}
article {{ background:#2a2622; border-radius:16px; overflow:hidden; }}
.n {{ padding:14px 16px 0; color:rgba(247,244,236,.45); font-size:13px; }}
h2 {{ margin:4px 16px 0; font-size:20px; }}
.brand {{ margin:6px 16px 12px; color:rgba(247,244,236,.62); font-size:14px; }}
video {{ width:100%; display:block; background:#000; max-height:620px; object-fit:contain; }}
.endwrap {{ background:#141210; padding:16px; border-top:1px solid rgba(247,244,236,.08); }}
.endlabel {{ margin:0 0 10px; font-size:12px; letter-spacing:.12em; color:#c6a86a; }}
.end {{ width:100%; display:block; border-radius:8px; }}
.cap {{ margin:0; padding:14px 16px 18px; white-space:pre-wrap; font:14px/1.55 "Apple SD Gothic Neo",sans-serif; background:#fff; color:#14100c; }}
</style>
<header>
  <h1>브릭 릴스 미리보기</h1>
  <p>엔딩은 어두운 briq.kr 카드입니다. 인스타 게시 전 미리보기만입니다.</p>
</header>
<main>
{chr(10).join(parts)}
</main>
"""
    (batch / "preview.html").write_text(page, encoding="utf-8")


def build_batch(batch: Path) -> None:
    batch = batch.resolve()
    if not batch.is_dir():
        raise SystemExit(f"not a folder: {batch}")

    shared_end = save_endcard(batch / "endcard.jpg")
    items = _load_manifest(batch)
    if not items:
        raise SystemExit(f"no numbered folders in {batch}")

    for item in items:
        n = int(item["n"])
        folder = batch / f"{n:02d}"
        slides = _slide_paths(folder)
        if not slides:
            raise SystemExit(f"no slides in {folder}")
        end = save_endcard(folder / "endcard.jpg")
        reel = folder / "reel.mp4"
        print(f"encode {n:02d}", flush=True)
        _encode_reel(reel, slides, end)
        # Always rebuild a clean product poster (do not keep an old texted copy).
        write_product_poster(folder, slides)
        seconds = round(SECONDS_PER_SLIDE * len(slides) + END_SECONDS, 1)
        item["seconds"] = seconds
        item["reel"] = f"{n:02d}/reel.mp4"
        item["poster"] = f"{n:02d}/poster.jpg"
        item["endcard"] = f"{n:02d}/endcard.jpg"
        item["slides"] = [f"{n:02d}/{p.name}" for p in slides]
        print(f"  {seconds}s", flush=True)

    (batch / "manifest.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    bust = str(int(time.time()))
    _write_preview(batch, items, bust)
    print(f"preview {batch / 'preview.html'} ?v={bust}")
    print(f"endcard {shared_end}")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Encode Briq reels with locked dark briq.kr endcard")
    p.add_argument("batch", help="draft batch folder (e.g. contents-briq-reels5)")
    args = p.parse_args(argv)
    batch = Path(args.batch)
    if not batch.is_absolute():
        batch = HERE / batch
    build_batch(batch)


if __name__ == "__main__":
    main()
