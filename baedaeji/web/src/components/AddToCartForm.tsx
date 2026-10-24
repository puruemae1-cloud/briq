"use client";

import { useActionState, useEffect, useRef, useState } from "react";
import { addCartItemAction, lookupProductAction } from "@/app/actions/cart";
import { enabledStores } from "@/lib/stores";
import { isHttpUrl } from "@/lib/product-input";

const initial = { error: "" };

function formatGbp(n: number) {
  return `£${n.toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

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
  const [gbpPrice, setGbpPrice] = useState<number | null>(null);
  const [priceNote, setPriceNote] = useState("");
  const [previewing, setPreviewing] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const seq = useRef(0);
  const stores = enabledStores();

  async function runLookup(raw: string, shop = storeId) {
    const text = raw.trim();
    if (!text) return;
    const n = ++seq.current;
    setPreviewing(true);
    try {
      const found = await lookupProductAction(text, shop);
      if (n !== seq.current) return;
      setTitle((prev) => prev || found.title);
      setStoreName(found.storeName);
      setGbpPrice(found.gbpPrice);
      setPriceNote(
        found.gbpPrice
          ? found.priceSource === "search"
            ? `${found.storeName} 검색 결과 가격입니다. 결제 전 운영자가 한 번 더 확인합니다.`
            : `${found.storeName}에서 확인한 가격입니다.`
          : "가격을 자동으로 못 찾아, 운영자가 확인한 뒤 견적이 나갑니다.",
      );
    } catch {
      if (n !== seq.current) return;
      setGbpPrice(null);
      setPriceNote("가격을 자동으로 못 찾아, 운영자가 확인한 뒤 견적이 나갑니다.");
    } finally {
      if (n === seq.current) setPreviewing(false);
    }
  }

  useEffect(() => {
    if (presetUrl.trim()) void runLookup(presetUrl, defaultStoreId);
    // initial paste from homepage / login redirect
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <form action={action} className="card grid gap-4 p-5 md:grid-cols-2">
      <label className="field md:col-span-2">
        <span>상품 이름 또는 링크</span>
        <textarea
          ref={inputRef}
          name="url"
          required
          rows={3}
          defaultValue={presetUrl}
          placeholder="ASOS DESIGN double layer minimal halter neck top in cream"
          autoCapitalize="off"
          autoCorrect="off"
          spellCheck={false}
          className="min-h-[72px]"
          onBlur={(e) => void runLookup(e.target.value)}
          onPaste={(e) => {
            const text = e.clipboardData.getData("text");
            if (text.trim()) window.setTimeout(() => void runLookup(text), 0);
          }}
        />
        <em className="text-[0.8rem] not-italic text-[var(--muted)]">
          {previewing
            ? "상품과 가격을 찾는 중…"
            : storeName
              ? `${storeName}로 인식했습니다. GBP는 고객이 넣을 수 없고 스토어에서 채웁니다.`
              : "이름이나 링크를 붙여넣으면 가격을 찾아 넣습니다. GBP는 직접 입력하지 않습니다."}
        </em>
      </label>
      <label className="field">
        <span>검색할 쇼핑몰</span>
        <select
          name="storeId"
          value={storeId}
          onChange={(e) => {
            const next = e.target.value;
            setStoreId(next);
            const raw = inputRef.current?.value || "";
            if (raw.trim() && !isHttpUrl(raw)) void runLookup(raw, next);
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
        <span>GBP 가격</span>
        <input
          readOnly
          value={gbpPrice != null ? formatGbp(gbpPrice) : ""}
          placeholder={previewing ? "찾는 중…" : "붙여넣으면 자동 입력"}
        />
        <em className="text-[0.8rem] not-italic text-[var(--muted)]">
          {priceNote || "고객이 금액을 바꿀 수 없습니다."}
        </em>
      </label>
      <label className="field md:col-span-2">
        <span>상품명</span>
        <input
          name="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="비워 두면 찾은 이름을 씁니다"
        />
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
        <button className="btn" disabled={pending || previewing} type="submit">
          {pending ? "담는 중…" : previewing ? "가격 찾는 중…" : "장바구니에 담기"}
        </button>
      </div>
    </form>
  );
}
