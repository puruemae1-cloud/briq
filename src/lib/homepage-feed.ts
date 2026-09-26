import type { HomepageData } from "@/lib/homepage-data";

/**
 * Homepage product cards for `app/page.tsx` / `Collection100`.
 *
 * Fetched from `/api/home-data` (CDN + Next Data Cache, keyed per deployment)
 * so the `/` bundle never contains the brand catalogues. Must not statically
 * import `@/lib/homepage-data` or `@/data/products`.
 */
const DEPLOY_KEY =
  process.env.VERCEL_DEPLOYMENT_ID ||
  process.env.VERCEL_GIT_COMMIT_SHA ||
  "local";
const TTL_SECONDS = 3600;
const EMPTY: HomepageData = { rails: {}, signature: [], newItems: [] };

function feedUrl(): string | null {
  const host = process.env.VERCEL_PROJECT_PRODUCTION_URL;
  if (!process.env.VERCEL || !host) return null;
  return `https://${host}/api/home-data?v=${encodeURIComponent(DEPLOY_KEY)}`;
}

async function buildLocally(): Promise<HomepageData> {
  const { buildHomepageData } = await import("@/lib/homepage-data");
  return buildHomepageData();
}

export async function getHomepageData(): Promise<HomepageData> {
  const url = feedUrl();
  if (url) {
    try {
      const res = await fetch(url, {
        next: { revalidate: TTL_SECONDS },
        signal: AbortSignal.timeout(25_000),
      });
      if (res.ok) return (await res.json()) as HomepageData;
      console.error(`[homepage-feed] ${url} → ${res.status}`);
    } catch (err) {
      console.error("[homepage-feed] fetch failed", err);
    }
  }
  try {
    return await buildLocally();
  } catch (err) {
    console.error("[homepage-feed] local build failed", err);
    return EMPTY;
  }
}
