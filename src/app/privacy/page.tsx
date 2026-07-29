import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "개인정보처리방침",
  description: "Briq 개인정보처리방침",
};

export default function PrivacyPage() {
  return (
    <main className="legal-page">
      <div className="legal-page__inner">
        <p className="legal-page__eyebrow">Legal</p>
        <h1 className="legal-page__title">개인정보처리방침</h1>
        <p className="legal-page__lead">
          (주)리치몬드인터내셔널(이하 “회사”)은 「개인정보 보호법」 등 관련
          법령에 따라 이용자의 개인정보를 보호하고, 이와 관련한 고충을 신속하고
          원활하게 처리할 수 있도록 다음과 같이 개인정보처리방침을 수립·공개합니다.
        </p>

        <section className="legal-page__section">
          <h2>1. 개인정보의 수집 항목 및 방법</h2>
          <p>회사는 서비스 제공을 위해 다음과 같은 개인정보를 수집할 수 있습니다.</p>
          <ul>
            <li>회원 가입: 이름, 이메일, 비밀번호, 휴대전화번호</li>
            <li>주문·결제·배송: 수령인 정보, 주소, 연락처, 결제 관련 정보</li>
            <li>고객문의: 문의 내용, 연락처, 이메일</li>
            <li>자동 수집: 접속 IP, 쿠키, 방문 일시, 서비스 이용 기록</li>
          </ul>
        </section>

        <section className="legal-page__section">
          <h2>2. 개인정보의 수집·이용 목적</h2>
          <ul>
            <li>회원 식별 및 서비스 제공·계약 이행</li>
            <li>주문 처리, 결제, 배송, 교환·반품 처리</li>
            <li>고객 상담 및 불만 처리</li>
            <li>서비스 개선, 부정 이용 방지, 법령상 의무 이행</li>
          </ul>
        </section>

        <section className="legal-page__section">
          <h2>3. 개인정보의 보유 및 이용 기간</h2>
          <p>
            회사는 원칙적으로 개인정보 수집·이용 목적이 달성된 후에는 해당 정보를
            지체 없이 파기합니다. 다만 관련 법령에 따라 일정 기간 보관이 필요한
            경우에는 그 기간 동안 보관합니다.
          </p>
          <ul>
            <li>계약 또는 청약철회 등에 관한 기록: 5년</li>
            <li>대금결제 및 재화 등의 공급에 관한 기록: 5년</li>
            <li>소비자 불만 또는 분쟁처리에 관한 기록: 3년</li>
            <li>웹사이트 방문 기록: 3개월</li>
          </ul>
        </section>

        <section className="legal-page__section">
          <h2>4. 개인정보의 제3자 제공</h2>
          <p>
            회사는 이용자의 개인정보를 원칙적으로 외부에 제공하지 않습니다. 다만
            이용자가 사전에 동의한 경우, 법령에 근거가 있는 경우, 또는 배송·결제
            등 서비스 이행을 위해 필요한 범위에서 관련 업체에 제공할 수 있습니다.
          </p>
        </section>

        <section className="legal-page__section">
          <h2>5. 개인정보 처리의 위탁</h2>
          <p>
            회사는 원활한 서비스 제공을 위해 개인정보 처리 업무를 외부에 위탁할
            수 있으며, 위탁 시 관련 법령에 따라 개인정보가 안전하게 관리되도록
            필요한 사항을 규정합니다. 위탁 현황은 변경 시 본 방침을 통해
            고지합니다.
          </p>
        </section>

        <section className="legal-page__section">
          <h2>6. 이용자의 권리</h2>
          <p>
            이용자는 언제든지 자신의 개인정보를 조회·수정·삭제·처리정지 요구를
            할 수 있으며, 회원 탈퇴를 요청할 수 있습니다. 관련 요청은 아래
            개인정보 보호책임자에게 연락해 주시면 지체 없이 조치하겠습니다.
          </p>
        </section>

        <section className="legal-page__section">
          <h2>7. 개인정보의 파기</h2>
          <p>
            회사는 보유 기간이 경과하거나 처리 목적이 달성된 개인정보를 복구·재생이
            불가능한 방법으로 지체 없이 파기합니다. 전자적 파일은 안전한 방법으로
            삭제하며, 출력물은 분쇄 또는 소각합니다.
          </p>
        </section>

        <section className="legal-page__section">
          <h2>8. 개인정보의 안전성 확보 조치</h2>
          <ul>
            <li>개인정보 접근 권한의 제한</li>
            <li>개인정보의 암호화</li>
            <li>접속기록의 보관 및 위·변조 방지</li>
            <li>보안 프로그램 설치 및 주기적 점검</li>
          </ul>
        </section>

        <section className="legal-page__section">
          <h2>9. 쿠키의 운영</h2>
          <p>
            회사는 이용자에게 개별적인 맞춤 서비스를 제공하기 위해 쿠키를 사용할
            수 있습니다. 이용자는 브라우저 설정을 통해 쿠키 저장을 거부하거나
            삭제할 수 있으나, 이 경우 일부 서비스 이용에 제한이 있을 수 있습니다.
          </p>
        </section>

        <section className="legal-page__section">
          <h2>10. 개인정보 보호책임자</h2>
          <div className="legal-page__card">
            <p>
              <strong>개인정보 보호책임자</strong> 홍화연
            </p>
            <p>
              <strong>대표자</strong> 이정현
            </p>
            <p>
              <strong>이메일</strong>{" "}
              <a href="mailto:support@hjstoryltd.com">support@hjstoryltd.com</a>
            </p>
            <p>
              <strong>연락처</strong>{" "}
              <a href="tel:+4407897535888">+44 7897 535888</a>
            </p>
            <p>
              <strong>주소</strong> 경기도 김포시 고촌읍 은행영사정로23번길 46
            </p>
          </div>
        </section>

        <section className="legal-page__section">
          <h2>11. 권익침해 구제방법</h2>
          <p>
            개인정보 침해에 대한 신고나 상담이 필요하신 경우 아래 기관에 문의하실
            수 있습니다.
          </p>
          <ul>
            <li>개인정보침해신고센터 (privacy.kisa.or.kr / 118)</li>
            <li>개인정보분쟁조정위원회 (www.kopico.go.kr / 1833-6972)</li>
            <li>대검찰청 사이버수사과 (www.spo.go.kr / 1301)</li>
            <li>경찰청 사이버수사국 (ecrm.cyber.go.kr / 182)</li>
          </ul>
        </section>

        <section className="legal-page__section">
          <h2>12. 방침의 변경</h2>
          <p>
            본 개인정보처리방침은 법령·정책 또는 보안기술의 변경에 따라 내용의
            추가·삭제 및 수정이 있을 수 있으며, 변경 시 몰을 통해 공지합니다.
          </p>
          <p>본 방침은 게시한 날부터 시행합니다.</p>
        </section>
      </div>
    </main>
  );
}
