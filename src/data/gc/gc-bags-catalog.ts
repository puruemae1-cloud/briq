import type { Product } from "@/data/product-types";
import data from "./gc-bags-catalog.json";

/** Bags-only slice — bags PLPs must not parse the full gc catalogue. */
export const gcBagsCatalogProducts = data as unknown as Product[];
