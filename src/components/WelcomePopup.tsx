"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { mediaUrl } from "@/lib/product-image";

const HIDE_KEY = "briq-welcome-hide-until";

const POINTS = [
  {
    label: "영국 현지 바잉 & 대한항공 직송",
    body: "히드로 공항 출항으로 안전하고 빠른 배송 (7~14일 소요)",
  },
  {
    label: "추가 비용 ZERO",
    body: "관부가세 전액 포함으로 표기된 금액 그대로",
  },
  {
    label: "안심 결제 & 혜택",
    body: "네이버페이 결제로 포인트 적립부터 100% 정품 보장까지",
  },
] as const;

function seoulMidnightStamp(): number {
  const now = new Date();
  const seoulNow = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Seoul" }));
  const end = new Date(seoulNow);
  end.setHours(24, 0, 0, 0);
  return Date.now() + (end.getTime() - seoulNow.getTime());
}

function WelcomeDialog({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
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
    onClose();
  };

  return createPortal(
    <div className="welcome-popup" role="presentation" onClick={onClose}>
      <div
        className="welcome-popup__panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="welcome-popup-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="welcome-popup__visual" aria-hidden>
          <img
            src={mediaUrl("/banners/hero-london.jpg")}
            alt=""
            draggable={false}
          />
        </div>
        <div className="welcome-popup__body">
          <button
            type="button"
            className="welcome-popup__close"
            aria-label="안내 닫기"
            onClick={onClose}
          >
            <svg viewBox="0 0 16 16" aria-hidden>
              <path d="M3 3l10 10M13 3L3 13" />
            </svg>
          </button>
          <p className="welcome-popup__eyebrow">Briq · London</p>
          <h2 id="welcome-popup-title" className="welcome-popup__title">
            <span>10년의 노하우, 100% 정품</span>
            <span>영국 직구를 가장 안전하게</span>
          </h2>
          <ul className="welcome-popup__points">
            {POINTS.map((point) => (
              <li key={point.label}>
                <strong>{point.label}</strong>
                <span>{point.body}</span>
              </li>
            ))}
          </ul>
          <button type="button" className="welcome-popup__cta" onClick={onClose}>
            쇼핑 계속하기
          </button>
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

/** Preview only. Opens on `?welcome=preview`, not for ordinary visits. */
export function WelcomePopupGate() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("welcome") !== "preview") return;
    setOpen(true);
  }, []);

  if (!open) return null;
  return <WelcomeDialog onClose={() => setOpen(false)} />;
}
