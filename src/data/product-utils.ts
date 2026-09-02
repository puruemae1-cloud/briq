import type { Product, ProductVariant } from "@/data/product-types";

/** KRW = round_만원(GBP × 2100 × 1.05 + 200,000) */
export function gbpToBriqKrw(gbp: number) {
  return Math.round((gbp * 2100 * 1.05 + 200_000) / 10_000) * 10_000;
}

/** Addon fees (bracelet resize etc.) — no +200,000 base, still 만원 rounding. */
export function gbpToBriqAddonKrw(gbp: number) {
  return Math.round((gbp * 2100 * 1.05) / 10_000) * 10_000;
}

/** Lowest purchasable KRW for PLP cards / metadata (variant → product → gbp fallback). */
export function productDisplayPrice(
  product: Product,
  variant?: ProductVariant | null,
): number {
  if (variant?.price != null && variant.price > 0) return variant.price;
  if (product.price != null && product.price > 0) return product.price;
  const variantPrices = (product.variants ?? [])
    .map((v) => v.price)
    .filter((p): p is number => typeof p === "number" && p > 0);
  if (variantPrices.length > 0) return Math.min(...variantPrices);
  if (product.gbpPrice != null && product.gbpPrice > 0) {
    return gbpToBriqKrw(product.gbpPrice);
  }
  return 0;
}

/** Compare-at KRW aligned with `productDisplayPrice` selection rules. */
export function productCompareAtPrice(
  product: Product,
  variant?: ProductVariant | null,
): number | undefined {
  if (variant?.compareAtPrice != null) return variant.compareAtPrice;
  if (product.compareAtPrice != null) return product.compareAtPrice;
  const was = (product.variants ?? [])
    .map((v) => v.compareAtPrice)
    .filter((p): p is number => typeof p === "number" && p > 0);
  return was.length > 0 ? Math.max(...was) : undefined;
}

/** Sale discount percent from compareAt → price, or null if not on sale.
 * When a variant is selected, only that variant's compareAtPrice counts
 * (so non-sale colours don't inherit another colourway's discount).
 */
export function productSalePercent(
  product: Product,
  variant?: ProductVariant | null,
) {
  const price = productDisplayPrice(product, variant);
  const was = productCompareAtPrice(product, variant);
  if (!was || was <= price) return null;
  return Math.max(1, Math.round((1 - price / was) * 100));
}

/** True if the product (or any of its variants) can be purchased. */
export function isProductInStock(product: Product) {
  if (product.shopColorKey != null && typeof product.inStock === "boolean") {
    return product.inStock;
  }
  if (product.variants && product.variants.length > 0) {
    return product.variants.some((v) => v.inStock);
  }
  return product.inStock !== false;
}

/** True if a specific variant (or the product itself) is purchasable. */
export function isVariantInStock(product: Product, variantId?: string | null) {
  if (product.variants && product.variants.length > 0) {
    if (!variantId) return false;
    return product.variants.some((v) => v.id === variantId && v.inStock);
  }
  return product.inStock !== false;
}

export function formatKrw(price: number) {
  return `${new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: 0,
  }).format(price)}원`;
}

/**
 * Official maison English product title for PDP (under Korean `nameKo`).
 * Returns null when missing, identical to Korean, or Hangul-only (no Latin).
 */
export function productOfficialEnglishName(
  product: Pick<Product, "name" | "nameKo">,
): string | null {
  const en = (product.name || "").trim();
  const ko = (product.nameKo || "").trim();
  if (!en) return null;
  if (en === ko) return null;
  // Hangul-only "English" field → nothing useful to show under Korean title
  if (/[\uac00-\ud7a3]/.test(en) && !/[A-Za-z]/.test(en)) return null;
  return en;
}


export type { Product, ProductVariant, ProductSizeChart, ProductSizeChartTab, ProductStorySection, ProductTechSpec } from "@/data/product-types";
