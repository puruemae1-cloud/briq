"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { addToCart, buyNow } from "@/app/cart/actions";
import { BraceletResizeControls } from "@/components/BraceletResizeControls";
import { ProductEngagement } from "@/components/ProductEngagement";
import { ProductGallery } from "@/components/ProductGallery";
import { ProductImage } from "@/components/ProductImage";
import { ProductPurchaseNotice } from "@/components/ProductPurchaseNotice";
import { ProductStorySections } from "@/components/ProductStorySections";
import { ProductTechSpecs } from "@/components/ProductTechSpecs";
import { SizeChartControl } from "@/components/SizeChartControl";
import { ShareLinkButton } from "@/components/ShareLinkButton";
import { NaverPayOrderButton } from "@/components/NaverPayOrderButton";
import type { Product, ProductVariant } from "@/data/products";
import {
  formatKrw,
  isProductInStock,
  isVariantInStock,
  productSalePercent,
} from "@/data/products";
import { cartUnitPrice } from "@/lib/cart-price";
import { resolveProductImage } from "@/lib/product-image";
import { compareAxSizes, isArcteryxProduct } from "@/lib/ax-size-order";

type ColorGroup = {
  key: string;
  nameKo: string;
  image: string;
  variants: ProductVariant[];
  inStock: boolean;
};

function ColorSwatches({
  productId,
  colors,
  selectedKey,
  size,
  idPrefix,
}: {
  productId: string;
  colors: ColorGroup[];
  selectedKey?: string;
  size?: string;
  idPrefix: string;
}) {
  return (
    <div className="variant-grid">
      {colors.map((c) => {
        const active = c.key === selectedKey;
        const soldOut = !c.inStock;
        const href = size
          ? `/product/${productId}?color=${encodeURIComponent(c.key)}&size=${encodeURIComponent(size)}`
          : `/product/${productId}?color=${encodeURIComponent(c.key)}`;
        return (
          <Link
            key={`${idPrefix}-${c.key}`}
            href={href}
            scroll={false}
            replace
            aria-current={active ? "true" : undefined}
            aria-disabled={soldOut ? true : undefined}
            className={`variant-swatch${active ? " is-active" : ""}${soldOut ? " is-sold-out" : ""}`}
            title={soldOut ? `${c.nameKo} · Sold Out` : c.nameKo}
          >
            <ProductImage src={c.image} alt="" tone="swatch" />
            <span>{c.nameKo}</span>
            {soldOut ? (
              <span className="variant-swatch__sold">Sold Out</span>
            ) : null}
          </Link>
        );
      })}
    </div>
  );
}

