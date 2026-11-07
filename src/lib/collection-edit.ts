import type { Product } from "@/data/products";
import {
  compareProductsByNewest,
  sortProducts,
} from "@/lib/product-sort";

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
/** Fixed max grid size for every 100 Collection section. */
export const SECTION_LIMIT = 20;

export type CuratedEdit = {
  signature: Product[];
  bestseller: Product[];
  newItems: Product[];
};

/**
 * Build the three 100 Collection sections — up to SECTION_LIMIT each.
 * - signature: ≥100만 원, 최신등록순 (패딩 없음)
 * - bestseller: 실제 결제 1회 이상인 상품만, 구매수 → 최신순 (패딩 없음)
 * - new: catalogue-wide 최신등록순 (`registeredAt`)
 *
 * Always set `registeredAt` on new products so 신상품 큐레이션 stays correct.
 */
export function curateCollectionEdit(
  products: Product[],
  purchaseCounts: Record<string, number> = {},
): CuratedEdit {
  const signature = sortProducts(
    products.filter((p) => p.price >= SIGNATURE_MIN),
    "new",
  ).slice(0, SECTION_LIMIT);

  const bestseller = products
    .filter((p) => (purchaseCounts[p.id] ?? 0) >= 1)
    .sort((a, b) => {
      const ca = purchaseCounts[a.id] ?? 0;
      const cb = purchaseCounts[b.id] ?? 0;
      if (cb !== ca) return cb - ca;
      return compareProductsByNewest(a, b);
    })
    .slice(0, SECTION_LIMIT);

  // Prefer in-stock newest so OOS styles don't fill the 신상품 rail.
  const inStock = products.filter((p) => p.inStock !== false);
  const newPool =
    inStock.length >= SECTION_LIMIT ? inStock : products;
  const newItems = sortProducts(newPool, "new").slice(0, SECTION_LIMIT);

  return { signature, bestseller, newItems };
}
