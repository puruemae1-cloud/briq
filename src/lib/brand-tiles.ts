/**
 * Brand-symbolic tile photos for chip / SEO brand grids.
 * Assets live under /public/brands/tiles (ships with the app, not CDN tag).
 */

import { navBrandFamily } from "@/lib/brand-nav-order";

const FAMILY_TILE: Record<string, string> = {
  "christopher-ward": "/brands/tiles/christopher-ward.jpg",
  chanel: "/brands/tiles/chanel.jpg",
  gucci: "/brands/tiles/gucci.jpg",
  "louis-vuitton": "/brands/tiles/louis-vuitton.jpg",
  dior: "/brands/tiles/dior.jpg",
  burberry: "/brands/tiles/burberry.jpg",
  "paul-smith": "/brands/tiles/paul-smith.jpg",
  arcteryx: "/brands/tiles/arcteryx.jpg",
  "london-undercover": "/brands/tiles/london-undercover.jpg",
  belstaff: "/brands/tiles/belstaff.jpg",
  "bottega-veneta": "/brands/tiles/bottega-veneta.jpg",
  celine: "/brands/tiles/celine.jpg",
  "saint-laurent": "/brands/tiles/saint-laurent.jpg",
  "vivienne-westwood": "/brands/tiles/vivienne-westwood.jpg",
  mulberry: "/brands/tiles/mulberry.jpg",
  "galvin-green": "/brands/tiles/galvin-green.jpg",
  prada: "/brands/tiles/prada.jpg",
  "all-saints": "/brands/tiles/all-saints.jpg",
};

/** Resolve a nav / subcategory / SEO slug to a brand tile photo. */
export function brandTileSrcForNavId(id: string): string | null {
  const x = (id || "").toLowerCase();
  if (!x) return null;

  if (x === "all-saints" || x.startsWith("all-saints") || x.startsWith("al-")) {
    return FAMILY_TILE["all-saints"];
  }
  if (x === "prada" || x.startsWith("prada-") || x.startsWith("pr-")) {
    return FAMILY_TILE.prada;
  }
  if (
    x === "bottega-veneta" ||
    x.startsWith("bottega-veneta") ||
    x.startsWith("bv-")
  ) {
    return FAMILY_TILE["bottega-veneta"];
  }
  if (x === "celine" || x.startsWith("celine-") || x.startsWith("ce-")) {
    return FAMILY_TILE.celine;
  }
  if (
    x === "saint-laurent" ||
    x.startsWith("saint-laurent") ||
    x.startsWith("ys-")
  ) {
    return FAMILY_TILE["saint-laurent"];
  }
  if (
    x === "vivienne-westwood" ||
    x.startsWith("vivienne-westwood") ||
    x.startsWith("vw-")
  ) {
    return FAMILY_TILE["vivienne-westwood"];
  }
  if (x === "mulberry" || x.startsWith("mulberry-") || x.startsWith("mb-")) {
    return FAMILY_TILE.mulberry;
  }
  if (x === "galvin-green" || x.startsWith("galvin-green") || x.startsWith("gg-")) {
    return FAMILY_TILE["galvin-green"];
  }
  if (
    x === "louis-vuitton" ||
    x.startsWith("louis-vuitton") ||
    x.startsWith("lv-")
  ) {
    return FAMILY_TILE["louis-vuitton"];
  }

  const family = navBrandFamily(id);
  if (!family || family === "_new") return null;
  return FAMILY_TILE[family] ?? null;
}
