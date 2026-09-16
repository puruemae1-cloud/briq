#!/usr/bin/env python3
"""Retranslate Vivienne Westwood Korean PDP copy for shop categories.

Uses Bing Translator (gtx/MyMemory are often 429 under batch). Unique English
strings are translated once, then applied across matching products.

Usage:
  python3 scripts/retranslate-vw-ko.py --category accessories
  python3 scripts/retranslate-vw-ko.py --category luxury,shoes,bags
  python3 scripts/retranslate-vw-ko.py --category all
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Hard-cap hung HTTPS sockets (urllib CLOSE_WAIT stalls were freezing the batch).
socket.setdefaulttimeout(10)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ko_qa import en_ratio, has_hangul, is_good_korean  # noqa: E402
from vw_common import load_json, save_json  # noqa: E402

CATALOG = ROOT / "src/data/vw/vw-catalog.json"
CACHE = ROOT / "src/data/vw/vw-translate-cache.json"

_LOCAL_KO = {
    "100% Brass": "황동 100%",
    "100% Acetate": "아세테이트 100%",
    "100% Cotton": "코튼 100%",
    "100% Cotton jersey": "코튼 저지 100%",
    "100% Cow leather": "소가죽 100%",
    "100% Leather": "레더 100%",
    "100% Coated polyester": "코팅 폴리에스터 100%",
    "100% Recycled silver": "재활용 실버 100%",
    "100% Organic cotton": "오가닉 코튼 100%",
    "100% calf leather": "송아지 가죽 100%",
    "100% brass": "황동 100%",
    "100% zinc alloy": "아연 합금 100%",
    "Main material: brass": "주요 소재: 황동",
    "Main material: sterling silver": "주요 소재: 스털링 실버",
    "Main material: 100% brass": "주요 소재: 황동 100%",
    "Main material: 100% calf leather": "주요 소재: 송아지 가죽 100%",
    "Hardware: 100% zinc alloy": "하드웨어: 아연 합금 100%",
    "Pearls: glass-based pearls": "진주: 글래스 펄",
    "Pearls: Swarovski crystals": "진주: 스와로브스키 크리스탈",
    "Pearls: Swarovski": "진주: 스와로브스키",
    "glass-based pearls": "글래스 펄",
    "Glass-based pearls": "글래스 펄",
    "Swarovski crystals": "스와로브스키 크리스탈",
    "Swarovski": "스와로브스키",
    "Preciosa crystals": "프레시오사 크리스탈",
    "Silver-tone plating": "실버톤 도금",
    "Silver-toned plating": "실버톤 도금",
    "Silver-tone plated metal": "실버톤 도금 메탈",
    "Gold-tone plating": "골드톤 도금",
    "Rhodium plating": "로듐 도금",
    "Polished finish": "폴리시 마감",
    "Post-back closure": "포스트 백 클로저",
    "Please note that we do not accept returns on earrings.": "이어링은 반품이 불가합니다.",
    "Do not wash": "세탁 금지",
    "Do not bleach": "표백 금지",
    "Do not tumble dry": "텀블 건조 금지",
    "Cool iron": "약하게 다림질",
    "Dry clean on a gentle cycle, professional cleaning only": "전문가용 약사이클 드라이클리닝",
    "Professional dry clean, gentle cycle": "전문가용 약사이클 드라이클리닝",
}

_BING = {"ig": "", "token": "", "key": "", "fetched_at": 0.0}
_BING_LOCK = threading.Lock()
_CACHE_LOCK = threading.Lock()
_RATE_LOCK = threading.Lock()
_NEXT_REQ_AT = 0.0


def _rate_wait(min_gap: float = 0.8) -> None:
    """Serialize outbound translate calls enough to avoid 429 storms."""
    global _NEXT_REQ_AT
    with _RATE_LOCK:
        now = time.time()
        delay = _NEXT_REQ_AT - now
        if delay > 0:
            time.sleep(delay)
        _NEXT_REQ_AT = time.time() + min_gap


def needs_ko(text: str | None) -> bool:
    s = (text or "").strip()
    if not s:
        return False
    if is_good_korean(s):
        return False
    return en_ratio(s) >= 0.35 or not has_hangul(s)


def normalize_glued(text: str) -> str:
    """SFCC often concatenates care/material lines without spaces."""
    s = (text or "").strip()
    if not s:
        return ""
    s = re.sub(r"(?<=[a-z0-9%\.])(?=[A-Z])", " ", s)
    s = re.sub(
        r"(?<=[a-zA-Z])(?=(Do not|Please |By means|Our |Main material|Upper:|These |"
        r"Sterling |Avoid |Hardware:|Pearls:|Glass|Cubic|Silver|Gold|Rhodium|Laminated|"
        r"Organic|Platform:))",
        " ",
        s,
    )
    return re.sub(r"\s+", " ", s).strip()


def local_ko(text: str) -> str | None:
    s = normalize_glued(text)
    if not s:
        return ""
    if s in _LOCAL_KO:
        return _LOCAL_KO[s]
    out = s
    for en, ko in sorted(_LOCAL_KO.items(), key=lambda kv: -len(kv[0])):
        if en in out:
            out = out.replace(en, ko)
    if out != s and is_good_korean(out, max_ratio=0.50):
        return out
    return None


def _refresh_bing() -> None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    html = urllib.request.urlopen(
        urllib.request.Request("https://www.bing.com/translator", headers=headers),
        timeout=12,
    ).read().decode("utf-8", "replace")
    ig = re.search(r'IG:"([^"]+)"', html)
    tok = re.search(
        r'params_AbusePreventionHelper\s*=\s*\[(\d+),"([^"]+)",(\d+)\]', html
    )
    if not ig or not tok:
        raise RuntimeError("bing-token-missing")
    _BING["ig"] = ig.group(1)
    _BING["key"] = tok.group(1)
    _BING["token"] = tok.group(2)
    _BING["fetched_at"] = time.time()


def _gtx_once(chunk: str) -> str:
    _rate_wait(0.25)
    q = urllib.parse.quote(chunk[:4500])
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        return "".join(part[0] for part in data[0] if part and part[0])
    except urllib.error.HTTPError as e:
        if e.code == 429:
            time.sleep(2.5)
        raise


def _mymemory_once(chunk: str) -> str:
    _rate_wait(0.4)
    url = (
        "https://api.mymemory.translated.net/get"
        f"?q={urllib.parse.quote(chunk[:480])}&langpair=en|ko"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as r:
        data = json.loads(r.read().decode())
    return (data.get("responseData") or {}).get("translatedText") or ""


def _bing_chunk(chunk: str) -> str:
    _rate_wait(0.3)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.bing.com/translator",
        "Origin": "https://www.bing.com",
    }
    with _BING_LOCK:
        if time.time() - float(_BING["fetched_at"] or 0) > 240 or not _BING["token"]:
            _refresh_bing()
        ig, token, key = _BING["ig"], _BING["token"], _BING["key"]
    body = urllib.parse.urlencode(
        {"fromLang": "en", "to": "ko", "text": chunk, "token": token, "key": key}
    ).encode()
    url = f"https://www.bing.com/ttranslatev3?isVertical=1&&IG={ig}&IID=translator.5023"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=12) as r:
        data = json.loads(r.read().decode())
    return data[0]["translations"][0]["text"]


def translate_text(text: str) -> str:
    """EN→KO via glossary → gtx → Bing → MyMemory. Fail fast on hung sockets."""
    text = normalize_glued(text)
    if not text:
        return ""
    loc = local_ko(text)
    if loc is not None:
        return loc

    if len(text) <= 480:
        chunks = [text]
    else:
        parts = re.split(r"(?<=[.!?])\s+", text)
        chunks, buf = [], ""
        for part in parts:
            limit = 480
            if len(buf) + len(part) + 1 <= limit:
                buf = f"{buf} {part}".strip()
            else:
                if buf:
                    chunks.append(buf)
                buf = part
        if buf:
            chunks.append(buf)

    outs: list[str] = []
    for chunk in chunks:
        loc = local_ko(chunk)
        if loc is not None:
            outs.append(loc)
            continue
        out = ""
        last_err: Exception | None = None
        # Prefer Bing under batch load — gtx 429s quickly with parallel workers.
        for fn in (_bing_chunk, _gtx_once, _mymemory_once):
            for attempt in range(3):
                try:
                    cand = fn(chunk)
                    if cand and en_ratio(cand) < 0.55:
                        out = cand
                        break
                except Exception as e:
                    last_err = e
                    if fn is _bing_chunk:
                        with _BING_LOCK:
                            _BING["fetched_at"] = 0
                    code = getattr(e, "code", None)
                    if code == 429 or "429" in str(e):
                        time.sleep(8.0 * (attempt + 1))
                        continue
                    break
            if out:
                break
        if not out:
            raise RuntimeError(f"translate-failed: {last_err}")
        outs.append(out)
    return " ".join(outs)


# Back-compat alias used by older callers / tests.
bing_translate = translate_text


VW_SHOP_CATEGORIES = ("accessories", "bags", "luxury", "shoes", "watches")


def parse_categories(raw: str) -> list[str]:
    s = (raw or "").strip().lower()
    if not s or s == "all":
        return list(VW_SHOP_CATEGORIES)
    cats = [c.strip() for c in s.split(",") if c.strip()]
    unknown = [c for c in cats if c not in VW_SHOP_CATEGORIES]
    if unknown:
        raise SystemExit(
            f"unknown category {unknown!r}; expected one of {list(VW_SHOP_CATEGORIES)} or all"
        )
    return cats


def collect_strings(products: list[dict], categories: set[str] | str) -> set[str]:
    cats = {categories} if isinstance(categories, str) else set(categories)
    out: set[str] = set()
    for p in products:
        if p.get("category") not in cats:
            continue
        for val in (p.get("descriptionKo"),):
            if needs_ko(val):
                out.add(str(val).strip())
        for f in p.get("featuresKo") or []:
            if needs_ko(f):
                out.add(str(f).strip())
        for sec in p.get("storySections") or []:
            title = str(sec.get("titleKo") or "")
            if title == "스타일링":
                continue
            if needs_ko(sec.get("bodyKo")):
                out.add(str(sec.get("bodyKo")).strip())
        for spec in p.get("techSpecs") or []:
            if needs_ko(spec.get("valueKo")):
                out.add(str(spec.get("valueKo")).strip())
    return out


def apply_translations(p: dict, cache: dict[str, str]) -> bool:
    changed = False

    def swap(val: str | None) -> str:
        s = str(val or "").strip()
        if not needs_ko(s):
            return s
        cached = cache.get(s)
        if cached and is_good_korean(cached, max_ratio=0.50):
            return cached
        loc = local_ko(s)
        if loc is not None:
            return loc
        return cached or s

    desc = str(p.get("descriptionKo") or "")
    if needs_ko(desc):
        new_desc = swap(desc)
        if new_desc != desc and is_good_korean(new_desc, max_ratio=0.50):
            p["descriptionKo"] = new_desc
            desc = new_desc
            changed = True

    feats: list[str] = []
    feat_changed = False
    for f in p.get("featuresKo") or []:
        nf = swap(f)
        if nf != str(f or ""):
            feat_changed = True
        feats.append(nf)
    if feat_changed:
        p["featuresKo"] = feats
        changed = True

    sections = []
    sec_changed = False
    for sec in p.get("storySections") or []:
        s = dict(sec)
        title = str(s.get("titleKo") or "")
        body = str(s.get("bodyKo") or "")
        if title == "제품 소개" and is_good_korean(desc):
            if body != desc:
                s["bodyKo"] = desc
                sec_changed = True
        elif title == "디테일 & 특징" and feats:
            joined = " · ".join(feats[:8])
            if is_good_korean(joined) and body != joined:
                s["bodyKo"] = joined
                sec_changed = True
            elif needs_ko(body):
                s["bodyKo"] = swap(body)
                sec_changed = True
        elif needs_ko(body):
            s["bodyKo"] = swap(body)
            sec_changed = True
        sections.append(s)
    if sec_changed:
        p["storySections"] = sections
        changed = True

    specs = list(p.get("techSpecs") or [])
    spec_changed = False
    for spec in specs:
        val = str(spec.get("valueKo") or "")
        if needs_ko(val):
            nv = swap(val)
            if nv != val:
                spec["valueKo"] = nv
                spec_changed = True
    if spec_changed:
        p["techSpecs"] = specs
        changed = True

    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--category",
        default="accessories",
        help="One category, comma-separated list, or 'all'",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--priority-id", default="", help="Translate this product's strings first")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()

    categories = parse_categories(args.category)
    cat_set = set(categories)

    products = load_json(CATALOG, [])
    cache = load_json(CACHE, {})
    purged = 0
    for k, v in list(cache.items()):
        if isinstance(v, str) and len(v) >= 40 and not is_good_korean(v):
            del cache[k]
            purged += 1
    if purged:
        print(f"purged {purged} EN/hybrid cache entries", flush=True)

    for en, ko in _LOCAL_KO.items():
        cache.setdefault(en, ko)

    pending = [t for t in todo if not (t in cache and is_good_korean(cache[t], max_ratio=0.45))]
    # Short strings first — materials/care land quickly; long PDP bodies after.
    # Keep --priority-id strings at the front so a target PDP is fixed early.
    priority_set: set[str] = set()
    if args.priority_id:
        pri = next((p for p in products if p.get("id") == args.priority_id), None)
        if pri:
            priority_set = collect_strings([pri], cat_set)
    pending.sort(
        key=lambda s: (0 if s in priority_set else 1, len(s), s)
    )
    workers = max(1, min(args.workers, 8))
    print(
        f"categories={','.join(categories)} unique={len(todo)} "
        f"pending={len(pending)} workers={workers}",
        flush=True,
    )

    done = failed = 0
    completed = 0

    def work(text: str) -> tuple[str, str | None, str | None]:
        try:
            loc = local_ko(text)
            ko = loc if loc is not None else translate_text(text)
            if ko and is_good_korean(ko, max_ratio=0.50):
                return text, ko, None
            return text, None, f"BAD_KO ratio={en_ratio(ko or ''):.2f}"
        except Exception as e:
            return text, None, f"{type(e).__name__}: {e}"

    def flush_progress() -> None:
        nonlocal done, failed, completed
        if args.dry_run:
            return
        with _CACHE_LOCK:
            save_json(CACHE, cache)
        if completed % 100 == 0 or completed == len(pending):
            changed_mid = 0
            for p in products:
                if p.get("category") not in cat_set:
                    continue
                if apply_translations(p, cache):
                    changed_mid += 1
            save_json(CATALOG, products)
            print(f"  mid-apply products_changed={changed_mid}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(work, t) for t in pending]
        for fut in as_completed(futs):
            text, ko, err = fut.result()
            completed += 1
            if ko:
                with _CACHE_LOCK:
                    cache[text] = ko
                done += 1
            else:
                failed += 1
                print(f"  FAIL {err} :: {text[:70]}", flush=True)
            if completed % 25 == 0 or completed == len(pending):
                print(
                    f"  {completed}/{len(pending)} ok={done} fail={failed}",
                    flush=True,
                )
                flush_progress()

    if not args.dry_run:
        save_json(CACHE, cache)

    changed_n = still_bad = 0
    for p in products:
        if p.get("category") not in cat_set:
            continue
        if apply_translations(p, cache):
            changed_n += 1
        if needs_ko(p.get("descriptionKo")):
            still_bad += 1

    if not args.dry_run:
        save_json(CATALOG, products)

    print(
        f"done products_changed={changed_n} still_en_desc={still_bad} "
        f"ok={done} fail={failed}",
        flush=True,
    )
    return 1 if still_bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
