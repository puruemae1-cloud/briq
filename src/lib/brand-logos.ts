/**
 * Brand wordmark assets + display names for shop nav chips
 * (solid black tile + uniform white text).
 * Paths live under /public/brands — not the product-images CDN tag.
 */

import { navBrandFamily } from "@/lib/brand-nav-order";

/** Uniform English wordmark shown on brand chips (same typeface via CSS). */
const FAMILY_DISPLAY: Record<string, string> = {
  "christopher-ward": "Christopher Ward",
  chanel: "Chanel",
  gucci: "Gucci",
  "louis-vuitton": "Louis Vuitton",
  dior: "Dior",
  burberry: "Burberry",
  "paul-smith": "Paul Smith",
  arcteryx: "Arc'teryx",
  "london-undercover": "London Undercover",
  belstaff: "Belstaff",
  "bottega-veneta": "Bottega Veneta",
  celine: "Celine",
  "saint-laurent": "Saint Laurent",
  "vivienne-westwood": "Vivienne Westwood",
  mulberry: "Mulberry",
  "galvin-green": "Galvin Green",
  prada: "Prada",
  "all-saints": "AllSaints",
  hermes: "Hermès",
};

/** Resolve a nav id to the uniform English brand label used on chips. */
export function brandDisplayNameForNavId(id: string): string | null {
  const family = navBrandFamily(id);
  if (family && FAMILY_DISPLAY[family]) return FAMILY_DISPLAY[family];
  const x = id.toLowerCase();
  if (x === "hermes" || x.startsWith("hermes-")) return FAMILY_DISPLAY.hermes;
  return FAMILY_DISPLAY[x] ?? null;
}

const FAMILY_LOGO: Record<string, string> = {
  "christopher-ward": "/brands/christopher-ward.svg",
  chanel: "/brands/chanel.svg",
  gucci: "/brands/gucci.svg",
  "louis-vuitton": "/brands/louis-vuitton.svg",
  dior: "/brands/dior.svg",
  burberry: "/brands/burberry.svg",
  "paul-smith": "/brands/paul-smith.svg",
  arcteryx: "/brands/arcteryx.svg",
  "london-undercover": "/brands/london-undercover.svg",
  belstaff: "/brands/belstaff.svg",
  "bottega-veneta": "/brands/bottega-veneta.svg",
  celine: "/brands/celine.svg",
  "saint-laurent": "/brands/saint-laurent.svg",
  "vivienne-westwood": "/brands/vivienne-westwood.svg",
  mulberry: "/brands/mulberry.svg",
  "galvin-green": "/brands/galvin-green.svg",
  prada: "/brands/prada.svg",
  "all-saints": "/brands/all-saints.svg",
};

/** Resolve a nav / subcategory id to a local brand wordmark, if known. */
export function brandLogoSrcForNavId(id: string): string | null {
  const x = id.toLowerCase();
  if (x === "all-saints" || x.startsWith("all-saints") || x.startsWith("al-")) {
    return FAMILY_LOGO["all-saints"];
  }
  if (x === "prada" || x.startsWith("prada-") || x.startsWith("pr-")) {
    return FAMILY_LOGO.prada;
  }
  if (
    x === "bottega-veneta" ||
    x.startsWith("bottega-veneta") ||
    x.startsWith("bv-")
  ) {
    return FAMILY_LOGO["bottega-veneta"];
  }
  if (x === "celine" || x.startsWith("celine-") || x.startsWith("ce-")) {
    return FAMILY_LOGO.celine;
  }
  if (
    x === "saint-laurent" ||
    x.startsWith("saint-laurent") ||
    x.startsWith("ys-")
  ) {
    return FAMILY_LOGO["saint-laurent"];
  }
  if (
    x === "vivienne-westwood" ||
    x.startsWith("vivienne-westwood") ||
    x.startsWith("vw-")
  ) {
    return FAMILY_LOGO["vivienne-westwood"];
  }
  if (x === "mulberry" || x.startsWith("mulberry-") || x.startsWith("mb-")) {
    return FAMILY_LOGO.mulberry;
  }
  if (x === "galvin-green" || x.startsWith("galvin-green") || x.startsWith("gg-")) {
    return FAMILY_LOGO["galvin-green"];
  }

  const family = navBrandFamily(id);
  if (!family || family === "_new") return null;
  return FAMILY_LOGO[family] ?? null;
}
