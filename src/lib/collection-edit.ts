import type { Product } from "@/data/product-types";
import { isHomepageSwimwearProduct } from "@/lib/homepage-product-filters";
import { homepageBrandKey } from "@/lib/homepage-rails";
import {
  compareProductsByNewest,
  diversifyByBrandNewestFirst,
  sortProducts,
  stockSortRank,
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
/** Fixed max grid size for every 100 Collection section (PC: 4×5 = 20). */
export const SECTION_LIMIT = 20;
/** Cap per brand in 신상품 큐레이션 so one sync cannot own the grid. */
export const NEW_EDIT_MAX_PER_BRAND = 2;

export type CuratedEdit = {
  signature: Product[];
  bestseller: Product[];
  newItems: Product[];
};

function isCwStrapProduct(product: Product): boolean {
  if (product.subcategory === "cw-straps") return true;
  if (product.id.startsWith("cw-strap-")) return true;
  return Boolean(product.cwCollections?.some((c) => c === "cw-straps"));
}

/**
 * Build the three 100 Collection sections — up to SECTION_LIMIT each.
 * - signature: ≥100만 원, 최신등록순 (품절은 맨 뒤)
 * - bestseller: 실제 결제 1회 이상인 상품만, 구매수 → 최신순 (품절은 맨 뒤)
 * - new: catalogue-wide 최신등록순 (`registeredAt`), brand-mixed, 품절은 맨 뒤
 *
 * Always set `registeredAt` on new products so 신상품 큐레이션 stays correct.
 */
export function curateCollectionEdit(
  products: Product[],
  purchaseCounts: Record<string, number> = {},
): CuratedEdit {
  // Homepage 100 Collection — exclude swimwear (shop/search unchanged).
  const pool = products.filter((p) => !isHomepageSwimwearProduct(p));

  const signature = sortProducts(
    pool.filter((p) => p.price >= SIGNATURE_MIN),
    "new",
  ).slice(0, SECTION_LIMIT);

  const bestseller = pool
    .filter((p) => (purchaseCounts[p.id] ?? 0) >= 1)
    .sort((a, b) => {
      const stock = stockSortRank(a) - stockSortRank(b);
      if (stock !== 0) return stock;
      const ca = purchaseCounts[a.id] ?? 0;
      const cb = purchaseCounts[b.id] ?? 0;
      if (cb !== ca) return cb - ca;
      return compareProductsByNewest(a, b);
    })
    .slice(0, SECTION_LIMIT);

  // Prefer filling with in-stock newest; sold-out still allowed as padding,
  // but sortProducts sinks them to the end of the section.
  const inStock = pool.filter((p) => p.inStock !== false);
  const newPool = inStock.length >= SECTION_LIMIT ? inStock : pool;
  // CW straps share one registration stamp — keep them on shop/CW nav, not
  // flooding 신상품 (otherwise newest-window is one brand → only maxPerBrand cards).
  const withoutStrapFlood = newPool.filter((p) => !isCwStrapProduct(p));
  const newEligible =
    withoutStrapFlood.length >= SECTION_LIMIT ? withoutStrapFlood : newPool;
  // Scan deep past a single weekly import so round-robin can fill 20 across brands.
  const newest = sortProducts(newEligible, "new");
  const newItems = diversifyByBrandNewestFirst(
    newest,
    SECTION_LIMIT,
    NEW_EDIT_MAX_PER_BRAND,
    homepageBrandKey,
  );

  return { signature, bestseller, newItems };
}
