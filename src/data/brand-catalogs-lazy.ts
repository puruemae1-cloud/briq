import type { Product } from "@/data/product-types";
import { expandSubcategoryFilter } from "@/data/categories";
import { readCatalogJson } from "@/data/catalog-json";
import { isYsShopSub } from "@/data/ys/ys-catalog-lazy";

/**
 * Per-brand lazy catalogue loaders.
 *
 * Static `import` of every brand JSON into `products.ts` forces Node to parse
 * hundreds of MB on any `/shop` hit — including a single-brand PLP. Weekly sync
 * grows those files; scoped `require()` keeps brand clicks fast regardless.
 */

export type BrandCatalogKey =
  | "cw"
  | "gg"
  | "bb"
  | "ax"
  | "lu"
  | "ps"
  | "bs"
  | "gc"
  | "bv"
  | "ch"
  | "ce"
  | "vw"
  | "al"
  | "pr"
  | "lv"
  | "di"
  | "mb";

const ALL_KEYS: BrandCatalogKey[] = [
  "cw",
  "gg",
  "bb",
  "ax",
  "lu",
  "ps",
  "bs",
  "gc",
  "bv",
  "ch",
  "ce",
  "vw",
  "al",
  "pr",
  "lv",
  "di",
  "mb",
];

type Loader = () => Product[];

const cache = new Map<BrandCatalogKey, Product[]>();
const bagsCache = new Map<BrandCatalogKey, Product[]>();
const shoesCache = new Map<BrandCatalogKey, Product[]>();
let allCache: Product[] | null = null;
let allBagsCache: Product[] | null = null;
let allShoesCache: Product[] | null = null;

/** Brands with a bags-only JSON slice (bags PLPs must not parse full catalogues). */
const BAGS_BRAND_KEYS: BrandCatalogKey[] = [
  "bb",
  "ax",
  "gc",
  "bv",
  "ch",
  "al",
  "ce",
  "vw",
  "pr",
  "di",
  "mb",
];

/** Brands with a shoes-only JSON slice (shoes PLPs must not parse full catalogues). */
const SHOES_BRAND_KEYS: BrandCatalogKey[] = [
  "bb",
  "ax",
  "ps",
  "bs",
  "gc",
  "bv",
  "ch",
  "al",
  "ce",
  "vw",
  "pr",
  "di",
];

function cached(
  map: Map<BrandCatalogKey, Product[]>,
  key: BrandCatalogKey,
  load: Loader,
): Product[] {
  let hit = map.get(key);
  if (!hit) {
    hit = load();
    map.set(key, hit);
  }
  return hit;
}

const LOADERS: Record<BrandCatalogKey, Loader> = {
  cw: () => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const mod = require("./cw/cw-products") as typeof import("./cw/cw-products");
    return mod.cwProducts;
  },
  gg: () => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const mod = require("./gg/gg-catalog") as typeof import("./gg/gg-catalog");
    return mod.ggCatalogProducts;
  },
  bb: () => {
    return readCatalogJson("bb/bb-catalog.json");
  },
  ax: () => {
    /* eslint-disable @typescript-eslint/no-require-imports */
    const shoes = require("./ax/ax-catalog") as typeof import("./ax/ax-catalog");
    const apparel =
      require("./ax/ax-apparel-catalog") as typeof import("./ax/ax-apparel-catalog");
    const outlet =
      require("./ax/ax-outlet-catalog") as typeof import("./ax/ax-outlet-catalog");
    const gear =
      require("./ax/ax-gear-catalog") as typeof import("./ax/ax-gear-catalog");
    /* eslint-enable @typescript-eslint/no-require-imports */
    return [
      ...shoes.axCatalogProducts,
      ...apparel.axApparelCatalogProducts,
      ...outlet.axOutletCatalogProducts,
      ...gear.axGearCatalogProducts,
    ];
  },
  lu: () => {
    /* eslint-disable @typescript-eslint/no-require-imports */
    const umbrellas =
      require("./lu/lu-catalog") as typeof import("./lu/lu-catalog");
    const lifestyle =
      require("./lu/lu-lifestyle-catalog") as typeof import("./lu/lu-lifestyle-catalog");
    /* eslint-enable @typescript-eslint/no-require-imports */
    return [
      ...umbrellas.luCatalogProducts,
      ...lifestyle.luLifestyleCatalogProducts,
    ];
  },
  ps: () => {
    return readCatalogJson("ps/ps-catalog.json");
  },
  bs: () => {
    return readCatalogJson("bs/bs-catalog.json");
  },
  gc: () => {
    return readCatalogJson("gc/gc-catalog.json");
  },
  bv: () => {
    return readCatalogJson("bv/bv-catalog.json");
  },
  ch: () => {
    return readCatalogJson("ch/ch-catalog.json");
  },
  ce: () => {
    return readCatalogJson("ce/ce-catalog.json");
  },
  vw: () => {
    return readCatalogJson("vw/vw-catalog.json");
  },
  al: () => {
    return readCatalogJson("al/al-catalog.json");
  },
  pr: () => {
    return readCatalogJson("pr/pr-catalog.json");
  },
  lv: () => {
    return readCatalogJson("lv/lv-catalog.json");
  },
  di: () => {
    return readCatalogJson("di/di-catalog.json");
  },
  mb: () => {
    return readCatalogJson("mb/mb-catalog.json");
  },
};

