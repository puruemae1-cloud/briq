import { ProductCard } from "@/components/ProductCard";
import type { Product } from "@/data/products";
import {
  EDIT_TIER_COPY,
  type EditTier,
} from "@/lib/collection-edit";

/** One 100 Collection tier — safe to render on the server. */
export function CollectionTierBlock({
  tier,
  products,
}: {
  tier: EditTier;
  products: Product[];
}) {
  if (!products.length) return null;
  const copy = EDIT_TIER_COPY[tier];
  return (
    <div className="collection-edit-tier">
      <header className="collection-edit-tier__head">
        <h3 className="collection-edit-tier__title">{copy.titleKo}</h3>
      </header>
      <div className="product-grid">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  );
}
