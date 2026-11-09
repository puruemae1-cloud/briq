"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { mediaUrl, mediaUrlFallback } from "@/lib/product-image";
import { seoulMidnightStamp } from "@/components/WelcomePopup";

export const FLANNELS_HIDE_KEY = "briq-flannels-promo-hide-until";
export const FLANNELS_SEEN_KEY = "briq-flannels-promo-seen";

const HREF = "/shop?category=luxury&sub=flannels";
const DESKTOP = "/banners/flannels-promo.jpg";
const MOBILE = "/banners/flannels-promo-m.jpg";

export function flannelsHiddenForNow(): boolean {
  try {
    const until = Number(localStorage.getItem(FLANNELS_HIDE_KEY) || 0);
    if (until > Date.now()) return true;
    return sessionStorage.getItem(FLANNELS_SEEN_KEY) === "1";
  } catch {
    return false;
  }
}

function PromoPhoto({ mobile }: { mobile: boolean }) {
  const path = mobile ? MOBILE : DESKTOP;
  const primary = mediaUrl(path);
  const [src, setSrc] = useState(primary);
  return (
    <img
      src={src}
      alt="FLANNELS 프로모션"
      draggable={false}
      referrerPolicy="no-referrer"
      onError={() => {
        const next = mediaUrlFallback(path);
        if (next && next !== src) setSrc(next);
      }}
    />
  );
}

function rememberFlannelsSeen() {
  try {
    sessionStorage.setItem(FLANNELS_SEEN_KEY, "1");
  } catch {
    /* private mode */
  }
}

/** Cream two-column shell shared with Welcome — original Flannels copy. */
export function FlannelsPromoDialog({ onClose }: { onClose: () => void }) {
  const [mobile, setMobile] = useState(false);

  const close = () => {
    rememberFlannelsSeen();
    onClose();
  };

  useEffect(() => {
    const mq = window.matchMedia("(max-width: 720px)");
    const sync = () => setMobile(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      rememberFlannelsSeen();
      onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener("keydown", onKey);
    };
  }, [onClose]);

  const dismissForToday = () => {
    try {
      localStorage.setItem(FLANNELS_HIDE_KEY, String(seoulMidnightStamp()));
    } catch {
      /* private mode */
    }
    close();
  };

  return createPortal(
    <div className="welcome-popup" role="presentation" onClick={close}>
      <div
        className="welcome-popup__panel welcome-popup__panel--flannels"
        role="dialog"
        aria-modal="true"
        aria-labelledby="flannels-promo-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="welcome-popup__visual" aria-hidden>
          <PromoPhoto mobile={mobile} />
        </div>
        <div className="welcome-popup__body">
          <button
            type="button"
            className="welcome-popup__close"
            aria-label="안내 닫기"
            onClick={close}
          >
            <svg viewBox="0 0 16 16" aria-hidden>
              <path d="M3 3l10 10M13 3L3 13" />
            </svg>
          </button>
          <p className="welcome-popup__eyebrow">FLANNELS</p>
          <h2 id="flannels-promo-title" className="welcome-popup__title">
            <span>플라날스 영국 하이엔드 컬렉션</span>
          </h2>
          <p className="welcome-popup__support">
            희소성 높은 명품 아이템을 오직 선택받은 혜택가로 만나보세요.
          </p>
          <Link href={HREF} className="welcome-popup__cta" onClick={close}>
            FLANNELS SHOP
          </Link>
          <button
            type="button"
            className="welcome-popup__later"
            onClick={dismissForToday}
          >
            오늘 하루 보지 않기
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
