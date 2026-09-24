import type { Product } from "@/data/product-types";
import data from "./pr-bags-catalog.json";

/** Bags-only slice — bags PLPs must not parse the full pr catalogue. */
export const prBagsCatalogProducts = data as unknown as Product[];
