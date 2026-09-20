#!/usr/bin/env python3
"""Retranslate Bottega Veneta Korean PDP copy (name + body).

Uses Bing Translator first (gtx 429s under batch). Unique English strings are
translated once, then applied across matching products.

Usage:
  python3 scripts/retranslate-bv-ko.py
  python3 scripts/retranslate-bv-ko.py --priority-id bv-609182v4kf18803
  python3 scripts/retranslate-bv-ko.py --limit 200
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

socket.setdefaulttimeout(10)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ko_qa import en_ratio, has_hangul, is_good_korean  # noqa: E402

CATALOG = ROOT / "src/data/bv/bv-catalog.json"
CACHE = ROOT / "src/data/bv/bv-translate-cache.json"

# High-frequency BV / maison glossary — keeps Intrecciato etc. consistent.
_LOCAL_KO = {
    "Intrecciato Belt": "인트레치아토 벨트",
    "Intrecciato leather belt": "인트레치아토 가죽 벨트",
    "Intrecciato calfskin leather belt": "인트레치아토 카프스킨 가죽 벨트",
    "Intrecciato calfskin leather belt.": "인트레치아토 카프스킨 가죽 벨트.",
    "Intrecciato leather belt.": "인트레치아토 가죽 벨트.",
    "Make it unique with a handmade customization by our artisans.": "장인들의 핸드메이드 커스터마이징으로 나만의 제품으로 완성해 보세요.",
    "Buckle closure": "버클 잠금",
    "Lining: Calfskin": "안감: 카프스킨",
    "Colour: Black": "색상: 블랙",
    "Colour: Space": "색상: 스페이스",
    "Colour: Fondant": "색상: 퐁당",
    "Colour: Nero": "색상: 네로",
    "• Material: 100% calfskin": "소재: 카프스킨 100%",
    "Material: 100% calfskin": "소재: 카프스킨 100%",
    "100% calfskin": "카프스킨 100%",
    "Hardware: Black finish": "하드웨어: 블랙 마감",
    "Intrecciato": "인트레치아토",
    "Intreccio": "인트레치오",
    "Andiamo": "안디아모",
    "Cassette": "카세트",
    "Jodie": "조디",
    "Puddle": "퍼들",
    "Tire": "타이어",
    "Stretch": "스트레치",
    "Calfskin": "카프스킨",
    "calfskin": "카프스킨",
    "Nappa": "나파",
    "Suede": "스웨이드",
    "Black": "블랙",
    "Belt": "벨트",
    "Wallet": "지갑",
    "Card Case": "카드 케이스",
    "Crossbody Bag": "크로스바디 백",
    "Tote Bag": "토트백",
    "Shoulder Bag": "숄더백",
    "Mini Bag": "미니 백",
    "Backpack": "백팩",
    "Sneakers": "스니커즈",
    "Loafers": "로퍼",
    "Sandals": "샌들",
    "Boots": "부츠",
    "Jacket": "재킷",
    "Coat": "코트",
    "Trousers": "트라우저",
    "Shirt": "셔츠",
    "T-shirt": "티셔츠",
    "Knitwear": "니트웨어",
    "Sunglasses": "선글라스",
    "Earrings": "이어링",
    "Necklace": "네크리스",
    "Bracelet": "브레이슬릿",
    "Ring": "링",
    "Clutch": "클러치",
    "Pouch": "파우치",
    "Keyring": "키링",
    "Card Holder": "카드 홀더",
    "Coin Purse": "코인 퍼스",
    "Bifold Wallet": "바이폴드 월렛",
    "Zip Wallet": "지퍼 월렛",
    "Document Case": "도큐먼트 케이스",
    "Briefcase": "브리프케이스",
    "Slippers": "슬리퍼",
    "Mules": "뮬",
    "Derby": "더비",
    "Oxford": "옥스포드",
    "Pump": "펌프스",
    "Ballerina": "발레리나",
    "Espadrille": "에스파드리유",
    "Hoodie": "후디",
    "Sweatshirt": "스웻셔츠",
    "Polo": "폴로",
    "Dress": "드레스",
    "Skirt": "스커트",
    "Shorts": "쇼츠",
    "Jeans": "진",
    "Denim": "데님",
    "Leather": "레더",
    "Wool": "울",
    "Cashmere": "캐시미어",
    "Cotton": "코튼",
    "Silk": "실크",
    "Linen": "린넨",
    "Polyester": "폴리에스터",
    "Nylon": "나일론",
    "Metal": "메탈",
    "Gold": "골드",
    "Silver": "실버",
    "White": "화이트",
    "Navy": "네이비",
    "Brown": "브라운",
    "Beige": "베이지",
    "Green": "그린",
    "Red": "레드",
    "Pink": "핑크",
    "Grey": "그레이",
    "Gray": "그레이",
    "Orange": "오렌지",
    "Yellow": "옐로우",
    "Purple": "퍼플",
    "Multicolor": "멀티컬러",
    "Printed": "프린트",
    "Embroidered": "자수",
    "Quilted": "퀼팅",
    "Magnetic closure": "마그네틱 잠금",
    "Zip closure": "지퍼 잠금",
    "Drawstring closure": "드로우스트링 잠금",
    "Adjustable strap": "조절 가능한 스트랩",
    "Detachable strap": "탈착식 스트랩",
    "Made in Italy": "이탈리아 제작",
    "The 70": "더 70",
    "70": "70",
}

_BING = {"ig": "", "token": "", "key": "", "fetched_at": 0.0}
_BING_LOCK = threading.Lock()
_CACHE_LOCK = threading.Lock()
_RATE_LOCK = threading.Lock()
_NEXT_REQ_AT = 0.0


def load_json(path: Path, default):
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _rate_wait(min_gap: float = 1.6) -> None:
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
    # Size-chart / region codes — leave as-is.
    if s in {"BV", "UK", "US", "KR", "EU", "IT", "FR", "OS", "TU"}:
        return False
    # Eyewear / style codes like "BV1012S 007", "BV1401SA 004"
    if re.fullmatch(r"BV\d{3,5}[A-Z]{0,3}\s*\d{0,4}", s, flags=re.I):
        return False
    # Measurements / hardware dims — keep Latin units
    if re.search(r"\d+[\.,]\d+\s*[x×]\s*\d+", s) and len(s) < 80:
        return False
    if re.fullmatch(r"[•\-–]?\s*[A-Za-z \-]+:\s*[\d\.,x×/ \-mmcmd]+", s):
        return False
    # Short model tokens without lowercase words
    if len(s) <= 18 and re.fullmatch(r"[A-Z0-9][A-Z0-9\-/ ]{0,16}", s) and not re.search(r"[a-z]{3,}", s):
        return False
    if is_good_korean(s, max_ratio=0.35) and has_hangul(s):
        return False
    return en_ratio(s) >= 0.35 or not has_hangul(s)


def local_ko(text: str) -> str | None:
    s = (text or "").strip()
    if not s:
        return ""
    if s in _LOCAL_KO:
        return _LOCAL_KO[s]
    out = s
    for en, ko in sorted(_LOCAL_KO.items(), key=lambda kv: -len(kv[0])):
        if en in out:
            out = out.replace(en, ko)
    if out != s and is_good_korean(out, max_ratio=0.55):
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
    html = (
        urllib.request.urlopen(
            urllib.request.Request("https://www.bing.com/translator", headers=headers),
            timeout=12,
        )
        .read()
        .decode("utf-8", "replace")
    )
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
    with urllib.request.urlopen(req, timeout=8) as r:
        data = json.loads(r.read().decode())
    return "".join(part[0] for part in data[0] if part and part[0])


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
    text = re.sub(r"\s+", " ", (text or "").strip())
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
            if len(buf) + len(part) + 1 <= 480:
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
                    if getattr(e, "code", None) == 429 or "429" in str(e):
                        time.sleep(20.0 * (attempt + 1))
                        continue
                    break
            if out:
                break
        if not out:
            raise RuntimeError(f"translate-failed: {last_err}")
        outs.append(out)
    return " ".join(outs)


def collect_strings(products: list[dict]) -> set[str]:
    out: set[str] = set()
    for p in products:
        for val in (p.get("nameKo"), p.get("descriptionKo")):
            if needs_ko(val):
                out.add(str(val).strip())
        for f in p.get("featuresKo") or []:
            if needs_ko(f):
                out.add(str(f).strip())
        for sec in p.get("storySections") or []:
            if needs_ko(sec.get("bodyKo")):
                out.add(str(sec.get("bodyKo")).strip())
        for spec in p.get("techSpecs") or []:
            if str(spec.get("labelKo") or "") == "제품 코드":
                continue
            if needs_ko(spec.get("valueKo")):
                out.add(str(spec.get("valueKo")).strip())
        chart = p.get("sizeChart") or {}
        if isinstance(chart, dict):
            for key in ("titleKo", "noteKo"):
                if needs_ko(chart.get(key)):
                    out.add(str(chart.get(key)).strip())
            for h in chart.get("headers") or []:
                if needs_ko(h):
                    out.add(str(h).strip())
    return out


def apply_translations(p: dict, cache: dict[str, str]) -> bool:
    changed = False

    def swap(val: str | None) -> str:
        s = str(val or "").strip()
        if not needs_ko(s):
            return s
        cached = cache.get(s)
        if cached and is_good_korean(cached, max_ratio=0.55):
            return cached
        loc = local_ko(s)
        if loc is not None:
            return loc
        return cached or s

    name = str(p.get("nameKo") or "")
    if needs_ko(name):
        # Prefer translating official EN title when nameKo is still English.
        src = str(p.get("name") or name).strip() or name
        new_name = swap(name) if name in cache or local_ko(name) else swap(src)
        if needs_ko(new_name) and src != name:
            new_name = swap(src)
        if new_name != name and (has_hangul(new_name) or is_good_korean(new_name, max_ratio=0.55)):
            p["nameKo"] = new_name
            changed = True

    desc = str(p.get("descriptionKo") or "")
    if needs_ko(desc):
        new_desc = swap(desc)
        if new_desc != desc and is_good_korean(new_desc, max_ratio=0.55):
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
        if title == "제품 소개" and is_good_korean(desc, max_ratio=0.55) and has_hangul(desc):
            # Keep intro story in sync with translated description lead.
            lead = desc.split("\n")[0].strip()
            if lead and body != lead and not needs_ko(lead):
                s["bodyKo"] = lead
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
        if str(spec.get("labelKo") or "") == "제품 코드":
            continue
        val = str(spec.get("valueKo") or "")
        if needs_ko(val):
            nv = swap(val)
            if nv != val:
                spec["valueKo"] = nv
                spec_changed = True
    if spec_changed:
        p["techSpecs"] = specs
        changed = True

    chart = p.get("sizeChart")
    if isinstance(chart, dict):
        chart_changed = False
        for key in ("titleKo", "noteKo"):
            val = str(chart.get(key) or "")
            if needs_ko(val):
                nv = swap(val)
                if nv != val:
                    chart[key] = nv
                    chart_changed = True
        headers = list(chart.get("headers") or [])
        new_headers = []
        for h in headers:
            if str(h) in {"BV", "UK", "US", "KR", "EU", "IT", "FR"}:
                new_headers.append(h)
            elif needs_ko(str(h)):
                new_headers.append(swap(str(h)))
                chart_changed = True
            else:
                new_headers.append(h)
        if chart_changed:
            chart["headers"] = new_headers
            p["sizeChart"] = chart
            changed = True

    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--priority-id", default="", help="Translate this product first")
    ap.add_argument("--limit", type=int, default=0, help="Max unique strings to translate")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--max-chars", type=int, default=0, help="Only translate strings up to this length")
    args = ap.parse_args()

    products = load_json(CATALOG, [])
    if not isinstance(products, list):
        print("ERROR bad catalog", flush=True)
        return 1
    cache = load_json(CACHE, {})
    if not isinstance(cache, dict):
        cache = {}

    purged = 0
    for k, v in list(cache.items()):
        if isinstance(v, str) and len(v) >= 24 and not is_good_korean(v, max_ratio=0.55):
            del cache[k]
            purged += 1
    if purged:
        print(f"purged {purged} EN/hybrid cache entries", flush=True)

    for en, ko in _LOCAL_KO.items():
        cache[en] = ko

    todo = collect_strings(products)
    pending = [
        t
        for t in todo
        if not (t in cache and is_good_korean(cache[t], max_ratio=0.55))
    ]
    priority_set: set[str] = set()
    if args.priority_id:
        pri = next((p for p in products if p.get("id") == args.priority_id), None)
        if pri:
            priority_set = collect_strings([pri])
            # Also queue official EN title
            if needs_ko(str(pri.get("name") or "")):
                priority_set.add(str(pri.get("name")).strip())
    pending.sort(key=lambda s: (0 if s in priority_set else 1, len(s), s))
    if args.max_chars and args.max_chars > 0:
        pending = [s for s in pending if len(s) <= args.max_chars]
    if args.limit and args.limit > 0:
        pending = pending[: args.limit]

    workers = max(1, min(args.workers, 6))
    print(
        f"unique={len(todo)} pending={len(pending)} workers={workers} "
        f"priority={args.priority_id or '-'}",
        flush=True,
    )
    if args.dry_run:
        for s in pending[:30]:
            print(" ", s[:100], flush=True)
        return 0

    done = failed = completed = 0

    def work(text: str) -> tuple[str, str | None, str | None]:
        try:
            loc = local_ko(text)
            ko = loc if loc is not None else translate_text(text)
            if ko and is_good_korean(ko, max_ratio=0.55):
                return text, ko, None
            return text, None, f"BAD_KO ratio={en_ratio(ko or ''):.2f}"
        except Exception as e:
            return text, None, f"{type(e).__name__}: {e}"

    def flush_progress() -> None:
        with _CACHE_LOCK:
            save_json(CACHE, cache)
        changed_mid = sum(1 for p in products if apply_translations(p, cache))
        save_json(CATALOG, products)
        print(f"  mid-apply products_changed={changed_mid}", flush=True)

    # Apply glossary-only first so priority PDP is fixed immediately.
    for p in products:
        apply_translations(p, cache)
    save_json(CATALOG, products)
    save_json(CACHE, cache)
    if args.priority_id:
        pri = next((p for p in products if p.get("id") == args.priority_id), None)
        if pri:
            print(
                f"priority now nameKo={pri.get('nameKo')!r} "
                f"desc={str(pri.get('descriptionKo') or '')[:80]!r}",
                flush=True,
            )

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
                print(f"  FAIL {err} :: {text[:80]}", flush=True)
            if completed % 40 == 0 or completed == len(pending):
                print(
                    f"  {completed}/{len(pending)} ok={done} fail={failed}",
                    flush=True,
                )
                flush_progress()

    save_json(CACHE, cache)
    changed_n = sum(1 for p in products if apply_translations(p, cache))
    save_json(CATALOG, products)

    still_bad_name = sum(
        1
        for p in products
        if needs_ko(str(p.get("nameKo") or ""))
    )
    still_bad_desc = sum(
        1
        for p in products
        if needs_ko(str(p.get("descriptionKo") or ""))
    )
    print(
        f"done ok={done} fail={failed} products_touched≈{changed_n} "
        f"still_bad_name={still_bad_name} still_bad_desc={still_bad_desc}",
        flush=True,
    )
    return 1 if failed and still_bad_desc > len(products) * 0.2 else 0


if __name__ == "__main__":
    raise SystemExit(main())
