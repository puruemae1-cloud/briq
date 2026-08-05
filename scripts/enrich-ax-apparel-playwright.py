#!/usr/bin/env python3
"""Enrich Arc'teryx outdoor apparel PDPs via Playwright (__NEXT_DATA__).

Captures per colour×size stockStatus, full galleries, description/features,
then downloads galleries into public/products/axa-pdp.

Usage:
  python3 scripts/enrich-ax-apparel-playwright.py
  python3 scripts/enrich-ax-apparel-playwright.py --limit 5
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from studio_whiten import whiten_file  # noqa: E402

RAW_PATH = ROOT / "src/data/ax/ax-apparel-raw.json"
OUT_PATH = ROOT / "src/data/ax/ax-apparel-pdp-cache.json"
IMG_ROOT = ROOT / "public/products/axa-pdp"

REFRESH_STOCK = os.environ.get("AX_REFRESH_STOCK", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:80] or "item"


def size_label(raw: str) -> str:
    """00-S → 00S, 32-R → 32R."""
    return (raw or "").replace("-", "").strip()


def dismiss_cookies(page) -> None:
    for sel in (
        "#onetrust-accept-btn-handler",
        "button#onetrust-accept-btn-handler",
        "button:has-text('Accept All')",
        "button:has-text('Allow all')",
    ):
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=1500):
                loc.click(timeout=3000)
                page.wait_for_timeout(500)
                return
        except Exception:
            pass
    # Hide banner if still present
    try:
        page.evaluate(
            """() => {
              const el = document.getElementById('onetrust-consent-sdk');
              if (el) el.style.display = 'none';
            }"""
        )
    except Exception:
        pass


def strip_html(text: str) -> str:
    s = re.sub(r"<br\s*/?>", "\n", text or "", flags=re.I)
    s = re.sub(r"</p\s*>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&nbsp;", " ", s)
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def colour_gallery_urls(colour: dict) -> list[str]:
    """Collect real PDP gallery URLs for a colour option (skip placeholders)."""
    imgs: list[str] = []

    def add(u: str | None) -> None:
        u = (u or "").strip()
        if not u or "placeholder" in u.lower():
            return
        if not (u.startswith("http://") or u.startswith("https://")):
            return
        if u not in imgs:
            imgs.append(u)

    for asset in colour.get("imageAssets") or []:
        if isinstance(asset, dict):
            add(((asset.get("image") or {}).get("url") or ""))
            add(asset.get("url"))
        elif isinstance(asset, str):
            add(asset)
    hero = colour.get("heroImage") or {}
    if isinstance(hero, dict):
        add(((hero.get("image") or {}).get("url") or ""))
        add(hero.get("url"))
    # Fallback: any arcteryx image URL nested in the colour blob
    if len(imgs) < 3:
        blob = json.dumps(colour, ensure_ascii=False)
        for u in re.findall(r"https://(?:images(?:-dynamic)?\.)[^\"\\]+", blob):
            add(u)
    return imgs


def parse_product(prod: dict) -> dict:
    colour_by_id = {}
    colours: list[str] = []
    colour_images: dict[str, list[str]] = {}
    for c in prod.get("colourOptions") or []:
        label = (c.get("label") or "").strip()
        if not label:
            continue
        colours.append(label)
        colour_by_id[str(c.get("id"))] = label
        colour_images[label] = colour_gallery_urls(c)

    size_by_id = {}
    sizes: list[str] = []
    for opt in (prod.get("sizeOptions") or {}).get("options") or []:
        label = size_label(opt.get("label") or "")
        if not label:
            continue
        sizes.append(label)
        size_by_id[str(opt.get("value"))] = label

    variants = []
    for v in prod.get("variants") or []:
        cid = str(v.get("colourId") or "")
        sid = str(v.get("sizeId") or "")
        color = colour_by_id.get(cid)
        size = size_by_id.get(sid)
        if not color or not size:
            continue
        status = v.get("stockStatus") or "OutOfStock"
        variants.append(
            {
                "variantSku": v.get("id"),
                "color": color,
                "size": size,
                "stockStatus": status,
                "inStock": status in ("InStock", "LowStock"),
                "gbpPrice": v.get("discountPrice") or v.get("price"),
                "gbpListPrice": v.get("price"),
            }
        )

    # Story content (exclude reviews/Q&A)
    sections: list[dict] = []
    short = strip_html(prod.get("shortDescription") or "")
    long = strip_html(prod.get("description") or "")
    if long:
        sections.append(
            {
                "heading": prod.get("name") or prod.get("marketingName") or "",
                "body": long,
            }
        )
    elif short:
        sections.append(
            {
                "heading": prod.get("name") or "",
                "body": short,
            }
        )

    features: list[dict] = []
    for kf in prod.get("keyFeatures") or []:
        title = strip_html(kf.get("title") or "")
        body = strip_html(kf.get("description") or "")
        if body:
            features.append({"title": title, "body": body})
    for feat in prod.get("features") or []:
        label = strip_html(feat.get("label") or "")
        vals = feat.get("value") or []
        if isinstance(vals, list):
            body = " · ".join(strip_html(str(x)) for x in vals if x)
        else:
            body = strip_html(str(vals))
        if body:
            features.append({"title": label, "body": body})

    materials = prod.get("materials") or []
    if materials:
        if isinstance(materials, list):
            mat_body = " · ".join(
                (m.get("label") or m.get("value") or str(m))
                if isinstance(m, dict)
                else str(m)
                for m in materials
            )
        else:
            mat_body = str(materials)
        if mat_body.strip():
            features.append({"title": "Materials", "body": mat_body.strip()})

    care = prod.get("careInstructions") or []
    if care:
        if isinstance(care, list):
            care_body = " · ".join(str(x) for x in care if x)
        else:
            care_body = str(care)
        if care_body.strip():
            features.append({"title": "Care", "body": care_body.strip()})

    fit = prod.get("fit")
    if isinstance(fit, dict):
        fit_body = fit.get("description") or fit.get("label") or ""
        if fit_body:
            features.append({"title": "Fit", "body": str(fit_body)})
    elif isinstance(fit, str) and fit.strip():
        features.append({"title": "Fit", "body": fit.strip()})

    sale = prod.get("discountPrice") or prod.get("price")
    list_p = prod.get("price") or sale

    return {
        "url": f"https://arcteryx.com/gb/en/shop/{prod.get('slug')}",
        "title": prod.get("name") or prod.get("marketingName"),
        "tagline": short or (prod.get("shortDescription") or ""),
        "gbpPrice": sale,
        "gbpListPrice": list_p,
        "colours": colours,
        "sizes": sizes,
        "colourImages": colour_images,
        "variants": variants,
        "sections": sections,
        "features": features,
        "gender": prod.get("gender"),
        "category": prod.get("categoryEnglish") or prod.get("category"),
        "subCategory": prod.get("subCategoryEnglish") or prod.get("subCategory"),
        "sizingChart": prod.get("sizingChart"),
        "weight": prod.get("weight"),
        "has3d": False,
    }


def fetch_one(page, url: str) -> dict:
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    dismiss_cookies(page)
    try:
        # __NEXT_DATA__ is a hidden <script>; must use attached not visible
        page.wait_for_selector("#__NEXT_DATA__", state="attached", timeout=45000)
    except Exception:
        page.wait_for_timeout(5000)
    next_data = page.evaluate(
        """() => {
          const nd = document.getElementById('__NEXT_DATA__');
          return nd ? JSON.parse(nd.textContent) : null;
        }"""
    )
    if not next_data:
        return {"error": "no __NEXT_DATA__"}
    raw_prod = next_data["props"]["pageProps"].get("product")
    if not raw_prod:
        return {"error": "no product"}
    prod = json.loads(raw_prod) if isinstance(raw_prod, str) else raw_prod
    return parse_product(prod)


def numbered_jpgs(d: Path) -> list[Path]:
    if not d.exists():
        return []
    out = []
    for p in d.iterdir():
        if p.is_file() and re.fullmatch(r"\d+\.jpg", p.name, flags=re.I):
            if p.stat().st_size > 800:
                out.append(p)
    return sorted(out, key=lambda p: int(p.stem))


def gallery_count(pid: str, color: str) -> int:
    return len(numbered_jpgs(IMG_ROOT / pid / slugify(color)))


def purge_space_named_images(d: Path) -> int:
    """Remove macOS-style duplicate names like '1 2.jpg' that break URLs."""
    n = 0
    if not d.exists():
        return 0
    for p in list(d.iterdir()):
        if p.is_file() and " " in p.name and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            try:
                p.unlink()
                n += 1
            except Exception:
                pass
    return n


def download_images(
    pid: str, colour_images: dict[str, list[str]], *, force: bool = False
) -> None:
    jobs = []
    for color, urls in colour_images.items():
        urls = [u for u in (urls or []) if u and "placeholder" not in u.lower()]
        if not urls:
            continue
        cslug = slugify(color)
        d = IMG_ROOT / pid / cslug
        d.mkdir(parents=True, exist_ok=True)
        purge_space_named_images(d)
        have = gallery_count(pid, color)
        want = min(8, len(urls))
        if not force and have >= want and have >= min(6, want):
            continue
        for i, url in enumerate(urls[:8], start=1):
            dest = d / f"{i}.jpg"
            if force or not dest.exists() or dest.stat().st_size <= 800:
                jobs.append((url, dest, True))
            else:
                jobs.append((url, dest, False))
        jobs.append((urls[0], d / "thumb.jpg", force or not (d / "thumb.jpg").exists()))
    if not jobs:
        return

    def one(url: str, dest: Path, overwrite: bool) -> bool:
        if not overwrite and dest.exists() and dest.stat().st_size > 800:
            return True
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/*"})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
            if len(data) < 800:
                return False
            # Atomic write avoids macOS creating "1 2.jpg" duplicates
            tmp = dest.with_suffix(".tmp.jpg")
            tmp.write_bytes(data)
            tmp.replace(dest)
            whiten_file(dest)
            return True
        except Exception:
            return False

    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(one, u, p, ow) for u, p, ow in jobs]
        for _ in as_completed(futs):
            pass


def compress_new_jpegs(root: Path) -> None:
    """Re-encode oversized new downloads without changing pixel dimensions."""
    import subprocess

    for p in root.rglob("*.jpg"):
        try:
            # Skip macOS duplicate names ("1 2.jpg") that sips may create
            if " " in p.name:
                try:
                    p.unlink()
                except Exception:
                    pass
                continue
            if p.stat().st_size < 220_000:
                continue
            # Never sips --out to the same path — macOS creates "name 2.jpg"
            tmp = p.with_suffix(".sips.jpg")
            subprocess.check_call(
                [
                    "sips",
                    "-s",
                    "format",
                    "jpeg",
                    "-s",
                    "formatOptions",
                    "68",
                    str(p),
                    "--out",
                    str(tmp),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if tmp.exists() and tmp.stat().st_size > 800:
                tmp.replace(p)
            elif tmp.exists():
                tmp.unlink()
        except Exception:
            try:
                p.with_suffix(".sips.jpg").unlink(missing_ok=True)  # type: ignore[arg-type]
            except Exception:
                pass


def main() -> None:
    global RAW_PATH, OUT_PATH, IMG_ROOT

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="Comma-separated SKUs")
    ap.add_argument("--skip-images", action="store_true")
    ap.add_argument(
        "--force-images",
        action="store_true",
        help="Re-download galleries even when local files exist",
    )
    ap.add_argument(
        "--refresh",
        action="store_true",
        help="Re-fetch PDPs even when cached (stock sync)",
    )
    ap.add_argument(
        "--refresh-thin",
        action="store_true",
        help="Re-fetch products with thin PDP/missing galleries",
    )
    ap.add_argument("--raw", default="", help="Override raw JSON path")
    ap.add_argument("--out", default="", help="Override PDP cache path")
    ap.add_argument("--img", default="", help="Override image root")
    args = ap.parse_args()

    if args.raw:
        RAW_PATH = ROOT / args.raw
    if args.out:
        OUT_PATH = ROOT / args.out
    if args.img:
        IMG_ROOT = ROOT / args.img

    refresh = bool(args.refresh or REFRESH_STOCK)

    raw = json.loads(RAW_PATH.read_text())
    products = raw["products"]
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        products = [p for p in products if p["id"] in want]
    if args.limit:
        products = products[: args.limit]

    cache: dict = {}
    if OUT_PATH.exists():
        cache = json.loads(OUT_PATH.read_text())

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        ctx = browser.new_context(
            user_agent=UA, locale="en-GB", viewport={"width": 1440, "height": 900}
        )
        page = ctx.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        def is_thin(row: dict) -> bool:
            if not row or row.get("error"):
                return True
            ci = row.get("colourImages") or {}
            if not ci:
                return True
            if any(any("placeholder" in (u or "") for u in urls) for urls in ci.values()):
                return True
            if any(len(urls) < 3 for urls in ci.values()):
                return True
            feats = row.get("features") or []
            body = "".join((s.get("body") or "") for s in (row.get("sections") or []))
            if len(feats) < 2 and len(body) < 250:
                return True
            if not row.get("variants"):
                return True
            return False

        for i, p in enumerate(products):
            pid = p["id"]
            existing = cache.get(pid) or {}
            thin = is_thin(existing)
            if (
                not refresh
                and not args.only
                and not (args.refresh_thin and thin)
                and existing.get("variants")
                and existing.get("colourImages")
                and (existing.get("sections") or existing.get("features"))
                and not existing.get("error")
                and not thin
            ):
                # Still top-up incomplete local galleries from cached URLs
                if not args.skip_images and existing.get("colourImages"):
                    download_images(
                        pid,
                        existing.get("colourImages") or {},
                        force=bool(args.force_images),
                    )
                print(f"[{i+1}/{len(products)}] {pid} skip (cached)", flush=True)
                continue
            url = p.get("url") or f"https://arcteryx.com/gb/en/shop/{p.get('slug')}"
            print(f"[{i+1}/{len(products)}] {pid} {p.get('name')}", flush=True)
            try:
                row = fetch_one(page, url)
            except Exception as e:
                row = {"error": str(e), "url": url}
                print("  ERR", e, flush=True)
            if row.get("error"):
                cache[pid] = {**(cache.get(pid) or {}), **row}
            else:
                cache[pid] = row
                if not args.skip_images:
                    download_images(
                        pid,
                        row.get("colourImages") or {},
                        force=bool(args.force_images or thin),
                    )
                in_c = sum(1 for v in row.get("variants") or [] if v.get("inStock"))
                img_n = sum(len(v) for v in (row.get("colourImages") or {}).values())
                print(
                    f"  colours={len(row.get('colours') or [])} "
                    f"sizes={len(row.get('sizes') or [])} "
                    f"images={img_n} features={len(row.get('features') or [])} "
                    f"inStockVariants={in_c}/{len(row.get('variants') or [])}",
                    flush=True,
                )
            OUT_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n")
            time.sleep(0.35 if refresh or args.refresh_thin else 0.15)

        browser.close()

    OUT_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n")
    if not args.skip_images:
        print("Compressing large JPEGs…", flush=True)
        compress_new_jpegs(IMG_ROOT)
    print(f"Wrote {len(cache)} → {OUT_PATH}")


if __name__ == "__main__":
    main()
