"use client";

import Link from "next/link";
import { useState } from "react";
import { addToCart, buyNow } from "@/app/cart/actions";
import { BraceletResizeControls } from "@/components/BraceletResizeControls";
import { ProductEngagement } from "@/components/ProductEngagement";
import { ProductGallery } from "@/components/ProductGallery";
import { ProductImage } from "@/components/ProductImage";
import { ProductPurchaseNotice } from "@/components/ProductPurchaseNotice";
import { ProductStorySections } from "@/components/ProductStorySections";
import type { Product, ProductVariant } from "@/data/products";
import {
  formatKrw,
  isProductInStock,
  isVariantInStock,
  productSalePercent,
} from "@/data/products";
import { cartUnitPrice } from "@/lib/cart-price";
import { resolveProductImage } from "@/lib/product-image";

function ColorSwatches({
  productId,
  variants,
  selectedId,
  idPrefix,
}: {
  productId: string;
  variants: ProductVariant[];
  selectedId?: string;
  idPrefix: string;
}) {
  return (
    <div className="variant-grid">
      {variants.map((v) => {
        const active = v.id === selectedId;
        const soldOut = !v.inStock;
        return (
          <Link
            key={`${idPrefix}-${v.id}`}
            href={`/product/${productId}?color=${v.id}`}
            scroll={false}
            replace
            aria-current={active ? "true" : undefined}
            aria-disabled={soldOut ? true : undefined}
            className={`variant-swatch${active ? " is-active" : ""}${soldOut ? " is-sold-out" : ""}`}
            title={soldOut ? `${v.nameKo} · Sold Out` : v.nameKo}
          >
            <ProductImage src={v.image} alt="" tone="swatch" />
            <span>{v.nameKo}</span>
            {soldOut ? (
              <span className="variant-swatch__sold">Sold Out</span>
            ) : null}
          </Link>
        );
      })}
    </div>
  );
}

/**
 * Product detail with optional bracelet resize + multi-image gallery.
 * Add-to-cart / buy-now use Server Actions.
 */
