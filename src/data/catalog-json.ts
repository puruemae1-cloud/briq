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

let missingImages: Set<string> | null | undefined;

/** Photo paths referenced by TS-literal catalogues but absent from the CDN tag (build-time list). */
function missingImageSet(): Set<string> | null {
  if (missingImages === undefined) {
    const file = path.join(process.cwd(), "catalog-dist", "missing-images.json.gz");
    missingImages = fs.existsSync(file)
      ? new Set(JSON.parse(zlib.gunzipSync(fs.readFileSync(file)).toString("utf8")) as string[])
      : null;
  }
  return missingImages;
}

type Photos = { image?: string; images?: string[]; hoverImage?: string };

function withoutMissing<T extends Photos>(item: T, missing: Set<string>): T {
  const ok = (src?: string) => !src || !missing.has(src.split("?")[0]);
  if (ok(item.image) && ok(item.hoverImage) && (item.images ?? []).every(ok)) return item;
  const images = item.images?.filter(ok);
  return {
    ...item,
    images,
    hoverImage: ok(item.hoverImage) ? item.hoverImage : undefined,
    image: ok(item.image) ? item.image : images?.[0],
  };
}

/**
 * TS-literal catalogues (cw, gg, ax, lu) skip the JSON build guard; apply the same
 * rule at load time: drop photos missing on the CDN, hide products left without one.
 */
export function dropMissingImages(products: Product[]): Product[] {
  const missing = missingImageSet();
  if (!missing?.size) return products;
  const out: Product[] = [];
  for (const p of products) {
    const fixed = withoutMissing(p, missing);
    if (!fixed.image) continue;
    const variants = fixed.variants?.map((v) => {
      const fv = withoutMissing(v, missing);
      return fv.image ? fv : { ...fv, image: fixed.image as string };
    });
    const changed = variants?.some((v, i) => v !== fixed.variants?.[i]);
    out.push(changed ? { ...fixed, variants } : fixed);
  }
  return out;
}
