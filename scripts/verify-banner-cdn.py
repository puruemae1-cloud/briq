#!/usr/bin/env python3
"""Verify homepage banner files on jsDelivr match the local public/banners tree.

Exits non-zero when GitHub tag / jsDelivr serves stale bytes (common after tag
force-push without purge, or before browser cache-bust deploy).

  python3 scripts/verify-banner-cdn.py
  python3 scripts/verify-banner-cdn.py --sample 20
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANNER_DIR = ROOT / "public" / "banners"
MANIFEST = ROOT / "src/data/banner-refresh-manifest.json"
CDN = "https://cdn.jsdelivr.net/gh/puruemae1-cloud/briq@product-images/public/banners"
RAW = "https://raw.githubusercontent.com/puruemae1-cloud/briq/product-images/public/banners"

KEY_SLOTS = [
    "hero-london-door.jpg",
    "hero-london-door.webp",
    "m/hero-london-door.jpg",
    "m/hero-london-door.webp",
    "t/hero-london-door.jpg",
    "t/hero-london-door.webp",
    "event-now-london.jpg",
    "event-now-london.webp",
    "m/event-now-london.jpg",
    "m/event-now-london.webp",
    "t/event-now-london.jpg",
    "t/event-now-london.webp",
    "watches-bel-canto.jpg",
    "watches-bel-canto.webp",
    "m/watches-bel-canto.jpg",
    "m/watches-bel-canto.webp",
    "t/watches-bel-canto.jpg",
    "t/watches-bel-canto.webp",
    "collection-100-gucci.jpg",
    "collection-100-gucci.webp",
    "m/collection-100-gucci.jpg",
    "m/collection-100-gucci.webp",
    "t/collection-100-gucci.jpg",
    "t/collection-100-gucci.webp",
    "bags-chanel-campaign.jpg",
    "bags-chanel-campaign.webp",
    "m/bags-chanel-campaign.jpg",
    "m/bags-chanel-campaign.webp",
    "t/bags-chanel-campaign.jpg",
    "t/bags-chanel-campaign.webp",
    "shoes-fur-mule.jpg",
    "shoes-fur-mule.webp",
    "m/shoes-fur-mule.jpg",
    "m/shoes-fur-mule.webp",
    "t/shoes-fur-mule.jpg",
    "t/shoes-fur-mule.webp",
    "luxury-heritage-modern.jpg",
    "luxury-heritage-modern.webp",
    "m/luxury-heritage-modern.jpg",
    "m/luxury-heritage-modern.webp",
    "t/luxury-heritage-modern.jpg",
    "t/luxury-heritage-modern.webp",
    "accessories-finishing-edit.jpg",
    "accessories-finishing-edit.webp",
    "m/accessories-finishing-edit.jpg",
    "m/accessories-finishing-edit.webp",
    "t/accessories-finishing-edit.jpg",
    "t/accessories-finishing-edit.webp",
    "brand-christopher-ward-moonphase.jpg",
    "brand-christopher-ward-moonphase.webp",
    "m/brand-christopher-ward-moonphase.jpg",
    "m/brand-christopher-ward-moonphase.webp",
    "t/brand-christopher-ward-moonphase.jpg",
    "t/brand-christopher-ward-moonphase.webp",
    "brand-chanel-premiere.jpg",
    "brand-chanel-premiere.webp",
    "m/brand-chanel-premiere.jpg",
    "m/brand-chanel-premiere.webp",
    "t/brand-chanel-premiere.jpg",
    "t/brand-chanel-premiere.webp",
    "brand-burberry-scarf.jpg",
    "brand-burberry-scarf.webp",
    "m/brand-burberry-scarf.jpg",
    "m/brand-burberry-scarf.webp",
    "t/brand-burberry-scarf.jpg",
    "t/brand-burberry-scarf.webp",
    "brand-prada-linea-rossa.jpg",
    "brand-prada-linea-rossa.webp",
    "m/brand-prada-linea-rossa.jpg",
    "m/brand-prada-linea-rossa.webp",
    "t/brand-prada-linea-rossa.jpg",
    "t/brand-prada-linea-rossa.webp",
    "brand-arcteryx-ridge.jpg",
    "brand-arcteryx-ridge.webp",
    "m/brand-arcteryx-ridge.jpg",
    "m/brand-arcteryx-ridge.webp",
    "t/brand-arcteryx-ridge.jpg",
    "t/brand-arcteryx-ridge.webp",
    "brand-chanel-como-bag.jpg",
    "brand-chanel-como-bag.webp",
    "m/brand-chanel-como-bag.jpg",
    "m/brand-chanel-como-bag.webp",
    "t/brand-chanel-como-bag.jpg",
    "t/brand-chanel-como-bag.webp",
    "brand-dior-bags.jpg",
    "brand-dior-bags.webp",
    "m/brand-dior-bags.jpg",
    "m/brand-dior-bags.webp",
    "t/brand-dior-bags.jpg",
    "t/brand-dior-bags.webp",
    "brand-dior-mens-rtw.jpg",
    "brand-dior-mens-rtw.webp",
    "m/brand-dior-mens-rtw.jpg",
    "m/brand-dior-mens-rtw.webp",
    "t/brand-dior-mens-rtw.jpg",
    "t/brand-dior-mens-rtw.webp",
    "brand-dior-womens-rtw.jpg",
    "brand-dior-womens-rtw.webp",
    "m/brand-dior-womens-rtw.jpg",
    "m/brand-dior-womens-rtw.webp",
    "t/brand-dior-womens-rtw.jpg",
    "t/brand-dior-womens-rtw.webp",
    "rot-hero-1.jpg",
    "rot-hero-2.jpg",
    "rot-hero-3.jpg",
    "rot-hero-4.jpg",
    "m/rot-hero-1.jpg",
    "m/rot-hero-2.jpg",
    "m/rot-hero-3.jpg",
    "m/rot-hero-4.jpg",
    "rot-luxury-1.jpg",
    "rot-event-1.jpg",
    "rot-cloth-1.jpg",
]


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "BriqBannerVerify/1.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--sample",
        type=int,
        default=0,
        help="Also spot-check N random banner JPGs under public/banners",
    )
    args = ap.parse_args()

    if MANIFEST.is_file():
        meta = json.loads(MANIFEST.read_text())
        print(f"manifest refreshedAt={meta.get('refreshedAt')}", flush=True)

    paths = list(KEY_SLOTS)
    if args.sample:
        extras = sorted(
            p.relative_to(BANNER_DIR).as_posix()
            for p in BANNER_DIR.rglob("*.jpg")
            if p.is_file()
        )
        for rel in extras:
            if rel not in paths:
                paths.append(rel)
            if len(paths) >= len(KEY_SLOTS) + args.sample:
                break

    bad: list[str] = []
    for rel in paths:
        local = BANNER_DIR / rel
        if not local.is_file():
            print(f"skip missing local {rel}", flush=True)
            continue
        lm = md5(local)
        # Production serves banners from raw GitHub — check it first.
        for label, base in (("github", RAW), ("jsdelivr", CDN)):
            url = f"{base}/{rel}"
            try:
                remote = fetch(url)
            except urllib.error.HTTPError as e:
                bad.append(f"{rel} {label} HTTP {e.code}")
                continue
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                bad.append(f"{rel} {label} fetch: {e}")
                continue
            rm = hashlib.md5(remote).hexdigest()
            if rm != lm:
                bad.append(f"{rel} {label} md5 {rm} != local {lm}")

    if bad:
        print("banner CDN verify FAILED:", flush=True)
        for line in bad[:40]:
            print(f"  {line}", flush=True)
        if len(bad) > 40:
            print(f"  … and {len(bad) - 40} more", flush=True)
        return 1

    print(f"banner CDN verify OK ({len(paths)} paths)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
