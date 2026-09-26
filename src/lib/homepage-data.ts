import { unstable_cache } from "next/cache";
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
 * Homepage product data, cached in the Vercel Data Cache.
 *
 * Building these parses every brand catalogue (hundreds of MB); doing it per
 * request made cold starts ~15s. Only the trimmed card fields are cached
 * (a few KB), and the key includes the deployment so catalogue syncs show up
 * on the next deploy instead of waiting for the TTL.
 *
 * Keep `@/data/products` a static import: switching it to `await import()`
 * inside these callbacks made every request recompute (~9s total, Sep 2026).
 */
const DEPLOY_KEY =
  process.env.VERCEL_DEPLOYMENT_ID ||
  process.env.VERCEL_GIT_COMMIT_SHA ||
  "local";
const TTL_SECONDS = 3600;

export const getHomepageRailCards = unstable_cache(
  async (): Promise<Record<string, Product[]>> => {
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
    return Object.fromEntries(
      Object.entries(rails).map(([id, list]) => [id, list.map(toProductCardProduct)]),
    );
  },
  ["home-rail-cards-v1", DEPLOY_KEY],
  { revalidate: TTL_SECONDS },
);

export const getCollection100Cards = unstable_cache(
  async (): Promise<{ signature: Product[]; newItems: Product[] }> => {
    const curated = curateCollectionEdit(getCollection100());
    return {
      signature: curated.signature.map(toProductCardProduct),
      newItems: curated.newItems.map(toProductCardProduct),
    };
  },
  ["home-collection100-cards-v1", DEPLOY_KEY],
  { revalidate: TTL_SECONDS },
);
