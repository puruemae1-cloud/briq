import { FEE } from "./types";

export type FxQuote = {
  gbpKrw: number;
  source: string;
  fetchedAt: string;
};

let cache: { at: number; value: FxQuote } | null = null;
const HOUR = 60 * 60 * 1000;
const FALLBACK = 1800;

export async function getGbpKrw(): Promise<FxQuote> {
  if (cache && Date.now() - cache.at < HOUR) return cache.value;
  try {
    const res = await fetch("https://api.frankfurter.app/latest?from=GBP&to=KRW", {
      next: { revalidate: 3600 },
    });
    if (!res.ok) throw new Error("fx http");
    const data = (await res.json()) as { rates?: { KRW?: number }; date?: string };
    const rate = data.rates?.KRW;
    if (!rate || !Number.isFinite(rate)) throw new Error("fx parse");
    const value: FxQuote = {
      gbpKrw: Math.round(rate * 100) / 100,
      source: "Frankfurter (ECB)",
      fetchedAt: new Date().toISOString(),
    };
    cache = { at: Date.now(), value };
    return value;
  } catch {
    const value: FxQuote = {
      gbpKrw: FALLBACK,
      source: "fallback",
      fetchedAt: new Date().toISOString(),
    };
    cache = { at: Date.now(), value };
    return value;
  }
}

export function roundWon(n: number) {
  return Math.round(n / 10) * 10;
}

export type QuoteBreakdown = {
  goodsKrw: number;
  agencyKrw: number;
  shippingKrw: number;
  cardKrw: number;
  subtotalKrw: number;
  totalKrw: number;
  fxMargin: number;
  agencyRate: number;
  cardRate: number;
};

export function quoteKrw(args: {
  goodsGbp: number;
  gbpKrw: number;
  itemCount?: number;
  fxMargin?: number;
  agencyRate?: number;
  shippingKrw?: number;
  cardRate?: number;
}): QuoteBreakdown {
  const fxMargin = args.fxMargin ?? FEE.fxMargin;
  const agencyRate = args.agencyRate ?? FEE.agencyRate;
  const shippingKrw = args.shippingKrw ?? FEE.shippingKrw;
  const cardRate = args.cardRate ?? FEE.cardRate;
  const converted = args.goodsGbp * args.gbpKrw * (1 + fxMargin);
  const goodsKrw = roundWon(converted);
  const agencyKrw = roundWon(converted * agencyRate);
  const shipping = roundWon(shippingKrw);
  const subtotalKrw = goodsKrw + agencyKrw + shipping;
  const cardKrw = roundWon(subtotalKrw * cardRate);
  const totalKrw = subtotalKrw + cardKrw;
  return {
    goodsKrw,
    agencyKrw,
    shippingKrw: shipping,
    cardKrw,
    subtotalKrw,
    totalKrw,
    fxMargin,
    agencyRate,
    cardRate,
  };
}

export function formatKrw(n: number) {
  return `${n.toLocaleString("ko-KR")}원`;
}

export function formatGbp(n: number) {
  return `£${n.toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatAgencyFee(agencyKrw: number) {
  return agencyKrw <= 0 ? "무료" : formatKrw(agencyKrw);
}

export function feePolicySummary() {
  return `대행 무료 · 배송 ${formatKrw(FEE.shippingKrw)} · 카드 ${Math.round(FEE.cardRate * 100)}% · 관부가세 고객 직접 납부`;
}
