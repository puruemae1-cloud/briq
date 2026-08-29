#!/usr/bin/env python3
"""Shared Louis Vuitton (GB) scrape helpers."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG_ROOT = ROOT / "public/products/lv-pdp"

BASE = "https://uk.louisvuitton.com"
LANG = "eng-gb"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)


def gbp_to_krw(gbp: float | None) -> int:
    """Luxury accessories — match Prada/Chanel bag formula."""
    if gbp is None:
        return 0
    raw = float(gbp) * 2100 * 1.05 * 1.15
    return int(round(raw / 10_000) * 10_000)


def slugify(text: str, *, max_len: int = 72) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s[:max_len] or "item").strip("-")


def leaf_id_from_slug(slug: str) -> str:
    slug = slug.strip("/").lower()
    if slug in ("all-furniture-and-lighting", "all"):
        return "lv-furniture-lighting-all"
    return f"lv-{slug.replace('/', '-')}"


def fetch_curl(url: str, *, impersonate: str = "safari17_0", retries: int = 4) -> str:
    from curl_cffi import requests as creq

    headers = {
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept": "text/html,application/json,*/*",
        "Referer": f"{BASE}/{LANG}/homepage",
    }
    last_err: Exception | None = None
    for i in range(retries):
        try:
            r = creq.get(
                url,
                impersonate=impersonate,
                headers=headers,
                timeout=45,
            )
            if r.status_code == 403:
                raise RuntimeError(f"403 bot wall at {url}")
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_err = e
            time.sleep(2 + i * 2)
    raise RuntimeError(f"fetch failed {url}: {last_err}")


def extract_next_data(html: str) -> dict | None:
    m = re.search(
        r'<script[^>]+id="__NEXT_DATA__"[^>]*>([\s\S]*?)</script>',
        html,
        re.I,
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def discover_furniture_leaves(html: str) -> list[dict[str, str]]:
    """Parse hub HTML/JSON for furniture-and-lighting subcategory links."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    pattern = re.compile(
        rf"/{LANG}/home-lifestyle-and-library/furniture-and-lighting/"
        r"([a-z0-9-]+)/_/N-([a-z0-9]+)",
        re.I,
    )
    for slug, code in pattern.findall(html):
        if slug in seen:
            continue
        seen.add(slug)
        leaf = leaf_id_from_slug(slug)
        out.append(
            {
                "id": leaf,
                "slug": slug,
                "code": code,
                "url": (
                    f"{BASE}/{LANG}/home-lifestyle-and-library/"
                    f"furniture-and-lighting/{slug}/_/N-{code}"
                ),
            }
        )
    return out


def clean_image_url(raw: str, *, prefer_wid: int = 1800) -> str | None:
    """Normalize LV CDN / srcset blobs into a single absolute image URL."""
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None
    # HTML entities + whitespace noise
    s = (
        s.replace("&amp;", "&")
        .replace("&#38;", "&")
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("\t", " ")
    )
    # srcset: "url 490w, url 600w, …"
    candidates: list[tuple[int, str]] = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\S+)\s+(\d+)w\s*$", part)
        if m:
            candidates.append((int(m.group(2)), m.group(1)))
            continue
        m = re.match(r"^(\S+)\s+(\d+)x\s*$", part)
        if m:
            candidates.append((int(m.group(2)) * 1000, m.group(1)))
            continue
        # bare url fragment
        tok = part.split()[0] if part.split() else ""
        if tok:
            candidates.append((0, tok))
    if not candidates and s.startswith("http"):
        candidates = [(0, s.split()[0])]
    if not candidates:
        # relative path beginning with /images/
        m = re.search(r"(/images/is/image/lv/[^\s,\"']+)", s)
        if m:
            candidates = [(0, m.group(1))]
    if not candidates:
        return None

    # Prefer closest to prefer_wid (or largest if none match)
    def score(item: tuple[int, str]) -> tuple[int, int]:
        w, _ = item
        if w <= 0:
            return (1, 0)
        return (0, abs(w - prefer_wid))

    candidates.sort(key=score)
    # Among similar, take largest width
    best_w = max((w for w, _ in candidates if w > 0), default=0)
    if best_w:
        near = [u for w, u in candidates if w == best_w]
        url = near[0]
    else:
        url = candidates[0][1]

    url = url.strip().strip("\"'")
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = f"{BASE}{url}"
    if not url.startswith("http"):
        return None
    # Drop control chars / spaces
    if re.search(r"[\s]", url):
        url = url.split()[0]
    if re.search(r"[\x00-\x1f\x7f]", url):
        return None
    # Force a solid width when LV Scene7 params present
    if "/images/is/image/lv/" in url and "wid=" not in url:
        join = "&" if "?" in url else "?"
        url = f"{url}{join}wid={prefer_wid}"
    elif "wid=" in url:
        url = re.sub(r"wid=\d+", f"wid={prefer_wid}", url)
        url = re.sub(r"hei=\d+", f"hei={prefer_wid}", url)
    return url


def normalize_image_list(urls: list[str], *, limit: int = 40) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in urls:
        cleaned = clean_image_url(raw)
        if not cleaned:
            continue
        # Dedupe by asset stem (ignore wid)
        key = re.sub(r"[?&]wid=\d+", "", cleaned)
        key = re.sub(r"[?&]hei=\d+", "", key)
        if key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
        if len(out) >= limit:
            break
    return out


def download_image(url: str, dest: Path) -> bool:
    cleaned = clean_image_url(url)
    if not cleaned:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 2048:
        return True
    # urllib is 403'd by LV image CDN; curl_cffi Safari impersonation works.
    try:
        from curl_cffi import requests as creq

        r = creq.get(
            cleaned,
            impersonate="safari17_0",
            timeout=60,
            headers={
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*",
                "Referer": f"{BASE}/{LANG}/homepage",
            },
        )
        if r.status_code != 200 or len(r.content) < 512:
            return False
        ctype = (r.headers.get("content-type") or "").lower()
        if "html" in ctype:
            return False
        dest.write_bytes(r.content)
        return True
    except Exception:
        pass
    req = urllib.request.Request(
        cleaned,
        headers={"User-Agent": UA, "Accept": "image/*,*/*", "Referer": f"{BASE}/"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if len(data) < 512:
            return False
        dest.write_bytes(data)
        return True
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False