export function loadBrandCatalog(key: BrandCatalogKey): Product[] {
  return cached(cache, key, LOADERS[key]);
}

/** Bags-only loaders — keep bags brand clicks ~same TTFB regardless of RTW/acc size. */
const BAGS_LOADERS: Partial<Record<BrandCatalogKey, Loader>> = {
  bb: () => {
    return readCatalogJson("bb/bb-bags-catalog.json");
  },
  ax: () => {
    return readCatalogJson("ax/ax-bags-catalog.json");
  },
  gc: () => {
    return readCatalogJson("gc/gc-bags-catalog.json");
  },
  bv: () => {
    return readCatalogJson("bv/bv-bags-catalog.json");
  },
  ch: () => {
    return readCatalogJson("ch/ch-bags-catalog.json");
  },
  al: () => {
    return readCatalogJson("al/al-bags-catalog.json");
  },
  ce: () => {
    return readCatalogJson("ce/ce-bags-catalog.json");
  },
  vw: () => {
    return readCatalogJson("vw/vw-bags-catalog.json");
  },
  pr: () => {
    return readCatalogJson("pr/pr-bags-catalog.json");
  },
  di: () => {
    return readCatalogJson("di/di-bags-catalog.json");
  },
  mb: () => {
    return readCatalogJson("mb/mb-bags-catalog.json");
  },
};

export function loadBrandBagsCatalog(key: BrandCatalogKey): Product[] {
  const loader = BAGS_LOADERS[key];
  if (!loader) return [];
  return cached(bagsCache, key, loader);
}

export function loadAllBagsCatalogs(): Product[] {
  if (!allBagsCache) {
    const out: Product[] = [];
    for (const key of BAGS_BRAND_KEYS) {
      out.push(...loadBrandBagsCatalog(key));
    }
    allBagsCache = out;
  }
  return allBagsCache;
}

/** Shoes-only loaders — keep shoes brand clicks ~same TTFB regardless of RTW/bags size. */
const SHOES_LOADERS: Partial<Record<BrandCatalogKey, Loader>> = {
  bb: () => {
    return readCatalogJson("bb/bb-shoes-catalog.json");
  },
  ax: () => {
    return readCatalogJson("ax/ax-shoes-catalog.json");
  },
  ps: () => {
    return readCatalogJson("ps/ps-shoes-catalog.json");
  },
  bs: () => {
    return readCatalogJson("bs/bs-shoes-catalog.json");
  },
  gc: () => {
    return readCatalogJson("gc/gc-shoes-catalog.json");
  },
  bv: () => {
    return readCatalogJson("bv/bv-shoes-catalog.json");
  },
  ch: () => {
    return readCatalogJson("ch/ch-shoes-catalog.json");
  },
  al: () => {
    return readCatalogJson("al/al-shoes-catalog.json");
  },
  ce: () => {
    return readCatalogJson("ce/ce-shoes-catalog.json");
  },
  vw: () => {
    return readCatalogJson("vw/vw-shoes-catalog.json");
  },
  pr: () => {
    return readCatalogJson("pr/pr-shoes-catalog.json");
  },
  di: () => {
    return readCatalogJson("di/di-shoes-catalog.json");
  },
};

export function loadBrandShoesCatalog(key: BrandCatalogKey): Product[] {
  const loader = SHOES_LOADERS[key];
  if (!loader) return [];
  return cached(shoesCache, key, loader);
}

export function loadAllShoesCatalogs(): Product[] {
  if (!allShoesCache) {
    const out: Product[] = [];
    for (const key of SHOES_BRAND_KEYS) {
      out.push(...loadBrandShoesCatalog(key));
    }
    allShoesCache = out;
  }
  return allShoesCache;
}

/** Core multi-brand catalogue (excludes Saint Laurent — still YS-lazy). */
export function loadAllBrandCatalogs(): Product[] {
  if (!allCache) {
    const out: Product[] = [];
    for (const key of ALL_KEYS) {
      out.push(...loadBrandCatalog(key));
    }
    allCache = out;
  }
  return allCache;
}

