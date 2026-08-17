"use client";

import Link from "next/link";
import { useSwingStore } from "@/lib/swing/store";

export function MembershipPanel() {
  const tier = useSwingStore((s) => s.tier);
  const trialUsed = useSwingStore((s) => s.trialUsed);
  const activatePro = useSwingStore((s) => s.activatePro);

  return (
    <div className="swing-page">
      <header className="swing-page__head">
        <p className="swing-kicker">멤버십</p>
        <h1>트라이얼은 요약, 유료는 교정 루프</h1>
        <p>
          결제 연동 전 데모입니다. 유료를 켜면 이 브라우저에서 재업로드·데일리·자료
          배포가 열립니다.
        </p>
      </header>

      <div className="swing-plans">
        <article>
          <p>Trial</p>
          <h2>무료 · 1회</h2>
          <ul>
            <li>스윙 영상 1회 분석</li>
            <li>선택한 프로와 다른 점 3가지 요약</li>
            <li>바로 할 교정 한 줄</li>
          </ul>
          <p className="swing-plans__state">
            {trialUsed ? "이미 사용함" : "아직 사용 가능"}
          </p>
          <Link href="/swing/analyze" className="swing-btn swing-btn--ghost">
            분석으로
          </Link>
        </article>
        <article className="is-featured">
          <p>Pro</p>
          <h2>29,000원 / 월</h2>
          <ul>
            <li>영상 계속 업데이트, 점수 추이</li>
            <li>앞·뒤 올리면 3D</li>
            <li>페이즈별 교정 + 데일리 코칭</li>
            <li>오늘 드릴 자료 배포 (다운로드·인쇄)</li>
          </ul>
          {tier === "pro" ? (
            <p className="swing-plans__state">이 기기에서 유료 멤버십이 켜져 있습니다</p>
          ) : (
            <button type="button" className="swing-btn" onClick={activatePro}>
              데모로 유료 켜기
            </button>
          )}
        </article>
      </div>
    </div>
  );
}
