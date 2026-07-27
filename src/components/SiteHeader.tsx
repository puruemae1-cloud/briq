import Link from "next/link";
import { ChevronDown, Menu, ShoppingBag, X } from "lucide-react";
import { navCategories, type NavChild } from "@/data/categories";
import { HeaderSearch } from "@/components/HeaderSearch";
import { HeaderAccount } from "@/components/HeaderAccount";

function DropdownLinks({ items, depth = 0 }: { items: NavChild[]; depth?: number }) {
  return (
    <>
      {items.map((child) => (
        <div key={child.id} className={depth > 0 ? "nav-dropdown__nest" : undefined}>
          <Link href={child.href}>{child.labelKo}</Link>
          {child.children?.length ? (
            <div className="nav-dropdown__group">
              <DropdownLinks items={child.children} depth={depth + 1} />
            </div>
          ) : null}
        </div>
      ))}
    </>
  );
}

/** Accordion branches — collapsed until tapped. */
function MobileBranches({
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
            className={`mobile-drawer__branch mobile-drawer__branch--d${depth}`}
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
              <MobileBranches items={child.children} depth={depth + 1} />
            </div>
          </details>
        ) : (
          <a
            key={child.id}
            href={child.href}
            className={
              depth === 0 ? "mobile-drawer__sub" : "mobile-drawer__sub2"
            }
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
      {/* Outside sticky header so the drawer covers the whole viewport */}
      <input
        type="checkbox"
        id="nav-drawer"
        className="nav-drawer-toggle"
        aria-hidden="true"
        tabIndex={-1}
      />

      <header className="site-header">
        <div className="site-header__inner">
          <label
            htmlFor="nav-drawer"
            className="icon-btn nav-drawer-open"
            aria-label="카테고리 메뉴 열기"
          >
            <Menu size={22} />
          </label>

          <Link href="/" className="brand-mark" aria-label="Briq home">
            <span className="brand-mark__word">Briq</span>
            <span className="brand-mark__sub">British Boutique</span>
          </Link>

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
                  <div className="nav-dropdown">
                    <DropdownLinks items={c.children} />
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
                    <MobileBranches items={c.children} />
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
