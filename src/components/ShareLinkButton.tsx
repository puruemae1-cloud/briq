"use client";

import { useCallback, useState } from "react";
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

export function ShareLinkButton({
  title,
  url,
  className,
  compact = false,
}: Props) {
  const [copied, setCopied] = useState(false);

  const onShare = useCallback(async () => {
    const href = resolveUrl(url);
    try {
      if (typeof navigator !== "undefined" && typeof navigator.share === "function") {
        await navigator.share({ title, url: href, text: title });
        return;
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
    }

    try {
      await navigator.clipboard.writeText(href);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      window.prompt("링크를 복사하세요", href);
    }
  }, [title, url]);

  return (
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
      aria-label={copied ? "링크가 복사되었습니다" : "공유하기"}
      title={copied ? "링크 복사됨" : "공유하기"}
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
  );
}
