import type { ProductTechSpec } from "@/data/products";

export function ProductTechSpecs({
  specs,
  features,
}: {
  specs?: ProductTechSpec[];
  features?: string[];
}) {
  if (!specs?.length && !features?.length) return null;

  return (
    <section className="product-tech" aria-label="기술 사양">
      <div className="product-tech__inner">
        <p className="product-tech__eyebrow">Tech Specs & Features</p>
        <h2 className="product-tech__title">기술 사양 & 특징</h2>

        {features?.length ? (
          <ul className="product-tech__features">
            {features.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        ) : null}

        {specs?.length ? (
          <dl className="product-tech__grid">
            {specs.map((s) => (
              <div key={`${s.labelKo}-${s.valueKo}`} className="product-tech__row">
                <dt>{s.labelKo}</dt>
                <dd>{s.valueKo}</dd>
              </div>
            ))}
          </dl>
        ) : null}
      </div>
    </section>
  );
}
