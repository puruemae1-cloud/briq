import type { Product } from "@/data/products";
import data from "./ax-catalog.json";

/** Auto-generated — thin wrapper over JSON catalogue. */
export const axCatalogProducts = data as unknown as Product[];
