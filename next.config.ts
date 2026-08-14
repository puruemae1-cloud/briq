import type { NextConfig } from "next";

/**
 * Product + banner media live on the `product-images` git tag.
 * On Vercel we do NOT proxy them (that burned Fast Origin Transfer / Hobby
 * fair-use). The browser loads jsDelivr directly via NEXT_PUBLIC_MEDIA_ORIGIN.
 */
const MEDIA_ORIGIN =
  process.env.MEDIA_ORIGIN ||
  "https://cdn.jsdelivr.net/gh/puruemae1-cloud/briq@product-images/public";

const nextConfig: NextConfig = {
  // mobile/ is a separate Expo app
  turbopack: {},
  // Hide the "N" dev tools badge (dev server only; production never shows it)
  devIndicators: false,
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
  env: {
    // Empty locally so `public/` paths keep working in next dev.
    NEXT_PUBLIC_MEDIA_ORIGIN: process.env.VERCEL ? MEDIA_ORIGIN : "",
  },
};

export default nextConfig;
