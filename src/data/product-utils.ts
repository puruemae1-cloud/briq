import type { Product, ProductVariant } from "@/data/product-types";

/** KRW = round_만원(GBP × 2100 × 1.05 + 200,000) */
export function gbpToBriqKrw(gbp: number) {
  return Math.round((gbp * 2100 * 1.05 + 200_000) / 10_000) * 10_000;
}

/** Addon fees (bracelet resize etc.) — no +200,000 base, still 만원 rounding. */
export function gbpToBriqAddonKrw(gbp: number) {
  return Math.round((gbp * 2100 * 1.05) / 10_000) * 10_000;
}

/** Sale discount percent from compareAt → price, or null if not on sale.
 * When a variant is selected, only that variant's compareAtPrice counts
 * (so non-sale colours don't inherit another colourway's discount).
 */
export function productSalePercent(
  product: Product,
  variant?: ProductVariant | null,
) {
  const price = variant?.price ?? product.price;
  const was = variant
    ? variant.compareAtPrice
    : product.compareAtPrice;
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

export type { Product, ProductVariant, ProductSizeChart, ProductSizeChartTab, ProductStorySection, ProductTechSpec } from "@/data/product-types";
