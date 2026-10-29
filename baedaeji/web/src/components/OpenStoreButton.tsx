"use client";

import { markStoreOpened } from "@/components/ReturnCoach";

export function OpenStoreButton({
  href,
  name,
}: {
  href: string;
  name: string;
}) {
  function openWithoutLeaving() {
    markStoreOpened(name);
    const child = window.open(href, "_blank");
    if (child) {
      try {
        child.opener = null;
      } catch {
        /* ignore */
      }
    }
  }

  return (
    <div className="grid gap-3">
      <button type="button" className="btn min-h-[52px] w-full" onClick={openWithoutLeaving}>
        {name} 새 창으로 열기
      </button>
      <p className="text-sm leading-6 text-[var(--muted)]">
        아이폰에서 배너만 누르면 배대지가 사라집니다. 이 화면은 배대지입니다. ASOS는
        아래를 <strong>길게 눌러 → 새로운 탭에서 열기</strong>로 여세요. 짧게 누르면
        안 됩니다.
      </p>
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="btn btn-ghost min-h-[52px] w-full"
        onClick={(event) => {
          event.preventDefault();
          openWithoutLeaving();
        }}
      >
        길게 눌러 새 탭에서 열기
      </a>
    </div>
  );
}
