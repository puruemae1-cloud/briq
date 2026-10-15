import { revalidatePath, revalidateTag } from "next/cache";
import { NextResponse } from "next/server";
import {
  getHomepageData,
  HOMEPAGE_DATA_TAG,
  isCurrentHomepageData,
} from "@/lib/homepage-feed";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

/**
 * Re-fetches the homepage cards when the cached copy was built by an older
 * deployment (the prerender runs before this deployment is live). No-op when
 * already current, so it is safe to call publicly and repeatedly.
 */
export async function GET() {
  const data = await getHomepageData();
  if (isCurrentHomepageData(data)) {
    return NextResponse.json({ stale: false });
  }
  revalidateTag(HOMEPAGE_DATA_TAG, { expire: 0 });
  revalidatePath("/");
  return NextResponse.json({ stale: true, cachedFrom: data.deployKey ?? null });
}
