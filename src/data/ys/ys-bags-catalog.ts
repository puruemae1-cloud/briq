import type { Product } from "@/data/product-types";
import data from "./ys-bags-catalog.json";

/** Bags-only slice — bags PLPs must not parse the full ys catalogue. */
export const ysBagsCatalogProducts = data as unknown as Product[];
