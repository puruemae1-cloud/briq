import Link from "next/link";

type Props = {
  searchParams: Promise<{ orderId?: string; paymentId?: string; msg?: string }>;
};

export default async function OrderCompletePage({ searchParams }: Props) {
  const params = await searchParams;

  return (
    <section className="section">
      <div className="panel" style={{ maxWidth: 560 }}>
        <p className="product-card__brand">Briq</p>
        <h2 style={{ marginTop: 0, fontFamily: "var(--font-display)", fontSize: "2.2rem" }}>
          주문이 접수되었습니다
        </h2>
        <p>주문번호: {params.orderId ?? "-"}</p>
        <p>결제 ID: {params.paymentId ?? "-"}</p>
        {params.msg ? <div className="notice">{params.msg}</div> : null}
        <Link href="/shop" className="btn btn-solid" style={{ marginTop: "1.25rem" }}>
          쇼핑 계속하기
        </Link>
        <Link href="/account/orders" className="btn btn-outline" style={{ marginTop: "0.75rem" }}>
          주문·결제이력 보기
        </Link>
      </div>
    </section>
  );
}
