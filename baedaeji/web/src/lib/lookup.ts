import { decodeHtml, extractGbpFromHtml, extractGbpFromText, extractGbpForTitle, extractImageFromHtml, extractTitleFromHtml } from "./gbp";
import { resolveProductInput, isHttpUrl, isStoreSearchUrl, searchUrlForStore } from "./product-input";
import { storeFromUrl, type StoreBanner } from "./stores";

const BROWSER_HEADERS = {
  "user-agent":
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
  accept: "text/html,application/xhtml+xml",
};

export type ProductLookup = {
  query: string;
  url: string;
  title: string;
  image: string;
  gbpPrice: number | null;
  storeId: string;
  storeName: string;
  source: "url" | "search";
  priceSource: "pdp" | "search" | null;
};

type WebHit = {
  url: string;
  title: string;
  snippet: string;
  gbpPrice: number | null;
};

const cache = new Map<string, { at: number; value: ProductLookup }>();
const CACHE_MS = 15 * 60 * 1000;

function cacheGet(key: string) {
  const hit = cache.get(key);
  if (!hit) return null;
  if (Date.now() - hit.at > CACHE_MS) {
    cache.delete(key);
    return null;
  }
  return hit.value;
}

async function fetchHtml(url: string, timeoutMs: number) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      redirect: "follow",
      headers: BROWSER_HEADERS,
    });
    if (!res.ok) return "";
    return (await res.text()).slice(0, 280_000);
  } catch {
    return "";
  } finally {
    clearTimeout(timer);
  }
}

function decodeUrl(raw: string) {
  try {
    return decodeURIComponent(raw.replace(/\+/g, " "));
  } catch {
    return raw;
  }
}

