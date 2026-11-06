"use client";

import { useActionState } from "react";

export function AuthForm({
  action,
  submitLabel,
  extra,
  next,
}: {
  action: (
    prev: { error: string } | null,
    formData: FormData,
  ) => Promise<{ error: string } | null>;
  submitLabel: string;
  extra?: React.ReactNode;
  next?: string;
}) {
  const [state, formAction, pending] = useActionState(action, null);
  return (
    <form action={formAction} className="card mx-auto grid max-w-md gap-4 p-6">
      {next ? <input type="hidden" name="next" value={next} /> : null}
      {extra}
      {state?.error ? <p className="err">{state.error}</p> : null}
      <button className="btn" disabled={pending} type="submit">
        {pending ? "처리 중…" : submitLabel}
      </button>
    </form>
  );
}
