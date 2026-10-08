import type { MetadataRoute } from "next";
import { getSiteUrl } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  const site = getSiteUrl();

  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          "/account/",
          "/cart",
          "/checkout",
          "/api/",
          "/order/",
        ],
      },
      {
        // Naver search robot
        userAgent: "Yeti",
        allow: "/",
        disallow: [
          "/account/",
          "/cart",
          "/checkout",
          "/api/",
          "/order/",
        ],
      },
    ],
    sitemap: `${site}/sitemap-index.xml`,
    host: site,
  };
}
