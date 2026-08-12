import type {  Product  } from "@/data/product-types";
import data from "./ax-catalog.json";

/** Auto-generated — thin wrapper over JSON catalogue. */
export const axCatalogProducts = data as unknown as Product[];
