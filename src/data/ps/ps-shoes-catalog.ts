import type { Product } from "@/data/product-types";
import data from "./ps-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full ps catalogue. */
export const psShoesCatalogProducts = data as unknown as Product[];
