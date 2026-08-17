import type { MotionSample, SkeletonFrame, SwingSyncMarkers } from "./types";

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

/** Detect takeaway (arms up), top, and impact from motion silhouettes. */
export function detectSwingSync(
  samples: MotionSample[],
  duration?: number,
): SwingSyncMarkers {
  const dur =
    duration ??
    samples[samples.length - 1]?.t ??
    (samples.length ? samples.length * 0.05 : 2);

  if (samples.length < 8) {
    return {
      takeawayT: dur * 0.12,
      topT: dur * 0.42,
      impactT: dur * 0.72,
      endT: dur * 0.88,
    };
  }

  const addressN = Math.max(3, Math.floor(samples.length * 0.12));
  const baseW =
    samples.slice(0, addressN).reduce((a, s) => a + s.width, 0) / addressN;
  const baseE =
    samples.slice(0, addressN).reduce((a, s) => a + s.energy, 0) / addressN;

  let takeawayI = addressN;
  for (let i = addressN; i < samples.length; i++) {
    const s = samples[i]!;
    if (s.width > baseW * 1.06 || s.energy > baseE * 1.35) {
      takeawayI = i;
      break;
    }
  }

  const searchEnd = Math.floor(samples.length * 0.62);
  let topI = takeawayI;
  let maxW = samples[takeawayI]?.width ?? 0;
  for (let i = takeawayI; i <= searchEnd; i++) {
    const w = samples[i]!.width;
    if (w >= maxW) {
      maxW = w;
      topI = i;
    }
  }

  let impactI = topI + 1;
  let maxE = -1;
  for (let i = topI + 1; i < samples.length; i++) {
    const e = samples[i]!.energy;
    if (e > maxE) {
      maxE = e;
      impactI = i;
    }
  }
  if (maxE < 0) impactI = Math.floor(samples.length * 0.72);

  const takeawayT = samples[takeawayI]?.t ?? dur * 0.12;
  const topT = Math.max(samples[topI]?.t ?? dur * 0.42, takeawayT + 0.08);
  const impactT = Math.max(samples[impactI]?.t ?? dur * 0.72, topT + 0.08);
  const swingLen = impactT - takeawayT;
  const endT = clamp(impactT + swingLen * 0.12, impactT + 0.05, dur * 0.98);

  return { takeawayT, topT, impactT, endT };
}

/** Rory / tour model timing when no tour clip is uploaded. */
export function modelSyncFromUser(user: SwingSyncMarkers): SwingSyncMarkers {
  const len = Math.max(user.impactT - user.takeawayT, 0.35);
  const topFrac = (0.42 - 0.09) / (0.74 - 0.09);
  const impactFrac = 1;
  return {
    takeawayT: 0,
    topT: len * topFrac,
    impactT: len * impactFrac,
    endT: len * 1.1,
  };
}

/** Map user playback time → tour time (takeaway / top / impact aligned). */
export function mapSyncedTourTime(
  userTime: number,
  user: SwingSyncMarkers,
  tour: SwingSyncMarkers,
): number {
  const u0 = user.takeawayT;
  const u1 = user.topT;
  const u2 = user.impactT;
  const t0 = tour.takeawayT;
  const t1 = tour.topT;
  const t2 = tour.impactT;
  const t = clamp(userTime, u0, user.endT);

  if (t <= u1) {
    const r = (t - u0) / Math.max(u1 - u0, 0.001);
    return t0 + r * (t1 - t0);
  }
  if (t <= u2) {
    const r = (t - u1) / Math.max(u2 - u1, 0.001);
    return t1 + r * (t2 - t1);
  }
  const r = (t - u2) / Math.max(user.endT - u2, 0.001);
  return t2 + r * (tour.endT - t2);
}

/** Fallback when an older saved result has no sync markers. */
export function syncFromSkeleton(frames: SkeletonFrame[]): SwingSyncMarkers | undefined {
  if (frames.length < 4) return undefined;
  const pick = (frac: number) =>
    frames[Math.min(frames.length - 1, Math.round(frac * (frames.length - 1)))]?.t ?? 0;
  const takeawayT = pick(0.12);
  const topT = Math.max(pick(0.42), takeawayT + 0.08);
  const impactT = Math.max(pick(0.74), topT + 0.08);
  const endT = impactT + (impactT - takeawayT) * 0.12;
  return { takeawayT, topT, impactT, endT };
}

export function swingPhaseNorm(
  userTime: number,
  user: SwingSyncMarkers,
): number {
  return clamp(
    (userTime - user.takeawayT) / Math.max(user.impactT - user.takeawayT, 0.001),
    0,
    1.12,
  );
}
