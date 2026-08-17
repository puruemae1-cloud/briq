export function PasteUrlBar({
  variant = "light",
}: {
  variant?: "light" | "dark";
}) {
  const dark = variant === "dark";
  return (
    <form action="/cart" method="get" className="grid gap-3 sm:grid-cols-[1fr_auto]">
      <label className="sr-only" htmlFor="product-url">
        상품 URL
      </label>
      <input
        id="product-url"
        name="url"
        inputMode="url"
        autoCapitalize="off"
        autoCorrect="off"
        spellCheck={false}
        required
        placeholder="복사한 상품 링크를 여기에 붙여 넣으세요"
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
