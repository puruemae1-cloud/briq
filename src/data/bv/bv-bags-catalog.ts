import type { Product } from "@/data/product-types";
import data from "./bv-bags-catalog.json";

/** Bags-only slice — bags PLPs must not parse the full bv catalogue. */
export const bvBagsCatalogProducts = data as unknown as Product[];
