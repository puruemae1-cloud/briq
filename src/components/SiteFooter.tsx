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
        <div className="site-footer__biz-head">
          <p className="site-footer__biz-eyebrow">Business Information</p>
          <p className="site-footer__biz-title">(주)리치몬드인터내셔널</p>
        </div>

        <dl className="site-footer__biz-grid">
          <div>
            <dt>대표자</dt>
            <dd>이정현</dd>
          </div>
          <div>
            <dt>개인정보책임자</dt>
            <dd>홍화연</dd>
          </div>
          <div>
            <dt>사업자등록번호</dt>
            <dd>
              {bizNo}{" "}
              <a
                className="site-footer__biz-check"
                href={`https://www.ftc.go.kr/bizCommPop.do?wrkr_no=${bizNoDigits}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                사업자정보확인
              </a>
            </dd>
          </div>
          <div>
            <dt>통신판매업신고</dt>
            <dd>제 2023-경기김포-1258 호</dd>
          </div>
          <div>
            <dt>주소</dt>
            <dd>경기도 김포시 고촌읍 은행영사정로23번길 46</dd>
          </div>
          <div>
            <dt>연락처</dt>
            <dd>
              <a href="tel:+4407897535888">+44 7897 535888</a>
            </dd>
          </div>
          <div>
            <dt>이메일</dt>
            <dd>
              <a href="mailto:support@hjstoryltd.com">support@hjstoryltd.com</a>
            </dd>
          </div>
          <div>
            <dt>UK Company</dt>
            <dd>HJ STORY LIMITED</dd>
          </div>
        </dl>

        <p className="site-footer__biz-address-uk">
          V307 Vox Studios, 1-45 Durham Street, Vauxhall, United Kingdom, SE11 5JH
        </p>

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
