function seekVideo(video: HTMLVideoElement, t: number) {
  const maxT = Number.isFinite(video.duration) && video.duration > 0
    ? Math.max(0, video.duration - 0.05)
    : 0;
  const target = Math.max(0, Math.min(t, maxT));

  return new Promise<void>((resolve, reject) => {
    if (Math.abs(video.currentTime - target) < 0.02 && video.readyState >= 2) {
      resolve();
      return;
    }

    const timeout = window.setTimeout(() => {
      cleanup();
      reject(new Error("Video seek timed out"));
    }, 12_000);

    const onSeeked = () => {
      cleanup();
      resolve();
    };
    const onError = () => {
      cleanup();
      reject(new Error("Could not read that video."));
    };
    const cleanup = () => {
      window.clearTimeout(timeout);
      video.removeEventListener("seeked", onSeeked);
      video.removeEventListener("error", onError);
    };

    video.addEventListener("seeked", onSeeked);
    video.addEventListener("error", onError);
    try {
      video.currentTime = target;
    } catch (e) {
      cleanup();
      reject(e instanceof Error ? e : new Error("Video seek failed"));
    }
  });
}

function luma(data: Uint8ClampedArray, i: number) {
  return data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
}

export type CropRect = { x: number; y: number; w: number; h: number };

export type FramingProgress = { label: string; percent: number };
export type FramingProgressCallback = (progress: FramingProgress) => void;

function report(
  onProgress: FramingProgressCallback | undefined,
  label: string,
  percent: number,
) {
  onProgress?.({
    label,
    percent: Math.min(100, Math.max(0, Math.round(percent))),
  });
}

export type BodyFrameMeta = {
  bodyFill: number;
  outputW: number;
  outputH: number;
  /** Source crop used before normalise (for tour scale matching). */
  sourceCrop: CropRect;
  sourceW: number;
  sourceH: number;
};

export type FramedVideoResult = {
  file: File;
  meta: BodyFrameMeta;
  /** Original file + CSS crop (no re-encode) — used on mobile for reliability. */
  cssOnly?: boolean;
};

const OUTPUT_W = 540;
const OUTPUT_H = 720;
const MOTION_THRESHOLD = 7;

async function loadVideoFromUrl(
  src: string,
  onProgress?: FramingProgressCallback,
) {
  report(onProgress, "Reading video…", 3);
  const video = document.createElement("video");
  video.src = src;
  video.muted = true;
  video.playsInline = true;
  video.setAttribute("playsinline", "true");
  video.preload = "auto";
  if (!src.startsWith("blob:")) {
    video.crossOrigin = "anonymous";
  }

  await new Promise<void>((resolve, reject) => {
    let settled = false;
    const finish = (ok: boolean) => {
      if (settled) return;
      settled = true;
      cleanup();
      if (ok) resolve();
      else reject(new Error("Could not read that video."));
    };

    const timeout = window.setTimeout(() => {
      if (video.readyState >= 1 && video.videoWidth > 0) finish(true);
      else finish(false);
    }, 20_000);

    const pulse = window.setInterval(() => {
      if (video.readyState >= 1 && video.videoWidth > 0) finish(true);
    }, 350);

    const tryReady = () => {
      report(onProgress, "Loading video…", 5);
      if (video.readyState >= 1 && video.videoWidth > 0) finish(true);
    };

    const cleanup = () => {
      window.clearTimeout(timeout);
      window.clearInterval(pulse);
      video.removeEventListener("loadedmetadata", tryReady);
      video.removeEventListener("loadeddata", tryReady);
      video.removeEventListener("canplay", tryReady);
      video.removeEventListener("error", onErr);
    };
    const onErr = () => finish(false);

    video.addEventListener("loadedmetadata", tryReady);
    video.addEventListener("loadeddata", tryReady);
    video.addEventListener("canplay", tryReady);
    video.addEventListener("error", onErr);
    video.load();
    tryReady();
  });

  report(onProgress, "Video ready", 7);
  return video;
}

