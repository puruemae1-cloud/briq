import { NextResponse } from "next/server";
import { products } from "@/data/products";
import { getSiteUrl } from "@/lib/site";
import { sortProducts } from "@/lib/product-sort";

/** RSS for Naver Search Advisor feed submission. */
export async function GET() {
  const site = getSiteUrl();
  const newest = sortProducts([...products], "new").slice(0, 40);
  const items = newest
    .map((p) => {
      const title = `${p.brand ? `${p.brand} ` : ""}${p.nameKo || p.name}`;
      const link = `${site}/product/${encodeURIComponent(p.id)}`;
      const desc = [
        p.brand,
        p.nameKo || p.name,
        "명품직구",
        "Briq",
        p.category,
      ]
        .filter(Boolean)
        .join(" · ");
      const date = p.registeredAt
        ? new Date(p.registeredAt).toUTCString()
        : new Date().toUTCString();
      return `<item>
  <title><![CDATA[${title}]]></title>
  <link>${link}</link>
  <guid isPermaLink="true">${link}</guid>
  <pubDate>${date}</pubDate>
  <description><![CDATA[${desc}]]></description>
</item>`;
    })
    .join("\n");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Briq 브릭 — 명품의류·명품직구 신상품</title>
  <link>${site}</link>
  <description>영국 셀렉트숍 Briq의 명품의류·가방·시계·악세서리 신상품 피드. 명품직구·명품구매대행.</description>
  <language>ko</language>
  <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
${items}
</channel>
</rss>`;

  return new NextResponse(xml, {
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8",
      "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=86400",
    },
  });
}
