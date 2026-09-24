import type { Product } from "@/data/product-types";
import data from "./ys-shoes-catalog.json";

/** Shoes-only slice — shoes PLPs must not parse the full ys catalogue. */
export const ysShoesCatalogProducts = data as unknown as Product[];
