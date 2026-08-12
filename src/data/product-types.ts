import type { CategoryId, SubcategoryId } from "@/data/categories";

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
   * Official brand PLP hover/swap photo for this colourway.
   * When omitted, cards fall back to the first gallery frame ≠ primary.
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
  /** London Undercover colourway PLP memberships (per colour). */
  luCollections?: SubcategoryId[];
  /** Paul Smith PLP memberships. */
  psCollections?: SubcategoryId[];
  /** Belstaff PLP memberships. */
  bsCollections?: SubcategoryId[];
  /** Gucci PLP memberships. */
  gcCollections?: SubcategoryId[];
  /** Chanel PLP memberships. */
  chCollections?: SubcategoryId[];
};

export type ProductTechSpec = {
  labelKo: string;
  valueKo: string;
};

export type ProductSizeChartTab = {
  id: string;
  labelKo: string;
  headers: string[];
  rows: string[][];
};

export type ProductSizeChart = {
  id: string;
  titleKo: string;
  noteKo: string;
  headers: string[];
  rows: string[][];
  /** Optional Tops / Bottoms tabs (Gucci RTW size guide). */
  tabs?: ProductSizeChartTab[];
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
  /** London Undercover umbrella PLP memberships. */
  luCollections?: SubcategoryId[];
  /** Paul Smith PLP memberships. */
  psCollections?: SubcategoryId[];
  /** Belstaff PLP memberships. */
  bsCollections?: SubcategoryId[];
  /** Gucci PLP memberships. */
  gcCollections?: SubcategoryId[];
  /** Chanel Ready-to-Wear PLP memberships. */
  chCollections?: SubcategoryId[];
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
   * Official brand PLP hover/swap photo (model / wrist / Hover.jpg).
   * When omitted, cards use the first gallery frame that differs from `image`.
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
   * Catalogue registration time on Briq (ISO). Used by 최신등록순 / homepage rails.
   * Always set this when first adding a product — newer timestamps rank first.
   * Rebuilds should preserve the original value so new imports stay on top.
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

