import Link from "next/link";
import { ProductCardMedia } from "@/components/ProductCardMedia";
import { ShareLinkButton } from "@/components/ShareLinkButton";
import type { Product } from "@/data/product-types";
import {
  formatKrw,
  isProductInStock,
  productSalePercent,
} from "@/data/product-utils";
import { needsChanelMobilePackshotZoom, needsChanelPcPackshotZoom } from "@/lib/ch-packshot-zoom";

function productCardPriceLabel(product: Product): string {
  const base = formatKrw(product.price);
  const prices = (product.variants ?? []).map((v) => v.price);
  if (prices.length === 0) return base;
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  return min !== max ? `${base}~` : base;
}

function productHref(product: Product) {
  return product.shopColorKey
    ? `/product/${product.id}?color=${encodeURIComponent(product.shopColorKey)}`
    : `/product/${product.id}`;
}

export function ProductCard({ product }: { product: Product }) {
  const soldOut = !isProductInStock(product);
  const salePct = productSalePercent(product);
  const onSale = Boolean(salePct && product.compareAtPrice);
  const isClearance =
    product.subcategory === "cw-clearance" ||
    product.subcategory === "gg-sale" ||
    product.cwCollections?.includes("cw-clearance") ||
    Boolean(product.ggCollections?.includes("gg-sale")) ||
    product.badge === "Nearly New" ||
    product.badge === "Sale";
  const chPackshotZoom = needsChanelMobilePackshotZoom(product);
  const chPackshotZoomPc = needsChanelPcPackshotZoom(product);
  const href = productHref(product);

  return (
    <div className="product-card-shell">
      <ShareLinkButton
        title={`${product.brand} · ${product.nameKo}`}
        url={href}
        compact
        className="product-card-shell__share"
      />
      <Link
        href={href}
        className={`product-card group${soldOut ? " product-card--sold-out" : ""}${
          chPackshotZoom ? " product-card--ch-packshot-zoom" : ""
        }${chPackshotZoomPc ? " product-card--ch-packshot-zoom-pc" : ""}`}
      >
        <ProductCardMedia product={product} soldOut={soldOut}>
          {soldOut ? (
            <span className="product-sold-out" aria-label="Sold Out">
              Sold Out
            </span>
          ) : onSale ? (
            <span
              className={`product-card__badge product-card__badge--sale${
                isClearance ? " product-card__badge--clearance" : ""
              }`}
            >
              {salePct}% OFF
            </span>
          ) : product.badge ? (
            <span
              className={`product-card__badge${
                isClearance ? " product-card__badge--clearance" : ""
              }`}
            >
              {product.badge}
            </span>
          ) : null}
        </ProductCardMedia>
        <div className="product-card__body">
          <p className="product-card__brand">{product.brand}</p>
          <h3 className="product-card__name">{product.nameKo}</h3>
          {soldOut ? (
            <p className="product-card__price">Sold Out</p>
          ) : onSale && product.compareAtPrice ? (
            <p className="product-card__price product-card__price--sale">
              <span className="product-card__price-now">{formatKrw(product.price)}</span>
              <span className="product-card__price-was">
                {formatKrw(product.compareAtPrice)}
              </span>
              <span className="product-card__price-pct">{salePct}%</span>
            </p>
          ) : (
            <p className="product-card__price">{productCardPriceLabel(product)}</p>
          )}
        </div>
      </Link>
    </div>
  );
}