async function loadVideoFromFile(
  file: File,
  onProgress?: FramingProgressCallback,
) {
  const url = URL.createObjectURL(file);
  const video = await loadVideoFromUrl(url, onProgress);
  return { video, url };
}

function isMobileLike() {
  return /iPhone|iPad|iPod|Android|Mobi/i.test(navigator.userAgent);
}

function encodeMimeType() {
  if (MediaRecorder.isTypeSupported("video/webm;codecs=vp9")) {
    return "video/webm;codecs=vp9";
  }
  if (MediaRecorder.isTypeSupported("video/webm;codecs=vp8")) {
    return "video/webm;codecs=vp8";
  }
  return "video/webm";
}

function encodeWithTimeout(
  video: HTMLVideoElement,
  crop: CropRect,
  onProgress?: FramingProgressCallback,
  ms = 45_000,
) {
  return Promise.race([
    renderBodyFocusedVideo(video, crop, onProgress),
    new Promise<Blob>((_, reject) => {
      window.setTimeout(() => reject(new Error("Encode timed out")), ms);
    }),
  ]);
}

type MotionAnalysis = {
  crop: CropRect;
  analysisW: number;
  analysisH: number;
};

export type CropMode = "user" | "tour";

/** Tight body + club crop — trims sky, floor, and empty sides via motion mass. */
export async function detectBodyCrop(
  video: HTMLVideoElement,
  onProgress?: FramingProgressCallback,
  mode: CropMode = "user",
): Promise<MotionAnalysis> {
  const vw = video.videoWidth;
  const vh = video.videoHeight;
  if (!vw || !vh) throw new Error("Video has no picture size.");

  const analysisW = 360;
  const analysisH = Math.max(1, Math.round(vh * (analysisW / vw)));
  const canvas = document.createElement("canvas");
  canvas.width = analysisW;
  canvas.height = analysisH;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) throw new Error("Could not analyse video frames.");

  const duration =
    Number.isFinite(video.duration) && video.duration > 0 ? video.duration : 2;
  const sampleCount = isMobileLike()
    ? Math.min(14, Math.max(8, Math.ceil(duration * 5)))
    : Math.min(24, Math.max(12, Math.ceil(duration * 8)));
  const pixelCount = analysisW * analysisH;
  const peakMotion = new Float32Array(pixelCount);
  const peakFastMotion = new Float32Array(pixelCount);
  let bg: Uint8ClampedArray | null = null;
  let prev: Uint8ClampedArray | null = null;
  let clubApexTopY = analysisH;
  const FAST_MOTION = 13;

  for (let i = 0; i < sampleCount; i++) {
    const t = (i / Math.max(sampleCount - 1, 1)) * duration * 0.98;
    report(onProgress, "Finding driver apex…", 8 + (i / sampleCount) * 22);
    try {
      await seekVideo(video, t);
    } catch {
      continue;
    }
    ctx.drawImage(video, 0, 0, analysisW, analysisH);
    const cur = ctx.getImageData(0, 0, analysisW, analysisH).data;
    if (!bg) bg = cur.slice();

    let frameFastTop = analysisH;
    for (let p = 0; p < pixelCount; p++) {
      const idx = p * 4;
      const L = luma(cur, idx);
      const fromBg = Math.abs(L - luma(bg, idx));
      const fromPrev = prev ? Math.abs(L - luma(prev, idx)) : 0;
      const motion = Math.max(fromBg, fromPrev);
      if (motion > peakMotion[p]) peakMotion[p] = motion;
      if (fromPrev >= FAST_MOTION) {
        if (fromPrev > peakFastMotion[p]) peakFastMotion[p] = fromPrev;
        const y = Math.floor(p / analysisW);
        if (y < frameFastTop) frameFastTop = y;
      }
    }
    if (frameFastTop < analysisH) {
      clubApexTopY = Math.min(clubApexTopY, frameFastTop);
    }
    prev = cur.slice();
  }

  if (clubApexTopY >= analysisH) {
    for (let p = 0; p < pixelCount; p++) {
      if (peakFastMotion[p] > 0) {
        const y = Math.floor(p / analysisW);
        if (y < clubApexTopY) clubApexTopY = y;
      }
    }
  }

  const rowMass = new Float32Array(analysisH);
  const colMass = new Float32Array(analysisW);
  let total = 0;

  for (let y = 0; y < analysisH; y++) {
    for (let x = 0; x < analysisW; x++) {
      const p = y * analysisW + x;
      const w = peakMotion[p] >= MOTION_THRESHOLD ? peakMotion[p] : 0;
      if (!w) continue;
      rowMass[y] += w;
      colMass[x] += w;
      total += w;
    }
  }

  if (total <= 0) {
    const crop: CropRect = {
      x: Math.round(vw * 0.22),
      y: Math.round(vh * 0.06),
      w: Math.round(vw * 0.56),
      h: Math.round(vh * 0.88),
    };
    return { crop, analysisW, analysisH };
  }

  const massWindow = (mass: Float32Array, cover: number) => {
    const target = total * cover;
    let bestLen = mass.length + 1;
    let bestStart = 0;
    let sum = 0;
    let left = 0;
    for (let right = 0; right < mass.length; right++) {
      sum += mass[right];
      while (sum >= target && left <= right) {
        const len = right - left + 1;
        if (len < bestLen) {
          bestLen = len;
          bestStart = left;
        }
        sum -= mass[left];
        left++;
      }
    }
    if (bestLen > mass.length) {
      let start = 0;
      for (let i = 0; i < mass.length; i++) {
        if (mass[i] > 0) {
          start = i;
          break;
        }
      }
      let end = mass.length - 1;
      for (let i = mass.length - 1; i >= 0; i--) {
        if (mass[i] > 0) {
          end = i;
          break;
        }
      }
      return { start, end };
    }
    return { start: bestStart, end: bestStart + bestLen - 1 };
  };

  const rowCover = mode === "tour" ? 0.86 : 0.968;
  const colCover = mode === "tour" ? 0.8 : 0.962;
  const rowWin = massWindow(rowMass, rowCover);
  const colWin = massWindow(colMass, colCover);

  let maxRowMass = 0;
  let maxColMass = 0;
  for (let y = 0; y < analysisH; y++) {
    if (rowMass[y] > maxRowMass) maxRowMass = rowMass[y];
  }
  for (let x = 0; x < analysisW; x++) {
    if (colMass[x] > maxColMass) maxColMass = colMass[x];
  }

  const rowFloor = maxRowMass * (mode === "tour" ? 0.14 : 0.1);
  const colFloor = maxColMass * (mode === "tour" ? 0.16 : 0.12);

  let bodyTopRow = rowWin.start;
  for (let y = rowWin.start; y <= rowWin.end; y++) {
    if (rowMass[y] >= rowFloor) {
      bodyTopRow = y;
      break;
    }
  }

  let bodyBottomRow = rowWin.end;
  for (let y = rowWin.end; y >= bodyTopRow; y--) {
    if (rowMass[y] >= rowFloor) {
      bodyBottomRow = y;
      break;
    }
  }
  if (mode === "user") {
    bodyBottomRow = Math.min(
      analysisH - 1,
      bodyBottomRow + Math.round(analysisH * 0.018),
    );
  }

  let cropLeftCol = colWin.start;
  for (let x = colWin.start; x <= colWin.end; x++) {
    if (colMass[x] >= colFloor) {
      cropLeftCol = x;
      break;
    }
  }

  let cropRightCol = colWin.end;
  for (let x = colWin.end; x >= cropLeftCol; x--) {
    if (colMass[x] >= colFloor) {
      cropRightCol = x;
      break;
    }
  }

  const landscape = vw > vh * 1.15;
  const skyBand = landscape ? Math.round(analysisH * 0.38) : 0;

  let cropTopRow = bodyTopRow;
  if (mode === "user" && clubApexTopY < analysisH && clubApexTopY >= skyBand) {
    cropTopRow = Math.min(bodyTopRow, clubApexTopY);
  }
  if (mode === "tour" && landscape) {
    cropTopRow = Math.max(cropTopRow, skyBand);
  }
  const headroom = Math.round(analysisH * (mode === "tour" ? 0.004 : 0.004));
  cropTopRow = Math.max(skyBand && mode === "tour" ? skyBand : 0, cropTopRow - headroom);

  const scaleX = vw / analysisW;
  const scaleY = vh / analysisH;

  if (mode === "tour") {
    let sumX = 0;
    let sumW = 0;
    for (let y = cropTopRow; y <= bodyBottomRow; y++) {
      for (let x = cropLeftCol; x <= cropRightCol; x++) {
        const p = y * analysisW + x;
        const m = peakMotion[p] >= MOTION_THRESHOLD ? peakMotion[p] : 0;
        if (m <= 0) continue;
        sumX += x * m;
        sumW += m;
      }
    }

    const cx = sumW > 0 ? sumX / sumW : (cropLeftCol + cropRightCol) / 2;
    const bodySpan = bodyBottomRow - cropTopRow + 1;
    const tourW = Math.min(
      analysisW * 0.36,
      Math.max(analysisW * 0.24, (cropRightCol - cropLeftCol + 1) * 0.62),
    );
    const tourH = Math.min(
      analysisH * 0.88,
      Math.max(bodySpan * 1.0, analysisH * 0.62),
    );

    let leftCol = cx - tourW * 0.44;
    let topRow = cropTopRow;
    if (topRow + tourH > analysisH) topRow = Math.max(0, analysisH - tourH);
    if (leftCol < 0) leftCol = 0;
    if (leftCol + tourW > analysisW) leftCol = Math.max(0, analysisW - tourW);

    cropLeftCol = Math.round(leftCol);
    cropRightCol = Math.min(analysisW - 1, Math.round(leftCol + tourW));
    cropTopRow = Math.round(topRow);
    bodyBottomRow = Math.min(analysisH - 1, Math.round(cropTopRow + tourH));
  }

  let x = cropLeftCol * scaleX;
  let y = cropTopRow * scaleY;
  let w = (cropRightCol - cropLeftCol + 1) * scaleX;
  let h = (bodyBottomRow - cropTopRow + 1) * scaleY;

  if (mode === "user") {
    const padLeft = w * 0.025;
    x = Math.max(0, x - padLeft);
    w = Math.min(vw - x, w + padLeft);

    const trimTop = h * 0.055;
    const trimBottom = h * 0.13;
    const trimRight = w * 0.14;
    y += trimTop;
    h -= trimTop + trimBottom;
    w -= trimRight;
  } else {
    x = Math.max(0, x);
    w = Math.min(vw - x, w);
  }

  h = Math.min(vh - y, h);

  x = Math.round(x);
  y = Math.round(y);
  w = Math.max(32, Math.round(w) & ~1);
  h = Math.max(32, Math.round(h) & ~1);
  if (x + w > vw) x = Math.max(0, vw - w);
  if (y + h > vh) y = Math.max(0, vh - h);

  return { crop: { x, y, w, h }, analysisW, analysisH };
}

