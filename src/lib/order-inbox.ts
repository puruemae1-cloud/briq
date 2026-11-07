import { promises as fs } from "fs";
import path from "path";
import type { MemberOrder } from "@/lib/orders";

type GlobalInbox = {
  __briqOrdersInbox?: MemberOrder[];
};

const g = globalThis as typeof globalThis & GlobalInbox;

const DATA_DIR = process.env.VERCEL
  ? path.join("/tmp", "briq-orders")
  : path.join(process.cwd(), "data");
const DATA_FILE = path.join(DATA_DIR, "orders.json");

function memoryOrders(): MemberOrder[] {
  if (!g.__briqOrdersInbox) g.__briqOrdersInbox = [];
  return g.__briqOrdersInbox;
}

async function readFileOrders(): Promise<MemberOrder[]> {
  try {
    const raw = await fs.readFile(DATA_FILE, "utf8");
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (row): row is MemberOrder =>
        Boolean(row && typeof row === "object" && typeof (row as MemberOrder).id === "string"),
    );
  } catch {
    return [];
  }
}

async function writeFileOrders(orders: MemberOrder[]) {
  try {
    await fs.mkdir(DATA_DIR, { recursive: true });
    await fs.writeFile(DATA_FILE, JSON.stringify(orders, null, 2), "utf8");
  } catch {
    /* read-only hosts — memory still holds the row */
  }
}

function mergeById(a: MemberOrder[], b: MemberOrder[]): MemberOrder[] {
  const map = new Map<string, MemberOrder>();
  for (const order of [...a, ...b]) {
    const prev = map.get(order.id);
    if (!prev || +new Date(order.updatedAt) >= +new Date(prev.updatedAt)) {
      map.set(order.id, order);
    }
  }
  return [...map.values()].sort(
    (x, y) => +new Date(y.createdAt) - +new Date(x.createdAt),
  );
}

export async function listInboxOrders(): Promise<MemberOrder[]> {
  const file = await readFileOrders();
  const merged = mergeById(memoryOrders(), file);
  g.__briqOrdersInbox = merged;
  return merged;
}

export async function upsertInboxOrder(order: MemberOrder): Promise<MemberOrder[]> {
  const current = await listInboxOrders();
  const next = mergeById(current, [order]);
  g.__briqOrdersInbox = next;
  await writeFileOrders(next);
  return next;
}

export async function patchInboxOrder(
  orderId: string,
  patch: Partial<MemberOrder>,
): Promise<MemberOrder | null> {
  const current = await listInboxOrders();
  const idx = current.findIndex((o) => o.id === orderId);
  if (idx < 0) return null;
  const updated: MemberOrder = {
    ...current[idx],
    ...patch,
    id: current[idx].id,
    updatedAt: new Date().toISOString(),
  };
  const next = [...current];
  next[idx] = updated;
  g.__briqOrdersInbox = next;
  await writeFileOrders(next);
  return updated;
}
