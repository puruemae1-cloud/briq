import type { Product } from "@/data/product-types";
import data from "./bs-bags-catalog.json";

/** Bags-only slice — bags PLPs must not parse the full bs catalogue. */
export const bsBagsCatalogProducts = data as unknown as Product[];
