#!/usr/bin/env python3
"""Backfill Dior catalog list prices + enrich known PDPs from official KO copy."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

_merge_spec = importlib.util.spec_from_file_location(
    "merge_di_catalog_ko",
    ROOT / "scripts/merge-di-catalog-ko.py",
)
_merge = importlib.util.module_from_spec(_merge_spec)
assert _merge_spec and _merge_spec.loader
_merge_spec.loader.exec_module(_merge)
list_price_from_variants = _merge.list_price_from_variants
gbp_to_krw = _merge.gbp_to_krw

CAT = ROOT / "src/data/di/di-catalog.json"

BACKPACK_ENRICH = {
    "di-1adba200ykk-h00n": {
        "descriptionKo": (
            "블랙 그레인 송아지 가죽 & 콘트라스트 스티칭\n\n"
            "새들 디자인을 모던하고 유니크하게 해석한 새들 플랩 백팩입니다. "
            "콘트라스트 스티칭을 더한 블랙 그레인 송아지 가죽과 테크니컬 패브릭 "
            "소재로 제작되었으며, 앞면의 Dior 시그니처 장식이 돋보입니다. "
            "메인 수납공간은 드로우스트링과 플랩으로 닫히며 데일리 소지품을 "
            "넉넉히 수납할 수 있습니다. CD 시그니처 알루미늄 버클의 앞면 플랩 "
            "포켓에는 지갑·열쇠·이어폰·휴대폰을 간편하게 꺼낼 수 있고, "
            "내부에는 15인치 노트북·A4 문서·태블릿을 넣을 수 있는 플랫 "
            "수납공간이 마련되어 있습니다. 조절 가능한 패딩 숄더 스트랩과 "
            "뒷면 Dior 시그니처 패딩 메시로 편안한 착용감을 제공하며, "
            "더스트 백이 함께 제공됩니다."
        ),
        "featuresKo": [
            "주요 소재: 테크니컬 패브릭 & 송아지 가죽",
            "테크니컬 패브릭, 코튼, 송아지 가죽 안감",
            "드로우스트링 디테일의 메인 플랩 수납공간",
            "내부 플랫 노트북 수납공간",
            "CD 시그니처 알루미늄 버클 디테일의 앞면 플랩 포켓",
            "가죽 탑 핸들",
            "조절 가능한 패딩 숄더 스트랩",
            "뒷면 Dior 시그니처 패딩 메시",
            "앞면 루테늄 피니시 브라스 Dior 시그니처",
            "내부 Dior 시그니처 엠보싱",
            "더스트 백 포함",
            "이탈리아 제조",
        ],
        "techSpecs": [
            {
                "labelKo": "사이즈",
                "valueKo": "26.5 × 41 × 14.5 cm (가로 × 높이 × 깊이)",
            },
            {
                "labelKo": "수납",
                "valueKo": "15인치 노트북, A4 문서, 태블릿 수납 가능",
            },
            {
                "labelKo": "무게",
                "valueKo": "약 1.1 kg (소재에 따라 달라질 수 있음)",
            },
            {"labelKo": "제조국", "valueKo": "이탈리아"},
        ],
        "storySections": [
            {
                "titleKo": "제품 소개",
                "bodyKo": (
                    "새들 디자인을 모던하고 유니크하게 해석한 새들 플랩 백팩입니다. "
                    "블랙 그레인 송아지 가죽과 콘트라스트 스티칭, 앞면 Dior "
                    "시그니처가 특징이며, 데일리부터 트래블까지 활용도 높은 "
                    "실루엣입니다."
                ),
                "image": "/products/di-pdp/1adba200ykk-h00n/1.jpg",
            },
            {
                "titleKo": "수납 & 디테일",
                "bodyKo": (
                    "드로우스트링과 플랩으로 닫히는 메인 수납공간, "
                    "CD 시그니처 알루미늄 버클의 앞면 플랩 포켓, "
                    "15인치 노트북·A4·태블릿을 수납할 수 있는 내부 플랫 "
                    "컴파트먼트로 실용성을 갖췄습니다. 가죽 탑 핸들과 "
                    "조절 가능한 패딩 숄더 스트랩, 뒷면 패딩 메시로 "
                    "편안한 착용감을 제공합니다."
                ),
                "image": "/products/di-pdp/1adba200ykk-h00n/5.jpg",
            },
            {
                "titleKo": "착용 & 스타일",
                "bodyKo": (
                    "루테늄 피니시 브라스 Dior 시그니처와 내부 엠보싱으로 "
                    "완성도 높은 마감을 자랑합니다. 캐주얼부터 비즈 "
                    "캐주얼까지 다양한 룩에 자연스럽게 어울리며, "
                    "더스트 백이 함께 제공됩니다."
                ),
                "image": "/products/di-pdp/1adba200ykk-h00n/10.jpg",
            },
            {
                "titleKo": "룩",
                "bodyKo": (
                    "Dior 남성 컬렉션 룩과 함께 제안되는 스타일링 "
                    "레퍼런스입니다."
                ),
                "image": "/products/di-pdp/1adba200ykk-h00n/11.jpg",
            },
        ],
    },
}


def main() -> None:
    products = json.loads(CAT.read_text())
    fixed = 0
    for p in products:
        variants = p.get("variants") or []
        fallback = 0
        if p.get("gbpPrice"):
            fallback = gbp_to_krw(float(p["gbpPrice"]))
        new_price = list_price_from_variants(variants, fallback)
        if new_price and p.get("price") != new_price:
            p["price"] = new_price
            fixed += 1
        enrich = BACKPACK_ENRICH.get(p.get("id") or "")
        if enrich:
            p.update(enrich)
    CAT.write_text(json.dumps(products, indent=2, ensure_ascii=False) + "\n")
    print(f"backfilled price on {fixed} products; enriched {len(BACKPACK_ENRICH)} PDPs")


if __name__ == "__main__":
    main()
