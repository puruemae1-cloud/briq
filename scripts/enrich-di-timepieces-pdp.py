#!/usr/bin/env python3
"""Enrich all Dior timepieces PDPs from official GB product pages.

1) Playwright-fetch each watch PDP → inspiration / characteristics / gallery
2) Download every product+look image into public/products/di-pdp/{slug}/
3) Translate EN → KO (cache + retries; never shrink existing good Korean)
4) Write descriptionKo / featuresKo / storySections into di-catalog.json

  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    python3 scripts/enrich-di-timepieces-pdp.py --fetch-only
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    python3 scripts/enrich-di-timepieces-pdp.py --apply
  python3 scripts/enrich-di-timepieces-pdp.py --only CD08461X1825_0000 --force
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from di_common import (  # noqa: E402
    BASE,
    IMG_ROOT,
    UA,
    download_image,
    extract_next_data,
    normalize_di_product_prices,
    slugify,
)
from ko_qa import is_good_korean, translate_en_to_ko  # noqa: E402

CAT = ROOT / "src/data/di/di-catalog.json"
PDP_CACHE = ROOT / "src/data/di/di-timepieces-pdp-cache.json"
TRANSLATE_CACHE = ROOT / "src/data/di/di-translate-cache.json"
CHECKPOINT_EVERY = 5

WATCH_LEAVES = {
    "dior-watches",
    "di-timepieces-all",
    "di-la-d-de-dior",
    "di-straps",
}


def log(msg: str) -> None:
    print(msg, flush=True)


def load_json(path: Path, default):
    if path.is_file():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    s = html_lib.unescape(str(text))
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</p\s*>", "\n\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def accept_cookies(page) -> None:
    for sel in (
        "#onetrust-accept-btn-handler",
        'button:has-text("Accept All")',
        'button:has-text("Accept")',
    ):
        try:
            page.locator(sel).first.click(timeout=2000)
            time.sleep(0.4)
            return
        except Exception:
            pass


def image_urls_from_product(prod: dict) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []

    def add(uri: str | None) -> None:
        if not uri or not isinstance(uri, str):
            return
        base = uri.split("?")[0]
        if base in seen:
            return
        if "christiandior.com" not in uri and "dam-broadcast.com" not in uri:
            return
        seen.add(base)
        if "is/image" in uri:
            out.append(f"{base}?$r2x3_default$&wid=1334&hei=2000&bfc=on&qlt=90")
        else:
            out.append(uri)

    for block in prod.get("medias") or []:
        presets = (block or {}).get("presetImages") or {}
        for key in ("r2x3detail", "r4x5detail", "r9x10detail"):
            node = presets.get(key)
            if isinstance(node, dict) and node.get("uri"):
                add(node["uri"])
                break

    views = prod.get("views") or {}
    for section in ("detail", "listing", "transparent"):
        block = views.get(section) or {}
        images = (block.get("images") or {}) if isinstance(block, dict) else {}
        for key in ("r2x3detail", "r4x5detail", "r9x10detail", "r2x3listing"):
            node = images.get(key)
            if isinstance(node, dict):
                add(node.get("uri"))
    for alt in views.get("alternatives") or []:
        images = ((alt or {}).get("images") or {}) if isinstance(alt, dict) else {}
        for key in ("r2x3detail", "r4x5detail", "r9x10detail", "r2x3listing"):
            node = images.get(key)
            if isinstance(node, dict):
                add(node.get("uri"))
    return out


def materialize_images(code: str, urls: list[str]) -> list[str]:
    folder = slugify(code)
    out: list[str] = []
    for i, url in enumerate(urls, start=1):
        if not url:
            continue
        rel = f"/products/di-pdp/{folder}/{i}.jpg"
        dest = IMG_ROOT / folder / f"{i}.jpg"
        try:
            if not dest.exists() or dest.stat().st_size < 800:
                download_image(url, dest)
            if dest.exists() and dest.stat().st_size > 800:
                out.append(rel)
        except Exception as e:
            log(f"  WARN img {code} #{i}: {e}")
    return out


def translate(text: str, cache: dict[str, str]) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s:
        return ""
    if is_good_korean(s):
        return s
    if s in cache and is_good_korean(cache[s]):
        return cache[s]
    # Prefer deep_translator — gtx/mymemory often 429 under parallel pipelines
    for attempt in range(5):
        try:
            from deep_translator import GoogleTranslator

            ko = GoogleTranslator(source="en", target="ko").translate(s[:4500])
            if is_good_korean(ko):
                cache[s] = ko
                return ko
        except Exception as e:
            log(f"  tr deep {attempt + 1}: {e}")
            time.sleep(3 * (attempt + 1))
    try:
        ko = translate_en_to_ko(s, cache=cache, retries=3)
        if is_good_korean(ko):
            cache[s] = ko
            return ko
    except Exception as e:
        log(f"  tr gtx fail: {e}")
    return ""


def translate_lines(lines: list[str], cache: dict[str, str]) -> list[str]:
    out: list[str] = []
    for ln in lines:
        ko = translate(ln, cache)
        if ko:
            out.append(ko)
        time.sleep(0.6)
    return out


def candidate_pdp_urls(code: str, source_url: str) -> list[str]:
    """en_gb sometimes returns 'Page unavailable' for watches; try en_us/fr_fr."""
    bare = code.split("_")[0] if "_" in code else code
    urls: list[str] = []
    for locale in ("en_us", "en_gb", "fr_fr"):
        urls.append(f"{BASE}/{locale}/fashion/products/{code}")
        if bare != code:
            urls.append(f"{BASE}/{locale}/fashion/products/{bare}")
    if source_url and source_url.startswith("http"):
        urls.insert(0, source_url)
    # dedupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def fetch_pdp(page, code: str, source_url: str) -> dict | None:
    log(f"  PDP {code}")
    last_err = ""
    for url in candidate_pdp_urls(code, source_url):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=120000)
            accept_cookies(page)
            time.sleep(1.4)
            for _ in range(4):
                page.mouse.wheel(0, 2400)
                time.sleep(0.2)
            html = page.content()
            if "Page unavailable" in html and "product" not in html.lower()[:5000]:
                last_err = "page-unavailable"
                continue
            data = extract_next_data(html) or {}
            prod = ((data.get("props") or {}).get("pageProps") or {}).get("product") or {}
            if not prod.get("code") and not prod.get("title"):
                last_err = "no-product"
                continue
            chars = prod.get("characteristics") or []
            if isinstance(chars, str):
                chars = [
                    ln.strip()
                    for ln in chars.replace("\r", "").split("\n")
                    if ln.strip()
                ]
            elif isinstance(chars, list):
                chars = [strip_html(str(c)) for c in chars if str(c).strip()]
            else:
                chars = []
            # Prefer English copy — skip FR-only if we already have EN attempts
            inspiration = strip_html(prod.get("inspiration") or "")
            title = (prod.get("title") or "").strip()
            gallery = image_urls_from_product(prod)
            log(f"    ok via {url.split('.com')[-1][:48]} insp={len(inspiration)} gal={len(gallery)}")
            return {
                "code": prod.get("code") or code,
                "title": title,
                "subtitle": strip_html(prod.get("subtitle") or ""),
                "description": strip_html(prod.get("description") or ""),
                "inspiration": inspiration,
                "characteristics": chars,
                "gallery": gallery,
                "madein": (prod.get("traceability") or {}).get("madeIn")
                or next((c for c in chars if c.lower().startswith("made in")), None),
                "sourceUrl": url,
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
                "source": "pdp-next-data",
            }
        except Exception as e:
            last_err = str(e)
            continue
    log(f"  FAIL {code} ({last_err})")
    return None


def is_watch_product(p: dict) -> bool:
    cols = set(p.get("diCollections") or [])
    sub = p.get("subcategory") or ""
    return (
        sub in WATCH_LEAVES
        or bool(cols & WATCH_LEAVES)
        or (
            p.get("category") == "watches"
            and (p.get("brand") or "").lower() == "dior"
        )
    )


def pdp_is_rich(pdp: dict | None) -> bool:
    if not pdp or pdp.get("source") != "pdp-next-data":
        return False
    if not (pdp.get("inspiration") or pdp.get("characteristics")):
        return False
    return len(pdp.get("gallery") or []) >= 1


def story_sections(
    description_ko: str,
    images: list[str],
    features_ko: list[str],
) -> list[dict]:
    if not images:
        return [{"titleKo": "제품 소개", "bodyKo": description_ko, "image": ""}]
    sections = [
        {"titleKo": "제품 소개", "bodyKo": description_ko, "image": images[0]},
    ]
    if features_ko and len(images) > 1:
        sections.append(
            {
                "titleKo": "스펙 & 특징",
                "bodyKo": "\n".join(f"· {f}" for f in features_ko[:12]),
                "image": images[min(2, len(images) - 1)],
            }
        )
    if len(images) > 3:
        body = (
            "디올 공식 제품·룩 컷으로 케이스·다이얼·스트랩 디테일을 확인하세요."
            if not features_ko
            else " · ".join(features_ko[:6])
        )
        sections.append(
            {
                "titleKo": "디테일 갤러리",
                "bodyKo": body,
                "image": images[min(4, len(images) - 1)],
            }
        )
    if len(images) > 5:
        pick = next(
            (
                f
                for f in features_ko
                if any(k in f for k in ("무브먼트", "파워", "워런티", "보증", "스위스"))
            ),
            "스위스 제작 무브먼트와 하우스 워치메이킹 디테일을 담았습니다.",
        )
        sections.append(
            {
                "titleKo": "착용 & 무브먼트",
                "bodyKo": pick,
                "image": images[min(5, len(images) - 1)],
            }
        )
    return sections


def prefer_text(new: str, old: str) -> str:
    """Keep the richer Korean (or non-empty) copy."""
    new = (new or "").strip()
    old = (old or "").strip()
    if not new:
        return old
    if not old:
        return new
    if is_good_korean(new) and not is_good_korean(old):
        return new
    if is_good_korean(old) and not is_good_korean(new):
        return old
    return new if len(new) >= len(old) else old


def apply_enrich(product: dict, pdp: dict, cache: dict[str, str]) -> None:
    code = product.get("sku") or product.get("id", "").replace("di-", "").upper()
    title_en = pdp.get("title") or product.get("name") or ""
    subtitle_en = pdp.get("subtitle") or ""
    inspiration_en = pdp.get("inspiration") or ""
    desc_en = pdp.get("description") or ""
    chars = list(pdp.get("characteristics") or [])

    title_ko = translate(title_en, cache) or product.get("nameKo") or title_en
    time.sleep(0.4)
    subtitle_ko = translate(subtitle_en, cache) if subtitle_en else ""
    time.sleep(0.4)
    inspiration_ko = translate(inspiration_en, cache) if inspiration_en else ""
    time.sleep(0.5)
    desc_extra = translate(desc_en, cache) if desc_en else ""
    time.sleep(0.3)
    features_ko = translate_lines(chars, cache)

    parts: list[str] = []
    if inspiration_ko:
        parts.append(inspiration_ko)
    if desc_extra and desc_extra not in (inspiration_ko or ""):
        parts.append(desc_extra)
    if subtitle_ko and subtitle_ko not in "\n".join(parts):
        parts.append(subtitle_ko)
    description_ko = prefer_text(
        "\n\n".join(parts), product.get("descriptionKo") or ""
    )
    if not description_ko:
        description_ko = title_ko

    gallery = list(pdp.get("gallery") or [])
    local_imgs = materialize_images(str(product.get("sku") or code), gallery)
    existing = list(product.get("images") or [])
    if len(local_imgs) >= max(3, len(existing)):
        product["images"] = local_imgs
    elif local_imgs:
        product["images"] = list(dict.fromkeys([*local_imgs, *existing]))
    if product.get("images"):
        product["image"] = product["images"][0]

    product["name"] = title_en or product.get("name")
    if is_good_korean(title_ko):
        product["nameKo"] = title_ko
    product["descriptionKo"] = description_ko
    if features_ko:
        product["featuresKo"] = features_ko
    elif not product.get("featuresKo"):
        product["featuresKo"] = []
    product["storySections"] = story_sections(
        description_ko, product.get("images") or [], product.get("featuresKo") or []
    )

    for v in product.get("variants") or []:
        v["images"] = product.get("images") or v.get("images") or []
        v["image"] = product.get("image") or v.get("image")

    gbp = float(product.get("gbpPrice") or 0)
    if gbp > 0:
        normalize_di_product_prices(product, gbp)


def select_targets(products: list[dict], only: set[str], limit: int) -> list[dict]:
    targets = [p for p in products if is_watch_product(p)]
    if only:
        targets = [
            p
            for p in targets
            if any(
                o.lower() in (p.get("sku") or "").lower()
                or o.lower() in (p.get("id") or "").lower()
                or o.lower().replace("_", "-") in (p.get("id") or "").lower()
                for o in only
            )
        ]
    if limit:
        targets = targets[:limit]
    return targets


def run_fetch(targets: list[dict], pdp_cache: dict, *, force: bool, headed: bool) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.webkit.launch(headless=not headed)
        ctx = browser.new_context(
            user_agent=UA,
            locale="en-US",
            viewport={"width": 1440, "height": 900},
        )
        page = ctx.new_page()
        page.goto(f"{BASE}/en_us/", wait_until="domcontentloaded", timeout=120000)
        accept_cookies(page)

        for i, product in enumerate(targets, 1):
            sku = str(product.get("sku") or "")
            code = sku or str(product.get("id") or "").removeprefix("di-")
            cached = pdp_cache.get(sku) or pdp_cache.get(code)
            if not force and pdp_is_rich(cached):
                log(f"[{i}/{len(targets)}] cache OK {sku}")
                # still materialize images if missing locally
                imgs = materialize_images(sku or code, cached.get("gallery") or [])
                if imgs and len(imgs) > len(product.get("images") or []):
                    product["images"] = imgs
                    product["image"] = imgs[0]
                continue
            try:
                pdp = fetch_pdp(page, code, product.get("sourceUrl") or "")
            except Exception as e:
                log(f"  ERR fetch {sku}: {e}")
                pdp = None
            if pdp:
                pdp_cache[sku or code] = pdp
                save_json(PDP_CACHE, pdp_cache)
                imgs = materialize_images(sku or code, pdp.get("gallery") or [])
                log(
                    f"[{i}/{len(targets)}] fetched {sku} "
                    f"insp={len(pdp.get('inspiration') or '')} "
                    f"chars={len(pdp.get('characteristics') or [])} "
                    f"gal={len(pdp.get('gallery') or [])} local={len(imgs)}"
                )
            else:
                log(f"[{i}/{len(targets)}] FAIL {sku}")
            time.sleep(0.9)
        browser.close()


def run_apply(products: list[dict], targets: list[dict], pdp_cache: dict, tr_cache: dict) -> None:
    for i, product in enumerate(targets, 1):
        sku = str(product.get("sku") or "")
        code = sku or str(product.get("id") or "").removeprefix("di-")
        pdp = pdp_cache.get(sku) or pdp_cache.get(code)
        if not pdp_is_rich(pdp):
            log(f"[{i}/{len(targets)}] SKIP thin cache {sku}")
            continue
        before_imgs = len(product.get("images") or [])
        before_desc = len(product.get("descriptionKo") or "")
        apply_enrich(product, pdp, tr_cache)
        log(
            f"[{i}/{len(targets)}] {sku} "
            f"imgs {before_imgs}->{len(product.get('images') or [])} "
            f"desc {before_desc}->{len(product.get('descriptionKo') or [])} "
            f"feats {len(product.get('featuresKo') or [])}"
        )
        if i % CHECKPOINT_EVERY == 0:
            CAT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
            save_json(TRANSLATE_CACHE, tr_cache)
            log(f"--- checkpoint {i}/{len(targets)} ---")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--fetch-only", action="store_true")
    ap.add_argument("--apply", action="store_true", help="Translate+write catalog from cache")
    ap.add_argument("--all", action="store_true", help="Fetch then apply (default)")
    args = ap.parse_args()
    if not args.fetch_only and not args.apply:
        args.all = True

    products = json.loads(CAT.read_text())
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    targets = select_targets(products, only, args.limit)
    log(f"targets={len(targets)}")

    pdp_cache = load_json(PDP_CACHE, {})
    tr_cache = load_json(TRANSLATE_CACHE, {})

    if args.fetch_only or args.all:
        run_fetch(targets, pdp_cache, force=args.force, headed=args.headed)
        # persist any image path updates from fetch
        CAT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
        save_json(PDP_CACHE, pdp_cache)

    if args.apply or args.all:
        # reload products in case fetch wrote images
        products = json.loads(CAT.read_text())
        targets = select_targets(products, only, args.limit)
        run_apply(products, targets, pdp_cache, tr_cache)
        CAT.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n")
        save_json(TRANSLATE_CACHE, tr_cache)
        save_json(PDP_CACHE, pdp_cache)

    watches = [p for p in products if is_watch_product(p)]
    thin = [
        p
        for p in watches
        if len(p.get("images") or []) < 3
        or len(p.get("descriptionKo") or "") < 80
        or not (p.get("featuresKo") or [])
    ]
    rich_cache = sum(1 for v in pdp_cache.values() if pdp_is_rich(v))
    log(f"DONE watches={len(watches)} thin={len(thin)} rich_pdp_cache={rich_cache}")
    for p in thin[:12]:
        log(
            f"  thin {p.get('sku')} imgs={len(p.get('images') or [])} "
            f"desc={len(p.get('descriptionKo') or [])} feats={len(p.get('featuresKo') or [])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
