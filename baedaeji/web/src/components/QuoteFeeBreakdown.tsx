import { formatAgencyFee, formatKrw, type QuoteBreakdown } from "@/lib/fx";

export function QuoteFeeBreakdown({
  quote,
  totalClassName = "",
}: {
  quote: QuoteBreakdown;
  totalClassName?: string;
}) {
  return (
    <dl className="grid gap-2 text-sm">
      <div className="flex justify-between">
        <dt>상품 (환율·마진 포함)</dt>
        <dd>{formatKrw(quote.goodsKrw)}</dd>
      </div>
      <div className="flex justify-between">
        <dt>대행 수수료</dt>
        <dd>{formatAgencyFee(quote.agencyKrw)}</dd>
      </div>
      <div className="flex justify-between">
        <dt>배송비</dt>
        <dd>{formatKrw(quote.shippingKrw)}</dd>
      </div>
      <div className="flex justify-between">
        <dt>카드 수수료 ({Math.round(quote.cardRate * 100)}%)</dt>
        <dd>{formatKrw(quote.cardKrw)}</dd>
      </div>
      <div className="flex justify-between text-[var(--muted)]">
        <dt>관부가세</dt>
        <dd>고객 직접 납부</dd>
      </div>
      <div className="mt-1 flex justify-between border-t border-[var(--line)] pt-2 font-medium">
        <dt>결제 예상 합계</dt>
        <dd className={totalClassName || undefined}>{formatKrw(quote.totalKrw)}</dd>
      </div>
    </dl>
  );
}
