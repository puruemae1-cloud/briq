import { NextResponse } from "next/server";
import { buildHomepageData } from "@/lib/homepage-data";
import { HOMEPAGE_DEPLOY_KEY } from "@/lib/homepage-feed";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

/**
 * Homepage product cards. Callers add `?v=<deployment>` so each deploy gets a
 * fresh CDN / Data Cache entry; the heavy catalogue parse runs once per deploy.
 */
export async function GET() {
  return NextResponse.json(
    { ...buildHomepageData(), deployKey: HOMEPAGE_DEPLOY_KEY },
    {
      headers: {
        "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=86400",
      },
    },
  );
}
