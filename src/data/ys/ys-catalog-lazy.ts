import { readCatalogJson } from "@/data/catalog-json";
import type { Product } from "@/data/product-types";

/**
 * Lazy Saint Laurent loader — keep the 14MB JSON out of the shop `category=all`
 * cold path. Static imports of `ys-catalog` parse the whole file into the
 * serverless heap and tip Vercel over the memory limit.
 */
let cached: Product[] | null = null;
let bagsCached: Product[] | null = null;
let shoesCached: Product[] | null = null;

export function getYsCatalogProducts(): Product[] {
  if (!cached) {
    cached = readCatalogJson("ys/ys-catalog.json");
  }
  return cached;
}

/** Bags-only YS slice — bags brand clicks must not parse the full YS catalogue. */
export function getYsBagsCatalogProducts(): Product[] {
  if (!bagsCached) {
    bagsCached = readCatalogJson("ys/ys-bags-catalog.json");
  }
  return bagsCached;
}

/** Shoes-only YS slice — shoes brand clicks must not parse the full YS catalogue. */
export function getYsShoesCatalogProducts(): Product[] {
  if (!shoesCached) {
    shoesCached = readCatalogJson("ys/ys-shoes-catalog.json");
  }
  return shoesCached;
}

/** True when the active shop filter is a Saint Laurent nav node. */
export function isYsShopSub(sub?: string | null): boolean {
  if (!sub) return false;
  return (
    sub === "saint-laurent" ||
    sub.startsWith("saint-laurent-") ||
    sub.startsWith("ys-")
  );
}
