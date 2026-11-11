import type { Product } from "@/data/product-types";
import { isProductInStock } from "@/data/product-utils";
import { homeLookBanners } from "@/data/home-banners";
import {
  getCollection100,
  getHomepageCategoryProducts,
  toProductCardProduct,
} from "@/data/products";
import { curateCollectionEdit } from "@/lib/collection-edit";
import {
  assignHomepageCategoryRails,
  seoulRotationDay,
} from "@/lib/homepage-rails";

/**
 * Builds the homepage product cards from the full brand catalogues.
 *
 * Heavy (parses hundreds of MB). Only `app/api/home-data/route.ts` and the
 * dynamic-import fallback in `homepage-feed.ts` may import this module — a
 * static import from the page/layout bundles every catalogue into the `/`
 * chunk and makes each cold boot ~9s.
 */
export type HomepageData = {
  rails: Record<string, Product[]>;
  /** Top winter Flannels clearance picks under the Flannels interstitial. */
  flannels: Product[];
  signature: Product[];
  newItems: Product[];
  /** Deployment that built these cards (set by `/api/home-data`). */
  deployKey?: string;
};

/** Homepage Flannels rail size — highest-discount winter layers. */
export const FLANNELS_HOME_LIMIT = 20;


function discountRatio(p: Product): number {
  const price = p.price ?? 0;
  const compare = p.compareAtPrice ?? 0;
  if (!compare || compare <= price || price <= 0) return 0;
  return (compare - price) / compare;
}

/** Party / formal / swim — keep these off the Flannels homepage rail. */
const FLANNELS_HOME_EXCLUDE =
  /dress|gown|sequin|party|evening|bridal|corset|bodysuit|bikini|swimsuit|heel|sandal|skirt|blouse|camisole|slip|tulle|cocktail|shirt[-\s]*dress|suit[-\s]*jacket|waistcoat|tuxedo|tailored|double[-\s]*breasted|single[-\s]*breasted|biker[-\s]*short|shorts?\b|bandeau|jumper[-\s]*dress|드레스|스팽글|파티|가운|비키니|샌들|힐|스커트|블라우스|바디수트|수트|정장|양복|쇼트/i;

/** Casual winter-friendly pieces (layers + everyday denim/cargo). */
const FLANNELS_HOME_CASUAL =
  /\bcoats?\b|parka|puffer|down|quilt|padded|bomber|varsity|denim[-\s]*jacket|leather[-\s]*jacket|hoodie|fleece|sweat(?:shirt)?|jumper|cardigan|sweater|knit(?:ted)?|wool|cashmere|shearling|gilet|anorak|overcoat|trench|jeans?\b|denim|jogger|cargo|boots?\b|코트|패딩|점퍼|봄버|후드|플리스|스웨터|니트|가디건|진|청바지|조거|카고|부츠|재킷|자켓|질레|파카|퍼퍼/i;

/** Prefer thick layers in the first slots (not bottoms-only). */
const FLANNELS_HOME_LAYER =
  /\bcoats?\b|parka|puffer|down|quilt|padded|bomber|varsity|denim[-\s]*jacket|leather[-\s]*jacket|hoodie|fleece|sweatshirt|jumper(?![-\s]*dress)|cardigan|sweater|shearling|gilet|anorak|overcoat|trench|코트|패딩|점퍼|봄버|후드|플리스|스웨터|니트|가디건|재킷|자켓|질레|파카|퍼퍼/i;

const FLANNELS_HOME_HEAVY =
  /parka|puffer|padded|down|quilt|fleece|shearling|insulated|heavyweight|파카|퍼퍼|패딩|플리스|헤비/i;

const FLANNELS_GENERIC_TAGS = new Set([
  "flannels",
  "fl-women",
  "fl-men",
  "women",
  "men",
  "sale",
  "clothing",
  "shoes",
  "sandals",
  "accessories",
  "bags",
]);

function flannelsText(p: Product): string {
  const tags = Array.isArray(p.tags) ? p.tags.join(" ") : "";
  return `${p.id || ""} ${p.name || ""} ${p.nameKo || ""} ${tags}`;
}

function flannelsGender(p: Product): "w" | "m" | "?" {
  const tags = Array.isArray(p.tags) ? p.tags : [];
  if (tags.includes("fl-women") || tags.includes("women")) return "w";
  if (tags.includes("fl-men") || tags.includes("men")) return "m";
  const t = flannelsText(p).toLowerCase();
  if (t.includes("womens") || t.includes("women") || t.includes("여성")) return "w";
  if (t.includes("mens") || t.includes("남성") || /\bmen\b/.test(t)) return "m";
  return "?";
}

