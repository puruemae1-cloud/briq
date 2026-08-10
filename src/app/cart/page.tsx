import Link from "next/link";
import { removeFromCart, updateCartQty } from "@/app/cart/actions";
import { NaverPayOrderButton } from "@/components/NaverPayOrderButton";
import { ProductImage } from "@/components/ProductImage";
import { formatBraceletLabel } from "@/data/cw-twelve-picnmix";
import { formatKrw } from "@/data/products";
import {
  cartSubtotal,
  getCartItems,
  productHref,
} from "@/lib/cart-server";
import { cartUnitPrice } from "@/lib/cart-price";
import { resolveProductImage } from "@/lib/product-image";

export default async function CartPage() {
  const items = await getCartItems();
  const total = cartSubtotal(items);

  if (items.length === 0) {
    return (
      <section className="section">
        <div className="panel">
          <h2 style={{ marginTop: 0, fontFamily: "var(--font-display)" }}>Cart</h2>
          <p>장바구니가 비어 있습니다.</p>
          <Link href="/shop" className="btn btn-solid" style={{ marginTop: "1rem" }}>
            쇼핑 계속하기
          </Link>
        </div>
      </section>
    );
  }

  const npayItems = items.map(({ product, variant, braceletCm, qty }) => ({
    productId: product.id,
    variantId: variant?.id,
    braceletCm,
    qty,
  }));

  return (
    <section className="section">
      <div className="section__head">
        <div>
          <h2>Cart</h2>
          <p>{items.length} items</p>
        </div>
      </div>
      <div className="panel cart-list">
        {items.map(({ product, variant, braceletCm, qty }) => {
          const unit = cartUnitPrice(product, variant, braceletCm);
          const image = resolveProductImage(product.image, variant?.image);
          const label = variant
            ? `${product.nameKo} · ${variant.nameKo}`
            : product.nameKo;
          const href = productHref(product.id, variant?.id);
          const lineKey = `${product.id}::${variant?.id ?? "default"}::${braceletCm ?? "none"}`;

          return (
            <div key={lineKey} className="cart-item">
              <Link href={href} className="cart-item__media">
                <ProductImage src={image} alt={label} tone="cart" />
              </Link>
              <div>
                <Link href={href} className="cart-item__title">
                  {label}
                </Link>
                {product.braceletResize && braceletCm ? (
                  <p className="product-card__en" style={{ marginTop: "0.2rem" }}>
                    {formatBraceletLabel(braceletCm)}
                  </p>
                ) : null}
                <p className="product-card__en">{formatKrw(unit)}</p>
                <div className="qty" style={{ marginTop: "0.5rem" }}>
                  <form action={updateCartQty}>
                    <input type="hidden" name="productId" value={product.id} />
                    {variant ? (
                      <input type="hidden" name="variantId" value={variant.id} />
                    ) : null}
                    {braceletCm ? (
                      <input type="hidden" name="braceletCm" value={braceletCm} />
                    ) : null}
                    <input type="hidden" name="qty" value={String(qty - 1)} />
                    <button type="submit">−</button>
                  </form>
                  <span>{qty}</span>
                  <form action={updateCartQty}>
                    <input type="hidden" name="productId" value={product.id} />
                    {variant ? (
                      <input type="hidden" name="variantId" value={variant.id} />
                    ) : null}
                    {braceletCm ? (
                      <input type="hidden" name="braceletCm" value={braceletCm} />
                    ) : null}
                    <input type="hidden" name="qty" value={String(qty + 1)} />
                    <button type="submit">+</button>
                  </form>
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <p style={{ margin: 0, fontWeight: 600 }}>{formatKrw(unit * qty)}</p>
                <form action={removeFromCart}>
                  <input type="hidden" name="productId" value={product.id} />
                  {variant ? (
                    <input type="hidden" name="variantId" value={variant.id} />
                  ) : null}
                  {braceletCm ? (
                    <input type="hidden" name="braceletCm" value={braceletCm} />
                  ) : null}
                  <button type="submit" className="icon-btn" style={{ marginLeft: "auto" }}>
                    삭제
                  </button>
                </form>
              </div>
            </div>
          );
        })}
        <div className="cart-checkout-row">
          <strong>합계 {formatKrw(total)}</strong>
          <div className="cart-checkout-row__actions">
            <Link href="/checkout" className="btn btn-solid">
              결제하기
            </Link>
            <NaverPayOrderButton
              page="cart"
              items={npayItems}
              className="npay-order-button npay-order-button--cart"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
