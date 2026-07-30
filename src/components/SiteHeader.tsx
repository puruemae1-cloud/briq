import Link from "next/link";
import { ChevronDown, Menu, ShoppingBag, X } from "lucide-react";
import { navCategories, type NavChild } from "@/data/categories";
import { HeaderSearch } from "@/components/HeaderSearch";
import { HeaderAccount } from "@/components/HeaderAccount";
import { HomeLogoLink } from "@/components/HomeLogoLink";

function clearanceClass(id: string) {
  return id === "cw-clearance" || id === "gg-sale"
    ? "nav-link--clearance"
    : undefined;
}

/** Full nested mega-menu — Burberry-style columns under each top category. */
function MegaLinks({ items }: { items: NavChild[] }) {
  const columns =
    items.length === 1 && items[0].children?.length
      ? items[0].children
      : items;

  return (
    <div className="nav-mega">
      {columns.map((col) => (
        <div key={col.id} className="nav-mega__col">
          <Link
            href={col.href}
            className={`nav-mega__heading ${clearanceClass(col.id) ?? ""}`}
          >
            {col.labelKo}
          </Link>
          {col.children?.map((child) => (
            <div key={child.id} className="nav-mega__group">
              <Link
                href={child.href}
                className={`nav-mega__link ${
                  child.children?.length ? "nav-mega__link--parent" : ""
                } ${clearanceClass(child.id) ?? ""}`}
              >
                {child.labelKo}
              </Link>
              {child.children?.map((leaf) => (
                <Link
                  key={leaf.id}
                  href={leaf.href}
                  className={`nav-mega__sublink ${clearanceClass(leaf.id) ?? ""}`}
                >
                  {leaf.labelKo}
                </Link>
              ))}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function MobileBranch({
  items,
  depth = 0,
}: {
  items: NavChild[];
  depth?: number;
}) {
  return (
    <>
      {items.map((child) =>
        child.children?.length ? (
          <details
            key={child.id}
            className={`mobile-drawer__branch mobile-drawer__branch--d${Math.min(depth, 3)}`}
          >
            <summary className="mobile-drawer__summary">
              <span>{child.labelKo}</span>
              <ChevronDown
                className="mobile-drawer__chevron"
                size={16}
                aria-hidden
              />
            </summary>
            <div className="mobile-drawer__branch-body">
              <a href={child.href} className="mobile-drawer__all">
                전체 보기
              </a>
              <MobileBranch items={child.children} depth={depth + 1} />
            </div>
          </details>
        ) : (
          <a
            key={child.id}
            href={child.href}
            className={[
              "mobile-drawer__sub2",
              clearanceClass(child.id) ?? "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {child.labelKo}
          </a>
        ),
      )}
    </>
  );
}

export function SiteHeader({ cartCount = 0 }: { cartCount?: number }) {
  return (
    <>
      <input
        type="checkbox"
        id="nav-drawer"
        className="nav-drawer-toggle"
        aria-hidden="true"
        tabIndex={-1}
      />

      <header className="site-header">
        <div className="site-header__inner">
          <div className="site-header__brand">
            <HomeLogoLink className="brand-mark" aria-label="Briq home">
              <span className="brand-mark__word">Briq</span>
              <span className="brand-mark__sub">British Boutique</span>
            </HomeLogoLink>
            <label
              htmlFor="nav-drawer"
              className="icon-btn nav-drawer-open"
              aria-label="카테고리 메뉴 열기"
            >
              <Menu size={22} />
            </label>
          </div>

          <nav className="site-nav" aria-label="Primary">
            <Link href="/shop" className="site-nav__link">
              Shop
              <span className="site-nav__sublabel">전체상품</span>
            </Link>

            {navCategories.map((c) =>
              c.children?.length ? (
                <div key={c.id} className="nav-item">
                  <Link href={c.href} className="site-nav__link">
                    {c.labelKo}
                    <ChevronDown size={14} aria-hidden />
                  </Link>
                  <div className="nav-dropdown nav-dropdown--mega">
                    <MegaLinks items={c.children} />
                  </div>
                </div>
              ) : (
                <Link key={c.id} href={c.href} className="site-nav__link">
                  {c.labelKo}
                </Link>
              ),
            )}
          </nav>

          <div className="site-header__actions">
            <HeaderSearch />
            <HeaderAccount />
            <Link href="/cart" className="icon-btn cart-btn" aria-label="장바구니">
              <ShoppingBag size={20} />
              {cartCount > 0 ? <span className="cart-count">{cartCount}</span> : null}
            </Link>
          </div>
        </div>
      </header>

      <div className="mobile-drawer" role="dialog" aria-modal="true" aria-label="카테고리 메뉴">
        <label
          htmlFor="nav-drawer"
          className="mobile-drawer__backdrop"
          aria-label="메뉴 닫기"
        />
        <div className="mobile-drawer__panel">
          <div className="mobile-drawer__top">
            <span className="brand-mark__word">Briq</span>
            <label htmlFor="nav-drawer" className="icon-btn" aria-label="메뉴 닫기">
              <X size={22} />
            </label>
          </div>
          <nav className="mobile-drawer__nav">
            <a href="/shop" className="mobile-drawer__top-link">
              Shop (전체상품)
            </a>
            {navCategories.map((c) =>
              c.children?.length ? (
                <details key={c.id} className="mobile-drawer__group">
                  <summary className="mobile-drawer__summary">
                    <span>{c.labelKo}</span>
                    <ChevronDown
                      className="mobile-drawer__chevron"
                      size={18}
                      aria-hidden
                    />
                  </summary>
                  <div className="mobile-drawer__branch-body">
                    <a href={c.href} className="mobile-drawer__all">
                      전체 보기
                    </a>
                    <MobileBranch items={c.children} />
                  </div>
                </details>
              ) : (
                <a key={c.id} href={c.href} className="mobile-drawer__top-link">
                  {c.labelKo}
                </a>
              ),
            )}
          </nav>
        </div>
      </div>
    </>
  );
}
