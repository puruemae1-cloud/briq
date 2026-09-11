#!/usr/bin/env python3
"""Seed natural Korean PDP copy for Vivienne Westwood watches, then rebuild.

Uses curated EN→KO strings (translate APIs are often rate-limited). Safe to re-run.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "src/data/vw/vw-translate-cache.json"

# Shared care / composition
CARE_EN = (
    "Wipe off any moisture, sweat or dirt with a soft cloth after removing it from the wrist."
    "To maintain plating of the watch protect it from heavy perspiration and chemicals such as "
    "perfumes, lotions, chlorine, household cleaning products, hairspray etc."
    "After saltwater use, rinse watch under tap and wipe dry with a soft cloth. "
    "Avoid extreme heat or cold, as well as prolonged periods of exposure to direct sunlight"
    "Avoid exposure to wet conditions that exceed the water resistance rating of your timepiece."
    "Avoid powerful electric fields or static electricity, which may interfere with the mechanism. "
    "Avoid extreme shock or impact."
)
CARE_KO = (
    "손목에서 벗은 뒤 수분·땀·먼지는 부드러운 천으로 가볍게 닦아 주세요. "
    "도금 상태를 오래 유지하려면 과한 땀과 향수·로션·염소·주방세제·헤어스프레이 등 화학 성분에 닿지 않게 해 주세요. "
    "바닷물과 접촉했다면 흐르는 물에 가볍게 헹군 뒤 부드러운 천으로 물기를 제거하세요. "
    "극심한 고온·저온과 직사광선에 장시간 노출을 피하고, 방수 등급을 넘는 습한 환경은 피하세요. "
    "메커니즘에 영향을 줄 수 있는 강한 전기장·정전기와 강한 충격도 피해주세요."
)

SEED: dict[str, str] = {
    "Main material: stainless steelLens: mineral glass": "소재: 스테인리스 스틸 / 렌즈: 미네랄 글래스",
    "100% Stainless steelMineral glass lens": "스테인리스 스틸 100% / 미네랄 글래스 렌즈",
    "100% Stainless steel": "스테인리스 스틸 100%",
    CARE_EN: CARE_KO,
    # Titles
    "Little Seymour Watch": "리틀 시모어 워치",
    "Seymour Watch": "시모어 워치",
    "36 Fenchurch Watch": "36 펜처치 워치",
    "Fenchurch Watch": "펜처치 워치",
    "Trellick Watch": "트렐릭 워치",
    "Lady Sydenham Watch": "레이디 시드넘 워치",
    "Audley Watch": "오들리 워치",
    "Chelsea Watch": "첼시 워치",
    "Aldgate Watch": "올드게이트 워치",
    "Tavistock Watch": "태비스톡 워치",
    "Berwick Watch": "버윅 워치",
    "Little Wallace Watch": "리틀 월리스 워치",
    "Wallace Watch": "월리스 워치",
    "Little Camberwell Watch": "리틀 캠버웰 워치",
    "Camberwell Watch": "캠버웰 워치",
    "Spring Cherub Watch": "스프링 커럽 워치",
    # Descriptions (split lines match build-vw extract_detail_lines)
}

# Full description bodies + sentence splits used by extract_detail_lines
DESCS: list[tuple[str, str]] = [
    (
        "Inspired by the signature Fenchurch silhouette, the 36 Fenchurch watch is reimagined this season in a larger size, featuring a classic three-link bracelet in polished silver-tone stainless steel. Crafted with specialist Swiss movement, the design is complete with a pink sunray-brushed dial, a date window at the three o'clock position and the house's signature orb emblem at the top of the dial, echoed on the second hand. Features a round facePolished platingSwiss movementTonal hardware Orb-branded detailing2-year warranty cover5 ATM Water resistant Case size: 36mmPlease note that the watch band can be adjusted to a smaller length Code: 8053195833160",
        "시그니처 펜처치 실루엣에서 영감을 받은 36 펜처치 워치를 이번 시즌 더 큰 사이즈로 재해석했습니다. 폴리시드 실버 톤 스테인리스 스틸의 클래식 3링크 브레이슬릿이 돋보이며, 스위스 무브먼트를 탑재했습니다. 핑크 선레이 브러시 다이얼, 3시 방향 날짜창, 다이얼 상단의 하우스 시그니처 오브 엠블럼과 초침의 오브 디테일로 완성됩니다. 라운드 페이스·폴리시드 도금·스위스 무브먼트·톤온톤 하드웨어·오브 브랜딩 / 2년 보증 / 5ATM 방수 / 케이스 36mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8053195833160",
    ),
    (
        "Inspired by the signature Fenchurch silhouette, the 36 Fenchurch watch is reimagined this season in a larger size, featuring a classic three-link bracelet in polished silver-tone stainless steel. Crafted with specialist Swiss movement, the design is complete with a navy sunray-brushed dial, a date window at the three o'clock position and the house's signature orb emblem at the top of the dial, echoed on the second hand. Features a round facePolished platingSwiss movementTonal hardware Orb-branded detailing2-year warranty cover5 ATM Water resistant Case size: 36mmPlease note that the watch band can be adjusted to a smaller length Code: 8053195833146",
        "시그니처 펜처치 실루엣에서 영감을 받은 36 펜처치 워치를 이번 시즌 더 큰 사이즈로 재해석했습니다. 폴리시드 실버 톤 스테인리스 스틸의 클래식 3링크 브레이슬릿이 돋보이며, 스위스 무브먼트를 탑재했습니다. 네이비 선레이 브러시 다이얼, 3시 방향 날짜창, 다이얼 상단의 하우스 시그니처 오브 엠블럼과 초침의 오브 디테일로 완성됩니다. 라운드 페이스·폴리시드 도금·스위스 무브먼트·톤온톤 하드웨어·오브 브랜딩 / 2년 보증 / 5ATM 방수 / 케이스 36mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8053195833146",
    ),
    (
        "Our Trellick watch features a circular stainless steel case, framed by a contrasting tortoiseshell bezel engraved with the house’s signature letter motif. The design features a twill-textured white dial is accented with intricate screw-inspired detailing and a classic three-hand movement, complemented by a three-link bracelet with satin-brushed and polished finishes. Features a three-link braceletTwill-textured dialgold-tone metal accentsScrew-inspired detailingTortoiseshell bezel Swiss movement2-year warranty cover5 ATM Water resistant Case size: 30mmPlease note that the watch band can be adjusted to a smaller length Code: 8053195833078",
        "트렐릭 워치는 원형 스테인리스 스틸 케이스에, 하우스 시그니처 레터 모티프가 새겨진 대비감 있는 토토이즈셸 베젤을 더했습니다. 트윌 텍스처의 화이트 다이얼에는 스크류에서 영감을 받은 섬세한 디테일과 클래식 3핸즈 무브먼트가 어우러지며, 새틴 브러시와 폴리시드가 교차하는 3링크 브레이슬릿으로 완성됩니다. 3링크 브레이슬릿·트윌 다이얼·골드 톤 메탈 액센트·스크류 디테일·토토이즈셸 베젤·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 30mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8053195833078",
    ),
    (
        "Our signature Lady Sydenham watch is reimagined this season with a silver-tone stainless steel case and bracelet, finished with a delicate light blue dial. Inspired by vintage luxury sportswear, the design features an intricate jacquard-etched dial, complete with a polished orb emblem at the 12 o'clock position, recalling Vivienne's vision of launching tradition into the future. Features a seven-link facetted braceletButterfly buckle fasteningHour markingsMaximum band circumference: 180mmSwiss movement2-year warranty cover5 ATM Water resistant Case size: 39mmPlease note that the watch band can be adjusted to a smaller length Code: 8053195833139",
        "시그니처 레이디 시드넘 워치를 이번 시즌 실버 톤 스테인리스 스틸 케이스와 브레이슬릿, 섬세한 라이트 블루 다이얼로 재해석했습니다. 빈티지 럭셔리 스포츠웨어에서 영감을 받은 자카드 에칭 다이얼과 12시 방향의 폴리시드 오브 엠블럼이, 전통을 미래로 이끄는 비비안의 비전을 떠올리게 합니다. 7링크 패싯 브레이슬릿·버터플라이 버클·아워 마커 / 최대 밴드 둘레 180mm / 스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 39mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8053195833139",
    ),
    (
        "The Audley watch in polished stainless steel features a sculptural pebble-shaped case, complemented by a sleek bangle-style bracelet. The tonal sunray dial is accented with the house’s raised orb motif and tonal hour markers, reflecting Vivienne’s vision of launching tradition for the future. Features a bangle-style strapPolished finishSunray dialPebble-shaped caseTortoiseshell patternSwiss movement2-year warranty cover5 ATM Water resistant Case size: 22mm Code: 8053195833115",
        "폴리시드 스테인리스 스틸의 오들리 워치는 조각적인 페블 셰이프 케이스와 슬릭한 뱅글 스타일 브레이슬릿이 조화를 이룹니다. 톤온톤 선레이 다이얼에는 하우스의 입체 오브 모티프와 톤온톤 아워 마커가 더해져, 전통을 미래로 이끄는 비비안의 비전을 담았습니다. 뱅글 스트랩·폴리시드 피니시·선레이 다이얼·페블 케이스·토토이즈셸 패턴·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 22mm. 코드: 8053195833115",
    ),
    (
        "The Audley watch in gold-tone stainless steel features a sculptural pebble-shaped case, complemented by a sleek bangle-style bracelet. The tonal sunray dial is accented with the house’s raised orb motif and tonal hour markers, reflecting Vivienne’s vision of launching tradition for the future. Features a bangle-style strapPolished gold-tone finishSunray dialPebble-shaped caseTortoiseshell patternSwiss movement2-year warranty cover5 ATM Water resistant Case size: 22mm Code: 8053195833122",
        "골드 톤 스테인리스 스틸의 오들리 워치는 조각적인 페블 셰이프 케이스와 슬릭한 뱅글 스타일 브레이슬릿이 조화를 이룹니다. 톤온톤 선레이 다이얼에는 하우스의 입체 오브 모티프와 톤온톤 아워 마커가 더해져, 전통을 미래로 이끄는 비비안의 비전을 담았습니다. 뱅글 스트랩·폴리시드 골드 톤·선레이 다이얼·페블 케이스·토토이즈셸 패턴·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 22mm. 코드: 8053195833122",
    ),
    (
        "The Audley watch in gold-tone stainless steel features a sculptural tortoiseshell pebble-shaped case, set on a sleek bangle-style strap. The deep brown sunray dial is adorned with the house’s raised orb motif and tonal hour markers, embodying Vivienne's vision of launching tradition into the future. Features a bangle-style strapPolished gold-tone finishSunray dialPebble-shaped caseTortoiseshell patternSwiss movement2-year warranty cover5 ATM Water resistant Case size: 24mm Code: 8053195833092",
        "골드 톤 스테인리스 스틸의 오들리 워치는 조각적인 토토이즈셸 페블 케이스와 슬릭한 뱅글 스트랩으로 완성됩니다. 딥 브라운 선레이 다이얼에는 하우스의 입체 오브 모티프와 톤온톤 아워 마커가 더해져, 전통을 미래로 이끄는 비비안의 비전을 담았습니다. 뱅글 스트랩·폴리시드 골드 톤·선레이 다이얼·페블 케이스·토토이즈셸 패턴·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 24mm. 코드: 8053195833092",
    ),
    (
        "Our Fenchurch watch features a sculpted three-link bracelet and stainless steel case, reimagined in polished silver tones and detailed with a mint sunray-brushed dial. Named after London's historic financial district, which resonated with Vivienne, the design features a date window at the three o'clock position and the house's signature orb emblem at the top of the dial, complete with an orb-shaped detail on the second hand. Features a round facePolished platingSwiss movement2-year warranty cover5 ATM Water resistant Case size: 28mmPlease note that the watch band can be adjusted to a smaller length Code: 8053195833184",
        "펜처치 워치는 조각적인 3링크 브레이슬릿과 스테인리스 스틸 케이스를 폴리시드 실버 톤으로 재해석하고, 민트 선레이 브러시 다이얼로 포인트를 줬습니다. 비비안이 애정한 런던의 역사적인 금융 지구에서 이름을 따왔으며, 3시 방향 날짜창과 다이얼 상단의 시그니처 오브 엠블럼, 초침의 오브 디테일로 완성됩니다. 라운드 페이스·폴리시드 도금·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 28mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8053195833184",
    ),
    (
        "Our Fenchurch watch features a sculpted three-link bracelet and stainless steel case, reimagined in polished gold tones and detailed with a champagne sunray-brushed dial. Named after London's historic financial district, which resonated with Vivienne, the design features a date window at the three o'clock position and the house's signature orb emblem at the top of the dial, complete with an orb-shaped detail on the second hand. Features a round facePolished platingSwiss movement2-year warranty cover5 ATM Water resistant Case size: 28mmPlease note that the watch band can be adjusted to a smaller length Code: 8053195833191",
        "펜처치 워치는 조각적인 3링크 브레이슬릿과 스테인리스 스틸 케이스를 폴리시드 골드 톤으로 재해석하고, 샴페인 선레이 브러시 다이얼로 포인트를 줬습니다. 비비안이 애정한 런던의 역사적인 금융 지구에서 이름을 따왔으며, 3시 방향 날짜창과 다이얼 상단의 시그니처 오브 엠블럼, 초침의 오브 디테일로 완성됩니다. 라운드 페이스·폴리시드 도금·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 28mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8053195833191",
    ),
    (
        "Our limited-edition watch is expertly crafted with this season's 'The Spring Cherubs' artwork, inspired by Boucher's painting, 'Spring, from a series of the Four Seasons', depicting cherubs playing with garlands of flowers. Complete with specialist Swiss movement, the design is framed by a halo of glistening crystals set into the bezel, finished with crystal-set hour markers and polished gold-tone hardware. Features a limited-edition presentation sleeveOrb motif seconds handSleek link bracelet designCrystal-set hour markersSpecialist Swiss movement2-year warranty cover5 ATM Water resistant Case size: 38mmMaximum band circumference: 180mmPlease note that the watch band can be adjusted to a smaller lengthCredit: Chateau de Fontainebleau, Seine-et-Marne, France/Bridgeman Images Code: 8050164232009",
        "이번 시즌 한정 에디션 워치는 부셰의 ‘사계절’ 연작 중 〈봄〉에서 영감을 받은 ‘스프링 커럽’ 아트워크를 정교하게 담았습니다. 꽃다발을 가지고 노는 천사들의 장면이 돋보이며, 스위스 무브먼트와 함께 베젤을 감싸는 크리스탈 헤일로, 크리스탈 아워 마커, 폴리시드 골드 톤 하드웨어로 완성됩니다. 한정 프레젠테이션 슬리브·오브 모티프 초침·슬릭 링크 브레이슬릿·크리스탈 아워 마커·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 38mm / 최대 밴드 둘레 180mm. 밴드 길이는 더 짧게 조절할 수 있습니다. Credit: Chateau de Fontainebleau, Seine-et-Marne, France/Bridgeman Images. 코드: 8050164232009",
    ),
    (
        "Our Chelsea watch draws inspiration from the historic Chelsea Barracks, embodying a refined equestrian elegance. The design is accented with engraved house branding along the brushed bezel and fastened with a butterfly clasp closure. The sand-blasted dial lends a soft, matte texture, creating an elegant contrast against the lustrous gold-toned stainless steel finish. Features a logo-etched bezelHour markersQuartz movementSand-blasted dialRound, brushed caseButterfly buckle claspCase size 31mm2-year warranty cover5 ATM Water resistant Strap width: 14mmWeight (not including packaging): 85.5g Please note that the watch band can be adjusted to a smaller length Code: 8050164232078",
        "첼시 워치는 역사적인 첼시 배럭스에서 영감을 받아, 세련된 승마풍 우아함을 담았습니다. 브러시드 베젤에 하우스 브랜딩이 새겨져 있고 버터플라이 클래스로 여닫습니다. 샌드블라스트 다이얼의 부드러운 매트 질감이 골드 톤 스테인리스 스틸의 광택과 우아하게 대비됩니다. 로고 에칭 베젤·아워 마커·쿼츠 무브먼트·샌드블라스트 다이얼·라운드 브러시 케이스·버터플라이 버클 / 케이스 31mm / 2년 보증 / 5ATM 방수 / 스트랩 폭 14mm / 무게 약 85.5g(패키지 제외). 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8050164232078",
    ),
    (
        "Our Aldgate watch draws inspiration from one of London’s most distinctive landmarks, The Gherkin, offering a three dimensional quilted-effect dial that echoes the building’s architectural form. The rotating seconds hand takes the shape of the house’s orb motif, while pyramid shaped studs feature as as hour markers, recalling Vivienne’s signature punk aesthetic. Features quartz movementRound, brushed caseButterfly buckle claspSilver-tone platingEtched branding around the octagonal bezel2-year warranty cover5 ATM Water resistant Strap width: 21mmWeight (not including packaging): 121g Case size 35 mmPlease note that the watch band can be adjusted to a smaller length Code: 8050164232030",
        "올드게이트 워치는 런던의 상징적 랜드마크 ‘거킨’에서 영감을 받아, 건축적 형태를 떠올리게 하는 입체 퀼티드 이펙트 다이얼을 선보입니다. 초침은 하우스 오브 모티프 형태이며, 피라미드형 스터드 아워 마커가 비비안 시그니처 펑크 감성을 상기시킵니다. 쿼츠 무브먼트·라운드 브러시 케이스·버터플라이 버클·실버 톤 도금·옥타고널 베젤 에칭 브랜딩 / 2년 보증 / 5ATM 방수 / 스트랩 폭 21mm / 무게 약 121g / 케이스 35mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8050164232030",
    ),
    (
        "The Tavistock watch draws inspiration from 1930s luxury timepieces, featuring a pan-shaped dial embellished with crystals and classic Roman hour markers. The design is highlighted by a brushed silver-toned case, set in a double-domed lens, and finished with a tapered ‘H-link’ bracelet crafted from stainless steel. Features a polished bezelHour markersCrystal detailingQuartz movementDouble domed lens Pan-shaped dialRound, brushed caseButterfly buckle claspCase size 28mm2-year warranty cover5 ATM Water resistant Strap width: 18mmWeight (not including packaging): 87g Please note that the watch band can be adjusted to a smaller length Code: 8050164232108",
        "태비스톡 워치는 1930년대 럭셔리 타임피스에서 영감을 받아, 크리스탈과 클래식 로마 아워 마커로 장식된 팬 셰이프 다이얼을 선보입니다. 브러시드 실버 톤 케이스와 더블 돔 렌즈, 스테인리스 스틸의 테이퍼드 H링크 브레이슬릿으로 완성됩니다. 폴리시드 베젤·아워 마커·크리스탈 디테일·쿼츠 무브먼트·더블 돔 렌즈·팬 다이얼·라운드 브러시 케이스·버터플라이 버클 / 케이스 28mm / 2년 보증 / 5ATM 방수 / 스트랩 폭 18mm / 무게 약 87g. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8050164232108",
    ),
    (
        "Named after London’s historic haberdashery street, the Berwick watch features a spirograph-textured dial overlaid with scattered safety pin motifs, evoking Vivienne’s signature punk aesthetic. The design is framed by a brushed and polished case, etched with ‘Vivienne Westwood Since 1971’ branding, honouring the year the house was founded. Features a logo-etched bezelHour markersQuartz movementDouble domed lens Colour-infilled crown Luminescent dialRound, brushed caseButterfly buckle claspCase size 37 mm2-year warranty cover5 ATM Water resistant Strap width: 20mmWeight (not including packaging): 116g Please note that the watch band can be adjusted to a smaller length Code: 8050164232061",
        "런던의 역사적인 하버대셔리 거리에서 이름을 딴 버윅 워치는, 스피로그래프 텍스처 다이얼 위에 흩어진 세이프티 핀 모티프로 비비안 시그니처 펑크 감성을 표현합니다. 브러시와 폴리시가 교차하는 케이스는 ‘Vivienne Westwood Since 1971’ 에칭으로 하우스 창립의 해를 기립니다. 로고 에칭 베젤·아워 마커·쿼츠 무브먼트·더블 돔 렌즈·컬러 인필 크라운·야광 다이얼·라운드 브러시 케이스·버터플라이 버클 / 케이스 37mm / 2년 보증 / 5ATM 방수 / 스트랩 폭 20mm / 무게 약 116g. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8050164232061",
    ),
    (
        "The design of our Little Wallace watch recalls the interiors of the Wallace Collection, complete with a gold-toned metal bracelet, Swarovski crystal details and an intricate jacquard-etched dial. The piece is branded with an orb-adorned second hand and crown, synonymous with Vivienne's vision of launching tradition into the future. Features gold-tone platingSleek braceletHour markersSwiss movement2-year warranty cover5 ATM Water resistant Case size: 32mmPlease note that the watch band can be adjusted to a smaller length Code: 8050164231125",
        "리틀 월리스 워치는 월리스 컬렉션의 인테리어를 떠올리게 하는 디자인으로, 골드 톤 메탈 브레이슬릿과 스와로브스키 크리스탈 디테일, 섬세한 자카드 에칭 다이얼이 돋보입니다. 오브가 장식된 초침과 크라운은 전통을 미래로 이끄는 비비안의 비전을 상징합니다. 골드 톤 도금·슬릭 브레이슬릿·아워 마커·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 32mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8050164231125",
    ),
    (
        "Our Little Wallace watch features a light pink jacquard-etched dial, inspired by the delicate pastel tones of 'The Swing' (1767) by Jean-Honoré Fragonard, housed at London’s Wallace Collection. The timepiece is framed by a silver-tone metal case and bracelet, elegantly adorned with a halo of shimmering Swarovski crystal embellishments. Features silver-tone platingSleek braceletHour markersQuartz movementRound, brushed caseButterfly buckle clasp2-year warranty cover5 ATM Water resistant Case size: 32mmStrap width: 16mmWeight (not including packaging): 77g Please note that the watch band can be adjusted to a smaller length Code: 8050164232023",
        "리틀 월리스 워치는 런던 월리스 컬렉션에 소장된 장오노레 프라고나르의 〈그네〉(1767)의 섬세한 파스텔 톤에서 영감을 받은 라이트 핑크 자카드 에칭 다이얼이 특징입니다. 실버 톤 메탈 케이스와 브레이슬릿을 반짝이는 스와로브스키 크리스탈 헤일로가 우아하게 감쌉니다. 실버 톤 도금·슬릭 브레이슬릿·아워 마커·쿼츠 무브먼트·라운드 브러시 케이스·버터플라이 버클 / 2년 보증 / 5ATM 방수 / 케이스 32mm / 스트랩 폭 16mm / 무게 약 77g. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8050164232023",
    ),
    (
        "Inspired by the infamous Wallace Collection in London, the Little Wallace watch features a light blue jacquard-etched dial, echoing the delicate hues of Jean-Honoré Fragonard’s artwork, 'The Swing'. The timepiece features a silver-toned metal bracelet and case, delicately adorned with shimmering white Swarovski crystal embellishments. Features silver-tone platingSleek braceletHour markersQuartz movementRound, brushed caseButterfly buckle clasp2-year warranty cover5 ATM Water resistant Case size: 32mmStrap width: 16mmWeight (not including packaging): 77g Please note that the watch band can be adjusted to a smaller length Code: 8050164231149",
        "런던 월리스 컬렉션에서 영감을 받은 리틀 월리스 워치는, 장오노레 프라고나르 〈그네〉의 섬세한 색감을 닮은 라이트 블루 자카드 에칭 다이얼이 돋보입니다. 실버 톤 메탈 브레이슬릿과 케이스에 반짝이는 화이트 스와로브스키 크리스탈이 섬세하게 더해집니다. 실버 톤 도금·슬릭 브레이슬릿·아워 마커·쿼츠 무브먼트·라운드 브러시 케이스·버터플라이 버클 / 2년 보증 / 5ATM 방수 / 케이스 32mm / 스트랩 폭 16mm / 무게 약 77g. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8050164231149",
    ),
    (
        "The Little Wallace watch is named after the infamous Wallace Collection in London, recalling Vivienne's admiration for art. The piece offers a green jacquard-etched dial, inspired by Jean-Honoré Fragonard’s 'The Swing', a masterpiece housed within the collection, complete with a gold-toned metal bracelet and Swarovski crystal details. Features gold-tone platingSleek braceletCrystal detailingHour markersSwiss movementButterfly buckle claspCase size: 32mm2-year warranty cover5 ATM Water resistantStrap width: 16mmWeight (not including packaging): 77g Please note that the watch band can be adjusted to a smaller lengthPlease note that the watch band can be adjusted to a smaller length Code: 8050164231132",
        "리틀 월리스 워치는 런던 월리스 컬렉션에서 이름을 따왔으며, 예술을 사랑한 비비안의 시선을 떠올리게 합니다. 컬렉션 소장작 장오노레 프라고나르 〈그네〉에서 영감을 받은 그린 자카드 에칭 다이얼과 골드 톤 메탈 브레이슬릿, 스와로브스키 크리스탈 디테일로 완성됩니다. 골드 톤 도금·슬릭 브레이슬릿·크리스탈 디테일·아워 마커·스위스 무브먼트·버터플라이 버클 / 케이스 32mm / 2년 보증 / 5ATM 방수 / 스트랩 폭 16mm / 무게 약 77g. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8050164231132",
    ),
    (
        "The design of our Wallace watch echoes the interiors of the Wallace Collection, complete with a gold-toned bracelet, Swarovski crystal details and an intricate jacquard-etched dial. The piece receives an orb motif at the twelve o'clock position, synonymous with Vivienne's vision of launching tradition into the future. Features a gold-tone platingSleek braceletOrb-detailed dialQuartz movementHour markersSwiss movement2-year warranty cover5 ATM Water resistant Case size: 38mmMaximum band circumference: 180mmPlease note that the watch band can be adjusted to a smaller length Code: 8050568621317",
        "월리스 워치는 월리스 컬렉션의 인테리어를 연상시키는 디자인으로, 골드 톤 브레이슬릿과 스와로브스키 크리스탈, 섬세한 자카드 에칭 다이얼이 조화를 이룹니다. 12시 방향의 오브 모티프는 전통을 미래로 이끄는 비비안의 비전을 상징합니다. 골드 톤 도금·슬릭 브레이슬릿·오브 디테일 다이얼·쿼츠·아워 마커·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 38mm / 최대 밴드 둘레 180mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8050568621317",
    ),
    (
        "The Little Camberwell is named after the London borough that houses Goldsmiths College, where Vivienne studied. Featuring a circular date window positioned at the three o'clock position, this timepiece offers a purple dial and a chain-link strap that fastens with a secure butterfly buckle. Features a round facePolished platingCase size: 29mmMaximum band circumference: 180mmThis watch comes in a gift box and has a two-year guaranteePlease note that the watch band can be adjusted to a smaller length Code: 8057555435735",
        "리틀 캠버웰은 비비안이 수학한 골드스미스 칼리지가 있는 런던의 자치구에서 이름을 따왔습니다. 3시 방향의 원형 날짜창, 퍼플 다이얼, 버터플라이 버클로 고정되는 체인 링크 스트랩이 특징입니다. 라운드 페이스·폴리시드 도금 / 케이스 29mm / 최대 밴드 둘레 180mm / 기프트 박스 포함 / 2년 보증. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8057555435735",
    ),
    (
        "A miniature version of the popular Camberwell watch, the Little Camberwell watch is named after the famous London borough, which Vivienne was fond of. The piece offers a circular date window at the three o'clock position, complete with a brushed dial and a polished orb plaque - synonymous with Vivienne's vision of launching tradition into the future. Features gold-tone platingRound faceStud markersPolished platingSwiss movement2-year warranty cover5 ATM Water resistant Case size: 29mmMaximum band circumference: 180mmPlease note that the watch band can be adjusted to a smaller length Code: 8050164230364",
        "인기 캠버웰 워치의 미니어처 버전인 리틀 캠버웰은 비비안이 사랑한 런던의 유명 자치구에서 이름을 따왔습니다. 3시 방향 원형 날짜창과 브러시드 다이얼, 폴리시드 오브 플레이크가 전통을 미래로 이끄는 비전을 상징합니다. 골드 톤 도금·라운드 페이스·스터드 마커·폴리시드 도금·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 29mm / 최대 밴드 둘레 180mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8050164230364",
    ),
    (
        "A miniature version of our popular Camberwell watch, the Little Camberwell watch is named after the famous London borough, which Vivienne was fond of. The piece adopts a circular date window at the three o'clock position, complete with a brushed dial and a polished orb plaque - synonymous with Vivienne's vision of launching tradition into the future. Features a round faceStud markersPolished platingSwiss movement2-year warranty cover5 ATM Water resistant Case size: 29mmMaximum band circumference: 180mmPlease note that the watch band can be adjusted to a smaller length Code: 8057555435728",
        "인기 캠버웰 워치의 미니어처 버전인 리틀 캠버웰은 비비안이 사랑한 런던의 유명 자치구에서 이름을 따왔습니다. 3시 방향 원형 날짜창과 브러시드 다이얼, 폴리시드 오브 플레이크가 전통을 미래로 이끄는 비전을 상징합니다. 라운드 페이스·스터드 마커·폴리시드 도금·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 29mm / 최대 밴드 둘레 180mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8057555435728",
    ),
    (
        "A scaled-down take on our popular Camberwell design, the Little Camberwell watch returns this season in a champagne-toned gold finish. Named after the London borough dear to Vivienne, the watch features a brushed dial, a polished Orb plaque, and a circular date window at the three o’clock position - echoing the house’s ethos of propelling the past into the future. Features a round faceStud markersPolished platingSwiss movement2-year warranty cover5 ATM Water resistant Case size: 29mmMaximum band circumference: 180mmPlease note that the watch band can be adjusted to a smaller length Code: 8050164231835",
        "인기 캠버웰 디자인을 축소한 리틀 캠버웰 워치가 이번 시즌 샴페인 톤 골드 피니시로 돌아왔습니다. 비비안이 아끼던 런던 자치구에서 이름을 따왔으며, 브러시드 다이얼과 폴리시드 오브 플레이크, 3시 방향 원형 날짜창이 과거를 미래로 이끄는 하우스 정신을 담습니다. 라운드 페이스·스터드 마커·폴리시드 도금·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 29mm / 최대 밴드 둘레 180mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8050164231835",
    ),
    (
        "A miniature version of our popular Camberwell watch, the Little Camberwell watch is named after the famous London borough, which Vivienne was fond of. The piece adopts a circular date window at the three o'clock position, complete with a brushed dial and a polished orb plaque - synonymous with Vivienne's vision of launching tradition into the future. Features a round facePolished platingStud markers Swiss movement2-year warranty cover5 ATM Water resistant Case size: 29mmMaximum band circumference: 180mmPlease note that the watch band can be adjusted to a smaller length Code: 8057555435711",
        "인기 캠버웰 워치의 미니어처 버전인 리틀 캠버웰은 비비안이 사랑한 런던의 유명 자치구에서 이름을 따왔습니다. 3시 방향 원형 날짜창과 브러시드 다이얼, 폴리시드 오브 플레이크가 전통을 미래로 이끄는 비전을 상징합니다. 라운드 페이스·폴리시드 도금·스터드 마커·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 29mm / 최대 밴드 둘레 180mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8057555435711",
    ),
    (
        "The Camberwell watch is named after the borough in south London, known for its art markets and Goldsmiths College. The piece adopts an oval date window, complete with stud details at the hour markers - reminiscent of the house's signature punk style. Features silver-tone plating Round faceOrb detailSwiss movement2-year warranty cover5 ATM Water resistant Case size: 37mmMaximum band circumference: 180mmPlease note that the watch band can be adjusted to a smaller length Code: 8057555418141",
        "캠버웰 워치는 아트 마켓과 골드스미스 칼리지로 유명한 남런던 자치구에서 이름을 따왔습니다. 타원형 날짜창과 아워 마커의 스터드 디테일이 하우스 시그니처 펑크 스타일을 연상시킵니다. 실버 톤 도금·라운드 페이스·오브 디테일·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 37mm / 최대 밴드 둘레 180mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8057555418141",
    ),
    (
        "A miniature take on our popular Seymour design, the Little Seymour watch is named after the former Seymour family townhouse - now home to the renowned Wallace Collection. Featuring a silver-tone profile and pink brushed dial, the watch is finished with a five-link bracelet and a distinctive pyramid-edged bezel. Features a push button butterfly clasp Hour markersCrown detailSwiss movement2-year warranty cover5 ATM Water resistant Case size: 32mmPlease note that the watch band can be adjusted to a smaller length Code: 8050164231842",
        "인기 시모어 디자인을 축소한 리틀 시모어 워치는, 현재 월리스 컬렉션이 자리한 옛 시모어 가문의 타운하우스에서 이름을 따왔습니다. 실버 톤 프로파일과 핑크 브러시드 다이얼에 5링크 브레이슬릿과 피라미드 엣지 베젤이 더해집니다. 푸시 버튼 버터플라이 클래스·아워 마커·크라운 디테일·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 32mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8050164231842",
    ),
    (
        "A miniature take on our popular Seymour design, the Little Seymour watch is named after the former Seymour family townhouse - now home to the renowned Wallace Collection. Featuring a gold-tone profile and an olive brushed dial, the watch is finished with a five-link bracelet and a distinctive pyramid-edged bezel. Features a push button butterfly clasp Hour markersCrown detailSwiss movement2-year warranty cover5 ATM Water resistant Case size: 32mmPlease note that the watch band can be adjusted to a smaller length Code: 8050164231859",
        "인기 시모어 디자인을 축소한 리틀 시모어 워치는, 현재 월리스 컬렉션이 자리한 옛 시모어 가문의 타운하우스에서 이름을 따왔습니다. 골드 톤 프로파일과 올리브 브러시드 다이얼에 5링크 브레이슬릿과 피라미드 엣지 베젤이 더해집니다. 푸시 버튼 버터플라이 클래스·아워 마커·크라운 디테일·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 32mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8050164231859",
    ),
    (
        "Named after the former townhouse of the Seymour family, where the infamous Wallace Collection is located, the Seymour watch features a gold-tone metal profile and this season's rose-coloured brushed dial. The design is complete with a two-tone Jubilee bracelet, set with a coin-edged bezel. Features a push button butterfly clasp Hour markersCrown detailSwiss movement2-year warranty cover5 ATM Water resistant Case size: 38mmMaximum band circumference: 180mmPlease note that the watch band can be adjusted to a smaller length Code: 8057555435698",
        "월리스 컬렉션이 자리한 옛 시모어 가문 타운하우스에서 이름을 딴 시모어 워치는, 골드 톤 메탈 프로파일과 이번 시즌의 로즈 컬러 브러시드 다이얼이 돋보입니다. 투톤 주빌리 브레이슬릿과 코인 엣지 베젤로 완성됩니다. 푸시 버튼 버터플라이 클래스·아워 마커·크라운 디테일·스위스 무브먼트 / 2년 보증 / 5ATM 방수 / 케이스 38mm / 최대 밴드 둘레 180mm. 밴드 길이는 더 짧게 조절할 수 있습니다. 코드: 8057555435698",
    ),
]


def expand_splits(en: str, ko: str, out: dict[str, str]) -> None:
    """Also seed sentence fragments produced by extract_detail_lines."""
    out[en] = ko
    # Mirror build-vw split heuristic so partial lines still hit cache.
    import re

    en_parts = [x.strip() for x in re.split(r"\n|\.(?=\s+[A-Z])", en) if x.strip()]
    ko_parts = [x.strip() for x in re.split(r"(?<=다)\s+|(?<=요)\s+| / ", ko) if x.strip()]
    # If counts match loosely, map 1:1; otherwise keep full-body only.
    if len(en_parts) >= 2 and abs(len(en_parts) - len(ko_parts)) <= 2 and len(ko_parts) >= 2:
        for e, k in zip(en_parts, ko_parts):
            if len(e) >= 20:
                out[e] = k


def main() -> None:
    cache: dict[str, str] = {}
    if CACHE.is_file():
        cache = json.loads(CACHE.read_text())
    seeded = 0
    for en, ko in {**SEED, **dict(DESCS)}.items():
        expand_splits(en, ko, cache)
        seeded += 1
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")
    print(f"seeded {seeded} watch strings into {CACHE}", flush=True)

    env = os.environ.copy()
    env.pop("BRIQ_FAST_BUILD", None)
    env["VW_LEAF_FILTER"] = "watches"
    env["PYTHONUNBUFFERED"] = "1"
    r = subprocess.run([sys.executable, "scripts/build-vw-catalog.py"], cwd=ROOT, env=env)
    raise SystemExit(r.returncode)


if __name__ == "__main__":
    main()
