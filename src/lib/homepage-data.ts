import type { Product } from "@/data/product-types";
import { homeLookBanners } from "@/data/home-banners";
import {
  getCollection100,
  getHomepageCategoryProducts,
  toProductCardProduct,
} from "@/data/products";
import { curateCollectionEdit } from "@/lib/collection-edit";
import {
  assignHomepageCategoryRails,
  HOMEPAGE_WATCHES_COLLECTION,
} from "@/lib/homepage-rails";

/**
 * Builds the homepage product cards from the full brand catalogues.
 *
 * Heavy (parses hundreds of MB). Only `app/api/home-data/route.ts` and the
 * dynamic-import fallback in `homepage-feed.ts` may import this module — a
 * static import from the page/layout bundles every catalogue into the `/`
 * chunk and makes each cold boot ~9s.
 */
export type HomepageData = {
  rails: Record<string, Product[]>;
  signature: Product[];
  newItems: Product[];
};

let memo: HomepageData | null = null;

export function buildHomepageData(): HomepageData {
  if (memo) return memo;

  // Skip YS merge here — homepage soft-nav was waiting on the 14MB catalogue.
  const categoryRails = homeLookBanners
    .filter((b) => b.categoryId)
    .map((b) => ({
      railId: b.id,
      products:
        b.id === "watches"
          ? getHomepageCategoryProducts("watches", HOMEPAGE_WATCHES_COLLECTION)
          : getHomepageCategoryProducts(b.categoryId),
    }));
  const rails = assignHomepageCategoryRails(categoryRails, 4);
  const curated = curateCollectionEdit(getCollection100());

  memo = {
    rails: Object.fromEntries(
      Object.entries(rails).map(([id, list]) => [id, list.map(toProductCardProduct)]),
    ),
    signature: curated.signature.map(toProductCardProduct),
    newItems: curated.newItems.map(toProductCardProduct),
  };
  return memo;
}
