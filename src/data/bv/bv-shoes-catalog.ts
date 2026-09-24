import type { Product } from "@/data/product-types";
import data from "./bv-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full bv catalogue. */
export const bvShoesCatalogProducts = data as unknown as Product[];
