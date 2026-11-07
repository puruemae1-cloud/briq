import { NextResponse } from "next/server";
import { buildHomepageData } from "@/lib/homepage-data";
import { CARD_DTO_VERSION, toCardProduct } from "@/lib/product-card-dto";
import { HOMEPAGE_DEPLOY_KEY } from "@/lib/homepage-feed";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

/**
 * Homepage product cards. Callers add `?v=<deployment>` so each deploy gets a
 * fresh CDN / Data Cache entry; the heavy catalogue parse runs once per deploy.
 *
 * Re-apply `toCardProduct` at the edge so a stale memo / older build cannot
 * ship fat PDP variants into Yeti HTML (Naver download-size).
 */
export async function GET() {
  const built = buildHomepageData();
  const body = {
    rails: Object.fromEntries(
      Object.entries(built.rails).map(([id, list]) => [
        id,
        list.map(toCardProduct),
      ]),
    ),
    flannels: (built.flannels ?? []).map(toCardProduct),
    signature: built.signature.map(toCardProduct),
    newItems: built.newItems.map(toCardProduct),
    deployKey: HOMEPAGE_DEPLOY_KEY,
    dto: CARD_DTO_VERSION,
  };
  return NextResponse.json(body, {
    headers: {
      "Cache-Control": "public, s-maxage=60, stale-while-revalidate=300",
      "CDN-Cache-Control": "public, s-maxage=60, stale-while-revalidate=300",
      "Vercel-CDN-Cache-Control":
        "public, s-maxage=60, stale-while-revalidate=300",
    },
  });
}
