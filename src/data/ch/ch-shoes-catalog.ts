import type { Product } from "@/data/product-types";
import data from "./ch-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full ch catalogue. */
export const chShoesCatalogProducts = data as unknown as Product[];
