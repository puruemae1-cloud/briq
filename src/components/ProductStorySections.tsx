import { ProductImage } from "@/components/ProductImage";
import type {  ProductStorySection  } from "@/data/product-types";

function vimeoEmbed(url: string) {
  // Accept full player URL or bare video id path
  if (url.includes("player.vimeo.com")) return url;
  const m = url.match(/vimeo\.com\/(?:video\/)?(\d+)/);
  if (m) return `https://player.vimeo.com/video/${m[1]}`;
  return url;
}

export function ProductStorySections({
  sections,
}: {
  sections: ProductStorySection[];
}) {
  if (!sections.length) return null;

  return (
    <section className="product-story" aria-label="상품 스토리">
      {sections.map((section, idx) => {
        const hasMedia = Boolean(section.image || section.videoUrl);
        const layout = section.layout ?? "default";
        return (
          <article
            key={`${section.titleKo}-${idx}`}
            className={[
              "product-story__block",
              section.reverse ? "product-story__block--reverse" : "",
              hasMedia ? "" : "product-story__block--text",
              layout === "wide" ? "product-story__block--wide" : "",
              layout === "caption" ? "product-story__block--caption" : "",
              section.videoUrl ? "product-story__block--video" : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {section.videoUrl ? (
              <div className="product-story__media product-story__media--video">
                <div className="product-story__video">
                  <iframe
                    src={vimeoEmbed(section.videoUrl)}
                    title={section.titleKo}
                    allow="autoplay; fullscreen; picture-in-picture"
                    allowFullScreen
                    loading="lazy"
                  />
                </div>
              </div>
            ) : section.image ? (
              <div className="product-story__media">
                <ProductImage
                  src={section.image}
                  alt={section.imageAlt ?? section.titleKo}
                  tone="detail"
                />
              </div>
            ) : null}
            <div className="product-story__copy">
              {section.titleKo ? (
                layout === "caption" ? (
                  <h3>{section.titleKo}</h3>
                ) : (
                  <h2>{section.titleKo}</h2>
                )
              ) : null}
              {section.bodyKo
                ? section.bodyKo
                    .split(/\n\n+/)
                    .map((para) => para.trim())
                    .filter(Boolean)
                    .map((para) => (
                      <p key={para.slice(0, 32)}>{para}</p>
                    ))
                : null}
            </div>
          </article>
        );
      })}
    </section>
  );
}
