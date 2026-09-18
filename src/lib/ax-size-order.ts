/**
 * Size chip ordering — small → large.
 * Handles Arc'teryx inseam (28-S), letter sizes, and compound labels
 * like YSL "XS / GB XS" or "F34 / GB 6".
 */

const LETTER_ORDER: Record<string, number> = {
  XXXS: 0,
  XXS: 1,
  XS: 2,
  S: 3,
  M: 4,
  L: 5,
  XL: 6,
  XXL: 7,
  "2XL": 7,
  XXXL: 8,
  "3XL": 8,
  "4XL": 9,
  "5XL": 10,
  OS: 11,
  "ONE SIZE": 11,
};

const LETTER_RE =
  /\b(XXXS|XXS|XS|S|M|L|XL|XXL|XXXL|2XL|3XL|4XL|5XL|OS|ONE\s*SIZE)\b/i;
const INSEAM_RE = /^(\d+(?:\.\d+)?)\s*[- ]?\s*([SRT])$/i;

function waistRank(raw: string): number {
  const s = raw.trim();
  if (s === "00") return -1;
  const n = Number(s);
  return Number.isFinite(n) ? n : 9999;
}

export function axSizeSortKey(size: string): [number, number, number, string] {
  const s = (size || "").trim();
  if (!s) return [9, 0, 0, ""];

  const inseam = s.match(INSEAM_RE);
  if (inseam) {
    const waist = inseam[1];
    const length = inseam[2].toUpperCase();
    return [0, "SRT".indexOf(length), waistRank(waist), s];
  }

  // Exact letter match (XS, M, …)
  const exact = LETTER_ORDER[s.toUpperCase()];
  if (exact !== undefined) return [1, exact, 0, s];

  // Compound: "XS / GB XS", "YSL S / GB S", "L / GB L"
  const letter = s.match(LETTER_RE);
  if (letter) {
    const tok = letter[1].toUpperCase().replace(/\s+/g, " ");
    const rank = LETTER_ORDER[tok === "ONE SIZE" ? "ONE SIZE" : tok];
    if (rank !== undefined) return [1, rank, 0, s];
  }

  // Fashion numeric: "F34 / GB 6", "IT 40", bare "34"
  const f = s.match(/\bF(\d{2})\b/i);
  if (f) return [2, Number(f[1]), 0, s];
  const gb = s.match(/\bGB\s*(\d{1,2})\b/i);
  if (gb) return [2, Number(gb[1]), 0, s];
  const bare = s.match(/^(\d{2})(?:\.\d+)?$/);
  if (bare) return [2, Number(bare[1]), 0, s];

  const n = Number(s);
  if (Number.isFinite(n)) return [2, n, 0, s];

  return [3, 0, 0, s.toLowerCase()];
}

export function compareAxSizes(a: string, b: string): number {
  const ka = axSizeSortKey(a);
  const kb = axSizeSortKey(b);
  for (let i = 0; i < 3; i++) {
    if (ka[i] !== kb[i]) return (ka[i] as number) - (kb[i] as number);
  }
  return ka[3] < kb[3] ? -1 : ka[3] > kb[3] ? 1 : 0;
}

export function isArcteryxProduct(product: {
  brand?: string;
  tags?: string[];
  id?: string;
}): boolean {
  if (product.brand === "아크테릭스" || product.brand === "Arc'teryx") return true;
  if (product.tags?.some((t) => /arcteryx|아크테릭스/i.test(t))) return true;
  if (product.id && /^(axa|axo|ax)-/i.test(product.id)) return true;
  return false;
}
