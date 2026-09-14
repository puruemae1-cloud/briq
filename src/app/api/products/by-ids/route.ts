import { NextRequest, NextResponse } from "next/server";
import { getProduct, type Product } from "@/data/products";
import { toCardProduct } from "@/lib/product-card-dto";

const MAX_IDS = 24;

export async function GET(req: NextRequest) {
  const raw = req.nextUrl.searchParams.get("ids") || "";
  const ids = [
    ...new Set(
      raw
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    ),
  ].slice(0, MAX_IDS);

  if (ids.length === 0) {
    return NextResponse.json({ products: [] as Product[] });
  }

  const products = ids
    .map((id) => getProduct(id))
    .filter((p): p is Product => Boolean(p))
    .map(toCardProduct);

  return NextResponse.json(
    { products },
    {
      headers: {
        "Cache-Control": "public, s-maxage=60, stale-while-revalidate=300",
      },
    },
  );
}
