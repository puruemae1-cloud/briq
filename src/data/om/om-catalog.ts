import type { Product } from "@/data/product-types";

/** Official GBP → KRW for DMR watches: pounds × 1900 × 1.16, round to ₩10,000. */
function krwFromDmrGbp(gbp: number): number {
  return Math.round((gbp * 1900 * 1.16) / 10000) * 10000;
}

const SKU_DIR = "seamaster-aqua-terra-41-22010412103007";
const PDP = `/products/om-pdp/${SKU_DIR}`;

/**
 * DMR (David M Robinson) watch sample catalogue.
 * Source: https://dmr.co.uk/collections/all-watches — brand / collection structure.
 */
const _omCatalogProducts: Product[] = [
  {
    id: "om-seamaster-aqua-terra-41-22010412103007",
    name: "OMEGA Seamaster Aqua Terra 150m Steel Chronometer 41mm",
    nameKo: "오메가 씨마스터 아쿠아 테라 150M 스틸 크로노미터 41mm",
    brand: "OMEGA",
    price: krwFromDmrGbp(6200),
    gbpPrice: 6200,
    category: "watches",
    subcategory: "om-seamaster",
    tags: ["omega", "om-seamaster", "dmr"],
    descriptionKo:
      "오메가 씨마스터 아쿠아 테라는 브랜드의 해양 유산을 기리며, 우아한 디자인과 정밀한 성능을 함께 담았습니다. 스테인리스 스틸로 제작된 41mm 모델은 대칭적인 케이스 실루엣과, 항해의 뿌리를 보여주는 웨이브 엣지 케이스백이 특징입니다.\n\n선브러시 블루 다이얼에는 럭셔리 요트 데크에서 영감을 받은 오메가 시그니처 가로 ‘티크’ 패턴이 새겨져 있습니다. 6시 방향 날짜창은 실용성을 더하고, 로듐 도금 핸즈와 인덱스에는 화이트 슈퍼루미노바가 채워져 어떤 조도에서도 시인성이 뛰어납니다.\n\n일체형 스테인리스 스틸 브레이슬릿은 폴리시 센터 링크와 브러시 아우터 링크의 대비로 세련된 마감을 완성합니다. 심장에는 METAS 인증을 받은 오메가 코액시얼 마스터 크로노미터 칼리버 8900이 탑재되어, 정확도·성능·내자성 모두에서 최고 수준의 기준을 충족합니다.\n\n모델 레퍼런스: 220.10.41.21.03.007",
    image: `${PDP}/1.jpg`,
    images: [
      `${PDP}/1.jpg`,
      `${PDP}/2.jpg`,
      `${PDP}/3.jpg`,
      `${PDP}/4.jpg`,
      `${PDP}/5.jpg`,
      `${PDP}/6.jpg`,
    ],
    hoverImage: `${PDP}/2.jpg`,
    accent: "#0B3A66",
    sku: "44-020252",
    productCode: "220.10.41.21.03.007",
    sourceUrl:
      "https://dmr.co.uk/products/omega-seamaster-aqua-terra-41mm-22010412103007",
    inStock: true,
    registeredAt: "2026-10-28T14:28:45Z",
    editTier: "signature",
    featuresKo: [
      "코액시얼 마스터 크로노미터 칼리버 8900",
      "METAS 인증 정확도·내자성",
      "스테인리스 스틸 41mm 케이스",
      "선브러시 블루 티크 패턴 다이얼",
      "6시 방향 날짜창",
      "로듐 도금 핸즈·인덱스 + 화이트 슈퍼루미노바",
      "일체형 스테인리스 스틸 브레이슬릿",
      "방수 150m",
      "파워리저브 약 60시간",
      "오토매틱(셀프와인딩)",
      "스위스 메이드",
    ],
    techSpecs: [
      { labelKo: "브랜드", valueKo: "OMEGA" },
      { labelKo: "컬렉션", valueKo: "씨마스터 아쿠아 테라" },
      { labelKo: "모델 레퍼런스", valueKo: "220.10.41.21.03.007" },
      { labelKo: "DMR SKU", valueKo: "44-020252" },
      { labelKo: "소재", valueKo: "스테인리스 스틸" },
      { labelKo: "스트랩", valueKo: "브레이슬릿" },
      { labelKo: "케이스 사이즈", valueKo: "41mm" },
      { labelKo: "다이얼 컬러", valueKo: "블루" },
      { labelKo: "방수", valueKo: "150m" },
      { labelKo: "칼리버", valueKo: "8900" },
      { labelKo: "파워리저브", valueKo: "60시간" },
      { labelKo: "무브먼트", valueKo: "오토매틱(셀프와인딩)" },
    ],
    storySections: [
      {
        titleKo: "해양 유산에서 온 우아함",
        bodyKo:
          "아쿠아 테라는 오메가의 해양 헤리티지를 기리며 우아한 디자인과 탁월한 정밀함을 결합합니다. 스테인리스 스틸 41mm 케이스는 대칭적인 실루엣을 유지하고, 웨이브 엣지 케이스백이 항해에서 비롯된 뿌리를 조용히 드러냅니다.",
        image: `${PDP}/story-1.jpg`,
      },
      {
        titleKo: "요트 데크에서 영감을 받은 블루 다이얼",
        bodyKo:
          "선브러시 블루 다이얼 위 가로 ‘티크’ 패턴은 럭셔리 요트의 나무 갑판에서 영감을 받았습니다. 6시 방향 날짜창과 화이트 슈퍼루미노바가 채워진 로듐 도금 핸즈·인덱스가 일상적인 가독성과 고급스러운 마감을 동시에 잡아 줍니다.",
        image: `${PDP}/story-2.jpg`,
        reverse: true,
      },
      {
        titleKo: "마스터 크로노미터 칼리버 8900",
        bodyKo:
          "심장에는 오메가 코액시얼 마스터 크로노미터 칼리버 8900이 자리합니다. METAS 인증으로 정확도·성능·자기장 저항성에서 최고 기준을 충족하며, 약 60시간의 파워리저브로 여유 있는 착용감을 제공합니다. 폴리시와 브러시가 교차된 일체형 스틸 브레이슬릿이 손목 위에서 마무리됩니다.",
        image: `${PDP}/story-3.jpg`,
      },
    ],
    variants: [
      {
        id: "om-220-10-41-21-03-007",
        name: "Blue teak dial / Steel bracelet",
        nameKo: "블루 티크 다이얼 / 스틸 브레이슬릿",
        sku: "44-020252",
        gbpPrice: 6200,
        price: krwFromDmrGbp(6200),
        image: `${PDP}/1.jpg`,
        images: [
          `${PDP}/1.jpg`,
          `${PDP}/2.jpg`,
          `${PDP}/3.jpg`,
          `${PDP}/4.jpg`,
          `${PDP}/5.jpg`,
          `${PDP}/6.jpg`,
        ],
        sourceUrl:
          "https://dmr.co.uk/products/omega-seamaster-aqua-terra-41mm-22010412103007",
        inStock: true,
      },
    ],
  },
];

export const omCatalogProducts: Product[] = _omCatalogProducts;
