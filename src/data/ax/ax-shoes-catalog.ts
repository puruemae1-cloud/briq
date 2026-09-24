import type { Product } from "@/data/product-types";
import data from "./ax-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full ax catalogue. */
export const axShoesCatalogProducts = data as unknown as Product[];
