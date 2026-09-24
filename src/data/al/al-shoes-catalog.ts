import type { Product } from "@/data/product-types";
import data from "./al-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full al catalogue. */
export const alShoesCatalogProducts = data as unknown as Product[];
