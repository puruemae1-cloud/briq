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
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const mod = require("./ys-catalog") as typeof import("./ys-catalog");
    cached = mod.ysCatalogProducts;
  }
  return cached;
}

/** Bags-only YS slice — bags brand clicks must not parse the full YS catalogue. */
export function getYsBagsCatalogProducts(): Product[] {
  if (!bagsCached) {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const mod =
      require("./ys-bags-catalog") as typeof import("./ys-bags-catalog");
    bagsCached = mod.ysBagsCatalogProducts;
  }
  return bagsCached;
}

/** Shoes-only YS slice — shoes brand clicks must not parse the full YS catalogue. */
export function getYsShoesCatalogProducts(): Product[] {
  if (!shoesCached) {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const mod =
      require("./ys-shoes-catalog") as typeof import("./ys-shoes-catalog");
    shoesCached = mod.ysShoesCatalogProducts;
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
