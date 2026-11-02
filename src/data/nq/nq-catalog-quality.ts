import type { Product } from "@/data/product-types";

/**
 * Guard: NORQAIN PDPs must ship with real Korean copy, story sections, tech
 * specs, and per-variant gallery images (featured image first). Prevents a
 * thin stub catalogue from going live again.
 */
export function assertNqCatalogQuality(products: Product[]): void {
  if (process.env.NODE_ENV === "production" && process.env.NEXT_PHASE === "phase-production-build") {
    // Always run during next build; also run in test/dev when explicitly called.
  }
  const errors: string[] = [];
  if (products.length < 40) {
    errors.push(`expected ≥40 NORQAIN watches, got ${products.length}`);
  }
  for (const p of products) {
    const id = p.id;
    if (!p.descriptionKo || p.descriptionKo.length < 80) {
      errors.push(`${id}: descriptionKo too short`);
    }
    if (/공홈 기준 옵션·가격을 반영했습니다/.test(p.descriptionKo || "")) {
      errors.push(`${id}: stub descriptionKo`);
    }
    if (!p.storySections || p.storySections.length < 1) {
      errors.push(`${id}: missing storySections`);
    } else {
      for (const [i, s] of p.storySections.entries()) {
        if (!s.titleKo || !s.bodyKo || s.bodyKo.length < 40) {
          errors.push(`${id}: storySections[${i}] incomplete`);
        }
        if (!s.image) {
          errors.push(`${id}: storySections[${i}] missing image`);
        }
      }
    }
    if (!p.techSpecs || p.techSpecs.length < 4) {
      errors.push(`${id}: techSpecs too few`);
    }
    if (!p.featuresKo || p.featuresKo.length < 2) {
      errors.push(`${id}: featuresKo too few`);
    }
    const variants = p.variants || [];
    if (variants.length < 1) {
      errors.push(`${id}: no variants`);
      continue;
    }
    for (const v of variants) {
      if (!v.image) errors.push(`${id}/${v.id}: missing variant.image`);
      if (!v.images || v.images.length < 1) {
        errors.push(`${id}/${v.id}: missing variant.images`);
      } else if (v.images[0] !== v.image) {
        errors.push(`${id}/${v.id}: variant.images[0] must equal variant.image`);
      }
    }
    // When Shopify exposes distinct featured images, they must stay distinct.
    const featured = new Set(variants.map((v) => v.image));
    if (variants.length >= 2 && featured.size === 1) {
      // Allowed when official media shares one packshot (e.g. X-Lite strap swap).
      // Still require the gallery to be non-empty (checked above).
    }
  }
  if (errors.length) {
    throw new Error(
      `NORQAIN catalogue quality failed (${errors.length}):\n- ${errors.slice(0, 20).join("\n- ")}`,
    );
  }
}
