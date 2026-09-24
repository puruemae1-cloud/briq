import type { Product } from "@/data/product-types";
import data from "./bs-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full bs catalogue. */
export const bsShoesCatalogProducts = data as unknown as Product[];