/** @deprecated use detectBodyCrop */
export async function detectMotionCrop(video: HTMLVideoElement): Promise<CropRect> {
  const { crop } = await detectBodyCrop(video);
  return crop;
}

export type SwingLandmarks = {
  /** Normalised 0–1 in source video. */
  headY: number;
  feetY: number;
  backX: number;
  ballX: number;
  ballY: number;
};

/** Rory portrait 540×720 — head, soles, spine, ball at address. */
export const RORY_PORTRAIT_LANDMARKS: SwingLandmarks = {
  headY: 0.18,
  feetY: 0.935,
  backX: 0.4,
  ballX: 0.52,
  ballY: 0.86,
};

function clamp01(n: number) {
  return Math.min(1, Math.max(0, n));
}

/** Extra CSS zoom so a distant phone golfer fills the panel like Rory. */
export const USER_TO_RORY_ZOOM = 1.55;

/**
 * Tight 3:4 crop so the user's head-to-feet span matches Rory in the panel.
 * Width follows body height (not ball-to-back, which made phone clips too wide/small).
 *
 * Head/feet must always be visible — generous headroom + footroom baked in.
 */
export function cropToMatchLandmarks(
  src: SwingLandmarks,
  target: SwingLandmarks,
  sourceW: number,
  sourceH: number,
): CropRect {
  let headY = src.headY;
  let feetY = src.feetY;
  let bodySpan = Math.max(0.12, feetY - headY);
  // Phone DTL often tags sky as "head", leaving the golfer tiny in a near-full-frame crop.
  if (bodySpan > 0.62) {
    feetY = Math.min(0.97, src.feetY);
    headY = Math.max(0.05, feetY - 0.45);
    bodySpan = feetY - headY;
  }
  const targetSpan = Math.max(0.72, target.feetY - target.headY);
  // body fills 72 % of the crop height, leaving 14 % headroom + 14 % footroom
  const fill = 0.72;
  const bodyH = bodySpan * sourceH;
  let cropH = bodyH / fill;
  let cropW = cropH * (3 / 4);

  cropW = Math.max(48, cropW);
  cropH = Math.max(64, cropH);

  // Place crop so head sits at ~14 % from top (never clipped even during backswing)
  const headroom = cropH * 0.14;
  let x = src.backX * sourceW - 0.42 * cropW;
  let y = headY * sourceH - headroom;

  if (cropW > sourceW) {
    cropH *= sourceW / cropW;
    cropW = sourceW;
    x = 0;
  }
  if (cropH > sourceH) {
    cropW *= sourceH / cropH;
    cropH = sourceH;
    y = 0;
  }
  x = Math.max(0, Math.min(x, sourceW - cropW));
  y = Math.max(0, Math.min(y, sourceH - cropH));

  x = Math.round(x);
  y = Math.round(y);
  let w = Math.max(32, Math.round(cropW) & ~1);
  let h = Math.max(32, Math.round(cropH) & ~1);
  if (x + w > sourceW) x = Math.max(0, sourceW - w);
  if (y + h > sourceH) y = Math.max(0, sourceH - h);

  return { x, y, w, h };
}

