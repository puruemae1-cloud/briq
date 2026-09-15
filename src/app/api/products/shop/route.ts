import { NextRequest, NextResponse } from "next/server";
import {
  SHOP_PAGE_SIZE,
  getShopListBundle,
  sliceShopPage,
} from "@/lib/shop-list";

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

  const { cards } = getShopListBundle({ category, sub, q, sort });
  const products = sliceShopPage(cards, offset, limit);

  return NextResponse.json(
    {
      products,
      total: cards.length,
      offset,
      limit,
    },
    {
      headers: {
        // CDN + browser: warm "더보기" hits stay under ~1–2s.
        "Cache-Control": "public, s-maxage=60, stale-while-revalidate=300",
      },
    },
  );
}
