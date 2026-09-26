import { NextResponse } from "next/server";
import { buildHomepageData } from "@/lib/homepage-data";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

/**
 * Homepage product cards. Callers add `?v=<deployment>` so each deploy gets a
 * fresh CDN / Data Cache entry; the heavy catalogue parse runs once per deploy.
 */
export async function GET() {
  return NextResponse.json(buildHomepageData(), {
    headers: {
      "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=86400",
    },
  });
}
