import type { Product } from "@/data/product-types";
import data from "./ch-bags-catalog.json";

/** Bags-only slice — bags PLPs must not parse the full ch catalogue. */
export const chBagsCatalogProducts = data as unknown as Product[];
