import Link from "next/link";
import { BookmarkletCard } from "@/components/BookmarkletCard";
import { HomeScreenHint } from "@/components/HomeScreenHint";
import { PasteUrlBar } from "@/components/PasteUrlBar";
import { StoreBannerGrid } from "@/components/StoreBannerGrid";
import { getGbpKrw } from "@/lib/fx";

export default async function HomePage() {
  const fx = await getGbpKrw();

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
              아래 영국 스토어에서 상품을 고른 뒤, 주소창 링크를 배대지에 담으세요.
              오늘 환율로 견적을 내고 원화로 결제하면 영국에서 대신 사서 보냅니다.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/#paste" className="btn btn-gold">
                URL 붙여넣기
              </Link>
              <Link href="/#stores" className="btn btn-ghost border-[#f7f4ee]/30 text-[#f7f4ee]">
                스토어 보기
              </Link>
            </div>
          </div>
          <div className="card bg-[#f7f4ee] p-6 text-[var(--ink)]">
            <p className="text-[0.72rem] tracking-[0.18em] uppercase text-[var(--muted)]">
              Today · GBP
            </p>
            <p className="display mt-2 text-4xl">{fx.gbpKrw.toLocaleString("en-US")}</p>
            <p className="mt-1 text-sm text-[var(--muted)]">원 · {fx.source}</p>
            <ol className="mt-6 grid gap-3 text-sm leading-6">
              <li>1. 배너를 누르면 Safari가 ASOS를 새 탭으로 연다</li>
              <li>2. 상품 페이지에서 주소를 복사한다</li>
              <li>3. Safari 탭에서 배대지로 돌아와 붙여 넣는다</li>
              <li>4. 또는 즐겨찾기 「배대지에 담기」로 한 번에 돌아온다</li>
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
            Paste product URL
          </p>
          <h2 className="display mt-1 text-3xl">복사한 상품 링크는 여기에</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--muted)]">
            영국 몰 주소창에서 복사한 뒤, 아래 칸을 길게 눌러 붙여넣기 하세요. 로그인되어
            있지 않으면 로그인 화면으로 이동합니다.
          </p>
          <div className="mt-5 max-w-3xl">
            <PasteUrlBar />
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
              t: "링크만 담으면 됩니다",
              d: "해외몰 장바구니는 이 사이트가 읽을 수 없습니다. 상품 URL을 배대지 장바구니에 넣는 것이 주문입니다.",
            },
            {
              t: "견적 후 결제",
              d: "환율·대행 수수료·예상 배송비를 보여 준 뒤 결제합니다. 첫 단계는 결제가 아니라 견적 확인입니다.",
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
