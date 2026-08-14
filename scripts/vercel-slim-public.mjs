#!/usr/bin/env node
/**
 * On Vercel builds, drop heavy media trees from `public/` so the deploy stays
 * small AND so runtime traffic does not serve multi-GB assets from Vercel.
 *
 * Product + banner bytes are loaded from jsDelivr (GitHub `product-images`
 * tag) via `mediaUrl()` / NEXT_PUBLIC_MEDIA_ORIGIN — never proxied.
 *
 * Local `next dev` / `next build` keep the images on disk.
 */
import { rmSync, existsSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const PUBLIC = join(process.cwd(), "public");
const PRODUCTS = join(PUBLIC, "products");
const BANNERS = join(PUBLIC, "banners");

/** Keep tiny SVG placeholders; remove every PDP / editorial photo tree. */
const KEEP_PRODUCT_FILES = new Set([
  "bottle.svg",
  "cap.svg",
  "crossbody.svg",
  "knit.svg",
  "loafer.svg",
  "pouch.svg",
  "run-jacket.svg",
  "runner.svg",
  "scarf.svg",
  "tote.svg",
  "track-tee.svg",
  "wool-coat.svg",
]);

function dirSizeMb(path) {
  let total = 0;
  const walk = (p) => {
    for (const name of readdirSync(p)) {
      const full = join(p, name);
      const st = statSync(full);
      if (st.isDirectory()) walk(full);
      else total += st.size;
    }
  };
  walk(path);
  return total / (1024 * 1024);
}

if (!process.env.VERCEL) {
  console.log("[vercel-slim-public] skip (not on Vercel)");
  process.exit(0);
}

let freed = 0;

if (existsSync(PRODUCTS)) {
  for (const name of readdirSync(PRODUCTS)) {
    if (KEEP_PRODUCT_FILES.has(name)) continue;
    const path = join(PRODUCTS, name);
    const st = statSync(path);
    const mb = st.isDirectory() ? dirSizeMb(path) : st.size / (1024 * 1024);
    rmSync(path, { recursive: true, force: true });
    freed += mb;
    console.log(`[vercel-slim-public] removed products/${name} (~${mb.toFixed(0)} MB)`);
  }
}

if (existsSync(BANNERS)) {
  const mb = dirSizeMb(BANNERS);
  rmSync(BANNERS, { recursive: true, force: true });
  freed += mb;
  console.log(`[vercel-slim-public] removed banners (~${mb.toFixed(0)} MB)`);
}

console.log(`[vercel-slim-public] freed ~${freed.toFixed(0)} MB`);
