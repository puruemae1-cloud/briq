"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { lookupProductAction } from "@/app/actions/cart";
import { QuoteFeeBreakdown } from "@/components/QuoteFeeBreakdown";
import { formatGbp, formatKrw, quoteKrw, feePolicySummary } from "@/lib/fx";
import { FEE } from "@/lib/types";

export function HomePasteQuote({
  gbpKrw,
  fxSource,
  storeId = "asos",
}: {
  gbpKrw: number;
  fxSource: string;
  storeId?: string;
}) {
  const [input, setInput] = useState("");
  const [title, setTitle] = useState("");
  const [gbpPrice, setGbpPrice] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [note, setNote] = useState("");
  const seq = useRef(0);

  const quote =
    gbpPrice && gbpPrice > 0 ? quoteKrw({ goodsGbp: gbpPrice, gbpKrw }) : null;

  async function runLookup(raw: string) {
    const text = raw.trim();
    if (!text) {
      setTitle("");
      setGbpPrice(null);
      setNote("");
      return;
    }
    const n = ++seq.current;
    setLoading(true);
    try {
      const found = await lookupProductAction(text, storeId);
      if (n !== seq.current) return;
      setTitle(found.title);
      setGbpPrice(found.gbpPrice);
      setNote(
        found.gbpPrice
          ? `${found.storeName} 표시가 · £1 = ${formatKrw(gbpKrw)} · 환전 마진 ${Math.round(FEE.fxMargin * 100)}% · ${feePolicySummary()}`
          : "가격을 못 찾았습니다. 장바구니에서 운영자 확인 후 견적이 나갑니다.",
      );
    } catch {
      if (n !== seq.current) return;
      setGbpPrice(null);
      setNote("상품을 인식하지 못했습니다. 이름이나 링크를 다시 확인해 주세요.");
    } finally {
      if (n === seq.current) setLoading(false);
    }
  }

  const cartHref = input.trim()
    ? `/cart?url=${encodeURIComponent(input.trim())}&store=${encodeURIComponent(storeId)}`
    : "/cart";

  return (
    <div className="grid gap-4">
      <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
        <label className="sr-only" htmlFor="home-product-input">
          상품 이름 또는 링크
        </label>
        <input
          id="home-product-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onBlur={(e) => void runLookup(e.target.value)}
          onPaste={(e) => {
            const text = e.clipboardData.getData("text");
            if (text.trim()) window.setTimeout(() => void runLookup(text), 0);
          }}
          autoCapitalize="off"
          autoCorrect="off"
          spellCheck={false}
          placeholder="ASOS DESIGN double layer minimal halter neck top in cream"
          className="min-h-[52px] w-full border border-[var(--line)] bg-white px-4"
        />
        <Link href={cartHref} className="btn min-h-[52px] whitespace-nowrap">
          장바구니에 담기
        </Link>
      </div>

      <div className="card grid gap-3 p-4 sm:grid-cols-[1fr_auto] sm:items-end">
        <div>
          <p className="text-[0.72rem] tracking-[0.16em] uppercase text-[var(--muted)]">
            {loading ? "가격 찾는 중…" : "GBP → KRW 견적"}
          </p>
          {title ? (
            <p className="mt-1 text-sm leading-6 text-[var(--muted)]">{title}</p>
          ) : (
            <p className="mt-1 text-sm text-[var(--muted)]">
              이름이나 링크를 붙여넣으면 £ 가격과 원화 견적이 나옵니다.
            </p>
          )}
          <p className="mt-2 text-sm text-[var(--muted)]">
            £1 = {formatKrw(gbpKrw)} · {fxSource}
          </p>
        </div>
        <div className="text-right">
          <p className="display text-3xl">
            {gbpPrice ? formatGbp(gbpPrice) : loading ? "…" : "£—"}
          </p>
          {quote ? (
            <p className="display mt-1 text-2xl text-[var(--navy)]">
              ≈ {formatKrw(quote.totalKrw)}
            </p>
          ) : null}
        </div>
      </div>

      {quote ? (
        <div className="card p-4">
          <QuoteFeeBreakdown quote={quote} />
        </div>
      ) : null}

      {note ? <p className="text-sm text-[var(--muted)]">{note}</p> : null}
    </div>
  );
}
