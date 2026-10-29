import { redirect } from "next/navigation";
import { AuthForm } from "@/components/AuthForm";
import { updateProfileAction } from "@/app/actions/auth";
import { getCurrentUser } from "@/lib/auth";

export default async function AccountPage({
  searchParams,
}: {
  searchParams: Promise<{ need?: string }>;
}) {
  const me = await getCurrentUser();
  if (!me) redirect("/login?next=/account");
  const { need } = await searchParams;

  return (
    <div className="page-wrap py-12">
      <h1 className="display text-4xl">회원정보</h1>
      {need === "shipping" ? (
        <p className="mt-3 text-sm text-[var(--red)]">견적을 받으려면 휴대폰과 한국 배송지가 필요합니다.</p>
      ) : null}
      <div className="mt-8">
        <AuthForm
          action={updateProfileAction}
          submitLabel="저장"
          extra={
            <>
              <label className="field">
                <span>이름</span>
                <input name="name" required defaultValue={me.name} />
              </label>
              <label className="field">
                <span>휴대폰</span>
                <input name="phone" required defaultValue={me.phone} />
              </label>
              <label className="field">
                <span>한국 배송지</span>
                <textarea name="address" rows={3} required defaultValue={me.address} />
              </label>
              <label className="field">
                <span>개인통관고유부호 (선택)</span>
                <input name="customsCode" defaultValue={me.customsCode} placeholder="P로 시작" />
              </label>
            </>
          }
        />
      </div>
    </div>
  );
}
