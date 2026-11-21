#!/usr/bin/env python3
"""Re-extract story Vimeo URLs, ignoring HTML comments (fixes cross-model contamination)."""
from __future__ import annotations

import html as H
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("/Users/jeonghyunlee/Documents/briq")
ED_PATH = ROOT / "src/data/cw/cw-editorial.json"
RAW = json.loads((ROOT / "src/data/cw/cw-catalog-raw.json").read_text())["products"]

UA = {"User-Agent": "Mozilla/5.0 (compatible; BriqBot/1.0)"}


def model_key(url: str) -> str | None:
    path = urlparse(url.split("?")[0]).path.strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and parts[-1].endswith(".html"):
        return parts[-2]
    return parts[-1].replace(".html", "") if parts else None


def clean_text(s: str) -> str:
    s = H.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")


def videos_by_title(html: str) -> dict[str, str | None]:
    start = html.find("pdp-long-description")
    if start < 0:
        start = html.find("/images/pdp-long-description/")
    end = len(html)
    for m in ("You might also like", "you-might-also", "Recently viewed", "pdpRecommendation"):
        i = html.find(m, max(0, start))
        if i > 0:
            end = min(end, i)
    chunk = html[max(0, start - 800) : end] if start > 0 else ""
    out: dict[str, str | None] = {}
    for m in re.finditer(r"<h2[^>]*>([\s\S]*?)</h2>", chunk):
        title = clean_text(m.group(1))
        if not title or title.lower() in ("technical", "features"):
            continue
        if title in out:
            continue
        ctx = chunk[m.start() : m.start() + 6000]
        ctx_live = re.sub(r"<!--([\s\S]*?)-->", "", ctx)
        vid_m = re.search(
            r'(?:data-src|src)="(https://player\.vimeo\.com/video/\d[^"]*)"',
            ctx_live,
        )
        video = H.unescape(vid_m.group(1)).rstrip('"').replace("%22", "") if vid_m else None
        if video and ("autoplay=1" in video or "controls=0" in video):
            video = None
        out[title] = video
    return out


def main() -> None:
    ed = json.loads(ED_PATH.read_text())
    models = ed.get("models") or {}
    seeds: dict[str, str] = {}
    for p in RAW:
        u = p.get("url") or ""
        if not u or "nearly-new" in u or "/sale/" in u:
            continue
        k = model_key(u)
        if k and k in models and k not in seeds:
            seeds[k] = u

    updated = 0
    cleared = 0
    for key, url in sorted(seeds.items()):
        print("fix", key, flush=True)
        try:
            by_title = videos_by_title(fetch(url))
        except Exception as e:
            print("  FAIL", e)
            continue
        secs = models[key].get("sections") or []
        for s in secs:
            title = (s.get("titleEn") or "").strip()
            if not title:
                # caption/wide slides should never carry a story video
                if s.get("videoUrl"):
                    s["videoUrl"] = None
                    cleared += 1
                continue
            new_v = by_title.get(title)
            old_v = s.get("videoUrl")
            if new_v != old_v:
                s["videoUrl"] = new_v
                updated += 1
                print(f"  {title[:40]!r}: {old_v!r} -> {new_v!r}")
        models[key]["sections"] = secs

    # sanitize any remaining junk
    for key, mod in models.items():
        for s in mod.get("sections") or []:
            v = s.get("videoUrl")
            if not v:
                continue
            if "%22" in v or v.endswith('"'):
                s["videoUrl"] = v.replace("%22", "").rstrip('"')
                updated += 1
            if "autoplay=1" in v or "controls=0" in v:
                s["videoUrl"] = None
                cleared += 1

    ed["models"] = models
    ED_PATH.write_text(json.dumps(ed, ensure_ascii=False, indent=2) + "\n")
    print("done updated", updated, "cleared", cleared)


if __name__ == "__main__":
    main()
