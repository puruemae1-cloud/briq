import type { Product } from "@/data/product-types";
import data from "./vw-bags-catalog.json";

/** Bags-only slice — bags PLPs must not parse the full vw catalogue. */
export const vwBagsCatalogProducts = data as unknown as Product[];
