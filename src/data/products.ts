import type { CategoryId, SubcategoryId } from "@/data/categories";
import { expandSubcategoryFilter } from "@/data/categories";
import { cwProducts } from "@/data/cw/cw-products";
import { ggCatalogProducts } from "@/data/gg/gg-catalog";
import { bbCatalogProducts } from "@/data/bb/bb-catalog";
import { axCatalogProducts } from "@/data/ax/ax-catalog";
import { axApparelCatalogProducts } from "@/data/ax/ax-apparel-catalog";
import { axOutletCatalogProducts } from "@/data/ax/ax-outlet-catalog";
import { axGearCatalogProducts } from "@/data/ax/ax-gear-catalog";

export type ProductStorySection = {
  titleKo: string;
  bodyKo: string;
  image?: string;
  imageAlt?: string;
  reverse?: boolean;
  /** Optional embedded video (e.g. Vimeo). */
  videoUrl?: string;
  /** Full-bleed / caption-card presentation. */
  layout?: "default" | "wide" | "caption";
};

export type ProductVariant = {
  id: string;
  name: string;
  nameKo: string;
  sku: string;
  gbpPrice: number;
  price: number;
  /** Pre-sale list price (KRW) for this colour/size when on sale. */
  compareAtPrice?: number;
  /**
   * Catalog photo path under `/public/products/`.
   * Use the shared 4:5 framing standard — see `src/lib/product-image.ts`.
   */
  image: string;
  /** Optional multi-image gallery for this strap/colour option. */
  images?: string[];
  /**
   * Optional PLP hover photo for this colourway (model / wrist shot).
   * When omitted, cards fall back to `images[1]`.
   */
  hoverImage?: string;
  sourceUrl: string;
  inStock: boolean;
  /** Colour group key when a product also has size options (e.g. apparel). */
  colorKey?: string;
  colorNameKo?: string;
  /** Size code when variants are colour × size (e.g. S / M / L). */
  size?: string;
  /**
   * Galvin Green colourway PLP memberships (per colour, not whole style).
   * Used so Men/Women shop grids match official colourway counts.
   */
  ggCollections?: SubcategoryId[];
  /** Burberry colourway PLP memberships (per colour). */
  bbCollections?: SubcategoryId[];
  /** Arc'teryx colourway PLP memberships (per colour). */
  axCollections?: SubcategoryId[];
};

export type ProductTechSpec = {
  labelKo: string;
  valueKo: string;
};

export type ProductSizeChart = {
  id: string;
  titleKo: string;
  noteKo: string;
  headers: string[];
  rows: string[][];
};

export type Product = {
  id: string;
  name: string;
  nameKo: string;
  brand: string;
  /** Selling price (KRW). When on sale this is the discounted amount. */
  price: number;
  /** Pre-sale / list price (KRW). Shown struck-through when higher than `price`. */
  compareAtPrice?: number;
  category: CategoryId;
  subcategory?: SubcategoryId;
  /**
   * Christopher Ward PLP memberships (a SKU can sit in New Releases + Twelve etc.).
   */
  cwCollections?: SubcategoryId[];
  /**
   * Galvin Green PLP memberships (e.g. New Arrivals + Bestsellers).
   */
  ggCollections?: SubcategoryId[];
  /** Burberry Women PLP memberships across luxury/bags/shoes/accessories. */
  bbCollections?: SubcategoryId[];
  /** Arc'teryx footwear PLP memberships (men/women). */
  axCollections?: SubcategoryId[];
  tags: string[];
  /** Customer-facing Korean description only */
  descriptionKo?: string;
  /**
   * Primary catalog photo (`/public/products/...`).
   * Prefer ~1600×2000 (4:5), subject centered — rendered via `ProductImage`
   * with `object-fit: contain` so all grid/PDP/cart tiles stay uniform.
   */
  image: string;
  images?: string[];
  /**
   * Optional PLP hover photo (model / wrist shot).
   * When omitted, cards use the second gallery image if available.
   */
  hoverImage?: string;
  accent: string;
  badge?: string;
  gbpPrice?: number;
  /** Original GBP list price when the CW site shows a reduction. */
  gbpListPrice?: number;
  sku?: string;
  sourceUrl?: string;
  size?: string;
  variants?: ProductVariant[];
  /**
   * Product-level stock when there are no variants.
   * With variants, availability is derived from `variant.inStock`.
   */
  inStock?: boolean;
  /**
   * Optional bracelet resize (Christopher Ward).
   * Selecting any cm size adds `feeKrw`; "no" keeps base price.
   */
  braceletResize?: {
    feeKrw: number;
    sizesCm: string[];
  };
  /** Long-form PDP story blocks (image + Korean copy). */
  storySections?: ProductStorySection[];
  /** Tech specs & features (Christopher Ward PDP). */
  techSpecs?: ProductTechSpec[];
  featuresKo?: string[];
  /** Adult Burberry shoe size conversion chart shown next to size picker. */
  sizeChart?: ProductSizeChart;
  /**
   * Catalogue registration time (ISO). Used by 최신등록순.
   * Always set this when adding a product — newer timestamps rank first.
   */
  registeredAt?: string;
  /**
   * 100 Collection / homepage edit bucket.
   * Set when registering: "signature" | "bestseller" | "new".
   * If omitted, inferred from price / badge / recency.
   */
  editTier?: "signature" | "bestseller" | "new";
  /**
   * Shop PLP colourway expand — when set, the card links to this colour on PDP.
   */
  shopColorKey?: string;
};

