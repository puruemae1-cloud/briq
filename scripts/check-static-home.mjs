#!/usr/bin/env node
/**
 * Build guard: the homepage must be prerendered (static / ISR).
 *
 * If `/` falls back to per-request SSR, every visit re-parses the brand
 * catalogues and Vercel cold starts take 10–15s. Common culprits:
 *   - cookies()/headers()/searchParams in app/layout.tsx or anything it renders
 *   - `export const dynamic = "force-dynamic"` / `revalidate = 0` on app/page.tsx
 *
 * Runs after `next build`; a non-zero exit aborts the Vercel deploy so the
 * previous (fast) build stays live.
 */
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const failures = [];

const manifestPath = join(root, ".next", "prerender-manifest.json");
if (!existsSync(manifestPath)) {
  failures.push(`${manifestPath} missing — run after \`next build\`.`);
} else {
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  if (!manifest.routes?.["/"]) {
    failures.push(
      "`/` is not in prerender-manifest routes → homepage renders per request.",
    );
  }
}

const layoutSrc = readFileSync(join(root, "src", "app", "layout.tsx"), "utf8");
for (const banned of ["next/headers", "cookies(", "headers(", "getCartCount"]) {
  if (layoutSrc.includes(banned)) {
    failures.push(`src/app/layout.tsx uses \`${banned}\` → makes every page dynamic.`);
  }
}

if (failures.length) {
  console.error("\n✖ Homepage static guard failed:");
  for (const f of failures) console.error(`  - ${f}`);
  console.error(
    "\nKeep the root layout request-agnostic (see HeaderCartCount for the cart badge).\n",
  );
  process.exit(1);
}

console.log("✓ Homepage static guard: `/` is prerendered.");
