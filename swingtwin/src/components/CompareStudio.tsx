import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { analyzePair } from "@/lib/analyze";
import { applyHandedness, captureView, fuseSkeletons, sampleCompareSet } from "@/lib/capture";
import { TOUR_STYLE } from "@/lib/anatomy";
import { defaultProId, getPro } from "@/lib/pros";
import { useTwinStore } from "@/lib/store";
import { saveClip, clipObjectUrl } from "@/lib/video-store";
import { modelSyncFromUser, syncFromSkeleton } from "@/lib/swing-sync";
import type { SkeletonFrame, ViewCapture } from "@/lib/types";
import { SideBySide } from "./SideBySide";
import { Swing3D } from "./Swing3D";
import { PlayerPicker } from "./PlayerPicker";
import { PhaseOverlay } from "./PhaseOverlay";

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
  const [phaseT, setPhaseT] = useState<number | undefined>();
  const [tourFrames, setTourFrames] = useState<SkeletonFrame[] | undefined>();
  const [userFileName, setUserFileName] = useState<string>();
  const [tourFileName, setTourFileName] = useState<string>();

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
  const userSync =
    result?.userSync ?? (skeleton.length ? syncFromSkeleton(skeleton) : undefined);
  const tourSync =
    result?.tourSync ??
    (userSync ? modelSyncFromUser(userSync) : undefined);

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

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const user = await clipObjectUrl("user");
      const tour = await clipObjectUrl("tour");
      if (cancelled) {
        user?.url && URL.revokeObjectURL(user.url);
        tour?.url && URL.revokeObjectURL(tour.url);
        return;
      }
      if (user) {
        setUserUrl(user.url);
        setUserFileName(user.name);
      }
      if (tour) {
        setTourUrl(tour.url);
        setTourFileName(tour.name);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  function commit(userViews: ViewCapture[], tourViews?: ViewCapture[]) {
    const user = applyHandedness(userViews, handedness);
    const tour = tourViews
      ? applyHandedness(tourViews, handedness, pro.style ?? TOUR_STYLE)
      : undefined;
    const fused = fuseSkeletons(
      user.find((v) => v.view === "faceOn")?.skeleton,
      user.find((v) => v.view === "downTheLine")?.skeleton,
    );
    const analysis = analyzePair({
      userViews: user,
      tourViews: tour,
      proId: pro.id,
      handedness,
      trialLimited: tier !== "subscriber",
    });
    const thumbsOut = [
      ...user.flatMap((v) => v.thumbs),
      ...(tour?.flatMap((v) => v.thumbs) ?? []),
    ];
    setTourFrames(tour?.[0]?.skeleton);
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
        await saveClip("user", myFace);
        const { video, url } = await fileToVideo(myFace);
        urls.push(url);
        setUserUrl(url);
        setUserFileName(myFace.name);
        userViews.push(
          await captureView(video, "faceOn", myFace.name, { handedness }),
        );
      }
      if (myDtl) {
        setBusy("Reading your down-the-line clip…");
        const { video, url } = await fileToVideo(myDtl);
        urls.push(url);
        if (!myFace) setUserUrl(url);
        userViews.push(
          await captureView(video, "downTheLine", myDtl.name, { handedness }),
        );
      }
      let tourViews: ViewCapture[] | undefined;
      if (tourFile) {
        setBusy("Reading the tour player clip…");
        await saveClip("tour", tourFile);
        const { video, url } = await fileToVideo(tourFile);
        urls.push(url);
        setTourUrl(url);
        setTourFileName(tourFile.name);
        tourViews = [
          await captureView(video, "faceOn", tourFile.name, {
            handedness,
            style: pro.style ?? TOUR_STYLE,
          }),
        ];
      }
      setBusy("Syncing 30 phases against the player…");
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
    const set = sampleCompareSet(handedness);
    commit(set.user, set.tour);
  }

  return (
    <div className="twin-page">
      <header className="twin-page__head">
        <p className="twin-kicker">Compare</p>
        <h1>Your swing next to the player you want</h1>
        <p>
          Pick any PGA name from the five Instagram archives, upload your clip,
          then (optionally) the exact tour slow-mo you are copying. We sync both
          swings through 30 phases and draw a line on every body part that
          differs — hands, wrists, arms, shoulders, thighs, knees, feet, head.
        </p>
      </header>

      {trialBlocked ? (
        <div className="twin-banner">
          You have used the free comparison.{" "}
          <Link to="/subscribe">Subscribe (£12.99 / month)</Link> to keep uploading.
        </div>
      ) : null}

      <PlayerPicker value={pro.id} onChange={setPreferredPro} />

      <div className="twin-grid3">
        <label className="twin-drop">
          <span>1. Your swing — face-on</span>
          <strong>{myFace ? myFace.name : "Choose video"}</strong>
          <em>Full body, camera in front</em>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => {
              const f = e.target.files?.[0] ?? null;
              setMyFace(f);
              if (f) {
                const url = URL.createObjectURL(f);
                setUserUrl((prev) => {
                  if (prev) URL.revokeObjectURL(prev);
                  return url;
                });
                setUserFileName(f.name);
                void saveClip("user", f);
              }
            }}
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
          <span>3. Their swing (optional clip)</span>
          <strong>{tourFile ? tourFile.name : "Saved Instagram / tour clip"}</strong>
          <em>If empty, we use the learned {pro.name} model</em>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => {
              const f = e.target.files?.[0] ?? null;
              setTourFile(f);
              if (f) {
                const url = URL.createObjectURL(f);
                setTourUrl((prev) => {
                  if (prev) URL.revokeObjectURL(prev);
                  return url;
                });
                setTourFileName(f.name);
                void saveClip("tour", f);
              }
            }}
          />
        </label>
      </div>

      <div className="twin-toolbar">
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
        Instagram is not scraped live (their terms). Each name is a model
        distilled from the public FO/DTL patterns those accounts repeat. Save a
        clip from @golf_swings, @pgatour, @golfdigest, @golf_gods or
        @golfonthesnap onto your phone and pick it in box 3 for clip-vs-clip.
        Changing the player after a compare redraws the overlay on this swing.
      </p>
      {error ? <p className="twin-error">{error}</p> : null}

      <SideBySide
        userUrl={userUrl}
        tourUrl={tourUrl}
        userLabel={myFace?.name || userFileName || "Your swing"}
        tourLabel={tourFile?.name || tourFileName || pro.name}
        userSync={userSync}
        tourSync={tourSync}
        phaseT={phaseT}
        pro={pro}
        handedness={handedness}
      />

      {userUrl && !userSync ? (
        <p className="twin-note">
          Press <strong>Trial compare</strong> to lock takeaway → impact sync with{" "}
          {pro.name}.
        </p>
      ) : null}

      {result && skeleton.length ? (
        <PhaseOverlay
          userFrames={skeleton}
          proFrames={tourFrames}
          pro={pro}
          handedness={handedness}
          trialLimited={result.trialLimited}
          onPhase={(_i, t) => setPhaseT(t)}
        />
      ) : null}

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
              Subscribers get all 30 phases, 30 body lines, a daily plan, and a
              printable sheet. <Link to="/subscribe">See plans</Link>
            </p>
          ) : (
            <div className="twin-phases twin-phases--fine">
              {(result.finePhaseNotes ?? []).map((p) => (
                <article key={`${p.n}-${p.label}`}>
                  <h3>
                    {p.n}. {p.code} · {p.label}
                  </h3>
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
