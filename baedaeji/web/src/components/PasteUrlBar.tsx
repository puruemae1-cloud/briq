export function PasteUrlBar({
  variant = "light",
  storeId = "asos",
}: {
  variant?: "light" | "dark";
  storeId?: string;
}) {
  const dark = variant === "dark";
  return (
    <form action="/cart" method="get" className="grid gap-3 sm:grid-cols-[1fr_auto]">
      <label className="sr-only" htmlFor="product-url">
        상품 이름 또는 링크
      </label>
      <input type="hidden" name="store" value={storeId} />
      <input
        id="product-url"
        name="url"
        type="text"
        autoCapitalize="off"
        autoCorrect="off"
        spellCheck={false}
        required
        placeholder="ASOS DESIGN double layer minimal halter neck top in cream"
        className={
          dark
            ? "min-h-[52px] w-full border border-[#f7f4ee]/25 bg-[#0e1a2b] px-4 text-[#f7f4ee] placeholder:text-[#f7f4ee]/50"
            : "min-h-[52px] w-full border border-[var(--line)] bg-white px-4"
        }
      />
      <button className="btn min-h-[52px] whitespace-nowrap" type="submit">
        여기에 붙여넣기
      </button>
    </form>
  );
}
