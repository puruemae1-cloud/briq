import type { Product } from "@/data/product-types";

/**
 * Guard: NORQAIN PDPs must ship with real Korean copy, story sections, tech
 * specs, and per-variant gallery images (featured image first). Prevents a
 * thin stub catalogue from going live again.
 */
export function assertNqCatalogQuality(products: Product[]): void {
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
    {
      const text = p.descriptionKo || "";
      const latin = (text.match(/[A-Za-z]/g) || []).length;
      const hangul = (text.match(/[\uac00-\ud7a3]/g) || []).length;
      if (latin > 40 && latin > hangul) {
        errors.push(`${id}: descriptionKo still mostly English`);
      }
    }
    if (!p.storySections || p.storySections.length < 1) {
      errors.push(`${id}: missing storySections`);
    } else {
      for (const [i, s] of p.storySections.entries()) {
        const isVideo = Boolean(s.videoUrl);
        if (!s.titleKo) {
          errors.push(`${id}: storySections[${i}] missing titleKo`);
        }
        if (!isVideo && (!s.bodyKo || s.bodyKo.length < 40)) {
          errors.push(`${id}: storySections[${i}] incomplete`);
        }
        if (isVideo && (!s.bodyKo || s.bodyKo.length < 20)) {
          errors.push(`${id}: storySections[${i}] video copy too short`);
        }
        if (!isVideo && !s.image) {
          errors.push(`${id}: storySections[${i}] missing image`);
        }
        if (isVideo && !/\.(mp4|webm|mov)(\?|#|$)/i.test(s.videoUrl || "")) {
          errors.push(`${id}: storySections[${i}] videoUrl not a direct video file`);
        }
      }
    }
    if (!p.techSpecs || p.techSpecs.length < 4) {
      errors.push(`${id}: techSpecs too few`);
    } else {
      for (const [i, spec] of p.techSpecs.entries()) {
        if (/^[A-Za-z][A-Za-z \/-]{2,}$/.test(spec.labelKo || "")) {
          errors.push(`${id}: techSpecs[${i}] label still English (${spec.labelKo})`);
        }
      }
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
  }
  if (errors.length) {
    throw new Error(
      `NORQAIN catalogue quality failed (${errors.length}):\n- ${errors.slice(0, 20).join("\n- ")}`,
    );
  }
}
