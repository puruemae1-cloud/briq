#!/usr/bin/env python3
"""Shared Chanel Hybris PDP parsers (characteristics, editorial, images).

Used by enrich-ch-details.py and optionally scrapers. Prefer chanel.cn /gb/
HTML (GBP + SSR characteristics) when www.chanel.com is Akamai-blocked.
"""
from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

SKIP_CHAR_LABELS = {
    "details of the piece",
    "care instructions",
    "user manuals",
    "all the details",
    "characteristics of each piece may vary**",
    "characteristics of each piece may vary*",
    "front view dimensions",
    "side view dimensions",
}


def to_cn_url(url: str) -> str:
    return (url or "").replace("://www.chanel.com/", "://www.chanel.cn/")


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def parse_editorial(html: str) -> str:
    """Marketing paragraphs under Features / key-feature blocks."""
    soup = BeautifulSoup(html or "", "html.parser")
    chunks: list[str] = []
    seen: set[str] = set()

    roots = soup.select(
        ".key-feature-content, .features-component__desc, .desc_block"
    )
    if not roots:
        roots = soup.select(".desc_wrapper.active_desc, .desc_wrapper")

    for root in roots:
        # Prefer individual wrappers to keep paragraph breaks.
        wrappers = root.select(".desc_wrapper") or [root]
        for w in wrappers:
            parts: list[str] = []
            for p in w.find_all(["p", "h2", "h3", "h4"], recursive=True):
                t = _clean(p.get_text(" ", strip=True))
                if len(t) < 40:
                    continue
                low = t.lower()
                if any(
                    x in low
                    for x in (
                        "cookie",
                        "privacy policy",
                        "subscribe",
                        "newsletter",
                        "virtual try-on",
                        "click & collect",
                        "delivery charge",
                    )
                ):
                    continue
                parts.append(t)
            if not parts:
                t = _clean(w.get_text("\n", strip=True))
                if len(t) >= 60:
                    parts = [t]
            for t in parts:
                key = t[:120].lower()
                if key in seen:
                    continue
                seen.add(key)
                chunks.append(t)

    return "\n\n".join(chunks)


def parse_characteristics(html: str) -> list[dict[str, str]]:
    """Label/value pairs from Details of the piece / eyewear dims."""
    soup = BeautifulSoup(html or "", "html.parser")
    out: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(label: str, value: str) -> None:
        label, value = _clean(label), _clean(value)
        if not label or not value:
            return
        if label.lower() in SKIP_CHAR_LABELS:
            return
        if value.lower() in SKIP_CHAR_LABELS:
            return
        # Skip legal footnotes used as values
        if value.startswith("Characteristics of each"):
            return
        key = f"{label.lower()}::{value.lower()}"
        if key in seen:
            return
        seen.add(key)
        out.append({"label": label, "value": value})

    # Watches: structured listings
    watch_root = soup.select_one("#characteristic-watches")
    if watch_root:
        for block in watch_root.select(".characteristic-listing"):
            texts = [_clean(t) for t in block.stripped_strings if _clean(t)]
            if len(texts) >= 2:
                add(texts[0], " · ".join(texts[1:]))

    # Fine / High jewellery + eyewear outer tiles
    for root in soup.select(
        "#product-characteristics, .characteristics__outer"
    ):
        # Jewelry tiles: heading + following text in .tiles
        for tile in root.select(".tiles"):
            heading = tile.select_one(".heading, h3, h4, .is-7")
            if heading:
                label = _clean(heading.get_text(" ", strip=True))
                # value = remaining text in tile
                texts = [_clean(t) for t in tile.stripped_strings if _clean(t)]
                vals = [t for t in texts if t != label and t.lower() not in SKIP_CHAR_LABELS]
                if label and vals:
                    add(label, " · ".join(vals))
                    continue
        # Eyewear dims: consecutive label/value lines
        lines = [_clean(t) for t in root.stripped_strings if _clean(t)]
        i = 0
        while i < len(lines):
            lab = lines[i]
            if lab.lower() in SKIP_CHAR_LABELS:
                i += 1
                continue
            # UV protection line often has no separate label
            if i + 1 < len(lines) and (
                lines[i + 1].endswith("mm")
                or re.match(r"^\d", lines[i + 1])
                or len(lines[i + 1]) < 80
            ):
                # Avoid pairing Diamonds with legal line
                if lines[i + 1].lower() in SKIP_CHAR_LABELS:
                    i += 1
                    continue
                add(lab, lines[i + 1])
                i += 2
                continue
            # UV protection / Made in Italy as standalone features
            if len(lab) > 24 and (
                "uva" in lab.lower()
                or "made in" in lab.lower()
                or "polarized" in lab.lower()
                or "protection" in lab.lower()
            ):
                add("Feature", lab)
                i += 1
                continue
            if i + 1 < len(lines) and (
                lines[i + 1].endswith("mm")
                or re.match(r"^\d", lines[i + 1])
                or (len(lines[i + 1]) < 80 and len(lab) < 40)
            ):
                # Avoid pairing Diamonds with legal line
                if lines[i + 1].lower() in SKIP_CHAR_LABELS:
                    i += 1
                    continue
                # Don't pair a long feature line with "Made in Italy"
                if len(lab) > 40 and "made in" in lines[i + 1].lower():
                    add("Feature", lab)
                    add("Feature", lines[i + 1])
                    i += 2
                    continue
                add(lab, lines[i + 1])
                i += 2
                continue
            i += 1

    return out


