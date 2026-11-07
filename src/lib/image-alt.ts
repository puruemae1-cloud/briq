/** Shared helpers so Naver / a11y never see empty img alt text. */

export function imageAlt(
  primary: string | null | undefined,
  fallback = "Briq",
): string {
  const text = (primary || "").replace(/\s+/g, " ").trim();
  return text || fallback;
}

export function productImageAlt(
  nameKo: string | null | undefined,
  detail?: string | null,
): string {
  const name = imageAlt(nameKo, "상품");
  const extra = (detail || "").replace(/\s+/g, " ").trim();
  return extra ? `${name} ${extra}` : name;
}
