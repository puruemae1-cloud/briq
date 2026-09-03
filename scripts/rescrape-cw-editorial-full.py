#!/usr/bin/env python3
"""Re-scrape CW PDP long-description with full h2/h3 caption text + images for all models."""
from __future__ import annotations

import html as H
import json
import re
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("/Users/jeonghyunlee/Documents/briq")
RAW = json.loads((ROOT / "src/data/cw/cw-catalog-raw.json").read_text())["products"]
ED_PATH = ROOT / "src/data/cw/cw-editorial.json"
EDIT = ROOT / "public/products/cw-editorial"
UA = {"User-Agent": "Mozilla/5.0 (compatible; BriqBot/1.0)"}


def slugify(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()


def model_key(url: str) -> str | None:
    path = urlparse(url.split("?")[0]).path.strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and parts[-1].endswith(".html"):
        return parts[-2]
    return parts[-1].replace(".html", "") if parts else None


def clean_text(s: str) -> str:
    s = H.unescape(s or "")
    s = re.sub(r"<script[\s\S]*?</script>", " ", s, flags=re.I)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_css_junk(s: str) -> bool:
    return bool(re.search(r"\{[^}]*:|\.section-|@media|padding:|display:\s*flex|margin-", s))


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def download(url: str, dest: Path, min_bytes: int = 2000) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size >= min_bytes:
        return True
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=45) as r:
            data = r.read()
        if len(data) < min_bytes:
            return False
        dest.write_bytes(data)
        return True
    except Exception:
        return False


def pick_img(urls: list[str]) -> str | None:
    scored = []
    for u in urls:
        name = u.split("/")[-1].lower()
        if any(x in name for x in ["_mob", "tabport", "tabland", "favicon", "icon", "video-replacement"]):
            continue
        score = 0
        if "@2x" in name:
            score += 3
        if re.match(r"^\d", name) or "movement" in name:
            score += 2
        if name.endswith((".jpg", ".jpeg", ".webp", ".png")):
            score += 1
        scored.append((score, u))
    if not scored:
        return None
    scored.sort(reverse=True)
    return scored[0][1]


def extract_picture_urls(fragment: str) -> list[str]:
    urls = [
        H.unescape(u.split(" ")[0].split(",")[0].split("?")[0])
        for u in re.findall(
            r'(?:data-src|data-srcset|src)="(https://www\.christopherward\.com[^"]+/pdp-long-description/[^"]+)"',
            fragment,
        )
    ]
    return urls