/** KRW = round_만원(GBP × 2100 × 1.05 + 200,000) */
export function gbpToBriqKrw(gbp: number) {
  return Math.round((gbp * 2100 * 1.05 + 200_000) / 10_000) * 10_000;
}

/** Addon fees (bracelet resize etc.) — no +200,000 base, still 만원 rounding. */
export function gbpToBriqAddonKrw(gbp: number) {
  return Math.round((gbp * 2100 * 1.05) / 10_000) * 10_000;
}

/** Sale discount percent from compareAt → price, or null if not on sale.
 * When a variant is selected, only that variant's compareAtPrice counts
 * (so non-sale colours don't inherit another colourway's discount).
 */
export function productSalePercent(
  product: Product,
  variant?: ProductVariant | null,
) {
  const price = variant?.price ?? product.price;
  const was = variant
    ? variant.compareAtPrice
    : product.compareAtPrice;
  if (!was || was <= price) return null;
  return Math.max(1, Math.round((1 - price / was) * 100));
}

/** True if the product (or any of its variants) can be purchased. */
export function isProductInStock(product: Product) {
  // Colourway-expanded shop cards keep only one colour's sizes in `variants`.
  // Listing sold-out must reflect the whole style — if another colour is
  // available, do not mark the card Sold Out.
  if (product.shopColorKey != null && typeof product.inStock === "boolean") {
    return product.inStock;
  }
  if (product.variants && product.variants.length > 0) {
    return product.variants.some((v) => v.inStock);
  }
  return product.inStock !== false;
}

/** True if a specific variant (or the product itself) is purchasable. */
export function isVariantInStock(product: Product, variantId?: string | null) {
  if (product.variants && product.variants.length > 0) {
    if (!variantId) return false;
    return product.variants.some((v) => v.id === variantId && v.inStock);
  }
  return product.inStock !== false;
}

const chinoCapVariants: ProductVariant[] = [
  {
    id: "black-white",
    name: "black/white",
    nameKo: "블랙/화이트",
    sku: "PO252P011-Q11",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: "/products/prl-chino-cap-black-white.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-cotton-chino-ball-cap-cap-blackwhite-po252p011-q11.html",
    inStock: false,
  },
  {
    id: "company-olive",
    name: "company olive",
    nameKo: "컴퍼니 올리브",
    sku: "PO252P011-M15",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: "/products/prl-chino-cap-company-olive.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-the-iconic-cotton-chino-ball-cap-cap-company-olive-po252p011-m15.html",
    inStock: false,
  },
  {
    id: "cruise-lime",
    name: "cruise lime",
    nameKo: "크루즈 라임",
    sku: "PO252P011-K19",
    gbpPrice: 60,
    price: gbpToBriqKrw(60),
    image: "/products/prl-chino-cap-cruise-lime.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-the-iconic-cotton-chino-ball-cap-cap-cruise-lime-po252p011-k19.html",
    inStock: false,
  },
  {
    id: "garden-trail-cream",
    name: "garden trail/cream pp",
    nameKo: "가든 트레일/크림",
    sku: "PO252P011-Q12",
    gbpPrice: 54,
    price: gbpToBriqKrw(54),
    image: "/products/prl-chino-cap-garden-trail-cream.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-the-iconic-cotton-chino-ball-cap-cap-garden-trailcream-pp-po252p011-q12.html",
    inStock: false,
  },
  {
    id: "new-forest",
    name: "new forest",
    nameKo: "뉴 포레스트",
    sku: "PO252P011-M11",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: "/products/prl-chino-cap-new-forest.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-cotton-chino-ball-cap-cap-new-forest-po252p011-m11.html",
    inStock: false,
  },
  {
    id: "rustic-navy",
    name: "rustic navy",
    nameKo: "러스틱 네이비",
    sku: "PO252P011-K13",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: "/products/prl-chino-cap-rustic-navy.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-chino-ball-hat-cap-rustic-navy-po252p011-k13.html",
    inStock: false,
  },
  {
    id: "rustic-tan",
    name: "rustic tan",
    nameKo: "러스틱 탄",
    sku: "PO252P011-B11",
    gbpPrice: 54,
    price: gbpToBriqKrw(54),
    image: "/products/prl-chino-cap-rustic-tan.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-cotton-chino-ball-cap-cap-rustic-tan-po252p011-b11.html",
    inStock: false,
  },
  {
    id: "terrace-pink",
    name: "terrace pink/c7560",
    nameKo: "테라스 핑크",
    sku: "PO252P011-J11",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: "/products/prl-chino-cap-terrace-pink.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-the-iconic-cotton-chino-ball-cap-cap-terrace-pinkc7560-po252p011-j11.html",
    inStock: false,
  },
  {
    id: "wisteria",
    name: "wisteria w/ c9601",
    nameKo: "위스테리아",
    sku: "PO252P011-I12",
    gbpPrice: 70,
    price: gbpToBriqKrw(70),
    image: "/products/prl-chino-cap-wisteria.jpg",
    sourceUrl:
      "https://www.zalando.co.uk/polo-ralph-lauren-the-iconic-cotton-chino-ball-cap-cap-wisteria-w-c9601-po252p011-i12.html",
    inStock: false,
  },
];

