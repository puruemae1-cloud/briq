import Link from "next/link";
import { navCategories } from "@/data/categories";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer__grid">
        <div>
          <p className="brand-mark__word">Briq</p>
          <p className="site-footer__tag">British + Boutique / Unique</p>
          <p className="site-footer__copy">
            영국 현지 기준의 까다로운 셀렉션,
            <br />
            오직 당신만을 위한 직배송.
          </p>
        </div>
        <div>
          <h4>Shop</h4>
          <Link href="/shop">Shop (전체상품)</Link>
          {navCategories.map((c) => (
            <Link key={c.id} href={c.href}>
              {c.labelKo}
            </Link>
          ))}
        </div>
        <div>
          <h4>Company</h4>
          <p>(주)리치몬드인터내셔널</p>
          <p>결제: 네이버페이 · 카카오페이 (연동 예정)</p>
        </div>
      </div>

      <div className="site-footer__legal-block">
        <p>
          <strong>UK Company</strong> HJ STORY LIMITED
        </p>
        <p>
          <strong>Address</strong> V307 Vox Studios, 1-45 Durham Street, Vauxhall,
          United Kingdom, SE11 5JH
        </p>
        <p className="site-footer__legal">
          © {new Date().getFullYear()} Briq. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
