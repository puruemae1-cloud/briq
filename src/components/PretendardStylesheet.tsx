"use client";

import { useEffect } from "react";

const HREF =
  "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css";

/** Load Pretendard without blocking first paint. */
export function PretendardStylesheet() {
  useEffect(() => {
    if (document.querySelector(`link[data-briq-pretendard]`)) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = HREF;
    link.crossOrigin = "anonymous";
    link.dataset.briqPretendard = "1";
    document.head.appendChild(link);
  }, []);
  return null;
}
