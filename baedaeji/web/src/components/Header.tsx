import Link from "next/link";
import { logoutAction } from "@/app/actions/auth";
import type { User } from "@/lib/types";

export function Header({ user }: { user: User | null }) {
  return (
    <header className="sticky top-0 z-30 border-b border-[var(--line)] bg-[var(--navy)] text-[#f7f4ee]">
      <div className="page-wrap flex items-center justify-between gap-4 py-3.5">
        <Link href="/" className="display text-[1.35rem] tracking-[0.12em]">
          배대지
        </Link>
        <nav className="flex items-center gap-3 overflow-x-auto whitespace-nowrap text-[0.72rem] tracking-[0.1em] uppercase sm:gap-4 sm:text-[0.78rem] sm:tracking-[0.12em]">
          <Link href="/#bookmarklet" className="opacity-80 hover:opacity-100">
            ASOS에서 돌아오기
          </Link>
          <Link href="/#paste" className="opacity-80 hover:opacity-100">
            URL 붙여넣기
          </Link>
          <Link href="/#stores" className="opacity-80 hover:opacity-100">
            Stores
          </Link>
          <Link href="/guide" className="opacity-80 hover:opacity-100">
            이용안내
          </Link>
          {user ? (
            <>
              <Link href="/cart" className="opacity-80 hover:opacity-100">
                장바구니
              </Link>
              <Link href="/orders" className="opacity-80 hover:opacity-100">
                주문
              </Link>
              <Link href="/account" className="opacity-80 hover:opacity-100">
                내정보
              </Link>
              {user.role === "admin" ? (
                <Link href="/admin" className="text-[var(--gold)]">
                  운영
                </Link>
              ) : null}
              <form action={logoutAction}>
                <button type="submit" className="opacity-80 hover:opacity-100">
                  로그아웃
                </button>
              </form>
            </>
          ) : (
            <>
              <Link href="/login" className="opacity-80 hover:opacity-100">
                로그인
              </Link>
              <Link href="/register" className="bg-[#f7f4ee] px-3 py-2 text-[var(--navy)]">
                회원가입
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="mt-20 border-t border-[var(--line)] py-10 text-[0.82rem] text-[var(--muted)]">
      <div className="page-wrap flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <p className="display text-lg text-[var(--ink)]">배대지</p>
        <div className="max-w-xl leading-6">
          영국 쇼핑몰 구매대행 · 배송대행 베타. 해외몰 장바구니는 읽지 않습니다. 상품
          URL을 이 사이트에 담아 견적을 받은 뒤 원화로 결제하세요. 네이버페이 등
          간편결제는 가맹 심사 후 연결됩니다. briq.kr과 별도 서비스입니다.
        </div>
      </div>
    </footer>
  );
}
