"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { mediaUrl, mediaUrlFallback } from "@/lib/product-image";

const HIDE_KEY = "briq-flannels-promo-hide-until";
const SEEN_KEY = "briq-flannels-promo-seen";
const HREF = "/shop?category=luxury&sub=flannels";
const DESKTOP = "/banners/flannels-promo.jpg";
const MOBILE = "/banners/flannels-promo-m.jpg";

function hiddenForNow(): boolean {
  try {
    const until = Number(localStorage.getItem(HIDE_KEY) || 0);
    if (until > Date.now()) return true;
    return sessionStorage.getItem(SEEN_KEY) === "1";
  } catch {
    return false;
  }
}

function seoulMidnightStamp(): number {
  const now = new Date();
  const seoulNow = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Seoul" }));
  const end = new Date(seoulNow);
  end.setHours(24, 0, 0, 0);
  return Date.now() + (end.getTime() - seoulNow.getTime());
}

function PromoPhoto({ mobile }: { mobile: boolean }) {
  const path = mobile ? MOBILE : DESKTOP;
  const primary = mediaUrl(path);
  const [src, setSrc] = useState(primary);
  return (
    <img
      src={src}
      alt=""
      draggable={false}
      referrerPolicy="no-referrer"
      onError={() => {
        const next = mediaUrlFallback(path);
        if (next && next !== src) setSrc(next);
      }}
    />
  );
}

function rememberSeen() {
  try {
    sessionStorage.setItem(SEEN_KEY, "1");
  } catch {
    /* private mode */
  }
}

function WelcomeDialog({ onClose }: { onClose: () => void }) {
  const [mobile, setMobile] = useState(false);

  const close = () => {
    rememberSeen();
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
      rememberSeen();
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
      localStorage.setItem(HIDE_KEY, String(seoulMidnightStamp()));
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
        aria-labelledby="welcome-popup-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="welcome-popup__visual" aria-hidden>
          <PromoPhoto mobile={mobile} />
          <div className="welcome-popup__shade" />
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
          <h2 id="welcome-popup-title" className="welcome-popup__title">
            플라날스 영국 하이엔드 컬렉션
          </h2>
          <p className="welcome-popup__support">
            희소성 높은 명품 아이템을 오직 선택받은 혜택가로 만나보세요.
          </p>

          <Link href={HREF} className="welcome-popup__cta" onClick={close}>
            FLANNELS SHOP →
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

/** Flannels promo on arrival. Hidden until Seoul midnight after “오늘 하루 보지 않기”, and for the rest of the tab after a close. `?welcome=preview` always opens it. */
export function WelcomePopupGate() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("welcome") === "preview" || !hiddenForNow()) setOpen(true);
  }, []);

  if (!open) return null;
  return <WelcomeDialog onClose={() => setOpen(false)} />;
}
