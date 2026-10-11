#!/usr/bin/env python3
"""Scrape Galvin Green PDP copy (description / features / fabric / tech) and rebuild catalog.

Stores English source on each raw colourway under `pdpCopy`, then rebuilds
gg-catalog.ts with natural Korean via Google Translate (cached).
"""
from __future__ import annotations

import html as H
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "src/data/gg/gg-catalog-raw.json"
COPY_CACHE = ROOT / "src/data/gg/gg-pdp-copy.json"
TX_CACHE_PATH = ROOT / "src/data/gg/gg-translate-cache.json"

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-GB,en;q=0.9",
}


def strip_html(html: str) -> str:
    if not html:
        return ""
    s = H.unescape(html)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p>", "\n", s)
    s = re.sub(r"(?i)</li>", "\n", s)
    s = re.sub(r"(?i)<li[^>]*>", "- ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def fetch_html(handle: str) -> str | None:
    url = f"https://www.galvingreen.com/en-gb/products/{handle}"
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=35) as r:
            return r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"  warn fetch {handle}: {e}")
        return None


def section_plain(html: str, start_label: str, end_labels: list[str]) -> str:
    idx = html.find(start_label)
    if idx < 0:
        return ""
    end = len(html)
    for lab in end_labels:
        j = html.find(lab, idx + len(start_label))
        if j >= 0:
            end = min(end, j)
    return strip_html(html[idx:end])


def parse_field(label: str, text: str) -> str:
    m = re.search(
        rf"{re.escape(label)}\s*:?\s*(.+?)(?:\n|$)",
        text,
        flags=re.I,
    )
    if not m:
        return ""
    val = m.group(1).strip(" -")
    val = re.sub(r"\s{2,}", " ", val)
    return val


def parse_bullets_after(label: str, text: str) -> list[str]:
    """Extract bullet lines after a standalone LABEL: heading (not inside another title)."""
    m = re.search(rf"(?mi)^\s*{re.escape(label)}\s*:\s*", text)
    if not m:
        return []
    rest = text[m.end() :]
    bullets: list[str] = []
    for line in rest.split("\n"):
        line = line.strip()
        if not line:
            if bullets:
                continue
            continue
        cleaned = line
        while re.match(r"^[-•]\s*", cleaned):
            cleaned = re.sub(r"^[-•]\s*", "", cleaned).strip()
        if not cleaned:
            continue
        if re.match(
            r"^(FABRIC|TECHNOLOGY|CARE|FEATURES|FIT|ART|MODEL|DESCRIPTION)\b",
            cleaned,
            re.I,
        ):
            break
        if re.match(r"^[A-Z][A-Z0-9 .&/™®-]{3,}:?\s*$", cleaned) and bullets:
            break
        # Ignore leftover title fragments
        if cleaned.upper() in {"AND DETAILS", "AND TECHNOLOGY", "DETAILS"}:
            continue
        bullets.append(cleaned)
    return [b for b in bullets if b and len(b) > 1]


def clean_description(text: str) -> str:
    if not text:
        return ""
    # Strip injected SEO / analytics scripts that sometimes leak into accordion HTML
    text = re.split(
        r"\blet\s+shop\b|window\.fetch\s*\(|<script|api-brokenlinkmanager",
        text,
        maxsplit=1,
        flags=re.I,
    )[0]
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip(" \n\t-")


def parse_pdp(html: str, fallback_description: str = "") -> dict:
    desc_block = section_plain(
        html,
        "DESCRIPTION",
        ["FEATURES AND DETAILS", "Fabric and technology", "Care instructions"],
    )
    desc_block = re.sub(r"^DESCRIPTION\s*", "", desc_block, flags=re.I).strip()
    description = desc_block if len(desc_block) > 80 else (fallback_description or desc_block)
    description = clean_description(description)

    feat_block = section_plain(
        html,
        "FEATURES AND DETAILS",
        ["Fabric and technology", "Care instructions", "Technology Comparison", "Reviews"],
    )
    fabric_block = section_plain(
        html,
        "Fabric and technology",
        ["Care instructions", "Reviews", "You may also like"],
    )

    features = parse_bullets_after("FEATURES", feat_block)
    if not features:
        features = []
        for ln in feat_block.split("\n"):
            ln = ln.strip()
            cleaned = ln
            while re.match(r"^[-•]\s*", cleaned):
                cleaned = re.sub(r"^[-•]\s*", "", cleaned).strip()
            if cleaned and len(cleaned) > 2 and not cleaned.endswith(":"):
                if re.match(r"^(ART|FIT|MODEL|FABRIC|TECHNOLOGY)\b", cleaned, re.I):
                    continue
                if cleaned.upper() in {"FEATURES", "FEATURES AND DETAILS"}:
                    continue
                features.append(cleaned)

    fabric_lines = parse_bullets_after("FABRIC", fabric_block)
    if not fabric_lines:
        m = re.search(
            r"FABRIC\s*:\s*(.+?)(?:TECHNOLOGY\s*:|$)",
            fabric_block,
            re.I | re.S,
        )
        if m:
            chunk = m.group(1)
            fabric_lines = []
            for x in re.split(r"\n|•", chunk):
                x = re.sub(r"^[-•]\s*", "", x).strip(" -")
                if x:
                    fabric_lines.append(x)

    technology = parse_field("TECHNOLOGY", fabric_block)
    if not technology:
        m = re.search(r"TECHNOLOGY\s*:\s*([^\n]+)", fabric_block, re.I)
        if m:
            technology = m.group(1).strip(" -")

    art_no = parse_field("ART. NO", feat_block) or parse_field("ART NO", feat_block)
    fit = parse_field("FIT", feat_block)
    model_info = parse_field("MODEL INFO", feat_block)

    fabric_lines = [f for f in fabric_lines if f and f not in {"-", "–"}][:8]
    features = [f for f in features if f and f not in {"-", "–"}][:16]
    # Drop accidental heading leftovers
    features = [
        f
        for f in features
        if f.upper() not in {"FEATURES", "FEATURES AND DETAILS"}
        and not f.upper().startswith("ART")
    ]

    return {
        "descriptionEn": description.strip(),
        "featuresEn": features,
        "fabricEn": fabric_lines,
        "technologyEn": technology,
        "artNo": art_no,
        "fitEn": fit,
        "modelInfoEn": model_info,
    }


