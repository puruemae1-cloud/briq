"use client";

import { useCallback, useEffect, useState, type MouseEvent } from "react";
import { createPortal } from "react-dom";
import { Check, Share2 } from "lucide-react";

type Props = {
  title: string;
  /** Absolute or path URL. Defaults to current page. */
  url?: string;
  className?: string;
  /** Compact icon-only mark for dense headers. */
  compact?: boolean;
};

function resolveUrl(url?: string) {
  if (typeof window === "undefined") return url || "";
  if (!url) return window.location.href;
  if (url.startsWith("http")) return url;
  return new URL(url, window.location.origin).toString();
}

async function copyText(text: string) {
  if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  document.execCommand("copy");
  document.body.removeChild(ta);
}

export function ShareLinkButton({
  title,
  url,
  className,
  compact = false,
}: Props) {
  const [copied, setCopied] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const onShare = useCallback(
    async (e: MouseEvent<HTMLButtonElement>) => {
      e.preventDefault();
      e.stopPropagation();
      const href = resolveUrl(url);
      try {
        await copyText(href);
        setCopied(true);
        window.setTimeout(() => setCopied(false), 2000);
      } catch {
        window.prompt("링크를 복사하세요", href);
      }
    },
    [url],
  );

  return (
    <>
      <button
        type="button"
        className={[
          "share-link",
          compact ? "share-link--compact" : "",
          copied ? "is-copied" : "",
          className || "",
        ]
          .filter(Boolean)
          .join(" ")}
        onClick={onShare}
        aria-label={copied ? "링크가 복사되었습니다" : "링크 복사"}
        title={copied ? "링크가 복사되었습니다" : "링크 복사"}
      >
        <span className="share-link__mark" aria-hidden>
          {copied ? (
            <Check size={compact ? 14 : 15} strokeWidth={2.25} />
          ) : (
            <Share2 size={compact ? 14 : 15} strokeWidth={1.75} />
          )}
        </span>
        {!compact ? (
          <span className="share-link__label">
            {copied ? "복사됨" : "공유"}
          </span>
        ) : null}
      </button>
      {mounted && copied
        ? createPortal(
            <div className="share-toast" role="status" aria-live="polite">
              링크가 복사되었습니다
            </div>,
            document.body,
          )
        : null}
    </>
  );
}
