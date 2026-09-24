import type { Product } from "@/data/product-types";
import data from "./ce-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full ce catalogue. */
export const ceShoesCatalogProducts = data as unknown as Product[];
