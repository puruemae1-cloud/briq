import type { SubcategoryId } from "@/data/categories";
import { expandSubcategoryFilter } from "@/data/categories";
import { cwProducts } from "@/data/cw/cw-products";
import { ggCatalogProducts } from "@/data/gg/gg-catalog";
import { bbCatalogProducts } from "@/data/bb/bb-catalog";
import { axCatalogProducts } from "@/data/ax/ax-catalog";
import { axApparelCatalogProducts } from "@/data/ax/ax-apparel-catalog";
import { axOutletCatalogProducts } from "@/data/ax/ax-outlet-catalog";
import { axGearCatalogProducts } from "@/data/ax/ax-gear-catalog";
import { luCatalogProducts } from "@/data/lu/lu-catalog";
import { luLifestyleCatalogProducts } from "@/data/lu/lu-lifestyle-catalog";
import { psCatalogProducts } from "@/data/ps/ps-catalog";
import { bsCatalogProducts } from "@/data/bs/bs-catalog";
import { gcCatalogProducts } from "@/data/gc/gc-catalog";
import { chCatalogProducts } from "@/data/ch/ch-catalog";
import { prCatalogProducts } from "@/data/pr/pr-catalog";
import { lvCatalogProducts } from "@/data/lv/lv-catalog";
import { diCatalogProducts } from "@/data/di/di-catalog";

export type * from "@/data/product-types";
export {
  formatKrw,
  gbpToBriqAddonKrw,
  gbpToBriqKrw,
  isProductInStock,
  isVariantInStock,
  productSalePercent,
} from "@/data/product-utils";
import type { Product } from "@/data/product-types";

export const products: Product[] = [
  ...cwProducts,
  ...ggCatalogProducts,
  ...bbCatalogProducts,
  ...axCatalogProducts,
  ...axApparelCatalogProducts,
  ...axOutletCatalogProducts,
  ...axGearCatalogProducts,
  ...luCatalogProducts,
  ...luLifestyleCatalogProducts,
  ...psCatalogProducts,
  ...bsCatalogProducts,
  ...gcCatalogProducts,
  ...chCatalogProducts,
  ...prCatalogProducts,
  ...lvCatalogProducts,
  ...diCatalogProducts,
];
/** Homepage 100 Collection — full live catalogue (curation picks newest / tiers). */
export function getCollection100() {
  return products;
}

export function getProduct(id: string) {
  const direct = products.find((p) => p.id === id);
  if (direct) return direct;
  // CW strap variants share a parent product — resolve by variant id or sku slug.
  return products.find(
    (p) =>
      p.sku === id ||
      p.variants?.some((v) => v.id === id || `cw-${v.id}` === id || v.sku === id),
  );
}

function isGgShopFilter(expanded?: string[]) {
  if (!expanded?.length) return false;
  return expanded.some(
    (id) =>
      id.startsWith("gg-") || id === "galvin-green" || id === "golf",
  );
}

/**
 * Official Galvin Green PLPs list each colourway as its own card.
 * Expand style-grouped GG products into one shop card per colour.
 */
export function expandGgColourwayCards(
  list: Product[],
  expanded?: string[],
): Product[] {
  if (!isGgShopFilter(expanded)) return list;

  const out: Product[] = [];
  for (const product of list) {
    if (!product.ggCollections?.length || !product.variants?.length) {
      out.push(product);
      continue;
    }

    const styleInStock = product.variants.some((v) => v.inStock);

    const byColor = new Map<string, NonNullable<Product["variants"]>>();
    for (const variant of product.variants) {
      const key = variant.colorKey;
      if (!key) continue;
      const bucket = byColor.get(key);
      if (bucket) bucket.push(variant);
      else byColor.set(key, [variant]);
    }

    if (byColor.size <= 1) {
      // Single colour — still re-filter memberships at colourway level when present.
      const only = byColor.size === 1 ? [...byColor.values()][0] : null;
      const cols = only?.[0]?.ggCollections ?? product.ggCollections;
      if (cols.some((c) => expanded!.includes(c))) {
        out.push(
          only
            ? {
                ...product,
                ggCollections: cols,
                shopColorKey: only[0]?.colorKey,
                image: only[0]?.image || product.image,
                images: only[0]?.images || product.images,
                inStock: styleInStock,
              }
            : product,
        );
      }
      continue;
    }

    for (const [colorKey, variants] of byColor) {
      const cols = variants[0]?.ggCollections ?? product.ggCollections;
      if (!cols.some((c) => expanded!.includes(c))) continue;

      const inStock = variants.filter((v) => v.inStock);
      const priced = (inStock.length ? inStock : variants).slice().sort(
        (a, b) => a.price - b.price,
      );
      const lead = priced[0] ?? variants[0];
      const compareAt =
        lead.compareAtPrice && lead.compareAtPrice > lead.price
          ? lead.compareAtPrice
          : undefined;

      out.push({
        ...product,
        image: lead.image || product.image,
        images: lead.images || product.images,
        price: lead.price,
        compareAtPrice: compareAt,
        gbpPrice: lead.gbpPrice,
        ggCollections: cols,
        variants,
        shopColorKey: colorKey,
        sourceUrl: lead.sourceUrl || product.sourceUrl,
        // Style-level stock for listing badges (other colours may still sell).
        inStock: styleInStock,
      });
    }
  }
  return out;
}

