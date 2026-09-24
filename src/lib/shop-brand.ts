import { findCategory, findNavPath } from "@/data/categories";
import {
  brandHeroes,
  brandRootToKey,
  type BrandHeroDef,
  type BrandKey,
} from "@/data/brand-heroes";

const PREFIX_RULES: { re: RegExp; key: BrandKey }[] = [
  { re: /^(gc-|gucci)/i, key: "gucci" },
  { re: /^(bv-|bottega)/i, key: "bottega-veneta" },
  { re: /^(ce-|celine)/i, key: "celine" },
  { re: /^(ys-|saint-laurent|ysl)/i, key: "saint-laurent" },
  { re: /^(vw-|vivienne)/i, key: "vivienne-westwood" },
  { re: /^(bb-|burberry)/i, key: "burberry" },
  { re: /^(ch-watches|chanel-watches)/i, key: "chanel-watches" },
  { re: /^(ch-|chanel)/i, key: "chanel" },
  { re: /^(pr-|prada)/i, key: "prada" },
  { re: /^(arcteryx-shoes|ax-shoes)/i, key: "arcteryx-shoes" },
  { re: /^(ax-|axa-|arcteryx)/i, key: "arcteryx" },
  { re: /^(paul-smith-shoes|ps-shoes)/i, key: "paul-smith-shoes" },
  { re: /^(ps-|paul-smith)/i, key: "paul-smith" },
  { re: /^(belstaff-shoes|bs-shoes)/i, key: "belstaff-shoes" },
  { re: /^(bs-|belstaff)/i, key: "belstaff" },
  { re: /^(gg-|galvin)/i, key: "galvin-green" },
  { re: /^(cw-|christopher-ward)/i, key: "christopher-ward" },
  { re: /^(lv-|louis-vuitton)/i, key: "louis-vuitton" },
  { re: /^(di-|dior)/i, key: "dior" },
  { re: /^(mb-|mulberry)/i, key: "mulberry" },
  {
    re: /^(all-saints-accessori|al-(men|women)-(accessori|acc-|sunglass|belt|hat|jewell|wallet|scarf))/i,
    key: "all-saints-accessories",
  },
  {
    re: /^(all-saints-bags|al-(men|women)-(bags|handbags|bags-group))/i,
    key: "all-saints-bags",
  },
  {
    re: /^(all-saints-shoes|al-(men|women)-(shoes|boots|flats|heels|trainers|casual-shoes))/i,
    key: "all-saints-shoes",
  },
  { re: /^(all-saints|al-(men|women))/i, key: "all-saints" },
  { re: /^(lu-|london-undercover|umbrellas)/i, key: "london-undercover" },
];

/**
 * When a shop brand (or nested collection under that brand) is selected,
 * return the brand hero definition for the category strip banner + logo.
 */
export function resolveShopBrand(
  category?: string,
  sub?: string,
): BrandHeroDef | null {
  if (!category || category === "all" || !sub) return null;

  const cat = findCategory(category);
  const path = findNavPath(cat?.children, sub);
  if (path?.length) {
    let found: BrandHeroDef | null = null;
    for (const node of path) {
      const key = brandRootToKey[node.id];
      if (key) found = brandHeroes[key];
    }
    if (found) return found;
  }

  const direct = brandRootToKey[sub];
  if (direct) return brandHeroes[direct];

  for (const rule of PREFIX_RULES) {
    if (rule.re.test(sub)) return brandHeroes[rule.key];
  }

  return null;
}
