import { Impit } from "impit";

export type OfficialSizeStock =
  | { state: "sold-out"; restockDate: string | null }
  | { state: "in-stock" }
  | { state: "unknown" };

type Json = Record<string, unknown>;

class MemoryCookieJar {
  private readonly pairs = new Map<string, string>();

  setCookie(cookie: string): void {
    const pair = String(cookie).split(";")[0] ?? "";
    const eq = pair.indexOf("=");
    if (eq <= 0) return;
    const name = pair.slice(0, eq).trim();
    const value = pair.slice(eq + 1).trim();
    if (name) this.pairs.set(name, value);
  }

  getCookieString(): string {
    return [...this.pairs.entries()].map(([name, value]) => `${name}=${value}`).join("; ");
  }
}

function asRecord(value: unknown): Json | null {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Json) : null;
}

export function normalizeSizeLabel(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/^size[\s-]*/i, "")
    .replace(/^uk[\s-]*/i, "")
    .replace(/\s+/g, "");
}

function sameSize(asked: string, candidate: string): boolean {
  const left = normalizeSizeLabel(asked);
  const right = normalizeSizeLabel(candidate);
  return Boolean(left) && left === right;
}

function sizeValues(product: Json): Json[] {
  const attrs = product.variationAttributes;
  if (!Array.isArray(attrs)) return [];
  const sizeAttr = attrs.find((attr) => {
    const row = asRecord(attr);
    return String(row?.attributeId || row?.id || "").toLowerCase() === "size";
  });
  const values = asRecord(sizeAttr)?.values;
  return Array.isArray(values) ? values.flatMap((value) => {
    const row = asRecord(value);
    return row ? [row] : [];
  }) : [];
}

function selectedSize(product: Json, asked: string): Json | null {
  const sizes = sizeValues(product);
  if (!sizes.length) return null;
  return (
    sizes.find((row) => row.selected === true && sameSize(asked, String(row.displayValue || row.value || ""))) ??
    sizes.find((row) => sameSize(asked, String(row.displayValue || row.value || ""))) ??
    null
  );
}

function publishedDate(value: unknown): string | null {
  if (value == null) return null;
  const text = String(value).trim();
  if (!text || text.toLowerCase() === "null") return null;
  return text;
}

function restockDate(product: Json): string | null {
  const availability = asRecord(product.availability);
  const dated = publishedDate(availability?.inStockDate);
  if (dated) return dated;
  const messages = Array.isArray(availability?.messages) ? availability.messages.join(" ") : "";
  const match = messages.match(
    /\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b/i,
  );
  return match?.[0] ?? null;
}

function soldOutPayload(product: Json, asked: string): boolean {
  const availability = asRecord(product.availability);
  const message = JSON.stringify(availability?.messages ?? "").toLowerCase();
  const stockClass = String(availability?.class ?? "").toLowerCase();
  const row = selectedSize(product, asked);
  const caption = String(row?.caption ?? "").toLowerCase();
  const sizeSoldOut = row
    ? row.selectable === false && (caption.includes("sold out") || caption.includes("out of stock") || product.available === false)
    : false;
  const productSoldOut =
    product.available === false &&
    (stockClass.includes("outofstock") || message.includes("sold out") || message.includes("out of stock"));
  if (row) return sizeSoldOut || (productSoldOut && row.selected === true);
  return productSoldOut;
}

function sfccRoot(html: string, pageUrl: string): { origin: string; site: string; locale: string; pid: string } | null {
  const site = html.match(/\/on\/demandware\.store\/(Sites-[A-Za-z0-9_-]+)\/([a-z]{2}_[A-Z]{2})\//);
  if (!site) return null;
  let origin: string;
  try {
    origin = new URL(pageUrl).origin;
  } catch {
    return null;
  }
  const pidFromUrl = pageUrl.match(/\/([A-Za-z0-9-]+)\.html/i)?.[1];
  const pidFromHtml = html.match(/"productId"\s*:\s*"([^"]+)"/)?.[1] || html.match(/[?&]pid=([A-Za-z0-9-]+)/)?.[1];
  const pid = pidFromUrl || pidFromHtml;
  if (!pid) return null;
  return { origin, site: site[1], locale: site[2], pid };
}

async function readVariation(
  client: Impit,
  url: string,
  referer: string,
): Promise<Json | null> {
  const response = await client.fetch(url, {
    headers: {
      accept: "application/json,text/javascript,*/*",
      "x-requested-with": "XMLHttpRequest",
      referer,
    },
  });
  if (response.status !== 200) return null;
  const text = await response.text();
  if (!text.trim().startsWith("{")) return null;
  const body = asRecord(JSON.parse(text) as unknown);
  return asRecord(body?.product);
}

/**
 * Live size on the brand's own product page.
 * Returns unknown when the page cannot be read or the size cannot be matched.
 */
export async function officialSizeStock(pageUrl: string, size: string): Promise<OfficialSizeStock> {
  const client = new Impit({
    browser: "chrome",
    timeout: 12_000,
    cookieJar: new MemoryCookieJar(),
  });
  const page = await client.fetch(pageUrl, {
    headers: { "accept-language": "en-GB,en;q=0.9" },
  });
  if (page.status !== 200) return { state: "unknown" };
  const html = await page.text();
  const root = sfccRoot(html, pageUrl);
  if (!root) return { state: "unknown" };

  const listUrl =
    `${root.origin}/on/demandware.store/${root.site}/${root.locale}/Product-Variation` +
    `?pid=${encodeURIComponent(root.pid)}&quantity=1`;
  const listed = await readVariation(client, listUrl, pageUrl);
  if (!listed) return { state: "unknown" };
  const match = selectedSize(listed, size);
  if (!match) return { state: "unknown" };

  const detailUrl = typeof match.url === "string" && match.url.startsWith("http") ? match.url : listUrl;
  const detail = detailUrl === listUrl ? listed : await readVariation(client, detailUrl, pageUrl);
  if (!detail) return { state: "unknown" };
  if (!soldOutPayload(detail, size)) return { state: "in-stock" };
  return { state: "sold-out", restockDate: restockDate(detail) };
}
