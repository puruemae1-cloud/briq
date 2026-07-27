import type { Product } from "@/data/products";

/** Curated homepage / 100 Collection section roles. */
export type EditTier = "signature" | "bestseller" | "new";

export const EDIT_TIER_COPY: Record<EditTier, { titleKo: string }> = {
  signature: {
    titleKo: "프리미엄을 재정의하다, 하이엔드 컬렉션",
  },
  bestseller: {
    titleKo: "첫 구매자 만족도 1위 컬렉션",
  },
  new: {
    titleKo: "가장 먼저 만나는 신상품 큐레이션",
  },
};

const SIGNATURE_MIN = 1_000_000;
const BESTSELLER_MIN = 100_000;
const BESTSELLER_MAX = 300_000;
/** How many newest SKUs to surface in the new-arrivals edit. */
const NEW_LIMIT = 12;

/**
 * When true, bestseller requires ≥1 recorded payment.
 * Temporarily false — show 10~30만 newest until live orders accumulate.
 */
const BESTSELLER_REQUIRE_PURCHASE = false;

function registeredMs(product: Product) {
  const ms = product.registeredAt ? Date.parse(product.registeredAt) : 0;
  return Number.isFinite(ms) ? ms : 0;
}

function byNewest(a: Product, b: Product) {
  return registeredMs(b) - registeredMs(a) || b.price - a.price;
}

export type CuratedEdit = {
  signature: Product[];
  bestseller: Product[];
  newItems: Product[];
};

/**
 * Build the three 100 Collection sections.
 * - signature: ≥100만 원, 최신등록순
 * - bestseller: 10~30만 원 (결제 조건은 BESTSELLER_REQUIRE_PURCHASE)
 * - new: catalogue-wide 최신등록순 (시그니처와 중복 허용 — 최신 CW 등이 맨 위)
 *
 * Always set `registeredAt` on new products so 신상품 큐레이션 stays correct.
 */
export function curateCollectionEdit(
  products: Product[],
  purchaseCounts: Record<string, number> = {},
): CuratedEdit {
  const signature = products
    .filter((p) => p.price >= SIGNATURE_MIN)
    .sort(byNewest);

  const bestseller = products
    .filter((p) => {
      if (p.price < BESTSELLER_MIN || p.price > BESTSELLER_MAX) return false;
      if (!BESTSELLER_REQUIRE_PURCHASE) return true;
      return (purchaseCounts[p.id] ?? 0) >= 1;
    })
    .sort((a, b) => {
      if (BESTSELLER_REQUIRE_PURCHASE) {
        const ca = purchaseCounts[a.id] ?? 0;
        const cb = purchaseCounts[b.id] ?? 0;
        if (cb !== ca) return cb - ca;
      }
      return byNewest(a, b);
    });

  // Independent of other sections — newest registered always rise to the top.
  const newItems = [...products].sort(byNewest).slice(0, NEW_LIMIT);

  return { signature, bestseller, newItems };
}
