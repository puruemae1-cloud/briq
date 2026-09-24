import type { Product } from "@/data/product-types";
import data from "./bb-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full bb catalogue. */
export const bbShoesCatalogProducts = data as unknown as Product[];
