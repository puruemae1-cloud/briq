"use client";

import Link from "next/link";
import { PROS } from "@/lib/swing/pros";
import { useSwingStore } from "@/lib/swing/store";

export function SwingLanding() {
  const tier = useSwingStore((s) => s.tier);
  const trialUsed = useSwingStore((s) => s.trialUsed);

  return (
    <div className="swing-page swing-landing">
      <section className="swing-hero">
        <p className="swing-kicker">Briq Swing</p>
        <h1>
          스윙 동영상 한 편으로,
          <br />
          원하는 PGA 선수와 다른 점을 교정합니다
        </h1>
        <p className="swing-hero__lead">
          앞면과 뒷면을 같이 올리면 3D로 축을 보고, 트라이얼은 요약만, 유료 회원은
          영상을 계속 업데이트하며 교정이 먹히는지와 오늘 할 드릴 자료까지 받습니다.
        </p>
        <div className="swing-hero__cta">
          <Link href="/swing/analyze" className="swing-btn">
            {trialUsed && tier !== "pro" ? "지난 요약 보기" : "트라이얼 분석"}
          </Link>
          <Link href="/swing/membership" className="swing-btn swing-btn--ghost">
            유료 코칭
          </Link>
        </div>
      </section>

      <ol className="swing-steps">
        <li>
          <span>01</span>
          <h2>스윙 영상</h2>
          <p>페이스온·다운더라인. 둘 다 있으면 3D 스켈레톤으로 합성합니다.</p>
        </li>
        <li>
          <span>02</span>
          <h2>프로 비교</h2>
          <p>
            @purego1f 슬로모션 아카이브에서 증류한 투어 모델, 로리·셰플러·모리카와 등과
            메트릭을 나란히 둡니다.
          </p>
        </li>
        <li>
          <span>03</span>
          <h2>교정 · 데일리</h2>
          <p>
            트라이얼은 다른 점 3가지와 바로 할 드릴만. 유료는 매일 플랜과 인쇄용 자료를
            배포합니다.
          </p>
        </li>
      </ol>

      <section>
        <h2 className="swing-h2">미리 학습한 프로 템플릿</h2>
        <p className="swing-note">
          Instagram은 원본 릴을 받아 재학습하지 않습니다. 공개된 FO/DTL 패턴과 선수별
          스윙 특성을 수치 템플릿으로 넣었습니다. 소스:{" "}
          <a href="https://www.instagram.com/purego1f" target="_blank" rel="noreferrer">
            instagram.com/purego1f
          </a>
        </p>
        <div className="swing-pro-grid">
          {PROS.map((p) => (
            <article key={p.id}>
              <p>
                {p.tour} · {p.name}
              </p>
              <h3>{p.nameKo}</h3>
              <p>{p.signature}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
