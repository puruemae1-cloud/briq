import type { Product } from "@/data/product-types";

/**
 * NORQAIN sample catalogue.
 * Full import later: split by nq-wild-one / nq-independence / nq-adventure /
 * nq-freedom / nq-manufacture / nq-limited (official collection leaves).
 */
const IMG = "/products/nq-pdp/wild-one-skeleton-x-lite-turquoise";

/** Official GBP → KRW: pounds × 1800 × 1.1, round to ₩1,000. */
function krwFromGbp(gbp: number): number {
  return Math.round((gbp * 1800 * 1.1) / 1000) * 1000;
}

const GBP = 9700;
const PRICE = krwFromGbp(GBP);

const GALLERY = [
  `${IMG}/1.jpg`,
  `${IMG}/2.jpg`,
  `${IMG}/3.jpg`,
  `${IMG}/4.jpg`,
  `${IMG}/5.jpg`,
  `${IMG}/6.jpg`,
  `${IMG}/7.jpg`,
] as const;

export const nqCatalogProducts: Product[] = [
  {
    id: "nq-wild-one-skeleton-x-lite-turquoise",
    name: "Wild ONE Skeleton X-Lite Turquoise",
    nameKo: "와일드 원 스켈레톤 X-Lite · 터콰이즈",
    brand: "NORQAIN",
    price: PRICE,
    gbpPrice: GBP,
    category: "watches",
    subcategory: "nq-wild-one",
    tags: ["norqain", "nq-wild-one", "wild-one"],
    descriptionKo:
      "와일드 원 스켈레톤 X-Lite는 극한 퍼포먼스를 위해 설계된 멀티 머티리얼 컨셉 시계입니다. 30개 이상의 부품으로 이뤄진 복합 케이스에 충격 흡수 X-Lite 링과 NORTEQ®·티타늄·알루미늄을 조합했고, 무게는 약 45g에 불과합니다. 초경량 더블 레이어 러버 스트랩과 함께 착용감·내구성·내충격성을 동시에 챙긴 스위스 메이드 타임피스입니다. 오픈워크 스켈레톤 다이얼로 NORQAIN 4K 매뉴팩처 칼리버의 움직임을 그대로 보여 주며, 선명한 터콰이즈 포인트가 다이얼과 스트랩을 하나로 잇습니다.",
    image: GALLERY[0],
    images: [...GALLERY],
    hoverImage: GALLERY[1],
    accent: "#00B3A4",
    sku: "N3003.26X02.B07.R01",
    productCode: "N3003.26X02",
    sourceUrl:
      "https://norqain.com/products/wild-one-skeleton-x-lite-turquoise",
    inStock: true,
    registeredAt: "2026-11-02T12:00:00.000Z",
    editTier: "signature",
    featuresKo: [
      "약 45g 초경량 멀티 머티리얼 케이스 (NORTEQ® · 티타늄 · 알루미늄)",
      "충격 흡수 X-Lite 케이싱 링",
      "스켈레톤 다이얼로 무브먼트 개방",
      "NORQAIN 4K Manufacture Calibre",
      "방수 100m",
      "케이스 사이즈 41mm",
      "터콰이즈 X-Lite 러버 / 플렉스 스트랩 선택",
      "스위스 메이드 · Animal cruelty free 스트랩",
    ],
    techSpecs: [
      { labelKo: "컬렉션", valueKo: "Wild ONE Skeleton X-Lite" },
      { labelKo: "케이스", valueKo: "NORTEQ® · 티타늄 · 알루미늄 · 약 45g" },
      { labelKo: "사이즈", valueKo: "41mm" },
      { labelKo: "다이얼", valueKo: "스켈레톤 (오픈워크)" },
      { labelKo: "무브먼트", valueKo: "NORQAIN 4K Manufacture Calibre" },
      { labelKo: "방수", valueKo: "100m" },
      { labelKo: "스트랩", valueKo: "터콰이즈 Rubber X-Lite / Flex Strap X-Lite" },
      { labelKo: "원산지", valueKo: "스위스 메이드" },
      { labelKo: "SKU", valueKo: "N3003.26X02.B07.R01" },
    ],
    storySections: [
      {
        titleKo: "극한용 멀티 머티리얼 케이스",
        bodyKo:
          "케이스만 30개 이상의 부품으로 조립됩니다. 충격 흡수 X-Lite 링을 중심으로 NORTEQ®·티타늄·알루미늄을 배치해, 스포츠 워치에 필요한 강성과 초경량을 동시에 맞췄습니다. 손목 위에서는 존재감 있게, 착용감은 가볍게 느껴지도록 설계했습니다.",
        image: GALLERY[2],
      },
      {
        titleKo: "스켈레톤으로 드러나는 4K 칼리버",
        bodyKo:
          "다이얼을 열어 NORQAIN 4K 매뉴팩처 칼리버의 비트와 마감을 그대로 보여 줍니다. 터콰이즈 포인트가 기어트레인 사이로 스며들어, 테크니컬한 스켈레톤에 컬러 시그니처를 남깁니다.",
        image: GALLERY[0],
        reverse: true,
      },
      {
        titleKo: "X-Lite 스트랩 · 45g의 착용감",
        bodyKo:
          "더블 레이어 러버 구조의 X-Lite 스트랩은 케이스와 같은 초경량 철학을 이어 갑니다. Rubber X-Lite와 Flex Strap X-Lite 중 선택해, 아웃도어부터 데일리까지 같은 터콰이즈 톤으로 맞춰 착용할 수 있습니다.",
        image: GALLERY[4],
      },
      {
        titleKo: "100m 방수 · 야생을 위한 완성도",
        bodyKo:
          "방수 100m와 견고한 멀티 머티리얼 구조로 활동적인 환경에서도 안심하고 착용할 수 있습니다. NORQAIN이 추구하는 ‘your life, your way’를 손목 위에서 가장 가볍게 표현한 Wild ONE 라인의 X-Lite 해석입니다.",
        image: GALLERY[5],
        reverse: true,
      },
      {
        titleKo: "스위스 메이드 · 윤리적 소재",
        bodyKo:
          "스위스에서 조립·검수되는 메커니컬 워치입니다. 2021년부터 가죽 스트랩 신제품을 도입하지 않는 NORQAIN의 방침에 따라, 이 모델도 애니멀 크루얼티 프리 러버 스트랩을 사용합니다.",
        image: GALLERY[6],
      },
    ],
    variants: [
      {
        id: "n3003-26x02-b07-r01",
        name: "Turquoise Rubber X-Lite",
        nameKo: "터콰이즈 러버 X-Lite",
        sku: "N3003.26X02.B07.R01",
        gbpPrice: GBP,
        price: PRICE,
        image: GALLERY[0],
        images: [...GALLERY],
        sourceUrl:
          "https://norqain.com/products/wild-one-skeleton-x-lite-turquoise",
        inStock: true,
      },
      {
        id: "n3003-26x02-b07-f01",
        name: "Turquoise Flex Strap X-Lite",
        nameKo: "터콰이즈 플렉스 스트랩 X-Lite",
        sku: "N3003.26X02.B07.F01",
        gbpPrice: GBP,
        price: PRICE,
        image: GALLERY[0],
        images: [...GALLERY],
        sourceUrl:
          "https://norqain.com/products/wild-one-skeleton-x-lite-turquoise",
        inStock: true,
      },
    ],
  },
];

