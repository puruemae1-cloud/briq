import { NextResponse } from "next/server";
import { CART_COOKIE_MAX_AGE, CART_COUNT_COOKIE } from "@/lib/cart-cookie";
import { getCartCount } from "@/lib/cart-count";

export const dynamic = "force-dynamic";

/** Backfills the readable count cookie for carts saved before it existed. */
export async function GET() {
  const count = await getCartCount();
  const res = NextResponse.json({ count }, { headers: { "Cache-Control": "no-store" } });
  res.cookies.set(CART_COUNT_COOKIE, String(count), {
    path: "/",
    sameSite: "lax",
    maxAge: CART_COOKIE_MAX_AGE,
  });
  return res;
}
