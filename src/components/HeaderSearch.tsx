"use client";

import { useId, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, X } from "lucide-react";
import { buildShopSearchHref } from "@/lib/product-search";

export function HeaderSearch() {
  const router = useRouter();
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) {
      inputRef.current?.focus();
      return;
    }
    router.push(buildShopSearchHref(q));
  }

  return (
    <form
      className="header-search"
      onSubmit={submit}
      role="search"
      aria-label="상품 검색"
    >
      <label className="sr-only" htmlFor={inputId}>
        상품명, 브랜드, 키워드 검색
      </label>
      <button
        type="button"
        className="header-search__trigger"
        aria-label="검색 열기"
        onClick={() => inputRef.current?.focus()}
      >
        <Search className="header-search__icon" size={18} aria-hidden />
      </button>
      <input
        ref={inputRef}
        id={inputId}
        type="search"
        name="q"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="header-search__input"
        placeholder="검색"
        enterKeyHint="search"
        autoComplete="off"
        autoCorrect="off"
        spellCheck={false}
      />
      {query ? (
        <button
          type="button"
          className="header-search__clear"
          aria-label="입력 지우기"
          onClick={() => {
            setQuery("");
            inputRef.current?.focus();
          }}
        >
          <X size={16} />
        </button>
      ) : null}
    </form>
  );
}
