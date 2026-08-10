"use client";

import { useEffect, useId, useRef } from "react";
import {
  getNaverPayButtonKey,
  getNaverPaySiteOrigin,
  getNaverPayUrls,
  isNaverPayOrderEnabled,
} from "@/lib/naverpay/config";

type OrderItem = {
  productId: string;
  variantId?: string;
  braceletCm?: string;
  qty: number;
};

type Props = {
  /** PDP vs cart — cart turns wishlist / talkTalk off (manual). */
  page: "product" | "cart";
  items: OrderItem[];
  /** When false (OOS), button is not rendered. */
  enabled?: boolean;
  /** Prefer current page as backUrl. */
  backUrl?: string;
  className?: string;
};

type NpayBuyResult = { key: string; merchantNo: string };

type NpaySdk = {
  order: {
    create: (opts: Record<string, unknown>) => void;
  };
};

declare global {
  interface Window {
    Npay?: NpaySdk;
    wcs?: {
      inflow: (domain?: string) => void;
      checkoutWhitelist?: string[];
    };
    wcs_add?: Record<string, string>;
    wcs_do?: () => void;
  }
}

function loadButtonScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(
      `script[data-briq-npay-button="1"]`,
    );
    if (existing && window.Npay) {
      resolve();
      return;
    }
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener(
        "error",
        () => reject(new Error("Npay button SDK failed to load")),
        { once: true },
      );
      return;
    }
    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.dataset.briqNpayButton = "1";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Npay button SDK failed to load"));
    document.body.appendChild(script);
  });
}

/**
 * 주문형 V2.1 template button. onBuyClick → POST /api/naverpay/order → { key, merchantNo }.
 * Mobile uses the same APIs; SDK opens order sheet via location (not a popup).
 */
export function NaverPayOrderButton({
  page,
  items,
  enabled = true,
  backUrl,
  className,
}: Props) {
  const reactId = useId().replace(/:/g, "");
  const containerId = `npay-btn-${page}-${reactId}`;
  const itemsRef = useRef(items);
  itemsRef.current = items;
  const itemsKey = JSON.stringify(items);

  const show =
    isNaverPayOrderEnabled() &&
    enabled &&
    items.length > 0 &&
    Boolean(getNaverPayButtonKey());

  useEffect(() => {
    if (!show) return;
    let cancelled = false;
    const mountEl = document.getElementById(containerId);
    if (mountEl) mountEl.innerHTML = "";

    async function mount() {
      const buttonKey = getNaverPayButtonKey();
      const { buttonScript } = getNaverPayUrls();
      try {
        await loadButtonScript(buttonScript);
      } catch {
        return;
      }
      if (cancelled || !window.Npay) return;

      // Ensure inflow ran before button (manual requirement).
      try {
        if (window.wcs) {
          window.wcs.checkoutWhitelist = ["briq.kr", "www.briq.kr"];
          window.wcs.inflow("briq.kr");
        }
      } catch {
        /* ignore */
      }

      const origin = getNaverPaySiteOrigin();
      const resolvedBack =
        backUrl ||
        (typeof window !== "undefined" ? window.location.href : `${origin}/cart`);

      window.Npay.order.create({
        buttonKey,
        containerId,
        orderRegistrationVersion: "2.1",
        type: "template",
        colorTheme: "green",
        enable: true,
        components: {
          // Cart: wishlist / talkTalk off per manual. PDP: leave off until Talk Talk + wishlist API are configured.
          talkTalk: false,
          wishlist: false,
          benefitMessage: true,
          benefitCoachMark: page === "product",
        },
        onBuyClick: async (): Promise<NpayBuyResult | null> => {
          try {
            const res = await fetch("/api/naverpay/order", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                items: itemsRef.current,
                backUrl: resolvedBack,
              }),
            });
            const data = (await res.json()) as {
              ok?: boolean;
              key?: string;
              merchantNo?: string;
              message?: string;
            };
            if (!res.ok || !data.ok || !data.key || !data.merchantNo) {
              alert(data.message || "네이버페이 주문 등록에 실패했습니다.");
              return null;
            }
            return { key: data.key, merchantNo: data.merchantNo };
          } catch {
            alert("네이버페이 주문 등록 중 오류가 발생했습니다.");
            return null;
          }
        },
      });
    }

    void mount();
    return () => {
      cancelled = true;
    };
  }, [show, containerId, itemsKey, backUrl, page]);

  if (!show) return null;

  return (
    <div className={className ?? "npay-order-button"}>
      <div
        id={containerId}
        className="npay-order-button__mount"
        aria-label="네이버페이 구매"
      />
    </div>
  );
}
