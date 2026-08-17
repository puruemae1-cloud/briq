"use client";

import { useActionState, useState } from "react";
import { addCartItemAction, previewUrlAction } from "@/app/actions/cart";
import { enabledStores } from "@/lib/stores";
import { isHttpUrl } from "@/lib/product-input";

const initial = { error: "" };

export function AddToCartForm({
  presetUrl = "",
  defaultStoreId = "asos",
}: {
  presetUrl?: string;
  defaultStoreId?: string;
}) {
  const [state, action, pending] = useActionState(addCartItemAction, initial);
  const [title, setTitle] = useState(isHttpUrl(presetUrl) ? "" : presetUrl.trim());
  const [storeId, setStoreId] = useState(defaultStoreId);
  const [storeName, setStoreName] = useState("");
  const [previewing, setPreviewing] = useState(false);
  const stores = enabledStores();
  const selected = stores.find((s) => s.id === storeId) ?? stores[0];

  async function onProductBlur(raw: string) {
    const text = raw.trim();
    if (!text) return;
    if (!isHttpUrl(text)) {
      setTitle((prev) => prev || text);
      setStoreName(selected?.nameEn ?? "ASOS");
      return;
    }
    setPreviewing(true);
    try {
      const preview = await previewUrlAction(text);
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
        <span>상품 이름 또는 링크</span>
        <textarea
          name="url"
          required
          rows={3}
          defaultValue={presetUrl}
          placeholder="ASOS DESIGN double layer minimal halter neck top in cream"
          autoCapitalize="off"
          autoCorrect="off"
          spellCheck={false}
          className="min-h-[72px]"
          onBlur={(e) => onProductBlur(e.target.value)}
        />
        <em className="text-[0.8rem] not-italic text-[var(--muted)]">
          {previewing
            ? "상품 정보를 읽는 중…"
            : storeName
              ? `${storeName}로 인식했습니다. 이름만 넣으면 그 스토어에서 검색합니다.`
              : "ASOS에서 복사한 상품 이름만 붙여넣어도 됩니다. 링크가 있으면 링크를 넣으세요."}
        </em>
      </label>
      <label className="field">
        <span>검색할 쇼핑몰</span>
        <select
          name="storeId"
          value={storeId}
          onChange={(e) => {
            setStoreId(e.target.value);
            const next = stores.find((s) => s.id === e.target.value);
            if (next && !isHttpUrl(presetUrl)) setStoreName(next.nameEn);
          }}
        >
          {stores.map((s) => (
            <option key={s.id} value={s.id}>
              {s.nameEn} ({s.nameKo})
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>상품명</span>
        <input
          name="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="비워 두면 위에 붙인 이름을 씁니다"
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