/** Detect head, soles, back (spine), and ball from address + motion. */
export async function detectSwingLandmarks(
  video: HTMLVideoElement,
  onProgress?: FramingProgressCallback,
): Promise<SwingLandmarks> {
  const { crop, analysisW, analysisH } = await detectBodyCrop(
    video,
    onProgress,
    "user",
  );
  const vw = video.videoWidth;
  const vh = video.videoHeight;
  const scaleX = vw / analysisW;
  const scaleY = vh / analysisH;

  const canvas = document.createElement("canvas");
  canvas.width = analysisW;
  canvas.height = analysisH;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) {
    return {
      headY: crop.y / vh,
      feetY: (crop.y + crop.h) / vh,
      backX: (crop.x + crop.w * 0.4) / vw,
      ballX: (crop.x + crop.w * 0.58) / vw,
      ballY: (crop.y + crop.h * 0.9) / vh,
    };
  }

  const duration =
    Number.isFinite(video.duration) && video.duration > 0 ? video.duration : 2;
  const tAddr = Math.min(0.35, duration * 0.12);
  try {
    await seekVideo(video, tAddr);
  } catch {
    /* use current frame */
  }
  ctx.drawImage(video, 0, 0, analysisW, analysisH);
  const img = ctx.getImageData(0, 0, analysisW, analysisH).data;

  const x0 = Math.max(0, Math.floor(crop.x / scaleX));
  const y0 = Math.max(0, Math.floor(crop.y / scaleY));
  const x1 = Math.min(analysisW - 1, Math.ceil((crop.x + crop.w) / scaleX));
  const y1 = Math.min(analysisH - 1, Math.ceil((crop.y + crop.h) / scaleY));

  const rowFill = new Float32Array(analysisH);
  const colFill = new Float32Array(analysisW);

  for (let y = y0; y <= y1; y++) {
    for (let x = x0; x <= x1; x++) {
      const idx = (y * analysisW + x) * 4;
      const r = img[idx];
      const g = img[idx + 1];
      const b = img[idx + 2];
      const L = luma(img, idx);
      const sky = L > 165 && Math.abs(r - g) < 45 && b + 8 >= r;
      const grass = g > r + 14 && g > b + 10 && y > analysisH * 0.55;
      if (sky || grass) continue;
      const body =
        L < 155 || (g > 90 && r > 70 && Math.abs(r - g) < 40);
      if (!body) continue;
      rowFill[y] += 1;
      colFill[x] += 1;
    }
  }

  let maxRow = 0;
  for (let y = y0; y <= y1; y++) if (rowFill[y] > maxRow) maxRow = rowFill[y];
  const rowT = Math.max(4, maxRow * 0.22);

  let headRow = y0 + Math.round((y1 - y0) * 0.1);
  for (let y = headRow; y <= y1; y++) {
    if (rowFill[y] >= rowT && rowFill[y] > analysisW * 0.06) {
      headRow = y;
      break;
    }
  }

  let feetRow = y1;
  for (let y = y1; y >= headRow; y--) {
    if (rowFill[y] >= rowT * 0.7) {
      feetRow = y;
      break;
    }
  }

  const torso0 = Math.round(headRow + (feetRow - headRow) * 0.28);
  const torso1 = Math.round(headRow + (feetRow - headRow) * 0.62);
  let backSum = 0;
  let backN = 0;
  for (let y = torso0; y <= torso1; y++) {
    for (let x = x0; x <= x1; x++) {
      if (colFill[x] <= 0) continue;
      const idx = (y * analysisW + x) * 4;
      const L = luma(img, idx);
      if (L < 140) {
        backSum += x;
        backN++;
      }
    }
  }
  const backCol =
    backN > 8 ? backSum / backN : (x0 + x1) * 0.42;

  let ballX = backCol + (x1 - x0) * 0.22;
  let ballY = feetRow - (feetRow - headRow) * 0.08;
  let bestBall = 0;
  const by0 = Math.max(y0, Math.round(feetRow - (feetRow - headRow) * 0.18));
  const by1 = Math.min(y1, feetRow + 2);
  const bx0 = Math.round(backCol);
  for (let y = by0; y <= by1; y++) {
    for (let x = bx0; x <= x1; x++) {
      const idx = (y * analysisW + x) * 4;
      const r = img[idx];
      const g = img[idx + 1];
      const b = img[idx + 2];
      const L = luma(img, idx);
      if (L > 190 && r > 175 && g > 175 && b > 160) {
        const score = L;
        if (score > bestBall) {
          bestBall = score;
          ballX = x;
          ballY = y;
        }
      }
    }
  }

  return {
    headY: clamp01((headRow * scaleY) / vh),
    feetY: clamp01((feetRow * scaleY) / vh),
    backX: clamp01((backCol * scaleX) / vw),
    ballX: clamp01((ballX * scaleX) / vw),
    ballY: clamp01((ballY * scaleY) / vh),
  };
}

