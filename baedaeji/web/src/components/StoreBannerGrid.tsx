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
          배너를 누르면 영국 쇼핑몰이 새 탭에서 열립니다. 사고 싶은 상품 페이지 URL을
          복사해 장바구니에 붙여 넣으세요.
        </p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {stores.map((store, i) => (
          <a
            key={store.id}
            href={store.href}
            target="_blank"
            rel="noopener noreferrer"
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
              스토어 열기
              <ArrowUpRight size={14} />
            </span>
          </a>
        ))}
      </div>
    </section>
  );
}
