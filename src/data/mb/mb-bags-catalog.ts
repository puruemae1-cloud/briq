import type { Product } from "@/data/product-types";
import data from "./mb-bags-catalog.json";

/** Bags-only slice — bags PLPs must not parse the full mb catalogue. */
export const mbBagsCatalogProducts = data as unknown as Product[];
