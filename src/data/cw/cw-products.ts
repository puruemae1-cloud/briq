import type { Product } from "@/data/products";
import { cwCatalogProducts } from "@/data/cw/cw-catalog";
import {
  CW_BRACELET_RESIZE_FEE,
  CW_BRACELET_SIZES_CM,
} from "@/data/cw-twelve-picnmix";

/** Pic'n'Mix SKUs keep the richer gallery + bracelet resize + Korean story. */
const PICNMIX_BY_SKU: Record<
  string,
  {
    slug: string;
    nameKo: string;
    accent: string;
    blurbKo: string;
  }
> = {
  "C12-36AHC1-T00K0-B0R": {
    slug: "kola-krystals",
    nameKo: "콜라 크리스털",
    accent: "#5C3A2E",
    blurbKo:
      "콜라 큐브를 떠올리게 하는 따뜻한 브라운 톤의 슈가 크리스털 다이얼. 컬러 매칭 러버 스트랩과 티타늄 브레이슬릿이 함께 제공됩니다.",
  },
  "C12-36AHC1-T00O0-B0R": {
    slug: "orange-fizz",
    nameKo: "오렌지 피즈",
    accent: "#D4652A",
    blurbKo:
      "상큼한 오렌지 피즈처럼 톡 쏘는 그라데이션 다이얼. 36mm 그레이드 2 티타늄 케이스와 COSC 인증 오토매틱이 조화를 이룹니다.",
  },
  "C12-36AHC1-T00P1-B0R": {
    slug: "berry-burst",
    nameKo: "베리 버스트",
    accent: "#8B2E5B",
    blurbKo:
      "잘 익은 베리처럼 깊고 화사한 핑크-퍼플 그라데이션. 한정 50피스의 여름 한정 에디션입니다.",
  },
  "C12-36AHC1-T00B1-B0R": {
    slug: "blue-sherbet",
    nameKo: "블루 셔벗",
    accent: "#2A6B8A",
    blurbKo:
      "시원한 블루 셔벗을 연상시키는 크리스털 다이얼. 퀵릴리즈 러버 스트랩과 티타늄 브레이슬릿으로 스타일을 자유롭게 바꿀 수 있습니다.",
  },
  "C12-36AHC1-T00R0-B0R": {
    slug: "cherry-pop",
    nameKo: "체리 팝",
    accent: "#B8202E",
    blurbKo:
      "체리 팝처럼 선명한 레드 그라데이션 다이얼. 루메 핸드셋으로 밤에도 또렷한 가독성을 유지합니다.",
  },
  "C12-36AHC1-T00V1-B0R": {
    slug: "apple-sour",
    nameKo: "애플 사워",
    accent: "#3D7A3A",
    blurbKo:
      "새콤한 그린 애플을 담은 상큼한 다이얼. 초경량 티타늄 케이스로 데일리 착용감까지 챙겼습니다.",
  },
};

const STORY = [
  {
    titleKo: "무브먼트",
    bodyKo:
      "COSC 인증 Sellita SW300-1 오토매틱. 정밀한 스위스 무브먼트가 티타늄 케이스 안에서 부드럽게 작동합니다.",
    image: "/products/cw-twelve-picnmix/story/movement.webp",
  },
  {
    titleKo: "다이얼",
    bodyKo:
      "슈가 크리스털 다이얼의 입체감과 컬러 그라데이션이 시간의 결을 선명하게 드러냅니다.",
    image: "/products/cw-twelve-picnmix/story/dial.webp",
    reverse: true,
  },
  {
    titleKo: "케이스백",
    bodyKo:
      "사파이어 전시창으로 무브먼트의 마감을 감상할 수 있습니다.",
    image: "/products/cw-twelve-picnmix/story/caseback.webp",
  },
  {
    titleKo: "케이스",
    bodyKo:
      "36mm 그레이드 2 티타늄 케이스 — 가벼우면서도 견고한 데일리 스포츠 프로파일.",
    image: "/products/cw-twelve-picnmix/story/case.webp",
    reverse: true,
  },
  {
    titleKo: "패키징",
    bodyKo:
      "티타늄 브레이슬릿과 The Twelve 러버 스트랩이 함께 제공되어 스타일을 자유롭게 바꿀 수 있습니다.",
    image: "/products/cw-twelve-picnmix/story/packaging.webp",
  },
];

function galleryFor(slug: string) {
  return [1, 2, 3, 4, 5, 6, 7].map(
    (n) => `/products/cw-twelve-picnmix/${slug}-${n}.jpg`,
  );
}

/** Full CW catalogue with Pic'n'Mix enrichment. */
export const cwProducts: Product[] = cwCatalogProducts.map((product) => {
  const sku = product.sku;
  if (!sku) return product;
  const mix = PICNMIX_BY_SKU[sku];
  if (!mix) return product;
  const images = galleryFor(mix.slug);
  return {
    ...product,
    name: `The Twelve (Ti) Pic'n'Mix — ${mix.nameKo}`,
    nameKo: `트웰브 (Ti) 픽앤믹스 · ${mix.nameKo}`,
    descriptionKo: `크리스토퍼와드 트웰브(Ti) 픽앤믹스 ${mix.nameKo}. COSC 인증 Sellita SW300-1 오토매틱, 36mm 그레이드 2 티타늄 케이스, 슈가 크리스털 다이얼. 컬러당 한정 50피스. ${mix.blurbKo}`,
    image: images[0],
    images,
    accent: mix.accent,
    badge: "Limited",
    braceletResize: {
      feeKrw: CW_BRACELET_RESIZE_FEE,
      sizesCm: [...CW_BRACELET_SIZES_CM],
    },
    storySections: STORY.map((s) => ({ ...s })),
  };
});
