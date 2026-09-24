import type { Product } from "@/data/product-types";
import data from "./gc-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full gc catalogue. */
export const gcShoesCatalogProducts = data as unknown as Product[];
