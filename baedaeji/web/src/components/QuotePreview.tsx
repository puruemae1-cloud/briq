import { getGbpKrw, quoteKrw, formatGbp, formatKrw } from "@/lib/fx";
import { FEE, type CartItem } from "@/lib/types";

export async function QuotePreview({ items }: { items: CartItem[] }) {
  const priced = items.filter((i) => i.gbpPrice && i.gbpPrice > 0);
  const missing = items.length - priced.length;
  const goodsGbp = priced.reduce((sum, i) => sum + (i.gbpPrice ?? 0) * i.qty, 0);
  const fx = await getGbpKrw();
  const qty = items.reduce((n, i) => n + i.qty, 0);
  const q =
    goodsGbp > 0
      ? quoteKrw({ goodsGbp, gbpKrw: fx.gbpKrw, itemCount: Math.max(1, qty) })
      : null;

  return (
    <aside className="card p-5">
      <p className="text-[0.72rem] tracking-[0.18em] uppercase text-[var(--muted)]">
        오늘 환율 견적
      </p>
      <p className="display mt-2 text-3xl">{fx.gbpKrw.toLocaleString("en-US")} KRW</p>
      <p className="mt-1 text-sm text-[var(--muted)]">
        £1 기준 · {fx.source} · 환전 마진 {Math.round(FEE.fxMargin * 100)}% · 대행{" "}
        {Math.round(FEE.agencyRate * 100)}%
      </p>
      <dl className="mt-5 grid gap-2 text-sm">
        <div className="flex justify-between">
          <dt>상품 GBP</dt>
          <dd>{goodsGbp ? formatGbp(goodsGbp) : "가격 미입력"}</dd>
        </div>
        {q ? (
          <>
            <div className="flex justify-between">
              <dt>상품 원화 (마진 포함)</dt>
              <dd>{formatKrw(q.goodsKrw)}</dd>
            </div>
            <div className="flex justify-between">
              <dt>대행 수수료</dt>
              <dd>{formatKrw(q.agencyKrw)}</dd>
            </div>
            <div className="flex justify-between">
              <dt>예상 국제배송</dt>
              <dd>{formatKrw(q.shippingKrw)}</dd>
            </div>
            <div className="mt-2 flex justify-between border-t border-[var(--line)] pt-3 text-base">
              <dt>예상 합계</dt>
              <dd className="display text-2xl">{formatKrw(q.totalKrw)}</dd>
            </div>
          </>
        ) : null}
      </dl>
      {missing > 0 ? (
        <p className="mt-4 text-sm text-[var(--red)]">
          {missing}개 상품은 GBP 가격이 없어 운영자가 확인한 뒤 견적이 확정됩니다.
        </p>
      ) : (
        <p className="mt-4 text-sm text-[var(--muted)]">
          견적은 {FEE.quoteTtlHours}시간 동안 유효합니다. 지금은 결제 버튼이 입금
          대기로 바뀌며, 네이버페이는 가맹 후 붙습니다.
        </p>
      )}
    </aside>
  );
}