export function ProductDetail({
  product,
  colorId,
}: {
  product: Product;
  colorId?: string;
}) {
  const allVariants = product.variants ?? [];
  const inStockVariants = allVariants.filter((v) => v.inStock);
  const productAvailable = isProductInStock(product);

  const selected =
    allVariants.find((v) => v.id === colorId) ??
    inStockVariants[0] ??
    allVariants[0] ??
    undefined;

  const selectedAvailable = selected
    ? isVariantInStock(product, selected.id)
    : productAvailable;

  const [braceletCm, setBraceletCm] = useState("no");
  const unitPrice = cartUnitPrice(product, selected, braceletCm);
  const primaryImage = resolveProductImage(product.image, selected?.image);
  const galleryImages =
    product.images && product.images.length > 0
      ? product.images
      : [primaryImage];
  const soldOut = !selectedAvailable;
  const salePct = productSalePercent(product);
  const onSale = Boolean(salePct && product.compareAtPrice);

  const hiddenFields = (
    <>
      <input type="hidden" name="productId" value={product.id} />
      {selected ? (
        <input type="hidden" name="variantId" value={selected.id} />
      ) : null}
      {product.braceletResize ? (
        <input type="hidden" name="braceletCm" value={braceletCm} />
      ) : null}
      <input type="hidden" name="qty" value="1" />
    </>
  );

  const braceletBlock = product.braceletResize ? (
    <BraceletResizeControls
      config={product.braceletResize}
      value={braceletCm}
      onChange={setBraceletCm}
    />
  ) : null;

  return (
    <div className={`product-page${soldOut ? " product-page--sold-out" : ""}`}>
      <article className="product-detail">
        <ProductGallery
          images={galleryImages}
          alt={`${product.nameKo} ${selected?.nameKo ?? ""}`}
          soldOut={soldOut}
          badge={selected?.nameKo}
        />

        <div className="product-detail__info">
          <p className="product-card__brand">{product.brand}</p>
          <h1>{product.nameKo}</h1>
          {selected ? (
            <p className="product-detail__color-name">
              {selected.nameKo}
              {soldOut ? (
                <span className="product-detail__stock"> · Sold Out</span>
              ) : null}
            </p>
          ) : soldOut ? (
            <p className="product-detail__color-name">
              <span className="product-detail__stock">Sold Out</span>
            </p>
          ) : null}
          <p className={`product-detail__price${onSale ? " product-detail__price--sale" : ""}`}>
            {soldOut ? (
              "Sold Out"
            ) : onSale && product.compareAtPrice ? (
              <>
                <span className="product-detail__price-now">
                  {formatKrw(unitPrice)}
                </span>
                <span className="product-detail__price-was">
                  {formatKrw(product.compareAtPrice)}
                </span>
                <span className="product-detail__price-pct">{salePct}% OFF</span>
              </>
            ) : (
              formatKrw(unitPrice)
            )}
          </p>
          {product.braceletResize && braceletCm !== "no" ? (
            <p className="product-detail__price-note">
              기본가 {formatKrw(selected?.price ?? product.price)} + 리사이즈{" "}
              {formatKrw(product.braceletResize.feeKrw)}
            </p>
          ) : null}

          {product.descriptionKo ? (
            <p className="product-detail__desc">{product.descriptionKo}</p>
          ) : null}

          {allVariants.length > 0 ? (
            <div className="variant-block">
              <p className="variant-block__label">
                {product.brand === "Christopher Ward" ? "스트랩 · " : "컬러 · "}
                <strong>{selected?.nameKo}</strong>
                {soldOut ? (
                  <span className="product-detail__stock"> · Sold Out</span>
                ) : null}
              </p>
              <ColorSwatches
                productId={product.id}
                variants={allVariants}
                selectedId={selected?.id}
                idPrefix="main"
              />
            </div>
          ) : null}

          {!soldOut ? braceletBlock : null}

          {soldOut ? (
            <div className="product-detail__sold-panel" role="status">
              <p className="product-detail__sold-mark">Sold Out</p>
              <p className="product-detail__sold-copy">
                현재 선택하신 옵션은 품절입니다. 다른 컬러를 확인해 주시거나,
                재입고 시 다시 안내드릴 예정입니다.
              </p>
            </div>
          ) : (
            <div className="product-detail__actions">
              <form action={buyNow}>
                {hiddenFields}
                <button type="submit" className="btn btn-solid">
                  구매하기
                </button>
              </form>
              <form action={addToCart}>
                {hiddenFields}
                <button type="submit" className="btn btn-primary">
                  장바구니 담기
                </button>
              </form>
              <Link href="/cart" className="btn btn-outline">
                장바구니 보기
              </Link>
            </div>
          )}
        </div>
      </article>

      {product.storySections?.length ? (
        <ProductStorySections sections={product.storySections} />
      ) : null}

      <ProductPurchaseNotice />

      <ProductEngagement productId={product.id} productName={product.nameKo} />

      <div className="pdp-dock" aria-label="구매 옵션">
        <input
          type="checkbox"
          id="pdp-dock-options"
          className="pdp-dock__toggle"
          aria-hidden="true"
          tabIndex={-1}
        />

        <div className="pdp-dock__panel">
          <div className="pdp-dock__panel-inner">
            <p className="pdp-dock__panel-title">
              옵션 선택
              {selected ? (
                <>
                  {" "}
                  · <strong>{selected.nameKo}</strong>
                </>
              ) : null}
            </p>
            {allVariants.length > 0 ? (
              <ColorSwatches
                productId={product.id}
                variants={allVariants}
                selectedId={selected?.id}
                idPrefix="dock"
              />
            ) : product.braceletResize ? null : (
              <p className="pdp-dock__empty">선택 가능한 옵션이 없습니다.</p>
            )}
            {!soldOut && product.braceletResize ? (
              <BraceletResizeControls
                config={product.braceletResize}
                value={braceletCm}
                onChange={setBraceletCm}
                idPrefix="dock-bracelet"
              />
            ) : null}
            <label htmlFor="pdp-dock-options" className="pdp-dock__close">
              닫기
            </label>
          </div>
        </div>

        <div className="pdp-dock__bar">
          {allVariants.length > 0 || product.braceletResize ? (
            <label htmlFor="pdp-dock-options" className="pdp-dock__opt">
              옵션 선택
            </label>
          ) : (
            <span className="pdp-dock__opt pdp-dock__opt--disabled">옵션 없음</span>
          )}
          <div className="pdp-dock__summary">
            <p className="pdp-dock__name">{product.nameKo}</p>
            <p className="pdp-dock__meta">
              {selected ? <span>{selected.nameKo}</span> : null}
              {product.braceletResize && braceletCm !== "no" ? (
                <span>{braceletCm}cm</span>
              ) : null}
              <strong>{soldOut ? "Sold Out" : formatKrw(unitPrice)}</strong>
            </p>
          </div>
          <div className="pdp-dock__actions">
            {soldOut ? (
              <button
                type="button"
                className="btn btn-solid pdp-dock__buy pdp-dock__buy--sold"
                disabled
                aria-disabled="true"
              >
                Sold Out
              </button>
            ) : (
              <>
                <form action={buyNow}>
                  {hiddenFields}
                  <button type="submit" className="btn btn-solid pdp-dock__buy">
                    구매하기
                  </button>
                </form>
                <form action={addToCart}>
                  {hiddenFields}
                  <button type="submit" className="btn btn-primary pdp-dock__cart">
                    장바구니
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
