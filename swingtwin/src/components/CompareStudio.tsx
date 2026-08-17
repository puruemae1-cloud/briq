import { useCallback, useEffect, useRef, useState } from "react";
import { analyzePair } from "@/lib/analyze";
import { applyHandedness, captureView, fuseSkeletons, sampleCompareSet } from "@/lib/capture";
import { TOUR_STYLE } from "@/lib/anatomy";
import { defaultProId, getPro } from "@/lib/pros";
import { getReferenceClip } from "@/lib/reference-clips";
import { useTwinStore } from "@/lib/store";
import { saveClip, clipObjectUrl, loadClip, deleteClip } from "@/lib/video-store";
import { autoFrameSwingVideo } from "@/lib/swing-framing";
import { detectSwingSync, modelSyncFromUser, syncFromSkeleton } from "@/lib/swing-sync";
import type { SkeletonFrame, SwingSyncMarkers, ViewCapture } from "@/lib/types";
import { SideBySide } from "./SideBySide";
import { Swing3D } from "./Swing3D";
import { PlayerPicker } from "./PlayerPicker";
import { PhaseOverlay } from "./PhaseOverlay";

async function loadVideo(src: string) {
  const video = document.createElement("video");
  video.src = src;
  video.muted = true;
  video.playsInline = true;
  video.crossOrigin = "anonymous";
  await new Promise<void>((resolve, reject) => {
    video.onloadedmetadata = () => resolve();
    video.onerror = () => reject(new Error("Could not read that video."));
  });
  return video;
}

async function fileToVideo(file: File) {
  const url = URL.createObjectURL(file);
  const video = await loadVideo(url);
  return { video, url };
}

function isBlobUrl(url?: string) {
  return Boolean(url?.startsWith("blob:"));
}

