import { products } from "@/data/products";
import {
  HUB_SITEMAP_LASTMOD,
  registeredAtMs,
} from "@/lib/sitemap-chunks";
import { SEO_BRANDS, getSiteUrl } from "@/lib/site";

export const dynamic = "force-static";

/** Cap for Yeti's tiny daily fetch — hubs first, then newest products only. */
const NAVER_PRODUCT_CAP = 120;

/**
 * Tiny priority sitemap for Naver Search Advisor.
 *
 * `sitemap-recent.xml` (~500 URLs) is still useful, but Yeti often finishes
 * only 1–2 pages/day. This file stays small so one visit yields hub pages
 * plus the newest product URLs without burning budget on the full catalogue.
 */
export async function GET() {
  const site = getSiteUrl();
  const hubUpdated = HUB_SITEMAP_LASTMOD;
  const pages = [
    site,
    `${site}/shop`,
    `${site}/brands`,
    `${site}/guide/luxury-direct`,
    `${site}/guide/buying-agency`,
    `${site}/guide/luxury-apparel`,
    ...SEO_BRANDS.map((brand) => `${site}/brands/${brand.slug}`),
  ];
  const newest = products
    .map((product) => ({ product, at: registeredAtMs(product.registeredAt) }))
    .filter((row): row is { product: (typeof products)[number]; at: number } =>
      row.at != null,
    )
    .sort((a, b) => b.at - a.at)
    .slice(0, NAVER_PRODUCT_CAP);

  const urls = [
    ...pages.map(
      (url) =>
        `  <url>\n    <loc>${url}</loc>\n    <lastmod>${hubUpdated}</lastmod>\n  </url>`,
    ),
    ...newest.map(
      ({ product, at }) =>
        `  <url>\n    <loc>${site}/product/${encodeURIComponent(product.id)}</loc>\n    <lastmod>${new Date(at).toISOString()}</lastmod>\n  </url>`,
    ),
  ];
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join("\n")}\n</urlset>\n`;
  return new Response(xml, {
    headers: { "Content-Type": "application/xml; charset=utf-8" },
  });
}
