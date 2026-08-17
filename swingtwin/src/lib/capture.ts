import { AMATEUR_STYLE, FINE_PHASES, TOUR_STYLE, type PlayerStyle } from "./anatomy";
import { framesForStyle, userFramesFromMotion } from "./pose";
import type { Handedness, MotionSample, SkeletonFrame, SwingView, ViewCapture } from "./types";

function waitSeek(video: HTMLVideoElement) {
  return new Promise<void>((resolve) => {
    const done = () => {
      video.removeEventListener("seeked", done);
      resolve();
    };
    video.addEventListener("seeked", done);
  });
}

function luma(data: Uint8ClampedArray, i: number) {
  return data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
}

function analyzeFrame(
  prev: Uint8ClampedArray | null,
  cur: Uint8ClampedArray,
  w: number,
  h: number,
) {
  let energy = 0;
  let sx = 0;
  let sy = 0;
  let n = 0;
  let minX = w;
  let minY = h;
  let maxX = 0;
  let maxY = 0;

  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4;
      const L = luma(cur, i);
      const d = prev ? Math.abs(L - luma(prev, i)) : 0;
      const fg = d > 18 || L < 90;
      if (d > 18) energy += d;
      if (fg) {
        sx += x;
        sy += y;
        n++;
        if (x < minX) minX = x;
        if (y < minY) minY = y;
        if (x > maxX) maxX = x;
        if (y > maxY) maxY = y;
      }
    }
  }

  const cx = n ? sx / n / w : 0.5;
  const cy = n ? sy / n / h : 0.5;
  const width = n ? (maxX - minX) / w : 0.3;
  const height = n ? (maxY - minY) / h : 0.6;
  return { energy: energy / (w * h), cx, cy, width, height };
}


export async function captureView(
  video: HTMLVideoElement,
  view: SwingView,
  fileName: string,
  opts?: {
    sampleCount?: number;
    handedness?: Handedness;
    style?: PlayerStyle;
  },
) {
  const sampleCount = opts?.sampleCount ?? FINE_PHASES.length;
  const handedness = opts?.handedness ?? "right";
  const duration = Number.isFinite(video.duration) && video.duration > 0
    ? video.duration
    : 2;
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) throw new Error("Could not read frames from that video.");

  canvas.width = 160;
  canvas.height = 90;
  const thumbCanvas = document.createElement("canvas");
  const tctx = thumbCanvas.getContext("2d");
  thumbCanvas.width = 320;
  thumbCanvas.height = 180;

  const samples: MotionSample[] = [];
  const thumbs: string[] = [];
  let prev: Uint8ClampedArray | null = null;

  for (let i = 0; i < sampleCount; i++) {
    const t = (i / Math.max(sampleCount - 1, 1)) * duration * 0.96;
    video.currentTime = t;
    await waitSeek(video);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const img = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const stats = analyzeFrame(
      prev,
      img.data,
      canvas.width,
      canvas.height,
    );
    prev = img.data;
    samples.push({ t, ...stats });

    if (tctx && (i === 2 || i === Math.floor(sampleCount * 0.45) || i === sampleCount - 3)) {
      tctx.drawImage(video, 0, 0, thumbCanvas.width, thumbCanvas.height);
      thumbs.push(thumbCanvas.toDataURL("image/jpeg", 0.6));
    }
  }

  const skeleton = opts?.style
    ? framesForStyle(opts.style, handedness, samples)
    : userFramesFromMotion(samples, handedness);
  return { view, fileName, duration, samples, thumbs, skeleton };
}

export function applyHandedness(
  views: ViewCapture[],
  handedness: Handedness,
  style?: PlayerStyle,
): ViewCapture[] {
  return views.map((v) => ({
    ...v,
    skeleton: style
      ? framesForStyle(style, handedness, v.samples)
      : userFramesFromMotion(v.samples, handedness),
  }));
}

export function fuseSkeletons(
  faceOn?: SkeletonFrame[],
  dtl?: SkeletonFrame[],
): SkeletonFrame[] {
  if (faceOn?.length && dtl?.length) {
    const n = Math.min(faceOn.length, dtl.length);
    return Array.from({ length: n }, (_, i) => {
      const a = faceOn[i];
      const b = dtl[i];
      const joints: SkeletonFrame["joints"] = {};
      for (const id of Object.keys(a.joints)) {
        const fa = a.joints[id];
        const fb = b.joints[id];
        joints[id] = {
          id,
          x: fa.x,
          y: (fa.y + fb.y) / 2,
          z: fb.z || fb.x,
        };
      }
      return { t: a.t, joints };
    });
  }
  return faceOn ?? dtl ?? [];
}

/** Demo pair: amateur-like face-on + DTL, plus a quieter tour face-on. */
export function sampleCompareSet(handedness: Handedness = "right") {
  const make = (
    view: SwingView,
    fileName: string,
    swayAmt: number,
    collapse: number,
    duration: number,
  ): ViewCapture => {
    const samples: MotionSample[] = [];
    const n = FINE_PHASES.length;
    for (let i = 0; i < n; i++) {
      const swingT = i / Math.max(n - 1, 1);
      const t = swingT * duration;
      const energy = 4 + Math.sin(swingT * Math.PI) * 18;
      const cx = 0.5 + Math.sin(swingT * Math.PI * 2) * swayAmt;
      const cy = 0.48 + Math.sin(swingT * Math.PI) * 0.04;
      const width = 0.28 + swingT * 0.04;
      const height = 0.72 - Math.max(0, swingT - 0.5) * collapse;
      samples.push({ t, energy, cx, cy, width, height });
    }
    const style = swayAmt > 0.05 ? AMATEUR_STYLE : TOUR_STYLE;
    return {
      view,
      fileName,
      duration,
      samples,
      thumbs: [],
      skeleton: framesForStyle(style, handedness, samples),
    };
  };

  return {
    user: [
      make("faceOn", "my-face-on.mp4", 0.09, 0.14, 1.35),
      make("downTheLine", "my-dtl.mp4", 0.04, 0.12, 1.35),
    ],
    tour: [make("faceOn", "tour-player.mp4", 0.03, 0.04, 1.55)],
  };
}

export function sampleDualViews(): ViewCapture[] {
  return sampleCompareSet().user;
}
