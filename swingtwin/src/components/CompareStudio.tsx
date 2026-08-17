"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { analyzePair } from "@/lib/analyze";
import { captureView, fuseSkeletons, sampleCompareSet } from "@/lib/capture";
import { defaultProId, getPro, PROS } from "@/lib/pros";
import { useTwinStore } from "@/lib/store";
import type { ViewCapture } from "@/lib/types";
import { PHASE_LABEL } from "@/lib/types";
import { SideBySide } from "./SideBySide";
import { Swing3D } from "./Swing3D";

async function fileToVideo(file: File) {
  const url = URL.createObjectURL(file);
  const video = document.createElement("video");
  video.src = url;
  video.muted = true;
  video.playsInline = true;
  await new Promise<void>((resolve, reject) => {
    video.onloadedmetadata = () => resolve();
    video.onerror = () => reject(new Error("Could not read that video."));
  });
  return { video, url };
}

export function CompareStudio() {
  const [myFace, setMyFace] = useState<File | null>(null);
  const [myDtl, setMyDtl] = useState<File | null>(null);
  const [tourFile, setTourFile] = useState<File | null>(null);
  const [userUrl, setUserUrl] = useState<string | undefined>();
  const [tourUrl, setTourUrl] = useState<string | undefined>();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const tier = useTwinStore((s) => s.tier);
  const trialUsed = useTwinStore((s) => s.trialUsed);
  const preferredProId = useTwinStore((s) => s.preferredProId);
  const handedness = useTwinStore((s) => s.handedness);
  const result = useTwinStore((s) => s.lastResult);
  const thumbs = useTwinStore((s) => s.lastThumbs);
  const skeleton = useTwinStore((s) => s.lastSkeleton) ?? [];
  const setPreferredPro = useTwinStore((s) => s.setPreferredPro);
  const setHandedness = useTwinStore((s) => s.setHandedness);
  const saveAnalysis = useTwinStore((s) => s.saveAnalysis);

  const pro = getPro(preferredProId) ?? getPro(defaultProId())!;
  const trialBlocked = tier === "trial" && trialUsed;

  useEffect(() => {
    return () => {
      if (userUrl) URL.revokeObjectURL(userUrl);
    };
  }, [userUrl]);

  useEffect(() => {
    return () => {
      if (tourUrl) URL.revokeObjectURL(tourUrl);
    };
  }, [tourUrl]);

  function commit(userViews: ViewCapture[], tourViews?: ViewCapture[]) {
    const fused = fuseSkeletons(
      userViews.find((v) => v.view === "faceOn")?.skeleton,
      userViews.find((v) => v.view === "downTheLine")?.skeleton,
    );
    const analysis = analyzePair({
      userViews,
      tourViews,
      proId: pro.id,
      handedness,
      trialLimited: tier !== "subscriber",
    });
    const thumbsOut = [
      ...userViews.flatMap((v) => v.thumbs),
      ...(tourViews?.flatMap((v) => v.thumbs) ?? []),
    ];
    const saved = saveAnalysis(analysis, fused, thumbsOut);
    if (!saved.ok) setError(saved.message);
  }

  async function run() {
    setError(null);
    if (trialBlocked) {
      setError("Trial is used. Subscribe to keep comparing new swings.");
      return;
    }
    if (!myFace && !myDtl) {
      setError("Upload at least one clip of your own swing.");
      return;
    }
    const urls: string[] = [];
    try {
      const userViews: ViewCapture[] = [];
      if (myFace) {
        setBusy("Reading your face-on clip…");
        const { video, url } = await fileToVideo(myFace);
        urls.push(url);
        setUserUrl(url);
        userViews.push(await captureView(video, "faceOn", myFace.name));
      }
      if (myDtl) {
        setBusy("Reading your down-the-line clip…");
        const { video, url } = await fileToVideo(myDtl);
        urls.push(url);
        if (!myFace) setUserUrl(url);
        userViews.push(await captureView(video, "downTheLine", myDtl.name));
      }
      let tourViews: ViewCapture[] | undefined;
      if (tourFile) {
        setBusy("Reading the tour player clip…");
        const { video, url } = await fileToVideo(tourFile);
        urls.push(url);
        setTourUrl(url);
        tourViews = [await captureView(video, "faceOn", tourFile.name)];
      }
      setBusy("Comparing you with the player…");
      commit(userViews, tourViews);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Compare failed.");
      urls.forEach((u) => URL.revokeObjectURL(u));
    } finally {
      setBusy(null);
    }
  }

  function runSample() {
    setError(null);
    if (trialBlocked) {
      setError("Trial is used. Subscribe to keep comparing new swings.");
      return;
    }
    const set = sampleCompareSet();
    commit(set.user, set.tour);
  }

  return (
    <div className="twin-page">
      <header className="twin-page__head">
        <p className="twin-kicker">Compare</p>
        <h1>Your swing next to the player you want</h1>
        <p>
          Upload your clip, then the PGA (or LPGA) slow-mo you are copying. We line them
          up, score the differences, and tell you what to change. Face-on plus
          down-the-line also builds a 3D skeleton.
        </p>
      </header>

      {trialBlocked ? (
        <div className="twin-banner">
          You have used the free comparison.{" "}
          <Link href="/subscribe">Subscribe (£12.99 / month)</Link> to keep uploading.
        </div>
      ) : null}

      <div className="twin-grid3">
        <label className="twin-drop">
          <span>1. Your swing — face-on</span>
          <strong>{myFace ? myFace.name : "Choose video"}</strong>
          <em>Full body, camera in front</em>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setMyFace(e.target.files?.[0] ?? null)}
          />
        </label>
        <label className="twin-drop">
          <span>2. Your swing — behind (optional)</span>
          <strong>{myDtl ? myDtl.name : "Choose video"}</strong>
          <em>Down the line — unlocks 3D</em>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setMyDtl(e.target.files?.[0] ?? null)}
          />
        </label>
        <label className="twin-drop twin-drop--tour">
          <span>3. Their swing</span>
          <strong>{tourFile ? tourFile.name : "Choose the player clip"}</strong>
          <em>The exact video you want to look like</em>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setTourFile(e.target.files?.[0] ?? null)}
          />
        </label>
      </div>

      <div className="twin-toolbar">
        <label>
          This clip is
          <select
            value={pro.id}
            onChange={(e) => setPreferredPro(e.target.value)}
          >
            {PROS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} · {p.tour}
              </option>
            ))}
          </select>
        </label>
        <label>
          You play
          <select
            value={handedness}
            onChange={(e) =>
              setHandedness(e.target.value === "left" ? "left" : "right")
            }
          >
            <option value="right">Right-handed</option>
            <option value="left">Left-handed</option>
          </select>
        </label>
        <button
          type="button"
          className="twin-btn"
          onClick={() => void run()}
          disabled={Boolean(busy) || trialBlocked}
        >
          {busy ?? (tier === "subscriber" ? "Compare & save" : "Trial compare")}
        </button>
        <button
          type="button"
          className="twin-btn twin-btn--ghost"
          onClick={runSample}
          disabled={Boolean(busy) || trialBlocked}
        >
          Sample pair
        </button>
      </div>
      <p className="twin-note">
        Sample uses the trial. Save a player slow-mo from Instagram or Tour coverage onto
        your phone, then pick it in box 3.
      </p>
      {error ? <p className="twin-error">{error}</p> : null}

      <SideBySide
        userUrl={userUrl}
        tourUrl={tourUrl}
        userLabel={myFace?.name || myDtl?.name || "Your swing"}
        tourLabel={tourFile?.name || pro.name}
        userPeakT={result?.userPeakT}
        tourPeakT={result?.tourPeakT}
      />

      {result ? (
        <section className="twin-result">
          <div className="twin-score">
            <p>Match</p>
            <strong>{result.overall}</strong>
            <span>
              vs {result.proName}
              {result.comparedAgainstClip ? " · clip vs clip" : " · player model"}
            </span>
            <em>
              {result.has3d
                ? "3D from face-on + down-the-line"
                : "Add a behind-the-ball clip for 3D"}
            </em>
          </div>
          <Swing3D
            frames={skeleton}
            label={result.has3d ? "Drag to orbit" : "Single-camera preview"}
          />
        </section>
      ) : null}

      {thumbs.length ? (
        <div className="twin-thumbs">
          {thumbs.map((src, i) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img key={i} src={src} alt="" />
          ))}
        </div>
      ) : null}

      {result ? (
        <>
          <h2>
            {result.trialLimited
              ? "Trial — three differences"
              : "Where you differ"}
          </h2>
          <ul className="twin-gaps">
            {result.gaps.map((g) => (
              <li key={g.key} className={`is-${g.severity}`}>
                <p>
                  {g.label}
                  <span>
                    You {g.user} · Them {g.pro}
                  </span>
                </p>
                <p>{g.summary}</p>
                <p className="twin-gaps__drill">Fix: {g.drill}</p>
                {result.trialLimited ? null : (
                  <p className="twin-gaps__feel">Feel: {g.feel}</p>
                )}
              </li>
            ))}
          </ul>
          {result.trialLimited ? (
            <p className="twin-note">
              Subscribers get every phase, a daily plan, and a printable sheet.{" "}
              <Link href="/subscribe">See plans</Link>
            </p>
          ) : (
            <div className="twin-phases">
              {result.phaseNotes.map((p) => (
                <article key={p.phase}>
                  <h3>{PHASE_LABEL[p.phase]}</h3>
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
