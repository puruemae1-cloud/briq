import type { Product } from "@/data/product-types";
import data from "./pr-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full pr catalogue. */
export const prShoesCatalogProducts = data as unknown as Product[];
