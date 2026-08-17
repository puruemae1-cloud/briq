import type { MotionSample, SkeletonFrame, SwingView, ViewCapture } from "./types";

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

function jointsFromBox(
  t: number,
  cx: number,
  cy: number,
  width: number,
  height: number,
  view: SwingView,
  swingT: number,
): SkeletonFrame {
  const phase = swingT;
  const shoulderY = cy - height * 0.28;
  const hipY = cy + height * 0.05;
  const turn = Math.sin(phase * Math.PI) * (view === "faceOn" ? 0.12 : 0.04);
  const armsUp = Math.sin(Math.min(phase, 0.55) * Math.PI) * height * 0.35;
  const zBase = view === "downTheLine" ? (cx - 0.5) * 1.4 : 0;
  const xBase = view === "faceOn" ? (cx - 0.5) * 1.6 : 0;

  const j = (id: string, x: number, y: number, z: number) => ({ id, x, y, z });

  const left = view === "faceOn" ? 1 : 0.2;
  const right = view === "faceOn" ? -1 : -0.2;

  return {
    t,
    joints: {
      head: j("head", xBase, shoulderY - height * 0.18, zBase),
      neck: j("neck", xBase, shoulderY - 0.02, zBase),
      lShoulder: j(
        "lShoulder",
        xBase + left * width * 0.35,
        shoulderY,
        zBase + turn,
      ),
      rShoulder: j(
        "rShoulder",
        xBase + right * width * 0.35,
        shoulderY,
        zBase - turn,
      ),
      lElbow: j(
        "lElbow",
        xBase + left * width * 0.5,
        shoulderY + height * 0.12 - armsUp * 0.3,
        zBase + turn * 1.4,
      ),
      rElbow: j(
        "rElbow",
        xBase + right * width * 0.55,
        shoulderY - armsUp * 0.5,
        zBase - turn * 1.6,
      ),
      lWrist: j(
        "lWrist",
        xBase + left * width * 0.25,
        shoulderY + height * 0.18 - armsUp,
        zBase + turn * 1.8,
      ),
      rWrist: j(
        "rWrist",
        xBase + right * width * 0.15,
        shoulderY - armsUp * 0.85,
        zBase - turn * 2,
      ),
      lHip: j("lHip", xBase + left * width * 0.18, hipY, zBase * 0.6),
      rHip: j("rHip", xBase + right * width * 0.18, hipY, zBase * 0.6),
      lKnee: j("lKnee", xBase + left * width * 0.16, hipY + height * 0.22, zBase * 0.3),
      rKnee: j("rKnee", xBase + right * width * 0.2, hipY + height * 0.22, zBase * 0.3),
      lAnkle: j("lAnkle", xBase + left * width * 0.14, hipY + height * 0.42, 0),
      rAnkle: j("rAnkle", xBase + right * width * 0.22, hipY + height * 0.42, 0),
    },
  };
}

export async function captureView(
  video: HTMLVideoElement,
  view: SwingView,
  fileName: string,
  sampleCount = 24,
) {
  const duration = Number.isFinite(video.duration) && video.duration > 0
    ? video.duration
    : 2;
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) throw new Error("캔버스를 사용할 수 없습니다.");

  canvas.width = 160;
  canvas.height = 90;
  const thumbCanvas = document.createElement("canvas");
  const tctx = thumbCanvas.getContext("2d");
  thumbCanvas.width = 320;
  thumbCanvas.height = 180;

  const samples: MotionSample[] = [];
  const skeleton: SkeletonFrame[] = [];
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
    skeleton.push(
      jointsFromBox(t, stats.cx, stats.cy, stats.width, stats.height, view, i / sampleCount),
    );

    if (tctx && (i === 2 || i === Math.floor(sampleCount * 0.45) || i === sampleCount - 3)) {
      tctx.drawImage(video, 0, 0, thumbCanvas.width, thumbCanvas.height);
      thumbs.push(thumbCanvas.toDataURL("image/jpeg", 0.6));
    }
  }

  return { view, fileName, duration, samples, thumbs, skeleton };
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

/** 영상 없이 앞·뒤 합성 3D와 분석 흐름을 미리 보는 샘플. */
export function sampleDualViews(): ViewCapture[] {
  const make = (view: SwingView): ViewCapture => {
    const samples: MotionSample[] = [];
    const skeleton: SkeletonFrame[] = [];
    const n = 24;
    for (let i = 0; i < n; i++) {
      const t = (i / (n - 1)) * 1.4;
      const swingT = i / n;
      const energy = 4 + Math.sin(swingT * Math.PI) * 18;
      const cx = 0.5 + Math.sin(swingT * Math.PI * 2) * (view === "faceOn" ? 0.08 : 0.03);
      const cy = 0.48 + Math.sin(swingT * Math.PI) * 0.04;
      const width = 0.28 + swingT * 0.04;
      const height = 0.72 - Math.max(0, swingT - 0.5) * 0.12;
      samples.push({ t, energy, cx, cy, width, height });
      skeleton.push(jointsFromBox(t, cx, cy, width, height, view, swingT));
    }
    return {
      view,
      fileName: view === "faceOn" ? "sample-face-on.mp4" : "sample-dtl.mp4",
      duration: 1.4,
      samples,
      thumbs: [],
      skeleton,
    };
  };
  return [make("faceOn"), make("downTheLine")];
}
