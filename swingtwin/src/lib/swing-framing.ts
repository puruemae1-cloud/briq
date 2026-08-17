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

/** Tight body + club crop — trims sky, floor, and empty sides via motion mass. */
export async function detectBodyCrop(
  video: HTMLVideoElement,
  onProgress?: FramingProgressCallback,
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

  const rowWin = massWindow(rowMass, 0.988);
  const colWin = massWindow(colMass, 0.988);

  let maxRowMass = 0;
  for (let y = 0; y < analysisH; y++) {
    if (rowMass[y] > maxRowMass) maxRowMass = rowMass[y];
  }

  let bodyTopRow = rowWin.start;
  const rowFloor = maxRowMass * 0.06;
  for (let y = rowWin.start; y <= rowWin.end; y++) {
    if (rowMass[y] >= rowFloor) {
      bodyTopRow = y;
      break;
    }
  }

  let cropTopRow = bodyTopRow;
  if (clubApexTopY < analysisH) {
    cropTopRow = Math.min(bodyTopRow, clubApexTopY);
  }
  cropTopRow = Math.max(0, cropTopRow - Math.round(analysisH * 0.012));

  const scaleX = vw / analysisW;
  const scaleY = vh / analysisH;

  let x = colWin.start * scaleX;
  let y = cropTopRow * scaleY;
  let w = (colWin.end - colWin.start + 1) * scaleX;
  let h = (rowWin.end - cropTopRow + 1) * scaleY;

  const padX = w * 0.02;
  const padBottom = h * 0.025;
  x = Math.max(0, x - padX);
  w = Math.min(vw - x, w + padX * 2);
  h = Math.min(vh - y, h + padBottom);

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
): number {
  const userBodyFrac = userMeta.sourceCrop.h / userMeta.sourceH;
  const tourBodyFrac = tourCrop.h / tourH;
  if (tourBodyFrac <= 0) return 1;
  return Math.min(2.4, Math.max(1, userBodyFrac / tourBodyFrac));
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

  const zoom = Math.min(2.4, Math.max(1, matchScale));
  let c = crop;
  if (zoom > 1.02) {
    const inset = 1 - 1 / zoom;
    c = {
      x: crop.x + crop.w * (inset / 2),
      y: crop.y + crop.h * (inset / 2),
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

export async function detectBodyCropFromUrl(src: string): Promise<{
  crop: CropRect;
  sourceW: number;
  sourceH: number;
}> {
  const video = await loadVideoFromUrl(src);
  const { crop } = await detectBodyCrop(video);
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
