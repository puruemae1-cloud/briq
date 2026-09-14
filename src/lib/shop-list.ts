import { getProductsByCategory } from "@/data/products";
import type { Product } from "@/data/product-types";
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

/** Shared shop PLP filter/sort used by `/shop` and `/api/products/shop`. */
export function getShopProductList(params: ShopListQuery): Product[] {
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

export function sliceShopPage(
  list: Product[],
  offset: number,
  limit: number = SHOP_PAGE_SIZE,
): Product[] {
  const start = Math.max(0, offset);
  return list.slice(start, start + Math.max(1, limit));
}

export type { ProductSort };
