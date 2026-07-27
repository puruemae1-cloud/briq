import Link from "next/link";
import { ProductImage } from "@/components/ProductImage";
import { formatKrw, isProductInStock, type Product } from "@/data/products";

export function ProductCard({ product }: { product: Product }) {
  const soldOut = !isProductInStock(product);

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
        ) : product.badge ? (
          <span className="product-card__badge">{product.badge}</span>
        ) : null}
      </ProductImage>
      <div className="product-card__body">
        <p className="product-card__brand">{product.brand}</p>
        <h3 className="product-card__name">{product.nameKo}</h3>
        <p className="product-card__price">
          {soldOut
            ? "Sold Out"
            : product.variants && product.variants.length > 0
              ? `${formatKrw(product.price)}~`
              : formatKrw(product.price)}
        </p>
      </div>
    </Link>
  );
}
