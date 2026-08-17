"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { lookupProductAction } from "@/app/actions/cart";
import { formatGbp, formatKrw, quoteKrw } from "@/lib/fx";
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
    gbpPrice && gbpPrice > 0
      ? quoteKrw({ goodsGbp: gbpPrice, gbpKrw, itemCount: 1 })
      : null;

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
          ? `${found.storeName} 표시가 기준 · 환율 ${formatKrw(gbpKrw)} · 마진 ${Math.round(FEE.fxMargin * 100)}% · 대행 ${Math.round(FEE.agencyRate * 100)}%`
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
        <dl className="card grid gap-2 p-4 text-sm">
          <div className="flex justify-between">
            <dt>상품 (환율·마진 포함)</dt>
            <dd>{formatKrw(quote.goodsKrw)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>대행 수수료</dt>
            <dd>{formatKrw(quote.agencyKrw)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>예상 국제배송</dt>
            <dd>{formatKrw(quote.shippingKrw)}</dd>
          </div>
          <div className="mt-1 flex justify-between border-t border-[var(--line)] pt-2 font-medium">
            <dt>예상 합계</dt>
            <dd>{formatKrw(quote.totalKrw)}</dd>
          </div>
        </dl>
      ) : null}

      {note ? <p className="text-sm text-[var(--muted)]">{note}</p> : null}
    </div>
  );
}
