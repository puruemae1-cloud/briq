import Link from "next/link";
import { redirect } from "next/navigation";
import { AddToCartForm } from "@/components/AddToCartForm";
import { QuotePreview } from "@/components/QuotePreview";
import { removeCartItemAction } from "@/app/actions/cart";
import { requestQuoteAction } from "@/app/actions/orders";
import { getCurrentUser } from "@/lib/auth";
import { readOnlyDb } from "@/lib/db";
import { formatGbp } from "@/lib/fx";
import { cartLinkLabel } from "@/lib/product-input";

export default async function CartPage({
  searchParams,
}: {
  searchParams: Promise<{ url?: string; store?: string }>;
}) {
  const me = await getCurrentUser();
  const { url, store } = await searchParams;
  if (!me) {
    const qs = new URLSearchParams();
    if (url) qs.set("url", url);
    if (store) qs.set("store", store);
    const next = qs.size ? `/cart?${qs.toString()}` : "/cart";
    redirect(`/login?next=${encodeURIComponent(next)}`);
  }
  const db = await readOnlyDb();
  const items = db.carts[me.id] ?? [];

  return (
    <div className="page-wrap py-12">
      <h1 className="display text-4xl">장바구니</h1>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--muted)]">
        ASOS에서 복사한 <strong>상품 이름</strong>이나 링크를 붙여넣으면 가격을 찾아
        넣습니다. GBP는 고객이 바꿀 수 없습니다. 사이즈·수량만 적고 「장바구니에 담기」를
        누르면 됩니다.
      </p>

      <div className="mt-8">
        <AddToCartForm presetUrl={url || ""} defaultStoreId={store || "asos"} />
      </div>

      <div className="mt-10 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="grid gap-3">
          {items.length === 0 ? (
            <p className="card p-6 text-sm text-[var(--muted)]">
              아직 담긴 상품이 없습니다.{" "}
              <Link href="/#stores" className="underline">
                스토어 배너
              </Link>
              에서 상품을 고르세요.
            </p>
          ) : (
            items.map((item) => (
              <article key={item.id} className="card flex gap-4 p-4">
                {item.image ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={item.image} alt="" className="h-24 w-20 object-cover" />
                ) : (
                  <div className="flex h-24 w-20 items-center justify-center bg-[var(--bg-deep)] text-[0.7rem]">
                    {item.storeName}
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-[0.7rem] tracking-[0.14em] uppercase text-[var(--muted)]">
                    {item.storeName}
                  </p>
                  <p className="mt-1 truncate font-medium">{item.title}</p>
                  <p className="mt-1 text-sm text-[var(--muted)]">
                    {item.size || "사이즈 미입력"} · {item.color || "색상 미입력"} · {item.qty}개
                    {item.gbpPrice ? ` · ${formatGbp(item.gbpPrice)}` : " · 가격 미입력"}
                  </p>
                  <a href={item.url} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-sm underline">
                    {cartLinkLabel(item.url, item.storeName, item.source)}
                  </a>
                </div>
                <form action={removeCartItemAction.bind(null, item.id)}>
                  <button type="submit" className="text-sm text-[var(--muted)]">
                    삭제
                  </button>
                </form>
              </article>
            ))
          )}
        </div>
        <div className="grid gap-4 self-start">
          <QuotePreview items={items} />
          {items.length > 0 ? (
            <form action={requestQuoteAction}>
              <button className="btn w-full" type="submit">
                견적 확인
              </button>
            </form>
          ) : null}
          <p className="text-sm text-[var(--muted)]">
            배송지·연락처가 비어 있으면{" "}
            <Link href="/account" className="underline">
              회원정보
            </Link>
            를 먼저 채워 주세요.
          </p>
        </div>
      </div>
    </div>
  );
}
