"use client";

import { useEffect, useState } from "react";

const HEARTBEAT_MS = 18_000;
const VID_KEY = "briq-vid";
const NO_TRACK_KEY = "briq-no-track";

function visitorId(): string {
  try {
    const existing = localStorage.getItem(VID_KEY);
    if (existing && /^[a-zA-Z0-9_-]+$/.test(existing)) return existing;
    const id =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID().replace(/-/g, "")
        : `v${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem(VID_KEY, id);
    return id;
  } catch {
    return `t${Date.now().toString(36)}`;
  }
}

function shouldSkipTrack(): boolean {
  try {
    return localStorage.getItem(NO_TRACK_KEY) === "1";
  } catch {
    return false;
  }
}

/**
 * Live “지금 N명이 이 제품을 보고 있어요” chip for PDP gallery.
 * Heartbeats into /api/presence; staff with briq-no-track still see the count
 * but do not inflate it.
 */
export function LiveViewersBadge({ productId }: { productId: string }) {
  const [display, setDisplay] = useState<number | null>(null);

  useEffect(() => {
    if (!productId) return;
    let cancelled = false;
    const skip = shouldSkipTrack();

    async function pulse() {
      try {
        if (skip) {
          const res = await fetch(
            `/api/presence?productId=${encodeURIComponent(productId)}`,
            { cache: "no-store" },
          );
          if (!res.ok || cancelled) return;
          const data = (await res.json()) as { display?: number };
          if (typeof data.display === "number" && !cancelled) {
            setDisplay(data.display);
          }
          return;
        }
        const res = await fetch("/api/presence", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ productId, visitorId: visitorId() }),
          cache: "no-store",
        });
        if (!res.ok || cancelled) return;
        const data = (await res.json()) as { display?: number };
        if (typeof data.display === "number" && !cancelled) {
          setDisplay(data.display);
        }
      } catch {
        /* keep last known */
      }
    }

    void pulse();
    const timer = window.setInterval(() => void pulse(), HEARTBEAT_MS);
    const onVis = () => {
      if (document.visibilityState === "visible") void pulse();
    };
    document.addEventListener("visibilitychange", onVis);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, [productId]);

  if (display == null || display < 1) return null;

  return (
    <div className="live-viewers" aria-live="polite">
      <span className="live-viewers__dot" aria-hidden="true" />
      <span className="live-viewers__text">
        지금 <span className="live-viewers__n">{display}</span>명이 이 제품을 보고
        있어요
      </span>
    </div>
  );
}
