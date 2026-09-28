import type { Product } from "@/data/product-types";
import data from "./al-bags-catalog.json";

/** Bags-only slice — bags PLPs must not parse the full al catalogue. */
export const alBagsCatalogProducts = data as unknown as Product[];
