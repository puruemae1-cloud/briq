import type { Product } from "@/data/products";
import data from "./ps-catalog.json";

/** Auto-generated — thin wrapper over JSON catalogue. */
export const psCatalogProducts = data as unknown as Product[];
