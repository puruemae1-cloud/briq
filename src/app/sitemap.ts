import type { MetadataRoute } from "next";
import { navCategories } from "@/data/categories";
import { products } from "@/data/products";
import { PRODUCT_CHUNK, sitemapCount } from "@/lib/sitemap-chunks";
import { SEO_BRANDS, getSiteUrl } from "@/lib/site";

export async function generateSitemaps() {
  // id 0 = static pages; 1..N = product chunks
  return Array.from({ length: sitemapCount() }, (_, id) => ({ id }));
}

export default async function sitemap(props: {
  id: Promise<string>;
}): Promise<MetadataRoute.Sitemap> {
  // Next 16 passes the id as a Promise<string>; comparing it to a number
  // silently produced empty sitemaps.
  const id = Number(await props.id);
  const site = getSiteUrl();
  const now = new Date();

  if (id === 0) {
    const staticUrls: MetadataRoute.Sitemap = [
      {
        url: site,
        lastModified: now,
        changeFrequency: "daily",
        priority: 1,
      },
      {
        url: `${site}/shop`,
        lastModified: now,
        changeFrequency: "daily",
        priority: 0.95,
      },
      {
        url: `${site}/shop?sort=new`,
        lastModified: now,
        changeFrequency: "daily",
        priority: 0.9,
      },
      {
        url: `${site}/brands`,
        lastModified: now,
        changeFrequency: "weekly",
        priority: 0.9,
      },
      {
        url: `${site}/guide/luxury-direct`,
        lastModified: now,
        changeFrequency: "monthly",
        priority: 0.85,
      },
      {
        url: `${site}/guide/buying-agency`,
        lastModified: now,
        changeFrequency: "monthly",
        priority: 0.85,
      },
      {
        url: `${site}/guide/luxury-apparel`,
        lastModified: now,
        changeFrequency: "monthly",
        priority: 0.85,
      },
      {
        url: `${site}/terms`,
        lastModified: now,
        changeFrequency: "yearly",
        priority: 0.2,
      },
      {
        url: `${site}/privacy`,
        lastModified: now,
        changeFrequency: "yearly",
        priority: 0.2,
      },
    ];

    for (const cat of navCategories) {
      staticUrls.push({
        url: `${site}${cat.href}`,
        lastModified: now,
        changeFrequency: "daily",
        priority: 0.85,
      });
    }

    for (const brand of SEO_BRANDS) {
      staticUrls.push({
        url: `${site}/brands/${brand.slug}`,
        lastModified: now,
        changeFrequency: "weekly",
        priority: 0.8,
      });
      staticUrls.push({
        url: `${site}${brand.shopHref}`,
        lastModified: now,
        changeFrequency: "daily",
        priority: 0.75,
      });
    }

    return staticUrls;
  }

  const chunkIndex = id - 1;
  const start = chunkIndex * PRODUCT_CHUNK;
  const slice = products.slice(start, start + PRODUCT_CHUNK);

  return slice.map((p) => ({
    url: `${site}/product/${encodeURIComponent(p.id)}`,
    lastModified: p.registeredAt ? new Date(p.registeredAt) : now,
    changeFrequency: "weekly" as const,
    priority: 0.6,
  }));
}