export async function detectSwingLandmarksFromUrl(
  src: string,
  onProgress?: FramingProgressCallback,
) {
  const video = await loadVideoFromUrl(src, onProgress);
  try {
    return {
      landmarks: await detectSwingLandmarks(video, onProgress),
      sourceW: video.videoWidth,
      sourceH: video.videoHeight,
    };
  } finally {
    video.src = "";
  }
}

export type VideoDisplayStyle = {
  position?: "absolute";
  top?: string;
  left?: string;
  width?: string;
  height?: string;
  objectFit?: "cover" | "contain" | "fill" | "none";
  objectPosition?: string;
  transform?: string;
  transformOrigin?: string;
  maxWidth?: string;
};

/** Zoom Rory so his body matches the user's framed body height. */
export function tourMatchScale(
  userMeta: BodyFrameMeta,
  tourCrop: CropRect,
  tourH: number,
  tourW?: number,
): number {
  const userBodyFrac = userMeta.sourceCrop.h / userMeta.sourceH;
  const tourBodyFrac = tourCrop.h / tourH;
  if (tourBodyFrac <= 0) return 1.35;

  const heightScale = userBodyFrac / tourBodyFrac;
  let scale = heightScale;

  if (tourW && tourW > 0) {
    const userWidthFrac = userMeta.sourceCrop.w / userMeta.sourceW;
    const tourWidthFrac = tourCrop.w / tourW;
    if (tourWidthFrac > 0) {
      const widthScale = userWidthFrac / tourWidthFrac;
      scale = heightScale * 0.55 + widthScale * 0.45;
    }
  }

  return Math.min(4.2, Math.max(1.15, scale));
}

