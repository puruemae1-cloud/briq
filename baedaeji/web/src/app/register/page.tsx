import { AuthForm } from "@/components/AuthForm";
import { registerAction } from "@/app/actions/auth";

export default function RegisterPage() {
  return (
    <div className="page-wrap py-14">
      <h1 className="display mb-2 text-center text-4xl">회원가입</h1>
      <p className="mb-8 text-center text-sm text-[var(--muted)]">
        가입 후 영국 스토어 상품 URL을 장바구니에 담을 수 있습니다.
      </p>
      <AuthForm
        action={registerAction}
        submitLabel="가입하고 장바구니로"
        extra={
          <>
            <label className="field">
              <span>이름</span>
              <input name="name" required autoComplete="name" />
            </label>
            <label className="field">
              <span>이메일</span>
              <input name="email" type="email" required autoComplete="email" />
            </label>
            <label className="field">
              <span>비밀번호</span>
              <input name="password" type="password" required minLength={8} autoComplete="new-password" />
            </label>
            <label className="field">
              <span>휴대폰</span>
              <input name="phone" autoComplete="tel" placeholder="010-" />
            </label>
            <label className="field">
              <span>한국 배송지</span>
              <textarea name="address" rows={2} placeholder="견적 전에 입력해도 됩니다" />
            </label>
            <label className="field">
              <span>운영 코드 (선택)</span>
              <input name="adminCode" autoComplete="off" placeholder="운영자만 입력" />
            </label>
          </>
        }
      />
    </div>
  );
}