export function CompareStudio() {
  const [myFace, setMyFace] = useState<File | null>(null);
  const [myDtl, setMyDtl] = useState<File | null>(null);
  const [tourFile, setTourFile] = useState<File | null>(null);
  const [userUrl, setUserUrl] = useState<string | undefined>();
  const [tourUrl, setTourUrl] = useState<string | undefined>();
  const [busy, setBusy] = useState<string | null>(null);
  const [syncBusy, setSyncBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [phaseT, setPhaseT] = useState<number | undefined>();
  const [tourFrames, setTourFrames] = useState<SkeletonFrame[] | undefined>();
  const [userFileName, setUserFileName] = useState<string>();
  const [tourFileName, setTourFileName] = useState<string>();
  const [liveUserSync, setLiveUserSync] = useState<SwingSyncMarkers | undefined>();
  const [liveTourSync, setLiveTourSync] = useState<SwingSyncMarkers | undefined>();
  const [refTourCapture, setRefTourCapture] = useState<ViewCapture | undefined>();
  const [usingReference, setUsingReference] = useState(false);

  const userFaceInputRef = useRef<HTMLInputElement>(null);
  const userDtlInputRef = useRef<HTMLInputElement>(null);
  const tourInputRef = useRef<HTMLInputElement>(null);

  const preferredProId = useTwinStore((s) => s.preferredProId);
  const handedness = useTwinStore((s) => s.handedness);
  const result = useTwinStore((s) => s.lastResult);
  const thumbs = useTwinStore((s) => s.lastThumbs);
  const skeleton = useTwinStore((s) => s.lastSkeleton) ?? [];
  const setPreferredPro = useTwinStore((s) => s.setPreferredPro);
  const setHandedness = useTwinStore((s) => s.setHandedness);
  const saveAnalysis = useTwinStore((s) => s.saveAnalysis);

  const pro = getPro(preferredProId) ?? getPro(defaultProId())!;
  const reference = getReferenceClip(pro.id);

  const userSync =
    result?.userSync ??
    liveUserSync ??
    (skeleton.length ? syncFromSkeleton(skeleton) : undefined);
  const tourSync =
    result?.tourSync ??
    liveTourSync ??
    (userSync ? modelSyncFromUser(userSync) : undefined);

  const captureReference = useCallback(async () => {
    const ref = getReferenceClip(pro.id);
    if (!ref || tourFile) return undefined;
    setSyncBusy("Loading tour reference…");
    try {
      const video = await loadVideo(ref.src);
      const cap = await captureView(video, "downTheLine", ref.label, {
        handedness,
        style: pro.style ?? TOUR_STYLE,
      });
      setRefTourCapture(cap);
      setLiveTourSync(detectSwingSync(cap.samples, cap.duration));
      setTourUrl(ref.src);
      setTourFileName(ref.label);
      setUsingReference(true);
      return cap;
    } finally {
      setSyncBusy(null);
    }
  }, [pro.id, pro.style, tourFile, handedness]);

  useEffect(() => {
    return () => {
      if (isBlobUrl(userUrl)) URL.revokeObjectURL(userUrl!);
    };
  }, [userUrl]);

  useEffect(() => {
    return () => {
      if (isBlobUrl(tourUrl)) URL.revokeObjectURL(tourUrl!);
    };
  }, [tourUrl]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const user = await clipObjectUrl("user");
      const tour = await clipObjectUrl("tour");
      if (cancelled) {
        if (user?.url) URL.revokeObjectURL(user.url);
        if (tour?.url) URL.revokeObjectURL(tour.url);
        return;
      }
      if (user) {
        setUserUrl(user.url);
        setUserFileName(user.name);
        const row = await loadClip("user");
        if (row) {
          const file = new File([row.blob], row.name, { type: row.blob.type });
          setMyFace(file);
          void captureUserForSync(file);
        }
      }
      if (tour) {
        setTourUrl(tour.url);
        setTourFileName(tour.name);
        setUsingReference(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (tourFile) return;
    void captureReference();
  }, [tourFile, captureReference]);

  async function captureUserForSync(file: File) {
    setSyncBusy("Finding your takeaway → impact…");
    try {
      const { video } = await fileToVideo(file);
      const cap = await captureView(video, "faceOn", file.name, { handedness });
      setLiveUserSync(detectSwingSync(cap.samples, cap.duration));
      return cap;
    } finally {
      setSyncBusy(null);
    }
  }

  async function prepareUserClip(file: File) {
    setSyncBusy("Auto-framing swing…");
    try {
      return await autoFrameSwingVideo(file, setSyncBusy);
    } catch {
      return file;
    } finally {
      setSyncBusy(null);
    }
  }

  async function applyUserFace(file: File) {
    const f = await prepareUserClip(file);
    setMyFace(f);
    const url = URL.createObjectURL(f);
    setUserUrl((prev) => {
      if (isBlobUrl(prev)) URL.revokeObjectURL(prev!);
      return url;
    });
    setUserFileName(f.name);
    await saveClip("user", f);
    await captureUserForSync(f);
  }

  async function applyUserDtl(file: File) {
    const f = await prepareUserClip(file);
    setMyDtl(f);
  }

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
      trialLimited: false,
    });
    const thumbsOut = [
      ...user.flatMap((v) => v.thumbs),
      ...(tour?.flatMap((v) => v.thumbs) ?? []),
    ];
    setTourFrames(tour?.[0]?.skeleton);
    setLiveUserSync(analysis.userSync);
    setLiveTourSync(analysis.tourSync);
    const saved = saveAnalysis(analysis, fused, thumbsOut);
    if (!saved.ok) setError(saved.message);
  }

  async function run() {
    setError(null);
    if (!myFace && !myDtl && !userUrl) {
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
      } else if (userUrl && userFileName) {
        const video = await loadVideo(userUrl);
        userViews.push(
          await captureView(video, "faceOn", userFileName, { handedness }),
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
        setBusy(`Reading ${pro.name}'s clip…`);
        await saveClip("tour", tourFile);
        const { video, url } = await fileToVideo(tourFile);
        urls.push(url);
        setTourUrl(url);
        setTourFileName(tourFile.name);
        setUsingReference(false);
        tourViews = [
          await captureView(video, "faceOn", tourFile.name, {
            handedness,
            style: pro.style ?? TOUR_STYLE,
          }),
        ];
      } else if (refTourCapture) {
        tourViews = [refTourCapture];
      } else {
        const cap = await captureReference();
        if (cap) tourViews = [cap];
      }
      setBusy("Syncing takeaway → impact with Rory…");
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
    const set = sampleCompareSet(handedness);
    commit(set.user, set.tour);
  }

  async function clearUserFace() {
    if (isBlobUrl(userUrl)) URL.revokeObjectURL(userUrl!);
    try {
      await deleteClip("user");
    } catch {
      /* ignore missing row */
    }
    setMyFace(null);
    setUserUrl(undefined);
    setUserFileName(undefined);
    setLiveUserSync(undefined);
    if (userFaceInputRef.current) userFaceInputRef.current.value = "";
  }

  function clearUserDtl() {
    setMyDtl(null);
    if (userDtlInputRef.current) userDtlInputRef.current.value = "";
  }

  async function clearTourUpload() {
    if (isBlobUrl(tourUrl)) URL.revokeObjectURL(tourUrl!);
    try {
      await deleteClip("tour");
    } catch {
      /* ignore missing row */
    }
    setTourFile(null);
    setRefTourCapture(undefined);
    setLiveTourSync(undefined);
    if (tourInputRef.current) tourInputRef.current.value = "";
    await captureReference();
  }

  const hasUserFace = Boolean(myFace || userFileName || userUrl);
  const hasUserDtl = Boolean(myDtl);
  const hasTourUpload = Boolean(tourFile);

  return (
    <div className="twin-page">
      <header className="twin-page__head">
        <p className="twin-kicker">Compare</p>
        <h1>You on the left — Rory on the right</h1>
        <p>
          Upload your face-on clip on the left — we auto-crop static background so
          your swing fills the frame (club arc included). Rory McIlroy&apos;s real PGA
          Tour down-the-line clip loads on the right. Press play to sync arms-up
          through impact.
        </p>
      </header>

      <PlayerPicker value={pro.id} onChange={setPreferredPro} />

      <div className="twin-grid3">
        <label className="twin-drop">
          <span>Left — your swing (face-on)</span>
          <strong>{myFace?.name || userFileName || "Choose video"}</strong>
          <em>Full body, camera in front · auto background crop</em>
          {hasUserFace ? (
            <button
              type="button"
              className="twin-drop__remove"
              aria-label="Remove face-on clip"
              onClick={(e) => {
                e.preventDefault();
                void clearUserFace();
              }}
            >
              Remove
            </button>
          ) : null}
          <input
            ref={userFaceInputRef}
            type="file"
            accept="video/*"
            onChange={(e) => {
              const f = e.target.files?.[0] ?? null;
              if (f) void applyUserFace(f);
            }}
          />
        </label>
        <label className="twin-drop">
          <span>Your swing — behind (optional)</span>
          <strong>{myDtl ? myDtl.name : "Choose video"}</strong>
          <em>Down the line · auto crop · unlocks 3D</em>
          {hasUserDtl ? (
            <button
              type="button"
              className="twin-drop__remove"
              aria-label="Remove down-the-line clip"
              onClick={(e) => {
                e.preventDefault();
                clearUserDtl();
              }}
            >
              Remove
            </button>
          ) : null}
          <input
            ref={userDtlInputRef}
            type="file"
            accept="video/*"
            onChange={(e) => {
              const f = e.target.files?.[0] ?? null;
              if (f) void applyUserDtl(f);
            }}
          />
        </label>
        <label className="twin-drop twin-drop--tour">
          <span>Right — override Rory clip (optional)</span>
          <strong>
            {tourFile
              ? tourFile.name
              : usingReference
                ? tourFileName || `${pro.name} reference`
                : "Uses bundled Rory DTL clip"}
          </strong>
          <em>Save from Instagram to replace the default tour file</em>
          {hasTourUpload ? (
            <button
              type="button"
              className="twin-drop__remove"
              aria-label="Remove tour clip override"
              onClick={(e) => {
                e.preventDefault();
                void clearTourUpload();
              }}
            >
              Remove
            </button>
          ) : null}
          <input
            ref={tourInputRef}
            type="file"
            accept="video/*"
            onChange={(e) => {
              const f = e.target.files?.[0] ?? null;
              setTourFile(f);
              if (f) {
                const url = URL.createObjectURL(f);
                setTourUrl((prev) => {
                  if (isBlobUrl(prev)) URL.revokeObjectURL(prev!);
                  return url;
                });
                setTourFileName(f.name);
                setUsingReference(false);
                setRefTourCapture(undefined);
                void saveClip("tour", f);
                void (async () => {
                  setSyncBusy("Reading tour clip…");
                  try {
                    const { video } = await fileToVideo(f);
                    const cap = await captureView(video, "faceOn", f.name, {
                      handedness,
                      style: pro.style ?? TOUR_STYLE,
                    });
                    setLiveTourSync(detectSwingSync(cap.samples, cap.duration));
                    setRefTourCapture(cap);
                  } finally {
                    setSyncBusy(null);
                  }
                })();
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
          disabled={Boolean(busy)}
        >
          {busy ?? "Compare & save"}
        </button>
        <button
          type="button"
          className="twin-btn twin-btn--ghost"
          onClick={runSample}
          disabled={Boolean(busy)}
        >
          Sample pair
        </button>
      </div>
      {reference && usingReference ? (
        <p className="twin-note">
          Right panel: <strong>{reference.label}</strong> from{" "}
          <a href={reference.sourceUrl} target="_blank" rel="noreferrer">
            {reference.sourceName}
          </a>
          . Same style of clip reposted on {reference.instagramHandles.join(", ")}.
          Instagram is not scraped — this is a bundled official excerpt.
        </p>
      ) : null}
      {syncBusy ? <p className="twin-note">{syncBusy}</p> : null}
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
        tourIsReference={usingReference}
      />

      {userUrl && tourUrl && userSync && tourSync ? (
        <p className="twin-note">
          Press <strong>Play synced swing</strong> — both clips start at takeaway
          and hit impact together.
        </p>
      ) : userUrl && !userSync ? (
        <p className="twin-note">Reading your clip for sync points…</p>
      ) : null}

      {result && skeleton.length ? (
        <PhaseOverlay
          userFrames={skeleton}
          proFrames={tourFrames}
          pro={pro}
          handedness={handedness}
          trialLimited={false}
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
              {result.comparedAgainstClip ? " · real tour clip" : " · player model"}
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
          <h2>Where you differ</h2>
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
                <p className="twin-gaps__feel">Feel: {g.feel}</p>
              </li>
            ))}
          </ul>
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
        </>
      ) : null}
    </div>
  );
}
