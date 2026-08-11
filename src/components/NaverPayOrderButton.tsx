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
  /** product = PDP dock/inline, cart = cart page, dock = sticky bar (unique container). */
  page: "product" | "cart" | "dock";
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
    create: (opts: Record<string, unknown>) => void | Promise<unknown>;
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

function waitForLayout(el: HTMLElement, minWidth = 120, timeoutMs = 5000) {
  return new Promise<void>((resolve) => {
    const start = Date.now();
    const tick = () => {
      const w = el.getBoundingClientRect().width || el.clientWidth;
      if (w >= minWidth) {
        resolve();
        return;
      }
      if (Date.now() - start > timeoutMs) {
        resolve();
        return;
      }
      requestAnimationFrame(tick);
    };
    tick();
  });
}

/**
 * 주문형 V2.1 template button — buy only (wishlist / talkTalk optional per Naver).
 * onBuyClick → POST /api/naverpay/order → { key, merchantNo }.
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
    let sideObs: MutationObserver | undefined;
    const timers: number[] = [];
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

      const root = document.getElementById(containerId);
      if (!root || cancelled) return;

      // SDK sizes from container width. Dock: fill shared CTA slot; avoid
      // undersized mounts that clip the buy chrome to the right.
      const dock = page === "dock";
      if (dock) {
        root.style.minWidth = "100%";
        root.style.width = "100%";
        root.style.height = "100%";
        root.style.display = "grid";
        root.style.placeItems = "center";
        root.style.overflow = "hidden";
      } else {
        root.style.minWidth = "168px";
        root.style.width = "100%";
      }
      await waitForLayout(root, dock ? 80 : 120);
      if (cancelled) return;

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

      // Buy only — SDK defaults wishlist/talkTalk to true unless explicitly false.
      await Promise.resolve(
        window.Npay.order.create({
          buttonKey,
          containerId,
          orderRegistrationVersion: "2.1",
          type: "template",
          colorTheme: "green",
          enable: true,
          components: {
            wishlist: false,
            talkTalk: false,
            benefitMessage: false,
            benefitCoachMark: false,
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
        }),
      );

      if (cancelled) return;
      const stripSideButtons = () => {
        root
          .querySelectorAll(
            [
              ".npay_side_cell",
              ".npay_link_wishlist",
              ".npay_wishlist",
              ".npay_talktalk",
              ".npay_link_talktalk",
              '[data-npay-component="wishlist"]',
              '[data-npay-component="talktalk"]',
            ].join(", "),
          )
          .forEach((el) => el.remove());
      };

      const fitDockButton = () => {
        stripSideButtons();

        // SDK keeps type_three_button even when wishlist/talkTalk are false,
        // which locks .npay_main_cell to 60% width — force buy-only layout.
        root.querySelectorAll(".npay_button_sdk_wrapper").forEach((node) => {
          const el = node as HTMLElement;
          el.classList.remove(
            "type_three_button",
            "type_two_button",
            "size_small",
          );
          el.classList.add("type_one_button", "size_medium");
          el.style.width = "100%";
          el.style.height = "100%";
          el.style.margin = "0";
        });

        // Drop empty leftover table columns that leave a left/right gap.
        root.querySelectorAll("td, th").forEach((cell) => {
          const el = cell as HTMLElement;
          if (
            !el.textContent?.trim() &&
            !el.querySelector("a, button, img, iframe, svg")
          ) {
            el.remove();
          }
        });

        root.querySelectorAll("table").forEach((table) => {
          const t = table as HTMLElement;
          t.style.width = "100%";
          t.style.height = "100%";
          t.style.margin = "0";
          t.style.tableLayout = "fixed";
        });

        root
          .querySelectorAll(
            ".npay_button_area, .npay_btn_container, .npay_main_cell",
          )
          .forEach((node) => {
            const el = node as HTMLElement;
            el.style.display = "flex";
            el.style.alignItems = "center";
            el.style.justifyContent = "center";
            el.style.width = "100%";
            el.style.height = "100%";
            el.style.margin = "0";
            el.style.maxWidth = "100%";
          });

        root
          .querySelectorAll(
            ".npay_main_cell > a, .npay_btn_pay, .npay_link_order",
          )
          .forEach((node) => {
            const el = node as HTMLElement;
            el.style.display = "flex";
            el.style.alignItems = "center";
            el.style.justifyContent = "center";
            el.style.width = "100%";
            el.style.height = "100%";
            el.style.margin = "0";
            el.style.padding = "0";
            el.style.boxSizing = "border-box";
            el.style.gap = "0.25rem";
            el.style.lineHeight = "1";
          });
      };

      const polish = dock ? fitDockButton : stripSideButtons;
      polish();
      timers.push(
        window.setTimeout(polish, 250),
        window.setTimeout(polish, 800),
        window.setTimeout(polish, 1600),
      );
      sideObs = new MutationObserver(polish);
      sideObs.observe(root, { childList: true, subtree: true });
    }

    void mount();
    return () => {
      cancelled = true;
      sideObs?.disconnect();
      timers.forEach((t) => window.clearTimeout(t));
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
