"use client";

import { useEffect, useSyncExternalStore } from "react";
import { usePathname } from "next/navigation";
import { CART_CHANGE_EVENT, CART_COUNT_COOKIE } from "@/lib/cart-cookie";

const COUNT_RE = new RegExp(`(?:^|; )${CART_COUNT_COOKIE}=(\\d+)`);

/** -1 when the count cookie is missing (carts saved before it existed). */
function readCount(): number {
  const m = document.cookie.match(COUNT_RE);
  return m ? Number(m[1]) : -1;
}

function subscribe(onChange: () => void) {
  window.addEventListener(CART_CHANGE_EVENT, onChange);
  window.addEventListener("focus", onChange);
  document.addEventListener("visibilitychange", onChange);
  return () => {
    window.removeEventListener(CART_CHANGE_EVENT, onChange);
    window.removeEventListener("focus", onChange);
    document.removeEventListener("visibilitychange", onChange);
  };
}

export function CartCountBadge() {
  const pathname = usePathname();
  const count = useSyncExternalStore(subscribe, readCount, () => 0);

  useEffect(() => {
    if (readCount() >= 0) return;
    fetch("/api/cart/count", { cache: "no-store" })
      .then(() => window.dispatchEvent(new Event(CART_CHANGE_EVENT)))
      .catch(() => {});
  }, []);

  // Cart server actions redirect or refresh; re-read the cookie they set.
  useEffect(() => {
    window.dispatchEvent(new Event(CART_CHANGE_EVENT));
  }, [pathname]);

  return count > 0 ? <span className="cart-count">{count}</span> : null;
}
