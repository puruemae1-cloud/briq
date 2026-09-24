import type { Product } from "@/data/product-types";
import data from "./bb-bags-catalog.json";

/** Bags-only slice — bags PLPs must not parse the full bb catalogue. */
export const bbBagsCatalogProducts = data as unknown as Product[];
