"use client";

import { useCallback, useEffect, useState, type MouseEvent } from "react";
import { createPortal } from "react-dom";

type Props = {
  title: string;
  /** Absolute or path URL. Defaults to current page. */
  url?: string;
  className?: string;
  /** Compact icon-only mark for dense headers. */
  compact?: boolean;
};

function ShareIcon({ size }: { size: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M4 12v7a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7" />
      <polyline points="16 6 12 2 8 6" />
      <line x1="12" y1="2" x2="12" y2="15" />
    </svg>
  );
}

function CheckIcon({ size }: { size: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.25"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

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
            <CheckIcon size={compact ? 14 : 15} />
          ) : (
            <ShareIcon size={compact ? 14 : 15} />
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
