/**
 * Clothing numbers where a longer run of zeros is the smaller size.
 * Moncler: 000 < 00 < 0 < 1. Number("00") === Number("0"), so a plain
 * numeric compare puts 0 to the left of 00.
 */
export function apparelSizeRank(raw) {
  const s = String(raw ?? "").trim();
  if (/^0+$/.test(s)) return -s.length;
  const n = Number(s);
  return Number.isFinite(n) ? n : 9999;
}

export function assertMonclerNumericSizeOrder() {
  const order = ["000", "00", "0", "1", "2", "3", "4", "5", "6", "7"];
  for (let i = 1; i < order.length; i++) {
    const prev = apparelSizeRank(order[i - 1]);
    const next = apparelSizeRank(order[i]);
    if (prev >= next) {
      throw new Error(
        `Moncler clothing sizes must run ${order.join(" < ")}, but ${order[i - 1]} ranked ${prev} and ${order[i]} ranked ${next}`,
      );
    }
  }
}
