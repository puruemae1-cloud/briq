export function decodeHtml(s: string) {
  return s
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#x27;/gi, "'")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
    .replace(/&nbsp;/g, " ")
    .replace(/&pound;/g, "£")
    .replace(/&#163;/g, "£")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .trim();
}

export function plausibleGbp(n: number) {
  return Number.isFinite(n) && n >= 0.5 && n <= 20000;
}

export function parseGbpAmount(raw: string) {
  const n = Number(String(raw).replace(/,/g, "").trim());
  return plausibleGbp(n) ? Math.round(n * 100) / 100 : null;
}

/** First £ amount in free text (search snippets, titles). */
export function extractGbpFromText(text: string) {
  const decoded = decodeHtml(text).replace(/\\u00a3/gi, "£");
  const m = decoded.match(/£\s*(\d{1,5}(?:\.\d{1,2})?)/);
  return m ? parseGbpAmount(m[1]) : null;
}

/** £ amount that appears next to this product title in search text. */
export function extractGbpForTitle(text: string, title: string) {
  const plain = decodeHtml(text)
    .replace(/<[^>]+>/g, " ")
    .replace(/\\u00a3/gi, "£")
    .replace(/\s+/g, " ");
  const needle = title.trim();
  if (!needle) return extractGbpFromText(plain);
  const escaped = needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/\s+/g, "\\s+");
  const re = new RegExp(`${escaped}[^£]{0,80}£\\s*(\\d{1,5}(?:\\.\\d{1,2})?)`, "i");
  const m = plain.match(re);
  return m ? parseGbpAmount(m[1]) : null;
}

function meta(html: string, keys: string[]) {
  for (const key of keys) {
    const re = new RegExp(
      `<meta[^>]+(?:property|name)=["']${key}["'][^>]+content=["']([^"']+)["']`,
      "i",
    );
    const re2 = new RegExp(
      `<meta[^>]+content=["']([^"']+)["'][^>]+(?:property|name)=["']${key}["']`,
      "i",
    );
    const m = html.match(re) || html.match(re2);
    if (m?.[1]) return decodeHtml(m[1]);
  }
  return "";
}

function offerPrice(offers: unknown): { price: number | null; currency: string } {
  if (!offers) return { price: null, currency: "" };
  const list = Array.isArray(offers) ? offers : [offers];
  for (const offer of list) {
    if (!offer || typeof offer !== "object") continue;
    const o = offer as Record<string, unknown>;
    const currency = String(o.priceCurrency || o.currency || "").toUpperCase();
    const price = parseGbpAmount(String(o.price ?? o.lowPrice ?? ""));
    if (price && (!currency || currency === "GBP")) return { price, currency: currency || "GBP" };
  }
  return { price: null, currency: "" };
}

function walkJsonLd(node: unknown): { price: number | null; title: string } {
  if (!node) return { price: null, title: "" };
  if (Array.isArray(node)) {
    for (const item of node) {
      const found = walkJsonLd(item);
      if (found.price) return found;
    }
    return { price: null, title: "" };
  }
  if (typeof node !== "object") return { price: null, title: "" };
  const o = node as Record<string, unknown>;
  if (o["@graph"]) {
    const nested = walkJsonLd(o["@graph"]);
    if (nested.price) return nested;
  }
  const type = o["@type"];
  const types = (Array.isArray(type) ? type : [type]).map((t) => String(t || "").toLowerCase());
  if (types.includes("product") || o.offers) {
    const { price } = offerPrice(o.offers);
    const title = String(o.name || "").slice(0, 200);
    if (price) return { price, title };
  }
  return { price: null, title: "" };
}

export function extractGbpFromHtml(html: string) {
  const scripts = html.matchAll(
    /<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi,
  );
  for (const block of scripts) {
    try {
      const json = JSON.parse(block[1].replace(/[\u0000-\u001f]+/g, " "));
      const found = walkJsonLd(json);
      if (found.price) return found.price;
    } catch {
      /* ignore broken JSON-LD */
    }
  }

  const amount = meta(html, ["product:price:amount", "og:price:amount"]);
  const currency = meta(html, ["product:price:currency", "og:price:currency"]).toUpperCase();
  if (amount && (!currency || currency === "GBP")) {
    const n = parseGbpAmount(amount);
    if (n) return n;
  }

  const asosCurrent = html.match(
    /"current"\s*:\s*\{\s*"value"\s*:\s*(\d+(?:\.\d+)?)\s*,\s*"text"\s*:\s*"£([^"]+)"/i,
  );
  if (asosCurrent) {
    const n = parseGbpAmount(asosCurrent[1]) ?? parseGbpAmount(asosCurrent[2]);
    if (n) return n;
  }

  const itemprop = html.match(
    /itemprop=["']price["'][^>]*content=["']([^"']+)["']/i,
  ) || html.match(/content=["']([^"']+)["'][^>]*itemprop=["']price["']/i);
  if (itemprop) {
    const n = parseGbpAmount(itemprop[1]);
    if (n) return n;
  }

  return extractGbpFromText(meta(html, ["og:title", "twitter:title"]));
}

export function extractTitleFromHtml(html: string, fallback = "") {
  const title =
    meta(html, ["og:title", "twitter:title"]) ||
    html.match(/<title[^>]*>([^<]+)<\/title>/i)?.[1]?.trim() ||
    fallback;
  return decodeHtml(title).replace(/\s+/g, " ").slice(0, 200);
}

export function extractImageFromHtml(html: string) {
  return meta(html, ["og:image", "twitter:image"]);
}
