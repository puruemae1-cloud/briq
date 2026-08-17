import { AuthForm } from "@/components/AuthForm";
import { loginAction } from "@/app/actions/auth";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;
  return (
    <div className="page-wrap py-14">
      <h1 className="display mb-6 text-center text-4xl">로그인</h1>
      <AuthForm
        action={loginAction}
        submitLabel="로그인"
        next={next || "/cart"}
        extra={
          <>
            <label className="field">
              <span>이메일</span>
              <input name="email" type="email" required autoComplete="email" />
            </label>
            <label className="field">
              <span>비밀번호</span>
              <input name="password" type="password" required autoComplete="current-password" />
            </label>
          </>
        }
      />
    </div>
  );
}
