import { ProductImage } from "@/components/ProductImage";
import type { ProductStorySection } from "@/data/products";

export function ProductStorySections({
  sections,
}: {
  sections: ProductStorySection[];
}) {
  if (!sections.length) return null;

  return (
    <section className="product-story" aria-label="상품 스토리">
      {sections.map((section) => (
        <article
          key={section.titleKo}
          className={`product-story__block${section.reverse ? " product-story__block--reverse" : ""}${section.image ? "" : " product-story__block--text"}`}
        >
          {section.image ? (
            <div className="product-story__media">
              <ProductImage
                src={section.image}
                alt={section.imageAlt ?? section.titleKo}
                tone="detail"
              />
            </div>
          ) : null}
          <div className="product-story__copy">
            <h2>{section.titleKo}</h2>
            {section.bodyKo.split("\n\n").map((para) => (
              <p key={para.slice(0, 24)}>{para}</p>
            ))}
          </div>
        </article>
      ))}
    </section>
  );
}
