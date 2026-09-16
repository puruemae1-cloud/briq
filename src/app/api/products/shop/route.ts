import { NextRequest, NextResponse } from "next/server";
import { toCardProduct } from "@/lib/product-card-dto";
import {
  SHOP_PAGE_SIZE,
  getShopProductList,
  sliceShopPage,
} from "@/lib/shop-list";

const MAX_LIMIT = 48;

/** Large multi-brand catalogue needs headroom after YS import. */
export const maxDuration = 60;
export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const category = sp.get("category") ?? "all";
  const sub = sp.get("sub") ?? undefined;
  const q = sp.get("q") ?? undefined;
  const sort = sp.get("sort");
  const offset = Math.max(0, Number.parseInt(sp.get("offset") || "0", 10) || 0);
  const limitRaw = Number.parseInt(sp.get("limit") || String(SHOP_PAGE_SIZE), 10);
  const limit = Math.min(MAX_LIMIT, Math.max(1, limitRaw || SHOP_PAGE_SIZE));

  try {
    const list = getShopProductList({ category, sub, q, sort });
    const products = sliceShopPage(list, offset, limit).map(toCardProduct);

    return NextResponse.json(
      {
        products,
        total: list.length,
        offset,
        limit,
      },
      {
        headers: {
          "Cache-Control": "public, s-maxage=120, stale-while-revalidate=600",
          "CDN-Cache-Control": "public, s-maxage=120, stale-while-revalidate=600",
          "Vercel-CDN-Cache-Control":
            "public, s-maxage=120, stale-while-revalidate=600",
        },
      },
    );
  } catch (err) {
    console.error("[api/products/shop]", err);
    return NextResponse.json(
      { products: [], total: 0, offset, limit, error: "shop_unavailable" },
      { status: 503 },
    );
  }
}
