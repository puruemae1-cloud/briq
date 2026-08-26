#!/usr/bin/env python3
"""Seed curated KO for Arc'teryx footwear PDP strings (ax-pdp-cache).

Used when gtx/mymemory are rate-limited; merge into ax-translate-cache.json
before build-ax-catalog.py.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "src/data/ax/ax-translate-cache.json"

# Natural Korean for footwear feature/story copy. Keep brand/tech tokens Latin.
FW_KO: dict[str, str] = {
    "Surface clean only": "표면만 가볍게 닦아 관리하세요",
    "Footwear construction": "슈즈 구조",
    "Footwear geometry": "슈즈 지오메트리",
    "Footwear liner construction": "안창 구조",
    "Footwear outsole construction": "아웃솔 구조",
    "Technical features": "기술 특징",
    "Sustainability": "지속가능성",
    "Materials": "소재",
    "Care": "관리",
    "Waterproof · Breathable": "방수 · 통기성",
    "Waterproof · Breathable · Durable": "방수 · 통기성 · 내구성",
    "Waterproof · Breathable · Lightweight · Durable · Abrasion resistant": "방수 · 통기성 · 경량 · 내구성 · 내마모성",
    "Waterproof · Breathable · Lightweight · Durable · Supportive construction · Abrasion resistant": "방수 · 통기성 · 경량 · 내구성 · 지지력 있는 구조 · 내마모성",
    "Breathable · Lightweight · Durable · Supportive construction · Abrasion resistant": "통기성 · 경량 · 내구성 · 지지력 있는 구조 · 내마모성",
    "Breathable · Lightweight · Abrasion resistant · Collapsible heel allows shoe to be worn as a camp and belay slipper": "통기성 · 경량 · 내마모성 · 접이식 힐로 캠프·빌레이 슬리퍼처럼 착용 가능",
    "Lightweight · Durable · Supportive construction · Abrasion resistant": "경량 · 내구성 · 지지력 있는 구조 · 내마모성",
    "Durable · Stable with heavy loads": "내구성 · 무거운 짐에도 안정적",
    "Durable · Weather protective · Forefoot grip for climbing rock and heel traction for hiking down soft surfaces · Ankle support for trekking with heavy packs": "내구성 · 방한·방수 보호 · 바위 등반용 앞발 그립과 소프트 지형 하강용 힐 접지력 · 무거운 배낭 트레킹을 위한 발목 지지",
    "Ventilated · Hiking grip": "통기성 · 하이킹 접지력",
    "Responsive for efficiency and reduced fatigue · Propulsive yet stable · Comfortable for long efforts": "효율적인 반응성과 피로 감소 · 추진력과 안정성 · 장거리에도 편안함",
    "Lining: Textile · Insole: Textile · Outsole: Rubber": "라이닝: 텍스타일 · 인솔: 텍스타일 · 아웃솔: 고무",
    "Lining: Textile · Insole: Textile/Synthetic · Outsole: Rubber": "라이닝: 텍스타일 · 인솔: 텍스타일/합성 · 아웃솔: 고무",
    "Lining: Textile/Synthetic · Insole: Textile · Outsole: Rubber": "라이닝: 텍스타일/합성 · 인솔: 텍스타일 · 아웃솔: 고무",
    "Lining: Textile · Outsole: Rubber": "라이닝: 텍스타일 · 아웃솔: 고무",
    "Lining: Leather · Outsole: Rubber": "라이닝: 가죽 · 아웃솔: 고무",
    "Lining: Textile/Synthetic · Outsole: Rubber · Insole: Synthetic": "라이닝: 텍스타일/합성 · 아웃솔: 고무 · 인솔: 합성",
    "Insole: Leather · Outsole: Rubber · Lining: Leather/Textile": "인솔: 가죽 · 아웃솔: 고무 · 라이닝: 가죽/텍스타일",
    "Outsole: Rubber · Insole: Synthetic · Upper: Textile/Synthetic/Leather": "아웃솔: 고무 · 인솔: 합성 · 갑피: 텍스타일/합성/가죽",
    "2mm lugs · Drop (Stack): 7mm (24mm : 17mm)": "러그 2mm · 드롭(스택): 7mm (24mm : 17mm)",
    "4mm lugs · Drop (Stack): 11mm (24mm : 13mm)": "러그 4mm · 드롭(스택): 11mm (24mm : 13mm)",
    "Drop (Stack): 12.5mm (35mm : 22.5mm) · 5.1mm lugs": "드롭(스택): 12.5mm (35mm : 22.5mm) · 러그 5.1mm",
    "Drop (Stack): 6mm (25mm : 19mm) · 6mm lugs": "드롭(스택): 6mm (25mm : 19mm) · 러그 6mm",
    "Ergonomically patterned 4mm lugs · Offset (Stack height): 8mm (18mm : 10mm)": "인체공학적 4mm 러그 패턴 · 오프셋(스택 높이): 8mm (18mm : 10mm)",
    "Mud-releasing custom 4mm lug pattern provides grip on hardpack and bite on soft trails · Offset (Stack height): 6mm (25mm : 19mm)": "진흙 배출형 커스텀 4mm 러그 패턴이 하드팩에서는 접지력을, 소프트 트레일에서는 물고 들어가는 그립을 제공합니다 · 오프셋(스택 높이): 6mm (25mm : 19mm)",
    "Offset (Stack height): 7mm (23mm : 16mm) · Zonal lug patterns are specifically designed to provide forefoot grip while smearing with comfort and surefootedness on the trail": "오프셋(스택 높이): 7mm (23mm : 16mm) · 존별 러그 패턴이 스미어링 시 앞발 그립과 트레일에서의 편안하고 확실한 접지력을 균형 있게 제공합니다",
    "Stepped 4.5mm/3.5mm lugs provide optimized traction on trails plus improved dirt shedding · Drop (Stack): 6mm (31.5mm : 25.5mm)": "계단형 4.5mm/3.5mm 러그가 트레일 접지력을 최적화하고 흙 배출을 개선합니다 · 드롭(스택): 6mm (31.5mm : 25.5mm)",
    "Form-moulded sockliner is smooth and comfortable": "폼 몰드 안창이 부드럽고 편안합니다",
    "Full GORE-TEX® liner with Invisible Fit Technology provides waterproof protection with improved flex, comfort, and breathability · Form-moulded sockliner is smooth and comfortable": "Invisible Fit 기술이 적용된 풀 GORE-TEX® 라이너가 방수 보호와 함께 유연성·편안함·통기성을 높입니다 · 폼 몰드 안창이 부드럽고 편안합니다",
    "Vibram® Megagrip outsole with LITEBASE technology delivers durable, surefooted performance across a range of conditions while shedding every gram possible": "LITEBASE 기술이 적용된 Vibram® Megagrip 아웃솔이 가능한 한 무게를 줄이면서도 다양한 조건에서 내구성 있는 확실한 접지력을 제공합니다",
    "Vibram® Megagrip outsole with LITEBASE technology delivers durable, surefooted performance across a range of conditions while shedding every gram possible · Outsole and midsole zones integrate for optimal response and performance · Forefoot TPU film provides underfoot protection and improved stability": "LITEBASE 기술이 적용된 Vibram® Megagrip 아웃솔이 가능한 한 무게를 줄이면서도 다양한 조건에서 내구성 있는 확실한 접지력을 제공합니다 · 아웃솔과 미드솔 존이 통합되어 반응성과 성능을 최적화합니다 · 앞발 TPU 필름이 발밑 보호와 안정성을 높입니다",
    "Logos & Label configuration": "로고 및 라벨 구성",
    "Vibram® Megagrip outsole delivers durable, surefooted performance across a range of conditions · Lug design optimized for traction on soft surfaces and grip on rocks": "Vibram® Megagrip 아웃솔이 다양한 조건에서 내구성 있는 확실한 접지력을 제공합니다 · 소프트 지형 접지력과 바위 그립에 최적화된 러그 디자인",
    "Vibram® MegaGrip™ rubber compound is durable and grippy · Multi-height traction pattern on the outsole includes a forefoot climbing zone for smearing up rock and a heel traction zone for hiking downhill · Extra lugs around the perimeter add traction on uneven terrain": "Vibram® MegaGrip™ 러버 컴파운드가 내구성과 그립력을 제공합니다 · 다단 접지 패턴은 바위 스미어링용 앞발 클라이밍 존과 내리막 하이킹용 힐 접지 존을 포함합니다 · 둘레의 추가 러그가 고르지 않은 지형에서 접지력을 더합니다",
    "Vibram® XS Flash 2 outsole delivers outstanding grip and durable, sure-footed performance across a range of conditions · Dual-purpose lugged outsole with a forefoot climbing zone optimized for smearing up rock and separate traction on the heel for hiking downhill": "Vibram® XS Flash 2 아웃솔이 다양한 조건에서 뛰어난 그립과 내구성 있는 확실한 접지력을 제공합니다 · 이중 목적 러그 아웃솔로, 바위 스미어링에 최적화된 앞발 클라이밍 존과 내리막 하이킹용 힐 접지 존을 갖춥니다",
    "Vibram® XS Flash 2 outsole delivers outstanding grip and durable, sure-footed performance across a range of conditions · Tread is specifically designed to provide grip while edging and offer on-trail traction with climbing performance": "Vibram® XS Flash 2 아웃솔이 다양한 조건에서 뛰어난 그립과 내구성 있는 확실한 접지력을 제공합니다 · 트레드가 엣징 그립과 클라이밍 성능이 있는 온트레일 접지력을 함께 제공하도록 설계되었습니다",
    "Norvan LD 4 Shoe": "Norvan LD 4 슈즈",
    "Norvan LD 4 GTX Shoe": "Norvan LD 4 GTX 슈즈",
    "Norvan 4 Nivalis GTX Shoe": "Norvan 4 Nivalis GTX 슈즈",
    "Konseal Shoe": "Konseal 슈즈",
    "Konseal GTX Shoe": "Konseal GTX 슈즈",
    "Konseal Subida Shoe": "Konseal Subida 슈즈",
    "Konseal Trek Boot": "Konseal Trek 부츠",
    "Kopec GTX Shoe": "Kopec GTX 슈즈",
    "Kopec Mid GTX Boot": "Kopec Mid GTX 부츠",
    "Kragg Shoe": "Kragg 슈즈",
    "Kragg Aura Shoe": "Kragg Aura 슈즈",
    "Sylan 2 Shoe": "Sylan 2 슈즈",
    "Vertex Speed Shoe": "Vertex Speed 슈즈",
    "Vertex Speed Low Shoe": "Vertex Speed Low 슈즈",
    "Vertex Alpine Shoe": "Vertex Alpine 슈즈",
    "Vertex Alpine GTX Shoe": "Vertex Alpine GTX 슈즈",
}

# Long construction / story bodies — continue in second dict merge below
FW_KO.update(
    {
        "Dual-density midsole material and construction combine cushioning with lasting shock absorption and support for all-day comfort and stability on rugged terrain · Lacing system provides a smooth pull and secure midfoot fit while preventing backslip · Tongue pocket secures the laces, eliminates lace bounce, and prevents snagging · Flexible external frame wraps the midfoot for a secure hold that prevents forward slide and toe bang · Abrasion-resistant PFAS-free woven polyester upper is durable, lightweight, breathable, and flexible · Flexible laminated TPU reinforcement zones add protection and abrasion resistance": "이중 밀도 미드솔 소재와 구조가 쿠셔닝과 지속적인 충격 흡수를 결합해 거친 지형에서도 하루 종일 편안함과 안정성을 제공합니다 · 레이싱 시스템이 부드럽게 조여지며 미드풋을 확실히 고정하고 뒤꿈치 밀림을 막습니다 · 텅 포켓이 끈을 고정해 끈 튀김을 없애고 걸림을 방지합니다 · 유연한 외부 프레임이 미드풋을 감싸 앞으로 밀리거나 발가락이 부딪히는 것을 막습니다 · PFAS-free 내마모성 직조 폴리에스터 갑피가 내구성·경량·통기성·유연성을 갖춥니다 · 유연한 라미네이트 TPU 보강 존이 보호력과 내마모성을 더합니다",
        "Dual-density midsole material and construction combine cushioning with lasting shock absorption and support for all-day comfort and stability on rugged terrain · Lacing system provides a smooth pull and secure midfoot fit while preventing backslip · Tongue pocket secures the laces, eliminates lace bounce, and prevents snagging · Flexible external frame wraps the midfoot for a secure hold that prevents forward slide and toe bang · Two woven PFAS-free upper materials are mapped to combine flex and breathability with targeted abrasion-resistance · Flexible laminated TPU reinforcement zones add protection and abrasion resistance · Flat-knit tongue wraps the foot to improve fit and lockdown": "이중 밀도 미드솔 소재와 구조가 쿠셔닝과 지속적인 충격 흡수를 결합해 거친 지형에서도 하루 종일 편안함과 안정성을 제공합니다 · 레이싱 시스템이 부드럽게 조여지며 미드풋을 확실히 고정하고 뒤꿈치 밀림을 막습니다 · 텅 포켓이 끈을 고정해 끈 튀김을 없애고 걸림을 방지합니다 · 유연한 외부 프레임이 미드풋을 감싸 앞으로 밀리거나 발가락이 부딪히는 것을 막습니다 · 두 가지 PFAS-free 직조 갑피 소재를 매핑해 유연·통기성과 국소 내마모성을 함께 잡았습니다 · 유연한 라미네이트 TPU 보강 존이 보호력과 내마모성을 더합니다 · 플랫 니트 텅이 발을 감싸 핏과 락다운을 높입니다",
        "Dual-density midsole material and construction combine cushioning with lasting shock absorption and support for all-day comfort and stability on rugged terrain · Specially designed TPU midfoot shank offers torsional support and underfoot protection for minimal weight · Extended U-throat construction provides more flex, better breathability, greater comfort · Waterproof, breathable GORE-TEX® ePE fabric protection with a reduced carbon footprint · Highly durable CORDURA® mesh upper delivers lightweight, breathable, quick-drying performance · Roomy toe box accommodates splay and protects toes · Lacing system utilizes integrated webbing with durable metal eyelets at the top to create a secure, supportive, comfortable fit · Asymmetric molded TPU toe cap and reinforcements at high-wear zones add protection and durability · External molded TPU heel counter adds support and protection": "이중 밀도 미드솔 소재와 구조가 쿠셔닝과 지속적인 충격 흡수를 결합해 거친 지형에서도 하루 종일 편안함과 안정성을 제공합니다 · 특수 설계 TPU 미드풋 생크가 최소한의 무게로 비틀림 지지와 발밑 보호를 제공합니다 · 확장된 U-스로트 구조가 유연성·통기성·편안함을 높입니다 · 탄소 발자국을 줄인 방수·통기성 GORE-TEX® ePE 패브릭 보호 · 고내구성 CORDURA® 메시 갑피가 경량·통기·속건 성능을 제공합니다 · 넉넉한 토박스가 발볼 확장을 수용하고 발가락을 보호합니다 · 일체형 웨빙과 상단 메탈 아일렛 레이싱이 안정적이고 지지력 있는 편안한 핏을 만듭니다 · 비대칭 몰드 TPU 토캡과 고마모 구간 보강이 보호력과 내구성을 더합니다 · 외부 몰드 TPU 힐 카운터가 지지와 보호를 더합니다",
    }
)


def main() -> None:
    # Load remaining long strings from /tmp if present and fill any gaps interactively via second file
    extra_path = ROOT / "scripts" / "ax_fw_ko_extra.json"
    if extra_path.exists():
        FW_KO.update(json.loads(extra_path.read_text()))

    cache: dict[str, str] = {}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text())
    before = len(cache)
    cache.update(FW_KO)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")
    print(f"Merged {len(FW_KO)} footwear KO strings → {CACHE} (entries {before} → {len(cache)})")


if __name__ == "__main__":
    main()