/** Hard CSS crop — maps source crop rect onto an overflow-hidden panel. */
export function cropToVideoStyle(
  crop: CropRect,
  sourceW: number,
  sourceH: number,
  matchScale = 1,
): VideoDisplayStyle {
  if (!sourceW || !sourceH || !crop.w || !crop.h) {
    return { objectFit: "cover", objectPosition: "50% 55%" };
  }

  const zoom = Math.min(4.2, Math.max(1, matchScale));
  let c = crop;
  if (zoom > 1.02) {
    const inset = 1 - 1 / zoom;
    // Bias inset downward so the head is never cropped: top takes only 5 % of the
    // inset, bottom takes the remaining 95 %.
    const topBias = 0.05;
    c = {
      x: crop.x + crop.w * (inset / 2),
      y: crop.y + crop.h * (inset * topBias),
      w: crop.w / zoom,
      h: crop.h / zoom,
    };
  }

  const wPct = (sourceW / c.w) * 100;
  const hPct = (sourceH / c.h) * 100;
  const leftPct = (-c.x / c.w) * 100;
  const topPct = (-c.y / c.h) * 100;

  return {
    position: "absolute",
    top: `${topPct}%`,
    left: `${leftPct}%`,
    width: `${wPct}%`,
    height: `${hPct}%`,
    objectFit: "fill",
    maxWidth: "none",
  };
}

