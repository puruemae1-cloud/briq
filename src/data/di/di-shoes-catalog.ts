import type { Product } from "@/data/product-types";
import data from "./di-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full di catalogue. */
export const diShoesCatalogProducts = data as unknown as Product[];
