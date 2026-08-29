import { findCategory, findNavPath } from "@/data/categories";
import {
  brandHeroes,
  brandRootToKey,
  type BrandHeroDef,
  type BrandKey,
} from "@/data/brand-heroes";

const PREFIX_RULES: { re: RegExp; key: BrandKey }[] = [
  { re: /^(gc-|gucci)/i, key: "gucci" },
  { re: /^(bb-|burberry)/i, key: "burberry" },
  { re: /^(ch-watches|chanel-watches)/i, key: "chanel-watches" },
  { re: /^(ch-|chanel)/i, key: "chanel" },
  { re: /^(pr-|prada)/i, key: "prada" },
  { re: /^(ax-|axa-|arcteryx)/i, key: "arcteryx" },
  { re: /^(ps-|paul-smith)/i, key: "paul-smith" },
  { re: /^(bs-|belstaff)/i, key: "belstaff" },
  { re: /^(gg-|galvin)/i, key: "galvin-green" },
  { re: /^(cw-|christopher-ward)/i, key: "christopher-ward" },
  { re: /^(lv-|louis-vuitton)/i, key: "louis-vuitton" },
  { re: /^(di-|dior)/i, key: "dior" },
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
    for (const node of path) {
      const key = brandRootToKey[node.id];
      if (key) return brandHeroes[key];
    }
  }

  const direct = brandRootToKey[sub];
  if (direct) return brandHeroes[direct];

  for (const rule of PREFIX_RULES) {
    if (rule.re.test(sub)) return brandHeroes[rule.key];
  }

  return null;
}
