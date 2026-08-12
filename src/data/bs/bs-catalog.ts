import type {  Product  } from "@/data/product-types";
import data from "./bs-catalog.json";

/** Auto-generated — thin wrapper over JSON catalogue. */
export const bsCatalogProducts = data as unknown as Product[];