function flannelsBrandKey(p: Product): string {
  const tags = Array.isArray(p.tags)
    ? p.tags.filter((t) => !FLANNELS_GENERIC_TAGS.has(t) && !t.startsWith("fl-"))
    : [];
  if (tags[0]) return tags[0];
  const m = /^(?:fl)-(.+?)-(?:womens?|mens?)-/i.exec(p.id || "");
  return m?.[1] || (p.id || "").split("-")[1] || p.id || "";
}

function flannelsBaseId(id: string): string {
  return id.replace(/-\d{6,}$/, "");
}

function flannelsHomeScore(p: Product): number {
  // Discount leads; winter layer / heavy outerwear only as a light tie-break
  // so 95% jeans do not outrank a 90% parka when both are winter-eligible.
  const t = flannelsText(p);
  let s = discountRatio(p);
  if (FLANNELS_HOME_LAYER.test(t)) s += 0.02;
  if (FLANNELS_HOME_HEAVY.test(t)) s += 0.02;
  return s;
}

/**
 * Diversified Flannels pick from a discount-sorted pool.
 * Brand cap 2, gender soft-cap ~half the rail, layers preferred first.
 */
function pickFlannelsDiverse(pool: Product[], limit: number): Product[] {
  const picked: Product[] = [];
  const seenBase = new Set<string>();
  const brandCount = new Map<string, number>();
  const genderCount: Record<string, number> = { w: 0, m: 0, "?": 0 };
  const brandCap = 2;
  const genderCap = Math.max(2, Math.ceil(limit / 2));

  const tryPick = (requireLayer: boolean) => {
    for (const p of pool) {
      if (picked.length >= limit) break;
      const t = flannelsText(p);
      if (requireLayer && !FLANNELS_HOME_LAYER.test(t)) continue;
      const base = flannelsBaseId(p.id);
      if (seenBase.has(base)) continue;
      const brand = flannelsBrandKey(p);
      if ((brandCount.get(brand) || 0) >= brandCap) continue;
      const g = flannelsGender(p);
      if ((g === "w" || g === "m") && (genderCount[g] || 0) >= genderCap) continue;
      picked.push(p);
      seenBase.add(base);
      brandCount.set(brand, (brandCount.get(brand) || 0) + 1);
      genderCount[g] = (genderCount[g] || 0) + 1;
    }
  };

  tryPick(true);
  tryPick(false);
  return picked;
}

/**
 * In-stock Flannels homepage rail: winter layers sorted by discount (high→low).
 * Party / formal / swimwear stay excluded. Default size is 20.
 */
function getFlannelsHomepageProducts(
  limit = FLANNELS_HOME_LIMIT,
): Product[] {
  const scored = getHomepageCategoryProducts("luxury", "flannels").filter(
    (p) => {
      if (!isProductInStock(p)) return false;
      const t = flannelsText(p);
      if (FLANNELS_HOME_EXCLUDE.test(t)) return false;
      return FLANNELS_HOME_CASUAL.test(t);
    },
  );
  scored.sort((a, b) => {
    const d = flannelsHomeScore(b) - flannelsHomeScore(a);
    if (d !== 0) return d;
    const layer =
      Number(FLANNELS_HOME_LAYER.test(flannelsText(b))) -
      Number(FLANNELS_HOME_LAYER.test(flannelsText(a)));
    if (layer !== 0) return layer;
    const tb = Date.parse(b.registeredAt || b.updatedAt || "") || 0;
    const ta = Date.parse(a.registeredAt || a.updatedAt || "") || 0;
    return tb - ta;
  });

  return pickFlannelsDiverse(scored, limit).map(toProductCardProduct);
}

let memo: { rotationDay: string; data: HomepageData } | null = null;

export function buildHomepageData(): HomepageData {
  const rotationDay = seoulRotationDay();
  if (memo?.rotationDay === rotationDay) return memo.data;

  // Skip YS merge here — homepage soft-nav was waiting on the 14MB catalogue.
  const categoryRails = homeLookBanners
    .filter((b) => b.categoryId)
    .map((b) => ({
      railId: b.id,
      products: getHomepageCategoryProducts(b.categoryId),
    }));
  const rails = assignHomepageCategoryRails(categoryRails, 4);
  const curated = curateCollectionEdit(getCollection100());

  const data: HomepageData = {
    rails: Object.fromEntries(
      Object.entries(rails).map(([id, list]) => [id, list.map(toProductCardProduct)]),
    ),
    flannels: getFlannelsHomepageProducts(FLANNELS_HOME_LIMIT),
    signature: curated.signature.map(toProductCardProduct),
    newItems: curated.newItems.map(toProductCardProduct),
  };
  memo = { rotationDay, data };
  return data;
}
