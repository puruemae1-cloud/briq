import type {
  AnalysisResult,
  MotionSample,
  SwingMetrics,
  SwingPhase,
  SwingView,
  ViewCapture,
} from "./types";
import { METRIC_LABEL, SWING_PHASES } from "./types";
import { getPro } from "./pros";
import {
  blendMetrics,
  clamp,
  overallScore,
  peakTime,
  primaryFocus,
  rankedGaps,
} from "./metrics";
import { gapCopy, phaseNote } from "./copy";
import { AMATEUR_STYLE, FINE_PHASES, TOUR_STYLE } from "./anatomy";
import { buildPose, comparePoses } from "./pose";
import { detectSwingSync, modelSyncFromUser } from "./swing-sync";

function peakIndex(samples: MotionSample[]) {
  let max = -1;
  let idx = Math.floor(samples.length / 2);
  samples.forEach((s, i) => {
    if (s.energy > max) {
      max = s.energy;
      idx = i;
    }
  });
  return idx;
}

function splitTempo(samples: MotionSample[]) {
  if (samples.length < 6) return { back: 1, down: 1, ratio: 1 };
  const peak = peakIndex(samples);
  const back = Math.max(samples[peak]?.t ?? 1, 0.15);
  const last = samples[samples.length - 1]?.t ?? back + 0.4;
  const down = Math.max(last - back, 0.08);
  return { back, down, ratio: back / down };
}

function sway(samples: MotionSample[]) {
  if (!samples.length) return 0;
  const xs = samples.map((s) => s.cx);
  return Math.max(...xs) - Math.min(...xs);
}

function heightCollapse(samples: MotionSample[]) {
  if (samples.length < 4) return 0;
  const start = samples.slice(0, 3).reduce((a, s) => a + s.height, 0) / 3;
  const mid = samples.slice(
    Math.floor(samples.length * 0.45),
    Math.floor(samples.length * 0.7),
  );
  const m = mid.reduce((a, s) => a + s.height, 0) / Math.max(mid.length, 1);
  return Math.max(0, start - m);
}

function widthAtTop(samples: MotionSample[]) {
  if (!samples.length) return 0.3;
  const i = Math.max(0, peakIndex(samples) - 2);
  return samples[i]?.width ?? 0.3;
}

/** Scores taken from the clip itself so two real videos can be compared. */
export function metricsFromMotion(
  views: ViewCapture[],
  hint?: SwingMetrics,
): SwingMetrics {
  const all = views.flatMap((v) => v.samples);
  const tempo = splitTempo(all);
  const tempoScore = clamp(100 - Math.abs(tempo.ratio - 3) * 18);
  const head = clamp(100 - sway(all) * 220);
  const posture = clamp(100 - heightCollapse(all) * 280);
  const energyPeak = peakIndex(all);
  const lateEnergy =
    energyPeak > all.length * 0.55 ? 8 : energyPeak < all.length * 0.35 ? -10 : 0;
  const turnProxy = clamp(widthAtTop(all) * 280);

  const derived: SwingMetrics = {
    shoulderTurn: turnProxy,
    hipTurn: clamp(turnProxy * 0.55 + (hint?.hipTurn ?? 45) * 0.2),
    xFactor: clamp(turnProxy * 0.35 + head * 0.15),
    spineTilt: clamp(posture * 0.9),
    headStability: head,
    weightShift: clamp(100 - sway(all) * 160),
    clubPath: clamp(78 + lateEnergy - sway(all) * 40),
    lag: clamp(70 + (tempo.ratio - 1.5) * 8),
    posture,
    tempo: tempoScore,
  };

  return hint ? blendMetrics(hint, derived) : derived;
}

function sampleAt(samples: MotionSample[], tNorm: number) {
  if (!samples.length) return undefined;
  const idx = Math.min(
    samples.length - 1,
    Math.round(tNorm * (samples.length - 1)),
  );
  return samples[idx];
}

function phaseHints(views: ViewCapture[]): Record<SwingPhase, string> {
  const all = views.flatMap((v) => v.samples);
  const t = splitTempo(all);
  const s = sway(all);
  const c = heightCollapse(all);
  return {
    address: s < 0.08 ? "Your address axis is fairly quiet." : "There is sway already at address.",
    takeaway: "Check the face-on clip: club, hands and chest should leave as one piece.",
    top:
      t.ratio < 2
        ? "You spend almost no time at the top — the change of direction is rushed."
        : "You have time to the top.",
    transition:
      t.ratio < 2.4
        ? "The downswing is quick. Start the lower body first."
        : "Transition tempo is closer to the model.",
    impact:
      c > 0.08
        ? "You lose height into impact — early extension is likely."
        : "Height into impact is holding up.",
    finish:
      s > 0.14
        ? "The axis collapses in the finish. Hold it for three seconds."
        : "Finish balance looks reasonable.",
  };
}