function isBbShopFilter(expanded?: string[]) {
  if (!expanded?.length) return false;
  return expanded.some(
    (id) =>
      id.startsWith("bb-") ||
      id === "burberry" ||
      id === "burberry-bags" ||
      id === "burberry-shoes" ||
      id === "burberry-accessories",
  );
}

function isAxShopFilter(expanded?: string[]) {
  if (!expanded?.length) return false;
  return expanded.some(
    (id) =>
      id.startsWith("ax-") ||
      id === "arcteryx-shoes" ||
      id === "arcteryx" ||
      id === "arcteryx-accessories",
  );
}

/** Official Burberry PLPs list each colourway as its own card. */
export function expandBbColourwayCards(
  list: Product[],
  expanded?: string[],
): Product[] {
  if (!isBbShopFilter(expanded)) return list;

  const out: Product[] = [];
  for (const product of list) {
    if (!product.bbCollections?.length || !product.variants?.length) {
      out.push(product);
      continue;
    }

    const styleInStock = product.variants.some((v) => v.inStock);

    const byColor = new Map<string, NonNullable<Product["variants"]>>();
    for (const variant of product.variants) {
      const key = variant.colorKey;
      if (!key) continue;
      const bucket = byColor.get(key);
      if (bucket) bucket.push(variant);
      else byColor.set(key, [variant]);
    }

    if (byColor.size <= 1) {
      const only = byColor.size === 1 ? [...byColor.values()][0] : null;
      const cols = only?.[0]?.bbCollections ?? product.bbCollections;
      if (cols.some((c) => expanded!.includes(c))) {
        out.push(
          only
            ? {
                ...product,
                bbCollections: cols,
                shopColorKey: only[0]?.colorKey,
                image: only[0]?.image || product.image,
                images: only[0]?.images || product.images,
                inStock: styleInStock,
              }
            : product,
        );
      }
      continue;
    }

    for (const [colorKey, variants] of byColor) {
      const cols = variants[0]?.bbCollections ?? product.bbCollections;
      if (!cols.some((c) => expanded!.includes(c))) continue;

      const inStock = variants.filter((v) => v.inStock);
      const priced = (inStock.length ? inStock : variants).slice().sort(
        (a, b) => a.price - b.price,
      );
      const lead = priced[0] ?? variants[0];
      const compareAt =
        lead.compareAtPrice && lead.compareAtPrice > lead.price
          ? lead.compareAtPrice
          : undefined;

      out.push({
        ...product,
        image: lead.image || product.image,
        images: lead.images || product.images,
        price: lead.price,
        compareAtPrice: compareAt,
        gbpPrice: lead.gbpPrice,
        bbCollections: cols,
        variants,
        shopColorKey: colorKey,
        sourceUrl: lead.sourceUrl || product.sourceUrl,
        inStock: styleInStock,
      });
    }
  }
  return out;
}

