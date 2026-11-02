import type { Product } from "@/data/product-types";

/**
 * NORQAIN sample catalogue.
 * Full import later: split by nq-wild-one / nq-independence / nq-adventure /
 * nq-freedom / nq-manufacture / nq-limited (official collection leaves).
 */
const IMG = "/products/nq-pdp/wild-one-skeleton-x-lite-turquoise";

/** CHF → KRW working rate for sample (round to ₩1,000). */
function krwFromChf(chf: number): number {
  return Math.round((chf * 1800) / 1000) * 1000;
}

const CHF = 9900;
const PRICE = krwFromChf(CHF);

export const nqCatalogProducts: Product[] = [
  {
    id: "nq-wild-one-skeleton-x-lite-turquoise",
    name: "Wild ONE Skeleton X-Lite Turquoise",
    nameKo: "와일드 원 스켈레톤 X-Lite · 터콰이즈",
    brand: "NORQAIN",
    price: PRICE,
    gbpPrice: CHF,
    category: "watches",
    subcategory: "nq-wild-one",
    tags: ["norqain", "nq-wild-one", "wild-one"],
    descriptionKo:
      "와일드 원 스켈레톤 X-Lite는 극한 퍼포먼스를 위해 설계된 멀티 머티리얼 컨셉 시계입니다. 30개 이상의 부품으로 이뤄진 케이스에 충격 흡수 X-Lite 링과 NORTEQ®·티타늄·알루미늄을 조합했으며, 무게는 약 45g에 불과합니다. 초경량 더블 레이어 러버 스트랩과 함께 착용감까지 챙긴 스위스 메이드 타임피스입니다.",
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
    hoverImage: `${IMG}/2.jpg`,
    accent: "#00B3A4",
    sku: "N3003.26X02.B07.R01",
    productCode: "N3003.26X02",
    sourceUrl:
      "https://norqain.com/products/wild-one-skeleton-x-lite-turquoise",
    inStock: true,
    registeredAt: "2026-11-02T12:00:00.000Z",
    editTier: "signature",
    techSpecs: [
      { labelKo: "케이스", valueKo: "NORTEQ® · 멀티 머티리얼 · 약 45g" },
      { labelKo: "다이얼", valueKo: "스켈레톤" },
      { labelKo: "무브먼트", valueKo: "NORQAIN 4K Manufacture Calibre" },
      { labelKo: "스트랩", valueKo: "터콰이즈 X-Lite 러버 / 플렉스" },
      { labelKo: "원산지", valueKo: "스위스 메이드" },
    ],
    storySections: [
      {
        titleKo: "극한용 멀티 머티리얼 케이스",
        bodyKo:
          "충격 흡수 X-Lite 케이싱 링과 NORTEQ®·티타늄·알루미늄을 조합한 복합 구조로, 스포츠 워치의 내구성과 초경량을 동시에 담았습니다.",
        image: `${IMG}/3.jpg`,
      },
      {
        titleKo: "스켈레톤 다이얼",
        bodyKo:
          "오픈워크 다이얼로 메커니컬 무브먼트의 움직임을 그대로 보여 줍니다. 터콰이즈 포인트가 다이얼과 스트랩을 하나로 잇습니다.",
        image: `${IMG}/4.jpg`,
        reverse: true,
      },
    ],
    variants: [
      {
        id: "n3003-26x02-b07-r01",
        name: "Turquoise Rubber X-Lite",
        nameKo: "터콰이즈 러버 X-Lite",
        sku: "N3003.26X02.B07.R01",
        gbpPrice: CHF,
        price: PRICE,
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
          "https://norqain.com/products/wild-one-skeleton-x-lite-turquoise",
        inStock: true,
      },
      {
        id: "n3003-26x02-b07-f01",
        name: "Turquoise Flex Strap X-Lite",
        nameKo: "터콰이즈 플렉스 스트랩 X-Lite",
        sku: "N3003.26X02.B07.F01",
        gbpPrice: CHF,
        price: PRICE,
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
          "https://norqain.com/products/wild-one-skeleton-x-lite-turquoise",
        inStock: true,
      },
    ],
  },
];
