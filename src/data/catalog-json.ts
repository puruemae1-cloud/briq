import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import type { Product } from "@/data/product-types";

/**
 * Read a catalogue JSON (path relative to src/data) from disk at runtime.
 *
 * Never bundle catalogue JSON: a bundled JSON module keeps its source text
 * alive next to the parsed objects (~3x the memory), and with every brand
 * loaded that exceeds the 2GB Vercel function. The gzipped copies live in
 * catalog-dist/, written by scripts/build-catalog-dist.mjs (run by `build`
 * and `dev`, which collects every `readCatalogJson("…")` literal) and traced
 * into the functions by next.config.ts.
 */
export function readCatalogJson(rel: string): Product[] {
  const file = path.join(process.cwd(), "catalog-dist", `${rel}.gz`);
  return JSON.parse(zlib.gunzipSync(fs.readFileSync(file)).toString("utf8")) as Product[];
}
