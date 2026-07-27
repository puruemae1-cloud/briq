import type { ReactNode } from "react";

const notices: { title: string; body: ReactNode }[] = [
  {
    title: "100% Authentic British Selection",
    body: (
      <>
        Briq에서 선보이는 모든 제품은 영국 현지에서 공식 검증된{" "}
        <strong>100% 정품</strong>입니다.
      </>
    ),
  },
  {
    title: "Order Process & Policy",
    body: (
      <>
        주문 완료 후 영국 현지 출고 프로세스가 즉시 진행되는 프라이빗 오더
        특성상,{" "}
        <strong>결제 완료 이후에는 단순 변심으로 인한 주문 취소가 불가</strong>
        합니다.
        <br />
        <br />
        아울러 해외 배송의 특성상{" "}
        <strong>
          제품 자체의 명백한 하자가 아닌 이상, 그 어떠한 사유로도 교환 및 반품이
          불가
        </strong>
        하오니 신중한 구매를 부탁드립니다.
      </>
    ),
  },
  {
    title: "Delivery Notice",
    body: (
      <>
        영국 현지 바잉 및 안전한 국외 운송 절차를 거쳐, 결제 완료일로부터{" "}
        <strong>영업일 기준 약 7일~14일 내외</strong>로 고객님의 자택까지
        전달됩니다.
      </>
    ),
  },
];

/** Shared purchase & shipping notice — shown on every product detail page. */
export function ProductPurchaseNotice() {
  return (
    <section className="purchase-notice" aria-labelledby="purchase-notice-title">
      <div className="purchase-notice__head">
        <p className="purchase-notice__eyebrow">Notice</p>
        <h2 id="purchase-notice-title">구매 및 배송 안내</h2>
      </div>
      <div className="purchase-notice__grid">
        {notices.map((item) => (
          <article key={item.title} className="purchase-notice__card">
            <h3>{item.title}</h3>
            <p>{item.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
