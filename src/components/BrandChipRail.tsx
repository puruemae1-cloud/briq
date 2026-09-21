"use client";

import { useEffect, useRef, type ReactNode } from "react";

type BrandChipRailProps = {
  as?: "nav" | "div" | "ul";
  className?: string;
  children: ReactNode;
  "aria-label"?: string;
};

/**
 * Horizontal brand-chip scroller that works on mobile even when
 * `body { touch-action: pan-y }` blocks native pan-x.
 */
export function BrandChipRail({
  as = "nav",
  className,
  children,
  "aria-label": ariaLabel,
}: BrandChipRailProps) {
  const ref = useRef<HTMLElement | null>(null);
  const drag = useRef({
    tracking: false,
    axis: null as null | "h" | "v",
    startX: 0,
    startY: 0,
    startScroll: 0,
    moved: false,
  });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const onStart = (e: TouchEvent) => {
      if (el.scrollWidth <= el.clientWidth + 2) {
        drag.current.tracking = false;
        return;
      }
      const t = e.touches[0];
      if (!t) return;
      drag.current = {
        tracking: true,
        axis: null,
        startX: t.clientX,
        startY: t.clientY,
        startScroll: el.scrollLeft,
        moved: false,
      };
    };

    const onMove = (e: TouchEvent) => {
      const s = drag.current;
      if (!s.tracking) return;
      const t = e.touches[0];
      if (!t) return;
      const dx = t.clientX - s.startX;
      const dy = t.clientY - s.startY;

      if (!s.axis) {
        if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
        s.axis = Math.abs(dx) >= Math.abs(dy) ? "h" : "v";
      }

      if (s.axis === "h") {
        e.preventDefault();
        el.scrollLeft = s.startScroll - dx;
        if (Math.abs(dx) > 6) s.moved = true;
      } else {
        s.tracking = false;
      }
    };

    const onEnd = () => {
      drag.current.tracking = false;
      drag.current.axis = null;
    };

    el.addEventListener("touchstart", onStart, { passive: true });
    el.addEventListener("touchmove", onMove, { passive: false });
    el.addEventListener("touchend", onEnd, { passive: true });
    el.addEventListener("touchcancel", onEnd, { passive: true });

    const onClickCapture = (e: MouseEvent) => {
      if (drag.current.moved) {
        e.preventDefault();
        e.stopPropagation();
        drag.current.moved = false;
      }
    };
    el.addEventListener("click", onClickCapture, true);

    return () => {
      el.removeEventListener("touchstart", onStart);
      el.removeEventListener("touchmove", onMove);
      el.removeEventListener("touchend", onEnd);
      el.removeEventListener("touchcancel", onEnd);
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
