const DB = "swingtwin-clips-v1";
const STORE = "clips";

type ClipRow = { key: string; blob: Blob; name: string; updatedAt: string };

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB, 1);
    req.onerror = () => reject(req.error);
    req.onupgradeneeded = () => {
      req.result.createObjectStore(STORE, { keyPath: "key" });
    };
    req.onsuccess = () => resolve(req.result);
  });
}

export async function saveClip(key: "user" | "tour", file: File) {
  const db = await openDb();
  const row: ClipRow = {
    key,
    blob: file,
    name: file.name,
    updatedAt: new Date().toISOString(),
  };
  return new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(row);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function loadClip(key: "user" | "tour") {
  const db = await openDb();
  return new Promise<ClipRow | null>((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).get(key);
    req.onsuccess = () => resolve((req.result as ClipRow) ?? null);
    req.onerror = () => reject(req.error);
  });
}

export async function clipObjectUrl(key: "user" | "tour") {
  const row = await loadClip(key);
  if (!row) return null;
  return { url: URL.createObjectURL(row.blob), name: row.name };
}
