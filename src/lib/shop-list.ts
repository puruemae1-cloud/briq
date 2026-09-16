import { getProductsByCategory } from "@/data/products";
import type { Product } from "@/data/product-types";
import { searchProducts } from "@/lib/product-search";
import {
  NEW_ARRIVALS_LIMIT,
  getNewArrivalsProducts,
  getTopSortedProducts,
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

/** Shared shop PLP filter/sort used by `/shop` and `/api/products/shop`. */
export function getShopProductList(params: ShopListQuery): Product[] {
  const category = params.category ?? "all";
  const sub = params.sub;
  const sort = parseProductSort(params.sort);
  const q = params.q?.trim();
  // Catalogue-wide surfaces must NOT full-sort/copy the multi-brand array —
  // that OOMs Vercel after large brand imports (YS et al.).
  const isCatalogueWide = Boolean(category === "all" && !sub && !q);
  const isNewArrivals = Boolean(isCatalogueWide && sort === "new");

  let list = getProductsByCategory(category, sub);
  list = searchProducts(list, params.q);
  if (isNewArrivals) {
    list = getNewArrivalsProducts(list);
  } else if (isCatalogueWide) {
    list = getTopSortedProducts(list, sort, NEW_ARRIVALS_LIMIT);
  } else {
    list = sortProducts(list, sort);
  }
  if (sub === "gg-men" || sub === "gg-women") {
    list = preferGgApparelFirst(list);
  }
  return list;
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