/** Arc'teryx PLPs list each colourway as its own card. */
export function expandAxColourwayCards(
  list: Product[],
  expanded?: string[],
): Product[] {
  if (!isAxShopFilter(expanded)) return list;

  const out: Product[] = [];
  for (const product of list) {
    if (!product.axCollections?.length || !product.variants?.length) {
      out.push(product);
      continue;
    }

    const styleInStock = product.variants.some((v) => v.inStock);

    const byColor = new Map<string, NonNullable<Product["variants"]>>();
    for (const variant of product.variants) {
      const key = variant.colorKey;
      if (!key) continue;
      const bucket = byColor.get(key);
      if (bucket) bucket.push(variant);
      else byColor.set(key, [variant]);
    }

    if (byColor.size <= 1) {
      const only = byColor.size === 1 ? [...byColor.values()][0] : null;
      const cols = only?.[0]?.axCollections ?? product.axCollections;
      if (cols.some((c) => expanded!.includes(c))) {
        out.push(
          only
            ? {
                ...product,
                axCollections: cols,
                shopColorKey: only[0]?.colorKey,
                image: only[0]?.image || product.image,
                images: only[0]?.images || product.images,
                inStock: styleInStock,
              }
            : product,
        );
      }
      continue;
    }

    for (const [colorKey, variants] of byColor) {
      const cols = variants[0]?.axCollections ?? product.axCollections;
      if (!cols.some((c) => expanded!.includes(c))) continue;

      const inStock = variants.filter((v) => v.inStock);
      const priced = (inStock.length ? inStock : variants).slice().sort(
        (a, b) => a.price - b.price,
      );
      const lead = priced[0] ?? variants[0];
      const compareAt =
        lead.compareAtPrice && lead.compareAtPrice > lead.price
          ? lead.compareAtPrice
          : undefined;

      out.push({
        ...product,
        image: lead.image || product.image,
        images: lead.images || product.images,
        price: lead.price,
        compareAtPrice: compareAt,
        gbpPrice: lead.gbpPrice,
        axCollections: cols,
        variants,
        shopColorKey: colorKey,
        sourceUrl: lead.sourceUrl || product.sourceUrl,
        inStock: styleInStock,
      });
    }
  }
  return out;
}

function isLuShopFilter(expanded?: string[]) {
  return Boolean(
    expanded?.some(
      (c) =>
        c === "umbrellas" ||
        c === "london-undercover" ||
        c.startsWith("lu-"),
    ),
  );
}

/** London Undercover PLPs list each colourway as its own card. */
export function expandLuColourwayCards(
  list: Product[],
  expanded?: string[],
): Product[] {
  if (!isLuShopFilter(expanded)) return list;

  const out: Product[] = [];
  for (const product of list) {
    if (!product.luCollections?.length || !product.variants?.length) {
      out.push(product);
      continue;
    }

    const styleInStock = product.variants.some((v) => v.inStock);
    const byColor = new Map<string, NonNullable<Product["variants"]>>();
    for (const variant of product.variants) {
      const key = variant.colorKey;
      if (!key) continue;
      const bucket = byColor.get(key);
      if (bucket) bucket.push(variant);
      else byColor.set(key, [variant]);
    }

    if (byColor.size <= 1) {
      const only = byColor.size === 1 ? [...byColor.values()][0] : null;
      const cols = only?.[0]?.luCollections ?? product.luCollections;
      if (cols?.some((c) => expanded!.includes(c))) {
        out.push(
          only
            ? {
                ...product,
                luCollections: cols,
                shopColorKey: only[0]?.colorKey,
                image: only[0]?.image || product.image,
                images: only[0]?.images || product.images,
                hoverImage: only[0]?.hoverImage || product.hoverImage,
                price: only[0]?.price ?? product.price,
                compareAtPrice: only[0]?.compareAtPrice,
                gbpPrice: only[0]?.gbpPrice ?? product.gbpPrice,
                inStock: styleInStock,
              }
            : product,
        );
      }
      continue;
    }

    for (const [colorKey, variants] of byColor) {
      const cols = variants[0]?.luCollections ?? product.luCollections;
      if (!cols?.some((c) => expanded!.includes(c))) continue;

      const inStock = variants.filter((v) => v.inStock);
      const priced = (inStock.length ? inStock : variants)
        .slice()
        .sort((a, b) => a.price - b.price);
      const lead = priced[0] ?? variants[0];
      const compareAt =
        lead.compareAtPrice && lead.compareAtPrice > lead.price
          ? lead.compareAtPrice
          : undefined;

      out.push({
        ...product,
        name: `${product.name} — ${lead.colorNameKo || lead.name}`,
        nameKo: `${product.nameKo} — ${lead.colorNameKo || lead.nameKo}`,
        image: lead.image || product.image,
        images: lead.images || product.images,
        hoverImage: lead.hoverImage || product.hoverImage,
        price: lead.price,
        compareAtPrice: compareAt,
        gbpPrice: lead.gbpPrice,
        luCollections: cols,
        variants,
        shopColorKey: colorKey,
        sourceUrl: lead.sourceUrl || product.sourceUrl,
        inStock: styleInStock,
      });
    }
  }
  return out;
}

