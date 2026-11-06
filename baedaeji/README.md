# 배대지

Briq(영국 셀렉트숍)과 **별도**인 구매대행·배송대행 웹 서비스입니다. briq.kr에 배포하지 마세요.

## 로컬 실행

```bash
cd baedaeji/web
cp .env.example .env.local
# BAEDAEJI_ADMIN_CODE 를 본인만 아는 값으로 바꾸세요.
npm install
npm run dev
```

브라우저: http://localhost:3001

회원가입 시 **운영 코드**를 넣으면 운영자(`/admin`)가 됩니다.

## 지금 되는 것

- 메인 스토어 배너 10곳 (ASOS, Zalando, Next, Very, Flannels, END., boohoo, Selfridges, Harrods, NET-A-PORTER)
- 회원가입 / 로그인
- 허용된 스토어 상품 URL 장바구니
- 환율 기반 견적 확인
- 고객 주문 · 운영자 주문 리스트 (영국 몰 자동 로그인 없음)
- 결제는 아직 입금 대기 표시만 (네이버페이 가맹 전)

## 문서

- [실현 가능성](docs/feasibility.md)
- [제품 스펙](docs/product-spec.md)
- [백로그](docs/mvp-backlog.md)
