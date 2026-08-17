"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { analyzeSwing } from "@/lib/swing/analyze";
import { captureView, fuseSkeletons, sampleDualViews } from "@/lib/swing/capture";
import { defaultProId, getPro, PROS } from "@/lib/swing/pros";
import { useSwingStore } from "@/lib/swing/store";
import type { ViewCapture } from "@/lib/swing/types";
import { PHASE_LABEL_KO } from "@/lib/swing/types";
import { Swing3D } from "./Swing3D";

async function fileToVideo(file: File) {
  const url = URL.createObjectURL(file);
  const video = document.createElement("video");
  video.src = url;
  video.muted = true;
  video.playsInline = true;
  await new Promise<void>((resolve, reject) => {
    video.onloadedmetadata = () => resolve();
    video.onerror = () => reject(new Error("영상을 읽을 수 없습니다."));
  });
  return { video, url };
}

export function AnalyzeStudio() {
  const [faceFile, setFaceFile] = useState<File | null>(null);
  const [dtlFile, setDtlFile] = useState<File | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const tier = useSwingStore((s) => s.tier);
  const trialUsed = useSwingStore((s) => s.trialUsed);
  const preferredProId = useSwingStore((s) => s.preferredProId);
  const handedness = useSwingStore((s) => s.handedness);
  const lastResult = useSwingStore((s) => s.lastResult);
  const lastThumbs = useSwingStore((s) => s.lastThumbs);
  const skeleton = useSwingStore((s) => s.lastSkeleton) ?? [];
  const setPreferredPro = useSwingStore((s) => s.setPreferredPro);
  const setHandedness = useSwingStore((s) => s.setHandedness);
  const saveAnalysis = useSwingStore((s) => s.saveAnalysis);

  const pro = getPro(preferredProId) ?? getPro(defaultProId())!;
  const trialBlocked = tier === "trial" && trialUsed;
  const thumbs = lastThumbs;

  const result = lastResult;

  function commit(views: ViewCapture[]) {
    const fused = fuseSkeletons(
      views.find((v) => v.view === "faceOn")?.skeleton,
      views.find((v) => v.view === "downTheLine")?.skeleton,
    );
    const analysis = analyzeSwing({
      views,
      proId: pro.id,
      handedness,
      trialLimited: tier !== "pro",
    });
    const thumbsOut = views.flatMap((v) => v.thumbs);
    const saved = saveAnalysis(analysis, fused, thumbsOut);
    if (!saved.ok) setError(saved.message);
  }

  async function run() {
    setError(null);
    if (trialBlocked) {
      setError("트라이얼 분석을 이미 사용했습니다. 유료 회원만 영상을 계속 업데이트할 수 있습니다.");
      return;
    }
    if (!faceFile && !dtlFile) {
      setError("앞면 또는 뒷면(다운더라인) 스윙 영상을 올려 주세요.");
      return;
    }

    const views: ViewCapture[] = [];
    const urls: string[] = [];
    try {
      if (faceFile) {
        setBusy("앞면 영상을 읽고 있습니다…");
        const { video, url } = await fileToVideo(faceFile);
        urls.push(url);
        views.push(await captureView(video, "faceOn", faceFile.name));
      }
      if (dtlFile) {
        setBusy("뒷면 영상을 읽고 있습니다…");
        const { video, url } = await fileToVideo(dtlFile);
        urls.push(url);
        views.push(await captureView(video, "downTheLine", dtlFile.name));
      }
      setBusy("프로 템플릿과 비교하는 중…");
      commit(views);
    } catch (e) {
      setError(e instanceof Error ? e.message : "분석에 실패했습니다.");
    } finally {
      urls.forEach((u) => URL.revokeObjectURL(u));
      setBusy(null);
    }
  }

  function runSample() {
    setError(null);
    if (trialBlocked) {
      setError("트라이얼 분석을 이미 사용했습니다. 유료 회원만 영상을 계속 업데이트할 수 있습니다.");
      return;
    }
    setBusy("샘플 앞·뒤 스윙을 비교하는 중…");
    try {
      commit(sampleDualViews());
    } finally {
      setBusy(null);
    }
  }

  const title = useMemo(() => {
    if (!result) return null;
    return `${pro.nameKo} 대비 ${result.overall}점`;
  }, [result, pro.nameKo]);

  return (
    <div className="swing-page">
      <header className="swing-page__head">
        <p className="swing-kicker">스윙 분석</p>
        <h1>원하는 프로와 다른 점만 집어 줍니다</h1>
        <p>
          앞면·뒷면 영상을 올리면 모션과 축을 읽고, @purego1f 아카이브에서 증류한
          투어 템플릿과 비교합니다. 트라이얼은 요약만, 유료는 페이즈별 교정과 데일리
          드릴까지 이어집니다.
        </p>
      </header>

      {trialBlocked ? (
        <div className="swing-banner">
          트라이얼 1회를 사용했습니다.{" "}
          <Link href="/swing/membership">유료 회원</Link>이 되면 영상을 계속 올려
          교정이 먹히는지 추적할 수 있습니다.
        </div>
      ) : null}

      <div className="swing-grid swing-grid--2">
        <label className="swing-drop">
          <span>앞면 (페이스온)</span>
          <strong>{faceFile ? faceFile.name : "탭해서 영상 선택"}</strong>
          <em>정면, 전신이 나오게</em>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setFaceFile(e.target.files?.[0] ?? null)}
          />
        </label>
        <label className="swing-drop">
          <span>뒷면 (다운더라인)</span>
          <strong>{dtlFile ? dtlFile.name : "탭해서 영상 선택"}</strong>
          <em>타깃 뒤쪽, 둘 다 올리면 3D</em>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setDtlFile(e.target.files?.[0] ?? null)}
          />
        </label>
      </div>

      <div className="swing-toolbar">
        <label>
          비교 프로
          <select
            value={pro.id}
            onChange={(e) => setPreferredPro(e.target.value)}
          >
            {PROS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nameKo} · {p.tour}
              </option>
            ))}
          </select>
        </label>
        <label>
          타격
          <select
            value={handedness}
            onChange={(e) =>
              setHandedness(e.target.value === "left" ? "left" : "right")
            }
          >
            <option value="right">오른손잡이</option>
            <option value="left">왼손잡이</option>
          </select>
        </label>
        <button
          type="button"
          className="swing-btn"
          onClick={() => void run()}
          disabled={Boolean(busy) || trialBlocked}
        >
          {busy ?? (tier === "pro" ? "분석하고 기록하기" : "트라이얼 요약 보기")}
        </button>
        <button
          type="button"
          className="swing-btn swing-btn--ghost"
          onClick={runSample}
          disabled={Boolean(busy) || trialBlocked}
        >
          샘플로 미리보기
        </button>
      </div>
      <p className="swing-note">
        샘플 미리보기도 트라이얼 1회에 포함됩니다. 앞·뒤 영상을 같이 올리면 실제 모션으로
        3D가 만들어집니다.
      </p>

      {error ? <p className="swing-error">{error}</p> : null}

      {result ? (
        <section className="swing-result">
          <div className="swing-score">
            <p>유사도</p>
            <strong>{result.overall}</strong>
            <span>{title}</span>
            {result.has3d ? (
              <em>3D 재구성됨</em>
            ) : (
              <em>앞·뒤를 같이 올리면 3D로 축을 봅니다</em>
            )}
          </div>
          <Swing3D
            frames={skeleton}
            label={result.has3d ? "앞·뒤 합성 3D" : "단일 시점 미리보기"}
          />
        </section>
      ) : (
        <section className="swing-result swing-result--empty">
          <Swing3D frames={[]} label="분석 후 스켈레톤이 여기에 생깁니다" />
        </section>
      )}

      {thumbs.length ? (
        <div className="swing-thumbs" aria-label="추출 프레임">
          {thumbs.map((src, i) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img key={i} src={src} alt="" />
          ))}
        </div>
      ) : null}

      {result ? (
        <>
          <h2 className="swing-h2">
            {result.trialLimited
              ? "트라이얼 요약 — 다른 점 3가지"
              : `${pro.nameKo}와 다른 점`}
          </h2>
          <ul className="swing-gaps">
            {result.gaps.map((g) => (
              <li key={g.key} className={`is-${g.severity}`}>
                <div>
                  <p>
                    {g.label}{" "}
                    <span>
                      나 {g.user} · 프로 {g.pro}
                    </span>
                  </p>
                  <p>{g.summary}</p>
                  {result.trialLimited ? (
                    <p className="swing-gaps__drill">교정: {g.drill}</p>
                  ) : (
                    <>
                      <p className="swing-gaps__drill">드릴: {g.drill}</p>
                      <p className="swing-gaps__feel">감각: {g.feel}</p>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ul>

          {result.trialLimited ? (
            <p className="swing-note">
              유료 회원은 6개 페이즈 전부, 데일리 코칭, 교정 자료 배포, 영상 재업로드
              추이까지 열립니다.{" "}
              <Link href="/swing/membership">멤버십 보기</Link>
            </p>
          ) : (
            <div className="swing-phases">
              {result.phaseNotes.map((p) => (
                <article key={p.phase}>
                  <h3>{PHASE_LABEL_KO[p.phase]}</h3>
                  <p>{p.note}</p>
                </article>
              ))}
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
