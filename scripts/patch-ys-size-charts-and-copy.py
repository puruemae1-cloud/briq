#!/usr/bin/env python3
"""Patch YS catalogues: size charts matching PDP options + Korean PDP copy.

- Denim inch-waist (24–36) → official YSL/GB denim chart (not FR/IT RTW)
- Women F34… / Men 42… → gender-correct RTW charts
- Shoes → gender-correct YSL/GB shoe charts
- Retranslate hybrid EN/KO descriptionKo + story/features from raw English

Safe to re-run; used by weekly YS sync.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ys_size_charts import parse_ys_size_token, size_chart_for_rtw  # noqa: E402
from ysl_common import load_json, save_json  # noqa: E402

CATALOG = ROOT / "src/data/ys/ys-catalog.json"
CACHE = ROOT / "src/data/ys/ys-translate-cache.json"

EN_HINT = re.compile(
    r"\b(the|with|and|made|featuring|cotton|leather|jeans|button|"
    r"high-waisted|waistband|closure|pocket|denim|wash|iron)\b",
    re.I,
)

_SHOES_LEAF_HINTS = (
    "shoes",
    "pumps",
    "boots",
    "sandals",
    "ballerina",
    "mules",
    "sneakers",
    "loafers",
)


def _load_build_ys():
    spec = importlib.util.spec_from_file_location(
        "build_ys_catalog", ROOT / "scripts" / "build-ys-catalog.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


_BYS = _load_build_ys()
translate = _BYS.translate
build_story = _BYS.build_story


def _load_all_raw() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted((ROOT / "src/data/ys").glob("*-catalog-raw.json")):
        data = load_json(path, {})
        for row in data.get("products") or []:
            pid = str(row.get("id") or "")
            if not pid:
                continue
            key = pid.upper()
            prev = out.get(key)
            if prev and (prev.get("description") or prev.get("sizes")) and not (
                row.get("description") or row.get("sizes")
            ):
                cols = list(
                    dict.fromkeys(
                        [*(prev.get("collections") or []), *(row.get("collections") or [])]
                    )
                )
                prev["collections"] = cols
                if row.get("leafId") and not prev.get("leafId"):
                    prev["leafId"] = row["leafId"]
                continue
            out[key] = row
    return out


def _is_mens(p: dict, raw: dict | None) -> bool:
    cols = [str(c) for c in (p.get("ysCollections") or [])]
    if raw:
        cols = list(
            dict.fromkeys([*cols, *[str(c) for c in (raw.get("collections") or [])]])
        )
    sub = str(p.get("subcategory") or "")
    # Women wins if tagged — prevents denim/RTW getting men jacket charts.
    if any(c == "ys-women" or c.startswith("ys-women-") for c in cols) or sub.startswith(
        "ys-women"
    ):
        return False
    if any(c == "ys-men" or c.startswith("ys-men-") for c in cols) or sub.startswith(
        "ys-men"
    ):
        return True
    return False


def _leaf_hint(p: dict, raw: dict | None) -> str:
    if raw and raw.get("leafId"):
        return str(raw["leafId"])
    for c in reversed(p.get("ysCollections") or []):
        cs = str(c)
        if cs.startswith("ys-") and cs not in {"ys-men", "ys-women", "saint-laurent"}:
            return cs
    return str(p.get("subcategory") or "")


def _sizes_from_raw(raw: dict | None) -> list[dict]:
    if not raw:
        return []
    return list(raw.get("sizes") or [])


def _sizes_from_variants(variants: list[dict]) -> list[dict]:
    out = []
    for v in variants or []:
        label = str(v.get("size") or v.get("nameKo") or v.get("name") or "")
        if not label:
            continue
        ysl, gb = parse_ys_size_token(label)
        disp = label
        if ysl and gb and "GB" not in label.upper():
            disp = f"YSL {ysl} / GB {gb}"
        out.append({"value": ysl or label, "displayValue": disp})
    return out


def _build_shoes_chart(sizes: list[dict], *, mens: bool) -> dict | None:
    rows: list[list[str]] = []
    for s in sizes or []:
        ysl, gb = parse_ys_size_token(str(s.get("displayValue") or s.get("value") or ""))
        if not ysl:
            continue
        rows.append([ysl, gb or "—"])
    if not rows:
        return None
    seen: set[str] = set()
    uniq: list[list[str]] = []
    for r in rows:
        if r[0] in seen:
            continue
        seen.add(r[0])
        uniq.append(r)
    ysl_cols = [r[0] for r in uniq]
    gb_cols = [r[1] for r in uniq]
    headers = ["구분", *ysl_cols]
    conv = [["YSL (EU)", *ysl_cols], ["GB", *gb_cols]]
    return {
        "id": "ys-shoes-men" if mens else "ys-shoes-women",
        "titleKo": "생로랑 슈즈 사이즈 가이드" + (" (남성)" if mens else " (여성)"),
        "noteKo": "공홈 표기(YSL / GB) 기준입니다. 발볼·디자인에 따라 핏이 달라질 수 있습니다.",
        "headers": headers,
        "rows": conv,
        "tabs": [
            {
                "id": "conversion",
                "labelKo": "사이즈 환산",
                "headers": headers,
                "rows": conv,
            }
        ],
    }


def _chart_matches_variants(chart: dict | None, variants: list[dict]) -> bool:
    if not chart:
        return False
    headers = {str(h) for h in (chart.get("headers") or []) if h != "구분"}
    expanded = set(headers)
    for h in list(headers):
        if h.startswith("F") and h[1:].isdigit():
            expanded.add(h[1:])
        elif h.isdigit():
            expanded.add(f"F{h}")
    labels: list[str] = []
    for v in variants or []:
        label = str(v.get("size") or v.get("name") or "")
        if not label or label.upper() in {"OS", "U", "TU"}:
            continue
        if not re.search(r"\d", label):
            continue
        # Chip may be "F34" or "34" — both must hit a header.
        if label in expanded:
            labels.append(label)
            continue
        ysl, _ = parse_ys_size_token(label)
        labels.append(label if label in expanded else (ysl or label))
    if not labels:
        return True
    return all(lab in expanded for lab in labels)


def _needs_ko(text: str) -> bool:
    if not text or not text.strip():
        return True
    return bool(EN_HINT.search(text))


def _is_shoes(p: dict, leaf: str) -> bool:
    if p.get("category") == "shoes":
        return True
    blob = " ".join(
        [leaf, str(p.get("subcategory") or ""), *[str(c) for c in (p.get("ysCollections") or [])]]
    ).lower()
    return any(h in blob for h in _SHOES_LEAF_HINTS)


def _is_rtw(p: dict, leaf: str) -> bool:
    if p.get("category") == "luxury":
        return True
    blob = " ".join(
        [leaf, str(p.get("subcategory") or ""), *[str(c) for c in (p.get("ysCollections") or [])]]
    ).lower()
    return any(
        h in blob
        for h in (
            "rtw",
            "denim",
            "shirt",
            "jersey",
            "knit",
            "jacket",
            "outer",
            "coat",
            "leather",
            "pant",
        )
    )


def _refresh_copy(p: dict, raw: dict, cache: dict[str, str]) -> bool:
    changed = False
    desc = str(raw.get("description") or "").strip()
    if desc:
        desc_ko = translate(desc, cache)
        if desc_ko and desc_ko != p.get("descriptionKo"):
            p["descriptionKo"] = desc_ko
            changed = True
    bullets_ko: list[str] = []
    for b in raw.get("shortDescription") or []:
        t = re.sub(r"<[^>]+>", "", str(b)).strip()
        if not t or t.startswith("http") or "marketing?cid=" in t:
            continue
        if len(t) > 220:
            t = t[:220].rsplit(" ", 1)[0]
        bullets_ko.append(translate(t, cache))
    care_en = str(raw.get("productCare") or "").strip()
    care_ko = translate(care_en, cache) if care_en else ""
    comps = str(raw.get("compositions") or "")
    comps_ko = translate(comps, cache) if comps else ""
    images = list(p.get("images") or [])
    if not images and raw.get("localImages"):
        images = list(raw["localImages"])
        p["images"] = images
        p["image"] = images[0]
        changed = True
    story = build_story(
        str(p.get("descriptionKo") or p.get("nameKo") or ""),
        bullets_ko,
        care_ko,
        images,
    )
    if story and story != p.get("storySections"):
        p["storySections"] = story
        changed = True
    features = [x for x in [comps_ko, *bullets_ko[:6]] if x]
    if features and features != p.get("featuresKo"):
        p["featuresKo"] = features
        changed = True
    tech = []
    if comps_ko:
        tech.append({"labelKo": "소재", "valueKo": comps_ko})
    if raw.get("madeIn"):
        tech.append(
            {
                "labelKo": "제조국",
                "valueKo": translate(str(raw["madeIn"]).title(), cache),
            }
        )
    tech.append(
        {
            "labelKo": "제품 코드",
            "valueKo": str(raw.get("sku") or raw.get("id") or "").upper(),
        }
    )
    if tech != p.get("techSpecs"):
        p["techSpecs"] = tech
        changed = True
    name = str(raw.get("name") or p.get("name") or "")
    if name and _needs_ko(str(p.get("nameKo") or "")):
        nk = translate(name, cache)
        if nk and nk != p.get("nameKo"):
            p["nameKo"] = nk
            changed = True
    return changed


def patch_product(p: dict, raw: dict | None, cache: dict[str, str]) -> bool:
    changed = False
    if raw:
        cols = list(
            dict.fromkeys(
                [*(p.get("ysCollections") or []), *(raw.get("collections") or [])]
            )
        )
        if cols != (p.get("ysCollections") or []):
            p["ysCollections"] = cols
            p["subcategory"] = cols[-1] if cols else p.get("subcategory")
            for v in p.get("variants") or []:
                v["ysCollections"] = cols
            changed = True
        raw_imgs = [x for x in (raw.get("localImages") or []) if x]
        cat_imgs = list(p.get("images") or [])
        if len(raw_imgs) > len(cat_imgs):
            p["images"] = raw_imgs
            p["image"] = raw_imgs[0]
            p["hoverImage"] = raw_imgs[1] if len(raw_imgs) > 1 else raw_imgs[0]
            for v in p.get("variants") or []:
                v["image"] = raw_imgs[0]
                v["images"] = raw_imgs
            changed = True

    variants = p.get("variants") or []
    for v in variants:
        if v.get("size"):
            continue
        label = str(v.get("nameKo") or v.get("name") or "")
        if label and re.search(r"\d", label):
            v["size"] = label
            changed = True

    sizes = _sizes_from_raw(raw) or _sizes_from_variants(variants)
    mens = _is_mens(p, raw)
    leaf = _leaf_hint(p, raw)

    chart = None
    if _is_shoes(p, leaf):
        chart = _build_shoes_chart(sizes, mens=mens)
    elif _is_rtw(p, leaf):
        chart = size_chart_for_rtw(sizes, mens=mens, leaf_hint=leaf)

    if chart and (
        chart != p.get("sizeChart")
        or not _chart_matches_variants(p.get("sizeChart"), variants)
    ):
        p["sizeChart"] = chart
        changed = True
    elif p.get("sizeChart") and not _chart_matches_variants(p.get("sizeChart"), variants):
        if chart:
            p["sizeChart"] = chart
            changed = True
        elif _is_rtw(p, leaf) or _is_shoes(p, leaf):
            p["sizeChart"] = None
            changed = True

    if raw and (
        _needs_ko(str(p.get("descriptionKo") or ""))
        or not (p.get("storySections") or [])
        or _needs_ko(
            " ".join(s.get("bodyKo") or "" for s in (p.get("storySections") or [])[:1])
        )
    ):
        # Bust stale hybrid cache entries keyed by English source.
        for key in (
            str(raw.get("description") or ""),
            *[str(b) for b in (raw.get("shortDescription") or [])],
            str(raw.get("productCare") or ""),
        ):
            key = re.sub(r"\s+", " ", key.strip())
            if key and key in cache and _needs_ko(str(cache.get(key) or "")):
                cache.pop(key, None)
        if _refresh_copy(p, raw, cache):
            changed = True

    return changed


def main() -> int:
    catalog = load_json(CATALOG, [])
    cache = load_json(CACHE, {})
    raw_by_id = _load_all_raw()

    changed_n = 0
    chart_ok = chart_bad = 0
    sample = None
    for p in catalog:
        pid = str(p.get("id") or "").removeprefix("ys-").upper()
        raw = raw_by_id.get(pid)
        if patch_product(p, raw, cache):
            changed_n += 1
        variants = p.get("variants") or []
        # Accessories (belts cm etc.) may omit charts — only score RTW / shoes.
        if p.get("category") not in {"luxury", "shoes"}:
            continue
        if any(re.search(r"\d", str(v.get("name") or "")) for v in variants):
            if _chart_matches_variants(p.get("sizeChart"), variants):
                chart_ok += 1
            else:
                chart_bad += 1
                # T1/T2 accessory-ish size tokens on RTW — ignore if only extras fail.
                labels = [
                    str(v.get("name") or "")
                    for v in variants
                    if re.search(r"\d", str(v.get("name") or ""))
                ]
                core = [x for x in labels if not re.fullmatch(r"T\d+", x, re.I)]
                if core and _chart_matches_variants(
                    p.get("sizeChart"),
                    [{"name": x} for x in core],
                ):
                    chart_ok += 1
                    chart_bad -= 1
        if p.get("id") == "ys-834135y28ea4093":
            sample = p

    save_json(CATALOG, catalog)
    save_json(CACHE, cache)
    report = {
        "changed": changed_n,
        "chart_ok": chart_ok,
        "chart_bad": chart_bad,
    }
    if sample:
        report["sample"] = {
            "id": sample["id"],
            "chart_id": (sample.get("sizeChart") or {}).get("id"),
            "headers": (sample.get("sizeChart") or {}).get("headers"),
            "sizes": [v.get("name") for v in (sample.get("variants") or [])],
            "descriptionKo": (sample.get("descriptionKo") or "")[:160],
            "images": len(sample.get("images") or []),
            "story_n": len(sample.get("storySections") or []),
            "care": next(
                (
                    s.get("bodyKo", "")[:100]
                    for s in (sample.get("storySections") or [])
                    if s.get("titleKo") == "케어 가이드"
                ),
                "",
            ),
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if chart_bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