def extract_image_urls(html: str, sku: str, limit: int = 24) -> list[str]:
    """All unique packshot/editorial images for this SKU (CDN filenames)."""
    sku_l = (sku or "").lower()
    if not sku_l:
        return []
    files: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(
        r"https://www\.chanel\.(?:com|cn)/images/[^\"\s'>]+", html or ""
    ):
        u = (
            m.group(0)
            .rstrip("\\")
            .split("?")[0]
            .replace("www.chanel.cn", "www.chanel.com")
        )
        if not re.search(r"\.(?:jpg|jpeg|png|webp)$", u, re.I):
            continue
        fn = u.rsplit("/", 1)[-1]
        fl = fn.lower()
        # Filenames often embed a truncated code: ...-packshot-default-a40888x09955l4395-8853.jpg
        tok_m = re.search(
            r"-(a\d+x[a-z0-9]+|j\d+|h\d+|g\d+|ap\d+|ab[a-z0-9]+)-\d+\.", fl
        )
        token = tok_m.group(1) if tok_m else ""
        ok = False
        if sku_l in fl:
            ok = True
        elif token and (sku_l.startswith(token) or token.startswith(sku_l)):
            ok = True
        if not ok:
            continue
        if fl in seen:
            continue
        seen.add(fl)
        files.append(fn)

    def rank(fn: str) -> tuple[int, str]:
        f = fn.lower()
        if "packshot-default" in f:
            return (0, f)
        if "packshot-artistique-vue1" in f or "packshot-face" in f:
            return (1, f)
        if "packshot-artistique-vue2" in f:
            return (2, f)
        if "packshot-alternative" in f or "packshot-profil" in f:
            return (3, f)
        if "packshot-other" in f or "packshot-dos" in f:
            return (4, f)
        if "packshot-extra" in f or "packshot-motif" in f or "fermoir" in f:
            return (5, f)
        if "packshot-transformable" in f:
            return (6, f)
        if "portee" in f or "worn" in f:
            return (7, f)
        return (8, f)

    files.sort(key=rank)
    return [
        "https://www.chanel.com/images/t_one/q_auto:good,f_auto,fl_lossy,dpr_1.1/"
        f"w_1240/{fn}"
        for fn in files[:limit]
    ]


def enrich_from_html(html: str, sku: str, details: dict | None = None) -> dict[str, Any]:
    """Return detail/image enrichment fields from Hybris HTML."""
    details = dict(details or {})
    editorial = parse_editorial(html)
    chars = parse_characteristics(html)
    images = extract_image_urls(html, sku)

    if editorial:
        details["editorial"] = editorial
        # Prefer editorial as primary description when LD desc is a material one-liner.
        old = (details.get("description") or "").strip()
        if not old or len(old) < 80 or old.lower() == (details.get("color") or "").lower():
            details["description"] = editorial
        elif editorial not in old:
            details["description"] = f"{old}\n\n{editorial}" if old else editorial

    if chars:
        details["characteristics"] = chars

    return {"details": details, "images": images, "editorial": editorial, "characteristics": chars}
