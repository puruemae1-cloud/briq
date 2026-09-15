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
  cards: Product[];
};

/** Warm-instance memo so /api/products/shop "더보기" does not rebuild + expand the full PLP each click. */
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

/** Shared shop PLP filter/sort used by `/shop` and `/api/products/shop`. */
export function getShopProductList(params: ShopListQuery): Product[] {
  return getShopListBundle(params).list;
}

/** Filtered list + slim card DTOs (cached together for fast pagination). */
export function getShopListBundle(params: ShopListQuery): {
  list: Product[];
  cards: Product[];
} {
  const key = cacheKey(params);
  const now = Date.now();
  const hit = LIST_CACHE.get(key);
  if (hit && now - hit.at < LIST_CACHE_TTL_MS) {
    return { list: hit.list, cards: hit.cards };
  }

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

  const cards = list.map(toCardProduct);
  pruneCache(now);
  LIST_CACHE.set(key, { at: now, list, cards });
  return { list, cards };
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
