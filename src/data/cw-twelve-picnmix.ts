/** Bracelet resize: No = free; any cm size = +₩25,000 */
export const CW_BRACELET_RESIZE_FEE = 25_000;

export const CW_BRACELET_SIZES_CM: string[] = (() => {
  const sizes: string[] = [];
  for (let cm = 135; cm <= 255; cm += 5) {
    sizes.push((cm / 10).toFixed(1));
  }
  return sizes;
})();

const STORY = [
  {
    titleKo: "달콤한 여름의 꿈",
    bodyKo:
      "올여름 가장 달콤한 시계를 고른다면, 트웰브 픽앤믹스를 빼놓을 수 없습니다. 트웰브(Ti) 36mm를 한층 과감하게 재해석한 모델로, 여섯 가지 그라데이션 컬러의 슈가 크리스털 다이얼이 눈길을 사로잡습니다.\n\n발랄한 비주얼 뒤에는 진지한 워치메이킹이 자리합니다. 크리스털 다이얼 위에 가지런히 앉은 슬림 인덱스와 트윈 플래그 로고, 그리고 야간에도 또렷한 루메 핸드셋까지—실용과 즐거움이 자연스럽게 만납니다.\n\n36mm의 초경량 그레이드 2 티타늄 케이스는 브러시·폴리시·샌드블라스트 마감으로 완성됩니다. 케이스백 사파이어에는 픽앤믹스 로고가 새겨져 있고, 그 너머로 Sellita SW300-1 COSC 오토매틱의 엘라보레 로터가 보입니다.\n\n컬러 매칭 러버 스트랩과 티타늄 트웰브 브레이슬릿이 함께 제공되며, 모두 CW 퀵릴리즈로 손쉽게 교체할 수 있습니다. COSC 인증 Sellita SW300-1은 56시간 파워리저브를 갖췄고, 스트라이프 픽앤믹스 페이퍼백에 담겨 도착합니다.",
    reverse: false,
  },
  {
    titleKo: "Sellita SW300-1 COSC 오토매틱",
    bodyKo:
      "2008년 출시된 Sellita의 25석 주얼 SW300-1 오토매틱은 스위스 워치메이킹에서 가장 신뢰받는 칼리버 중 하나입니다. 직경 25.6mm, 두께 3.6mm로 SW200-1보다 1mm 얇으며, 28,800vph(4Hz)로 작동하고 56시간 파워리저브를 제공합니다. ETA 2892-A2의 대안으로 평가받으며, 데이트·문페이즈·GMT 등 다양한 컴플리케이션으로 커스터마이즈할 수 있습니다.",
    image: "/products/cw-twelve-picnmix/story/movement.webp",
    imageAlt: "Sellita SW300-1 COSC 무브먼트",
    reverse: true,
  },
  {
    titleKo: "슈가 크리스털 다이얼",
    bodyKo:
      "여섯 가지 고채도 컬러로 완성된 바삭한 슈가 크리스털 다이얼. 셰벗 분수와 콜라 큐브를 떠올리게 하는 텍스처가 여름 특유의 발랄함을 전합니다.",
    image: "/products/cw-twelve-picnmix/story/dial.webp",
    imageAlt: "슈가 크리스털 다이얼 디테일",
  },
  {
    titleKo: "전시형 케이스백",
    bodyKo:
      "사파이어 전시형 케이스백에 새겨진 픽앤믹스 프린트가 무브먼트의 아름다움을 한층 더 특별하게 만듭니다.",
    image: "/products/cw-twelve-picnmix/story/caseback.webp",
    imageAlt: "픽앤믹스 케이스백",
    reverse: true,
  },
  {
    titleKo: "36mm 티타늄 케이스",
    bodyKo:
      "그레이드 2 티타늄의 12면체 케이스를 브러시·폴리시·샌드블라스트 세 가지 방식으로 마감했습니다. 초경량이면서도 견고해 어떤 손목에도 편안하게 어울립니다.\n\n각 시계는 스트라이프 픽앤믹스 페이퍼백과 함께 패키징되어 도착합니다.",
    image: "/products/cw-twelve-picnmix/story/case.webp",
    imageAlt: "36mm 티타늄 케이스",
  },
  {
    titleKo: "픽앤믹스 패키징",
    bodyKo:
      "시계와 함께 제공되는 스트라이프 픽앤믹스 페이퍼백이 언박싱 순간부터 달콤한 분위기를 완성합니다.",
    image: "/products/cw-twelve-picnmix/story/packaging.webp",
    imageAlt: "픽앤믹스 패키징",
    reverse: true,
  },
] as const;

type Flavor = {
  slug: string;
  sku: string;
  nameEn: string;
  nameKo: string;
  accent: string;
  sourceUrl: string;
  blurbKo: string;
};

