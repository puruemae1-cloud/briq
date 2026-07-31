import Link from "next/link";
import { ChevronDown, Menu, ShoppingBag, X } from "lucide-react";
import { navCategories, type NavChild } from "@/data/categories";
import { HeaderSearch } from "@/components/HeaderSearch";
import { HeaderAccount } from "@/components/HeaderAccount";
import { HomeLogoLink } from "@/components/HomeLogoLink";

function brandLinkClass(id: string, extra?: string) {
  const clearance =
    id === "cw-clearance" || id === "gg-sale" ? "nav-link--clearance" : "";
  return [extra, clearance].filter(Boolean).join(" ") || undefined;
}

/** Brand row with one nested leaf level (e.g. Arc'teryx → 여성용/남성용/아울렛). */
function BrandLinks({ items }: { items: NavChild[] }) {
  return (
    <>
      {items.map((child) => (
        <div key={child.id} className="nav-dropdown__group">
          <Link
            href={child.href}
            className={brandLinkClass(child.id, "nav-dropdown__parent")}
          >
            {child.labelKo}
          </Link>
          {child.children?.length ? (
            <div className="nav-dropdown__nest nav-dropdown__nest--d1">
              {child.children.map((leaf) => (
                <Link
                  key={leaf.id}
                  href={leaf.href}
                  className={brandLinkClass(leaf.id)}
                >
                  {leaf.labelKo}
                </Link>
              ))}
            </div>
          ) : null}
        </div>
      ))}
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
          <div className="site-header__left">
            <label
              htmlFor="nav-drawer"
              className="icon-btn nav-drawer-open"
              aria-label="카테고리 메뉴 열기"
            >
              <Menu className="nav-drawer-open__icon" size={22} aria-hidden />
            </label>
            <HomeLogoLink className="brand-mark" aria-label="Briq home">
              <span className="brand-mark__word">Briq</span>
              <span className="brand-mark__sub">British Boutique</span>
            </HomeLogoLink>
          </div>

          <nav className="site-nav" aria-label="Primary">
            <Link href="/shop" className="site-nav__link">
              Shop
            </Link>

            {navCategories.map((c) =>
              c.children?.length ? (
                <div key={c.id} className="nav-item">
                  <Link href={c.href} className="site-nav__link">
                    {c.labelKo}
                    <ChevronDown size={14} aria-hidden />
                  </Link>
                  <div className="nav-dropdown">
                    <BrandLinks items={c.children} />
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
              Shop
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
                    {c.children.map((child) => (
                      <div key={child.id} className="mobile-drawer__brand">
                        <a
                          href={child.href}
                          className={[
                            "mobile-drawer__sub mobile-drawer__sub--brand",
                            child.id === "cw-clearance" || child.id === "gg-sale"
                              ? "nav-link--clearance"
                              : "",
                          ]
                            .filter(Boolean)
                            .join(" ")}
                        >
                          {child.labelKo}
                        </a>
                        {child.children?.length ? (
                          <div className="mobile-drawer__leaves">
                            {child.children.map((leaf) => (
                              <a
                                key={leaf.id}
                                href={leaf.href}
                                className={[
                                  "mobile-drawer__sub2",
                                  leaf.id === "cw-clearance" ||
                                  leaf.id === "gg-sale"
                                    ? "nav-link--clearance"
                                    : "",
                                ]
                                  .filter(Boolean)
                                  .join(" ")}
                              >
                                {leaf.labelKo}
                              </a>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    ))}
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
