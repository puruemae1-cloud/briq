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

코드 자리: `src/lib/payments.ts`

## 도메인

별도 확인 결과 요약은 프로젝트 안내 메시지 참고.
