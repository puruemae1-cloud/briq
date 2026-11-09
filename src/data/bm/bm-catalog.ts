import type { Product } from "@/data/product-types";

/**
 * Bremont Watch Company (Henley-on-Thames, UK).
 * Price formula: GBP × 1800 × 1.1, rounded to nearest ₩10,000.
 * Sample catalog — full import TBD after preview approval.
 */
const IMG =
  "/products/bm-pdp/supermarine-43mm-full-ceramic-deep-blue-leather-strap-watch";

function krwFromGbp(gbp: number): number {
  return Math.round((gbp * 1800 * 1.1) / 10000) * 10000;
}

const sampleGbp = 6450;
const sampleKrw = krwFromGbp(sampleGbp);

const _products: Product[] = [
  {
    id: "bm-supermarine-43mm-full-ceramic-deep-blue-leather-strap-watch",
    name: "Supermarine Full Ceramic Deep Blue Leather Strap",
    nameKo: "슈퍼마린 풀 세라믹 딥 블루 레더 스트랩",
    brand: "Bremont",
    price: sampleKrw,
    gbpPrice: sampleGbp,
    accent: "#0B1C3A",
    category: "watches",
    subcategory: "bm-supermarine",
    tags: ["bremont", "bm-supermarine", "bm-limited"],
    descriptionKo:
      "브레몽 슈퍼마린 풀 세라믹 딥 블루는 전 세계 250피스 한정 다이버 워치입니다. 500m 방수와 헬륨 이스케이프 밸브를 갖추고, 모노블록 블루 세라믹 케이스에 티타늄 이너 케이스, 널드 티타늄 단방향 베젤(블루 세라믹 인서트), 블랙 웨이브 이펙트 다이얼을 조합했습니다. 블루 엠보스 러버에 가죽 라이닝을 더한 퀵 릴리즈 스트랩으로 교체가 간편합니다. 헨리온템스 워크숍에서 핸드빌드·테스트되는 Made in UK 타임피스입니다.",
    image: `${IMG}/1.jpg`,
    images: [
      `${IMG}/1.jpg`,
      `${IMG}/2.jpg`,
      `${IMG}/3.jpg`,
      `${IMG}/4.jpg`,
      `${IMG}/5.jpg`,
      `${IMG}/6.jpg`,
      `${IMG}/7.jpg`,
      `${IMG}/8.jpg`,
      `${IMG}/9.jpg`,
    ],
    hoverImage: `${IMG}/2.jpg`,
    sku: "SM43-DT-BLCER-BK-L-S",
    productCode: "SM43-DT-BLCER-BK-L-S",
    sourceUrl:
      "https://www.bremont.com/products/supermarine-43mm-full-ceramic-deep-blue-leather-strap-watch",
    inStock: true,
    featuresKo: [
      "브레몽 정품 · Made in UK",
      "전 세계 250피스 한정",
      "43mm 모노블록 블루 세라믹 케이스",
      "티타늄 이너 케이스",
      "500m(50ATM) 방수 · 헬륨 이스케이프 밸브",
      "BB64AH 오토매틱 · 56시간 파워리저브",
      "슈퍼루미노바®(블루 발광) 인덱스·핸즈",
      "퀵 릴리즈 블루 엠보스 러버/레더 스트랩",
    ],
    techSpecs: [
      { labelKo: "브랜드", valueKo: "브레몽 (Bremont)" },
      { labelKo: "컬렉션", valueKo: "슈퍼마린 풀 세라믹" },
      { labelKo: "모델 레퍼런스", valueKo: "SM43-DT-BLCER-BK-L-S" },
      { labelKo: "원산지", valueKo: "Made in UK" },
      { labelKo: "무브먼트", valueKo: "BB64AH 오토매틱 · 25석 · 28,800bph · 56시간 파워리저브" },
      { labelKo: "기능", valueKo: "시·분·초 · 3시 방향 데이트 · 단방향 회전 베젤" },
      {
        labelKo: "케이스",
        valueKo:
          "블루 세라믹 + 티타늄 · Ø43mm · 길이 50mm · 두께 13mm · 러그 22mm",
      },
      {
        labelKo: "베젤",
        valueKo: "널드 티타늄 단방향 베젤 · 블루 세라믹 인서트",
      },
      {
        labelKo: "케이스백",
        valueKo: "PVD 블루 티타늄 스크류인 · 세계 대양 지도 각인",
      },
      {
        labelKo: "다이얼·핸즈",
        valueKo:
          "블랙 3D 웨이브 패턴 · 사다리꼴 인덱스 · 블랙 골드 핸즈 · 슈퍼루미노바®(블루)",
      },
      { labelKo: "크리스탈", valueKo: "돔형 반사방지 사파이어" },
      { labelKo: "방수", valueKo: "50ATM / 500m" },
      {
        labelKo: "스트랩",
        valueKo: "퀵 릴리즈 블루 엠보스 러버 & 레더 · 폭 22mm",
      },
      { labelKo: "무게", valueKo: "74g (헤드만)" },
      { labelKo: "취급", valueKo: "브레몽 영국 공식" },
    ],
    storySections: [
      {
        titleKo: "슈퍼마린 풀 세라믹 딥 블루",
        bodyKo:
          "슈퍼마린 풀 세라믹 딥 블루는 전 세계 250피스 한정으로, 브레몽 슈퍼마린 풀 세라믹 라인의 최신 챕터입니다. 바다와 얼음이 맞닿는 지점에서 영감을 받았으며, 가혹한 환경에서도 버틸 수 있도록 설계된 세라믹 블루 다이버 워치입니다.\n\n43mm 모노블록 블루 세라믹 케이스는 스크래치에 강하고 가벼우며, 티타늄 이너 케이스·헬륨 이스케이프 밸브·500m 방수를 갖춥니다. 널드 티타늄 단방향 베젤에는 블루 세라믹 인서트가 들어가고, 블랙 웨이브 다이얼의 사다리꼴 인덱스는 베젤에서 이어져 해군식 크로스헤어를 만듭니다. 데이트는 3시, 티타늄 케이스백에는 세계 대양 지도가 새겨져 있습니다.\n\nBB64AH 오토매틱(56시간 파워리저브)으로 구동되며, 브레몽 앰배서더 알도 케인(Aldo Kane)이 아이슬란드 빙하호와 빙하 위에서 테스트했습니다. 블루 엠보스 러버에 가죽 라이닝을 더한 스트랩으로 구성됩니다.",
        image: `${IMG}/8.jpg`,
        videoUrl: `${IMG}/story.mp4`,
        videoAudio: true,
        layout: "wide",
      },
      {
        titleKo: "슈퍼루미노바®",
        bodyKo:
          "인덱스와 핸즈에 슈퍼루미노바®(블루 발광)를 채워, 깊은 수중에서도 시인성을 확보합니다.",
        image: `${IMG}/3.jpg`,
      },
      {
        titleKo: "모노블록 블루 세라믹 케이스",
        bodyKo:
          "43mm 모노블록 블루 세라믹 케이스는 스크래치에 매우 강하고 가벼우며, 티타늄 이너 케이스와 조합됩니다.",
        image: `${IMG}/4.jpg`,
        reverse: true,
      },
      {
        titleKo: "세계 대양이 새겨진 케이스백",
        bodyKo:
          "PVD 블루 티타늄 케이스백에는 바다와 얼음이 만나는 지점에서 영감을 받은 세계 대양 지도가 각인되어 있습니다.",
        image: `${IMG}/5.jpg`,
      },
      {
        titleKo: "헬륨 이스케이프 밸브",
        bodyKo:
          "헬륨 이스케이프 밸브와 스크류다운 크라운으로 500m 방수를 지원합니다.",
        image: `${IMG}/6.jpg`,
        reverse: true,
      },
      {
        titleKo: "웨이브 이펙트 다이얼",
        bodyKo:
          "블랙 웨이브 다이얼 위 사다리꼴 인덱스가 베젤에서 이어져 해군에서 영감을 받은 크로스헤어를 형성합니다.",
        image: `${IMG}/7.jpg`,
      },
      {
        titleKo: "BB64AH 오토매틱 무브먼트",
        bodyKo:
          "BB64AH 오토매틱 무브먼트는 25석, 글루시뒤르 밸런스, 아나크론 밸런스 스프링, 니바플렉스 메인스프링, 28,800bph(4Hz), 56시간 파워리저브를 갖춥니다.",
        image: `${IMG}/9.jpg`,
        reverse: true,
      },
      {
        titleKo: "Proudly Made in the UK",
        bodyKo:
          "영국은 시계 제작 역사에서 수많은 혁신을 남긴 나라입니다. 브레몽은 헨리온템스 워크숍에서 모든 시계를 핸드빌드하고 출고 전 테스트를 마칩니다. 원산지 Made in UK.",
        image: `${IMG}/1.jpg`,
      },
    ],
    variants: [
      {
        id: "bm-supermarine-43mm-full-ceramic-deep-blue-leather-strap-watch-default",
        name: "Deep Blue Leather Strap",
        nameKo: "딥 블루 레더 스트랩",
        sku: "SM43-DT-BLCER-BK-L-S",
        gbpPrice: sampleGbp,
        price: sampleKrw,
        image: `${IMG}/1.jpg`,
        images: [
          `${IMG}/1.jpg`,
          `${IMG}/2.jpg`,
          `${IMG}/3.jpg`,
          `${IMG}/4.jpg`,
          `${IMG}/5.jpg`,
          `${IMG}/6.jpg`,
          `${IMG}/7.jpg`,
        ],
        sourceUrl:
          "https://www.bremont.com/products/supermarine-43mm-full-ceramic-deep-blue-leather-strap-watch",
        inStock: true,
      },
    ],
  },
];

export const bmCatalogProducts: Product[] = _products;