const FLAVORS: Flavor[] = [
  {
    slug: "kola-krystals",
    sku: "C12-36AHC1-T00K0-B0R",
    nameEn: "Kola Krystals",
    nameKo: "콜라 크리스털",
    accent: "#5C3A2E",
    sourceUrl:
      "https://www.christopherward.com/watches/the-twelve-%28ti%29-pic%27n%27mix/C12-36AHC1-T00K0-B0R.html",
    blurbKo:
      "콜라 큐브를 떠올리게 하는 따뜻한 브라운 톤의 슈가 크리스털 다이얼. 컬러 매칭 러버 스트랩과 티타늄 브레이슬릿이 함께 제공됩니다.",
  },
  {
    slug: "orange-fizz",
    sku: "C12-36AHC1-T00O0-B0R",
    nameEn: "Orange Fizz",
    nameKo: "오렌지 피즈",
    accent: "#D4652A",
    sourceUrl:
      "https://www.christopherward.com/watches/the-twelve-%28ti%29-pic%27n%27mix/C12-36AHC1-T00O0-B0R.html",
    blurbKo:
      "상큼한 오렌지 피즈처럼 톡 쏘는 그라데이션 다이얼. 36mm 그레이드 2 티타늄 케이스와 COSC 인증 오토매틱이 조화를 이룹니다.",
  },
  {
    slug: "berry-burst",
    sku: "C12-36AHC1-T00P1-B0R",
    nameEn: "Berry Burst",
    nameKo: "베리 버스트",
    accent: "#8B2E5B",
    sourceUrl:
      "https://www.christopherward.com/watches/the-twelve-%28ti%29-pic%27n%27mix/C12-36AHC1-T00P1-B0R.html",
    blurbKo:
      "잘 익은 베리처럼 깊고 화사한 핑크-퍼플 그라데이션. 한정 50피스의 여름 한정 에디션입니다.",
  },
  {
    slug: "blue-sherbet",
    sku: "C12-36AHC1-T00B1-B0R",
    nameEn: "Blue Sherbet",
    nameKo: "블루 셔벗",
    accent: "#2A6B8A",
    sourceUrl:
      "https://www.christopherward.com/watches/the-twelve-%28ti%29-pic%27n%27mix/C12-36AHC1-T00B1-B0R.html",
    blurbKo:
      "시원한 블루 셔벗을 연상시키는 크리스털 다이얼. 퀵릴리즈 러버 스트랩과 티타늄 브레이슬릿으로 스타일을 자유롭게 바꿀 수 있습니다.",
  },
  {
    slug: "cherry-pop",
    sku: "C12-36AHC1-T00R0-B0R",
    nameEn: "Cherry Pop",
    nameKo: "체리 팝",
    accent: "#B8202E",
    sourceUrl:
      "https://www.christopherward.com/watches/the-twelve-%28ti%29-pic%27n%27mix/C12-36AHC1-T00R0-B0R.html",
    blurbKo:
      "체리 팝처럼 선명한 레드 그라데이션 다이얼. 루메 핸드셋으로 밤에도 또렷한 가독성을 유지합니다.",
  },
  {
    slug: "apple-sour",
    sku: "C12-36AHC1-T00V1-B0R",
    nameEn: "Apple Sour",
    nameKo: "애플 사워",
    accent: "#3D7A3A",
    sourceUrl:
      "https://www.christopherward.com/watches/the-twelve-%28ti%29-pic%27n%27mix/C12-36AHC1-T00V1-B0R.html",
    blurbKo:
      "새콤한 그린 애플을 담은 상큼한 다이얼. 초경량 티타늄 케이스로 데일리 착용감까지 챙겼습니다.",
  },
];

const PRICE = 3_970_000;

function galleryFor(slug: string): string[] {
  return [1, 2, 3, 4, 5, 6, 7].map(
    (n) => `/products/cw-twelve-picnmix/${slug}-${n}.jpg`,
  );
}

export const cwTwelvePicNMixProducts = FLAVORS.map((f, index) => {
  const images = galleryFor(f.slug);
  return {
    id: `cw-twelve-picnmix-${f.slug}`,
    name: `The Twelve (Ti) Pic'n'Mix — ${f.nameEn}`,
    nameKo: `트웰브 (Ti) 픽앤믹스 · ${f.nameKo}`,
    brand: "Christopher Ward",
    price: PRICE,
    category: "watches" as const,
    subcategory: "christopher-ward" as const,
    tags: ["christopher-ward", "twelve", "pic-n-mix", "titanium", "limited"],
    descriptionKo: `크리스토퍼와드 트웰브(Ti) 픽앤믹스 ${f.nameKo}. COSC 인증 Sellita SW300-1 오토매틱, 36mm 그레이드 2 티타늄 케이스, 슈가 크리스털 다이얼. 컬러당 한정 50피스. ${f.blurbKo}`,
    image: images[0],
    images,
    accent: f.accent,
    badge: "Limited",
    sku: f.sku,
    sourceUrl: f.sourceUrl,
    inStock: true,
    // Newest first within the set (first flavor ranks highest).
    registeredAt: new Date(
      Date.parse("2026-07-27T18:00:00.000Z") +
        (FLAVORS.length - 1 - index) * 60_000,
    ).toISOString(),
    braceletResize: {
      feeKrw: CW_BRACELET_RESIZE_FEE,
      sizesCm: [...CW_BRACELET_SIZES_CM],
    },
    storySections: STORY.map((s) => ({ ...s })),
  };
});

export function isBraceletResizeSelected(braceletCm?: string | null) {
  return Boolean(braceletCm && braceletCm !== "no");
}

export function braceletResizeFee(
  product: { braceletResize?: { feeKrw: number } },
  braceletCm?: string | null,
): number {
  if (!product.braceletResize) return 0;
  return isBraceletResizeSelected(braceletCm)
    ? product.braceletResize.feeKrw
    : 0;
}

export function formatBraceletLabel(braceletCm?: string | null) {
  if (!braceletCm || braceletCm === "no") return "브레이슬릿 리사이즈 없음";
  return `브레이슬릿 리사이즈 ${braceletCm}cm`;
}
