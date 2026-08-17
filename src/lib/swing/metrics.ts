import { METRIC_KEYS, METRIC_LABEL_KO, type MetricKey, type SwingMetrics } from "./types";

export function clamp(n: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, n));
}

export function avg(values: number[]) {
  if (!values.length) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

export function emptyMetrics(): SwingMetrics {
  return {
    shoulderTurn: 0,
    hipTurn: 0,
    xFactor: 0,
    spineTilt: 0,
    headStability: 0,
    weightShift: 0,
    clubPath: 0,
    lag: 0,
    posture: 0,
    tempo: 0,
  };
}

export function overallScore(user: SwingMetrics, pro: SwingMetrics) {
  const diffs = METRIC_KEYS.map((k) => Math.abs(user[k] - pro[k]));
  const mean = avg(diffs);
  return Math.round(clamp(100 - mean * 1.15));
}

export function metricSeverity(delta: number): "ok" | "watch" | "fix" {
  const a = Math.abs(delta);
  if (a < 8) return "ok";
  if (a < 16) return "watch";
  return "fix";
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

export { METRIC_LABEL_KO };
