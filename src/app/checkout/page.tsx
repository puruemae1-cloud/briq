import Link from "next/link";
import { CheckoutClient } from "@/components/CheckoutClient";
import { getCartItems } from "@/lib/cart-server";

export default async function CheckoutPage() {
  const items = await getCartItems();

  if (items.length === 0) {
    return (
      <section className="section">
        <div className="panel">
          <h2 style={{ marginTop: 0, fontFamily: "var(--font-display)" }}>Checkout</h2>
          <p>결제할 상품이 없습니다.</p>
          <Link href="/shop" className="btn btn-solid" style={{ marginTop: "1rem" }}>
            쇼핑 계속하기
          </Link>
        </div>
      </section>
    );
  }

  return <CheckoutClient items={items} />;
}
