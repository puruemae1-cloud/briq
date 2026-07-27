import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // mobile/ is a separate Expo app
  turbopack: {},
  // Hide the "N" dev tools badge (dev server only; production never shows it)
  devIndicators: false,
};

export default nextConfig;
