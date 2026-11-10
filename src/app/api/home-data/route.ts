import { NextResponse } from "next/server";
import { buildHomepageData } from "@/lib/homepage-data";
import { CARD_DTO_VERSION, toCardProduct } from "@/lib/product-card-dto";
import { HOMEPAGE_DEPLOY_KEY } from "@/lib/homepage-feed";
import {
  secondsUntilNextSeoulRotation,
  seoulRotationDay,
} from "@/lib/homepage-rails";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

/**
 * Homepage product cards. Callers add `?v=<deployment>&day=<rotationDay>` so
 * each deploy and each 22:00 KST flip gets a fresh CDN / Data Cache entry.
 *
 * Re-apply `toCardProduct` at the edge so a stale memo / older build cannot
 * ship fat PDP variants into Yeti HTML (Naver download-size).
 */
export async function GET() {
  const built = buildHomepageData();
  const rotationDay = seoulRotationDay();
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
    rotationDay,
    dto: CARD_DTO_VERSION,
  };
  const maxAge = Math.min(300, secondsUntilNextSeoulRotation());
  return NextResponse.json(body, {
    headers: {
      "Cache-Control": `public, s-maxage=${maxAge}, stale-while-revalidate=60`,
      "CDN-Cache-Control": `public, s-maxage=${maxAge}, stale-while-revalidate=60`,
      "Vercel-CDN-Cache-Control": `public, s-maxage=${maxAge}, stale-while-revalidate=60`,
    },
  });
}
