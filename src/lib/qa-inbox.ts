import { get, put } from "@vercel/blob";
import { promises as fs } from "fs";
import path from "path";
import type { QaItem } from "@/lib/qa-store";

type GlobalQa = {
  __briqQaInbox?: QaItem[];
};

const g = globalThis as typeof globalThis & GlobalQa;

const BLOB_PATH = "qa/inbox.json";
const DATA_DIR = process.env.VERCEL
  ? path.join("/tmp", "briq-qa")
  : path.join(process.cwd(), "data");
const DATA_FILE = path.join(DATA_DIR, "qa.json");

function memoryItems(): QaItem[] {
  if (!g.__briqQaInbox) g.__briqQaInbox = [];
  return g.__briqQaInbox;
}

function blobEnabled(): boolean {
  return Boolean(process.env.BLOB_READ_WRITE_TOKEN);
}

function isQaItem(value: unknown): value is QaItem {
  if (!value || typeof value !== "object") return false;
  const row = value as Record<string, unknown>;
  return (
    typeof row.id === "string" &&
    typeof row.productId === "string" &&
    typeof row.productName === "string" &&
    typeof row.authorName === "string" &&
    typeof row.question === "string" &&
    typeof row.createdAt === "string"
  );
}

function parseItems(raw: string): QaItem[] {
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isQaItem);
  } catch {
    return [];
  }
}

async function readFileItems(): Promise<QaItem[]> {
  try {
    return parseItems(await fs.readFile(DATA_FILE, "utf8"));
  } catch {
    return [];
  }
}

async function writeFileItems(items: QaItem[]) {
  try {
    await fs.mkdir(DATA_DIR, { recursive: true });
    await fs.writeFile(DATA_FILE, JSON.stringify(items, null, 2), "utf8");
  } catch {
    /* read-only hosts — memory still holds the row */
  }
}

async function readBlobItems(): Promise<QaItem[]> {
  const result = await get(BLOB_PATH, { access: "private", useCache: false });
  if (!result || result.statusCode !== 200 || !result.stream) return [];
  return parseItems(await new Response(result.stream).text());
}

async function writeBlobItems(items: QaItem[]) {
  await put(BLOB_PATH, JSON.stringify(items), {
    access: "private",
    addRandomSuffix: false,
    allowOverwrite: true,
    contentType: "application/json",
    cacheControlMaxAge: 60,
  });
}

function mergeById(a: QaItem[], b: QaItem[]): QaItem[] {
  const map = new Map<string, QaItem>();
  for (const item of [...a, ...b]) {
    const prev = map.get(item.id);
    const prevStamp = prev?.answeredAt || prev?.createdAt || "";
    const nextStamp = item.answeredAt || item.createdAt;
    if (!prev || nextStamp >= prevStamp) map.set(item.id, item);
  }
  return [...map.values()].sort(
    (x, y) => +new Date(y.createdAt) - +new Date(x.createdAt),
  );
}

async function readDurable(): Promise<QaItem[]> {
  if (blobEnabled()) return readBlobItems();
  return readFileItems();
}

async function writeDurable(items: QaItem[]) {
  if (blobEnabled()) {
    await writeBlobItems(items);
    return;
  }
  await writeFileItems(items);
}

export async function listQa(): Promise<QaItem[]> {
  const stored = await readDurable();
  const merged = mergeById(memoryItems(), stored);
  g.__briqQaInbox = merged;
  return merged;
}

export async function addQa(item: QaItem): Promise<QaItem[]> {
  const current = await listQa();
  const next = mergeById(current, [item]);
  g.__briqQaInbox = next;
  await writeDurable(next);
  return next;
}

export async function answerQa(
  id: string,
  answer: string,
  answeredBy: string,
): Promise<QaItem | null> {
  const current = await listQa();
  const idx = current.findIndex((item) => item.id === id);
  if (idx < 0) return null;
  const now = new Date().toISOString();
  const updated: QaItem = {
    ...current[idx],
    answer,
    answeredAt: now,
    answeredBy,
  };
  const next = [...current];
  next[idx] = updated;
  g.__briqQaInbox = next;
  await writeDurable(next);
  return updated;
}
