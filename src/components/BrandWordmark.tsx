type BrandWordmarkProps = {
  nameEn: string;
  className?: string;
};

/**
 * Luxury brand wordmark for shop heroes.
 * Uses per-letter flex spacing (not CSS/SVG letter-spacing) so iOS Safari
 * never renders the trailing “?” replacement glyph after the last letter.
 */
export function BrandWordmark({ nameEn, className }: BrandWordmarkProps) {
  const chars = nameEn.toUpperCase().split("");

  return (
    <p
      className={["brand-wordmark", className].filter(Boolean).join(" ")}
      aria-label={nameEn}
    >
      {chars.map((ch, i) =>
        ch === " " ? (
          <span key={`sp-${i}`} className="brand-wordmark__word-gap" aria-hidden />
        ) : (
          <span key={`ch-${i}`} className="brand-wordmark__letter">
            {ch}
          </span>
        ),
      )}
    </p>
  );
}
