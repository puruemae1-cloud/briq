#!/usr/bin/env node
/**
 * On Vercel builds, drop heavy product image trees from `public/` so the
 * build stays under the 32GB disk limit. Runtime requests to `/products/*`
 * are rewritten to GitHub (see next.config.ts).
 *
 * Local `next dev` / `next build` keep the images on disk.
 */
import { rmSync, existsSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const ROOT = join(process.cwd(), "public", "products");

/** Directories that are safe to serve from GitHub instead of the deploy. */
const SLIM_DIRS = [
  "axa-pdp",
  "ax-pdp",
  "axg-pdp",
  "axo-pdp",
  "ps-pdp",
  "bs-pdp",
  "bb-pdp",
  "gg-pdp",
  "cw-pdp",
  "cw-editorial",
  "cw",
  "cw-twelve-picnmix",
  "lu-pdp",
];

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

if (!existsSync(ROOT)) {
  console.log("[vercel-slim-public] no public/products");
  process.exit(0);
}

let freed = 0;
for (const name of SLIM_DIRS) {
  const path = join(ROOT, name);
  if (!existsSync(path)) continue;
  const mb = dirSizeMb(path);
  rmSync(path, { recursive: true, force: true });
  freed += mb;
  console.log(`[vercel-slim-public] removed ${name} (~${mb.toFixed(0)} MB)`);
}

console.log(`[vercel-slim-public] freed ~${freed.toFixed(0)} MB`);
