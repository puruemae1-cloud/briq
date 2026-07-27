import AsyncStorage from "@react-native-async-storage/async-storage";
import { useEffect, useMemo, useState } from "react";
import {
  getProduct,
  type Product,
  type ProductVariant,
} from "./data/products";

type StoredLine = {
  productId: string;
  variantId?: string;
  qty: number;
};

export type CartItem = {
  product: Product;
  variant?: ProductVariant;
  qty: number;
};

const KEY = "briq-cart-v3";

let memory: StoredLine[] = [];
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

function lineKey(productId: string, variantId?: string) {
  return variantId ? `${productId}::${variantId}` : productId;
}

function hydrate(lines: StoredLine[]): CartItem[] {
  const result: CartItem[] = [];
  for (const line of lines) {
    const product = getProduct(line.productId);
    if (!product) continue;
    const variant = line.variantId
      ? product.variants?.find((v) => v.id === line.variantId)
      : undefined;
    result.push({ product, variant, qty: line.qty });
  }
  return result;
}

async function load() {
  try {
    const raw = await AsyncStorage.getItem(KEY);
    memory = raw ? (JSON.parse(raw) as StoredLine[]) : [];
    emit();
  } catch {
    memory = [];
  }
}

async function save(items: StoredLine[]) {
  memory = items;
  emit();
  await AsyncStorage.setItem(KEY, JSON.stringify(items));
}

load();

export function useCart() {
  const [, bump] = useState(0);

  useEffect(() => {
    const l = () => bump((n) => n + 1);
    listeners.add(l);
    return () => {
      listeners.delete(l);
    };
  }, []);

  const items = useMemo(() => hydrate(memory), [memory, bump]);

  return useMemo(
    () => ({
      items,
      count: items.reduce((s, i) => s + i.qty, 0),
      subtotal: items.reduce((s, i) => {
        const unit = i.variant?.price ?? i.product.price;
        return s + unit * i.qty;
      }, 0),
      add: (product: Product, variant?: ProductVariant) => {
        const key = lineKey(product.id, variant?.id);
        const existing = memory.find(
          (i) => lineKey(i.productId, i.variantId) === key,
        );
        if (existing) {
          void save(
            memory.map((i) =>
              lineKey(i.productId, i.variantId) === key
                ? { ...i, qty: i.qty + 1 }
                : i,
            ),
          );
        } else {
          void save([
            ...memory,
            { productId: product.id, variantId: variant?.id, qty: 1 },
          ]);
        }
      },
      setQty: (productId: string, qty: number, variantId?: string) => {
        const key = lineKey(productId, variantId);
        void save(
          qty <= 0
            ? memory.filter((i) => lineKey(i.productId, i.variantId) !== key)
            : memory.map((i) =>
                lineKey(i.productId, i.variantId) === key
                  ? { ...i, qty }
                  : i,
              ),
        );
      },
      clear: () => void save([]),
    }),
    [items],
  );
}
