import Link from "next/link";
import { BookmarkletCard } from "@/components/BookmarkletCard";
import { HomeScreenHint } from "@/components/HomeScreenHint";
import { enabledStores } from "@/lib/stores";

export default function GuidePage() {
  const stores = enabledStores();
  return (
    <div className="page-wrap py-12">
      <h1 className="display text-4xl">이용안내</h1>
      <div className="mt-8 grid max-w-3xl gap-6 text-[0.98rem] leading-7">
        <p>
          배대지는 영국 쇼핑몰에서 고른 상품을 한국 고객이 원화로 맡기고, 운영자가
          영국에서 구매해 보내는 서비스입니다. 해외몰 장바구니는 보안상 이 사이트가
          읽을 수 없어, <strong>상품 페이지 URL을 여기에 담는 방식</strong>을 씁니다.
        </p>
        <p>
          ASOS 같은 영국 몰에는 배대지로 돌아오는 버튼이 없습니다. 배너를 눌러도 이
          화면은 남겨 두고 새 탭으로 열고, 아이폰은 Safari 왼쪽 위 뒤로 가기·탭 전환,
          또는 즐겨찾기 「배대지에 담기」를 쓰면 됩니다.
        </p>
        <ol className="grid gap-3">
          <li>1. 메인 배너에서 영국 스토어를 새 탭으로 연다.</li>
          <li>2. 사고 싶은 상품 페이지에서 주소창 URL을 복사한다.</li>
          <li>3. 배대지 탭으로 돌아와 붙여 넣거나, 즐겨찾기 「배대지에 담기」를 누른다.</li>
          <li>4. <strong>견적 확인</strong> — 아직 결제가 아니다.</li>
          <li>5. 견적에 동의하면 결제(현재는 입금 대기). 이후 네이버페이 연결 예정.</li>
        </ol>
        <BookmarkletCard />
        <HomeScreenHint />
        <p>지금은 아래 스토어만 URL을 받을 수 있습니다.</p>
        <ul className="grid gap-1">
          {stores.map((s) => (
            <li key={s.id}>
              {s.nameEn} ({s.nameKo}) — {s.href}
            </li>
          ))}
        </ul>
        <p>
          품절 시 해당 상품은 환불하는 것이 기본입니다. 청약철회·관부가세·통신판매업
          고지는 사업자 준비와 함께 정식 약관으로 붙입니다.
        </p>
        <Link href="/#stores" className="btn w-fit">
          스토어로
        </Link>
      </div>
    </div>
  );
}
