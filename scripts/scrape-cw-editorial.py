#!/usr/bin/env python3
"""Scrape CW PDP long-description editorial (story + video + captions) for all models."""
from __future__ import annotations

import html as H
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("/Users/jeonghyunlee/Documents/briq")
RAW = json.loads((ROOT / "src/data/cw/cw-catalog-raw.json").read_text())
ENR_PATH = ROOT / "src/data/cw/cw-pdp-enriched.json"
OUT = ROOT / "src/data/cw/cw-editorial.json"
IMG = ROOT / "public/products/cw-editorial"
IMG.mkdir(parents=True, exist_ok=True)

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
}


def slugify(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()


def model_key(url: str) -> str | None:
    if not url:
        return None
    path = urlparse(url).path.strip("/")
    parts = [p for p in path.split("/") if p]
    # .../c1-jump-hour-mk-v/SKU.html
    if len(parts) >= 2 and parts[-1].endswith(".html"):
        return parts[-2]
    if len(parts) >= 1:
        return parts[-1].replace(".html", "")
    return None


def download(url: str, dest: Path) -> str | None:
    rel = f"/products/cw-editorial/{dest.parent.name}/{dest.name}"
    if dest.exists() and dest.stat().st_size > 2000:
        return rel
    try:
        full = url + ("&" if "?" in url else "?") + "sw=1400"
        req = urllib.request.Request(full, headers={"User-Agent": UA["User-Agent"]})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if len(data) < 1000:
            return None
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return rel
    except Exception:
        return None


def clean_text(s: str) -> str:
    s = H.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def pick_desktop_img(urls: list[str]) -> str | None:
    scored = []
    for u in urls:
        name = u.split("/")[-1].lower()
        if any(x in name for x in ["_mob", "tabport", "tabland", "favicon", "icon"]):
            continue
        score = 0
        if name.endswith((".webp", ".jpg", ".jpeg", ".png")):
            score += 1
        if "@2x" in name:
            score += 1
        if re.match(r"^\d", name):
            score += 2
        scored.append((score, u))
    if not scored:
        return None
    scored.sort(reverse=True)
    return scored[0][1]


def scrape_page(url: str, key: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=70) as r:
        html = r.read().decode("utf-8", "replace")

    # Prefer long-description region; stop before recommendations
    start = html.find("pdp-long-description")
    if start < 0:
        start = html.find("Long description")
    end_markers = [
        "You might also like",
        "you-might-also",
        "pdpRecommendation",
        "Recently viewed",
    ]
    end = len(html)
    for m in end_markers:
        i = html.find(m, start if start > 0 else 0)
        if i > 0:
            end = min(end, i)
    chunk = html[max(0, start - 500) : end] if start > 0 else html

    sections = []
    seen_titles = set()

    # h2-driven blocks
    for m in re.finditer(r"<h2[^>]*>([\s\S]*?)</h2>", chunk):
        title = clean_text(m.group(1))
        if not title or len(title) < 3:
            continue
        low = title.lower()
        if any(x in low for x in ["cookie", "newsletter", "related", "basket", "cart"]):
            continue
        if title in seen_titles:
            continue
        ctx = chunk[m.start() : m.start() + 4500]
        # Ignore commented-out leftover embeds (CW often leaves old Vimeo iframes in <!-- -->)
        ctx_live = re.sub(r"<!--([\s\S]*?)-->", "", ctx)
        vid_m = re.search(
            r'data-src="(https://player\.vimeo\.com/video/\d[^"]*)"|src="(https://player\.vimeo\.com/video/\d[^"]*)"',
            ctx_live,
        )
        video = H.unescape((vid_m.group(1) or vid_m.group(2))).rstrip('"').replace("%22", "") if vid_m else None
        if video and ("autoplay=1" in video or "controls=0" in video):
            video = None
        imgs = [
            H.unescape(u.split("?")[0])
            for u in re.findall(
                r'(?:data-src|data-srcset|src)="(https://www\.christopherward\.com[^"]+/pdp-long-description/[^"]+)"',
                ctx,
            )
        ]
        # also broader library images near title
        if not imgs:
            imgs = [
                H.unescape(u.split("?")[0].split(" ")[0])
                for u in re.findall(
                    r'(?:data-src|src)="(https://www\.christopherward\.com/on/demandware\.static/-/Library-Sites-cw-library/[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
                    ctx,
                    re.I,
                )
            ]
        paras = [
            clean_text(p)
            for p in re.findall(r"<p[^>]*>([\s\S]*?)</p>", ctx)
        ]
        paras = [p for p in paras if len(p) > 60 and title not in p[: len(title) + 5]]
        body = paras[0] if paras else ""
        if not body and not video and not imgs:
            continue

        local_img = None
        remote = pick_desktop_img(imgs) if imgs else None
        if remote:
            ext = Path(urlparse(remote).path).suffix or ".jpg"
            dest = IMG / key / f"story-{len(sections)+1}{ext}"
            local_img = download(remote, dest)
            if local_img and not local_img.startswith("/"):
                local_img = "/" + local_img

        layout = "default"
        if video:
            layout = "default"
        elif not body and local_img:
            layout = "wide"

        sections.append(
            {
                "titleEn": title,
                "bodyEn": body,
                "image": local_img,
                "videoUrl": video,
                "layout": layout,
                "reverse": bool(video) or (len(sections) % 2 == 1),
            }
        )
        seen_titles.add(title)

    # Caption cards under editorial images
    caps = re.findall(
        r'<div class="text-block[^"]*"[^>]*>\s*<p[^>]*>([\s\S]*?)</p>',
        chunk,
    )
    cap_imgs = re.findall(
        r'data-src(?:set)?="(https://www\.christopherward\.com[^"]+/pdp-long-description/[^"]+)"',
        chunk,
    )
    desktop_caps = []
    seen_c = set()
    for u in cap_imgs:
        u = H.unescape(u.split(" ")[0].split(",")[0].split("?")[0])
        name = u.split("/")[-1].lower()
        if any(x in name for x in ["_mob", "tabport", "tabland", "video-replacement"]):
            continue
        if u in seen_c:
            continue
        seen_c.add(u)
        desktop_caps.append(u)

    unique_caps = []
    for c in caps:
        t = clean_text(c)
        if t and t not in unique_caps and len(t) > 25:
            unique_caps.append(t)

    # Pair captions with later gallery images (skip video poster / movement duplicates)
    pair_imgs = [
        u
        for u in desktop_caps
        if not u.lower().endswith("movement.webp")
        and "video-replacement" not in u.lower()
    ]
    # Prefer numbered 1..n assets
    pair_imgs = sorted(
        set(pair_imgs),
        key=lambda u: (
            0 if re.search(r"/(\d+)(?:@2x)?\.(webp|jpg|png)$", u) else 1,
            u,
        ),
    )

    for i, cap in enumerate(unique_caps[:8]):
        remote = pair_imgs[i] if i < len(pair_imgs) else None
        local = None
        if remote:
            ext = Path(urlparse(remote).path).suffix or ".jpg"
            dest = IMG / key / f"caption-{i+1}{ext}"
            local = download(remote, dest)
            if local and not local.startswith("/"):
                local = "/" + local
        if not local:
            continue
        sections.append(
            {
                "titleEn": "",
                "bodyEn": cap,
                "image": local,
                "videoUrl": None,
                "layout": "caption",
                "reverse": i % 2 == 1,
            }
        )

    # Also collect zoom/lifestyle product images into gallery extras from watch gallery HTML via page
    extra_gallery = []
    for u in re.findall(
        r'(https://www\.christopherward\.com/dw/image/[^"\s>]+\.(?:jpg|jpeg|png|webp))',
        chunk,
        re.I,
    ):
        u = H.unescape(u.split("?")[0])
        if "/SWATCHES/" in u:
            continue
        if u not in extra_gallery:
            extra_gallery.append(u)

    return {
        "modelKey": key,
        "sourceUrl": url,
        "sections": sections,
        "extraGalleryUrls": extra_gallery[:12],
    }


def main():
    # unique model pages from raw
    models = {}
    for p in RAW["products"]:
        url = p.get("url") or ""
        key = model_key(url)
        if not key:
            continue
        if key not in models:
            models[key] = url

    print("models", len(models))
    results = {}
    if OUT.exists():
        try:
            results = json.loads(OUT.read_text()).get("models") or {}
        except Exception:
            results = {}

    todo = [(k, u) for k, u in models.items() if k not in results or not results[k].get("sections")]
    print("todo", len(todo), "cached", len(results))

    done = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(scrape_page, u, k): k for k, u in todo}
        for f in as_completed(futs):
            key = futs[f]
            try:
                results[key] = f.result()
            except Exception as e:
                results[key] = {"modelKey": key, "error": str(e), "sections": []}
            done += 1
            if done % 10 == 0:
                print(" ", done, "/", len(todo))
                OUT.write_text(
                    json.dumps({"scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "models": results}, ensure_ascii=False, indent=2)
                )

    OUT.write_text(
        json.dumps(
            {
                "scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "models": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    ok = sum(1 for v in results.values() if v.get("sections"))
    print("done models", len(results), "with sections", ok, "→", OUT)

    # Attach modelKey editorial onto enriched products by URL
    if ENR_PATH.exists():
        enr = json.loads(ENR_PATH.read_text())
        prods = enr.get("products") or {}
        by_sku_url = {p["sku"]: p.get("url") for p in RAW["products"]}
        attached = 0
        for sku, row in prods.items():
            url = row.get("sourceUrl") or by_sku_url.get(sku) or ""
            # strip query
            url = url.split("?")[0]
            key = model_key(url)
            if key and key in results and results[key].get("sections"):
                row["editorial"] = results[key]
                attached += 1
        ENR_PATH.write_text(json.dumps(enr, ensure_ascii=False, indent=2))
        print("attached editorial to", attached, "enriched rows")


if __name__ == "__main__":
    main()
