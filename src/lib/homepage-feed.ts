import type { HomepageData } from "@/lib/homepage-data";
import {
  secondsUntilNextSeoulRotation,
  seoulRotationDay,
} from "@/lib/homepage-rails";

/**
 * Homepage product cards for `app/page.tsx` / `Collection100`.
 *
 * Fetched from `/api/home-data` (CDN + Next Data Cache, keyed per deployment
 * and Seoul rotation day) so the `/` bundle never contains the brand catalogues.
 * Must not statically import `@/lib/homepage-data` or `@/data/products`.
 *
 * At build time the production host is still the previous deployment, so the
 * prerendered cards can be one deploy behind. Responses carry `deployKey`
 * (rendered as `data-cards-deploy`); `/api/home-data/refresh`, called after
 * every deploy, re-renders the homepage when it doesn't match.
 *
 * `?day=` forces a new cache entry at every 22:00 KST flip even if the
 * nightly cron is late; `revalidate` expires just before the next flip.
 */
export const HOMEPAGE_DEPLOY_KEY =
  process.env.VERCEL_DEPLOYMENT_ID ||
  process.env.VERCEL_GIT_COMMIT_SHA ||
  "local";
export const HOMEPAGE_DATA_TAG = "home-data";
const EMPTY: HomepageData = {
  rails: {},
  flannels: [],
  signature: [],
  newItems: [],
};

function feedUrl(): string | null {
  const host = process.env.VERCEL_PROJECT_PRODUCTION_URL;
  if (!process.env.VERCEL || !host) return null;
  const day = seoulRotationDay();
  return `https://${host}/api/home-data?v=${encodeURIComponent(HOMEPAGE_DEPLOY_KEY)}&day=${encodeURIComponent(day)}`;
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
        next: {
          // Expire by the next 22:00 KST flip (cap 6h so a stuck clock still refreshes).
          revalidate: Math.min(6 * 60 * 60, secondsUntilNextSeoulRotation()),
          tags: [HOMEPAGE_DATA_TAG],
        },
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
