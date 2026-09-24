import type { Product } from "@/data/product-types";
import data from "./di-bags-catalog.json";

/** Bags-only slice — bags PLPs must not parse the full di catalogue. */
export const diBagsCatalogProducts = data as unknown as Product[];
