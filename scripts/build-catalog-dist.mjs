#!/usr/bin/env node
/**
 * Write gzipped, minified copies of every catalogue JSON the site reads at
 * runtime to catalog-dist/ (see src/data/catalog-json.ts). The file list is every
 * `readCatalogJson("…")` literal under src/, so loaders and this script cannot
 * drift apart.
 *
 * Also fails the build when all catalogues together would not fit the
 * serverless heap budget: a failed build keeps the previous deployment live,
 * whereas an oversized one takes the shop down with OOM kills.
 *
 * Run with --expose-gc for an accurate heap measurement.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import zlib from "node:zlib";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SRC = path.join(ROOT, "src");
const DATA = path.join(SRC, "data");
const OUT = path.join(ROOT, "catalog-dist");
// Vercel functions have 2GB; leave room for Next/React and concurrent requests.
const HEAP_BUDGET_MB = Number(process.env.CATALOG_HEAP_BUDGET_MB || 1100);

function sourceFiles(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...sourceFiles(p));
    else if (/\.(ts|tsx)$/.test(entry.name)) out.push(p);
  }
  return out;
}

const rels = new Set();
for (const file of sourceFiles(SRC)) {
  const text = fs.readFileSync(file, "utf8");
  for (const m of text.matchAll(/readCatalogJson\(\s*"([^"]+\.json)"\s*\)/g)) {
    rels.add(m[1]);
  }
}
if (!rels.size) {
  console.error("[catalog-dist] no readCatalogJson() calls found");
  process.exit(1);
}

fs.rmSync(OUT, { recursive: true, force: true });
const parsed = [];
global.gc?.();
const heapBefore = process.memoryUsage().heapUsed;
let bytes = 0;
for (const rel of [...rels].sort()) {
  const src = path.join(DATA, rel);
  if (!fs.existsSync(src)) {
    console.error(`[catalog-dist] missing ${path.relative(ROOT, src)}`);
    process.exit(1);
  }
  const data = JSON.parse(fs.readFileSync(src, "utf8"));
  if (!Array.isArray(data)) {
    console.error(`[catalog-dist] ${rel} is not a product array`);
    process.exit(1);
  }
  const gz = zlib.gzipSync(JSON.stringify(data), { level: 6 });
  const dest = path.join(OUT, `${rel}.gz`);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.writeFileSync(dest, gz);
  bytes += gz.length;
  parsed.push(data);
}
global.gc?.();
const heapMb = (process.memoryUsage().heapUsed - heapBefore) / 1e6;
console.log(
  `[catalog-dist] ${rels.size} file(s), ${(bytes / 1e6).toFixed(0)}MB gzipped, ` +
    `~${heapMb.toFixed(0)}MB heap with every catalogue loaded (budget ${HEAP_BUDGET_MB}MB)`,
);
if (heapMb > HEAP_BUDGET_MB) {
  console.error(
    "[catalog-dist] catalogues exceed the serverless heap budget — slim the " +
      "catalogue JSON (or split loaders) before deploying",
  );
  process.exit(1);
}
