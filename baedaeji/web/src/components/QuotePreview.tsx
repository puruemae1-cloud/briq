import { getGbpKrw, quoteKrw, formatGbp, formatKrw, feePolicySummary } from "@/lib/fx";
import { FEE, type CartItem } from "@/lib/types";
import { QuoteFeeBreakdown } from "@/components/QuoteFeeBreakdown";

export async function QuotePreview({ items }: { items: CartItem[] }) {
  const priced = items.filter((i) => i.gbpPrice && i.gbpPrice > 0);
  const missing = items.length - priced.length;
  const goodsGbp = priced.reduce((sum, i) => sum + (i.gbpPrice ?? 0) * i.qty, 0);
  const fx = await getGbpKrw();
  const q = goodsGbp > 0 ? quoteKrw({ goodsGbp, gbpKrw: fx.gbpKrw }) : null;

  return (
    <aside className="card p-5">
      <p className="text-[0.72rem] tracking-[0.18em] uppercase text-[var(--muted)]">
        오늘 환율 견적
      </p>
      <p className="display mt-2 text-3xl">£1 = {formatKrw(fx.gbpKrw)}</p>
      <p className="mt-1 text-sm text-[var(--muted)]">
        {fx.source} · 환전 마진 {Math.round(FEE.fxMargin * 100)}% · {feePolicySummary()}
      </p>
      <dl className="mt-5 grid gap-2 text-sm">
        <div className="flex justify-between">
          <dt>상품 GBP</dt>
          <dd>{goodsGbp ? formatGbp(goodsGbp) : "가격 미입력"}</dd>
        </div>
      </dl>
      {q ? (
        <div className="mt-4">
          <QuoteFeeBreakdown quote={q} totalClassName="display text-2xl" />
        </div>
      ) : null}
      {missing > 0 ? (
        <p className="mt-4 text-sm text-[var(--red)]">
          {missing}개 상품은 GBP 가격이 없어 운영자가 확인한 뒤 견적이 확정됩니다.
        </p>
      ) : (
        <p className="mt-4 text-sm text-[var(--muted)]">
          견적은 {FEE.quoteTtlHours}시간 동안 유효합니다. 관부가세는 통관 시 별도입니다.
        </p>
      )}
    </aside>
  );
}
