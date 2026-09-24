import type { Product } from "@/data/product-types";
import data from "./ax-bags-catalog.json";

/** Bags-only slice — bags PLPs must not parse the full ax catalogue. */
export const axBagsCatalogProducts = data as unknown as Product[];