def enrich(force_refresh: bool = False) -> dict:
    if not RAW_PATH.exists():
        raise SystemExit(f"Missing {RAW_PATH}")

    raw = json.loads(RAW_PATH.read_text())
    products: list[dict] = raw.get("products") or []
    copy_cache: dict[str, dict] = (
        {} if force_refresh
        else (json.loads(COPY_CACHE.read_text()) if COPY_CACHE.exists() else {})
    )

    # One PDP scrape per style title (+ gender via collection)
    by_style: dict[str, list[dict]] = {}
    for p in products:
        title = (p.get("title") or "").strip()
        if not title:
            continue
        by_style.setdefault(title, []).append(p)

    fetched = 0
    reused = 0
    failed = 0

    for title, members in sorted(by_style.items()):
        cache_key = title
        existing = copy_cache.get(cache_key) or {}
        needs_fetch = (
            force_refresh
            or not existing.get("descriptionEn")
            or "let shop" in (existing.get("descriptionEn") or "")
            or "window.fetch" in (existing.get("descriptionEn") or "")
            or (
                not existing.get("featuresEn")
                and not existing.get("fabricEn")
            )
        )
        if not needs_fetch:
            copy = existing
            # Still clean description if polluted
            copy["descriptionEn"] = clean_description(copy.get("descriptionEn") or "")
            reused += 1
        else:
            # Prefer in-stock / richest body handle
            primary = sorted(
                members,
                key=lambda m: (
                    0 if any(v.get("available") for v in m.get("variants") or []) else 1,
                    -(len(m.get("body_html") or "")),
                    m.get("handle") or "",
                ),
            )[0]
            handle = primary["handle"]
            print(f"PDP {handle} …")
            html = None
            for attempt in range(4):
                html = fetch_html(handle)
                if html:
                    break
                wait = 2.5 * (attempt + 1)
                print(f"  retry in {wait:.1f}s …")
                time.sleep(wait)
            time.sleep(0.35)
            if not html:
                failed += 1
                copy = {
                    "descriptionEn": strip_html(primary.get("body_html") or ""),
                    "featuresEn": [],
                    "fabricEn": [],
                    "technologyEn": "",
                    "artNo": "",
                    "fitEn": "",
                    "modelInfoEn": "",
                    "handle": handle,
                }
            else:
                copy = parse_pdp(html, strip_html(primary.get("body_html") or ""))
                copy["handle"] = handle
                fetched += 1
                print(
                    f"  desc={len(copy['descriptionEn'])} "
                    f"feats={len(copy['featuresEn'])} "
                    f"fabric={len(copy['fabricEn'])} tech={copy['technologyEn']!r}"
                )
            copy_cache[cache_key] = copy

        for m in members:
            m["pdpCopy"] = copy

    COPY_CACHE.parent.mkdir(parents=True, exist_ok=True)
    COPY_CACHE.write_text(
        json.dumps(copy_cache, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    raw["scrapedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw["products"] = products
    RAW_PATH.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Rebuilding gg-catalog.ts with Korean copy …")
    subprocess.check_call(
        [sys.executable, str(ROOT / "scripts/build-gg-catalog.py")],
        cwd=str(ROOT),
    )

    return {
        "styles": len(by_style),
        "fetched": fetched,
        "reused": reused,
        "failed": failed,
    }


if __name__ == "__main__":
    force = "--refresh" in sys.argv
    if force and COPY_CACHE.exists():
        COPY_CACHE.unlink()
        print("Cleared PDP copy cache")
    stats = enrich(force_refresh=force)
    print(
        f"Done. styles={stats['styles']} fetched={stats['fetched']} "
        f"reused={stats['reused']} failed={stats['failed']}"
    )
