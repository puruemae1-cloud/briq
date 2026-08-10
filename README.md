# Briq (브릭)

British + Boutique / Unique — UK→KR 셀렉트 숍.

## 구성

| 폴더 | 설명 |
|------|------|
| `/` (루트) | Next.js 반응형 웹 (PC + 모바일) |
| `/mobile` | Expo iOS / Android 앱 |

## 웹 실행

```bash
export PATH="$HOME/.local/node/bin:$PATH"
cd /Users/jeonghyunlee/Documents/briq
npm run dev
```

브라우저: http://localhost:3000

## 앱 실행 (iOS / Android)

```bash
export PATH="$HOME/.local/node/bin:$PATH"
cd /Users/jeonghyunlee/Documents/briq/mobile
npm start
```

- iOS: `i` 또는 Expo Go로 QR 스캔
- Android: `a` 또는 Expo Go로 QR 스캔
- 스토어 배포: Apple Developer / Google Play 계정 필요 (본인 등록)

## 결제 (추후)

1. `(주)리치몬드인터내셔널`로 PG 계약 (토스페이먼츠 / 나이스 / 이니시스 등)
2. 네이버페이 · 카카오페이 활성화
3. `.env.example`을 `.env.local`로 복사 후 키 입력

```bash
cp .env.example .env.local
```

코드 자리: `src/lib/payments.ts` (기존 데모 체크아웃)

### 네이버페이 주문형 V2.1 (샌드박스)

독립몰 주문형 연동 스켈레톤이 포함되어 있습니다 (`NEXT_PUBLIC_NAVERPAY_SANDBOX=true` 기본).

| 환경변수 | 공개 | 설명 |
|---------|------|------|
| `NEXT_PUBLIC_NAVERPAY_ORDER` | yes | `true`면 버튼 강제 노출 |
| `NEXT_PUBLIC_NAVERPAY_SANDBOX` | yes | `false`만 운영 URL (검수 승인 후) |
| `NEXT_PUBLIC_NAVER_WCS_ACCOUNT` | yes | 네이버공통인증키 (wcs) |
| `NEXT_PUBLIC_NAVERPAY_BUTTON_KEY` | yes | 버튼 인증키 (SDK용) |
| `NAVERPAY_MERCHANT_ID` | **no** | 상점 ID |
| `NAVERPAY_CERTI_KEY` | **no** | 가맹점인증키 (서버 전용) |

- 상품정보 XML: `/api/naverpay/product-info?product[0][id]=<productId>`
- 주문 등록: `POST /api/naverpay/order` (서버→Naver register XML)
- 버튼: PDP · 장바구니 (기존 `/checkout` 데모 결제와 병행)

검수 요청 전 `dl_techsupport@navercorp.com`으로 테스트 URL + 상품정보 XML URL을 전달해야 합니다. 배송비·반품지·톡톡 등은 플레이스홀더이므로 가맹점 설정 후 교체하세요.

## 도메인

별도 확인 결과 요약은 프로젝트 안내 메시지 참고.
