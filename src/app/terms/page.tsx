import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "이용약관",
  description: "Briq 서비스 이용약관",
};

export default function TermsPage() {
  return (
    <main className="legal-page">
      <div className="legal-page__inner">
        <p className="legal-page__eyebrow">Legal</p>
        <h1 className="legal-page__title">이용약관</h1>
        <p className="legal-page__lead">
          Briq(이하 “회사”)가 운영하는 온라인 쇼핑몰 서비스의 이용과 관련하여
          회사와 이용자 간의 권리·의무 및 책임사항을 규정합니다.
        </p>

        <section className="legal-page__section">
          <h2>제1조 (목적)</h2>
          <p>
            본 약관은 회사가 제공하는 전자상거래 관련 서비스의 이용조건 및 절차,
            회사와 이용자의 권리·의무·책임사항과 기타 필요한 사항을 규정함을
            목적으로 합니다.
          </p>
        </section>

        <section className="legal-page__section">
          <h2>제2조 (정의)</h2>
          <ol>
            <li>
              “몰”이란 회사가 재화 또는 용역을 이용자에게 제공하기 위하여 컴퓨터
              등 정보통신설비를 이용하여 재화 등을 거래할 수 있도록 설정한
              가상의 영업장을 말합니다.
            </li>
            <li>
              “이용자”란 몰에 접속하여 본 약관에 따라 회사가 제공하는 서비스를
              받는 회원 및 비회원을 말합니다.
            </li>
            <li>
              “회원”이란 몰에 회원등록을 한 자로서, 계속적으로 회사가 제공하는
              서비스를 이용할 수 있는 자를 말합니다.
            </li>
          </ol>
        </section>

        <section className="legal-page__section">
          <h2>제3조 (약관의 명시와 개정)</h2>
          <ol>
            <li>
              회사는 본 약관의 내용과 상호, 대표자명, 영업소 소재지, 사업자등록번호,
              통신판매업 신고번호, 연락처 등을 이용자가 쉽게 알 수 있도록 몰의
              초기 화면 또는 하단에 게시합니다.
            </li>
            <li>
              회사는 관련 법령을 위배하지 않는 범위에서 본 약관을 개정할 수
              있으며, 개정 시 적용일자 및 개정사유를 명시하여 현행 약관과 함께
              몰에 공지합니다.
            </li>
          </ol>
        </section>

        <section className="legal-page__section">
          <h2>제4조 (서비스의 제공 및 변경)</h2>
          <ol>
            <li>
              회사는 다음과 같은 업무를 수행합니다.
              <ul>
                <li>재화 또는 용역에 대한 정보 제공 및 구매계약의 체결</li>
                <li>구매계약이 체결된 재화 또는 용역의 배송</li>
                <li>기타 회사가 정하는 업무</li>
              </ul>
            </li>
            <li>
              회사는 재화의 품절 또는 기술적 사양 변경 등의 경우에는 장차 체결되는
              계약에 의해 제공할 재화·용역의 내용을 변경할 수 있습니다.
            </li>
          </ol>
        </section>

        <section className="legal-page__section">
          <h2>제5조 (구매신청 및 계약의 성립)</h2>
          <ol>
            <li>
              이용자는 몰에서 다음 방법에 의하여 구매를 신청합니다.
              <ul>
                <li>재화 등의 검색 및 선택</li>
                <li>성명, 주소, 연락처, 이메일 등 주문 정보 입력</li>
                <li>약관 내용 확인 및 동의</li>
                <li>구매신청 및 결제</li>
              </ul>
            </li>
            <li>
              회사의 승낙이 이용자에게 도달한 시점에 계약이 성립한 것으로 봅니다.
            </li>
          </ol>
        </section>

        <section className="legal-page__section">
          <h2>제6조 (지급방법)</h2>
          <p>
            몰에서 구매한 재화 등에 대한 대금지급방법은 신용카드, 간편결제
            (네이버페이·카카오페이 등), 기타 회사가 가용하다고 인정하는 방법으로
            할 수 있습니다.
          </p>
        </section>

        <section className="legal-page__section">
          <h2>제7조 (배송)</h2>
          <p>
            회사는 이용자가 구매한 재화에 대해 배송수단, 수단별 배송비용 부담자,
            수단별 배송기간 등을 명시합니다. 해외 직배송 상품의 경우 통관 및
            국제운송 사정에 따라 일정이 변동될 수 있습니다.
          </p>
        </section>

        <section className="legal-page__section">
          <h2>제8조 (청약철회 등)</h2>
          <ol>
            <li>
              이용자는 「전자상거래 등에서의 소비자보호에 관한 법률」 등 관련
              법령에 따라 청약철회를 할 수 있습니다.
            </li>
            <li>
              이용자에게 책임 있는 사유로 재화가 멸실·훼손된 경우, 이용자의 사용
              또는 일부 소비로 재화의 가치가 현저히 감소한 경우 등에는 청약철회가
              제한될 수 있습니다.
            </li>
          </ol>
        </section>

        <section className="legal-page__section">
          <h2>제9조 (개인정보보호)</h2>
          <p>
            회사는 이용자의 개인정보 수집 시 서비스 제공에 필요한 최소한의
            정보를 수집하며, 개인정보의 보호 및 사용에 대해서는 관련 법령 및
            회사의{" "}
            <Link href="/privacy">개인정보처리방침</Link>이 적용됩니다.
          </p>
        </section>

        <section className="legal-page__section">
          <h2>제10조 (회사의 의무)</h2>
          <p>
            회사는 법령과 본 약관이 금지하거나 공서양속에 반하는 행위를 하지
            않으며, 계속적이고 안정적으로 서비스를 제공하기 위해 최선을 다합니다.
          </p>
        </section>

        <section className="legal-page__section">
          <h2>제11조 (이용자의 의무)</h2>
          <p>
            이용자는 신청 시 허위 내용을 등록해서는 안 되며, 타인의 정보를
            도용하거나 회사의 서비스 운영을 방해하는 행위를 하여서는 안 됩니다.
          </p>
        </section>

        <section className="legal-page__section">
          <h2>제12조 (분쟁해결)</h2>
          <p>
            회사는 이용자로부터 제출되는 불만사항 및 의견을 우선적으로 처리합니다.
            다만 신속한 처리가 곤란한 경우에는 이용자에게 그 사유와 처리일정을
            통보합니다.
          </p>
        </section>

        <section className="legal-page__section">
          <h2>제13조 (재판권 및 준거법)</h2>
          <p>
            회사와 이용자 간에 발생한 전자상거래 분쟁에 관한 소송은 대한민국
            법을 준거법으로 하며, 관할 법원은 민사소송법 등 관련 법령에
            따릅니다.
          </p>
        </section>

        <section className="legal-page__section">
          <h2>부칙</h2>
          <p>본 약관은 게시한 날부터 시행합니다.</p>
          <p>
            상호: (주)리치몬드인터내셔널 · 대표자: 이정현 · 문의:{" "}
            <a href="mailto:support@hjstoryltd.com">support@hjstoryltd.com</a>
          </p>
        </section>
      </div>
    </main>
  );
}
