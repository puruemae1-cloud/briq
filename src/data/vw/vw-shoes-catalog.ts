import type { Product } from "@/data/product-types";
import data from "./vw-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full vw catalogue. */
export const vwShoesCatalogProducts = data as unknown as Product[];
