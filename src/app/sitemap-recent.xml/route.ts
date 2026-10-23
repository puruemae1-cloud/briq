import { products } from "@/data/products";
import {
  RECENT_SITEMAP_CAP,
  RECENT_SITEMAP_DAYS,
  newestProductLastmod,
  registeredAtMs,
} from "@/lib/sitemap-chunks";
import { SEO_BRANDS, getSiteUrl } from "@/lib/site";

export const dynamic = "force-static";

/**
 * Short sitemap Naver can fetch in one visit. The full catalogue stays in
 * sitemap-index.xml; this file is only landing pages plus the newest products.
 */
export async function GET() {
  const site = getSiteUrl();
  const catalogUpdated = newestProductLastmod().toISOString();
  const cutoff = Date.now() - RECENT_SITEMAP_DAYS * 24 * 60 * 60 * 1000;
  const pages = [
    site,
    `${site}/shop`,
    `${site}/brands`,
    `${site}/guide/luxury-direct`,
    `${site}/guide/buying-agency`,
    `${site}/guide/luxury-apparel`,
    ...SEO_BRANDS.map((brand) => `${site}/brands/${brand.slug}`),
  ];
  const recent = products
    .map((product) => ({ product, at: registeredAtMs(product.registeredAt) }))
    .filter((row): row is { product: (typeof products)[number]; at: number } =>
      row.at != null && row.at >= cutoff,
    )
    .sort((a, b) => b.at - a.at)
    .slice(0, RECENT_SITEMAP_CAP);

  const urls = [
    ...pages.map(
      (url) =>
        `  <url>\n    <loc>${url}</loc>\n    <lastmod>${catalogUpdated}</lastmod>\n  </url>`,
    ),
    ...recent.map(
      ({ product, at }) =>
        `  <url>\n    <loc>${site}/product/${encodeURIComponent(product.id)}</loc>\n    <lastmod>${new Date(at).toISOString()}</lastmod>\n  </url>`,
    ),
  ];
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join("\n")}\n</urlset>\n`;
  return new Response(xml, {
    headers: { "Content-Type": "application/xml; charset=utf-8" },
  });
}
