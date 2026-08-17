import Link from "next/link";
import { notFound } from "next/navigation";
import { BookmarkletCard } from "@/components/BookmarkletCard";
import { OpenStoreButton } from "@/components/OpenStoreButton";
import { PasteUrlBar } from "@/components/PasteUrlBar";
import { storeById } from "@/lib/stores";

export default async function GoStorePage({
  params,
}: {
  params: Promise<{ storeId: string }>;
}) {
  const { storeId } = await params;
  const store = storeById(storeId);
  if (!store) notFound();

  return (
    <div className="page-wrap py-10">
      <p className="text-[0.72rem] tracking-[0.18em] uppercase text-[var(--muted)]">
        Stay on 배대지
      </p>
      <h1 className="display mt-2 text-4xl">{store.nameEn}</h1>
      <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--muted)]">
        이 화면은 배대지입니다. {store.nameKo}로 가도 여기로 돌아올 수 있게, 먼저 이
        페이지를 열어 두세요. 상품 주소를 복사한 뒤 이 칸에 붙이면 됩니다.
      </p>

      <div
        className="mt-8 p-5"
        style={{ background: store.bg, color: store.fg }}
      >
        <p className="display text-3xl">{store.nameEn}</p>
        <p className="mt-2 text-sm opacity-80">
          {store.nameKo} · {store.blurb}
        </p>
      </div>

      <div className="card mt-4 p-5">
        <OpenStoreButton href={store.href} name={store.nameEn} />
      </div>

      <section className="mt-10">
        <h2 className="display text-2xl">복사한 상품 링크는 여기에</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          {store.nameEn} 탭에서 주소를 복사한 다음, Safari 탭에서 이 화면으로 돌아와
          붙이세요.
        </p>
        <div className="mt-4">
          <PasteUrlBar />
        </div>
      </section>

      <div className="mt-10">
        <BookmarkletCard />
      </div>

      <Link href="/#stores" className="mt-8 inline-block text-sm underline">
        다른 스토어 보기
      </Link>
    </div>
  );
}