function stripTags(s: string) {
  return decodeHtml(s).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

export function parseDuckDuckGoHtml(html: string): WebHit[] {
  const hits: WebHit[] = [];
  const blocks = html.split(/result__body/i);
  for (const block of blocks.slice(1)) {
    const link = block.match(
      /class="result__a"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/i,
    );
    if (!link) continue;
    const href = decodeHtml(link[1]);
    let url = "";
    const uddg = href.match(/[?&]uddg=([^&]+)/i);
    if (uddg) url = decodeUrl(uddg[1]);
    else if (/^https?:\/\//i.test(href)) url = href;
    if (!url || !/^https?:\/\//i.test(url)) continue;
    const title = stripTags(link[2]);
    const snippetRaw =
      block.match(/class="result__snippet"[^>]*>([\s\S]*?)<\/a>/i)?.[1] ||
      block.match(/class="result__snippet"[^>]*>([\s\S]*?)<\/(?:div|a|span)>/i)?.[1] ||
      "";
    const snippet = stripTags(snippetRaw);
    hits.push({
      url,
      title,
      snippet,
      gbpPrice: extractGbpFromText(`${title} ${snippet}`),
    });
  }
  return hits;
}

function normalize(s: string) {
  return s
    .toLowerCase()
    .replace(/['"“”]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function asosProductId(url: string) {
  try {
    return new URL(url).pathname.match(/\/prd\/(\d+)/i)?.[1] || "";
  } catch {
    return "";
  }
}

function isRegionalAsos(url: string) {
  try {
    const first = new URL(url).pathname.split("/").filter(Boolean)[0] || "";
    return /^(us|au|fr|de|es|it|nl|pl|se|dk|no|ru|il|in|mx|row|at|be|ch)$/i.test(first);
  } catch {
    return false;
  }
}

function hostMatches(url: string, store: StoreBanner) {
  try {
    const host = new URL(url).hostname.toLowerCase().replace(/^www\./, "");
    return store.hosts.some((h) => host === h || host.endsWith(`.${h}`));
  } catch {
    return false;
  }
}

function scoreHit(query: string, hit: WebHit, store: StoreBanner) {
  const nq = normalize(query);
  const nt = normalize(hit.title);
  let score = 0;
  if (nt === nq) score += 100;
  else if (nt.includes(nq) || nq.includes(nt)) score += 70;
  else {
    const qw = nq.split(" ").filter(Boolean);
    const tw = new Set(nt.split(" ").filter(Boolean));
    const hitCount = qw.filter((w) => tw.has(w)).length;
    score += (hitCount / Math.max(qw.length, 1)) * 45;
  }
  if (hostMatches(hit.url, store)) score += 30;
  if (store.id === "asos" && asosProductId(hit.url)) score += 25;
  if (store.id === "asos" && isRegionalAsos(hit.url)) score -= 45;
  if (hit.gbpPrice) score += 12;
  return score;
}

async function searchDuckDuckGo(query: string) {
  const url = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
  const html = await fetchHtml(url, 10000);
  if (!html) return { hits: [] as WebHit[], html: "" };
  return { hits: parseDuckDuckGoHtml(html), html };
}

async function previewPdp(url: string, store: StoreBanner) {
  const html = await fetchHtml(url, 4500);
  if (!html) {
    return {
      title: "",
      image: "",
      gbpPrice: null as number | null,
    };
  }
  return {
    title: extractTitleFromHtml(html, store.nameEn),
    image: extractImageFromHtml(html),
    gbpPrice: extractGbpFromHtml(html),
  };
}

function searchQueryForStore(store: StoreBanner, query: string) {
  const host = store.hosts[0] || "asos.com";
  return `site:${host} ${query}`;
}

export async function lookupProduct(raw: string, storeId = "asos"): Promise<ProductLookup> {
  const resolved = resolveProductInput(raw, storeId);
  const query = resolved.kind === "search" ? resolved.title : raw.trim();
  const key = `${resolved.store.id}::${normalize(query)}`;
  const cached = cacheGet(key);
  if (cached) return cached;

  let url = resolved.url;
  let title = resolved.title;
  let image = "";
  let gbpPrice: number | null = null;
  let source: "url" | "search" = resolved.kind;
  let priceSource: "pdp" | "search" | null = null;
  const store = resolved.store;

  const directUrl =
    resolved.kind === "url" && !isStoreSearchUrl(resolved.url) ? resolved.url : "";

  if (directUrl) {
    const pdp = await previewPdp(directUrl, store);
    title = pdp.title || title;
    image = pdp.image;
    if (pdp.gbpPrice) {
      gbpPrice = pdp.gbpPrice;
      priceSource = "pdp";
    }
  }

  if (!gbpPrice || resolved.kind === "search") {
    const q =
      resolved.kind === "search"
        ? searchQueryForStore(store, resolved.title)
        : searchQueryForStore(store, title || query);
    const { hits, html } = await searchDuckDuckGo(q);
    const ranked = hits
      .map((hit) => ({ hit, score: scoreHit(resolved.title || query, hit, store) }))
      .filter((row) => row.score >= 40)
      .sort((a, b) => b.score - a.score);

    const best = ranked[0]?.hit;
    if (best) {
      if (resolved.kind === "search" || !directUrl) {
        url = best.url;
        source = hostMatches(best.url, store) && !isStoreSearchUrl(best.url) ? "url" : "search";
        title = best.title || title;
      }
      if (!gbpPrice && best.gbpPrice) {
        gbpPrice = best.gbpPrice;
        priceSource = "search";
      }
      if (!gbpPrice) {
        const priced = ranked.find((row) => {
          if (!row.hit.gbpPrice) return false;
          const sameId = asosProductId(best.url) && asosProductId(best.url) === asosProductId(row.hit.url);
          const sameTitle = normalize(row.hit.title) === normalize(best.title);
          return sameId || sameTitle;
        });
        if (priced?.hit.gbpPrice) {
          gbpPrice = priced.hit.gbpPrice;
          priceSource = "search";
        }
      }
      if (!gbpPrice) {
        const named = extractGbpForTitle(html, best.title || resolved.title || query);
        if (named) {
          gbpPrice = named;
          priceSource = "search";
        }
      }
    }

    if (source === "url" && url && !gbpPrice) {
      const pdp = await previewPdp(url, store);
      title = title || pdp.title;
      image = image || pdp.image;
      if (pdp.gbpPrice) {
        gbpPrice = pdp.gbpPrice;
        priceSource = "pdp";
      }
    }
  }

  if (!title) title = store.nameEn;
  if (source === "search" && !isHttpUrl(url)) {
    url = searchUrlForStore(store.id, query);
  }
  const knownStore = storeFromUrl(url);
  const value: ProductLookup = {
    query,
    url,
    title: title.slice(0, 200),
    image,
    gbpPrice,
    storeId: knownStore?.id || store.id,
    storeName: knownStore?.nameEn || store.nameEn,
    source,
    priceSource,
  };
  if (value.gbpPrice != null) cache.set(key, { at: Date.now(), value });
  return value;
}
