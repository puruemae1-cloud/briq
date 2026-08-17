"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const KEY = "baedaeji:lastStore";
const EVENT = "baedaeji:store-opened";

export function markStoreOpened(name: string) {
  sessionStorage.setItem(KEY, name);
  window.dispatchEvent(new Event(EVENT));
}

export function ReturnCoach() {
  const [store, setStore] = useState<string | null>(null);

  useEffect(() => {
    const read = () => setStore(sessionStorage.getItem(KEY));
    read();
    window.addEventListener(EVENT, read);
    return () => window.removeEventListener(EVENT, read);
  }, []);

  if (!store) return null;

  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-[var(--line)] bg-[var(--navy)] px-4 py-3 text-[#f7f4ee] shadow-[0_-12px_40px_rgba(14,26,43,0.25)]">
      <div className="page-wrap flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm leading-6">
          <strong>{store}</strong>에는 배대지로 돌아오는 버튼이 없습니다. 상품 주소를
          복사한 뒤 Safari <strong>왼쪽 위 ←</strong> 또는 <strong>탭 전환</strong>으로
          이 화면으로 돌아오세요.
        </p>
        <Link href="/#paste" className="btn btn-gold shrink-0">
          붙여넣기 칸으로
        </Link>
      </div>
    </div>
  );
}
