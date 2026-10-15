import type { HomepageData } from "@/lib/homepage-data";

/**
 * Homepage product cards for `app/page.tsx` / `Collection100`.
 *
 * Fetched from `/api/home-data` (CDN + Next Data Cache, keyed per deployment)
 * so the `/` bundle never contains the brand catalogues. Must not statically
 * import `@/lib/homepage-data` or `@/data/products`.
 *
 * At build time the production host is still the previous deployment, so the
 * prerendered cards can be one deploy behind. Responses carry `deployKey`;
 * `/api/home-data/refresh` (called after every deploy) re-fetches when stale.
 */
export const HOMEPAGE_DEPLOY_KEY =
  process.env.VERCEL_DEPLOYMENT_ID ||
  process.env.VERCEL_GIT_COMMIT_SHA ||
  "local";
export const HOMEPAGE_DATA_TAG = "home-data";
const TTL_SECONDS = 3600;
const EMPTY: HomepageData = { rails: {}, signature: [], newItems: [] };

/** True when the cards were built by this deployment's code. */
export function isCurrentHomepageData(data: HomepageData): boolean {
  return data.deployKey === HOMEPAGE_DEPLOY_KEY;
}

function feedUrl(): string | null {
  const host = process.env.VERCEL_PROJECT_PRODUCTION_URL;
  if (!process.env.VERCEL || !host) return null;
  return `https://${host}/api/home-data?v=${encodeURIComponent(HOMEPAGE_DEPLOY_KEY)}`;
}

async function buildLocally(): Promise<HomepageData> {
  const { buildHomepageData } = await import("@/lib/homepage-data");
  return { ...buildHomepageData(), deployKey: HOMEPAGE_DEPLOY_KEY };
}

export async function getHomepageData(): Promise<HomepageData> {
  const url = feedUrl();
  if (url) {
    try {
      const res = await fetch(url, {
        next: { revalidate: TTL_SECONDS, tags: [HOMEPAGE_DATA_TAG] },
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
