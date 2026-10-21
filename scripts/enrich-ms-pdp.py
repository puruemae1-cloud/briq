#!/usr/bin/env python3
"""Fill Mismo PDPs with the official size, material and story blocks.

Reads each mismo.dk product page, keeps the existing Korean description, and
adds size, composition and illustrated material sections.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "src/data/ms/ms-catalog.json"
CACHE = ROOT / "src/data/ms/ms-translate-cache.json"
SPECS = ROOT / "src/data/ms/ms-specs.json"
STORY_DIR = ROOT / "public/products/ms-story"

LABELS = {
    "Length": "길이",
    "Height": "높이",
    "Width": "너비",
    "Depth": "깊이",
    "Volume": "용량",
    "Weight": "제품 무게",
    "Strap length": "스트랩 길이",
    "Strap": "스트랩",
    "Handle drop": "핸들 드롭",
    "Shoulder strap": "숄더 스트랩",
    "Belt length": "벨트 길이",
    "Drop": "드롭",
}

FIBERS = {
    "PA": "나일론",
    "NY": "나일론",
    "CO": "코튼",
    "WO": "울",
    "LI": "리넨",
    "EA": "엘라스테인",
    "PL": "폴리에스터",
    "PES": "폴리에스터",
    "CV": "비스코스",
    "PU": "폴리우레탄",
    "SE": "실크",
    "RA": "라미",
    "PC": "아크릴",
    "WA": "앙고라",
}

MODELS = [
    ("Book Case, Large", "북 케이스 라지"),
    ("Book Case, Medium", "북 케이스 미디엄"),
    ("Large Book Case", "라지 북 케이스"),
    ("Medium Book Case", "미디엄 북 케이스"),
    ("Watch Case", "워치 케이스"),
    ("Jewel Case", "주얼 케이스"),
    ("M/S Pouch Large", "M/S 파우치 라지"),
    ("M/S Belt Bag", "M/S 벨트백"),
    ("M/S Mega Tote", "M/S 메가 토트"),
    ("M/S Suit Carrier", "M/S 수트 캐리어"),
    ("M/S Luggage Tag", "M/S 러기지 택"),
    ("M/S Cardholder", "M/S 카드홀더"),
    ("M/S Carpet Bag", "M/S 카펫 백"),
    ("M/S Drop Bag", "M/S 드롭백"),
    ("M/S Helmet Bag", "M/S 헬멧 백"),
    ("M/S Washbag", "M/S 워시백"),
    ("M/S Backpack", "M/S 백팩"),
    ("M/S Aspire", "M/S 아스파이어"),
    ("M/S Avail", "M/S 어베일"),
    ("M/S Brief", "M/S 브리프"),
    ("M/S Capsule", "M/S 캡슐"),
    ("M/S Carry", "M/S 캐리"),
    ("M/S Companion", "M/S 컴패니언"),
    ("M/S Drawstring", "M/S 드로우스트링"),
    ("M/S Endeavour", "M/S 엔데버"),
    ("M/S Escape", "M/S 이스케이프"),
    ("M/S Explorer", "M/S 익스플로러"),
    ("M/S Groom", "M/S 그룸"),
    ("M/S Haven", "M/S 헤이븐"),
    ("M/S Mate", "M/S 메이트"),
    ("M/S Office", "M/S 오피스"),
    ("M/S Passage", "M/S 파사지"),
    ("M/S Pouch", "M/S 파우치"),
    ("M/S Prime", "M/S 프라임"),
    ("M/S Rucksack", "M/S 럭색"),
    ("M/S Satchel", "M/S 사첼"),
    ("M/S Shopper", "M/S 쇼퍼"),
    ("M/S Storage", "M/S 스토리지"),
    ("M/S Supply", "M/S 서플라이"),
    ("M/S Tour", "M/S 투어"),
    ("M/S Transit", "M/S 트랜짓"),
    ("M/S Utility", "M/S 유틸리티"),
    ("M/S Vigour", "M/S 비거"),
    ("M/S Well", "M/S 웰"),
    ("Classic Belt", "클래식 벨트"),
    ("Shoulder Strap", "숄더 스트랩"),
    ("Belt Bag", "벨트백"),
    ("Into the Deep", "인투 더 딥"),
    ("A Lovely Land", "어 러블리 랜드"),
    ("Army Canvas", "아미 캔버스"),
    ("Grand Herringbone", "그랜드 헤링본"),
    ("Ocean Jacquard", "오션 자카드"),
    ("Palm Jacquard", "팜 자카드"),
]


def plain(fragment: str) -> str:
    text = re.sub(r"(?i)<br\s*/?>", "\n", fragment or "")
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\xa0", " ").replace("&amp;", "&")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch(url: str) -> str:
    last = ""
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=40) as res:
                return res.read().decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
            time.sleep(0.8 * (attempt + 1))
    raise RuntimeError(last)


def gtx(text: str, cache: dict[str, str]) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return ""
    if text in cache and cache[text]:
        return polish(cache[text])
    q = urllib.parse.quote(text[:4500])
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl=ko&dt=t&q={q}"
    )
    last = ""
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as res:
                data = json.loads(res.read().decode())
            out = "".join(part[0] for part in data[0] if part and part[0]).strip()
            if out:
                cache[text] = out
                time.sleep(0.12)
                return polish(out)
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
            time.sleep(1.2 * (attempt + 1))
    raise SystemExit(f"translate failed: {last[:100]} :: {text[:60]}")


def polish(text: str) -> str:
    for src, dst in MODELS:
        text = text.replace(src, dst)
    text = text.replace("Mismo", "미스모").replace("MISMO", "미스모")
    text = text.replace("잡동사니", "홀드올").replace("전보", "케이블")
    text = text.replace("굴레 가죽", "브라이들 가죽").replace("타박", "타바코")
    text = text.replace("육군 캔버스", "아미 캔버스").replace("육군 캔버스", "아미 캔버스")
    text = text.replace("Martindale", "마틴데일").replace("Excella", "엑셀라")
    text = text.replace("깊은 곳으로", "인투 더 딥")
    text = text.replace("사랑스러운 땅", "어 러블리 랜드")
    text = text.replace("반 식물성 무두질", "세미 베지터블 태닝")
    text = re.sub(r"\bw\.\s*", "· ", text)
    text = re.sub(r"(\d{1,3})\.(\d{3})\b", r"\1,\2", text)
    text = text.replace("미스모(미스모)", "미스모")
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def translated(text: str, cache: dict[str, str]) -> str:
    key = re.sub(r"\s+", " ", (text or "").strip())
    value = cache.get(key) or cache.get(text) or text
    return polish(value)


def image_url(raw: str) -> str:
    raw = raw.replace("{width}", "1600")
    if raw.startswith("//"):
        raw = "https:" + raw
    return raw.split(" ")[0]


def story_filename(url: str) -> str:
    name = urllib.parse.urlparse(url).path.rsplit("/", 1)[-1]
    name = re.sub(r"_\d+x(?=\.)", "", name)
    name = name.replace("_small", "")
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)
    return name or "story.jpg"


def parse_page(html: str) -> dict:
    dims = []
    for match in re.finditer(
        r'class="dimensions-table--item">\s*<span>([^<]+)</span>\s*<span([^>]*)>(.*?)</span>',
        html,
        re.S,
    ):
        cm = re.search(r'data-dimension-cm="([0-9.]+)"', match.group(2))
        dims.append(
            {
                "label": match.group(1).strip(),
                "cm": cm.group(1) if cm else "",
                "text": plain(match.group(3)),
            }
        )
    materials: list[str] = []
    features: list[str] = []
    for block in html.split('<div class="product-top--details-specs"')[1:]:
        title = re.search(r"small-title[^>]*>([^<]+)", block)
        if not title:
            continue
        name = title.group(1).strip()
        spans = [
            plain(s)
            for s in re.findall(r"<span>([^<]{2,160})</span>", block[:2500])
            if plain(s)
        ]
        if name == "Material":
            materials = spans
        elif name == "Features":
            features = spans
    stories = []
    chunks = html.split('<div class="product-specs--tab swiper-slide">')[1:]
    for chunk in chunks:
        head = re.search(r'product-specs--tab-heading">([^<]*)</p>(.*)', chunk, re.S)
        img = re.search(r'data-src="([^"]+)"', chunk) or re.search(
            r'src="(//www\.mismo[^"]+)"', chunk
        )
        image = image_url(img.group(1)) if img else ""
        if not head:
            continue
        rest = head.group(2)
        metas = [plain(x) for x in re.findall(r'<p class="small-title[^"]*">(.*?)</p>', rest, re.S)]
        body_html = re.split(r'<p class="small-title', rest, maxsplit=1)[0]
        body = plain(body_html)
        # Drop the in-page menu slide that only repeats section names.
        if body.count("Dimensions") and "Main Material" in body:
            body = body.split("Dimensions")[0].strip()
        if len(body) < 40 and not metas:
            continue
        stories.append(
            {
                "heading": head.group(1).strip(),
                "body": body,
                "metas": [m for m in metas if m and m.lower() != "dimensions"],
                "image": image,
            }
        )
    return {"dims": dims, "materials": materials, "features": features, "stories": stories}


def fmt_cm(raw: str) -> str:
    number = float(raw)
    shown = str(int(number)) if number == int(number) else f"{number:g}"
    return f"{shown}cm"


def composition_ko(line: str) -> str:
    text = re.sub(r"(?i)^composition:\s*", "", line).strip()
    parts = re.split(r"\s*[-/]\s*", text)
    out = []
    for part in parts:
        match = re.match(r"([A-Z]{2})\s*([0-9]+)\s*%", part.strip())
        if not match:
            continue
        fiber = FIBERS.get(match.group(1), match.group(1))
        out.append(f"{fiber} {match.group(2)}%")
    return " · ".join(out)


def meta_bits(metas: list[str]) -> dict[str, str]:
    found: dict[str, str] = {}
    for meta in metas:
        comp = composition_ko(meta)
        if comp:
            found["composition"] = comp
            continue
        mart = re.search(
            r"Martindale:\s*([0-9.]+)(?:\s*/\s*Weight:\s*([0-9.]+)\s*gr\.?(.*))?",
            meta,
            re.I,
        )
        if mart:
            found["martindale"] = mart.group(1).replace(".", ",") if "." in mart.group(1) and len(mart.group(1).split(".")[-1]) == 3 else mart.group(1)
            if "." in found["martindale"] and re.fullmatch(r"\d+\.\d{3}", mart.group(1)):
                found["martindale"] = mart.group(1).replace(".", ",")
            if mart.group(2):
                found["fabricWeight"] = mart.group(2)
            continue
        surface = re.sub(r"(?i)^surface treatment:\s*", "", meta).strip()
        if surface and surface != meta:
            found["surface"] = surface
            continue
        if meta.lower().startswith("surface"):
            found["surface"] = re.sub(r"(?i)^surface treatment:\s*", "", meta).strip()
    return found


def download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 2000:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as res:
        dest.write_bytes(res.read())


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    specs: dict[str, dict] = {}
    if SPECS.exists():
        specs = json.loads(SPECS.read_text(encoding="utf-8"))

    missing = [p for p in catalog if p["id"] not in specs]
    print(f"fetch {len(missing)} pages", flush=True)

    def load(product: dict) -> tuple[str, dict]:
        try:
            return product["id"], parse_page(fetch(product["sourceUrl"]))
        except Exception as exc:  # noqa: BLE001
            print("page fail", product["id"], exc, flush=True)
            return product["id"], {"dims": [], "materials": [], "features": [], "stories": []}

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(load, p) for p in missing]
        done = 0
        for future in as_completed(futures):
            pid, parsed = future.result()
            specs[pid] = parsed
            done += 1
            if done % 40 == 0:
                SPECS.write_text(json.dumps(specs, ensure_ascii=False), encoding="utf-8")
                print(f"  pages {done}/{len(missing)}", flush=True)
    SPECS.write_text(json.dumps(specs, ensure_ascii=False), encoding="utf-8")
    story_n = sum(len(s["stories"]) for s in specs.values())
    print(f"stories {story_n}", flush=True)

    texts: list[str] = []
    for spec in specs.values():
        texts.extend(spec["materials"])
        texts.extend(spec["features"])
        for story in spec["stories"]:
            texts.append(story["heading"])
            if story["body"]:
                texts.append(story["body"])
            for meta in story["metas"]:
                if meta_bits([meta]).get("surface"):
                    texts.append(meta_bits([meta])["surface"])
    unique = []
    seen = set()
    for text in texts:
        key = re.sub(r"\s+", " ", (text or "").strip())
        if key and key not in cache and key not in seen:
            seen.add(key)
            unique.append(key)
    print(f"translate {len(unique)}", flush=True)
    for index, text in enumerate(unique, 1):
        gtx(text, cache)
        if index % 20 == 0:
            CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  translated {index}/{len(unique)}", flush=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

    jobs: dict[str, str] = {}
    for spec in specs.values():
        for story in spec["stories"]:
            if story["image"]:
                jobs[story_filename(story["image"])] = story["image"]
    print(f"images {len(jobs)}", flush=True)
    failed = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(download, url, STORY_DIR / name): name for name, url in jobs.items()
        }
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print("image fail", futures[future], exc)
    print("image fails", failed, flush=True)

    for product in catalog:
        spec = specs[product["id"]]
        size_lines = []
        spec_rows = []
        belt = product.get("subcategory") == "ms-belts"
        variant_sizes = [v.get("size") for v in product.get("variants") or [] if v.get("size")]
        if belt and variant_sizes:
            size_lines.append("길이 " + " · ".join(variant_sizes))
            spec_rows.append({"labelKo": "길이", "valueKo": " · ".join(variant_sizes)})
        for dim in spec["dims"]:
            label = LABELS.get(dim["label"], dim["label"])
            if dim["cm"]:
                value = fmt_cm(dim["cm"])
                if belt and dim["label"] == "Width" and float(dim["cm"]) >= 10:
                    wide = next((f for f in spec["features"] if re.search(r"\d+\s*cm wide", f, re.I)), "")
                    mm = re.search(r"(\d+)\s*mm", " ".join(spec["features"]))
                    if wide:
                        value = re.search(r"(\d+(?:\.\d+)?)\s*cm", wide, re.I).group(0).replace(" ", "")
                    elif mm:
                        value = f"{mm.group(1)}mm"
            else:
                value = re.sub(r"(\d+)\s*l\b", r"\1L", dim["text"], flags=re.I)
            if belt and dim["label"] == "Width" and variant_sizes:
                pass
            if not value or (belt and variant_sizes and dim["label"] == "Length"):
                continue
            if any(row["labelKo"] == label and row["valueKo"] == value for row in spec_rows):
                continue
            size_lines.append(f"{label} {value}")
            spec_rows.append({"labelKo": label, "valueKo": value})

        material_lines = [translated(line, cache) for line in spec["materials"]]
        feature_lines = [translated(line, cache) for line in spec["features"]]
        comp_lines = []
        surface_lines = []
        martindale = ""
        fabric_weight = ""
        stories = []
        for story in spec["stories"]:
            heading = translated(story["heading"], cache)
            body = translated(story["body"], cache) if story["body"] else ""
            bits = meta_bits(story["metas"])
            extra = []
            if bits.get("composition"):
                comp = f"{heading}: {bits['composition']}" if heading else bits["composition"]
                if comp not in comp_lines:
                    comp_lines.append(comp)
                extra.append(f"원재료 {bits['composition']}")
            if bits.get("martindale"):
                martindale = bits["martindale"]
                extra.append(f"마틴데일 {martindale}")
            if bits.get("fabricWeight"):
                fabric_weight = bits["fabricWeight"]
                extra.append(f"원단 무게 미터당 {fabric_weight}g")
            if bits.get("surface"):
                surface = translated(bits["surface"], cache)
                if surface not in surface_lines:
                    surface_lines.append(surface)
                extra.append(surface)
            copy = body
            if extra:
                copy = (copy + "\n\n" if copy else "") + "\n".join(extra)
            image = ""
            if story["image"]:
                filename = story_filename(story["image"])
                path = STORY_DIR / filename
                if path.exists() and path.stat().st_size > 2000:
                    image = f"/products/ms-story/{filename}"
            if not copy:
                continue
            stories.append(
                {
                    "titleKo": heading or "소재",
                    "bodyKo": copy,
                    "image": image,
                    "imageAlt": heading or product["nameKo"],
                    "reverse": len(stories) % 2 == 1,
                }
            )

        if size_lines:
            gallery = product.get("images") or []
            shot = gallery[1] if len(gallery) > 1 else (gallery[0] if gallery else "")
            stories.insert(
                0,
                {
                    "titleKo": "사이즈",
                    "bodyKo": "\n".join(f"· {line}" for line in size_lines),
                    "image": shot,
                    "imageAlt": product["nameKo"],
                    "reverse": False,
                },
            )
            for index, story in enumerate(stories[1:], 1):
                story["reverse"] = index % 2 == 1

        base = re.split(r"\n\n사이즈\n", product.get("descriptionKo") or "")[0].strip()
        blocks = [base] if base else []
        if size_lines:
            blocks.append("사이즈\n" + "\n".join(f"· {line}" for line in size_lines))
        if material_lines:
            blocks.append("소재\n" + "\n".join(f"· {line}" for line in material_lines))
        if comp_lines:
            blocks.append("원재료\n" + "\n".join(f"· {line}" for line in comp_lines))
        product["descriptionKo"] = "\n\n".join(blocks)
        product["featuresKo"] = feature_lines or material_lines
        color = next((row for row in product.get("techSpecs") or [] if row.get("labelKo") == "컬러"), None)
        weight = next((row for row in product.get("techSpecs") or [] if row.get("labelKo") == "무게"), None)
        if material_lines:
            spec_rows.append({"labelKo": "소재", "valueKo": " · ".join(material_lines)})
        if comp_lines:
            spec_rows.append({"labelKo": "원재료", "valueKo": " · ".join(comp_lines)})
        if martindale:
            spec_rows.append({"labelKo": "내마모도", "valueKo": f"마틴데일 {martindale}"})
        if fabric_weight:
            spec_rows.append({"labelKo": "원단 무게", "valueKo": f"미터당 {fabric_weight}g"})
        if surface_lines:
            spec_rows.append({"labelKo": "표면 처리", "valueKo": " · ".join(surface_lines)})
        if color:
            spec_rows.append(color)
        if weight and not any(row["labelKo"] == "제품 무게" for row in spec_rows):
            spec_rows.append(weight)
        product["techSpecs"] = spec_rows
        product["storySections"] = [{k: v for k, v in story.items() if v} for story in stories]

    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=1), encoding="utf-8")
    with_story = sum(1 for p in catalog if p.get("storySections"))
    with_size = sum(1 for p in catalog if "사이즈" in (p.get("descriptionKo") or ""))
    print(f"wrote stories {with_story} sized {with_size}")


if __name__ == "__main__":
    main()
