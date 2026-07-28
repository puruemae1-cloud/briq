import Link from "next/link";
import { ProductImage } from "@/components/ProductImage";
import {
  formatKrw,
  isProductInStock,
  productSalePercent,
  type Product,
} from "@/data/products";

export function ProductCard({ product }: { product: Product }) {
  const soldOut = !isProductInStock(product);
  const salePct = productSalePercent(product);
  const onSale = Boolean(salePct && product.compareAtPrice);
  const isClearance =
    product.subcategory === "cw-clearance" ||
    product.cwCollections?.includes("cw-clearance") ||
    product.badge === "Nearly New";

  return (
    <Link
      href={`/product/${product.id}`}
      className={`product-card group${soldOut ? " product-card--sold-out" : ""}`}
    >
      <ProductImage
        src={product.image}
        alt={product.nameKo}
        tone="card"
        imgClassName="product-card__img"
      >
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
      </ProductImage>
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
          <p className="product-card__price">
            {product.variants && product.variants.length > 0
              ? `${formatKrw(product.price)}~`
              : formatKrw(product.price)}
          </p>
        )}
      </div>
    </Link>
  );
}
