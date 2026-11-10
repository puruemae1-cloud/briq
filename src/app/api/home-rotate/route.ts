import { revalidatePath, revalidateTag } from "next/cache";
import { NextResponse } from "next/server";
import { HOMEPAGE_DATA_TAG } from "@/lib/homepage-feed";
import { seoulRotationDay } from "@/lib/homepage-rails";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

function cronAuthorized(req: Request): boolean {
  const secret = process.env.CRON_SECRET?.trim();
  if (!secret) return false;
  return req.headers.get("authorization") === `Bearer ${secret}`;
}

/**
 * Daily homepage luxury-rail rotation. Vercel Cron at 13:00 UTC (= 22:00 KST)
 * clears the home-data cache so the Seoul-seeded 4-product set refreshes.
 */
export async function GET(req: Request) {
  if (!cronAuthorized(req)) {
    return NextResponse.json({ ok: false }, { status: 401 });
  }
  const rotationDay = seoulRotationDay();
  revalidateTag(HOMEPAGE_DATA_TAG, { expire: 0 });
  revalidatePath("/");
  return NextResponse.json({
    ok: true,
    rotationDay,
    revalidated: [HOMEPAGE_DATA_TAG, "/"],
  });
}
