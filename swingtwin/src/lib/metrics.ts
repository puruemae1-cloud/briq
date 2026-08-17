import { METRIC_KEYS, type MetricKey, type SwingMetrics } from "./types";

export function clamp(n: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, n));
}

export function avg(values: number[]) {
  if (!values.length) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

export function overallScore(user: SwingMetrics, pro: SwingMetrics) {
  const diffs = METRIC_KEYS.map((k) => Math.abs(user[k] - pro[k]));
  return Math.round(clamp(100 - avg(diffs) * 1.15));
}

export function rankedGaps(user: SwingMetrics, pro: SwingMetrics) {
  return [...METRIC_KEYS]
    .map((key) => ({
      key,
      delta: user[key] - pro[key],
      abs: Math.abs(user[key] - pro[key]),
    }))
    .sort((a, b) => b.abs - a.abs);
}

export function blendMetrics(
  base: SwingMetrics,
  overlay: Partial<SwingMetrics>,
): SwingMetrics {
  const out = { ...base };
  for (const key of METRIC_KEYS) {
    const v = overlay[key];
    if (typeof v === "number") out[key] = clamp(v);
  }
  return out;
}

export function primaryFocus(user: SwingMetrics, pro: SwingMetrics): MetricKey {
  return rankedGaps(user, pro)[0]?.key ?? "tempo";
}

export function peakTime(
  samples: { t: number; energy: number }[],
): number {
  if (!samples.length) return 0;
  let max = -1;
  let t = samples[Math.floor(samples.length / 2)]?.t ?? 0;
  for (const s of samples) {
    if (s.energy > max) {
      max = s.energy;
      t = s.t;
    }
  }
  return t;
}
