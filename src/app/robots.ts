import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const site = (
    process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") || "https://briq.kr"
  );

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
    sitemap: `${site}/sitemap.xml`,
    host: site,
  };
}
