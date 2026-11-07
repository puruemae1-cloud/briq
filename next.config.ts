import type { NextConfig } from "next";

/**
 * Product + banner media live on the `product-images` git tag.
 * On Vercel we do NOT proxy them (that burned Fast Origin Transfer / Hobby
 * fair-use). Point browsers at GitHub raw for the tag — jsDelivr intermittently
 * 403s under PLP load, which shows as broken product thumbnails.
 */
const MEDIA_ORIGIN =
  process.env.MEDIA_ORIGIN ||
  "https://raw.githubusercontent.com/puruemae1-cloud/briq/product-images/public";

const nextConfig: NextConfig = {
  // mobile/ is a separate Expo app
  turbopack: {},
  // Native TLS impersonation. Bundling it breaks the platform binary.
  serverExternalPackages: ["impit"],
  // Hide the "N" dev tools badge (dev server only; production never shows it)
  devIndicators: false,
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
  // Catalogue JSON is read from disk at runtime (src/data/catalog-json.ts).
  outputFileTracingIncludes: {
    "/": ["./catalog-dist/**/*.json.gz"],
    "/**/*": ["./catalog-dist/**/*.json.gz"],
    "/api/qa": [
      "./node_modules/impit/**/*",
      "./node_modules/impit-linux-x64-gnu/**/*",
    ],
    "/api/qa/auto-reply": [
      "./node_modules/impit/**/*",
      "./node_modules/impit-linux-x64-gnu/**/*",
    ],
  },
  // Shop/product HTML only changes with a deploy (catalogue is bundled, cart badge
  // is client-side) and Vercel purges the CDN on deploy, so serve it from the edge
  // instead of waking a cold function that has to load every catalogue.
  async headers() {
    const edgeCache = [
      {
        key: "Vercel-CDN-Cache-Control",
        value: "public, s-maxage=3600, stale-while-revalidate=86400",
      },
    ];
    return [
      { source: "/shop", headers: edgeCache },
      { source: "/product/:id", headers: edgeCache },
    ];
  },
  // Serve the index at /sitemap.xml with no redirect. Naver/Google drop
  // sitemap URLs that 3xx (see getSiteUrl comment in site.ts).
  async rewrites() {
    return [{ source: "/sitemap.xml", destination: "/sitemap-index.xml" }];
  },
  async redirects() {
    return [
      // Banners/products are not in the Vercel deploy (product-images tag).
      // Redirect so crawlers hitting https://www.briq.kr/banners/... get 308→CDN
      // instead of 404/400 (Naver "접근 불가한 페이지").
      {
        source: "/banners/:path*",
        destination: `${MEDIA_ORIGIN}/banners/:path*`,
        permanent: true,
      },
      {
        source: "/products/:path*",
        destination: `${MEDIA_ORIGIN}/products/:path*`,
        permanent: true,
      },
    ];
  },
  env: {
    // Empty locally so `public/` paths keep working in next dev.
    NEXT_PUBLIC_MEDIA_ORIGIN: process.env.VERCEL ? MEDIA_ORIGIN : "",
  },
};

export default nextConfig;
