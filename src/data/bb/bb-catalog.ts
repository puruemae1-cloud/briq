import type { Product } from "@/data/products";
import data from "./bb-catalog.json";

/** Auto-generated — thin wrapper over JSON catalogue. */
export const bbCatalogProducts = data as unknown as Product[];
