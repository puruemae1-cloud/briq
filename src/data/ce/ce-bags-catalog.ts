import type { Product } from "@/data/product-types";
import data from "./ce-bags-catalog.json";

/** Bags-only slice — bags PLPs must not parse the full ce catalogue. */
export const ceBagsCatalogProducts = data as unknown as Product[];
