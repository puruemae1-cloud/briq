import type { Product } from "@/data/product-types";
import data from "./mb-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full mb catalogue. */
export const mbShoesCatalogProducts = data as unknown as Product[];
