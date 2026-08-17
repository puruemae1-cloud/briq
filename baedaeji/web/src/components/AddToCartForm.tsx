"use client";

import { useActionState, useState } from "react";
import { addCartItemAction, previewUrlAction } from "@/app/actions/cart";

const initial = { error: "" };

export function AddToCartForm({ presetUrl = "" }: { presetUrl?: string }) {
  const [state, action, pending] = useActionState(addCartItemAction, initial);
  const [title, setTitle] = useState("");
  const [storeName, setStoreName] = useState("");
  const [previewing, setPreviewing] = useState(false);

  async function onUrlBlur(url: string) {
    if (!url.trim()) return;
    setPreviewing(true);
    try {
      const preview = await previewUrlAction(url.trim());
      setTitle((prev) => prev || preview.title);
      setStoreName(preview.storeName);
    } catch {
      setStoreName("");
    } finally {
      setPreviewing(false);
    }
  }

  return (
    <form action={action} className="card grid gap-4 p-5 md:grid-cols-2">
      <label className="field md:col-span-2">
        <span>상품 URL</span>
        <input
          name="url"
          required
          defaultValue={presetUrl}
          placeholder="https://www.selfridges.com/..."
          onBlur={(e) => onUrlBlur(e.target.value)}
        />
        <em className="text-[0.8rem] not-italic text-[var(--muted)]">
          {previewing
            ? "상품 정보를 읽는 중…"
            : storeName
              ? `${storeName} 링크로 인식했습니다.`
              : "메인 배너 스토어의 상품 페이지만 가능합니다."}
        </em>
      </label>
      <label className="field md:col-span-2">
        <span>상품명</span>
        <input
          name="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="자동으로 채워지지 않으면 직접 입력"
        />
      </label>
      <label className="field">
        <span>GBP 가격 (선택)</span>
        <input name="gbpPrice" inputMode="decimal" placeholder="예: 89.00" />
      </label>
      <label className="field">
        <span>수량</span>
        <input name="qty" type="number" min={1} defaultValue={1} />
      </label>
      <label className="field">
        <span>사이즈</span>
        <input name="size" placeholder="UK 8 / M" />
      </label>
      <label className="field">
        <span>색상</span>
        <input name="color" placeholder="Black" />
      </label>
      <label className="field md:col-span-2">
        <span>메모</span>
        <textarea name="memo" rows={2} placeholder="선물 포장, 대체 사이즈 등" />
      </label>
      {state?.error ? <p className="err md:col-span-2">{state.error}</p> : null}
      <div className="md:col-span-2">
        <button className="btn" disabled={pending} type="submit">
          {pending ? "담는 중…" : "장바구니에 담기"}
        </button>
      </div>
    </form>
  );
}
