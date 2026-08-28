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
  const words = nameEn.toUpperCase().split(/\s+/).filter(Boolean);

  return (
    <p
      className={["brand-wordmark", className].filter(Boolean).join(" ")}
      aria-label={nameEn}
    >
      {words.map((word, wi) => (
        <span key={word} className="brand-wordmark__word">
          {word.split("").map((ch, ci) => (
            <span key={`${wi}-${ci}`} className="brand-wordmark__letter">
              {ch}
            </span>
          ))}
        </span>
      ))}
    </p>
  );
}
