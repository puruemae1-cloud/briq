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
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
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

/**
 * Every path on the product-images tag (tree-only fetch, ~10MB / a few seconds),
 * or null when the guard is off or the tag cannot be listed. On by default on
 * Vercel; CATALOG_IMAGE_GUARD=1/0 forces it on/off elsewhere.
 */
function tagImagePaths() {
  const flag = process.env.CATALOG_IMAGE_GUARD;
  if (flag === "0" || (!process.env.VERCEL && flag !== "1")) return null;
  const repo = `https://github.com/${process.env.GITHUB_REPOSITORY || "puruemae1-cloud/briq"}.git`;
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "briq-tag-"));
  const git = (...args) =>
    spawnSync("git", ["-C", dir, ...args], { encoding: "utf8", timeout: 180_000, maxBuffer: 256 << 20 });
  try {
    spawnSync("git", ["init", "-q", "--bare", dir]);
    const fetched = git(
      "fetch", "-q", "--depth=1", "--filter=blob:none", repo,
      "+refs/tags/product-images:refs/tags/product-images",
    );
    const listed = fetched.status === 0 && git("ls-tree", "-r", "--name-only", "product-images", "public/products/");
    if (!listed || listed.status !== 0) {
      console.warn("[catalog-dist] WARN could not list product-images tag — image guard skipped");
      return null;
    }
    return new Set(listed.stdout.split("\n").filter(Boolean).map((p) => p.slice("public".length)));
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

/**
 * Drop gallery frames that are not on the CDN and hide products left without a
 * primary photo, so a failed image upload shows fewer photos rather than broken ones.
 */
function guardImages(rel, products, onTag) {
  const ok = (src) =>
    typeof src !== "string" || !src.startsWith("/products/") || onTag.has(src.split("?")[0]);
  const fix = (item) => {
    if (Array.isArray(item.images)) item.images = item.images.filter(ok);
    if (item.hoverImage && !ok(item.hoverImage)) delete item.hoverImage;
    if (item.image && !ok(item.image)) item.image = item.images?.[0];
    return Boolean(item.image);
  };
  let frames = 0;
  const kept = products.filter((p) => {
    const before = JSON.stringify(p);
    const keep = fix(p);
    for (const v of p.variants ?? []) {
      if (!fix(v)) v.image = p.image;
    }
    if (JSON.stringify(p) !== before) frames++;
    return keep;
  });
  const hidden = products.length - kept.length;
  if (hidden > Math.max(20, products.length * 0.3)) {
    console.warn(`[catalog-dist] WARN ${rel}: ${hidden}/${products.length} products lack CDN photos — not hiding them`);
    return products;
  }
  if (hidden || frames) {
    console.warn(`[catalog-dist] ${rel}: hid ${hidden} product(s) without CDN photos, trimmed images on ${frames}`);
  }
  return kept;
}

const onTag = tagImagePaths();
if (onTag) console.log(`[catalog-dist] image guard: ${onTag.size} files on product-images tag`);

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
  let data = JSON.parse(fs.readFileSync(src, "utf8"));
  if (!Array.isArray(data)) {
    console.error(`[catalog-dist] ${rel} is not a product array`);
    process.exit(1);
  }
  if (onTag) data = guardImages(rel, data, onTag);
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