function SizePicker({
  productId,
  colorKey,
  sizes,
  selectedSize,
  sizeLabel,
}: {
  productId: string;
  colorKey: string;
  sizes: ProductVariant[];
  selectedSize?: string;
  /** Chip label override — defaults to variant.size / name. */
  sizeLabel?: (v: ProductVariant) => string;
}) {
  return (
    <div className="size-grid" role="list">
      {sizes.map((v) => {
        const size = v.size || v.name;
        const label = sizeLabel ? sizeLabel(v) : size;
        const active = size === selectedSize;
        const soldOut = !v.inStock;
        const hrefColor = v.colorKey || colorKey;
        return (
          <Link
            key={v.id}
            href={`/product/${productId}?color=${encodeURIComponent(hrefColor)}&size=${encodeURIComponent(size)}`}
            scroll={false}
            replace
            role="listitem"
            aria-current={active ? "true" : undefined}
            aria-disabled={soldOut ? true : undefined}
            className={`size-chip${active ? " is-active" : ""}${soldOut ? " is-sold-out" : ""}`}
            title={soldOut ? `${label} · Sold Out` : label}
          >
            {label}
            {soldOut ? <span className="size-chip__sold">품절</span> : null}
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
  sizeId,
}: {
  product: Product;
  colorId?: string;
  sizeId?: string;
}) {
  const allVariants = product.variants ?? [];
  const hasSizes = allVariants.some((v) => Boolean(v.size));
  const isCw = product.brand === "Christopher Ward";
  const productAvailable = isProductInStock(product);

  const colorGroups: ColorGroup[] = useMemo(() => {
    if (!hasSizes) {
      return allVariants.map((v) => ({
        key: v.id,
        nameKo: v.nameKo,
        image: v.image,
        variants: [v],
        inStock: v.inStock,
      }));
    }
    const map = new Map<string, ColorGroup>();
    for (const v of allVariants) {
      const key = v.colorKey || v.id;
      const existing = map.get(key);
      if (!existing) {
        map.set(key, {
          key,
          nameKo: v.colorNameKo || v.nameKo,
          image: v.image,
          variants: [v],
          inStock: v.inStock,
        });
      } else {
        existing.variants.push(v);
        if (v.inStock) existing.inStock = true;
        if (!existing.image && v.image) existing.image = v.image;
      }
    }
    const groups = Array.from(map.values());
    if (isArcteryxProduct(product)) {
      for (const g of groups) {
        g.variants = [...g.variants].sort((a, b) =>
          compareAxSizes(a.size || "", b.size || ""),
        );
      }
    }
    if (isCw) {
      for (const g of groups) {
        g.variants = [...g.variants].sort((a, b) => {
          const na = Number.parseInt(a.size || "", 10) || 0;
          const nb = Number.parseInt(b.size || "", 10) || 0;
          return na - nb;
        });
      }
    }
    return groups;
  }, [allVariants, hasSizes, product, isCw]);

  // CW: pick case size first (official WSize), then strap swatches for that size.
  const cwCaseSizeOptions = useMemo(() => {
    if (!isCw || !hasSizes) return [] as ProductVariant[];
    const bySize = new Map<string, ProductVariant>();
    for (const v of allVariants) {
      if (!v.size) continue;
      const prev = bySize.get(v.size);
      if (!prev) {
        bySize.set(v.size, v);
        continue;
      }
      // Prefer matching the requested strap colour when building the chip set later.
      if (!prev.inStock && v.inStock) bySize.set(v.size, v);
    }
    return Array.from(bySize.values()).sort((a, b) => {
      const na = Number.parseInt(a.size || "", 10) || 0;
      const nb = Number.parseInt(b.size || "", 10) || 0;
      return na - nb;
    });
  }, [allVariants, hasSizes, isCw]);

  const preferredCwSize =
    (sizeId && cwCaseSizeOptions.some((v) => v.size === sizeId) ? sizeId : undefined) ||
    cwCaseSizeOptions.find((v) => v.inStock)?.size ||
    cwCaseSizeOptions[0]?.size;

  const colorGroupsForUi = useMemo(() => {
    if (!isCw || !hasSizes || !preferredCwSize) return colorGroups;
    return colorGroups
      .map((g) => {
        const variants = g.variants.filter((v) => v.size === preferredCwSize);
        if (variants.length === 0) return null;
        return {
          ...g,
          variants,
          image: variants[0]?.image || g.image,
          inStock: variants.some((v) => v.inStock),
        };
      })
      .filter((g): g is ColorGroup => Boolean(g));
  }, [colorGroups, hasSizes, isCw, preferredCwSize]);

  const selectedColor =
    colorGroupsForUi.find((c) => c.key === colorId) ??
    // Legacy CW links used full variant ids as ?color=
    colorGroupsForUi.find((c) =>
      c.variants.some((v) => v.id === colorId || `cw-${v.id}` === colorId),
    ) ??
    colorGroupsForUi.find((c) => c.inStock) ??
    colorGroupsForUi[0];

  const sizeOptions = isCw && hasSizes
    ? // One chip per case diameter; prefer current strap when available.
      cwCaseSizeOptions.map((chip) => {
        const match =
          (selectedColor &&
            allVariants.find(
              (v) =>
                v.size === chip.size &&
                v.colorKey === selectedColor.key &&
                v.inStock,
            )) ||
          (selectedColor &&
            allVariants.find(
              (v) => v.size === chip.size && v.colorKey === selectedColor.key,
            )) ||
          allVariants.find((v) => v.size === chip.size && v.inStock) ||
          allVariants.find((v) => v.size === chip.size) ||
          chip;
        return match;
      })
    : (selectedColor?.variants ?? []);

  const legacyVariant =
    colorId
      ? allVariants.find((v) => v.id === colorId || `cw-${v.id}` === colorId)
      : undefined;

  const selected =
    (hasSizes
      ? (legacyVariant &&
          (!sizeId || legacyVariant.size === sizeId) &&
          legacyVariant) ||
        sizeOptions.find((v) => v.size === sizeId && v.inStock) ||
        sizeOptions.find((v) => v.size === sizeId) ||
        (isCw && preferredCwSize
          ? selectedColor?.variants.find((v) => v.size === preferredCwSize && v.inStock) ||
            selectedColor?.variants.find((v) => v.size === preferredCwSize) ||
            selectedColor?.variants.find((v) => v.inStock) ||
            selectedColor?.variants[0]
          : undefined) ||
        sizeOptions.find((v) => v.inStock) ||
        sizeOptions[0]
      : allVariants.find((v) => v.id === colorId) ||
        allVariants.find((v) => v.inStock) ||
        allVariants[0]) ?? undefined;

  const selectedAvailable = selected
    ? isVariantInStock(product, selected.id)
    : productAvailable;

  const [braceletCm, setBraceletCm] = useState("no");
  const unitPrice = cartUnitPrice(product, selected, braceletCm);
  const primaryImage = resolveProductImage(product.image, selected?.image);
  const galleryImages = (() => {
    const variantGallery = selected?.images?.filter(Boolean) ?? [];
    if (variantGallery.length > 0) return variantGallery;
    const productGallery = product.images?.filter(Boolean) ?? [];
    if (selected?.image) {
      const rest = productGallery.filter((src) => src !== selected.image);
      return [selected.image, ...rest];
    }
    if (productGallery.length > 0) return productGallery;
    return [primaryImage];
  })();
  const soldOut = !selectedAvailable;
  const salePct = productSalePercent(product, selected);
  const displayCompareAt = selected?.compareAtPrice ?? (
    selected ? undefined : product.compareAtPrice
  );
  const onSale = Boolean(salePct && displayCompareAt);

  const optionLabel = selected
    ? hasSizes
      ? isCw
        ? `${selected.size || ""} · ${selected.colorNameKo || selectedColor?.nameKo || ""}`.trim()
        : `${selected.colorNameKo || selectedColor?.nameKo || ""} · ${selected.size || ""}`.trim()
      : selected.nameKo
    : "";

  const variantLabel =
    product.brand === "Christopher Ward"
      ? "스트랩"
      : hasSizes
        ? "컬러"
        : "컬러";

  const sizeAxisLabel = isCw ? "케이스 사이즈" : "사이즈";

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

  const colorBlock =
    colorGroupsForUi.length > 0 ? (
      <div className="variant-block">
        <p className="variant-block__label">
          {variantLabel} ·{" "}
          <strong>{selectedColor?.nameKo ?? selected?.nameKo}</strong>
          {selectedColor && !selectedColor.inStock ? (
            <span className="product-detail__stock"> · Sold Out</span>
          ) : null}
        </p>
        <ColorSwatches
          productId={product.id}
          colors={colorGroupsForUi}
          selectedKey={selectedColor?.key}
          size={hasSizes ? selected?.size : undefined}
          idPrefix="main"
        />
      </div>
    ) : null;

  const sizeBlock =
    hasSizes && sizeOptions.length > 0 && (selectedColor || isCw) ? (
      <div className="variant-block">
        <p className="variant-block__label">
          {sizeAxisLabel} · <strong>{selected?.size ?? "선택"}</strong>
          {selected && !selected.inStock ? (
            <span className="product-detail__stock"> · Sold Out</span>
          ) : null}
        </p>
        <SizePicker
          productId={product.id}
          colorKey={selectedColor?.key || selected?.colorKey || ""}
          sizes={sizeOptions}
          selectedSize={selected?.size}
        />
        {product.sizeChart ? <SizeChartControl chart={product.sizeChart} /> : null}
      </div>
    ) : null;

  const optionBlocks =
    isCw && hasSizes ? (
      <>
        {sizeBlock}
        {colorBlock}
      </>
    ) : (
      <>
        {colorBlock}
        {sizeBlock}
      </>
    );

  return (
    <div className={`product-page${soldOut ? " product-page--sold-out" : ""}`}>
      <article className="product-detail">
        <ProductGallery
          images={galleryImages}
          alt={`${product.nameKo} ${optionLabel}`}
          soldOut={soldOut}
          badge={optionLabel || selected?.nameKo}
          resetKey={selected?.id ?? product.id}
        />

        <div className="product-detail__info">
          <p className="product-card__brand">{product.brand}</p>
          <div className="product-detail__title-row">
            <h1>{product.nameKo}</h1>
            <ShareLinkButton
              title={`${product.brand} · ${product.nameKo}`}
              url={`/product/${product.id}`}
              compact
              className="product-detail__share"
            />
          </div>
          {selected ? (
            <p className="product-detail__color-name">
              {optionLabel}
              {soldOut ? (
                <span className="product-detail__stock"> · Sold Out</span>
              ) : null}
            </p>
          ) : soldOut ? (
            <p className="product-detail__color-name">
              <span className="product-detail__stock">Sold Out</span>
            </p>
          ) : null}
          <p
            className={`product-detail__price${onSale ? " product-detail__price--sale" : ""}`}
          >
            {soldOut ? (
              "Sold Out"
            ) : onSale && displayCompareAt ? (
              <>
                <span className="product-detail__price-now">
                  {formatKrw(unitPrice)}
                </span>
                <span className="product-detail__price-was">
                  {formatKrw(displayCompareAt)}
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

          {optionBlocks}

          {!soldOut ? braceletBlock : null}

          {soldOut ? (
            <div className="product-detail__sold-panel" role="status">
              <p className="product-detail__sold-mark">Sold Out</p>
              <p className="product-detail__sold-copy">
                현재 선택하신 옵션은 품절입니다. 다른 컬러·사이즈를 확인해
                주시거나, 재입고 시 다시 안내드릴 예정입니다.
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

      <ProductTechSpecs specs={product.techSpecs} features={product.featuresKo} />

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
                  · <strong>{optionLabel}</strong>
                </>
              ) : null}
            </p>
            {isCw && hasSizes && sizeOptions.length > 0 ? (
              <SizePicker
                productId={product.id}
                colorKey={selectedColor?.key || selected?.colorKey || ""}
                sizes={sizeOptions}
                selectedSize={selected?.size}
              />
            ) : null}
            {colorGroupsForUi.length > 0 ? (
              <ColorSwatches
                productId={product.id}
                colors={colorGroupsForUi}
                selectedKey={selectedColor?.key}
                size={hasSizes ? selected?.size : undefined}
                idPrefix="dock"
              />
            ) : product.braceletResize ? null : (
              <p className="pdp-dock__empty">선택 가능한 옵션이 없습니다.</p>
            )}
            {!isCw && hasSizes && sizeOptions.length > 0 && selectedColor ? (
              <>
                <SizePicker
                  productId={product.id}
                  colorKey={selectedColor.key}
                  sizes={sizeOptions}
                  selectedSize={selected?.size}
                />
                {product.sizeChart ? (
                  <SizeChartControl chart={product.sizeChart} />
                ) : null}
              </>
            ) : null}
            {isCw && hasSizes && product.sizeChart ? (
              <SizeChartControl chart={product.sizeChart} />
            ) : null}
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
              {selected ? <span>{optionLabel}</span> : null}
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
                <NaverPayOrderButton
                  page="dock"
                  enabled={!soldOut}
                  className="npay-order-button npay-order-button--dock"
                  items={[
                    {
                      productId: product.id,
                      variantId: selected?.id,
                      braceletCm:
                        product.braceletResize && braceletCm !== "no"
                          ? braceletCm
                          : undefined,
                      qty: 1,
                    },
                  ]}
                />
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
