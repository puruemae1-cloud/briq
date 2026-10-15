import { revalidatePath, revalidateTag } from "next/cache";
import { NextResponse } from "next/server";
import { HOMEPAGE_DATA_TAG, HOMEPAGE_DEPLOY_KEY } from "@/lib/homepage-feed";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

/**
 * Re-renders the homepage when its live HTML was built from an older
 * deployment's cards (the prerender runs before this deployment is live).
 * No-op when already current, so it is safe to call publicly and repeatedly.
 */
export async function GET() {
  const host = process.env.VERCEL_PROJECT_PRODUCTION_URL;
  if (!host) return NextResponse.json({ stale: false, skipped: "no host" });

  let builtWith: string | null = null;
  try {
    const res = await fetch(`https://${host}/`, {
      cache: "no-store",
      headers: { "User-Agent": "briq-home-refresh" },
      signal: AbortSignal.timeout(45_000),
    });
    const html = await res.text();
    builtWith = html.match(/data-cards-deploy="([^"]*)"/)?.[1] ?? null;
  } catch (err) {
    console.error("[home-data/refresh] homepage fetch failed", err);
  }
  if (builtWith === HOMEPAGE_DEPLOY_KEY) {
    return NextResponse.json({ stale: false });
  }

  revalidateTag(HOMEPAGE_DATA_TAG, { expire: 0 });
  revalidatePath("/");
  return NextResponse.json({ stale: true, builtWith });
}