export async function detectBodyCropFromUrl(
  src: string,
  mode: CropMode = "user",
): Promise<{
  crop: CropRect;
  sourceW: number;
  sourceH: number;
}> {
  const video = await loadVideoFromUrl(src);
  const { crop } = await detectBodyCrop(video, undefined, mode);
  return { crop, sourceW: video.videoWidth, sourceH: video.videoHeight };
}

async function renderBodyFocusedVideo(
  video: HTMLVideoElement,
  crop: CropRect,
  onProgress?: FramingProgressCallback,
): Promise<Blob> {
  const outW = OUTPUT_W;
  const outH = OUTPUT_H;
  const canvas = document.createElement("canvas");
  canvas.width = outW;
  canvas.height = outH;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Could not render cropped video.");

  const scale = Math.max(outW / crop.w, outH / crop.h);
  const drawW = crop.w * scale;
  const drawH = crop.h * scale;
  const dx = (outW - drawW) / 2;
  const dy = (outH - drawH) / 2;

  const fps = 24;
  const duration =
    Number.isFinite(video.duration) && video.duration > 0 ? video.duration : 2;
  const frameCount = Math.max(1, Math.ceil(duration * fps));
  const frameMs = 1000 / fps;

  const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
    ? "video/webm;codecs=vp9"
    : MediaRecorder.isTypeSupported("video/webm;codecs=vp8")
      ? "video/webm;codecs=vp8"
      : "video/webm";

  if (!MediaRecorder.isTypeSupported(mimeType)) {
    throw new Error("MediaRecorder not supported");
  }

  const stream = canvas.captureStream(fps);
  const recorder = new MediaRecorder(stream, {
    mimeType,
    videoBitsPerSecond: 2_800_000,
  });
  const chunks: BlobPart[] = [];

  const blob = await new Promise<Blob>((resolve, reject) => {
    recorder.ondataavailable = (e) => {
      if (e.data.size) chunks.push(e.data);
    };
    recorder.onstop = () => {
      const out = new Blob(chunks, { type: mimeType });
      if (out.size < 1024) {
        reject(new Error("Encoded video was empty"));
        return;
      }
      resolve(out);
    };
    recorder.onerror = () =>
      reject(new Error("Could not encode cropped video."));
    recorder.start(250);

    void (async () => {
      try {
        for (let i = 0; i < frameCount; i++) {
          report(
            onProgress,
            "Framing body — cutting sky at driver apex…",
            34 + (i / frameCount) * 58,
          );
          const t = Math.min(i / fps, Math.max(0, duration - 0.001));
          await seekVideo(video, t);
          ctx.fillStyle = "#04110c";
          ctx.fillRect(0, 0, outW, outH);
          ctx.drawImage(
            video,
            crop.x,
            crop.y,
            crop.w,
            crop.h,
            dx,
            dy,
            drawW,
            drawH,
          );
          await new Promise((r) => setTimeout(r, frameMs));
        }
        recorder.stop();
      } catch (e) {
        recorder.stop();
        reject(e);
      }
    })();
  });

  return blob;
}