/** Map a nav / collection id to a brand catalogue key. */
export function brandCatalogKeyFromNavId(
  id: string,
): BrandCatalogKey | null {
  const x = id.toLowerCase();
  if (x.startsWith("cw-") || x === "christopher-ward") return "cw";
  if (x.startsWith("gg-") || x === "galvin-green" || x === "golf") return "gg";
  if (x.startsWith("bb-") || x.startsWith("burberry")) return "bb";
  if (
    x.startsWith("ax-") ||
    x.startsWith("axa-") ||
    x.startsWith("axg-") ||
    x.startsWith("axo-") ||
    x.includes("arcteryx")
  ) {
    return "ax";
  }
  if (
    x.startsWith("lu-") ||
    x === "london-undercover" ||
    x === "umbrellas"
  ) {
    return "lu";
  }
  if (x.startsWith("ps-") || x.includes("paul-smith")) return "ps";
  if (x.startsWith("bs-") || x.includes("belstaff")) return "bs";
  if (x.startsWith("gc-") || x.includes("gucci")) return "gc";
  if (x.startsWith("bv-") || x.includes("bottega")) return "bv";
  if (x.startsWith("ch-") || x.includes("chanel")) return "ch";
  if (x.startsWith("ce-") || x.includes("celine")) return "ce";
  if (
    x.startsWith("vw-") ||
    x.includes("vivienne") ||
    x.includes("westwood")
  ) {
    return "vw";
  }
  // AllSaints nav ids are `all-saints` / `all-saints-*`; leaf ids use `al-`.
  // Missing this falls through to "all" and parses every brand JSON on click.
  if (
    x === "all-saints" ||
    x.startsWith("all-saints") ||
    x.startsWith("al-")
  ) {
    return "al";
  }
  if (x.startsWith("pr-") || x.includes("prada")) return "pr";
  if (x.startsWith("lv-") || x.includes("louis-vuitton")) return "lv";
  if (x.startsWith("di-") || x.includes("dior")) return "di";
  if (x.startsWith("mb-") || x.includes("mulberry")) return "mb";
  return null;
}

export function brandCatalogKeyFromProductId(
  id: string,
): BrandCatalogKey | "ys" | null {
  const x = id.toLowerCase();
  if (x.startsWith("ys-")) return "ys";
  if (x.startsWith("cw-")) return "cw";
  if (x.startsWith("gg-")) return "gg";
  if (x.startsWith("bb-")) return "bb";
  if (
    x.startsWith("ax-") ||
    x.startsWith("axa-") ||
    x.startsWith("axg-") ||
    x.startsWith("axo-")
  ) {
    return "ax";
  }
  if (x.startsWith("lu-")) return "lu";
  if (x.startsWith("ps-")) return "ps";
  if (x.startsWith("bs-")) return "bs";
  if (x.startsWith("gc-")) return "gc";
  if (x.startsWith("bv-")) return "bv";
  if (x.startsWith("ch-")) return "ch";
  if (x.startsWith("ce-")) return "ce";
  if (x.startsWith("vw-")) return "vw";
  if (x.startsWith("al-")) return "al";
  if (x.startsWith("pr-")) return "pr";
  if (x.startsWith("lv-")) return "lv";
  if (x.startsWith("di-")) return "di";
  if (x.startsWith("mb-")) return "mb";
  return null;
}

/**
 * Which core brand catalogues a shop filter needs.
 * - no `sub`: all brands (category / 전체 PLP), except narrow categories
 * - YS-only sub: empty (caller merges YS lazily)
 * - brand / leaf sub: only matching brand(s)
 */
export function resolveBrandCatalogKeys(
  category?: string,
  sub?: string,
): BrandCatalogKey[] | "all" {
  if (!sub) {
    // Watches category is Christopher Ward only — do not parse luxury JSON.
    if (category === "watches") return ["cw"];
    // Bags hub — only brands with bag SKUs (bags slices), not every RTW catalogue.
    if (category === "bags") return [...BAGS_BRAND_KEYS];
    // Shoes hub — only brands with shoe SKUs (shoes slices), not every RTW catalogue.
    if (category === "shoes") return [...SHOES_BRAND_KEYS];
    return "all";
  }
  if (isYsShopSub(sub)) return [];

  const expanded = expandSubcategoryFilter(sub) ?? [sub];
  const keys = new Set<BrandCatalogKey>();
  for (const id of [sub, ...expanded]) {
    const key = brandCatalogKeyFromNavId(id);
    if (key) keys.add(key);
  }
  if (keys.size === 0) return "all";
  return [...keys];
}

export function loadCatalogsForShop(
  category?: string,
  sub?: string,
): Product[] {
  const keys = resolveBrandCatalogKeys(category, sub);
  const bagsOnly = category === "bags";
  const shoesOnly = category === "shoes";

  if (keys === "all") {
    if (bagsOnly) return loadAllBagsCatalogs();
    if (shoesOnly) return loadAllShoesCatalogs();
    return loadAllBrandCatalogs();
  }
  if (keys.length === 0) return [];

  if (bagsOnly) {
    const out: Product[] = [];
    for (const key of keys) {
      // Prefer bags slice; empty when brand has no bags file.
      out.push(...loadBrandBagsCatalog(key));
    }
    return out;
  }

  if (shoesOnly) {
    const out: Product[] = [];
    for (const key of keys) {
      // Prefer shoes slice; empty when brand has no shoes file.
      out.push(...loadBrandShoesCatalog(key));
    }
    return out;
  }

  if (keys.length === 1) return loadBrandCatalog(keys[0]);
  const out: Product[] = [];
  for (const key of keys) {
    out.push(...loadBrandCatalog(key));
  }
  return out;
}
