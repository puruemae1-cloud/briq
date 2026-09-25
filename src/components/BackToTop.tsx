"use client";

import { useCallback, useEffect, useRef, useState, type MouseEvent } from "react";

/** Snappy ease — quicker settle than CSS `scroll-behavior: smooth`. */
function easeOutCubic(t: number) {
  return 1 - (1 - t) ** 3;
}

/**
 * AllSaints-style back-to-top: short, velocity-forward scroll (not a slow
 * browser smooth-scroll). Mounted once in the root layout → every page.
 */
export function BackToTop() {
  const [visible, setVisible] = useState(false);
  const animRef = useRef<number | null>(null);

  const cancelScroll = useCallback(() => {
    if (animRef.current != null) {
      cancelAnimationFrame(animRef.current);
      animRef.current = null;
    }
  }, []);

  useEffect(() => {
    const onScroll = () => {
      setVisible(window.scrollY > 420);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const stop = () => cancelScroll();
    window.addEventListener("wheel", stop, { passive: true });
    window.addEventListener("touchstart", stop, { passive: true });
    window.addEventListener("keydown", stop);
    return () => {
      window.removeEventListener("wheel", stop);
      window.removeEventListener("touchstart", stop);
      window.removeEventListener("keydown", stop);
      cancelScroll();
    };
  }, [cancelScroll]);

  const scrollToTop = useCallback(
    (e: MouseEvent<HTMLButtonElement>) => {
      e.preventDefault();
      cancelScroll();

      const startY = window.scrollY || document.documentElement.scrollTop;
      if (startY <= 0) return;

      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (reduced) {
        window.scrollTo(0, 0);
        return;
      }

      // Cap duration so long PLPs still feel snappy (~AllSaints zip).
      const duration = Math.min(520, Math.max(260, startY * 0.28));
      const start = performance.now();

      const tick = (now: number) => {
        const t = Math.min(1, (now - start) / duration);
        const y = Math.round(startY * (1 - easeOutCubic(t)));
        window.scrollTo(0, y);
        if (t < 1) {
          animRef.current = requestAnimationFrame(tick);
        } else {
          animRef.current = null;
        }
      };
      animRef.current = requestAnimationFrame(tick);
    },
    [cancelScroll],
  );

  return (
    <button
      type="button"
      className={`back-to-top${visible ? " is-visible" : ""}`}
      aria-label="맨 위로"
      onClick={scrollToTop}
    >
      <span aria-hidden="true">↑</span>
    </button>
  );
}
