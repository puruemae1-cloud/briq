import type {
  AnalysisResult,
  MetricGap,
  MotionSample,
  SwingMetrics,
  SwingPhase,
  SwingView,
  ViewCapture,
} from "./types";
import { METRIC_LABEL_KO, SWING_PHASES } from "./types";
import { getPro } from "./pros";
import { blendMetrics, clamp, overallScore, primaryFocus, rankedGaps } from "./metrics";
import { gapCopy, phaseNote } from "./copy";

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
  const mid = samples.slice(Math.floor(samples.length * 0.45), Math.floor(samples.length * 0.7));
  const m = mid.reduce((a, s) => a + s.height, 0) / Math.max(mid.length, 1);
  return Math.max(0, start - m);
}

function hashFromCapture(views: ViewCapture[]) {
  let h = 0;
  for (const v of views) {
    h += v.duration * 100;
    h += v.samples.reduce((a, s) => a + s.energy * 10 + s.cx * 3, 0);
  }
  return h;
}

function metricsFromViews(views: ViewCapture[], pro: SwingMetrics): SwingMetrics {
  const all = views.flatMap((v) => v.samples);
  const tempo = splitTempo(all.length ? all : views[0]?.samples ?? []);
  const tempoScore = clamp(100 - Math.abs(tempo.ratio - 3) * 18);
  const head = clamp(100 - sway(all) * 220);
  const posture = clamp(100 - heightCollapse(all) * 280);
  const energyPeak = peakIndex(all);
  const lateEnergy =
    energyPeak > all.length * 0.55 ? 8 : energyPeak < all.length * 0.35 ? -10 : 0;

  const seed = hashFromCapture(views);
  const jitter = (n: number, spread: number) =>
    clamp(n + ((Math.sin(seed * (spread + 1)) + 1) / 2 - 0.5) * spread);

  const amateurBias = {
    shoulderTurn: jitter(pro.shoulderTurn - 14, 8),
    hipTurn: jitter(pro.hipTurn - 8, 6),
    xFactor: jitter(pro.xFactor - 12, 7),
    spineTilt: jitter(posture * 0.9, 5),
    headStability: jitter(head, 6),
    weightShift: jitter(pro.weightShift - sway(all) * 80, 8),
    clubPath: jitter(pro.clubPath - 16 + lateEnergy, 7),
    lag: jitter(pro.lag - 18, 8),
    posture: jitter(posture, 5),
    tempo: jitter(tempoScore, 6),
  };

  return blendMetrics(pro, amateurBias);
}

function phaseHints(views: ViewCapture[]): Record<SwingPhase, string> {
  const all = views.flatMap((v) => v.samples);
  const t = splitTempo(all);
  const s = sway(all);
  const c = heightCollapse(all);
  return {
    address: s < 0.08 ? "어드레스 축은 비교적 안정적입니다." : "어드레스부터 좌우 흔들림이 있습니다.",
    takeaway: "테이크어웨이에서 손과 클럽이 한 덩어리인지 앞면 영상으로 확인하세요.",
    top:
      t.ratio < 2
        ? "탑에 머무는 시간이 짧습니다. 전환을 서두르고 있습니다."
        : "탑까지의 시간은 여유가 있습니다.",
    transition:
      t.ratio < 2.4
        ? "다운이 급합니다. 하체가 먼저 나가게 바꿔 보세요."
        : "전환 템포는 프로 쪽에 가깝습니다.",
    impact:
      c > 0.08
        ? "임팩트 구간에서 키가 줄어듭니다. 얼리 익스텐션을 의심하세요."
        : "임팩트에서 키가 비교적 유지됩니다.",
    finish:
      s > 0.14
        ? "피니시에서 축이 무너집니다. 3초 홀드로 점검하세요."
        : "피니시 밸런스는 괜찮은 편입니다.",
  };
}

export function analyzeSwing(opts: {
  views: ViewCapture[];
  proId: string;
  handedness: "right" | "left";
  trialLimited: boolean;
}): AnalysisResult {
  const pro = getPro(opts.proId);
  if (!pro) throw new Error("프로 템플릿을 찾을 수 없습니다.");

  const userMetrics = metricsFromViews(opts.views, pro.metrics);
  const overall = overallScore(userMetrics, pro.metrics);
  const ranked = rankedGaps(userMetrics, pro.metrics);
  const hints = phaseHints(opts.views);
  const views = opts.views.map((v) => v.view) as SwingView[];
  const has3d = views.includes("faceOn") && views.includes("downTheLine");

  const allGaps: MetricGap[] = ranked.map(({ key, delta }) => {
    const copy = gapCopy(key, userMetrics[key], pro.metrics[key]);
    const abs = Math.abs(delta);
    return {
      key,
      label: METRIC_LABEL_KO[key],
      user: Math.round(userMetrics[key]),
      pro: Math.round(pro.metrics[key]),
      delta: Math.round(delta),
      severity: abs < 8 ? "ok" : abs < 16 ? "watch" : "fix",
      summary: copy.summary,
      drill: copy.drill,
      feel: copy.feel,
    };
  });

  const gaps = opts.trialLimited ? allGaps.slice(0, 3) : allGaps;
  const phaseNotes = SWING_PHASES.map((phase) => ({
    phase,
    note: phaseNote(pro, phase, hints[phase]),
  }));

  return {
    id: `sw_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
    createdAt: new Date().toISOString(),
    proId: pro.id,
    handedness: opts.handedness,
    views,
    has3d,
    overall,
    gaps,
    phaseNotes: opts.trialLimited ? phaseNotes.slice(0, 2) : phaseNotes,
    userMetrics,
    proMetrics: pro.metrics,
    trialLimited: opts.trialLimited,
    coachingFocus: primaryFocus(userMetrics, pro.metrics),
  };
}
