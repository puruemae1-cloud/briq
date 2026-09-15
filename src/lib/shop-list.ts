import { getProductsByCategory } from "@/data/products";
import type { Product } from "@/data/product-types";
import { toCardProduct } from "@/lib/product-card-dto";
import { searchProducts } from "@/lib/product-search";
import {
  getNewArrivalsProducts,
  parseProductSort,
  preferGgApparelFirst,
  sortProducts,
  type ProductSort,
} from "@/lib/product-sort";

export const SHOP_PAGE_SIZE = 24;

export type ShopListQuery = {
  category?: string;
  sub?: string;
  q?: string;
  sort?: string | null;
};

type CacheEntry = {
  at: number;
  list: Product[];
};

/**
 * Warm-instance memo for filtered/sorted PLP lists.
 * Intentionally caches only `list` (not a second full `cards` copy) — mapping
 * every colourway through `toCardProduct` OOM'd Vercel builds on large PLPs.
 */
const LIST_CACHE = new Map<string, CacheEntry>();
const LIST_CACHE_TTL_MS = 90_000;
const LIST_CACHE_MAX = 48;

function cacheKey(params: ShopListQuery): string {
  return [
    params.category ?? "all",
    params.sub ?? "",
    (params.q ?? "").trim().toLowerCase(),
    params.sort ?? "",
  ].join("\0");
}

function pruneCache(now: number) {
  for (const [k, v] of LIST_CACHE) {
    if (now - v.at > LIST_CACHE_TTL_MS) LIST_CACHE.delete(k);
  }
  while (LIST_CACHE.size > LIST_CACHE_MAX) {
    const oldest = LIST_CACHE.keys().next().value;
    if (oldest == null) break;
    LIST_CACHE.delete(oldest);
  }
}

function buildShopProductList(params: ShopListQuery): Product[] {
  const category = params.category ?? "all";
  const sub = params.sub;
  const sort = parseProductSort(params.sort);
  const isNewArrivals = Boolean(
    params.sort === "new" &&
      !params.q?.trim() &&
      category === "all" &&
      !sub,
  );

  let list = getProductsByCategory(category, sub);
  list = searchProducts(list, params.q);
  if (isNewArrivals) {
    list = getNewArrivalsProducts(list);
  } else {
    list = sortProducts(list, sort);
  }
  if (sub === "gg-men" || sub === "gg-women") {
    list = preferGgApparelFirst(list);
  }
  return list;
}

/** Shared shop PLP filter/sort used by `/shop` and `/api/products/shop`. */
export function getShopProductList(params: ShopListQuery): Product[] {
  const key = cacheKey(params);
  const now = Date.now();
  const hit = LIST_CACHE.get(key);
  if (hit && now - hit.at < LIST_CACHE_TTL_MS) {
    return hit.list;
  }

  const list = buildShopProductList(params);
  pruneCache(now);
  LIST_CACHE.set(key, { at: now, list });
  return list;
}

/** Filtered list + slim card DTOs for the requested window only. */
export function getShopListBundle(params: ShopListQuery): {
  list: Product[];
  cards: Product[];
} {
  const list = getShopProductList(params);
  // Keep `cards` as an alias for callers that still expect it — they must
  // slice before mapping in hot paths. Full-list mapping is avoided here.
  return { list, cards: list };
}

/** Slim card page for API / SSR — map only the sliced window. */
export function getShopCardPage(
  params: ShopListQuery,
  offset: number,
  limit: number = SHOP_PAGE_SIZE,
): { products: Product[]; total: number } {
  const list = getShopProductList(params);
  const products = sliceShopPage(list, offset, limit).map(toCardProduct);
  return { products, total: list.length };
}

export function sliceShopPage(
  list: Product[],
  offset: number,
  limit: number = SHOP_PAGE_SIZE,
): Product[] {
  const start = Math.max(0, offset);
  return list.slice(start, start + Math.max(1, limit));
}

export type { ProductSort };
