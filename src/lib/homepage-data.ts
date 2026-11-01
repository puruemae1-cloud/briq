import type { Product } from "@/data/product-types";
import { homeLookBanners } from "@/data/home-banners";
import {
  getCollection100,
  getHomepageCategoryProducts,
  toProductCardProduct,
} from "@/data/products";
import { curateCollectionEdit } from "@/lib/collection-edit";
import { assignHomepageCategoryRails } from "@/lib/homepage-rails";

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
  /** Four Flannels picks under the Flannels interstitial. */
  flannels: Product[];
  signature: Product[];
  newItems: Product[];
  /** Deployment that built these cards (set by `/api/home-data`). */
  deployKey?: string;
};


function discountRatio(p: Product): number {
  const price = p.price ?? 0;
  const compare = p.compareAtPrice ?? 0;
  if (!compare || compare <= price || price <= 0) return 0;
  return (compare - price) / compare;
}

/** In-stock Flannels (women+men clearance) — highest discount first. */
function getFlannelsHomepageProducts(limit = 4): Product[] {
  const list = getHomepageCategoryProducts("luxury", "flannels").filter(
    (p) => p.inStock !== false,
  );
  list.sort((a, b) => {
    const d = discountRatio(b) - discountRatio(a);
    if (d !== 0) return d;
    const tb = Date.parse(b.registeredAt || b.updatedAt || "") || 0;
    const ta = Date.parse(a.registeredAt || a.updatedAt || "") || 0;
    return tb - ta;
  });
  return list.slice(0, limit).map(toProductCardProduct);
}

let memo: HomepageData | null = null;

export function buildHomepageData(): HomepageData {
  if (memo) return memo;

  // Skip YS merge here — homepage soft-nav was waiting on the 14MB catalogue.
  const categoryRails = homeLookBanners
    .filter((b) => b.categoryId)
    .map((b) => ({
      railId: b.id,
      products: getHomepageCategoryProducts(b.categoryId),
    }));
  const rails = assignHomepageCategoryRails(categoryRails, 4);
  const curated = curateCollectionEdit(getCollection100());

  memo = {
    rails: Object.fromEntries(
      Object.entries(rails).map(([id, list]) => [id, list.map(toProductCardProduct)]),
    ),
    flannels: getFlannelsHomepageProducts(4),
    signature: curated.signature.map(toProductCardProduct),
    newItems: curated.newItems.map(toProductCardProduct),
  };
  return memo;
}
