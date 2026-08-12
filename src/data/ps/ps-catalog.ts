import type {  Product  } from "@/data/product-types";
import data from "./ps-catalog.json";

/** Auto-generated — thin wrapper over JSON catalogue. */
export const psCatalogProducts = data as unknown as Product[];
