#!/usr/bin/env python3
"""
Re-sync all CW PDPs:
- re-download full zoom galleries (verify files)
- re-scrape long-description editorial (text/video/images)
- write cw-editorial.json + refresh enriched image lists
"""
from __future__ import annotations

import html as H
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("/Users/jeonghyunlee/Documents/briq")
RAW = json.loads((ROOT / "src/data/cw/cw-catalog-raw.json").read_text())
ENR_PATH = ROOT / "src/data/cw/cw-pdp-enriched.json"
ED_PATH = ROOT / "src/data/cw/cw-editorial.json"
PDP = ROOT / "public/products/cw-pdp"
EDIT = ROOT / "public/products/cw-editorial"
PDP.mkdir(parents=True, exist_ok=True)
EDIT.mkdir(parents=True, exist_ok=True)

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
}
API = "https://www.christopherward.com/on/demandware.store/Sites-cwgross-Site/en_GB/Product-Variation"


def slugify(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()


def fetch_json(url: str, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={**UA, "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
            )
            with urllib.request.urlopen(req, timeout=55) as r:
                return json.load(r)
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(1.1 * (i + 1))


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=70) as r:
        return r.read().decode("utf-8", "replace")


def download(url: str, dest: Path, min_bytes=2500) -> bool:
    try:
        if dest.exists() and dest.stat().st_size > min_bytes:
            return True
        full = url + ("&" if "?" in url else "?") + "sw=1400&sh=1600"
        req = urllib.request.Request(full, headers={"User-Agent": UA["User-Agent"]})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if len(data) < min_bytes:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception:
        return False


def parse_price(product: dict):
    html = (product.get("price") or {}).get("html") or ""
    vals = [float(x) for x in re.findall(r'content="([\d.]+)"', html)]
    if not vals:
        return None, None
    if 'class="range"' in html or "price range" in html.lower():
        # Range across options — caller should prefer raw SKU price.
        return max(vals), min(vals) if len(vals) > 1 else None
    if "strike-through list" in html and len(vals) >= 2:
        return vals[1], vals[0]
    return vals[0], None


def collect_zoom_urls(product: dict) -> list[str]:
    urls = []
    imgs = product.get("images") or {}
    for key in ("zoomImage", "large", "hiRes"):
        for i in imgs.get(key) or []:
            u = i.get("url") if isinstance(i, dict) else None
            if u:
                urls.append(u)
    for html_key in ("watchGalleryHtml", "secondaryWatchGalleryHtml", "imageCarouselHtml"):
        html = product.get(html_key) or ""
        urls.extend(re.findall(r"https://www\.christopherward\.com/dw/image/[^\"'\s>]+", html))
    out, seen = [], set()
    for u in urls:
        b = H.unescape(u.split("?")[0])
        if "/SWATCHES/" in b or b in seen:
            continue
        seen.add(b)
        out.append(b)
    return out[:12]


def sku_from_urls(urls: list[str], fallback: str) -> str:
    for u in urls:
        m = re.search(r"/WATCHES/([A-Za-z0-9][A-Za-z0-9\-]+)/", u)
        if m and "-" in m.group(1) and len(m.group(1)) > 8:
            return m.group(1)
    return fallback


def sync_gallery(sku: str) -> list[str]:
    data = fetch_json(f"{API}?pid={urllib.parse.quote(sku)}&quantity=1")
    p = data.get("product") or {}
    urls = collect_zoom_urls(p)
    real = sku_from_urls(urls, p.get("id") or sku)
    if ("-" not in real or len(real) < 10) and "-" in sku:
        real = sku
    folder = PDP / slugify(real)
    folder.mkdir(parents=True, exist_ok=True)
    # wipe broken tiny files
    for f in folder.glob("*.jpg"):
        if f.stat().st_size < 2500:
            f.unlink(missing_ok=True)
    locals_ = []
    for i, u in enumerate(urls, 1):
        dest = folder / f"{i}.jpg"
        ok = download(u, dest)
        if ok:
            locals_.append(f"/products/cw-pdp/{folder.name}/{i}.jpg")
    # remove leftover higher indexes that aren't in new set
    for f in folder.glob("*.jpg"):
        n = int(re.sub(r"\D", "", f.stem) or "0")
        if n > len(locals_):
            f.unlink(missing_ok=True)
    gbp, list_gbp = parse_price(p)
    return {
        "sku": real,
        "seedSku": sku,
        "gbpPrice": gbp,
        "gbpListPrice": list_gbp,
        "images": locals_,
        "image": locals_[0] if locals_ else None,
        "nameEn": p.get("productName"),
        "shortDescriptionEn": H.unescape(p.get("shortDescription") or "").strip(),
        "featuresEn": [
            H.unescape(str(f)).replace("\xa0", " ").strip()
            for f in (p.get("productFeatures") or [])
            if f
        ],
        "technicalsEn": [
            {"labelEn": str(t.get("label") or "").strip(), "valueEn": str(t.get("value") if not isinstance(t.get("value"), list) else ", ".join(map(str, t.get("value")))).strip()}
            for t in (p.get("productTechnicals") or [])
            if t.get("label") and t.get("value") is not None
        ],
        "product": p,
    }


def clean_text(s: str) -> str:
    s = H.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_css_junk(s: str) -> bool:
    return bool(re.search(r"\{[^}]*:|\.section-|@media|padding:|display:\s*flex|margin-", s))


def model_key(url: str) -> str | None:
    path = urlparse(url.split("?")[0]).path.strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and parts[-1].endswith(".html"):
        return parts[-2]
    return parts[-1].replace(".html", "") if parts else None


def pick_img(urls: list[str]) -> str | None:
    scored = []
    for u in urls:
        name = u.split("/")[-1].lower()
        if any(x in name for x in ["_mob", "tabport", "tabland", "favicon", "icon", "video-replacement"]):
            continue
        score = 0
        if "@2x" in name:
            score += 3
        if re.match(r"^\d", name):
            score += 2
        if name.endswith((".jpg", ".jpeg", ".webp", ".png")):
            score += 1
        scored.append((score, u))
    if not scored:
        return None
    scored.sort(reverse=True)
    return scored[0][1]


def scrape_editorial(url: str, key: str) -> dict:
    html = fetch_html(url)
    start = html.find("pdp-long-description")
    if start < 0:
        start = html.find("/images/pdp-long-description/")
    end = len(html)
    for m in ("You might also like", "you-might-also", "Recently viewed", "pdpRecommendation"):
        i = html.find(m, max(0, start))
        if i > 0:
            end = min(end, i)
    chunk = html[max(0, start - 800) : end] if start > 0 else ""
    if len(chunk) < 500:
        return {"modelKey": key, "sourceUrl": url, "sections": [], "error": "no-long-desc"}

    sections = []
    seen = set()

    # Title blocks
    for m in re.finditer(r"<h2[^>]*>([\s\S]*?)</h2>", chunk):
        title = clean_text(m.group(1))
        if not title or len(title) < 2:
            continue
        low = title.lower()
        if any(x in low for x in ["cookie", "newsletter", "related", "basket", "cart", "technical", "features"]):
            # Technical/Features are covered by techSpecs — skip duplicate HTML tables
            if low in ("technical", "features"):
                continue
            continue
        if title in seen:
            continue
        ctx = chunk[m.start() : m.start() + 6000]
        # Ignore commented-out leftover embeds (CW often leaves old Vimeo iframes in <!-- -->)
        ctx_live = re.sub(r"<!--([\s\S]*?)-->", "", ctx)
        vid_m = re.search(
            r'(?:data-src|src)="(https://player\.vimeo\.com/video/\d[^"]*)"',
            ctx_live,
        )
        video = H.unescape(vid_m.group(1)).rstrip('"').replace("%22", "") if vid_m else None
        # Drop autoplay dial-loop clips; keep story embeds
        if video and ("autoplay=1" in video or "controls=0" in video):
            video = None
        imgs = [
            H.unescape(u.split(" ")[0].split(",")[0].split("?")[0])
            for u in re.findall(
                r'(?:data-src|data-srcset|src)="(https://www\.christopherward\.com[^"]+/pdp-long-description/[^"]+)"',
                ctx,
            )
        ]
        paras = [clean_text(p) for p in re.findall(r"<p[^>]*>([\s\S]*?)</p>", ctx)]
        paras = [p for p in paras if len(p) > 50 and not is_css_junk(p) and title not in p[: len(title) + 2]]
        # Prefer the longest meaningful paragraph
        body = max(paras, key=len) if paras else ""
        if not body and not video and not imgs:
            continue

        local = None
        remote = pick_img(imgs)
        if remote:
            ext = Path(urlparse(remote).path).suffix.lower() or ".jpg"
            if ext not in (".jpg", ".jpeg", ".png", ".webp"):
                ext = ".jpg"
            dest = EDIT / key / f"story-{len(sections)+1}{ext}"
            if download(remote, dest, min_bytes=2000):
                # normalize to jpg when possible later; keep path
                local = f"/products/cw-editorial/{key}/{dest.name}"

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
        seen.add(title)

    # Caption cards
    caps = []
    for c in re.findall(r'<div class="text-block[^"]*"[^>]*>\s*<p[^>]*>([\s\S]*?)</p>', chunk):
        t = clean_text(c)
        if t and len(t) > 25 and not is_css_junk(t) and t not in caps:
            caps.append(t)

    img_urls = []
    for u in re.findall(
        r'(?:data-src|data-srcset|src)="(https://www\.christopherward\.com[^"]+/pdp-long-description/[^"]+)"',
        chunk,
    ):
        u = H.unescape(u.split(" ")[0].split(",")[0].split("?")[0])
        name = u.split("/")[-1].lower()
        if any(x in name for x in ["_mob", "tabport", "tabland", "video-replacement", "movement"]):
            continue
        if u not in img_urls:
            img_urls.append(u)

    # Prefer numbered desktop assets
    numbered = []
    for u in img_urls:
        name = u.split("/")[-1]
        if re.match(r"^\d+(@2x)?\.(jpg|jpeg|png|webp)$", name, re.I):
            numbered.append(u)
    # de-dupe by number keeping @2x
    by_num = {}
    for u in numbered:
        n = re.match(r"^(\d+)", u.split("/")[-1]).group(1)
        if n not in by_num or "@2x" in u:
            by_num[n] = u
    pair_imgs = [by_num[k] for k in sorted(by_num, key=lambda x: int(x))]

    for i, cap in enumerate(caps[:10]):
        remote = pair_imgs[i] if i < len(pair_imgs) else None
        local = None
        if remote:
            ext = Path(urlparse(remote).path).suffix.lower() or ".jpg"
            dest = EDIT / key / f"caption-{i+1}{ext}"
            if download(remote, dest, min_bytes=2000):
                local = f"/products/cw-editorial/{key}/{dest.name}"
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

    # Wide leftover numbered images not used as captions
    used = {s.get("image") for s in sections if s.get("image")}
    for i, remote in enumerate(pair_imgs):
        ext = Path(urlparse(remote).path).suffix.lower() or ".jpg"
        dest = EDIT / key / f"wide-{i+1}{ext}"
        local = f"/products/cw-editorial/{key}/{dest.name}"
        if local in used:
            continue
        # only add extras if we have few sections
        if len([s for s in sections if s.get("layout") == "caption"]) >= 4:
            break
        if download(remote, dest, min_bytes=2000):
            # skip if already have as caption
            pass

    return {"modelKey": key, "sourceUrl": url, "sections": sections}


def main():
    # Unique full SKUs
    skus = []
    seen = set()
    for p in RAW["products"]:
        s = p.get("sku") or ""
        if s.count("-") < 2 or s in seen:
            continue
        seen.add(s)
        skus.append(s)
    print("sync galleries", len(skus))

    enr = {"products": {}}
    if ENR_PATH.exists():
        try:
            enr = json.loads(ENR_PATH.read_text())
        except Exception:
            enr = {"products": {}}
    products = enr.get("products") or {}

    done = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(sync_gallery, s): s for s in skus}
        for f in as_completed(futs):
            seed = futs[f]
            try:
                row = f.result()
            except Exception as e:
                print("gallery fail", seed, e)
                done += 1
                continue
            sku = row["sku"]
            prev = products.get(sku) or products.get(seed) or {}
            merged = {**prev, **{k: row[k] for k in row if k != "product"}}
            # Keep strapVariants from prev; prices will be fixed from raw in rebuild
            products[sku] = merged
            products[seed] = merged
            # Also update strap variant galleries if matching sku
            for v in merged.get("strapVariants") or []:
                if v.get("sku") == sku and row.get("images"):
                    v["images"] = row["images"]
                    v["image"] = row["images"][0]
                    if row.get("gbpPrice") and ("-" in sku and len(sku) > 10):
                        v["gbpPrice"] = row["gbpPrice"]
            done += 1
            if done % 40 == 0:
                print(" ", done, "/", len(skus))
                enr["products"] = products
                ENR_PATH.write_text(json.dumps(enr, ensure_ascii=False, indent=2))

    enr["products"] = products
    enr["scrapedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ENR_PATH.write_text(json.dumps(enr, ensure_ascii=False, indent=2))
    print("galleries done")

    # Editorial by model
    models = {}
    for p in RAW["products"]:
        url = p.get("url") or ""
        key = model_key(url)
        if key and key not in models:
            models[key] = url
    print("editorial models", len(models))
    ed = {}
    todo = list(models.items())
    done = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(scrape_editorial, u, k): k for k, u in todo}
        for f in as_completed(futs):
            key = futs[f]
            try:
                ed[key] = f.result()
            except Exception as e:
                ed[key] = {"modelKey": key, "error": str(e), "sections": []}
            done += 1
            if done % 10 == 0:
                print(" ", done, "/", len(todo))
                ED_PATH.write_text(
                    json.dumps({"scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "models": ed}, ensure_ascii=False, indent=2)
                )

    ED_PATH.write_text(
        json.dumps(
            {"scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "models": ed},
            ensure_ascii=False,
            indent=2,
        )
    )
    ok = sum(1 for v in ed.values() if len(v.get("sections") or []) >= 2)
    print("editorial done", len(ed), "rich", ok)


if __name__ == "__main__":
    main()
