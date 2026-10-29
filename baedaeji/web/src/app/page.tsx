import Link from "next/link";
import { BookmarkletCard } from "@/components/BookmarkletCard";
import { HomePasteQuote } from "@/components/HomePasteQuote";
import { HomeScreenHint } from "@/components/HomeScreenHint";
import { StoreBannerGrid } from "@/components/StoreBannerGrid";
import { formatKrw, getGbpKrw, quoteKrw, feePolicySummary } from "@/lib/fx";
import { FEE } from "@/lib/types";

export default async function HomePage() {
  const fx = await getGbpKrw();
  const sample = quoteKrw({ goodsGbp: 10, gbpKrw: fx.gbpKrw });

  return (
    <>
      <section className="bg-[var(--navy)] text-[#f7f4ee]">
        <div className="page-wrap grid gap-10 py-16 md:grid-cols-[1.3fr_0.9fr] md:py-24">
          <div>
            <p className="text-[0.72rem] tracking-[0.22em] uppercase text-[var(--gold)]">
              UK → KR · Purchase & Forwarding
            </p>
            <h1 className="display mt-4 text-[2.7rem] leading-[1.05] sm:text-[4.2rem]">
              영국에서 고르고
              <br />
              한국에서 맡기다
            </h1>
            <p className="mt-6 max-w-xl text-[1.02rem] leading-7 text-[#d7d2c8]">
              아래 영국 스토어에서 상품을 고른 뒤, 상품 이름이나 링크를 배대지에 담으세요.
              오늘 환율로 견적을 내고 원화로 결제하면 영국에서 대신 사서 보냅니다.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/#paste" className="btn btn-gold">
                이름·링크 붙여넣기
              </Link>
              <Link href="/#stores" className="btn btn-ghost border-[#f7f4ee]/30 text-[#f7f4ee]">
                스토어 보기
              </Link>
            </div>
          </div>
          <div className="card bg-[#f7f4ee] p-6 text-[var(--ink)]">
            <p className="text-[0.72rem] tracking-[0.18em] uppercase text-[var(--muted)]">
              Today · GBP → KRW
            </p>
            <p className="display mt-2 text-4xl">£1 = {formatKrw(fx.gbpKrw)}</p>
            <p className="mt-1 text-sm text-[var(--muted)]">
              {fx.source} · 환전 마진 {Math.round(FEE.fxMargin * 100)}%
            </p>
            <p className="mt-2 text-sm leading-6">{feePolicySummary()}</p>
            <p className="mt-2 text-sm leading-6">
              예: £10 상품 1개 → 약 {formatKrw(sample.totalKrw)} (관부가세 제외)
            </p>
            <ol className="mt-6 grid gap-3 text-sm leading-6">
              <li>1. 배너를 누르면 배대지 안내 화면이 남는다</li>
              <li>2. ASOS는 길게 눌러 새 탭으로 연다</li>
              <li>3. 상품 이름이나 주소를 복사하고 배대지 탭으로 돌아와 붙인다</li>
              <li>4. 즐겨찾기 「배대지에 담기」면 한 번에 돌아온다</li>
            </ol>
          </div>
        </div>
      </section>

      <section
        id="paste"
        className="scroll-mt-24 border-y border-[var(--line)] bg-[var(--bg-deep)] py-10"
      >
        <div className="page-wrap">
          <p className="text-[0.72rem] tracking-[0.2em] uppercase text-[var(--muted)]">
            Paste name or URL
          </p>
          <h2 className="display mt-1 text-3xl">복사한 이름이나 링크는 여기에</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--muted)]">
            ASOS 상품 이름을 그대로 붙여넣어도 됩니다. £ 가격을 찾아 오늘 환율로 원화
            견적을 바로 보여 줍니다.
          </p>
          <div className="mt-5 max-w-3xl">
            <HomePasteQuote gbpKrw={fx.gbpKrw} fxSource={fx.source} />
          </div>
        </div>
      </section>

      <div className="page-wrap py-14">
        <StoreBannerGrid />

        <div className="mt-10 grid gap-4 md:grid-cols-2">
          <BookmarkletCard />
          <HomeScreenHint />
        </div>

        <section className="mt-16 grid gap-6 md:grid-cols-3">
          {[
            {
              t: "이름만 담아도 됩니다",
              d: "해외몰 장바구니는 이 사이트가 읽을 수 없습니다. 상품 이름이나 링크를 배대지 장바구니에 넣는 것이 주문입니다.",
            },
            {
              t: "견적 후 결제",
              d: "환율·배송·카드 수수료를 보여 준 뒤 결제합니다. 대행은 무료, 관부가세는 통관 시 고객이 직접 납부합니다.",
            },
            {
              t: "영국에서 사람이 삽니다",
              d: "결제되면 운영자 화면에 고객별 상품 리스트가 뜹니다. 영국 몰 자동 로그인은 하지 않습니다.",
            },
          ].map((item) => (
            <article key={item.t} className="card p-5">
              <h3 className="display text-2xl">{item.t}</h3>
              <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{item.d}</p>
            </article>
          ))}
        </section>
      </div>
    </>
  );
}
