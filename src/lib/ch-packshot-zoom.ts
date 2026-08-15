import type { Product } from "@/data/product-types";

/** Fragrance gift/discovery sets already fill the PLP frame — don't zoom. */
const FRAGRANCE_SET_RE = /세트|\bSET\b/i;
/** Refill spray sets are still tiny bottles and should keep mobile zoom. */
const FRAGRANCE_REFILL_RE = /리필|refill/i;

function isChanelFragranceSet(product: Product): boolean {
  const name = `${product.nameKo ?? ""} ${product.name ?? ""}`;
  if (!FRAGRANCE_SET_RE.test(name)) return false;
  if (FRAGRANCE_REFILL_RE.test(name)) return false;
  return true;
}

/**
 * Mobile packshot zoom for Chanel fragrance (non-set) + fine jewellery.
 * Gift sets with box+bottles already read large — leave those at default scale.
 */
export function needsChanelMobilePackshotZoom(product: Product): boolean {
  const sub = product.subcategory;
  const cols = product.chCollections;

  const isFragrance =
    sub === "ch-fragrance" || Boolean(cols?.includes("ch-fragrance"));
  const isFineJewellery =
    sub === "ch-fine-jewellery" ||
    Boolean(cols?.includes("ch-fine-jewellery"));

  if (isFineJewellery) return true;
  if (isFragrance) return !isChanelFragranceSet(product);
  return false;
}
