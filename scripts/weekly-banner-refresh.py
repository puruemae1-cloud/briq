#!/usr/bin/env python3
"""Weekly refresh of Briq homepage / category banners with luxury on-model photos.

Sources official product galleries already on the `product-images` CDN
(Gucci / Burberry / Chanel / Arc'teryx …) — models wearing the brands we sell.
Writes PC + tablet + mobile crops (see banner_smart_crop.py), then callers push
the `product-images` tag so Vercel serves them via jsDelivr.

  python3 scripts/weekly-banner-refresh.py
  python3 scripts/weekly-banner-refresh.py --limit 8
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from banner_smart_crop import export_banner_set  # noqa: E402

BANNER_DIR = ROOT / "public" / "banners"
MOBILE_DIR = BANNER_DIR / "m"
TABLET_DIR = BANNER_DIR / "t"
MANIFEST = ROOT / "src/data/banner-refresh-manifest.json"
MEDIA = "https://cdn.jsdelivr.net/gh/puruemae1-cloud/briq@product-images/public"

UA = (
    "Mozilla/5.0 (compatible; BriqBannerBot/1.0; +https://briq.kr)"
)

# Slot filename → theme buckets used to pick catalog on-model frames.
SLOT_THEMES: dict[str, list[str]] = {
    "rot-hero-1.jpg": ["luxury", "fashion"],
    "rot-hero-2.jpg": ["luxury", "fashion"],
    "rot-hero-3.jpg": ["fashion", "street"],
    "rot-hero-4.jpg": ["luxury", "bags"],
    "rot-event-1.jpg": ["fashion", "luxury"],
    "rot-event-2.jpg": ["street", "fashion"],
    "rot-event-3.jpg": ["luxury", "fashion"],
    "rot-luxury-1.jpg": ["luxury"],
    "rot-luxury-2.jpg": ["luxury"],
    "rot-luxury-3.jpg": ["luxury"],
    "rot-cloth-1.jpg": ["fashion"],
    "rot-cloth-2.jpg": ["fashion"],
    "rot-cloth-3.jpg": ["fashion"],
    "rot-bag-1.jpg": ["bags"],
    "rot-bag-2.jpg": ["bags"],
    "rot-bag-3.jpg": ["bags"],
    "rot-shoe-1.jpg": ["shoes"],
    "rot-shoe-2.jpg": ["shoes"],
    "rot-shoe-3.jpg": ["shoes"],
    "rot-acc-1.jpg": ["accessories"],
    "rot-acc-2.jpg": ["accessories"],
    "rot-acc-3.jpg": ["accessories"],
    "rot-watch-1.jpg": ["watches"],
    "rot-watch-2.jpg": ["watches"],
    "rot-watch-3.jpg": ["watches"],
    "rot-cw-1.jpg": ["watches"],
    "rot-cw-2.jpg": ["watches"],
    "rot-cw-3.jpg": ["watches"],
    "rot-cw-alt.jpg": ["watches"],
    "rot-golf-1.jpg": ["golf"],
    "rot-golf-2.jpg": ["golf"],
    "rot-golf-3.jpg": ["golf"],
    "rot-cycle-1.jpg": ["outdoor"],
    "rot-cycle-2.jpg": ["outdoor"],
    "rot-cycle-3.jpg": ["outdoor"],
    "rot-swim-1.jpg": ["outdoor"],
    "rot-swim-2.jpg": ["outdoor"],
    "rot-swim-3.jpg": ["outdoor"],
    "rot-run-1.jpg": ["outdoor"],
    "rot-run-2.jpg": ["outdoor"],
    "rot-run-3.jpg": ["outdoor"],
    "rot-tennis-1.jpg": ["outdoor"],
    "rot-tennis-2.jpg": ["outdoor"],
    "rot-tennis-3.jpg": ["outdoor"],
    "shop-lux-w-1.jpg": ["luxury"],
    "shop-lux-w-2.jpg": ["luxury"],
    "shop-lux-m-1.jpg": ["luxury"],
    "shop-lux-m-2.jpg": ["luxury"],
    "shop-cloth-1.jpg": ["fashion"],
    "shop-cloth-w-1.jpg": ["fashion"],
    "shop-cloth-m-1.jpg": ["fashion"],
    "shop-bag-1.jpg": ["bags"],
    "shop-shoe-lux-w-1.jpg": ["shoes"],
    "shop-shoe-lux-m-1.jpg": ["shoes"],
    "shop-shoe-train-w-1.jpg": ["outdoor"],
    "shop-shoe-train-m-1.jpg": ["outdoor"],
    "shop-golf-1.jpg": ["golf"],
    "shop-run-1.jpg": ["outdoor"],
}

SHOP_SLOTS = {n for n in SLOT_THEMES if n.startswith("shop-")}


def week_seed(now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    return int(now.strftime("%G%V"))  # ISO year+week


def load_catalog(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return [p for p in data if isinstance(p, dict)]
    if isinstance(data, dict) and isinstance(data.get("products"), list):
        return [p for p in data["products"] if isinstance(p, dict)]
    return []


def product_images(product: dict) -> list[str]:
    """Prefer hover / secondary gallery frames (often on-model)."""
    out: list[str] = []
    seen: set[str] = set()
    for key in ("hoverImage", "image"):
        src = product.get(key)
        if isinstance(src, str) and src.startswith("/products/") and src not in seen:
            seen.add(src)
            out.append(src)
    for src in product.get("images") or []:
        if isinstance(src, str) and src.startswith("/products/") and src not in seen:
            seen.add(src)
            out.append(src)
    # On-model is rarely the first packshot — prefer [1:] when available
    if len(out) >= 2:
        return out[1:] + out[:1]
    return out


def theme_match(product: dict, themes: list[str]) -> bool:
    blob = " ".join(
        [
            str(product.get("category") or ""),
            str(product.get("subcategory") or ""),
            " ".join(product.get("tags") or []),
            " ".join(product.get("chCollections") or []),
            " ".join(product.get("bbCollections") or []),
            " ".join(product.get("gcCollections") or []),
            " ".join(product.get("axCollections") or []),
            str(product.get("brand") or ""),
            str(product.get("nameKo") or ""),
        ]
    ).lower()
    checks = {
        "luxury": any(
            x in blob
            for x in ("gucci", "버버리", "burberry", "chanel", "샤넬", "luxury", "gc-", "bb-", "ch-")
        ),
        "fashion": any(
            x in blob
            for x in (
                "rtw",
                "clothing",
                "ready-to-wear",
                "의류",
                "jacket",
                "coat",
                "dress",
                "sweater",
                "shirt",
                "hoodie",
                "arc'teryx",
                "arcteryx",
                "axa-",
            )
        ),
        "street": any(x in blob for x in ("street", "hoodie", "tee", "sneaker", "trainer")),
        "bags": any(x in blob for x in ("bag", "handbag", "가방", "tote", "backpack", "wallet")),
        "shoes": any(x in blob for x in ("shoe", "sneaker", "boot", "loafer", "heel", "슈즈", "footwear")),
        "accessories": any(
            x in blob
            for x in ("accessor", "jewellery", "jewelry", "sunglass", "scarf", "belt", "악세서", "주얼")
        ),
        "watches": any(x in blob for x in ("watch", "시계", "christopher ward", "cw-")),
        "golf": any(x in blob for x in ("golf", "골프", "galvin")),
        "outdoor": any(
            x in blob for x in ("arc'teryx", "arcteryx", "outdoor", "running", "hike", "axa-", "ax-")
        ),
    }
    return any(checks.get(t, False) for t in themes)


def is_likely_on_model(path: str) -> bool:
    """Heuristic: gallery/hover frames and non-packshot filenames."""
    name = path.lower()
    if any(x in name for x in ("/1.jpg", "/thumb.jpg", "packshot", "still-life")):
        # still allow if it's a hover path elsewhere
        if "hover" in name:
            return True
        return False
    return True


def collect_candidates() -> dict[str, list[tuple[str, str]]]:
    """theme → list of (product_id, image_path)."""
    catalogs = [
        ROOT / "src/data/gc/gc-catalog.json",
        ROOT / "src/data/bb/bb-catalog.json",
        ROOT / "src/data/ch/ch-catalog.json",
        ROOT / "src/data/ax/ax-apparel-catalog.json",
        ROOT / "src/data/gg/gg-catalog.json",
    ]
    by_theme: dict[str, list[tuple[str, str]]] = {t: [] for t in {
        "luxury", "fashion", "street", "bags", "shoes", "accessories",
        "watches", "golf", "outdoor",
    }}
    for path in catalogs:
        for product in load_catalog(path):
            pid = str(product.get("id") or "")
            imgs = [i for i in product_images(product) if is_likely_on_model(i)]
            if not imgs:
                imgs = product_images(product)[:2]
            if not imgs:
                continue
            for theme in list(by_theme):
                if theme_match(product, [theme]):
                    for img in imgs[:3]:
                        by_theme[theme].append((pid, img))
    for theme, rows in by_theme.items():
        # stable unique by image path
        seen: set[str] = set()
        uniq = []
        for pid, img in rows:
            if img in seen:
                continue
            seen.add(img)
            uniq.append((pid, img))
        by_theme[theme] = uniq
        print(f"candidates {theme}={len(uniq)}", flush=True)
    return by_theme


def fetch_image(rel: str) -> Image.Image | None:
    urls = [
        f"{MEDIA}{rel}",
        f"https://raw.githubusercontent.com/puruemae1-cloud/briq/product-images/public{rel}",
    ]
    local = ROOT / "public" / rel.lstrip("/")
    if local.is_file() and local.stat().st_size > 2000:
        try:
            return Image.open(local).convert("RGB")
        except Exception:
            pass
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/*"})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read()
            if len(data) < 2000:
                continue
            from io import BytesIO

            return Image.open(BytesIO(data)).convert("RGB")
        except Exception:
            continue
    return None


def pick_for_slot(
    slot: str,
    themes: list[str],
    pool: dict[str, list[tuple[str, str]]],
    rng: random.Random,
    used: set[str],
    seed: int,
) -> tuple[str, str] | None:
    options: list[tuple[str, str]] = []
    for t in themes:
        options.extend(pool.get(t) or [])
    options = [o for o in options if o[1] not in used]
    if not options:
        # fallback any luxury/fashion
        for t in ("luxury", "fashion", "outdoor"):
            options.extend(pool.get(t) or [])
        options = [o for o in options if o[1] not in used]
    if not options:
        return None
    # Deterministic weekly shuffle per slot
    digest = hashlib.sha1(f"{seed}:{slot}".encode()).hexdigest()
    slot_rng = random.Random(digest)
    slot_rng.shuffle(options)
    return options[0]


def referenced_slots() -> list[str]:
    text = ""
    for rel in (
        "src/data/home-banners.ts",
        "src/data/shop-heroes.ts",
        "src/app/shop/page.tsx",
        "src/components/Collection100.tsx",
    ):
        p = ROOT / rel
        if p.is_file():
            text += p.read_text()
    names = sorted(set(re.findall(r"/banners/(?!m/|t/)([A-Za-z0-9._-]+\.jpg)", text)))
    return names


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="Only refresh N slots (debug)")
    ap.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Override week seed (force a new shuffle mid-week)",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    seed = args.seed or week_seed()
    rng = random.Random(seed)
    print(f"week_seed={seed}", flush=True)

    slots = [s for s in referenced_slots() if s in SLOT_THEMES]
    # Also refresh any SLOT_THEMES not referenced? stick to referenced
    if args.limit:
        slots = slots[: args.limit]
    print(f"slots={len(slots)}", flush=True)

    pool = collect_candidates()
    used: set[str] = set()
    manifest = {
        "refreshedAt": datetime.now(timezone.utc).isoformat(),
        "weekSeed": seed,
        "slots": {},
    }

    BANNER_DIR.mkdir(parents=True, exist_ok=True)
    MOBILE_DIR.mkdir(parents=True, exist_ok=True)
    TABLET_DIR.mkdir(parents=True, exist_ok=True)

    ok = fail = 0
    for i, slot in enumerate(slots, start=1):
        themes = SLOT_THEMES.get(slot) or ["luxury"]
        pick = pick_for_slot(slot, themes, pool, rng, used, seed)
        if not pick:
            print(f"{i}/{len(slots)} {slot} FAIL no-candidate", flush=True)
            fail += 1
            continue
        pid, img = pick
        used.add(img)
        source = fetch_image(img)
        if source is None:
            print(f"{i}/{len(slots)} {slot} FAIL fetch {img}", flush=True)
            fail += 1
            continue
        if args.dry_run:
            print(f"{i}/{len(slots)} {slot} <- {pid} {img} ({source.size})", flush=True)
            ok += 1
            continue
        shop = slot in SHOP_SLOTS
        try:
            focal = export_banner_set(
                source,
                desktop_path=BANNER_DIR / slot,
                tablet_path=TABLET_DIR / slot,
                mobile_path=MOBILE_DIR / slot,
                shop=shop,
            )
        except Exception as e:
            print(f"{i}/{len(slots)} {slot} FAIL crop {e}", flush=True)
            fail += 1
            continue
        manifest["slots"][slot] = {
            "sourceProductId": pid,
            "sourceImage": img,
            "focal": focal.css,
            "shop": shop,
        }
        ok += 1
        if i <= 12 or i % 10 == 0 or i == len(slots):
            print(
                f"{i}/{len(slots)} {slot} ok focal={focal.css} src={img}",
                flush=True,
            )
        time.sleep(0.02)

    if not args.dry_run:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        print(f"wrote {MANIFEST}", flush=True)

    print(f"done ok={ok} fail={fail}", flush=True)
    return 0 if ok > 0 and fail < ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
