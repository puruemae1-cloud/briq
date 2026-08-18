import type { Product } from "@/data/product-types";
import { CH_MAKEUP_LEAF_IDS, CH_SKINCARE_LEAF_IDS } from "@/data/categories";

/** Gift/discovery sets already fill the PLP frame — don't zoom. */
const PACKSHOT_SET_RE = /세트|\bSET\b/i;
/** Refill spray sets are still tiny bottles and should keep mobile zoom. */
const FRAGRANCE_REFILL_RE = /리필|refill/i;

const CH_MAKEUP_SUBS = new Set<string>(CH_MAKEUP_LEAF_IDS);
const CH_SKINCARE_SUBS = new Set<string>(["ch-skincare", ...CH_SKINCARE_LEAF_IDS]);

function isChanelPackshotSet(product: Product): boolean {
  const name = `${product.nameKo ?? ""} ${product.name ?? ""}`;
  if (!PACKSHOT_SET_RE.test(name)) return false;
  if (FRAGRANCE_REFILL_RE.test(name)) return false;
  return true;
}

function isChanelMakeup(product: Product): boolean {
  const sub = product.subcategory;
  if (sub && CH_MAKEUP_SUBS.has(sub)) return true;
  const cols = product.chCollections ?? [];
  if (cols.includes("ch-makeup")) return true;
  return cols.some((c) => CH_MAKEUP_SUBS.has(c));
}

function isChanelSkincare(product: Product): boolean {
  const sub = product.subcategory;
  if (sub && CH_SKINCARE_SUBS.has(sub)) return true;
  const cols = product.chCollections ?? [];
  if (cols.includes("ch-skincare")) return true;
  return cols.some((c) => CH_SKINCARE_SUBS.has(c));
}

/**
 * Mobile packshot zoom for Chanel fragrance (non-set), fine jewellery, makeup,
 * and skincare. Gift sets with box+bottles already read large — leave those at
 * default scale.
 */
export function needsChanelMobilePackshotZoom(product: Product): boolean {
  const sub = product.subcategory;
  const cols = product.chCollections;

  const isFragrance =
    sub === "ch-fragrance" || Boolean(cols?.includes("ch-fragrance"));
  const isFineJewellery =
    sub === "ch-fine-jewellery" ||
    Boolean(cols?.includes("ch-fine-jewellery"));
  const isMakeup = isChanelMakeup(product);
  const isSkincare = isChanelSkincare(product);

  if (isFineJewellery) return true;
  if (isMakeup) return !isChanelPackshotSet(product);
  if (isSkincare) return !isChanelPackshotSet(product);
  if (isFragrance) return !isChanelPackshotSet(product);
  return false;
}
