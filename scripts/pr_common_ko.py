#!/usr/bin/env python3
"""Shared Prada EN→KO phrase maps for bags, travel, and accessories."""
from __future__ import annotations

# Longer phrases first when applied via apply_phrases().
PHRASE_KO: list[tuple[str, str]] = sorted(
    [
        (
            "For sustainable care to preserve the product's characteristics and reduce microfiber shedding, we recommend not washing the item too often. Let the product air out after every use and have it dry cleaned at a specialized ecological dry cleaners.",
            "제품의 특성을 유지하고 미세섬유 발생을 줄이기 위해 잦은 세탁은 피해 주세요. 사용 후에는 통풍이 잘 되는 곳에서 건조시키고, 친환경 전문 드라이클리닝을 이용해 주세요.",
        ),
        (
            "For sustainable care to preserve the product's characteristics and reduce microfiber shedding, we recommend not washing the item too often. Let the product air out after every use and follow the washing instructions on the label.",
            "제품의 특성을 유지하고 미세섬유 발생을 줄이기 위해 잦은 세탁은 피해 주세요. 사용 후에는 통풍이 잘 되는 곳에서 건조시키고, 라벨의 세탁 지침을 따라 주세요.",
        ),
        ("Prada's innovative Re-Nylon fabric produced from recycled plastic materials collected in the ocean", "바다에서 수거한 재활용 플라스틱으로 만든 프라다의 혁신적인 Re-Nylon 패브릭"),
        ("innovative regenerated nylon fabric obtained from recycled plastic materials collected in the ocean", "바다에서 수거한 재활용 플라스틱으로 만든 혁신적인 재생 나일론 패브릭"),
        ("innovative regenerated nylon yarn", "혁신적인 재생 나일론 원사"),
        ("the iconic enameled metal triangle logo", "아이코닉한 에나멜 메탈 트라이앵글 로고"),
        ("the iconic signature of the enameled metal triangle logo", "에나멜 메탈 트라이앵글 로고의 아이코닉 시그니처"),
        ("the distinctive signature touch of the enameled metal triangle logo", "에나멜 메탈 트라이앵글 로고의 독보적인 시그니처"),
        ("Enameled metal triangle logo on the front", "앞면 에나멜 메탈 트라이앵글 로고"),
        ("Enameled metal triangle logo on front", "앞면 에나멜 메탈 트라이앵글 로고"),
        ("Enameled metal triangle logo", "에나멜 메탈 트라이앵글 로고"),
        ("Detachable adjustable woven nylon tape shoulder strap", "탈부착·길이 조절 우븐 나일론 테이프 숄더 스트랩"),
        ("Detachable adjustable woven nylon shoulder strap", "탈부착·길이 조절 우븐 나일론 숄더 스트랩"),
        ("With straps and side-release buckles", "스트랩 및 사이드 릴리스 버클"),
        ("Woven nylon tape handles", "우븐 나일론 테이프 핸들"),
        ("Two external zipper pockets", "외부 지퍼 포켓 2개"),
        ("Two internal zipper pockets", "내부 지퍼 포켓 2개"),
        ("Two inner zipper pockets", "내부 지퍼 포켓 2개"),
        ("One external zipper pocket", "외부 지퍼 포켓 1개"),
        ("Small pocket on the back", "뒷면 스몰 포켓"),
        ("Zipper closure", "지퍼 클로저"),
        ("Fabric/Leather", "패브릭/가죽"),
        ("Other Materials", "기타 소재"),
        ("Fabric", "패브릭"),
        ("Leather", "가죽"),
    ],
    key=lambda kv: -len(kv[0]),
)


def apply_phrases(text: str) -> str:
    out = text or ""
    for en, ko in PHRASE_KO:
        if en in out:
            out = out.replace(en, ko)
    return out
