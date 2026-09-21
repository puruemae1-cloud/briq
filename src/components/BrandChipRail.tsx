"use client";

import { useEffect, useRef, type ReactNode } from "react";

type BrandChipRailProps = {
  as?: "nav" | "div" | "ul";
  className?: string;
  children: ReactNode;
  "aria-label"?: string;
};

/**
 * Brand chip rail — relies on native overflow scrolling (momentum + 1:1 finger
 * tracking). Only suppresses link clicks after a horizontal drag.
 */
export function BrandChipRail({
  as = "nav",
  className,
  children,
  "aria-label": ariaLabel,
}: BrandChipRailProps) {
  const ref = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    let startX = 0;
    let startScroll = 0;
    let dragged = false;

    const onStart = (e: TouchEvent) => {
      const t = e.touches[0];
      if (!t) return;
      startX = t.clientX;
      startScroll = el.scrollLeft;
      dragged = false;
    };

    const onMove = (e: TouchEvent) => {
      const t = e.touches[0];
      if (!t) return;
      if (
        Math.abs(t.clientX - startX) > 8 ||
        Math.abs(el.scrollLeft - startScroll) > 2
      ) {
        dragged = true;
      }
    };

    const onClickCapture = (e: MouseEvent) => {
      if (!dragged) return;
      e.preventDefault();
      e.stopPropagation();
      dragged = false;
    };

    el.addEventListener("touchstart", onStart, { passive: true });
    el.addEventListener("touchmove", onMove, { passive: true });
    el.addEventListener("click", onClickCapture, true);

    return () => {
      el.removeEventListener("touchstart", onStart);
      el.removeEventListener("touchmove", onMove);
      el.removeEventListener("click", onClickCapture, true);
    };
  }, []);

  const setRef = (node: HTMLElement | null) => {
    ref.current = node;
  };

  if (as === "ul") {
    return (
      <ul ref={setRef} className={className} aria-label={ariaLabel}>
        {children}
      </ul>
    );
  }
  if (as === "div") {
    return (
      <div ref={setRef} className={className} aria-label={ariaLabel}>
        {children}
      </div>
    );
  }
  return (
    <nav ref={setRef} className={className} aria-label={ariaLabel}>
      {children}
    </nav>
  );
}
