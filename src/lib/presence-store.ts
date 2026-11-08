import { get, put } from "@vercel/blob";
import { promises as fs } from "fs";
import path from "path";

/** Heartbeats older than this are pruned (viewer left / tab backgrounded). */
export const PRESENCE_TTL_MS = 50_000;

type PresenceMap = Record<string, number>;

type GlobalPresence = {
  __briqPresence?: Map<string, PresenceMap>;
};

const g = globalThis as typeof globalThis & GlobalPresence;

function memory(): Map<string, PresenceMap> {
  if (!g.__briqPresence) g.__briqPresence = new Map();
  return g.__briqPresence;
}

function blobEnabled(): boolean {
  return Boolean(process.env.BLOB_READ_WRITE_TOKEN);
}

function dataDir(): string {
  return process.env.VERCEL
    ? path.join("/tmp", "briq-presence")
    : path.join(process.cwd(), "data", "presence");
}

function safeProductId(productId: string): string | null {
  const id = (productId || "").trim();
  if (!id || id.length > 120) return null;
  if (!/^[a-zA-Z0-9][a-zA-Z0-9._:-]*$/.test(id)) return null;
  return id;
}

function blobPath(productId: string): string {
  return `presence/${encodeURIComponent(productId)}.json`;
}

function filePath(productId: string): string {
  return path.join(dataDir(), `${encodeURIComponent(productId)}.json`);
}

function prune(map: PresenceMap, now = Date.now()): PresenceMap {
  const out: PresenceMap = {};
  for (const [vid, ts] of Object.entries(map)) {
    if (typeof ts === "number" && now - ts <= PRESENCE_TTL_MS) {
      out[vid] = ts;
    }
  }
  return out;
}

function parseMap(raw: string): PresenceMap {
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    const out: PresenceMap = {};
    for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
      if (typeof v === "number" && Number.isFinite(v)) out[k] = v;
    }
    return out;
  } catch {
    return {};
  }
}

async function readBlob(productId: string): Promise<PresenceMap> {
  try {
    const result = await get(blobPath(productId), {
      access: "private",
      useCache: false,
    });
    if (!result || result.statusCode !== 200 || !result.stream) return {};
    return parseMap(await new Response(result.stream).text());
  } catch {
    return {};
  }
}

async function writeBlob(productId: string, map: PresenceMap): Promise<void> {
  await put(blobPath(productId), JSON.stringify(map), {
    access: "private",
    addRandomSuffix: false,
    allowOverwrite: true,
    contentType: "application/json",
    cacheControlMaxAge: 10,
  });
}

async function readFile(productId: string): Promise<PresenceMap> {
  try {
    return parseMap(await fs.readFile(filePath(productId), "utf8"));
  } catch {
    return {};
  }
}

async function writeFile(productId: string, map: PresenceMap): Promise<void> {
  try {
    await fs.mkdir(dataDir(), { recursive: true });
    await fs.writeFile(filePath(productId), JSON.stringify(map), "utf8");
  } catch {
    /* read-only hosts — memory still holds the row */
  }
}

function mergeMaps(a: PresenceMap, b: PresenceMap): PresenceMap {
  const out: PresenceMap = { ...a };
  for (const [k, v] of Object.entries(b)) {
    const prev = out[k];
    out[k] = prev == null ? v : Math.max(prev, v);
  }
  return prune(out);
}

/** Soft floor so sparse traffic still feels like the preview (3–8, drifts ~20m). */
export function softViewerFloor(productId: string): number {
  const bucket = Math.floor(Date.now() / (20 * 60 * 1000));
  let h = 2166136261;
  const s = `${productId}:${bucket}`;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return 3 + (h >>> 0) % 6;
}

export function displayViewerCount(real: number, productId: string): number {
  const n = Number.isFinite(real) ? Math.max(0, Math.floor(real)) : 0;
  return Math.max(n, softViewerFloor(productId));
}

export async function heartbeatPresence(
  productIdRaw: string,
  visitorIdRaw: string,
): Promise<{ ok: true; count: number; display: number } | { ok: false; error: string }> {
  const productId = safeProductId(productIdRaw);
  const visitorId = (visitorIdRaw || "").trim().slice(0, 80);
  if (!productId) return { ok: false, error: "invalid productId" };
  if (!visitorId || !/^[a-zA-Z0-9_-]+$/.test(visitorId)) {
    return { ok: false, error: "invalid visitorId" };
  }

  const now = Date.now();
  const mem = memory();
  let map = prune(mem.get(productId) || {});

  if (blobEnabled()) {
    map = mergeMaps(map, await readBlob(productId));
  } else {
    map = mergeMaps(map, await readFile(productId));
  }

  map[visitorId] = now;
  map = prune(map, now);
  mem.set(productId, map);

  if (blobEnabled()) {
    try {
      await writeBlob(productId, map);
    } catch {
      /* memory still serves this instance */
    }
  } else {
    await writeFile(productId, map);
  }

  const count = Object.keys(map).length;
  return { ok: true, count, display: displayViewerCount(count, productId) };
}

export async function readPresenceCount(
  productIdRaw: string,
): Promise<{ ok: true; count: number; display: number } | { ok: false; error: string }> {
  const productId = safeProductId(productIdRaw);
  if (!productId) return { ok: false, error: "invalid productId" };

  const mem = memory();
  let map = prune(mem.get(productId) || {});
  if (blobEnabled()) {
    map = mergeMaps(map, await readBlob(productId));
  } else {
    map = mergeMaps(map, await readFile(productId));
  }
  mem.set(productId, map);
  const count = Object.keys(map).length;
  return { ok: true, count, display: displayViewerCount(count, productId) };
}
