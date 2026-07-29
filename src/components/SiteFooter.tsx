import Link from "next/link";
import { navCategories } from "@/data/categories";

const bizNo = "725-86-02737";
const bizNoDigits = bizNo.replace(/-/g, "");

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
          <div className="site-footer__policy-links">
            <Link href="/terms">이용약관</Link>
            <span aria-hidden className="site-footer__policy-sep">
              ·
            </span>
            <Link href="/privacy">개인정보처리방침</Link>
          </div>
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
          <h4>Customer Care</h4>
          <a href="mailto:support@hjstoryltd.com">support@hjstoryltd.com</a>
          <a href="tel:+4407897535888">+44 7897 535888</a>
          <p>결제: 네이버페이 · 카카오페이 (연동 예정)</p>
        </div>
      </div>

      <div className="site-footer__biz">
        <div className="site-footer__biz-lines" aria-label="사업자 정보">
          <p>
            <span>상호명: (주)리치몬드인터내셔널</span>
            <span className="site-footer__biz-sep" aria-hidden>
              |
            </span>
            <span>메일: support@hjstoryltd.com</span>
            <span className="site-footer__biz-sep" aria-hidden>
              |
            </span>
            <span>전화번호: +44 7897 535888</span>
          </p>
          <p>
            <span>주소: 경기도 김포시 고촌읍 은행영사정로23번길 46</span>
            <span className="site-footer__biz-sep" aria-hidden>
              |
            </span>
            <span>사업자등록번호: {bizNo}</span>
          </p>
          <p>
            <span>통신판매업신고: 제 2023-경기김포-1258 호</span>
            <span className="site-footer__biz-sep" aria-hidden>
              |
            </span>
            <a
              className="site-footer__biz-check"
              href={`https://www.ftc.go.kr/bizCommPop.do?wrkr_no=${bizNoDigits}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              사업자정보확인
            </a>
            <span className="site-footer__biz-sep" aria-hidden>
              |
            </span>
            <span>대표자: 이정현</span>
            <span className="site-footer__biz-sep" aria-hidden>
              |
            </span>
            <span>개인정보책임자: 홍화연</span>
          </p>
          <p>
            <span>UK Company: HJ STORY LIMITED</span>
            <span className="site-footer__biz-sep" aria-hidden>
              |
            </span>
            <span>
              V307 Vox Studios, 1-45 Durham Street, Vauxhall, United Kingdom,
              SE11 5JH
            </span>
          </p>
        </div>

        <div className="site-footer__bottom">
          <div className="site-footer__bottom-links">
            <Link href="/terms">이용약관</Link>
            <Link href="/privacy">개인정보처리방침</Link>
          </div>
          <p className="site-footer__legal">
            © {new Date().getFullYear()} Briq. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