export function analyzePair(opts: {
  userViews: ViewCapture[];
  tourViews?: ViewCapture[];
  proId: string;
  handedness: "right" | "left";
  trialLimited: boolean;
}): AnalysisResult {
  const pro = getPro(opts.proId);
  if (!pro) throw new Error("Player model not found.");

  const comparedAgainstClip = Boolean(opts.tourViews?.length);
  const userMetrics = metricsFromMotion(opts.userViews);
  const proMetrics = comparedAgainstClip
    ? metricsFromMotion(opts.tourViews!)
    : pro.metrics;

  const overall = overallScore(userMetrics, proMetrics);
  const ranked = rankedGaps(userMetrics, proMetrics);
  const hints = phaseHints(opts.userViews);
  const views = opts.userViews.map((v) => v.view) as SwingView[];
  const has3d = views.includes("faceOn") && views.includes("downTheLine");
  const userAll = opts.userViews.flatMap((v) => v.samples);
  const tourAll = opts.tourViews?.flatMap((v) => v.samples) ?? [];

  const allGaps = ranked.map(({ key, delta }) => {
    const copy = gapCopy(key, userMetrics[key], proMetrics[key]);
    const abs = Math.abs(delta);
    return {
      key,
      label: METRIC_LABEL[key],
      user: Math.round(userMetrics[key]),
      pro: Math.round(proMetrics[key]),
      delta: Math.round(delta),
      severity: (abs < 8 ? "ok" : abs < 16 ? "watch" : "fix") as
        | "ok"
        | "watch"
        | "fix",
      summary: comparedAgainstClip
        ? copy.summary.replace("the model", "their clip")
        : copy.summary,
      drill: copy.drill,
      feel: copy.feel,
    };
  });

  const gaps = opts.trialLimited ? allGaps.slice(0, 3) : allGaps;
  const phaseNotes = SWING_PHASES.map((phase) => ({
    phase,
    note: phaseNote(pro, phase, hints[phase]),
  }));

  const userFace = opts.userViews.find((v) => v.view === "faceOn");
  const userSamples = userFace?.samples ?? userAll;
  const userDur = userFace?.duration ?? userSamples[userSamples.length - 1]?.t ?? 2;
  const userSync = detectSwingSync(userSamples, userDur);

  const tourFace = opts.tourViews?.find((v) => v.view === "faceOn");
  const tourSamples = tourFace?.samples ?? tourAll;
  const tourDur = tourFace?.duration ?? tourSamples[tourSamples.length - 1]?.t ?? userDur;
  const tourSync = tourFace
    ? (() => {
        const detected = detectSwingSync(tourSamples, tourDur);
        return {
          ...detected,
          addressT: detected.addressT ?? 0,
          endT: Math.max(detected.endT, tourDur * 0.995),
        };
      })()
    : modelSyncFromUser(userSync);

  const allFine = FINE_PHASES.map((phase) => {
    const userPose = buildPose({
      style: AMATEUR_STYLE,
      phaseT: phase.t,
      handedness: opts.handedness,
      motion: sampleAt(userAll, phase.t),
    });
    const proPose = buildPose({
      style: comparedAgainstClip ? AMATEUR_STYLE : (pro.style ?? TOUR_STYLE),
      phaseT: phase.t,
      handedness: opts.handedness,
      motion: comparedAgainstClip ? sampleAt(tourAll, phase.t) : undefined,
    });
    const top = comparePoses(userPose, proPose).slice(0, 3);
    return {
      n: phase.n,
      code: phase.code,
      label: phase.label,
      cue: phase.cue,
      note: `${phase.cue} Biggest gaps: ${top.map((d) => d.label).join(", ")}.`,
    };
  });

  return {
    id: `sw_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
    createdAt: new Date().toISOString(),
    proId: pro.id,
    proName: comparedAgainstClip ? `${pro.name} (your clip)` : pro.name,
    comparedAgainstClip,
    handedness: opts.handedness,
    views,
    has3d,
    overall,
    gaps,
    phaseNotes: opts.trialLimited ? phaseNotes.slice(0, 2) : phaseNotes,
    finePhaseNotes: opts.trialLimited ? allFine.slice(0, 3) : allFine,
    userMetrics,
    proMetrics,
    trialLimited: opts.trialLimited,
    coachingFocus: primaryFocus(userMetrics, proMetrics),
    userPeakT: peakTime(userAll),
    tourPeakT: peakTime(tourAll),
    userSync,
    tourSync,
  };
}
