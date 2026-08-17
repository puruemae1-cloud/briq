function waitSeek(video: HTMLVideoElement) {
  return new Promise<void>((resolve, reject) => {
    const onSeeked = () => {
      cleanup();
      resolve();
    };
    const onError = () => {
      cleanup();
      reject(new Error("Could not read that video."));
    };
    const cleanup = () => {
      video.removeEventListener("seeked", onSeeked);
      video.removeEventListener("error", onError);
    };
    video.addEventListener("seeked", onSeeked);
    video.addEventListener("error", onError);
  });
}

function luma(data: Uint8ClampedArray, i: number) {
  return data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
}

export type CropRect = { x: number; y: number; w: number; h: number };

async function loadVideoFromFile(file: File) {
  const url = URL.createObjectURL(file);
  const video = document.createElement("video");
  video.src = url;
  video.muted = true;
  video.playsInline = true;
  video.preload = "auto";
  await new Promise<void>((resolve, reject) => {
    video.onloadedmetadata = () => resolve();
    video.onerror = () => reject(new Error("Could not read that video."));
  });
  return { video, url };
}

/** Union bbox of every pixel that moves (body + club arc), in source video pixels. */
export async function detectMotionCrop(video: HTMLVideoElement): Promise<CropRect> {
  const vw = video.videoWidth;
  const vh = video.videoHeight;
  if (!vw || !vh) {
    throw new Error("Video has no picture size.");
  }

  const analysisW = 360;
  const analysisH = Math.max(1, Math.round(vh * (analysisW / vw)));
  const canvas = document.createElement("canvas");
  canvas.width = analysisW;
  canvas.height = analysisH;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) throw new Error("Could not analyse video frames.");

  const duration =
    Number.isFinite(video.duration) && video.duration > 0 ? video.duration : 2;
  const sampleCount = Math.min(56, Math.max(28, Math.ceil(duration * 14)));
  const pixelCount = analysisW * analysisH;
  const peakMotion = new Float32Array(pixelCount);
  let bg: Uint8ClampedArray | null = null;
  let prev: Uint8ClampedArray | null = null;

  for (let i = 0; i < sampleCount; i++) {
    const t = (i / Math.max(sampleCount - 1, 1)) * duration * 0.98;
    video.currentTime = t;
    await waitSeek(video);
    ctx.drawImage(video, 0, 0, analysisW, analysisH);
    const cur = ctx.getImageData(0, 0, analysisW, analysisH).data;
    if (!bg) bg = cur.slice();

    for (let p = 0; p < pixelCount; p++) {
      const idx = p * 4;
      const L = luma(cur, idx);
      const fromBg = Math.abs(L - luma(bg, idx));
      const fromPrev = prev ? Math.abs(L - luma(prev, idx)) : 0;
      const motion = Math.max(fromBg, fromPrev);
      if (motion > peakMotion[p]) peakMotion[p] = motion;
    }
    prev = cur.slice();
  }

  const motionThreshold = 8;
  let minX = analysisW;
  let minY = analysisH;
  let maxX = 0;
  let maxY = 0;
  let hits = 0;

  for (let y = 0; y < analysisH; y++) {
    for (let x = 0; x < analysisW; x++) {
      const p = y * analysisW + x;
      if (peakMotion[p] >= motionThreshold) {
        hits++;
        if (x < minX) minX = x;
        if (y < minY) minY = y;
        if (x > maxX) maxX = x;
        if (y > maxY) maxY = y;
      }
    }
  }

  const scaleX = vw / analysisW;
  const scaleY = vh / analysisH;

  if (!hits) {
    return {
      x: Math.round(vw * 0.12),
      y: Math.round(vh * 0.06),
      w: Math.round(vw * 0.76),
      h: Math.round(vh * 0.88),
    };
  }

  let x = minX * scaleX;
  let y = minY * scaleY;
  let w = (maxX - minX + 1) * scaleX;
  let h = (maxY - minY + 1) * scaleY;

  const padX = w * 0.1;
  const padY = h * 0.1;
  x = Math.max(0, x - padX);
  y = Math.max(0, y - padY);
  w = Math.min(vw - x, w + padX * 2);
  h = Math.min(vh - y, h + padY * 2);

  x = Math.round(x);
  y = Math.round(y);
  w = Math.round(w) & ~1;
  h = Math.round(h) & ~1;

  if (w < 32) w = Math.min(vw, 32);
  if (h < 32) h = Math.min(vh, 32);
  if (x + w > vw) x = vw - w;
  if (y + h > vh) y = vh - h;

  return { x: Math.max(0, x), y: Math.max(0, y), w, h };
}

function cropCoversMostOfFrame(crop: CropRect, vw: number, vh: number) {
  return crop.w / vw > 0.94 && crop.h / vh > 0.94;
}

async function renderCroppedVideo(
  video: HTMLVideoElement,
  crop: CropRect,
  onProgress?: (message: string) => void,
): Promise<Blob> {
  const maxEdge = 720;
  const scale = Math.min(1, maxEdge / Math.max(crop.w, crop.h));
  const outW = Math.max(2, Math.round(crop.w * scale) & ~1);
  const outH = Math.max(2, Math.round(crop.h * scale) & ~1);

  const canvas = document.createElement("canvas");
  canvas.width = outW;
  canvas.height = outH;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Could not render cropped video.");

  const fps = 30;
  const duration =
    Number.isFinite(video.duration) && video.duration > 0 ? video.duration : 2;
  const frameCount = Math.max(1, Math.ceil(duration * fps));
  const frameMs = 1000 / fps;

  const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
    ? "video/webm;codecs=vp9"
    : MediaRecorder.isTypeSupported("video/webm;codecs=vp8")
      ? "video/webm;codecs=vp8"
      : "video/webm";

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
    recorder.onstop = () => resolve(new Blob(chunks, { type: mimeType }));
    recorder.onerror = () =>
      reject(new Error("Could not encode cropped video."));
    recorder.start(250);

    void (async () => {
      try {
        for (let i = 0; i < frameCount; i++) {
          if (i % 8 === 0) {
            onProgress?.(`Cropping swing… ${Math.round((i / frameCount) * 100)}%`);
          }
          const t = Math.min(i / fps, Math.max(0, duration - 0.001));
          video.currentTime = t;
          await waitSeek(video);
          ctx.drawImage(video, crop.x, crop.y, crop.w, crop.h, 0, 0, outW, outH);
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

/**
 * Auto-crop static background on upload — keeps the full moving region (golfer + club path)
 * and re-encodes so the swing fills the preview frame.
 */
export async function autoFrameSwingVideo(
  file: File,
  onProgress?: (message: string) => void,
): Promise<File> {
  if (!file.type.startsWith("video/") || typeof MediaRecorder === "undefined") {
    return file;
  }

  const { video, url } = await loadVideoFromFile(file);
  try {
    onProgress?.("Finding swing motion…");
    const crop = await detectMotionCrop(video);
    const vw = video.videoWidth;
    const vh = video.videoHeight;

    if (cropCoversMostOfFrame(crop, vw, vh)) {
      return file;
    }

    onProgress?.("Removing static background…");
    try {
      const blob = await renderCroppedVideo(video, crop, onProgress);
      const stem = file.name.replace(/\.[^.]+$/, "") || "swing";
      return new File([blob], `${stem}-framed.webm`, { type: blob.type });
    } catch {
      return file;
    }
  } finally {
    URL.revokeObjectURL(url);
  }
}
