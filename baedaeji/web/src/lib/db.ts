import { mkdir, readFile, writeFile } from "fs/promises";
import path from "path";
import type { CartItem, Order, User } from "./types";

export type DB = {
  users: User[];
  carts: Record<string, CartItem[]>;
  orders: Order[];
};

const FILE = path.join(process.cwd(), ".data", "db.json");

const empty = (): DB => ({ users: [], carts: {}, orders: [] });

let queue: Promise<unknown> = Promise.resolve();

async function readDb(): Promise<DB> {
  try {
    const raw = await readFile(FILE, "utf8");
    const parsed = JSON.parse(raw) as Partial<DB>;
    return {
      users: parsed.users ?? [],
      carts: parsed.carts ?? {},
      orders: parsed.orders ?? [],
    };
  } catch {
    return empty();
  }
}

async function writeDb(db: DB) {
  await mkdir(path.dirname(FILE), { recursive: true });
  await writeFile(FILE, JSON.stringify(db, null, 2), "utf8");
}

export function updateDb<T>(fn: (db: DB) => Promise<T> | T): Promise<T> {
  const run = queue.then(async () => {
    const db = await readDb();
    const result = await fn(db);
    await writeDb(db);
    return result;
  });
  queue = run.then(
    () => undefined,
    () => undefined,
  );
  return run;
}

export function readOnlyDb(): Promise<DB> {
  return queue.then(() => readDb());
}
