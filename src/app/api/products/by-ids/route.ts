import { NextRequest, NextResponse } from "next/server";
import { getProduct, type Product } from "@/data/products";

const MAX_IDS = 24;

/** Slim product for PLP/cards — omit heavy PDP-only fields. */
function toCardProduct(p: Product): Product {
  return {
    id: p.id,
    name: p.name,
    nameKo: p.nameKo,
    brand: p.brand,
    price: p.price,
    compareAtPrice: p.compareAtPrice,
    category: p.category,
    subcategory: p.subcategory,
    tags: p.tags,
    image: p.image,
    images: p.images?.slice(0, 8),
    hoverImage: p.hoverImage,
    accent: p.accent,
    badge: p.badge,
    sku: p.sku,
    inStock: p.inStock,
    registeredAt: p.registeredAt,
    editTier: p.editTier,
    shopColorKey: p.shopColorKey,
    cwCollections: p.cwCollections,
    ggCollections: p.ggCollections,
    variants: p.variants?.map((v) => ({
      id: v.id,
      name: v.name,
      nameKo: v.nameKo,
      sku: v.sku,
      gbpPrice: v.gbpPrice,
      price: v.price,
      compareAtPrice: v.compareAtPrice,
      image: v.image,
      images: v.images?.slice(0, 4),
      hoverImage: v.hoverImage,
      sourceUrl: v.sourceUrl,
      inStock: v.inStock,
      colorKey: v.colorKey,
      colorNameKo: v.colorNameKo,
      size: v.size,
    })),
  };
}

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
