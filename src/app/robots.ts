import type { MetadataRoute } from "next";
import { getSiteUrl } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  const site = getSiteUrl();
  const disallow = [
    // No trailing slash — also blocks /account (마이페이지 hub).
    "/account",
    "/cart",
    "/checkout",
    "/api/",
    "/order",
  ];

  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow,
      },
      {
        // Naver search robot
        userAgent: "Yeti",
        allow: "/",
        disallow,
      },
    ],
    // Naver (Yeti) first: tiny priority list, then recent, then full index.
    // RSS is linked from HTML <head> (seo-metadata) and submitted in Search Advisor.
    sitemap: [
      `${site}/sitemap-naver.xml`,
      `${site}/sitemap-recent.xml`,
      `${site}/sitemap-index.xml`,
    ],
    host: site,
  };
}
