import { FEE } from "./types";

export type FxQuote = {
  gbpKrw: number;
  source: string;
  fetchedAt: string;
};

let cache: { at: number; value: FxQuote } | null = null;
const HOUR = 60 * 60 * 1000;
const FALLBACK = 1957;

async function fetchNaverGbpCashBuy() {
  const res = await fetch(
    "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_GBPKRW",
    {
      next: { revalidate: 3600 },
      headers: {
        "user-agent":
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        accept: "text/html,application/xhtml+xml",
      },
    },
  );
  if (!res.ok) throw new Error("naver fx http");
  const html = new TextDecoder("euc-kr").decode(await res.arrayBuffer());
  const m = html.match(/현찰\s*사실때[\s\S]*?<td>[\s\S]*?([0-9,]+\.?[0-9]*)/);
  if (!m?.[1]) throw new Error("naver fx parse");
  const rate = Number(m[1].replace(/,/g, ""));
  if (!Number.isFinite(rate) || rate <= 0) throw new Error("naver fx invalid");
  return Math.round(rate);
}

export async function getGbpKrw(): Promise<FxQuote> {
  if (cache && Date.now() - cache.at < HOUR) return cache.value;
  try {
    const rate = await fetchNaverGbpCashBuy();
    const value: FxQuote = {
      gbpKrw: rate,
      source: "네이버 · 현찰 살 때",
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
