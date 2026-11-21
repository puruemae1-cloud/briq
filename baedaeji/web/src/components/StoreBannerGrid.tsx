"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { enabledStores } from "@/lib/stores";

export function StoreBannerGrid() {
  const stores = enabledStores();
  return (
    <section id="stores" className="scroll-mt-20">
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <p className="text-[0.72rem] tracking-[0.2em] uppercase text-[var(--muted)]">
            UK Stores
          </p>
          <h2 className="display mt-1 text-3xl">스토어 배너</h2>
        </div>
        <p className="hidden max-w-xs text-right text-sm leading-6 text-[var(--muted)] sm:block">
          배너를 눌러도 배대지를 떠나지 않습니다. 다음 화면에서 ASOS를 새 탭으로
          여세요.
        </p>
      </div>
      <p className="mb-4 text-sm leading-6 text-[var(--muted)] sm:hidden">
        배너를 누르면 배대지 안내 화면이 나옵니다. ASOS는 그 다음 화면에서 길게 눌러
        새 탭으로 여세요. 짧게 누르면 배대지가 사라집니다.
      </p>
      <div className="grid gap-3 md:grid-cols-2">
        {stores.map((store, i) => (
          <Link
            key={store.id}
            href={`/go/${store.id}`}
            className="store-banner"
            style={{ background: store.bg, color: store.fg }}
          >
            <span className="store-index">
              {String(i + 1).padStart(2, "0")} / UK
            </span>
            <div className="relative z-[1]">
              <p
                className="display text-[1.85rem] leading-none sm:text-[2.15rem]"
                style={{ color: store.fg }}
              >
                {store.nameEn}
              </p>
              <p className="mt-2 text-[0.8rem] tracking-[0.12em] opacity-80">
                {store.nameKo} · {store.blurb}
              </p>
            </div>
            <span
              className="relative z-[1] inline-flex items-center gap-1 border px-3 py-2 text-[0.72rem] tracking-[0.14em] uppercase"
              style={{ borderColor: store.accent, color: store.fg }}
            >
              배대지에서 열기
              <ArrowUpRight size={14} />
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}
