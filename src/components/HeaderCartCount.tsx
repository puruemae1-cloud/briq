"use client";

import { usePathname } from "next/navigation";
import { useEffect, useSyncExternalStore } from "react";
import {
  CART_COUNT_COOKIE,
  CART_COUNT_EVENT,
} from "@/lib/cart-count-cookie";

const COUNT_RE = new RegExp(`(?:^|;\\s*)${CART_COUNT_COOKIE}=(\\d+)`);

/** -1 = cookie not set yet (legacy cart or first visit). */
function readCount(): number {
  const m = COUNT_RE.exec(document.cookie);
  return m ? Number(m[1]) : -1;
}

function subscribe(onChange: () => void) {
  window.addEventListener(CART_COUNT_EVENT, onChange);
  window.addEventListener("focus", onChange);
  document.addEventListener("visibilitychange", onChange);
  return () => {
    window.removeEventListener(CART_COUNT_EVENT, onChange);
    window.removeEventListener("focus", onChange);
    document.removeEventListener("visibilitychange", onChange);
  };
}

export function notifyCartCountChanged() {
  window.dispatchEvent(new Event(CART_COUNT_EVENT));
}

export function HeaderCartCount() {
  const pathname = usePathname();
  const count = useSyncExternalStore(subscribe, readCount, () => 0);

  useEffect(() => {
    notifyCartCountChanged();
  }, [pathname]);

  useEffect(() => {
    if (readCount() !== -1) return;
    void fetch("/api/cart/count", { cache: "no-store" })
      .then(() => notifyCartCountChanged())
      .catch(() => {});
  }, []);

  return count > 0 ? <span className="cart-count">{count}</span> : null;
}

/** Drop into dynamic cart pages so qty edits refresh the header badge. */
export function CartCountSync({ count }: { count: number }) {
  useEffect(() => {
    notifyCartCountChanged();
  }, [count]);
  return null;
}
