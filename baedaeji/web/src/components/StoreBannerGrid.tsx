"use client";

import type { MouseEvent } from "react";
import { ArrowUpRight } from "lucide-react";
import { enabledStores, type StoreBanner } from "@/lib/stores";
import { markStoreOpened } from "@/components/ReturnCoach";

function openStore(event: MouseEvent<HTMLAnchorElement>, store: StoreBanner) {
  event.preventDefault();
  markStoreOpened(store.nameEn);
  window.open(store.href, "_blank", "noopener,noreferrer");
  document.getElementById("paste")?.scrollIntoView({ behavior: "smooth" });
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
          배너를 눌러도 이 화면은 그대로 둡니다. 영국 몰은 새 탭에서 열리고, 상품
          주소는 위에 붙여 넣으면 됩니다.
        </p>
      </div>
      <p className="mb-4 text-sm leading-6 text-[var(--muted)] sm:hidden">
        배너를 누르면 ASOS 등이 새 탭으로 열립니다. 이 배대지 화면은 그대로 있으니,
        상품 주소를 복사한 뒤 탭을 다시 눌러 붙여 넣으세요.
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
            onClick={(event) => openStore(event, store)}
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
              새 탭으로 열기
              <ArrowUpRight size={14} />
            </span>
          </a>
        ))}
      </div>
    </section>
  );
}
