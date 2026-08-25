#!/usr/bin/env python3
"""Merge curated Korean copy for Prada men's accessories into pr-accessories-ko-copy.json."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_W_PATH = ROOT / "src/data/pr/pr-womens-accessories-catalog-raw.json"
RAW_M_PATH = ROOT / "src/data/pr/pr-mens-accessories-catalog-raw.json"
SLG_PATH = ROOT / "src/data/pr/pr-slg-ko-copy.json"
OUT_PATH = ROOT / "src/data/pr/pr-accessories-ko-copy.json"
WOMEN_DESC_DATA = Path(__file__).with_name("_accessories_desc_ko.py")
MEN_DESC_DATA = Path(__file__).with_name("_mens_accessories_desc_ko.py")
MEN_DETAIL_DATA = Path(__file__).with_name("_mens_accessories_detail_extra.py")

# Reuse women's seed helpers and base detail maps.
import importlib.util

_women_seed = Path(__file__).with_name("seed-pr-accessories-ko-copy.py")
_spec = importlib.util.spec_from_file_location("seed_pr_accessories_ko_copy", _women_seed)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)
DETAIL_EXACT = _mod.DETAIL_EXACT
FRAME_PREFIXES = _mod.FRAME_PREFIXES
MATERIALS = _mod.MATERIALS

MEN_FRAME_PREFIXES: list[tuple[str, str]] = [
    *FRAME_PREFIXES,
    ("Bio-acetate frame front - Color: ", "바이오 아세테이트 프레임 프론트 · 컬러: "),
    ("Bio-acetate frame front - ", "바이오 아세테이트 프레임 프론트 · "),
    ("Nylon frame front - Color: ", "나일론 프레임 프론트 · 컬러: "),
    ("Nylon frame front - ", "나일론 프레임 프론트 · "),
    ("Titanium frame front in ", "티타늄 프레임 프론트 · "),
    ("Recycled bio-acetate frame front -- Color: ", "리사이클 바이오 아세테이트 프레임 프론트 · 컬러: "),
    ("Recycled bio-acetate frame front - Color: ", "리사이클 바이오 아세테이트 프레임 프론트 · 컬러: "),
]

MEN_MATERIALS: dict[str, str] = {
    **MATERIALS,
    "925 Silver": "925 실버",
    "Nylon": "나일론",
    "Silk": "실크",
    "Wool/Silk": "울/실크",
}


def _load_py_dict(path: Path, name: str) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path.name}")
    ns: dict[str, object] = {}
    exec(path.read_text(encoding="utf-8"), ns)  # noqa: S102
    mapping = ns.get(name)
    if not isinstance(mapping, dict):
        raise ValueError(f"{path.name} must define {name} dict")
    return dict(mapping)


def _collect_unique(raw_path: Path) -> tuple[set[str], set[str], set[str]]:
    raw = json.loads(raw_path.read_text())
    descs: set[str] = set()
    details: set[str] = set()
    materials: set[str] = set()
    for product in raw["products"]:
        d = (product.get("description") or "").strip()
        if d:
            descs.add(d)
        for item in product.get("details") or []:
            s = (item or "").strip()
            if s:
                details.add(s)
        m = (product.get("material") or "").strip()
        if m:
            materials.add(m)
        for item in product.get("materialsCare") or []:
            s = (item or "").strip()
            if s:
                materials.add(s)
    return descs, details, materials


def _load_slg_reuse() -> dict[str, str]:
    if not SLG_PATH.exists():
        return {}
    slg = json.loads(SLG_PATH.read_text())
    reuse: dict[str, str] = {}
    for section in ("descriptions", "details", "materials"):
        reuse.update(slg.get(section) or {})
    return reuse


def _load_existing_copy() -> dict[str, dict[str, str]]:
    if not OUT_PATH.exists():
        return {"descriptions": {}, "details": {}, "materials": {}}
    data = json.loads(OUT_PATH.read_text())
    return {
        "descriptions": dict(data.get("descriptions") or {}),
        "details": dict(data.get("details") or {}),
        "materials": dict(data.get("materials") or {}),
    }


def translate_detail(text: str, slg_reuse: dict[str, str], men_extra: dict[str, str]) -> str:
    if text in slg_reuse:
        return slg_reuse[text]
    if text in DETAIL_EXACT:
        return DETAIL_EXACT[text]
    if text in men_extra:
        return men_extra[text]
    for prefix, ko_prefix in MEN_FRAME_PREFIXES:
        if text.startswith(prefix):
            return ko_prefix + text[len(prefix) :].replace("&amp;", "&")
    m = re.match(r"Lens-nose-temple measurements?: (.+)$", text)
    if m:
        return f"렌즈-브릿지-템플 길이: {m.group(1)}"
    m = re.match(r"Lens-nose-temple measurement : (.+)$", text)
    if m:
        return f"렌즈-브릿지-템플 길이: {m.group(1)}"
    raise KeyError(f"Missing detail translation: {text!r}")


def build_copy() -> dict[str, dict[str, str]]:
    w_desc, w_det, w_mat = _collect_unique(RAW_W_PATH)
    m_desc, m_det, m_mat = _collect_unique(RAW_M_PATH)
    desc_needed = w_desc | m_desc
    detail_needed = w_det | m_det
    material_needed = w_mat | m_mat

    existing = _load_existing_copy()
    slg_reuse = _load_slg_reuse()
    women_descriptions = _load_py_dict(WOMEN_DESC_DATA, "DESCRIPTIONS")
    men_descriptions = _load_py_dict(MEN_DESC_DATA, "DESCRIPTIONS")
    men_detail_extra = _load_py_dict(MEN_DETAIL_DATA, "MEN_DETAIL_EXTRA")

    descriptions = dict(existing["descriptions"])
    descriptions.update(women_descriptions)
    descriptions.update(men_descriptions)

    details = dict(existing["details"])
    for s in sorted(detail_needed):
        details[s] = translate_detail(s, slg_reuse, men_detail_extra)

    materials = dict(existing["materials"])
    materials.update(MEN_MATERIALS)

    for section, needed, mapping in (
        ("descriptions", desc_needed, descriptions),
        ("details", detail_needed, details),
        ("materials", material_needed, materials),
    ):
        missing = sorted(needed - set(mapping))
        if missing:
            raise SystemExit(
                f"Missing {section} translations ({len(missing)}):\n" + "\n".join(missing[:5])
            )
        for en, ko in slg_reuse.items():
            if en in needed and en not in mapping:
                mapping[en] = ko

    return {"descriptions": descriptions, "details": details, "materials": materials}


def main() -> None:
    payload = build_copy()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(
        f"Wrote {OUT_PATH} "
        f"({len(payload['descriptions'])} desc, "
        f"{len(payload['details'])} details, "
        f"{len(payload['materials'])} materials)"
    )


if __name__ == "__main__":
    main()
