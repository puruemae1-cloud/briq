import { NextResponse } from "next/server";
import { getCartCount } from "@/lib/cart-count";
import { CART_COUNT_COOKIE } from "@/lib/cart-count-cookie";

export const dynamic = "force-dynamic";

/** Backfills `briq-cart-n` for carts created before the header went client-side. */
export async function GET() {
  const count = await getCartCount();
  const res = NextResponse.json({ count });
  res.headers.set("Cache-Control", "no-store");
  res.cookies.set(CART_COUNT_COOKIE, String(count), {
    path: "/",
    httpOnly: false,
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 30,
  });
  return res;
}
