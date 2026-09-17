import type { Product } from "@/data/product-types";

/** Subcategory / collection tokens that mean swimwear apparel (not sports `swimming`). */
const SWIMWEAR_TAXONOMY_RE =
  /swimwear|swimsuit|swimsuits|스윔웨어|수영복/i;

/** Product title cues for swimwear when taxonomy is missing or mixed (e.g. RTW shorts). */
const SWIMWEAR_NAME_RE =
  /수영복|비키니|swimsuit|swimwear|swim\s*shorts?|스윔\s*쇼츠|bikini|one[-\s]?piece\s*swim|삼각\s*탑.*수영|수영.*삼각/i;

/**
 * Homepage-only: hide swimsuits / swimwear. Shop category PLPs and search stay unchanged.
 */
export function isHomepageSwimwearProduct(product: Product): boolean {
  const sub = String(product.subcategory || "");
  if (SWIMWEAR_TAXONOMY_RE.test(sub)) return true;

  const collections = [
    ...(product.tags || []),
    ...(product.cwCollections || []),
    ...(product.ggCollections || []),
    ...(product.bbCollections || []),
    ...(product.axCollections || []),
    ...(product.luCollections || []),
    ...(product.psCollections || []),
    ...(product.bsCollections || []),
    ...(product.gcCollections || []),
    ...(product.chCollections || []),
    ...(product.ceCollections || []),
    ...(product.vwCollections || []),
    ...(product.alCollections || []),
    ...(product.mbCollections || []),
    ...(product.prCollections || []),
    ...(product.lvCollections || []),
    ...(product.diCollections || []),
  ];
  if (collections.some((c) => SWIMWEAR_TAXONOMY_RE.test(String(c)))) return true;

  const name = `${product.name || ""} ${product.nameKo || ""}`;
  if (SWIMWEAR_NAME_RE.test(name)) return true;

  return false;
}
