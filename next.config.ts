import type { NextConfig } from "next";

/** Product PDP images live in git; on Vercel they are slimmed from the deploy
 *  and served from GitHub via rewrite to keep builds under disk limits. */
const PRODUCT_IMAGE_ORIGIN =
  process.env.PRODUCT_IMAGE_ORIGIN ||
  "https://raw.githubusercontent.com/puruemae1-cloud/briq/product-images/public/products";

const nextConfig: NextConfig = {
  // mobile/ is a separate Expo app
  turbopack: {},
  // Hide the "N" dev tools badge (dev server only; production never shows it)
  devIndicators: false,
  async rewrites() {
    // Only proxy when the local file is missing (Vercel slim build). Locally,
    // files in public/products are served directly and this rewrite is unused.
    return [
      {
        source: "/products/:path*",
        destination: `${PRODUCT_IMAGE_ORIGIN}/:path*`,
      },
    ];
  },
};

export default nextConfig;
