"use client";

import { useEffect, useState } from "react";

export function BookmarkletCard() {
  const [href, setHref] = useState("#");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const origin = window.location.origin;
    setHref(
      `javascript:void(location.href='${origin}/cart?url='+encodeURIComponent(location.href))`,
    );
  }, []);

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section id="bookmarklet" className="card scroll-mt-24 p-5">
      <p className="text-[0.72rem] tracking-[0.18em] uppercase text-[var(--muted)]">
        iPhone · ASOS return
      </p>
      <h2 className="display mt-1 text-2xl">ASOS에서 배대지로 한 번에</h2>
      <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
        ASOS·Zalando 같은 영국 몰에는 우리 사이트로 돌아오는 버튼이 없습니다. Safari
        즐겨찾기에 <strong>배대지에 담기</strong>를 넣어 두면, 상품 페이지에서 그
        즐겨찾기를 누르는 순간 상품 주소가 담긴 채 배대지로 돌아옵니다.
      </p>
      <ol className="mt-4 grid gap-2 text-sm leading-6">
        <li>1. 아래 노란 버튼을 <strong>길게</strong> 누른다</li>
        <li>2. <strong>즐겨찾기에 추가</strong> (또는 북마크 추가)</li>
        <li>3. ASOS에서 상품을 연 다음, 책갈피 → <strong>배대지에 담기</strong></li>
      </ol>
      <div className="mt-5 flex flex-wrap gap-3">
        <a
          href={href}
          className="btn btn-gold"
          onClick={(e) => e.preventDefault()}
        >
          배대지에 담기
        </a>
        <button type="button" className="btn btn-ghost" onClick={copyCode}>
          {copied ? "복사됨" : "코드 복사"}
        </button>
      </div>
      <p className="mt-3 text-sm text-[var(--muted)]">
        버튼을 그냥 누르면 안 됩니다. 길게 눌러 즐겨찾기에 넣어야 ASOS에서 쓸 수
        있습니다. 길게 누르기가 안 되면 코드 복사 후, 아무 북마크나 추가하고 주소를
        그 코드로 바꾸세요.
      </p>
    </section>
  );
}