function buildMeta(video: HTMLVideoElement, crop: CropRect): BodyFrameMeta {
  return {
    bodyFill: 1,
    outputW: OUTPUT_W,
    outputH: OUTPUT_H,
    sourceCrop: crop,
    sourceW: video.videoWidth,
    sourceH: video.videoHeight,
  };
}

async function frameVideoElement(
  video: HTMLVideoElement,
  file: File,
  onProgress?: FramingProgressCallback,
  fileStem = "swing",
): Promise<FramedVideoResult> {
  report(onProgress, "Finding driver apex…", 8);
  const { crop } = await detectBodyCrop(video, onProgress);
  const meta = buildMeta(video, crop);
  report(onProgress, "Cutting sky at driver apex…", 32);

  const mimeType = encodeMimeType();
  const useCssOnly =
    isMobileLike() ||
    typeof MediaRecorder === "undefined" ||
    !MediaRecorder.isTypeSupported(mimeType);

  if (useCssOnly) {
    report(onProgress, "Crop applied (fast mode)", 100);
    return { file, meta, cssOnly: true };
  }

  try {
    report(onProgress, "Encoding cropped video…", 40);
    const blob = await encodeWithTimeout(video, crop, onProgress);
    report(onProgress, "Body crop complete", 94);
    const out = new File([blob], `${fileStem}-framed.webm`, { type: blob.type });
    return { file: out, meta, cssOnly: false };
  } catch {
    report(onProgress, "Using fast crop mode", 96);
    return { file, meta, cssOnly: true };
  }
}

export async function autoFrameSwingVideo(
  file: File,
  onProgress?: FramingProgressCallback,
): Promise<FramedVideoResult> {
  report(onProgress, "Reading video…", 2);
  if (!file.type.startsWith("video/")) {
    return {
      file,
      meta: {
        bodyFill: 1,
        outputW: OUTPUT_W,
        outputH: OUTPUT_H,
        sourceCrop: { x: 0, y: 0, w: 1, h: 1 },
        sourceW: 1,
        sourceH: 1,
      },
    };
  }

  const { video, url } = await loadVideoFromFile(file, onProgress);
  try {
    const stem = file.name.replace(/\.[^.]+$/, "") || "swing";
    const result = await frameVideoElement(video, file, onProgress, stem);
    report(onProgress, "Done", 100);
    return result;
  } catch {
    report(onProgress, "Done", 100);
    return {
      file,
      meta: buildMeta(video, { x: 0, y: 0, w: video.videoWidth, h: video.videoHeight }),
      cssOnly: true,
    };
  } finally {
    URL.revokeObjectURL(url);
  }
}

export { OUTPUT_W, OUTPUT_H };
