"use client";

import { ArrowUpRight } from "lucide-react";
import { enabledStores, type StoreBanner } from "@/lib/stores";
import { markStoreOpened } from "@/components/ReturnCoach";

function onStoreClick(store: StoreBanner) {
  markStoreOpened(store.nameEn);
}

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
          배너는 Safari가 직접 새 탭으로 엽니다. 팝업으로 열면 아이폰에서 ASOS 홈이
          빈 화면이 될 수 있습니다.
        </p>
      </div>
      <p className="mb-4 text-sm leading-6 text-[var(--muted)] sm:hidden">
        배너를 누르면 ASOS가 Safari 탭으로 열립니다. 상품 주소를 복사한 뒤 배대지
        탭으로 돌아와 붙여 넣으세요.
      </p>
      <div className="grid gap-3 md:grid-cols-2">
        {stores.map((store, i) => (
          <a
            key={store.id}
            href={store.href}
            target="_blank"
            rel="noopener noreferrer"
            className="store-banner"
            style={{ background: store.bg, color: store.fg }}
            onClick={() => onStoreClick(store)}
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
              Safari에서 열기
              <ArrowUpRight size={14} />
            </span>
          </a>
        ))}
      </div>
    </section>
  );
}
