import { Suspense } from "react";
import { LoginForm } from "@/components/LoginForm";

export default function LoginPage() {
  return (
    <section className="section account-auth">
      <Suspense fallback={<div className="panel">불러오는 중…</div>}>
        <LoginForm />
      </Suspense>
    </section>
  );
}
