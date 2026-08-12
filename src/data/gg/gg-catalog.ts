import type {  Product  } from "@/data/product-types";
import data from "./gg-catalog.json";

/** Auto-generated — thin wrapper over JSON catalogue. */
export const ggCatalogProducts = data as unknown as Product[];