const chinoCapMinPrice = Math.min(...chinoCapVariants.map((v) => v.price));

export const products: Product[] = [
  {
    id: "prl-chino-cap",
    name: "The Iconic Cotton Chino Ball Cap",
    nameKo: "폴로 랄프 로렌 아이코닉 코튼 치노 볼캡",
    brand: "Polo Ralph Lauren",
    price: chinoCapMinPrice,
    gbpPrice: Math.min(...chinoCapVariants.map((v) => v.gbpPrice)),
    category: "accessories",
    tags: ["cap", "cotton", "one-size"],
    descriptionKo: "100% 코튼 치노 볼캡. 포니 자수, 버클 조절 스트랩. 사이즈 One Size.",
    image: chinoCapVariants[0].image,
    images: chinoCapVariants.map((v) => v.image),
    accent: "#1a1a1a",
    badge: "New",
    editTier: "new",
    size: "One Size",
    sku: "PO252P011",
    sourceUrl: chinoCapVariants[0].sourceUrl,
    variants: chinoCapVariants,
    registeredAt: "2026-07-20T09:00:00.000Z",
  },
  ...cwProducts,
  ...ggCatalogProducts,
  ...bbCatalogProducts,
  ...axCatalogProducts,
  ...axApparelCatalogProducts,
  ...axOutletCatalogProducts,
  ...axGearCatalogProducts,
];

/** Homepage 100 Collection — full live catalogue (curation picks newest / tiers). */
export function getCollection100() {
  return products;
}

export function formatKrw(price: number) {
  return `${new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: 0,
  }).format(price)}원`;
}

export function getProduct(id: string) {
  if (id === "prl-chino-cap-old-royal") {
    return products.find((p) => p.id === "prl-chino-cap");
  }
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

export function getProductsByCategory(category?: string, sub?: string) {
  let list = products;
  if (category && category !== "all") {
    list = list.filter((p) => p.category === category);
  }
  const expanded = expandSubcategoryFilter(sub);
  if (expanded) {
    list = list.filter((p) => {
      if (p.subcategory && expanded.includes(p.subcategory)) return true;
      if (p.cwCollections?.some((c) => expanded.includes(c))) return true;
      if (p.ggCollections?.some((c) => expanded.includes(c))) return true;
      if (p.bbCollections?.some((c) => expanded.includes(c))) return true;
      if (p.axCollections?.some((c) => expanded.includes(c))) return true;
      if (p.variants?.some((v) => v.ggCollections?.some((c) => expanded.includes(c))))
        return true;
      if (p.variants?.some((v) => v.bbCollections?.some((c) => expanded.includes(c))))
        return true;
      if (p.variants?.some((v) => v.axCollections?.some((c) => expanded.includes(c))))
        return true;
      return false;
    });
    list = expandGgColourwayCards(list, expanded);
    list = expandBbColourwayCards(list, expanded);
    list = expandAxColourwayCards(list, expanded);
  }
  return list;
}

/** @deprecated use navCategories from categories.ts */
export const categories = [
  { id: "luxury" as const, label: "Luxury", labelKo: "명품 하이엔드 의류" },
  { id: "watches" as const, label: "Watches", labelKo: "시계" },
  { id: "clothing" as const, label: "Clothing", labelKo: "패션의류" },
  { id: "bags" as const, label: "Bags", labelKo: "가방" },
  { id: "shoes" as const, label: "Shoes", labelKo: "슈즈" },
  { id: "accessories" as const, label: "Accessories", labelKo: "악세서리" },
  { id: "sports" as const, label: "Sports", labelKo: "스포츠" },
];
