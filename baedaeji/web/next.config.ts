import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  devIndicators: false,
  turbopack: {
    root: path.join(__dirname),
  },
  allowedDevOrigins: ["*.trycloudflare.com"],
  experimental: {
    serverActions: {
      allowedOrigins: ["localhost:3001", "*.trycloudflare.com"],
    },
  },
};

export default nextConfig;
