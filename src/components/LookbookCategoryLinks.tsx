import Link from "next/link";
import type { NavCategory, NavChild } from "@/data/categories";

/**
 * Homepage lookbook nav — Burberry-style multi-column link tree.
 * If the category has a single brand with nested children (e.g. 버버리),
 * expand into that brand's columns (트렌치 / 여성용 / 남성용 …).
 */
export function LookbookCategoryLinks({
  category,
}: {
  category: NavCategory;
}) {
  const columns = resolveColumns(category);
  if (!columns.length) return null;

  return (
    <nav className="lookbook-mega" aria-label={`${category.labelKo} 카테고리`}>
      {columns.map((col) => (
        <div key={col.id} className="lookbook-mega__col">
          <Link href={col.href} className="lookbook-mega__heading">
            {col.labelKo}
          </Link>
          {col.children?.length ? (
            <ul className="lookbook-mega__list">
              {col.children.map((child) => (
                <li key={child.id} className="lookbook-mega__item">
                  <Link href={child.href} className="lookbook-mega__link">
                    {child.labelKo}
                  </Link>
                  {child.children?.length ? (
                    <ul className="lookbook-mega__sublist">
                      {child.children.map((leaf) => (
                        <li key={leaf.id}>
                          <Link
                            href={leaf.href}
                            className="lookbook-mega__sublink"
                          >
                            {leaf.labelKo}
                          </Link>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ))}
    </nav>
  );
}

function resolveColumns(category: NavCategory): NavChild[] {
  const kids = category.children ?? [];
  if (!kids.length) return [];

  // Single brand hub → use its nested columns (Burberry Women/Men/…)
  if (kids.length === 1 && kids[0].children?.length) {
    return kids[0].children;
  }

  return kids;
}
