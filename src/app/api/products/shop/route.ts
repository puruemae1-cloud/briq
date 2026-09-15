import { NextRequest, NextResponse } from "next/server";
import { SHOP_PAGE_SIZE, getShopCardPage } from "@/lib/shop-list";

const MAX_LIMIT = 48;

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const category = sp.get("category") ?? "all";
  const sub = sp.get("sub") ?? undefined;
  const q = sp.get("q") ?? undefined;
  const sort = sp.get("sort");
  const offset = Math.max(0, Number.parseInt(sp.get("offset") || "0", 10) || 0);
  const limitRaw = Number.parseInt(sp.get("limit") || String(SHOP_PAGE_SIZE), 10);
  const limit = Math.min(MAX_LIMIT, Math.max(1, limitRaw || SHOP_PAGE_SIZE));

  const { products, total } = getShopCardPage(
    { category, sub, q, sort },
    offset,
    limit,
  );

  return NextResponse.json(
    {
      products,
      total,
      offset,
      limit,
    },
    {
      headers: {
        // CDN edge: warm "더보기" hits should be sub-second after first miss.
        "Cache-Control": "public, s-maxage=120, stale-while-revalidate=600",
        "CDN-Cache-Control": "public, s-maxage=120, stale-while-revalidate=600",
        "Vercel-CDN-Cache-Control":
          "public, s-maxage=120, stale-while-revalidate=600",
      },
    },
  );
}
