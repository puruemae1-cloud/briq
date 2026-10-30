/**
 * Arc'teryx size ordering — match official site:
 * inseam Short → Regular → Tall, then numeric ascending (00 before 0).
 */

const LETTER_ORDER: Record<string, number> = {
  XXS: 0,
  XS: 1,
  S: 2,
  M: 3,
  L: 4,
  XL: 5,
  XXL: 6,
  "2XL": 6,
  XXXL: 7,
  "3XL": 7,
  "4XL": 8,
  OS: 9,
  "ONE SIZE": 9,
};

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

  const m = s.match(INSEAM_RE);
  if (m) {
    const waist = m[1];
    const length = m[2].toUpperCase();
    return [0, "SRT".indexOf(length), waistRank(waist), s];
  }

  const letter = LETTER_ORDER[s.toUpperCase()];
  if (letter !== undefined) return [1, letter, 0, s];

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