def scrape_editorial(url: str, key: str) -> dict:
    html = fetch(url)
    start = html.find("pdp-long-description-wrapper")
    if start < 0:
        start = html.find("pdp-long-description")
    if start < 0:
        start = html.find("/images/pdp-long-description/")
    end = len(html)
    for marker in (
        "more-technical-features",
        "You might also like",
        "you-might-also",
        "Recently viewed",
        "pdpRecommendation",
    ):
        i = html.find(marker, max(0, start))
        if i > 0:
            end = min(end, i)
    chunk = html[max(0, start) : end]
    if len(chunk) < 400:
        return {"modelKey": key, "sourceUrl": url, "sections": [], "error": "no-long-desc"}

    sections: list[dict] = []
    seen_titles: set[str] = set()
    img_i = 0

    def save_img(remote: str | None, prefix: str) -> str | None:
        nonlocal img_i
        if not remote:
            return None
        img_i += 1
        ext = Path(urlparse(remote).path).suffix.lower() or ".jpg"
        if ext not in (".jpg", ".jpeg", ".png", ".webp"):
            ext = ".jpg"
        dest = EDIT / key / f"{prefix}-{img_i}{ext}"
        if download(remote, dest):
            return f"/products/cw-editorial/{key}/{dest.name}"
        img_i -= 1
        return None

    # 1) Hero h2 sections (Poetry / Introducing Calibre / etc.)
    for m in re.finditer(r"<h2[^>]*>([\s\S]*?)</h2>", chunk):
        title = clean_text(m.group(1))
        if not title or len(title) < 2:
            continue
        low = title.lower()
        if low in ("technical", "features") or any(
            x in low for x in ["cookie", "newsletter", "related", "basket", "cart"]
        ):
            continue
        if title in seen_titles:
            continue
        ctx = chunk[m.start() : m.start() + 7000]
        ctx_live = re.sub(r"<!--([\s\S]*?)-->", "", ctx)
        vid_m = re.search(
            r'(?:data-src|src)="(https://player\.vimeo\.com/video/\d[^"]*)"',
            ctx_live,
        )
        video = H.unescape(vid_m.group(1)).rstrip('"').replace("%22", "") if vid_m else None
        if video and ("autoplay=1" in video or "controls=0" in video):
            video = None
        # Loco / story videos often left in comments with a poster image — keep known story embeds
        if not video:
            commented = re.search(
                r'<!--[\s\S]{0,400}(?:data-src|src)="(https://player\.vimeo\.com/video/\d[^"]*)"',
                ctx,
            )
            if commented:
                cand = H.unescape(commented.group(1)).rstrip('"').replace("%22", "")
                if "autoplay=1" not in cand and "controls=0" not in cand:
                    video = cand
        paras = [clean_text(p) for p in re.findall(r"<p[^>]*>([\s\S]*?)</p>", ctx[:9000])]
        paras = [
            p
            for p in paras
            if len(p) > 40
            and not is_css_junk(p)
            and title not in p[: len(title) + 2]
            and p not in ("&nbsp;",)
        ]
        # Keep multi-paragraph story copy (Biscay / newer long-desc layouts)
        body = "\n\n".join(paras) if paras else ""
        # If h2 has no paragraph, borrow untitled following copy (not an h3 caption card)
        if not body:
            after = chunk[m.end() : m.end() + 5000]
            tb = re.search(r'<div class="text-block[^"]*"[^>]*>([\s\S]*?)</div>', after)
            if tb and not re.search(r"<h3[^>]*>", tb.group(1)):
                tparas = [clean_text(p) for p in re.findall(r"<p[^>]*>([\s\S]*?)</p>", tb.group(1))]
                tparas = [p for p in tparas if len(p) > 40 and not is_css_junk(p)]
                if tparas:
                    body = "\n\n".join(tparas)
        # Prefer movement / story image near h2, not numbered caption assets
        urls = extract_picture_urls(ctx[:5000])
        story_urls = [u for u in urls if re.search(r"(movement|story|hero|video-replacement)", u, re.I)] or urls
        remote = pick_img(story_urls)
        local = save_img(remote, "story")
        if not body and not video and not local:
            continue
        sections.append(
            {
                "titleEn": title,
                "bodyEn": body,
                "image": local,
                "videoUrl": video,
                "layout": "default",
                "reverse": bool(video) or (len(sections) % 2 == 1),
            }
        )
        seen_titles.add(title)

    # 2) Caption cards: each text-block with h3 + body, paired to nearest preceding picture
    for m in re.finditer(r'<div class="text-block[^"]*"[^>]*>([\s\S]*?)</div>', chunk):
        inner = m.group(1)
        h3 = re.search(r"<h3[^>]*>([\s\S]*?)</h3>", inner)
        title = clean_text(h3.group(1)) if h3 else ""
        paras = [clean_text(p) for p in re.findall(r"<p[^>]*>([\s\S]*?)</p>", inner)]
        paras = [p for p in paras if len(p) > 25 and not is_css_junk(p)]
        body = "\n\n".join(paras)
        if not title and not body:
            continue
        # Skip if this title already used as an h2 hero
        if title and title in seen_titles:
            continue
        # Skip tiny label-only blocks
        if title and not body and len(title) < 4:
            continue
        before = chunk[max(0, m.start() - 4000) : m.start()]
        pics = list(re.finditer(r"<picture>([\s\S]*?)</picture>", before))
        remote = None
        if pics:
            remote = pick_img(extract_picture_urls(pics[-1].group(1)))
        if not remote:
            # try following picture in same parent window
            after = chunk[m.end() : m.end() + 2500]
            pics_a = list(re.finditer(r"<picture>([\s\S]*?)</picture>", after))
            if pics_a:
                remote = pick_img(extract_picture_urls(pics_a[0].group(1)))
        local = save_img(remote, "caption")
        if not body and not local and not title:
            continue
        # Deduplicate identical bodies (caption cards may have empty titles)
        key_t = title or body[:40]
        if key_t in seen_titles:
            continue
        seen_titles.add(key_t)
        reverse = len(sections) % 2 == 1
        sections.append(
            {
                "titleEn": title,
                "bodyEn": body,
                "image": local,
                "videoUrl": None,
                "layout": "caption",
                "reverse": reverse,
            }
        )

    return {
        "modelKey": key,
        "sourceUrl": url,
        "sections": sections,
        "sectionCount": len(sections),
    }


def main() -> None:
    existing = json.loads(ED_PATH.read_text()) if ED_PATH.exists() else {"models": {}}
    models = existing.get("models") or {}
    seeds: dict[str, str] = {}
    for p in RAW:
        u = p.get("url") or ""
        if not u or "nearly-new" in u.lower() or "/sale/" in u:
            continue
        k = model_key(u)
        if k and k not in seeds:
            seeds[k] = u

    print("models to scrape", len(seeds), flush=True)
    rich = 0
    for i, (key, url) in enumerate(sorted(seeds.items()), 1):
        print(f"  {i}/{len(seeds)} {key}", flush=True)
        try:
            data = scrape_editorial(url, key)
        except Exception as e:
            print("   FAIL", e)
            continue
        models[key] = data
        n = len(data.get("sections") or [])
        with_text = sum(1 for s in data.get("sections") or [] if (s.get("bodyEn") or "").strip())
        print(f"   sections {n} withText {with_text}")
        if with_text >= 2:
            rich += 1
        time.sleep(0.35)

    # Keep nearly-new keys pointing at empty or inherit later in rebuild
    for k in list(models.keys()):
        if "nearly-new" in k and k not in seeds:
            models[k] = models.get(k) or {"modelKey": k, "sections": []}

    ED_PATH.write_text(
        json.dumps({"scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "models": models}, ensure_ascii=False, indent=2)
        + "\n"
    )
    print("done models", len(models), "rich", rich)


if __name__ == "__main__":
    main()