export function getProductsByCategory(category?: string, sub?: string) {
  let list = products;
  const expanded = expandSubcategoryFilter(sub);
  // Gift PLPs include apparel/bags/shoes tagged with gifts*; skip category gate.
  const isPsGifts =
    expanded?.some((c) => c === "ps-gifts" || c.startsWith("ps-gifts-")) ?? false;
  const isGcGifts =
    expanded?.some(
      (c) =>
        c === "gc-gifts" ||
        c.startsWith("gc-gifts-") ||
        c === "gc-men-gifts" ||
        c.startsWith("gc-men-gifts-"),
    ) ?? false;
  // Dior Icons hub mixes jewellery + timepieces on the official PLP.
  const isDiDiorIcons = sub === "di-dior-icons";
  if (category && category !== "all" && !isPsGifts && !isGcGifts && !isDiDiorIcons) {
    list = list.filter((p) => p.category === category);
  }
  if (expanded) {
    list = list.filter((p) => {
      if (p.subcategory && expanded.includes(p.subcategory)) return true;
      if (p.cwCollections?.some((c) => expanded.includes(c))) return true;
      if (p.ggCollections?.some((c) => expanded.includes(c))) return true;
      if (p.bbCollections?.some((c) => expanded.includes(c))) return true;
      if (p.axCollections?.some((c) => expanded.includes(c))) return true;
      if (p.luCollections?.some((c) => expanded.includes(c))) return true;
      if (p.psCollections?.some((c) => expanded.includes(c))) return true;
      if (p.bsCollections?.some((c) => expanded.includes(c))) return true;
      if (p.gcCollections?.some((c) => expanded.includes(c))) return true;
      if (p.chCollections?.some((c) => expanded.includes(c))) return true;
      if (p.prCollections?.some((c) => expanded.includes(c))) return true;
      if (p.lvCollections?.some((c) => expanded.includes(c))) return true;
      if (p.diCollections?.some((c) => expanded.includes(c))) return true;
      if (p.variants?.some((v) => v.ggCollections?.some((c) => expanded.includes(c))))
        return true;
      if (p.variants?.some((v) => v.bbCollections?.some((c) => expanded.includes(c))))
        return true;
      if (p.variants?.some((v) => v.axCollections?.some((c) => expanded.includes(c))))
        return true;
      if (p.variants?.some((v) => v.luCollections?.some((c) => expanded.includes(c))))
        return true;
      if (p.variants?.some((v) => v.psCollections?.some((c) => expanded.includes(c))))
        return true;
      if (p.variants?.some((v) => v.bsCollections?.some((c) => expanded.includes(c))))
        return true;
      if (p.variants?.some((v) => v.gcCollections?.some((c) => expanded.includes(c))))
        return true;
      if (p.variants?.some((v) => v.chCollections?.some((c) => expanded.includes(c))))
        return true;
      if (p.variants?.some((v) => v.prCollections?.some((c) => expanded.includes(c))))
        return true;
      if (p.variants?.some((v) => v.lvCollections?.some((c) => expanded.includes(c))))
        return true;
      if (p.variants?.some((v) => v.diCollections?.some((c) => expanded.includes(c))))
        return true;
      return false;
    });
    list = expandGgColourwayCards(list, expanded);
    list = expandBbColourwayCards(list, expanded);
    list = expandAxColourwayCards(list, expanded);
    list = expandLuColourwayCards(list, expanded);
  }
  return list;
}

/** @deprecated use navCategories from categories.ts */
export const categories = [
  { id: "luxury" as const, label: "Signature", labelKo: "시그니처 의류 컬렉션" },
  { id: "watches" as const, label: "Watches", labelKo: "시계" },
  { id: "bags" as const, label: "Bags", labelKo: "가방" },
  { id: "shoes" as const, label: "Shoes", labelKo: "슈즈" },
  { id: "accessories" as const, label: "Accessories", labelKo: "악세서리" },
  { id: "sports" as const, label: "Sports", labelKo: "스포츠" },
];
